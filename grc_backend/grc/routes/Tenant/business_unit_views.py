"""
Business Unit API Views - Phase 2.3

Endpoints for managing TenantBusinessUnits scoped to entities.
"""

import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view

from ...models import TenantBusinessUnit, Entity, Users, TenantAuditLog
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
            entity_type='business_unit',
            entity_id=entity_id,
            entity_name=entity_name,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        )
    except Exception as exc:
        logger.warning(f"[business_unit_views] Audit log failed: {exc}")


def _bu_to_dict(bu):
    return {
        'id': bu.id,
        'tenant_id': bu.tenant_id,
        'entity_id': bu.entity_id,
        'name': bu.name,
        'code': bu.code,
        'description': bu.description,
        'head_user_id': bu.head_id,
        'parent_bu_id': bu.parent_bu_id,
        'status': bu.status,
        'is_deleted': bu.is_deleted,
        'created_at': bu.created_at.isoformat() if bu.created_at else None,
        'updated_at': bu.updated_at.isoformat() if bu.updated_at else None,
    }


@api_view(['GET', 'POST'])
@require_tenant
def bu_list_create(request, entity_id):
    """
    GET  /api/entities/{entity_id}/business-units/  – List BUs for entity
    POST /api/entities/{entity_id}/business-units/  – Create BU under entity
    """
    tenant_id = get_tenant_id_from_request(request)

    entity = Entity.objects.filter(Id=entity_id, IsActive=True).first()
    if not entity:
        return JsonResponse({'status': 'error', 'message': 'Entity not found'}, status=404)

    if request.method == 'GET':
        try:
            bus = TenantBusinessUnit.objects.filter(
                entity_id=entity_id,
                is_deleted=False,
            )
            return JsonResponse({
                'status': 'success',
                'count': bus.count(),
                'business_units': [_bu_to_dict(b) for b in bus],
            })
        except Exception as exc:
            logger.error(f"[business_unit_views] list error: {exc}")
            return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)

    # POST – create
    try:
        data = request.data if hasattr(request, 'data') else {}
        name = data.get('name')
        code = data.get('code')

        if not name or not code:
            return JsonResponse(
                {'status': 'error', 'message': 'name and code are required'}, status=400
            )

        if TenantBusinessUnit.objects.filter(code=code).exists():
            return JsonResponse(
                {'status': 'error', 'message': f'Code "{code}" already exists'}, status=400
            )

        bu = TenantBusinessUnit.objects.create(
            tenant_id=tenant_id,
            entity_id=entity_id,
            name=name,
            code=code,
            description=data.get('description'),
            head_id=data.get('head_user_id'),
            parent_bu_id=data.get('parent_bu_id'),
            status=data.get('status', 'active'),
        )

        _log_audit(tenant_id, 'CREATE', bu.id, bu.name, None, _bu_to_dict(bu), request)

        return JsonResponse({
            'status': 'success',
            'message': 'Business unit created',
            'business_unit': _bu_to_dict(bu),
        }, status=201)
    except Exception as exc:
        logger.error(f"[business_unit_views] create error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET', 'PUT', 'DELETE'])
@require_tenant
def bu_detail(request, bu_id):
    """
    GET    /api/business-units/{bu_id}/
    PUT    /api/business-units/{bu_id}/
    DELETE /api/business-units/{bu_id}/
    """
    tenant_id = get_tenant_id_from_request(request)

    bu = TenantBusinessUnit.objects.filter(id=bu_id, tenant_id=tenant_id, is_deleted=False).first()
    if not bu:
        return JsonResponse({'status': 'error', 'message': 'Business unit not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'status': 'success', 'business_unit': _bu_to_dict(bu)})

    if request.method == 'PUT':
        try:
            data = request.data if hasattr(request, 'data') else {}
            old = _bu_to_dict(bu)

            if 'name' in data:
                bu.name = data['name']
            if 'description' in data:
                bu.description = data['description']
            if 'head_user_id' in data:
                bu.head_id = data['head_user_id']
            if 'parent_bu_id' in data:
                bu.parent_bu_id = data['parent_bu_id']
            if 'status' in data:
                bu.status = data['status']

            bu.save()
            _log_audit(tenant_id, 'UPDATE', bu.id, bu.name, old, _bu_to_dict(bu), request)

            return JsonResponse({
                'status': 'success',
                'message': 'Business unit updated',
                'business_unit': _bu_to_dict(bu),
            })
        except Exception as exc:
            logger.error(f"[business_unit_views] update error: {exc}")
            return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)

    # DELETE – soft delete
    try:
        old = _bu_to_dict(bu)
        bu.is_deleted = True
        bu.save()
        _log_audit(tenant_id, 'DELETE', bu.id, bu.name, old, {'is_deleted': True}, request)
        return JsonResponse({'status': 'success', 'message': 'Business unit deleted'})
    except Exception as exc:
        logger.error(f"[business_unit_views] delete error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)
