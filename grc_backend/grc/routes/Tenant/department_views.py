"""
Department API Views - Phase 2.4

Endpoints for managing Departments scoped under Business Units.
"""

import logging
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view

from ...models import Department, TenantBusinessUnit, Users, TenantAuditLog, Framework
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
            entity_type='department',
            entity_id=entity_id,
            entity_name=entity_name,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by,
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        )
    except Exception as exc:
        logger.warning(f"[department_views] Audit log failed: {exc}")


def _dept_to_dict(dept):
    return {
        'department_id': dept.DepartmentId,
        'tenant_id': dept.tenant_id,
        'entity_id': dept.EntityId,
        'department_name': dept.DepartmentName,
        'department_head': dept.DepartmentHead,
        'business_unit_id': dept.BusinessUnitId,
        'is_active': dept.IsActive,
        'created_date': dept.CreatedDate.isoformat() if dept.CreatedDate else None,
        'framework_id': dept.FrameworkId_id,
    }


@api_view(['GET', 'POST'])
@require_tenant
def department_list_create(request, bu_id):
    """
    GET  /api/business-units/{bu_id}/departments/  – List departments for BU
    POST /api/business-units/{bu_id}/departments/  – Create department under BU
    """
    tenant_id = get_tenant_id_from_request(request)

    bu = TenantBusinessUnit.objects.filter(id=bu_id, tenant_id=tenant_id, is_deleted=False).first()
    if not bu:
        return JsonResponse({'status': 'error', 'message': 'Business unit not found'}, status=404)

    if request.method == 'GET':
        try:
            depts = Department.objects.filter(
                BusinessUnitId=bu_id,
                tenant_id=tenant_id,
                IsActive=True,
            )
            return JsonResponse({
                'status': 'success',
                'count': depts.count(),
                'departments': [_dept_to_dict(d) for d in depts],
            })
        except Exception as exc:
            logger.error(f"[department_views] list error: {exc}")
            return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)

    # POST – create
    try:
        data = request.data if hasattr(request, 'data') else {}
        dept_name = data.get('department_name') or data.get('DepartmentName')
        dept_head = data.get('department_head') or data.get('DepartmentHead', 0)
        framework_id = data.get('framework_id') or data.get('FrameworkId')

        if not dept_name:
            return JsonResponse(
                {'status': 'error', 'message': 'department_name is required'}, status=400
            )
        if not framework_id:
            return JsonResponse(
                {'status': 'error', 'message': 'framework_id is required'}, status=400
            )

        dept = Department.objects.create(
            tenant_id=tenant_id,
            EntityId=bu.entity_id,
            DepartmentName=dept_name,
            DepartmentHead=int(dept_head),
            BusinessUnitId=bu_id,
            FrameworkId_id=int(framework_id),
            IsActive=True,
            CreatedDate=timezone.now(),
        )

        _log_audit(tenant_id, 'CREATE', dept.DepartmentId, dept.DepartmentName,
                   None, _dept_to_dict(dept), request)

        return JsonResponse({
            'status': 'success',
            'message': 'Department created',
            'department': _dept_to_dict(dept),
        }, status=201)
    except Exception as exc:
        logger.error(f"[department_views] create error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['PUT'])
@require_tenant
def department_update(request, dept_id):
    """
    PUT /api/departments/{dept_id}/
    """
    tenant_id = get_tenant_id_from_request(request)

    dept = Department.objects.filter(DepartmentId=dept_id, tenant_id=tenant_id, IsActive=True).first()
    if not dept:
        return JsonResponse({'status': 'error', 'message': 'Department not found'}, status=404)

    try:
        data = request.data if hasattr(request, 'data') else {}
        old = _dept_to_dict(dept)

        if 'department_name' in data:
            dept.DepartmentName = data['department_name']
        if 'department_head' in data:
            dept.DepartmentHead = int(data['department_head'])
        if 'is_active' in data:
            dept.IsActive = bool(data['is_active'])

        dept.save()
        _log_audit(tenant_id, 'UPDATE', dept.DepartmentId, dept.DepartmentName,
                   old, _dept_to_dict(dept), request)

        return JsonResponse({
            'status': 'success',
            'message': 'Department updated',
            'department': _dept_to_dict(dept),
        })
    except Exception as exc:
        logger.error(f"[department_views] update error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['POST'])
@require_tenant
def department_assign_user(request, dept_id):
    """
    POST /api/departments/{dept_id}/assign-user/
    Body: { "user_id": <int> }
    Sets this user as the DepartmentHead.
    """
    tenant_id = get_tenant_id_from_request(request)

    dept = Department.objects.filter(DepartmentId=dept_id, tenant_id=tenant_id, IsActive=True).first()
    if not dept:
        return JsonResponse({'status': 'error', 'message': 'Department not found'}, status=404)

    try:
        data = request.data if hasattr(request, 'data') else {}
        user_id = data.get('user_id')
        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'user_id is required'}, status=400)

        if not Users.objects.filter(UserId=user_id).exists():
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)

        old = _dept_to_dict(dept)
        dept.DepartmentHead = int(user_id)
        dept.save()

        _log_audit(tenant_id, 'UPDATE', dept.DepartmentId, dept.DepartmentName,
                   old, _dept_to_dict(dept), request)

        return JsonResponse({
            'status': 'success',
            'message': f'User {user_id} assigned as department head',
            'department': _dept_to_dict(dept),
        })
    except Exception as exc:
        logger.error(f"[department_views] assign_user error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)
