"""
RBAC Views for TPRM System

This module provides views for RBAC functionality including user permissions for TPRM.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import logging
from .tprm_utils import RBACTPRMUtils
from .tprm_decorators import rbac_required
import jwt
from django.conf import settings

logger = logging.getLogger(__name__)

def get_user_id_from_jwt(request):
    """
    Extract user_id from JWT token in Authorization header
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("[RBAC TPRM VIEWS] No Bearer token found in Authorization header")
            return None
        
        token = auth_header.split(' ')[1]
        
        # Decode JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        if user_id:
            logger.info(f"[RBAC TPRM VIEWS] Successfully extracted user_id from JWT: {user_id}")
            return user_id
        else:
            logger.warning("[RBAC TPRM VIEWS] No user_id found in JWT payload")
            return None
            
    except jwt.ExpiredSignatureError:
        logger.error("[RBAC TPRM VIEWS] JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"[RBAC TPRM VIEWS] Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error extracting user_id from JWT: {e}")
        return None

@csrf_exempt
@require_http_methods(["GET"])
def get_user_permissions(request):
    """
    Get user permissions for frontend RBAC service
    
    Returns:
        JSON response with user permissions organized by module
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        # Get user permissions summary
        permissions_summary = RBACTPRMUtils.get_user_permissions_summary(user_id)
        
        if not permissions_summary:
            return JsonResponse({
                'error': 'User not found',
                'message': 'User not found in RBAC system'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'permissions': permissions_summary
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in get_user_permissions: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_rfp_permission(request):
    """
    Check if user has specific RFP permission
    
    Query Parameters:
        permission_type: Type of RFP permission to check
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        permission_type = request.GET.get('permission_type')
        if not permission_type:
            return JsonResponse({
                'error': 'Missing parameter',
                'message': 'permission_type is required'
            }, status=400)
        
        # Check permission
        has_permission = RBACTPRMUtils.check_rfp_permission(user_id, permission_type)
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'permission_type': permission_type,
            'has_permission': has_permission
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in check_rfp_permission: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_contract_permission(request):
    """
    Check if user has specific contract permission
    
    Query Parameters:
        permission_type: Type of contract permission to check
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        permission_type = request.GET.get('permission_type')
        if not permission_type:
            return JsonResponse({
                'error': 'Missing parameter',
                'message': 'permission_type is required'
            }, status=400)
        
        # Check permission
        has_permission = RBACTPRMUtils.check_contract_permission(user_id, permission_type)
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'permission_type': permission_type,
            'has_permission': has_permission
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in check_contract_permission: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_vendor_permission(request):
    """
    Check if user has specific vendor permission
    
    Query Parameters:
        permission_type: Type of vendor permission to check
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        permission_type = request.GET.get('permission_type')
        if not permission_type:
            return JsonResponse({
                'error': 'Missing parameter',
                'message': 'permission_type is required'
            }, status=400)
        
        # Check permission
        has_permission = RBACTPRMUtils.check_vendor_permission(user_id, permission_type)
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'permission_type': permission_type,
            'has_permission': has_permission
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in check_vendor_permission: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_risk_permission(request):
    """
    Check if user has specific risk permission
    
    Query Parameters:
        permission_type: Type of risk permission to check
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        permission_type = request.GET.get('permission_type')
        if not permission_type:
            return JsonResponse({
                'error': 'Missing parameter',
                'message': 'permission_type is required'
            }, status=400)
        
        # Check permission
        has_permission = RBACTPRMUtils.check_risk_permission(user_id, permission_type)
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'permission_type': permission_type,
            'has_permission': has_permission
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in check_risk_permission: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_compliance_permission(request):
    """
    Check if user has specific compliance permission
    
    Query Parameters:
        permission_type: Type of compliance permission to check
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        permission_type = request.GET.get('permission_type')
        if not permission_type:
            return JsonResponse({
                'error': 'Missing parameter',
                'message': 'permission_type is required'
            }, status=400)
        
        # Check permission
        has_permission = RBACTPRMUtils.check_compliance_permission(user_id, permission_type)
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'permission_type': permission_type,
            'has_permission': has_permission
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in check_compliance_permission: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_bcp_drp_permission(request):
    """
    Check if user has specific BCP/DRP permission
    
    Query Parameters:
        permission_type: Type of BCP/DRP permission to check
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        permission_type = request.GET.get('permission_type')
        if not permission_type:
            return JsonResponse({
                'error': 'Missing parameter',
                'message': 'permission_type is required'
            }, status=400)
        
        # Check permission
        has_permission = RBACTPRMUtils.check_bcp_drp_permission(user_id, permission_type)
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'permission_type': permission_type,
            'has_permission': has_permission
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in check_bcp_drp_permission: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_sla_permission(request):
    """
    Check if user has specific SLA permission
    
    Query Parameters:
        permission_type: Type of SLA permission to check (ViewSLA, CreateSLA, UpdateSLA, DeleteSLA, ActivateDeactivateSLA)
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        logger.info(f"[RBAC SLA CHECK] Checking permission for user_id: {user_id}")
        
        if not user_id:
            logger.warning("[RBAC SLA CHECK] No user_id found in request")
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        permission_type = request.GET.get('permission_type')
        if not permission_type:
            logger.warning(f"[RBAC SLA CHECK] No permission_type provided for user {user_id}")
            return JsonResponse({
                'error': 'Missing parameter',
                'message': 'permission_type is required'
            }, status=400)
        
        logger.info(f"[RBAC SLA CHECK] User {user_id} checking permission: {permission_type}")
        
        # Get RBAC record to debug
        rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
        if rbac_record:
            logger.info(f"[RBAC SLA CHECK] Found RBAC record for user {user_id}: role={rbac_record.role}, is_active={rbac_record.is_active}")
            # Log specific SLA permission values
            logger.info(f"[RBAC SLA CHECK] SLA permissions for user {user_id}: "
                       f"view_sla={rbac_record.view_sla}, "
                       f"create_sla={rbac_record.create_sla}, "
                       f"update_sla={rbac_record.update_sla}, "
                       f"delete_sla={rbac_record.delete_sla}, "
                       f"activate_deactivate_sla={rbac_record.activate_deactivate_sla}")
        else:
            logger.warning(f"[RBAC SLA CHECK] No RBAC record found for user {user_id}")
        
        # Check permission
        has_permission = RBACTPRMUtils.check_sla_permission(user_id, permission_type)
        
        logger.info(f"[RBAC SLA CHECK] Permission check result for user {user_id}, {permission_type}: {has_permission}")
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'permission_type': permission_type,
            'has_permission': has_permission
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in check_sla_permission: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def check_module_access(request):
    """
    Check if user has access to a specific module
    
    Query Parameters:
        module_name: Name of the module to check access for
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        module_name = request.GET.get('module_name')
        if not module_name:
            return JsonResponse({
                'error': 'Missing parameter',
                'message': 'module_name is required'
            }, status=400)
        
        # Check module access
        has_access = RBACTPRMUtils.has_module_access(user_id, module_name)
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'module_name': module_name,
            'has_access': has_access
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in check_module_access: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_user_role(request):
    """
    Get user's role from RBAC system
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        # Get RBAC record
        rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
        
        if not rbac_record:
            return JsonResponse({
                'error': 'User not found',
                'message': 'User not found in RBAC system'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'username': rbac_record.username,
            'role': rbac_record.role,
            'is_admin': rbac_record.has_admin_access
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in get_user_role: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def bulk_check_permissions(request):
    """
    Check multiple permissions at once
    
    Request Body:
        permissions: List of permission objects with module and type
    """
    try:
        # Get user_id from JWT token
        user_id = get_user_id_from_jwt(request)
        
        if not user_id:
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'Valid JWT token required'
            }, status=401)
        
        # Parse request body
        import json
        try:
            data = json.loads(request.body)
            permissions = data.get('permissions', [])
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON',
                'message': 'Request body must be valid JSON'
            }, status=400)
        
        if not permissions:
            return JsonResponse({
                'error': 'Missing permissions',
                'message': 'permissions array is required'
            }, status=400)
        
        # Check each permission
        results = []
        for perm in permissions:
            module = perm.get('module')
            permission_type = perm.get('type')
            
            if not module or not permission_type:
                results.append({
                    'module': module,
                    'type': permission_type,
                    'has_permission': False,
                    'error': 'Missing module or type'
                })
                continue
            
            # Check permission based on module
            if module == 'rfp':
                has_permission = RBACTPRMUtils.check_rfp_permission(user_id, permission_type)
            elif module == 'contract':
                has_permission = RBACTPRMUtils.check_contract_permission(user_id, permission_type)
            elif module == 'vendor':
                has_permission = RBACTPRMUtils.check_vendor_permission(user_id, permission_type)
            elif module == 'risk':
                has_permission = RBACTPRMUtils.check_risk_permission(user_id, permission_type)
            elif module == 'compliance':
                has_permission = RBACTPRMUtils.check_compliance_permission(user_id, permission_type)
            elif module == 'bcp_drp':
                has_permission = RBACTPRMUtils.check_bcp_drp_permission(user_id, permission_type)
            else:
                has_permission = False
            
            results.append({
                'module': module,
                'type': permission_type,
                'has_permission': has_permission
            })
        
        return JsonResponse({
            'success': True,
            'user_id': user_id,
            'results': results
        }, status=200)
        
    except Exception as e:
        logger.error(f"[RBAC TPRM VIEWS] Error in bulk_check_permissions: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)
