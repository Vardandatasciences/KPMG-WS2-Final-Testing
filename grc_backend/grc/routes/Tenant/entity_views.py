"""
Entity Management API Views - Phase 2.2

Endpoints for managing entities (legal entities, subsidiaries, branches)
scoped under a tenant.
"""

import logging
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from ...models import (
    Tenant, Entity, Users, UserEntityMapping, TenantAuditLog, Department
)
from ...tenant_utils import require_tenant, get_tenant_id_from_request

logger = logging.getLogger(__name__)


def _log_audit(tenant_id, action_type, entity_type, entity_id, entity_name,
               old_value, new_value, request):
    try:
        user = getattr(request, 'user', None)
        performed_by = None
        if user and user.is_authenticated:
            user_id = getattr(user, 'UserId', getattr(user, 'id', None))
            if user_id:
                performed_by = Users.objects.filter(UserId=user_id).first()
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR', '')
        )
        TenantAuditLog.objects.create(
            tenant_id=tenant_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        )
    except Exception as exc:
        logger.warning(f"[entity_views] Audit log failed: {exc}")


def _get_plain(entity, field_name):
    """Return decrypted value if encrypted, otherwise plain value. Never returns ciphertext."""
    try:
        raw = getattr(entity, field_name, None)
        if raw is None:
            return ''
        # Use mixin's decryption if available
        if hasattr(entity, '_get_decrypted_value'):
            try:
                decrypted = entity._get_decrypted_value(field_name)
                if decrypted:
                    return str(decrypted)
            except Exception:
                pass
        return str(raw) if raw else ''
    except Exception:
        return ''


def _entity_to_dict(entity):
    return {
        'id': entity.Id,
        'name': _get_plain(entity, 'EntityName'),
        'entity_name': _get_plain(entity, 'EntityName'),
        'code': _get_plain(entity, 'EntityCode') if hasattr(entity, 'EntityCode') else '',
        'entity_type': entity.EntityType or '',
        'status': 'active' if entity.IsActive else 'inactive',
        'parent_entity_id': entity.ParentEntityId,
        'location_id': entity.LocationId,
        'is_active': entity.IsActive,
        'created_date': entity.CreatedDate.isoformat() if entity.CreatedDate else None,
        'framework_id': entity.FrameworkId_id,
        'description': _get_plain(entity, 'Description') if hasattr(entity, 'Description') else '',
    }


@api_view(['GET', 'POST'])
@require_tenant
def entity_list_create(request, tenant_id):
    """
    GET  /api/tenants/{tenant_id}/entities/  – List entities for tenant
    POST /api/tenants/{tenant_id}/entities/  – Create entity under tenant
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
    if not tenant:
        return JsonResponse({'status': 'error', 'message': 'Tenant not found'}, status=404)

    if request.method == 'GET':
        try:
            # Entities linked via UserEntityMapping for this tenant
            entity_ids = UserEntityMapping.objects.filter(
                tenant_id=tenant_id, is_deleted=False
            ).values_list('entity_id', flat=True).distinct()

            entities = Entity.objects.filter(Id__in=entity_ids, IsActive=True)
            return JsonResponse({
                'status': 'success',
                'count': entities.count(),
                'entities': [_entity_to_dict(e) for e in entities],
            })
        except Exception as exc:
            logger.error(f"[entity_views] list error: {exc}")
            return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)

    # POST – create
    try:
        data = request.data if hasattr(request, 'data') else {}
        entity_name = data.get('name') or data.get('entity_name') or data.get('EntityName')
        entity_code = data.get('code') or data.get('entity_code') or data.get('EntityCode', '')
        entity_type = data.get('entity_type') or data.get('EntityType', 'Branch')
        description = data.get('description') or data.get('Description', '')
        location_id = data.get('location_id') or data.get('LocationId', 1)
        framework_id = data.get('framework_id') or data.get('FrameworkId')
        parent_entity_id = data.get('parent_entity_id') or data.get('ParentEntityId')

        if not entity_name:
            return JsonResponse({'status': 'error', 'message': 'entity_name is required'}, status=400)
        if not framework_id:
            return JsonResponse({'status': 'error', 'message': 'framework_id is required'}, status=400)

        create_kwargs = dict(
            EntityName=entity_name,
            EntityType=entity_type,
            LocationId=int(location_id),
            FrameworkId_id=int(framework_id),
            ParentEntityId=int(parent_entity_id) if parent_entity_id else None,
            IsActive=True,
            CreatedDate=timezone.now(),
        )
        if hasattr(Entity, 'EntityCode'):
            create_kwargs['EntityCode'] = entity_code
        if hasattr(Entity, 'Description'):
            create_kwargs['Description'] = description
        entity = Entity.objects.create(**create_kwargs)

        _log_audit(tenant_id, 'CREATE', 'entity', entity.Id, entity.EntityName,
                   None, _entity_to_dict(entity), request)

        return JsonResponse({
            'status': 'success',
            'message': 'Entity created successfully',
            'entity': _entity_to_dict(entity),
        }, status=201)
    except Exception as exc:
        logger.error(f"[entity_views] create error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET'])
@require_tenant
def entity_tree(request, tenant_id):
    """
    GET /api/tenants/{tenant_id}/entities/tree/
    Returns the full entity hierarchy as a nested tree.
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    try:
        entity_ids = UserEntityMapping.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).values_list('entity_id', flat=True).distinct()

        entities = list(Entity.objects.filter(Id__in=entity_ids, IsActive=True))

        def build_tree(parent_id):
            children = [e for e in entities if e.ParentEntityId == parent_id]
            return [
                {**_entity_to_dict(e), 'children': build_tree(e.Id)}
                for e in children
            ]

        roots = [e for e in entities if not e.ParentEntityId]
        tree = [
            {**_entity_to_dict(e), 'children': build_tree(e.Id)}
            for e in roots
        ]

        return JsonResponse({'status': 'success', 'tree': tree})
    except Exception as exc:
        logger.error(f"[entity_views] tree error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET', 'PUT', 'DELETE'])
@require_tenant
def entity_detail(request, entity_id):
    """
    GET    /api/entities/{entity_id}/  – Retrieve entity
    PUT    /api/entities/{entity_id}/  – Update entity
    DELETE /api/entities/{entity_id}/  – Soft delete entity
    """
    tenant_id = get_tenant_id_from_request(request)

    entity = Entity.objects.filter(Id=entity_id).first()
    if not entity:
        return JsonResponse({'status': 'error', 'message': 'Entity not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'status': 'success', 'entity': _entity_to_dict(entity)})

    if request.method == 'PUT':
        try:
            data = request.data if hasattr(request, 'data') else {}
            old = _entity_to_dict(entity)

            if 'name' in data or 'entity_name' in data:
                entity.EntityName = data.get('name') or data.get('entity_name')
            if 'code' in data and hasattr(entity, 'EntityCode'):
                entity.EntityCode = data['code']
            if 'description' in data and hasattr(entity, 'Description'):
                entity.Description = data['description']
            if 'entity_type' in data:
                entity.EntityType = data['entity_type']
            if 'location_id' in data:
                entity.LocationId = int(data['location_id'])
            if 'parent_entity_id' in data:
                entity.ParentEntityId = int(data['parent_entity_id']) if data['parent_entity_id'] else None
            if 'is_active' in data:
                entity.IsActive = bool(data['is_active'])

            entity.save()
            _log_audit(tenant_id, 'UPDATE', 'entity', entity.Id, entity.EntityName,
                       old, _entity_to_dict(entity), request)

            return JsonResponse({
                'status': 'success',
                'message': 'Entity updated',
                'entity': _entity_to_dict(entity),
            })
        except Exception as exc:
            logger.error(f"[entity_views] update error: {exc}")
            return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)

    # DELETE – soft delete
    try:
        old = _entity_to_dict(entity)
        entity.IsActive = False
        entity.save()
        _log_audit(tenant_id, 'DELETE', 'entity', entity.Id, entity.EntityName,
                   old, {'is_active': False}, request)

        return JsonResponse({'status': 'success', 'message': 'Entity deactivated'})
    except Exception as exc:
        logger.error(f"[entity_views] delete error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET'])
@require_tenant
def entity_users(request, entity_id):
    """
    GET /api/entities/{entity_id}/users/
    Returns users mapped to a specific entity.
    """
    tenant_id = get_tenant_id_from_request(request)
    try:
        mappings = UserEntityMapping.objects.filter(
            entity_id=entity_id, tenant_id=tenant_id, is_deleted=False
        ).select_related('user')

        users = []
        for m in mappings:
            u = m.user
            users.append({
                'user_id': u.UserId,
                'username': getattr(u, 'UserName', ''),
                'email': getattr(u, 'Email', ''),
                'role': m.role,
                'access_level': m.access_level,
                'status': m.status,
                'assigned_at': m.assigned_at.isoformat() if m.assigned_at else None,
            })

        return JsonResponse({'status': 'success', 'count': len(users), 'users': users})
    except Exception as exc:
        logger.error(f"[entity_views] entity_users error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)
