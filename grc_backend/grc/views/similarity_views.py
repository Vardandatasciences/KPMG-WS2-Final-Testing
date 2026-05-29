"""
Step 7: Similarity Check API Views
API endpoints for fetching and displaying similarity results to frontend.
"""

import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from ..models_extensions.similarity_models import SimilarityCheckAudit
from ..services.similarity_service import SimilarityService, SimilarityCheckRequest
from ..tenant_utils import get_tenant_id_from_request

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_similarity(request):
    """
    Initiate similarity check (Steps 1-6).
    
    Called when user submits create form.
    Runs full pipeline: Text Cleaning → Domain → Embedding → Search → Rerank → LLM
    
    Request Body:
    {
        "item_type": "Framework|Policy|SubPolicy|Compliance",
        "item_data": {form data},
        "tenant_id": 1,
        "parent_framework_id": null,
        "parent_policy_id": null,
        "parent_subpolicy_id": null
    }
    
    Response:
    {
        "check_id": 60,
        "status": "ANALYZED",
        "can_create": true,
        "risk_level": "MEDIUM",
        "overall_advice": "Review manually...",
        "suggested_action": "WARN",
        "candidates": [...]
    }
    """
    try:
        data = request.data
        
        def _parse_optional_int(value):
            if value is None or value == '':
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        # Build request
        check_request = SimilarityCheckRequest(
            item_type=data.get('item_type'),
            item_data=data.get('item_data', {}),
            tenant_id=data.get('tenant_id') or get_tenant_id_from_request(request),
            user_id=request.user.id,
            parent_framework_id=_parse_optional_int(data.get('parent_framework_id')),
            parent_policy_id=_parse_optional_int(data.get('parent_policy_id')),
            parent_subpolicy_id=_parse_optional_int(data.get('parent_subpolicy_id')),
            exclude_entity_id=_parse_optional_int(data.get('exclude_entity_id')),
            framework_context=data.get('framework_context'),
            policy_context=data.get('policy_context'),
        )
        
        # Run Steps 1-6
        service = SimilarityService()
        result = service.initiate_similarity_check(check_request)
        
        # Format response for Step 7 UI
        response_data = {
            "check_id": result.check_id,
            "status": result.status,
            "can_create": result.suggested_action != 'BLOCK',
            "risk_level": result.classification or 'UNKNOWN',
            "overall_advice": result.reasoning or "Analysis complete.",
            "suggested_action": result.suggested_action or 'ALLOW',
            "candidates": format_candidates_for_ui(result.candidates, check_request.item_type),
            "domain": result.step2_result.primary_domain if result.step2_result else None,
            "industry": result.step2_result.industry_vertical if result.step2_result else None,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Similarity check failed: {e}")
        return Response(
            {"error": str(e), "status": "FAILED"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_similarity_result(request, check_id):
    """
    Fetch similarity check results for display (Step 7 UI).
    
    GET /api/similarity/check/{check_id}/
    
    Response:
    {
        "check_id": 60,
        "status": "ANALYZED",
        "new_record": {
            "name": "Food Cleanliness Framework",
            "description": "...",
            "type": "Framework"
        },
        "analysis": {
            "can_create": true,
            "risk_level": "MEDIUM",
            "overall_advice": "Review manually...",
            "suggested_action": "WARN"
        },
        "candidates": [
            {
                "id": 101,
                "name": "Food Hygiene Framework",
                "type": "Framework",
                "chroma_score": 0.944,
                "reranker_score": 0.939,
                "final_status": "highly_similar",
                "reason": "Both address food safety...",
                "same_points": ["Domain", "Category"],
                "different_points": ["Specific focus"],
                "recommendation": "review_manually",
                "view_url": "/framework/101/"
            }
        ]
    }
    """
    try:
        audit = get_object_or_404(
            SimilarityCheckAudit,
            id=check_id,
            tenant_id=get_tenant_id_from_request(request)
        )
        
        # Format for UI
        ctx = _audit_context(audit)
        response_data = {
            "check_id": audit.id,
            "status": "ANALYZED" if audit.llm_classification else "PENDING",
            "flow": ctx.get("flow"),
            "background_status": ctx.get("background_status"),
            "batch_check_ids": ctx.get("batch_check_ids") or [],
            "batch_summaries": ctx.get("batch_summaries") or [],
            "new_record": {
                "name": audit.proposed_name,
                "description": audit.proposed_description,
                "type": audit.item_type,
                "structured_json": audit.proposed_structured_json
            },
            "analysis": {
                "can_create": audit.llm_suggested_action != 'BLOCK',
                "risk_level": audit.llm_classification or 'UNKNOWN',
                "confidence": audit.llm_confidence,
                "overall_advice": audit.llm_reasoning or "Analysis in progress...",
                "suggested_action": audit.llm_suggested_action or 'ALLOW',
                "domain": audit.classified_primary_domain,
                "industry": audit.classified_industry_vertical
            },
            "candidates": format_candidates_for_ui(audit.candidates_found, audit.item_type)
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Failed to fetch similarity result: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def format_candidates_for_ui(candidates, default_entity_type=None):
    """Format candidates for frontend display."""
    if not candidates:
        return []
    
    formatted = []
    for c in candidates:
        entity_type = (
            c.get('entity_type')
            or c.get('record_type')
            or default_entity_type
            or ''
        )
        formatted.append({
            "id": c.get('entity_id') or c.get('id'),
            "record_type": entity_type,
            "entity_type": entity_type,
            "name": c.get('name', 'Unknown'),
            "chroma_score": c.get('chroma_score', c.get('score', 0)),
            "reranker_score": c.get('reranker_score', 0),
            "final_status": c.get('final_status', 'unknown'),
            "reason": c.get('reason', ''),
            "same_points": c.get('same_points', []),
            "different_points": c.get('different_points', []),
            "recommendation": c.get('recommendation', 'review_manually'),
            "domain": c.get('domain', ''),
            "category": c.get('category', ''),
            "view_url": generate_view_url(c)
        })
    
    return formatted


def generate_view_url(candidate):
    """Generate view URL for candidate record."""
    entity_type = candidate.get('entity_type', '').lower()
    entity_id = candidate.get('entity_id') or candidate.get('id')
    
    url_map = {
        'framework': f'/framework/{entity_id}/',
        'policy': f'/policy/{entity_id}/',
        'subpolicy': f'/subpolicy/{entity_id}/',
        'compliance': f'/compliance/{entity_id}/'
    }
    
    return url_map.get(entity_type, '#')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_similarity_decision(request, check_id):
    """
    Step 8 & 9: Record user decision and finalize (create/use existing/cancel).
    
    Called when user clicks: Create Anyway / Use Existing / Cancel
    
    Request Body:
    {
        "decision": "CREATE_ANYWAY|USE_EXISTING|CANCEL",
        "selected_candidate_id": 101,  # if USE_EXISTING
        "reason": "User provided reason"
    }
    
    Response:
    {
        "success": true,
        "step8_decision": "CREATE_ANYWAY",
        "step9_result": {
            "action_taken": "CREATED",
            "created_record_id": 123,
            "created_record_type": "Framework",
            "message": "Created Framework successfully"
        }
    }
    """
    try:
        from ..services.similarity_finalize_service import finalize_similarity_check
        
        data = request.data
        decision = data.get('decision', 'CANCEL')
        selected_candidate_id = data.get('selected_candidate_id')
        reason = data.get('reason', '')
        
        # Step 8: Record user decision
        audit = get_object_or_404(
            SimilarityCheckAudit,
            id=check_id,
            tenant_id=get_tenant_id_from_request(request)
        )
        
        audit.user_decision = decision
        audit.user_id = request.user.id
        audit.save(update_fields=['user_decision', 'user_id'])
        
        logger.info(f"[Step 8] User decision for check {check_id}: {decision}")
        
        # Step 9: Finalize based on decision
        result = finalize_similarity_check(
            check_id=check_id,
            user_decision=decision,
            selected_candidate_id=selected_candidate_id,
            user_id=request.user.id
        )
        
        logger.info(f"[Step 9] Finalize result: {result.action_taken}")
        
        return Response({
            "success": result.success,
            "step8_decision": decision,
            "step9_result": {
                "action_taken": result.action_taken,
                "created_record_id": result.created_record_id,
                "created_record_type": result.created_record_type,
                "message": result.message,
                "error": result.error
            }
        })
        
    except Exception as e:
        logger.exception(f"Failed to process user decision: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _audit_context(audit: SimilarityCheckAudit) -> dict:
    ctx = audit.classification_context_used
    return ctx if isinstance(ctx, dict) else {}


def _get_async_audit(request, check_id: int) -> SimilarityCheckAudit:
    auth_user = getattr(request, 'user', None)
    user_id = getattr(auth_user, 'UserId', None) or getattr(auth_user, 'id', None)
    audit = get_object_or_404(SimilarityCheckAudit, id=check_id)
    ctx = _audit_context(audit)
    if ctx.get('flow') != 'async_update':
        from rest_framework.exceptions import ValidationError
        raise ValidationError('Not an async update batch')
    if user_id is not None and audit.user_id is not None and int(audit.user_id) != int(user_id):
        from django.http import Http404
        raise Http404()
    return audit


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def async_update_similarity(request):
    """
    Option A: queue background similarity for updates. Does not save the record.
    Body: { checks: [...], pending_save: { operation, entity_pk, payload, label? } }
    """
    try:
        from ..services.similarity_async_update_service import start_async_update_batch

        data = request.data
        checks = data.get('checks') or []
        pending_save = data.get('pending_save') or {}
        if not checks:
            return Response({'error': 'checks array is required'}, status=status.HTTP_400_BAD_REQUEST)

        auth_user = getattr(request, 'user', None)
        user_id = getattr(auth_user, 'UserId', None) or getattr(auth_user, 'id', None)

        result = start_async_update_batch(
            check_specs=checks,
            pending_save=pending_save,
            tenant_id=data.get('tenant_id') or get_tenant_id_from_request(request),
            user_id=user_id,
        )
        return Response(result, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        logger.exception('async_update_similarity failed: %s', e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_async_update_status(request, check_id):
    """Poll or load batch status + pending save metadata (not full payload until confirm)."""
    try:
        audit = _get_async_audit(request, check_id)
        ctx = _audit_context(audit)

        return Response({
            'master_check_id': audit.id,
            'background_status': ctx.get('background_status', 'PROCESSING'),
            'pending_save_operation': ctx.get('pending_save_operation'),
            'pending_save_entity_pk': ctx.get('pending_save_entity_pk'),
            'pending_save_label': ctx.get('pending_save_label'),
            'batch_check_ids': ctx.get('batch_check_ids') or [],
            'batch_summaries': ctx.get('batch_summaries') or [],
            'error': ctx.get('error'),
        })
    except Exception as e:
        logger.exception('get_async_update_status failed: %s', e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_save_payload(request, check_id):
    """Return stored save payload for execute after user confirms on review page."""
    try:
        audit = _get_async_audit(request, check_id)
        ctx = _audit_context(audit)
        if ctx.get('background_status') != 'READY':
            return Response({'error': 'Similarity check not ready yet'}, status=status.HTTP_409_CONFLICT)
        if ctx.get('pending_save_executed'):
            return Response({'error': 'Save already completed'}, status=status.HTTP_409_CONFLICT)

        return Response({
            'operation': ctx.get('pending_save_operation'),
            'entity_pk': ctx.get('pending_save_entity_pk'),
            'payload': ctx.get('pending_save_payload'),
            'meta': ctx.get('pending_save_meta'),
            'label': ctx.get('pending_save_label'),
        })
    except Exception as e:
        logger.exception('get_pending_save_payload failed: %s', e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_pending_save_executed(request, check_id):
    """Mark batch complete after frontend performed the deferred save."""
    try:
        audit = _get_async_audit(request, check_id)
        ctx = _audit_context(audit)
        ctx['pending_save_executed'] = True
        ctx['pending_save_executed_at'] = timezone.now().isoformat()
        audit.classification_context_used = ctx
        audit.check_status = 'COMPLETED'
        audit.final_action = 'CREATED'
        audit.completed_at = timezone.now()
        audit.save(update_fields=['classification_context_used', 'check_status', 'final_action', 'completed_at'])
        return Response({'success': True})
    except Exception as e:
        logger.exception('mark_pending_save_executed failed: %s', e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
