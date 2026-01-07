"""
Views for handling vendor contacts
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.db import connection
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from .rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission
from tprm_backend.rbac.tprm_decorators import rbac_rfp_required

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    require_tenant,
    tenant_filter
)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_vendor_primary_contact(request, vendor_id):
    """
    Get primary contact for a vendor
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return JsonResponse({'error': 'Tenant context not found'}, status=403)
    
    try:
        # MULTI-TENANCY: Verify vendor belongs to tenant
        from .models import Vendor
        try:
            vendor = Vendor.objects.get(vendor_id=vendor_id, tenant_id=tenant_id)
        except Vendor.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Vendor not found: {vendor_id}'
            }, status=404)
        
        # Query vendor_contacts table for primary contact
        # MULTI-TENANCY: Filter by tenant
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT vc.contact_id, vc.first_name, vc.last_name, vc.email, vc.phone, vc.mobile, vc.designation
                FROM vendor_contacts vc
                INNER JOIN vendors v ON vc.vendor_id = v.vendor_id
                WHERE vc.vendor_id = %s 
                    AND vc.contact_type = 'PRIMARY' 
                    AND vc.is_primary = 1 
                    AND vc.is_active = 1
                    AND v.TenantId = %s
                LIMIT 1
            ''', [vendor_id, tenant_id])
            contact = cursor.fetchone()
            
            if contact:
                contact_data = {
                    'contact_id': contact[0],
                    'first_name': contact[1],
                    'last_name': contact[2],
                    'email': contact[3],
                    'phone': contact[4],
                    'mobile': contact[5],
                    'designation': contact[6]
                }
                return JsonResponse({
                    'success': True,
                    'contact': contact_data
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No primary contact found for vendor'
                })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
