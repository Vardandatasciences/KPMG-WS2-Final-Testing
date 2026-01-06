"""
Tenant Management API Views

Endpoints for creating, updating, and managing tenants.
"""

import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from ...models import Tenant, Users
from ...tenant_utils import require_tenant, get_tenant_from_request

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def create_tenant(request):
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
@permission_classes([AllowAny])
def list_tenants(request):
    """
    List all tenants (for super admin)
    
    GET /api/tenants/list/
    """
    try:
        tenants = Tenant.objects.all().order_by('-created_at')
        
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
            'tenants': tenant_list
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


@api_view(['PUT'])
@permission_classes([AllowAny])
@csrf_exempt
def update_tenant(request, tenant_id):
    """
    Update tenant information
    
    PUT /api/tenants/{tenant_id}/update/
    Body:
    {
        "name": "Updated Name",
        "subscription_tier": "enterprise",
        "status": "active",
        "max_users": 100,
        "storage_limit_gb": 500
    }
    """
    try:
        tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
        
        if not tenant:
            return JsonResponse({
                'status': 'error',
                'message': 'Tenant not found'
            }, status=404)
        
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
@permission_classes([AllowAny])
@csrf_exempt
def delete_tenant(request, tenant_id):
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
@permission_classes([AllowAny])
@csrf_exempt
def activate_tenant(request, tenant_id):
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
@permission_classes([AllowAny])
@csrf_exempt
def suspend_tenant(request, tenant_id):
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

