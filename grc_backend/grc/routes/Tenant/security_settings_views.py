"""
Security Settings API Views - Phase 2.7

Endpoints for managing per-tenant security policies.
"""

import logging
import ipaddress
from django.http import JsonResponse
from rest_framework.decorators import api_view

from ...models import Tenant, TenantSecuritySettings, Users, TenantAuditLog
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
            entity_type='security',
            entity_id=entity_id,
            entity_name=entity_name,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        )
    except Exception as exc:
        logger.warning(f"[security_settings_views] Audit log failed: {exc}")


def _settings_to_dict(s):
    return {
        'id': s.id,
        'tenant_id': s.tenant_id,
        'mfa_required': s.mfa_required,
        'mfa_methods': s.mfa_methods,
        'sso_enabled': s.sso_enabled,
        'sso_provider': s.sso_provider,
        'sso_config': s.sso_config,
        'allowed_email_domains': s.allowed_email_domains,
        'ip_restriction_enabled': s.ip_restriction_enabled,
        'allowed_ip_ranges': s.allowed_ip_ranges,
        'session_timeout_minutes': s.session_timeout_minutes,
        'password_expiry_days': s.password_expiry_days,
        'export_allowed': s.export_allowed,
        'export_requires_approval': s.export_requires_approval,
        'updated_at': s.updated_at.isoformat() if s.updated_at else None,
    }


def _get_or_create_settings(tenant_id):
    settings, _ = TenantSecuritySettings.objects.get_or_create(
        tenant_id=tenant_id,
        defaults={
            'mfa_required': False,
            'session_timeout_minutes': 30,
            'password_expiry_days': 90,
        },
    )
    return settings


@api_view(['GET', 'PUT'])
@require_tenant
def security_settings(request, tenant_id):
    """
    GET /api/tenants/{tenant_id}/security-settings/
    PUT /api/tenants/{tenant_id}/security-settings/
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
    if not tenant:
        return JsonResponse({'status': 'error', 'message': 'Tenant not found'}, status=404)

    if request.method == 'GET':
        try:
            s = _get_or_create_settings(tenant_id)
            return JsonResponse({'status': 'success', 'security_settings': _settings_to_dict(s)})
        except Exception as exc:
            logger.error(f"[security_settings_views] GET error: {exc}")
            return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)

    # PUT – update
    try:
        data = request.data if hasattr(request, 'data') else {}
        s = _get_or_create_settings(tenant_id)
        old = _settings_to_dict(s)

        updatable = [
            'mfa_required', 'mfa_methods', 'sso_enabled', 'sso_provider', 'sso_config',
            'allowed_email_domains', 'ip_restriction_enabled', 'allowed_ip_ranges',
            'session_timeout_minutes', 'password_expiry_days',
            'export_allowed', 'export_requires_approval',
        ]
        for field in updatable:
            if field in data:
                setattr(s, field, data[field])

        performer_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))
        s.updated_by_id = performer_id
        s.save()

        _log_audit(tenant_id, 'UPDATE', s.id, 'Security Settings',
                   old, _settings_to_dict(s), request)

        return JsonResponse({
            'status': 'success',
            'message': 'Security settings updated',
            'security_settings': _settings_to_dict(s),
        })
    except Exception as exc:
        logger.error(f"[security_settings_views] PUT error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['POST'])
@require_tenant
def test_ip_restriction(request, tenant_id):
    """
    POST /api/tenants/{tenant_id}/test-ip-restriction/
    Body: { "ip_address": "1.2.3.4" }
    Returns whether the IP would be allowed under current rules.
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    try:
        data = request.data if hasattr(request, 'data') else {}
        test_ip = data.get('ip_address')
        if not test_ip:
            return JsonResponse({'status': 'error', 'message': 'ip_address is required'}, status=400)

        s = _get_or_create_settings(tenant_id)

        if not s.ip_restriction_enabled:
            return JsonResponse({
                'status': 'success',
                'allowed': True,
                'reason': 'IP restriction is not enabled for this tenant',
            })

        allowed = False
        try:
            client = ipaddress.ip_address(test_ip)
            for cidr in s.allowed_ip_ranges:
                try:
                    if client in ipaddress.ip_network(cidr, strict=False):
                        allowed = True
                        break
                except ValueError:
                    continue
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid IP address'}, status=400)

        return JsonResponse({
            'status': 'success',
            'ip_address': test_ip,
            'allowed': allowed,
            'allowed_ranges': s.allowed_ip_ranges,
        })
    except Exception as exc:
        logger.error(f"[security_settings_views] test_ip_restriction error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET'])
@require_tenant
def security_audit(request, tenant_id):
    """
    GET /api/tenants/{tenant_id}/security-audit/
    Returns the audit history for security setting changes.
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    try:
        logs = TenantAuditLog.objects.filter(
            tenant_id=tenant_id, entity_type='security'
        ).order_by('-performed_at')[:100]

        return JsonResponse({
            'status': 'success',
            'count': logs.count(),
            'audit_logs': [
                {
                    'id': log.id,
                    'action_type': log.action_type,
                    'entity_name': log.entity_name,
                    'old_value': log.old_value,
                    'new_value': log.new_value,
                    'performed_by_id': log.performed_by_id,
                    'performed_at': log.performed_at.isoformat(),
                    'ip_address': log.ip_address,
                }
                for log in logs
            ],
        })
    except Exception as exc:
        logger.error(f"[security_settings_views] security_audit error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)
