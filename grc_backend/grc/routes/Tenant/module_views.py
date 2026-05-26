"""
Module Management API Views - Phase 2.6

Endpoints for enabling/disabling GRC modules per tenant.
"""

import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view

from ...models import Tenant, TenantModule, Users, TenantAuditLog
from ...tenant_utils import require_tenant, get_tenant_id_from_request

logger = logging.getLogger(__name__)

ALL_MODULES = ['framework', 'policy', 'compliance', 'audit', 'risk', 'incident', 'event']


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
            entity_type='module',
            entity_id=entity_id,
            entity_name=entity_name,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        )
    except Exception as exc:
        logger.warning(f"[module_views] Audit log failed: {exc}")


def _module_to_dict(m):
    return {
        'id': m.id,
        'tenant_id': m.tenant_id,
        'module_code': m.module_code,
        'is_enabled': m.is_enabled,
        'license_tier': m.license_tier,
        'effective_from': m.effective_from.isoformat() if m.effective_from else None,
        'effective_to': m.effective_to.isoformat() if m.effective_to else None,
        'user_limit': m.user_limit,
        'storage_limit_gb': m.storage_limit_gb,
        'api_limit': m.api_limit,
        'ai_limit': m.ai_limit,
        'configured_at': m.configured_at.isoformat() if m.configured_at else None,
        'updated_at': m.updated_at.isoformat() if m.updated_at else None,
    }


@api_view(['GET', 'PUT'])
@require_tenant
def tenant_modules(request, tenant_id):
    """
    GET /api/tenants/{tenant_id}/modules/  – List all module configs for tenant
    PUT /api/tenants/{tenant_id}/modules/  – Bulk update module enabled state
        Body: { "modules": [ {"module_code": "risk", "is_enabled": true, ...}, ... ] }
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
    if not tenant:
        return JsonResponse({'status': 'error', 'message': 'Tenant not found'}, status=404)

    if request.method == 'GET':
        try:
            modules = TenantModule.objects.filter(tenant_id=tenant_id)
            return JsonResponse({
                'status': 'success',
                'modules': [_module_to_dict(m) for m in modules],
            })
        except Exception as exc:
            logger.error(f"[module_views] list error: {exc}")
            return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)

    # PUT – bulk update
    try:
        data = request.data if hasattr(request, 'data') else {}
        updates = data.get('modules', [])
        if not isinstance(updates, list):
            return JsonResponse(
                {'status': 'error', 'message': '"modules" must be a list'}, status=400
            )

        performer_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))
        results = []

        for item in updates:
            module_code = item.get('module_code')
            if module_code not in ALL_MODULES:
                continue

            module, _ = TenantModule.objects.get_or_create(
                tenant_id=tenant_id,
                module_code=module_code,
                defaults={'configured_by_id': performer_id},
            )
            old = _module_to_dict(module)

            was_enabled = module.is_enabled
            if 'is_enabled' in item:
                module.is_enabled = bool(item['is_enabled'])
            if 'license_tier' in item:
                module.license_tier = item['license_tier']
            if 'user_limit' in item:
                module.user_limit = item['user_limit']
            if 'storage_limit_gb' in item:
                module.storage_limit_gb = item['storage_limit_gb']
            if 'api_limit' in item:
                module.api_limit = item['api_limit']
            if 'ai_limit' in item:
                module.ai_limit = item['ai_limit']
            if 'effective_from' in item:
                module.effective_from = item['effective_from']
            if 'effective_to' in item:
                module.effective_to = item['effective_to']

            module.save()

            action = ('ENABLE_MODULE' if module.is_enabled and not was_enabled
                      else 'DISABLE_MODULE' if not module.is_enabled and was_enabled
                      else 'UPDATE')
            _log_audit(tenant_id, action, module.id, module_code,
                       old, _module_to_dict(module), request)
            results.append(_module_to_dict(module))

        return JsonResponse({
            'status': 'success',
            'message': f'{len(results)} module(s) updated',
            'modules': results,
        })
    except Exception as exc:
        logger.error(f"[module_views] bulk update error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET'])
def available_modules(request):
    """
    GET /api/modules/available/
    Returns the list of all available module codes (no auth required).
    """
    return JsonResponse({
        'status': 'success',
        'modules': [
            {'code': 'framework',   'label': 'Framework'},
            {'code': 'policy',      'label': 'Policy'},
            {'code': 'compliance',  'label': 'Compliance'},
            {'code': 'audit',       'label': 'Audit'},
            {'code': 'risk',        'label': 'Risk'},
            {'code': 'incident',    'label': 'Incident'},
            {'code': 'event',       'label': 'Event'},
        ],
    })


@api_view(['GET'])
@require_tenant
def module_status(request, tenant_id, module_code):
    """
    GET /api/tenants/{tenant_id}/module-status/{module}/
    Returns whether a specific module is enabled.
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    if module_code not in ALL_MODULES:
        return JsonResponse({'status': 'error', 'message': 'Unknown module'}, status=400)

    try:
        module = TenantModule.objects.filter(
            tenant_id=tenant_id, module_code=module_code
        ).first()
        is_enabled = module.is_enabled if module else False

        return JsonResponse({
            'status': 'success',
            'module_code': module_code,
            'is_enabled': is_enabled,
            'details': _module_to_dict(module) if module else None,
        })
    except Exception as exc:
        logger.error(f"[module_views] module_status error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)
