"""
Background similarity checks for update/version flows (Option A).
Does not save until user reviews suggestions and confirms on Similarity Review page.
"""

import logging
import threading
from typing import Any, Dict, List, Optional

from django.db import connection
from django.utils import timezone

from ..models_extensions.similarity_models import SimilarityCheckAudit
from ..routes.Global.notifications import get_user_email_from_id
from .similarity_service import SimilarityCheckRequest, SimilarityService

logger = logging.getLogger(__name__)

_ENTITY_COPY = {
    'Framework': {
        'review_title': 'Similar frameworks ready to review',
        'noun': 'framework',
        'nouns': 'frameworks',
        'category': 'framework',
    },
    'Policy': {
        'review_title': 'Similar policies ready to review',
        'noun': 'policy',
        'nouns': 'policies',
        'category': 'policy',
    },
    'SubPolicy': {
        'review_title': 'Similar sub-policies ready to review',
        'noun': 'sub-policy',
        'nouns': 'sub-policies',
        'category': 'policy',
    },
    'Compliance': {
        'review_title': 'Similar compliance items ready to review',
        'noun': 'compliance item',
        'nouns': 'compliance items',
        'category': 'compliance',
    },
}

_OPERATION_PHRASE = {
    'framework_version': 'framework version',
    'policy_version': 'policy version',
    'compliance_update': 'compliance version',
    'tt_create_framework': 'new tailored framework',
    'tt_create_policy': 'new tailored policy',
}


def _resolve_notification_entity(operation: Optional[str], item_types: List[str]) -> str:
    types = list(dict.fromkeys(t for t in (item_types or []) if t))
    if operation == 'compliance_update':
        return 'Compliance'
    if operation in ('framework_version', 'tt_create_framework'):
        return 'Framework'
    if operation in ('policy_version', 'tt_create_policy'):
        if types == ['SubPolicy']:
            return 'SubPolicy'
        if 'SubPolicy' in types and 'Policy' not in types and 'Framework' not in types:
            return 'SubPolicy'
        return 'Policy'
    if len(types) == 1:
        return types[0]
    if 'Compliance' in types:
        return 'Compliance'
    if 'SubPolicy' in types:
        return 'SubPolicy'
    if 'Policy' in types:
        return 'Policy'
    if 'Framework' in types:
        return 'Framework'
    return 'Policy'


def _build_start_message(operation: Optional[str], item_types: List[str]) -> str:
    entity = _resolve_notification_entity(operation, item_types)
    meta = _ENTITY_COPY.get(entity, _ENTITY_COPY['Policy'])
    return (
        f'We are comparing your {meta["noun"]} changes with existing records. '
        'You will receive a notification when the review is ready. '
        'Nothing is saved until you open the review and confirm.'
    )


def _build_ready_notification(
    operation: Optional[str],
    item_types: List[str],
    label: str,
) -> Dict[str, str]:
    entity = _resolve_notification_entity(operation, item_types)
    meta = _ENTITY_COPY.get(entity, _ENTITY_COPY['Policy'])
    op_phrase = _OPERATION_PHRASE[operation] if operation in _OPERATION_PHRASE else meta['noun']
    name = (label or '').strip()
    name_part = f' "{name[:120]}"' if name else ''
    return {
        'title': meta['review_title'],
        'message': (
            f'Possible matches are ready for your {op_phrase}{name_part}. '
            'Open the review, then confirm save to apply your changes.'
        ),
        'category': meta['category'],
        'entity_type': entity,
    }


def get_similarity_notification_display(check_id: int) -> Optional[Dict[str, str]]:
    """
    Build notification title/message from the similarity master audit row.
    Used when loading notifications so older rows without entity: in error still read correctly.
    """
    try:
        master = SimilarityCheckAudit.objects.get(id=check_id)
    except SimilarityCheckAudit.DoesNotExist:
        return None

    ctx = dict(master.classification_context_used or {})
    operation = ctx.get('pending_save_operation')
    label = (ctx.get('pending_save_label') or master.proposed_name or '').strip()
    item_types = [
        s.get('item_type')
        for s in (ctx.get('batch_summaries') or [])
        if s.get('item_type')
    ]
    if not item_types and master.item_type:
        item_types = [master.item_type]
    return _build_ready_notification(operation, item_types, label)


def _parse_int(value) -> Optional[int]:
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _insert_similarity_notification(
    recipient: str,
    master_check_id: int,
    *,
    entity_type: str,
    operation: Optional[str] = None,
) -> None:
    err = f"check_id:{master_check_id};entity:{entity_type}"
    if operation:
        err += f";op:{operation}"
    try:
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO notifications (recipient, type, channel, success, error, created_at, FrameworkId)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    recipient,
                    'similarity_check_ready',
                    'in_app',
                    1,
                    err,
                    timezone.now(),
                    None,
                ),
            )
    except Exception as e:
        logger.exception('Failed to insert similarity notification check_id=%s: %s', master_check_id, e)


def _build_check_request(spec: Dict[str, Any], tenant_id: Optional[int], user_id: Optional[int]) -> SimilarityCheckRequest:
    return SimilarityCheckRequest(
        item_type=spec.get('item_type'),
        item_data=spec.get('item_data') or {},
        tenant_id=tenant_id,
        user_id=user_id,
        parent_framework_id=_parse_int(spec.get('parent_framework_id')),
        parent_policy_id=_parse_int(spec.get('parent_policy_id')),
        parent_subpolicy_id=_parse_int(spec.get('parent_subpolicy_id')),
        exclude_entity_id=_parse_int(spec.get('exclude_entity_id')),
        framework_context=spec.get('framework_context'),
        policy_context=spec.get('policy_context'),
    )


def _run_batch(master_id: int, check_specs: List[Dict], tenant_id: Optional[int], user_id: Optional[int]) -> None:
    connection.close()
    service = SimilarityService()
    batch_check_ids: List[int] = []
    batch_summaries: List[Dict] = []
    failed = False
    error_msg = ''

    try:
        master = SimilarityCheckAudit.objects.get(id=master_id)
        for spec in check_specs:
            name = (spec.get('item_data') or {}).get('name') or (spec.get('item_data') or {}).get('PolicyName') or ''
            if not str(name).strip():
                continue
            req = _build_check_request(spec, tenant_id, user_id)
            result = service.initiate_similarity_check(req)
            batch_check_ids.append(result.check_id)
            try:
                child = SimilarityCheckAudit.objects.get(id=result.check_id)
                child_ctx = dict(child.classification_context_used or {})
                child_ctx['flow'] = 'async_update_review'
                child_ctx['master_check_id'] = master_id
                child.classification_context_used = child_ctx
                child.save(update_fields=['classification_context_used'])
            except Exception as tag_err:
                logger.warning(
                    '[async-update] could not tag child check %s: %s',
                    result.check_id,
                    tag_err,
                )
            batch_summaries.append({
                'check_id': result.check_id,
                'item_type': spec.get('item_type'),
                'item_name': str(name).strip(),
                'risk_level': result.classification,
                'candidate_count': len(result.candidates or []),
                'suggested_action': result.suggested_action,
            })

        ctx = dict(master.classification_context_used or {})
        ctx['background_status'] = 'READY'
        ctx['batch_check_ids'] = batch_check_ids
        ctx['batch_summaries'] = batch_summaries
        master.classification_context_used = ctx
        master.check_status = 'PENDING'
        master.save(update_fields=['classification_context_used', 'check_status'])

        label = ctx.get('pending_save_label') or master.proposed_name or ''
        operation = ctx.get('pending_save_operation')
        item_types = [s.get('item_type') for s in batch_summaries if s.get('item_type')]
        ready = _build_ready_notification(operation, item_types, label)
        email = get_user_email_from_id(user_id) if user_id else None
        recipient = (email or '').strip() or f'user_{user_id}'
        _insert_similarity_notification(
            recipient,
            master_id,
            entity_type=ready['entity_type'],
            operation=operation,
        )
        try:
            from ..routes.Global.notifications import notifications_storage
            from datetime import datetime as dt
            import uuid

            notifications_storage.append({
                'id': str(uuid.uuid4()),
                'title': ready['title'],
                'message': ready['message'],
                'category': ready['category'],
                'priority': 'medium',
                'createdAt': dt.now().isoformat(),
                'status': {'isRead': False, 'readAt': None},
                'user_id': str(user_id) if user_id else '',
                'metadata': {
                    'type': 'similarity_check_ready',
                    'check_id': master_id,
                    'entity_type': ready['entity_type'],
                    'operation': operation,
                    'action_url': f'/similarity/review?checkId={master_id}',
                },
            })
            if len(notifications_storage) > 1000:
                notifications_storage.pop(0)
        except Exception as mem_err:
            logger.warning('In-memory similarity notification failed: %s', mem_err)
        logger.info('[async-update] batch ready master=%s checks=%s', master_id, batch_check_ids)
    except Exception as e:
        failed = True
        error_msg = str(e)
        logger.exception('[async-update] batch failed master=%s', master_id)
        try:
            master = SimilarityCheckAudit.objects.get(id=master_id)
            ctx = dict(master.classification_context_used or {})
            ctx['background_status'] = 'FAILED'
            ctx['error'] = error_msg
            master.classification_context_used = ctx
            master.check_status = 'FAILED'
            master.error_message = error_msg
            master.save(update_fields=['classification_context_used', 'check_status', 'error_message'])
        except Exception:
            pass


def start_async_update_batch(
    *,
    check_specs: List[Dict[str, Any]],
    pending_save: Dict[str, Any],
    tenant_id: Optional[int],
    user_id: Optional[int],
) -> Dict[str, Any]:
    """
    Queue background similarity for an update. Returns immediately; save is deferred.
    """
    if not pending_save or not pending_save.get('operation'):
        raise ValueError('pending_save.operation is required')

    first = check_specs[0] if check_specs else {}
    first_data = first.get('item_data') or {}
    item_types = [c.get('item_type') for c in check_specs if c.get('item_type')]
    operation = pending_save.get('operation')
    label = (
        pending_save.get('label')
        or first_data.get('name')
        or first_data.get('PolicyName')
        or first_data.get('ComplianceTitle')
        or 'Update'
    )

    master = SimilarityCheckAudit.objects.create(
        tenant_id=tenant_id,
        user_id=user_id,
        item_type=first.get('item_type') or 'Framework',
        proposed_name=str(label)[:1000],
        proposed_description=pending_save.get('summary') or str(label),
        check_status='PENDING',
        classification_context_used={
            'flow': 'async_update',
            'background_status': 'PROCESSING',
            'pending_save_operation': pending_save.get('operation'),
            'pending_save_entity_pk': pending_save.get('entity_pk'),
            'pending_save_payload': pending_save.get('payload'),
            'pending_save_meta': pending_save.get('meta'),
            'pending_save_label': label,
            'batch_check_ids': [],
            'batch_summaries': [],
        },
    )

    thread = threading.Thread(
        target=_run_batch,
        args=(master.id, check_specs, tenant_id, user_id),
        daemon=True,
    )
    thread.start()

    return {
        'master_check_id': master.id,
        'status': 'PROCESSING',
        'message': _build_start_message(operation, item_types),
        'entity_type': _resolve_notification_entity(operation, item_types),
    }
