"""
Support Access API Views - Phase 2.9

Endpoints for the support-team access request / approval workflow.
"""

import logging
import secrets
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view

from ...models import Tenant, SupportAccessRequest, Users, TenantAuditLog
from ...tenant_utils import require_tenant, get_tenant_id_from_request

logger = logging.getLogger(__name__)


def _log_audit(tenant_id, action_type, entity_id, entity_name,
               old_value, new_value, request):
    try:
        user = getattr(request, 'user', None)
        performed_by = None
        if user and user.is_authenticated:
            uid = getattr(user, 'UserId', getattr(user, 'id', None))
            if uid:
                performed_by = Users.objects.filter(UserId=uid).first()
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '')
        )
        TenantAuditLog.objects.create(
            tenant_id=tenant_id,
            action_type=action_type,
            entity_type='support_access',
            entity_id=entity_id,
            entity_name=entity_name,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        )
    except Exception as exc:
        logger.warning(f"[support_access_views] Audit log failed: {exc}")


def _sar_to_dict(s):
    return {
        'id': s.id,
        'tenant_id': s.tenant_id,
        'support_user_id': s.support_user_id,
        'request_reason': s.request_reason,
        'requested_at': s.requested_at.isoformat() if s.requested_at else None,
        'approved_by_id': s.approved_by_id,
        'approved_at': s.approved_at.isoformat() if s.approved_at else None,
        'valid_from': s.valid_from.isoformat() if s.valid_from else None,
        'valid_to': s.valid_to.isoformat() if s.valid_to else None,
        'status': s.status,
        'is_active': s.is_active,
        'last_used_at': s.last_used_at.isoformat() if s.last_used_at else None,
        'created_at': s.created_at.isoformat() if s.created_at else None,
    }


@api_view(['POST'])
@require_tenant
def request_support_access(request):
    """
    POST /api/support-access/request/
    Body: { "tenant_id": <int>, "request_reason": "<str>",
            "valid_from": "<ISO datetime>", "valid_to": "<ISO datetime>" }
    """
    try:
        data = request.data if hasattr(request, 'data') else {}
        tenant_id = data.get('tenant_id') or get_tenant_id_from_request(request)
        reason = data.get('request_reason')

        if not tenant_id:
            return JsonResponse({'status': 'error', 'message': 'tenant_id is required'}, status=400)
        if not reason:
            return JsonResponse(
                {'status': 'error', 'message': 'request_reason is required'}, status=400
            )

        tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
        if not tenant:
            return JsonResponse({'status': 'error', 'message': 'Tenant not found'}, status=404)

        support_user_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))

        sar = SupportAccessRequest.objects.create(
            tenant_id=tenant_id,
            support_user_id=support_user_id,
            request_reason=reason,
            valid_from=data.get('valid_from'),
            valid_to=data.get('valid_to'),
            status='pending',
            is_active=True,
        )

        _log_audit(tenant_id, 'CREATE', sar.id, f'SupportAccess #{sar.id}',
                   None, _sar_to_dict(sar), request)

        return JsonResponse({
            'status': 'success',
            'message': 'Support access request submitted',
            'request': _sar_to_dict(sar),
        }, status=201)
    except Exception as exc:
        logger.error(f"[support_access_views] request_support_access error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET'])
@require_tenant
def pending_support_requests(request, tenant_id):
    """
    GET /api/tenant-admins/{tenant_id}/support-requests/
    Returns all pending support access requests for the tenant.
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    try:
        requests_qs = SupportAccessRequest.objects.filter(
            tenant_id=tenant_id, status='pending'
        ).order_by('-requested_at')

        return JsonResponse({
            'status': 'success',
            'count': requests_qs.count(),
            'requests': [_sar_to_dict(r) for r in requests_qs],
        })
    except Exception as exc:
        logger.error(f"[support_access_views] pending_support_requests error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['POST'])
@require_tenant
def approve_support_access(request, request_id):
    """
    POST /api/support-access/{request_id}/approve/
    Body (optional): { "valid_from": "<ISO>", "valid_to": "<ISO>" }
    """
    tenant_id = get_tenant_id_from_request(request)

    sar = SupportAccessRequest.objects.filter(
        id=request_id, tenant_id=tenant_id, status='pending'
    ).first()
    if not sar:
        return JsonResponse(
            {'status': 'error', 'message': 'Support access request not found or already processed'},
            status=404,
        )

    try:
        data = request.data if hasattr(request, 'data') else {}
        approver_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))
        old = _sar_to_dict(sar)

        sar.status = 'approved'
        sar.approved_by_id = approver_id
        sar.approved_at = timezone.now()
        sar.access_token = secrets.token_urlsafe(32)
        if data.get('valid_from'):
            sar.valid_from = data['valid_from']
        if data.get('valid_to'):
            sar.valid_to = data['valid_to']

        sar.save()
        _log_audit(tenant_id, 'UPDATE', sar.id, f'SupportAccess #{sar.id}',
                   old, _sar_to_dict(sar), request)

        return JsonResponse({
            'status': 'success',
            'message': 'Support access approved',
            'request': _sar_to_dict(sar),
        })
    except Exception as exc:
        logger.error(f"[support_access_views] approve_support_access error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['POST'])
@require_tenant
def revoke_support_access(request, request_id):
    """
    POST /api/support-access/{request_id}/revoke/
    """
    tenant_id = get_tenant_id_from_request(request)

    sar = SupportAccessRequest.objects.filter(
        id=request_id, tenant_id=tenant_id
    ).exclude(status='revoked').first()
    if not sar:
        return JsonResponse(
            {'status': 'error', 'message': 'Support access request not found or already revoked'},
            status=404,
        )

    try:
        old = _sar_to_dict(sar)
        sar.status = 'revoked'
        sar.is_active = False
        sar.access_token = None
        sar.save()

        _log_audit(tenant_id, 'UPDATE', sar.id, f'SupportAccess #{sar.id}',
                   old, _sar_to_dict(sar), request)

        return JsonResponse({'status': 'success', 'message': 'Support access revoked'})
    except Exception as exc:
        logger.error(f"[support_access_views] revoke_support_access error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET'])
@require_tenant
def my_support_accesses(request):
    """
    GET /api/support-access/my-accesses/
    Returns all active support access grants for the authenticated support user.
    """
    try:
        user_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))
        accesses = SupportAccessRequest.objects.filter(
            support_user_id=user_id, status='approved', is_active=True
        ).order_by('-approved_at')

        return JsonResponse({
            'status': 'success',
            'count': accesses.count(),
            'accesses': [_sar_to_dict(a) for a in accesses],
        })
    except Exception as exc:
        logger.error(f"[support_access_views] my_support_accesses error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET'])
@require_tenant
def support_history(request, tenant_id):
    """
    GET /api/tenants/{tenant_id}/support-history/
    Full history of support access requests for the tenant.
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    try:
        history = SupportAccessRequest.objects.filter(
            tenant_id=tenant_id
        ).order_by('-requested_at')

        return JsonResponse({
            'status': 'success',
            'count': history.count(),
            'history': [_sar_to_dict(r) for r in history],
        })
    except Exception as exc:
        logger.error(f"[support_access_views] support_history error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)
