"""Webhook and helpers for recurring audit scheduler (cron / Scheduler microservice)."""
import json
import logging
from datetime import date

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ...models import Audit, RBAC, Users
from ...rbac.utils import RBACUtils
from ...services.audit_recurrence_service import (
    process_audit_recurrence_and_escalations,
    store_in_app_audit_notification,
)
from ...services.audit_review_service import list_stalled_reviews_for_managers
from ...tenant_utils import get_tenant_id_from_request, require_tenant, tenant_filter
from ...utils.auto_decrypt_helper import display_audit_title

logger = logging.getLogger(__name__)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


def _parse_webhook_body(request):
    if hasattr(request, 'data') and isinstance(request.data, dict):
        return request.data
    try:
        raw = request.body.decode('utf-8') if request.body else '{}'
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _is_compliance_manager(user_id: int) -> bool:
    return RBAC.objects.filter(
        user_id=user_id,
        is_active='Y',
        role='Compliance Manager',
    ).exists()


def _is_audit_manager(user_id: int) -> bool:
    return RBAC.objects.filter(
        user_id=user_id,
        is_active='Y',
        role='Audit Manager',
    ).exists()


@csrf_exempt
@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AllowAny])
def run_scheduled_audits_cron(request):
    """
    Daily (or periodic) webhook for audit reminders, overdue escalation, and recurrence.
    Header: X-Scheduled-Audits-Secret or JSON body secret field.
    Must match SCHEDULED_AUDITS_CRON_SECRET (or POLICY_SELF_HEAL_CRON_SECRET if unset).
    Manual: python manage.py run_scheduled_audits
    """
    expected = (getattr(settings, 'SCHEDULED_AUDITS_CRON_SECRET', None) or '').strip()
    body = _parse_webhook_body(request)
    got_header = (
        request.headers.get('X-Scheduled-Audits-Secret')
        or request.META.get('HTTP_X_SCHEDULED_AUDITS_SECRET')
        or ''
    ).strip()
    got_body = ''
    if isinstance(body, dict):
        got_body = (body.get('secret') or body.get('cron_secret') or '').strip()
    got = got_header or got_body

    if not expected:
        logger.error(
            'SCHEDULED_AUDITS_CRON_SECRET and POLICY_SELF_HEAL_CRON_SECRET are not set in .env'
        )
        return Response(
            {'detail': 'Cron secret not configured on server'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    if got != expected:
        return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    tenant_id = None
    if isinstance(body, dict) and body.get('tenant_id') is not None:
        try:
            tenant_id = int(body['tenant_id'])
        except (TypeError, ValueError):
            return Response({'error': 'Invalid tenant_id'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        stats = process_audit_recurrence_and_escalations(tenant_id=tenant_id)
        return Response({'success': True, 'date': date.today().isoformat(), **stats})
    except Exception as e:
        logger.exception('scheduled audits run failed: %s', e)
        return Response(
            {'success': False, 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@require_tenant
@tenant_filter
def list_pending_audit_overdue_escalations(request):
    """Compliance managers: overdue audits needing auditor reassignment."""
    uid = RBACUtils.get_user_id_from_request(request)
    if uid is None or not _is_compliance_manager(uid):
        return Response(
            {'error': 'Compliance Manager access required'},
            status=status.HTTP_403_FORBIDDEN,
        )

    tenant_id = get_tenant_id_from_request(request)
    today = timezone.now().date()
    audits = (
        Audit.objects.filter(tenant_id=tenant_id, DueDate__lt=today)
        .exclude(Q(Status__iexact='completed') | Q(Status__iexact='Completed'))
        .select_related('Auditor', 'FrameworkId')
        .order_by('DueDate', 'AuditId')
    )

    items = []
    for audit in audits:
        fw = audit.FrameworkId
        auditor = audit.Auditor
        items.append(
            {
                'audit_id': audit.AuditId,
                'title': display_audit_title(audit.Title),
                'due_date': audit.DueDate.isoformat() if audit.DueDate else None,
                'status': audit.Status,
                'auditor_id': auditor.UserId if auditor else None,
                'auditor_name': auditor.UserName if auditor else None,
                'framework_id': fw.FrameworkId if fw else None,
                'framework_name': getattr(fw, 'FrameworkName', None) if fw else None,
                'overdue_escalated_at': (
                    audit.OverdueEscalatedAt.isoformat() if audit.OverdueEscalatedAt else None
                ),
            }
        )

    return Response({'success': True, 'escalations': items, 'count': len(items)})


@api_view(['GET'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@require_tenant
@tenant_filter
def list_pending_audit_review_escalations(request):
    """Audit managers: audits stuck in Under review needing reviewer assignment."""
    uid = RBACUtils.get_user_id_from_request(request)
    if uid is None or not _is_audit_manager(uid):
        return Response(
            {'error': 'Audit Manager access required'},
            status=status.HTTP_403_FORBIDDEN,
        )

    tenant_id = get_tenant_id_from_request(request)
    items = list_stalled_reviews_for_managers(tenant_id)
    return Response({'success': True, 'escalations': items, 'count': len(items)})


@api_view(['POST'])
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@require_tenant
@tenant_filter
def reassign_audit_reviewer(request, audit_id):
    """Audit manager reassigns reviewer for an audit under review."""
    from ...utils.auto_decrypt_helper import display_audit_title as _title

    requester_id = RBACUtils.get_user_id_from_request(request)
    if requester_id is None or not _is_audit_manager(requester_id):
        return Response({'error': 'Audit Manager access required'}, status=status.HTTP_403_FORBIDDEN)

    tenant_id = get_tenant_id_from_request(request)
    try:
        audit_id = int(audit_id)
    except (TypeError, ValueError):
        return Response({'error': 'Invalid audit id'}, status=status.HTTP_400_BAD_REQUEST)

    new_reviewer_id = request.data.get('new_reviewer_id') or request.data.get('reviewer_id')
    if not new_reviewer_id:
        return Response({'error': 'new_reviewer_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        audit = Audit.objects.get(AuditId=audit_id, tenant_id=tenant_id)
        new_reviewer = Users.objects.get(UserId=int(new_reviewer_id), tenant_id=tenant_id)
    except Audit.DoesNotExist:
        return Response({'error': 'Audit not found'}, status=status.HTTP_404_NOT_FOUND)
    except Users.DoesNotExist:
        return Response({'error': 'Reviewer not found'}, status=status.HTTP_404_NOT_FOUND)

    status_val = (audit.Status or '').strip().lower()
    if status_val != 'under review':
        return Response(
            {'error': 'Audit must be Under review to reassign reviewer'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    audit.Reviewer = new_reviewer
    audit.ReviewEscalatedAt = None
    audit.ReviewStartDate = timezone.now()
    audit.save(update_fields=['Reviewer', 'ReviewEscalatedAt', 'ReviewStartDate'])

    label = _title(audit.Title)
    store_in_app_audit_notification(
        new_reviewer.UserId,
        'audit_ready_for_review',
        'Audit assigned for your review',
        (
            f'Audit "{label}" (ID {audit.AuditId}) was assigned to you for review. '
            f'Please complete your review in the Reviewer workspace.'
        ),
        audit.FrameworkId_id,
        {
            'audit_id': audit.AuditId,
            'action_url': '/auditor/reviews',
        },
    )

    return Response(
        {
            'success': True,
            'audit_id': audit.AuditId,
            'reviewer_id': new_reviewer.UserId,
            'message': 'Reviewer reassigned successfully',
        },
        status=status.HTTP_200_OK,
    )
