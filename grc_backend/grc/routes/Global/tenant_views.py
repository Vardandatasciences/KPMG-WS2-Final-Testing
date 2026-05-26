"""
Tenant Management API Views

Endpoints for creating, updating, and managing tenants.
"""

import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from ...models import Tenant, Users, TenantAuditLog
from ...tenant_utils import require_tenant, get_tenant_from_request, get_tenant_id_from_request
from ...rbac.utils import RBACUtils


def _is_global_admin(request):
    """
    Returns True if the requesting user is a platform-level (global) admin.
    Global admins have no tenant assignment (tenant_id is None).
    Tenant-scoped users always have a tenant_id.
    """
    try:
        user_id = RBACUtils.get_user_id_from_request(request)
        if not user_id:
            return False
        user = Users.objects.filter(UserId=user_id).first()
        if not user:
            return False
        return user.tenant_id is None
    except Exception:
        return False


def _get_requesting_user(request):
    """Return the Users object for the requesting user, or None."""
    try:
        user_id = RBACUtils.get_user_id_from_request(request)
        if user_id:
            return Users.objects.filter(UserId=user_id).first()
    except Exception:
        pass
    return None

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def create_tenant(request):
    if not _is_global_admin(request):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    """
    Create a new tenant (organization)
    
    POST /api/tenants/create/
    Body:
    {
        "name": "Acme Corporation",
        "subdomain": "acmecorp",
        "license_key": "unique-license-key",
        "subscription_tier": "enterprise",
        "max_users": 50,
        "storage_limit_gb": 100,
        "primary_contact_email": "admin@acmecorp.com",
        "primary_contact_name": "John Doe",
        "primary_contact_phone": "+1234567890"
    }
    """
    try:
        data = request.data if hasattr(request, 'data') else request.POST
        
        # Required fields
        name = data.get('name')
        subdomain = data.get('subdomain')
        
        if not name or not subdomain:
            return JsonResponse({
                'status': 'error',
                'message': 'Name and subdomain are required'
            }, status=400)
        
        # Check if subdomain already exists
        if Tenant.objects.filter(subdomain=subdomain).exists():
            return JsonResponse({
                'status': 'error',
                'message': f'Subdomain "{subdomain}" is already taken'
            }, status=400)
        
        # Check if license_key already exists
        license_key = data.get('license_key')
        if license_key and Tenant.objects.filter(license_key=license_key).exists():
            return JsonResponse({
                'status': 'error',
                'message': f'License key already in use'
            }, status=400)
        
        # Create tenant
        tenant = Tenant.objects.create(
            name=name,
            subdomain=subdomain,
            license_key=license_key,
            subscription_tier=data.get('subscription_tier', 'starter'),
            status='trial',  # Start with trial
            max_users=int(data.get('max_users', 10)),
            storage_limit_gb=int(data.get('storage_limit_gb', 10)),
            primary_contact_email=data.get('primary_contact_email'),
            primary_contact_name=data.get('primary_contact_name'),
            primary_contact_phone=data.get('primary_contact_phone'),
            trial_ends_at=datetime.now() + timedelta(days=30),  # 30-day trial
            settings=data.get('settings', {})
        )
        
        logger.info(f"✅ Created new tenant: {tenant.name} ({tenant.subdomain})")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Tenant created successfully',
            'tenant': {
                'tenant_id': tenant.tenant_id,
                'name': tenant.name,
                'subdomain': tenant.subdomain,
                'subscription_tier': tenant.subscription_tier,
                'status': tenant.status,
                'max_users': tenant.max_users,
                'storage_limit_gb': tenant.storage_limit_gb,
                'trial_ends_at': tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
                'created_at': tenant.created_at.isoformat()
            }
        }, status=201)
        
    except Exception as e:
        logger.error(f"❌ Error creating tenant: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error creating tenant: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tenants(request):
    """
    List tenants.
    - Global admins (tenant_id=None): see all tenants.
    - Tenant-scoped users: see only their own tenant.

    GET /api/tenants/list/
    """
    try:
        user = _get_requesting_user(request)
        if not user:
            return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

        if user.tenant_id is None:
            # Platform-level admin — return all tenants
            tenants = Tenant.objects.all().order_by('-created_at')
        else:
            # Tenant-scoped user — return only their own tenant
            tenants = Tenant.objects.filter(tenant_id=user.tenant_id)
        
        tenant_list = []
        for tenant in tenants:
            # Count users for this tenant
            user_count = Users.objects.filter(tenant=tenant).count()
            
            tenant_list.append({
                'tenant_id': tenant.tenant_id,
                'name': tenant.name,
                'subdomain': tenant.subdomain,
                'subscription_tier': tenant.subscription_tier,
                'status': tenant.status,
                'max_users': tenant.max_users,
                'current_users': user_count,
                'storage_limit_gb': tenant.storage_limit_gb,
                'trial_ends_at': tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
                'is_trial_expired': tenant.is_trial_expired(),
                'primary_contact_email': tenant.primary_contact_email,
                'created_at': tenant.created_at.isoformat(),
                'updated_at': tenant.updated_at.isoformat()
            })
        
        return JsonResponse({
            'status': 'success',
            'count': len(tenant_list),
            'tenants': tenant_list,
            'is_global_admin': user.tenant_id is None
        })
        
    except Exception as e:
        logger.error(f"❌ Error listing tenants: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error listing tenants: {str(e)}'
        }, status=500)


@api_view(['GET'])
@require_tenant
def get_tenant_info(request):
    """
    Get current tenant information
    
    GET /api/tenants/current/
    """
    try:
        tenant = get_tenant_from_request(request)
        
        if not tenant:
            return JsonResponse({
                'status': 'error',
                'message': 'Tenant not found'
            }, status=404)
        
        # Count users for this tenant
        user_count = Users.objects.filter(tenant=tenant).count()
        
        return JsonResponse({
            'status': 'success',
            'tenant': {
                'tenant_id': tenant.tenant_id,
                'name': tenant.name,
                'subdomain': tenant.subdomain,
                'subscription_tier': tenant.subscription_tier,
                'status': tenant.status,
                'max_users': tenant.max_users,
                'current_users': user_count,
                'storage_limit_gb': tenant.storage_limit_gb,
                'trial_ends_at': tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
                'is_trial_expired': tenant.is_trial_expired(),
                'is_active': tenant.is_active(),
                'settings': tenant.settings,
                'primary_contact_email': tenant.primary_contact_email,
                'primary_contact_name': tenant.primary_contact_name,
                'primary_contact_phone': tenant.primary_contact_phone,
                'created_at': tenant.created_at.isoformat(),
                'updated_at': tenant.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting tenant info: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error getting tenant info: {str(e)}'
        }, status=500)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def update_tenant(request, tenant_id):
    user = _get_requesting_user(request)
    if not user:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)
    # Tenant-scoped users may only read/update their own tenant
    if user.tenant_id is not None and str(user.tenant_id) != str(tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    """
    Get or update tenant information
    
    GET /api/tenants/{tenant_id}/update/  — fetch tenant detail
    PUT /api/tenants/{tenant_id}/update/  — update tenant fields
    """
    try:
        tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
        
        if not tenant:
            return JsonResponse({
                'status': 'error',
                'message': 'Tenant not found'
            }, status=404)

        if request.method == 'GET':
            user_count = Users.objects.filter(tenant=tenant).count()
            return JsonResponse({
                'status': 'success',
                'tenant': {
                    'tenant_id': tenant.tenant_id,
                    'name': tenant.name,
                    'subdomain': tenant.subdomain,
                    'subscription_tier': tenant.subscription_tier,
                    'status': tenant.status,
                    'max_users': tenant.max_users,
                    'current_users': user_count,
                    'storage_limit_gb': tenant.storage_limit_gb,
                    'trial_ends_at': tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
                    'is_trial_expired': tenant.is_trial_expired(),
                    'is_active': tenant.is_active(),
                    'settings': tenant.settings,
                    'primary_contact_email': tenant.primary_contact_email,
                    'primary_contact_name': tenant.primary_contact_name,
                    'primary_contact_phone': tenant.primary_contact_phone,
                    'created_at': tenant.created_at.isoformat(),
                    'updated_at': tenant.updated_at.isoformat()
                }
            })
        
        data = request.data if hasattr(request, 'data') else request.POST
        
        # Update fields
        if 'name' in data:
            tenant.name = data['name']
        if 'subscription_tier' in data:
            tenant.subscription_tier = data['subscription_tier']
        if 'status' in data:
            tenant.status = data['status']
        if 'max_users' in data:
            tenant.max_users = int(data['max_users'])
        if 'storage_limit_gb' in data:
            tenant.storage_limit_gb = int(data['storage_limit_gb'])
        if 'primary_contact_email' in data:
            tenant.primary_contact_email = data['primary_contact_email']
        if 'primary_contact_name' in data:
            tenant.primary_contact_name = data['primary_contact_name']
        if 'primary_contact_phone' in data:
            tenant.primary_contact_phone = data['primary_contact_phone']
        if 'settings' in data:
            tenant.settings = data['settings']
        
        tenant.save()
        
        logger.info(f"✅ Updated tenant: {tenant.name} ({tenant.tenant_id})")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Tenant updated successfully',
            'tenant': {
                'tenant_id': tenant.tenant_id,
                'name': tenant.name,
                'subdomain': tenant.subdomain,
                'subscription_tier': tenant.subscription_tier,
                'status': tenant.status,
                'max_users': tenant.max_users,
                'storage_limit_gb': tenant.storage_limit_gb,
                'updated_at': tenant.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error updating tenant: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error updating tenant: {str(e)}'
        }, status=500)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def delete_tenant(request, tenant_id):
    if not _is_global_admin(request):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    """
    Delete a tenant (WARNING: This will delete all associated data!)
    
    DELETE /api/tenants/{tenant_id}/delete/
    """
    try:
        tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
        
        if not tenant:
            return JsonResponse({
                'status': 'error',
                'message': 'Tenant not found'
            }, status=404)
        
        tenant_name = tenant.name
        tenant_subdomain = tenant.subdomain
        
        # Delete tenant (cascade will delete all related data)
        tenant.delete()
        
        logger.warning(f"🗑️ Deleted tenant: {tenant_name} ({tenant_subdomain})")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Tenant "{tenant_name}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Error deleting tenant: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error deleting tenant: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def activate_tenant(request, tenant_id):
    if not _is_global_admin(request):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    """
    Activate a tenant (change status from trial to active)
    
    POST /api/tenants/{tenant_id}/activate/
    """
    try:
        tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
        
        if not tenant:
            return JsonResponse({
                'status': 'error',
                'message': 'Tenant not found'
            }, status=404)
        
        tenant.status = 'active'
        tenant.trial_ends_at = None  # Clear trial end date
        tenant.save()
        
        logger.info(f"✅ Activated tenant: {tenant.name} ({tenant.tenant_id})")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Tenant "{tenant.name}" activated successfully',
            'tenant': {
                'tenant_id': tenant.tenant_id,
                'name': tenant.name,
                'status': tenant.status
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error activating tenant: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error activating tenant: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def suspend_tenant(request, tenant_id):
    if not _is_global_admin(request):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    """
    Suspend a tenant (change status to suspended)
    
    POST /api/tenants/{tenant_id}/suspend/
    """
    try:
        tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
        
        if not tenant:
            return JsonResponse({
                'status': 'error',
                'message': 'Tenant not found'
            }, status=404)
        
        tenant.status = 'suspended'
        tenant.save()
        
        logger.warning(f"⚠️ Suspended tenant: {tenant.name} ({tenant.tenant_id})")
        
        return JsonResponse({
            'status': 'success',
            'message': f'Tenant "{tenant.name}" suspended successfully',
            'tenant': {
                'tenant_id': tenant.tenant_id,
                'name': tenant.name,
                'status': tenant.status
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error suspending tenant: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error suspending tenant: {str(e)}'
        }, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def archive_tenant(request, tenant_id):
    if not _is_global_admin(request):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    """
    POST /api/tenants/{tenant_id}/archive/
    Archives a tenant (soft inactive state – data retained).
    """
    try:
        tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
        if not tenant:
            return JsonResponse({'status': 'error', 'message': 'Tenant not found'}, status=404)

        old_status = tenant.status
        tenant.status = 'archived'
        tenant.save()

        try:
            performer_id = None
            if hasattr(request, 'user') and request.user and request.user.is_authenticated:
                performer_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))
            TenantAuditLog.objects.create(
                tenant_id=tenant_id,
                action_type='ARCHIVE',
                entity_type='tenant',
                entity_id=tenant_id,
                entity_name=tenant.name,
                old_value={'status': old_status},
                new_value={'status': 'archived'},
                performed_by_id=performer_id,
                ip_address=request.META.get('REMOTE_ADDR', ''),
            )
        except Exception:
            pass

        logger.info(f"📦 Archived tenant: {tenant.name} ({tenant.tenant_id})")
        return JsonResponse({
            'status': 'success',
            'message': f'Tenant "{tenant.name}" archived successfully',
            'tenant': {'tenant_id': tenant.tenant_id, 'name': tenant.name, 'status': tenant.status},
        })
    except Exception as e:
        logger.error(f"❌ Error archiving tenant: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'Error archiving tenant: {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tenant_users(request, tenant_id):
    """
    GET /api/tenants/{tenant_id}/users/
    Returns all user mappings for the tenant with user details.
    """
    user = _get_requesting_user(request)
    if not user:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)
    if user.tenant_id is not None and str(user.tenant_id) != str(tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

    try:
        from ...models import TenantUserMapping
        mappings = TenantUserMapping.objects.filter(
            tenant_id=tenant_id, is_deleted=False
        ).select_related('user')

        result = []
        for m in mappings:
            u = m.user
            result.append({
                'id': m.id,
                'user_id': m.user_id,
                'user_name': getattr(u, 'UserName', ''),
                'user_email': getattr(u, 'Email', ''),
                'first_name': getattr(u, 'FirstName', ''),
                'last_name': getattr(u, 'LastName', ''),
                'role': m.role,
                'is_primary': m.is_primary,
                'status': m.status,
                'assigned_at': m.assigned_at.isoformat() if m.assigned_at else None,
            })

        return JsonResponse({'status': 'success', 'count': len(result), 'users': result})
    except Exception as exc:
        logger.error(f"[list_tenant_users] error: {exc}")
        return JsonResponse({'status': 'error', 'message': str(exc)}, status=500)


@api_view(['GET'])
@require_tenant
def get_tenant_audit_logs(request, tenant_id):
    """
    GET /api/tenants/{tenant_id}/audit-logs/
    Returns the audit log for tenant-level administrative actions.
    Query params: ?limit=50&offset=0&action_type=<str>&entity_type=<str>
    """
    session_tenant_id = get_tenant_id_from_request(request)
    if int(tenant_id) != int(session_tenant_id):
        return JsonResponse({'status': 'error', 'message': 'Access denied'}, status=403)

    try:
        qs = TenantAuditLog.objects.filter(tenant_id=tenant_id).order_by('-performed_at')

        action_type = request.GET.get('action_type')
        entity_type = request.GET.get('entity_type')
        if action_type:
            qs = qs.filter(action_type=action_type)
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        total = qs.count()
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))
        qs = qs[offset:offset + limit]

        logs = [
            {
                'id': log.id,
                'action_type': log.action_type or '',
                'entity_type': log.entity_type or '',
                'entity_id': log.entity_id,
                'entity_name': log.entity_name or '',
                'old_value': log.old_value,
                'new_value': log.new_value,
                'performed_by_id': log.performed_by_id,
                'performed_by_name': (
                    f"{log.performed_by.FirstName or ''} {log.performed_by.LastName or ''}".strip()
                    or getattr(log.performed_by, 'UserName', '')
                ) if log.performed_by else '',
                'performed_at': log.performed_at.isoformat() if log.performed_at else None,
                'ip_address': log.ip_address or '',
                'user_agent': log.user_agent or '',
            }
            for log in qs
        ]

        return JsonResponse({
            'status': 'success',
            'total': total,
            'limit': limit,
            'offset': offset,
            'audit_logs': logs,
        })
    except Exception as e:
        logger.error(f"❌ Error fetching audit logs: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

