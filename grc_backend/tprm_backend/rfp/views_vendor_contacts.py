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

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_vendor_primary_contact(request, vendor_id):
    """Get primary contact for a vendor"""
    try:
        # Query vendor_contacts table for primary contact
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT contact_id, first_name, last_name, email, phone, mobile, designation
                FROM vendor_contacts
                WHERE vendor_id = %s AND contact_type = 'PRIMARY' AND is_primary = 1 AND is_active = 1
                LIMIT 1
            ''', [vendor_id])
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
