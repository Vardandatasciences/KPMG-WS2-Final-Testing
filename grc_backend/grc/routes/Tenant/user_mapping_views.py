"""
User Mapping API Views - Phase 2.5

Endpoints for mapping/unmapping users to tenants and entities.
"""

import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view

from ...models import (
    Tenant, Users, TenantUserMapping, UserEntityMapping, Entity, TenantAuditLog
)
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
            entity_type='user',
            entity_id=entity_id,
            entity_name=entity_name,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        )
    except Exception as exc:
        logger.warning(f"[user_mapping_views] Audit log failed: {exc}")


def _tum_to_dict(m):
    return {
        'id': m.id,
        'tenant_id': m.tenant_id,
        'user_id': m.user_id,
        'role': m.role,
        'is_primary': m.is_primary,
        'status': m.status,
        'assigned_at': m.assigned_at.isoformat() if m.assigned_at else None,
    }


def _uem_to_dict(m):
    return {
        'id': m.id,
        'user_id': m.user_id,
        'entity_id': m.entity_id,
        'tenant_id': m.tenant_id,
        'role': m.role,
        'access_level': m.access_level,
        'status': m.status,
        'assigned_at': m.assigned_at.isoformat() if m.assigned_at else None,
    }


# ──────────────────────────────────────────────────────────────
# Tenant-level user mapping
# ──────────────────────────────────────────────────────────────

@api_view(['POST'])
@require_tenant
def map_user_to_tenant(request, tenant_id):
    """
    POST /api/tenants/{tenant_id}/map-user/
    Body: { "user_id": <int>, "role": "<str>", "is_primary": <bool> }
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
    if not tenant:
        return JsonResponse({'status': 'error', 'message': 'Tenant not found'}, status=404)

    try:
        data = request.data if hasattr(request, 'data') else {}
        user_id = data.get('user_id')
        role = data.get('role', 'Viewer')

        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'user_id is required'}, status=400)

        user = Users.objects.filter(UserId=user_id).first()
        if not user:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)

        # Check for existing active mapping
        existing = TenantUserMapping.objects.filter(tenant_id=tenant_id, user_id=user_id).first()
        if existing:
            if existing.is_deleted:
                existing.is_deleted = False
                existing.status = 'active'
                existing.role = role
                existing.save()
                _log_audit(tenant_id, 'MAP_USER', user_id,
                           getattr(user, 'UserName', str(user_id)),
                           None, _tum_to_dict(existing), request)
                return JsonResponse({
                    'status': 'success',
                    'message': 'User re-mapped to tenant',
                    'mapping': _tum_to_dict(existing),
                })
            return JsonResponse(
                {'status': 'error', 'message': 'User already mapped to this tenant'}, status=400
            )

        performer_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))

        mapping = TenantUserMapping.objects.create(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            is_primary=bool(data.get('is_primary', False)),
            assigned_by_id=performer_id,
            status='active',
        )

        _log_audit(tenant_id, 'MAP_USER', user_id,
                   getattr(user, 'UserName', str(user_id)),
                   None, _tum_to_dict(mapping), request)

        return JsonResponse({
            'status': 'success',
            'message': 'User mapped to tenant',
            'mapping': _tum_to_dict(mapping),
        }, status=201)
    except Exception as exc:
        logger.error(f"[user_mapping_views] map_user_to_tenant error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['DELETE'])
@require_tenant
def unmap_user_from_tenant(request, tenant_id, user_id):
    """
    DELETE /api/tenants/{tenant_id}/unmap-user/{user_id}/
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    mapping = TenantUserMapping.objects.filter(
        tenant_id=tenant_id, user_id=user_id, is_deleted=False
    ).first()
    if not mapping:
        return JsonResponse({'status': 'error', 'message': 'Mapping not found'}, status=404)

    try:
        old = _tum_to_dict(mapping)
        mapping.is_deleted = True
        mapping.status = 'inactive'
        mapping.save()

        _log_audit(tenant_id, 'UNMAP_USER', user_id, str(user_id),
                   old, {'status': 'inactive'}, request)

        return JsonResponse({'status': 'success', 'message': 'User unmapped from tenant'})
    except Exception as exc:
        logger.error(f"[user_mapping_views] unmap_user_from_tenant error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['PUT'])
@require_tenant
def set_primary_user(request, tenant_id, user_id):
    """
    PUT /api/tenants/{tenant_id}/set-primary-user/{user_id}/
    Sets this mapping as the user's primary tenant.
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    mapping = TenantUserMapping.objects.filter(
        tenant_id=tenant_id, user_id=user_id, is_deleted=False
    ).first()
    if not mapping:
        return JsonResponse({'status': 'error', 'message': 'Mapping not found'}, status=404)

    try:
        # Clear other primary mappings for this user
        TenantUserMapping.objects.filter(user_id=user_id, is_primary=True).update(is_primary=False)
        mapping.is_primary = True
        mapping.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Primary tenant updated',
            'mapping': _tum_to_dict(mapping),
        })
    except Exception as exc:
        logger.error(f"[user_mapping_views] set_primary_user error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


# ──────────────────────────────────────────────────────────────
# Entity-level user mapping
# ──────────────────────────────────────────────────────────────

@api_view(['POST'])
@require_tenant
def map_user_to_entity(request, entity_id):
    """
    POST /api/entities/{entity_id}/map-user/
    Body: { "user_id": <int>, "role": "<str>", "access_level": "read|write|admin" }
    """
    tenant_id = get_tenant_id_from_request(request)

    entity = Entity.objects.filter(Id=entity_id, IsActive=True).first()
    if not entity:
        return JsonResponse({'status': 'error', 'message': 'Entity not found'}, status=404)

    try:
        data = request.data if hasattr(request, 'data') else {}
        user_id = data.get('user_id')
        role = data.get('role', 'Viewer')
        access_level = data.get('access_level', 'read')

        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'user_id is required'}, status=400)

        user = Users.objects.filter(UserId=user_id).first()
        if not user:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)

        existing = UserEntityMapping.objects.filter(user_id=user_id, entity_id=entity_id).first()
        if existing:
            if existing.is_deleted:
                existing.is_deleted = False
                existing.status = 'active'
                existing.role = role
                existing.access_level = access_level
                existing.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'User re-mapped to entity',
                    'mapping': _uem_to_dict(existing),
                })
            return JsonResponse(
                {'status': 'error', 'message': 'User already mapped to this entity'}, status=400
            )

        performer_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))

        mapping = UserEntityMapping.objects.create(
            user_id=user_id,
            entity_id=entity_id,
            tenant_id=tenant_id,
            role=role,
            access_level=access_level,
            assigned_by_id=performer_id,
            status='active',
        )

        _log_audit(tenant_id, 'MAP_USER', user_id,
                   getattr(user, 'UserName', str(user_id)),
                   None, _uem_to_dict(mapping), request)

        return JsonResponse({
            'status': 'success',
            'message': 'User mapped to entity',
            'mapping': _uem_to_dict(mapping),
        }, status=201)
    except Exception as exc:
        logger.error(f"[user_mapping_views] map_user_to_entity error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


# ──────────────────────────────────────────────────────────────
# User context endpoints
# ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@require_tenant
def user_tenants(request, user_id):
    """
    GET /api/users/{user_id}/tenants/
    Returns all tenants the user belongs to.
    """
    try:
        mappings = TenantUserMapping.objects.filter(
            user_id=user_id, is_deleted=False
        ).select_related('tenant')

        tenants = []
        for m in mappings:
            t = m.tenant
            tenants.append({
                'tenant_id': t.tenant_id,
                'name': t.name,
                'subdomain': t.subdomain,
                'status': t.status,
                'role': m.role,
                'is_primary': m.is_primary,
            })

        return JsonResponse({'status': 'success', 'count': len(tenants), 'tenants': tenants})
    except Exception as exc:
        logger.error(f"[user_mapping_views] user_tenants error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET'])
@require_tenant
def user_entities(request, user_id):
    """
    GET /api/users/{user_id}/entities/
    Returns all entities the user has access to.
    """
    tenant_id = get_tenant_id_from_request(request)
    try:
        mappings = UserEntityMapping.objects.filter(
            user_id=user_id, tenant_id=tenant_id, is_deleted=False
        ).select_related('entity')

        entities = []
        for m in mappings:
            e = m.entity
            entities.append({
                'entity_id': e.Id,
                'entity_name': e.EntityName,
                'entity_type': e.EntityType,
                'access_level': m.access_level,
                'role': m.role,
                'status': m.status,
            })

        return JsonResponse({'status': 'success', 'count': len(entities), 'entities': entities})
    except Exception as exc:
        logger.error(f"[user_mapping_views] user_entities error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)
