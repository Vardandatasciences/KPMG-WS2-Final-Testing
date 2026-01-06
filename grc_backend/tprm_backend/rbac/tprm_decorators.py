"""
RBAC Decorators for TPRM System

This module provides decorators for checking permissions using the rbac_tprm table schema.
"""

import logging
from functools import wraps
from django.http import JsonResponse
from .tprm_utils import RBACTPRMUtils

logger = logging.getLogger(__name__)

def rbac_required(permission_name, module_name=None):
    """
    Decorator to check if user has required RBAC permission
    
    Args:
        permission_name: Name of the permission to check
        module_name: Optional module name for context
    
    Usage:
        @rbac_required('create_rfp', 'rfp')
        def create_rfp_view(request):
            # View logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get user_id from request
                user_id = RBACTPRMUtils.get_user_id_from_request(request)
                
                if not user_id:
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check permission
                has_permission = RBACTPRMUtils.check_permission(user_id, permission_name)
                
                if not has_permission:
                    logger.warning(f"[RBAC TPRM DECORATOR] User {user_id} denied access to {permission_name}")
                    return JsonResponse({
                        'error': 'Permission denied',
                        'message': f'You do not have permission to perform this action: {permission_name}'
                    }, status=403)
                
                logger.info(f"[RBAC TPRM DECORATOR] User {user_id} granted access to {permission_name}")
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC TPRM DECORATOR] Error checking permission {permission_name}: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking permissions'
                }, status=500)
        
        return wrapper
    return decorator

def rbac_rfp_required(permission_type):
    """
    Decorator to check RFP-specific permissions
    
    Args:
        permission_type: Type of RFP permission ('create', 'edit', 'view', 'delete', etc.)
    
    Usage:
        @rbac_rfp_required('create')
        def create_rfp_view(request):
            # View logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get user_id from request
                user_id = RBACTPRMUtils.get_user_id_from_request(request)
                
                if not user_id:
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check RFP permission
                has_permission = RBACTPRMUtils.check_rfp_permission(user_id, permission_type)
                
                if not has_permission:
                    logger.warning(f"[RBAC TPRM DECORATOR] User {user_id} denied RFP access: {permission_type}")
                    return JsonResponse({
                        'error': 'Permission denied',
                        'message': f'You do not have permission to perform this RFP action: {permission_type}'
                    }, status=403)
                
                logger.info(f"[RBAC TPRM DECORATOR] User {user_id} granted RFP access: {permission_type}")
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC TPRM DECORATOR] Error checking RFP permission {permission_type}: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking RFP permissions'
                }, status=500)
        
        return wrapper
    return decorator


def rbac_rfp_optional(permission_type):
    """
    Decorator to optionally enforce RFP permissions.
    If an Authorization header is present, RBAC checks are performed.
    If no Authorization header is present, the request is allowed to proceed.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                auth_header = None

                # Prefer DRF's request.headers accessor
                if hasattr(request, "headers"):
                    auth_header = request.headers.get("Authorization")

                # Fallback to META for standard Django requests
                if not auth_header and hasattr(request, "META"):
                    auth_header = request.META.get("HTTP_AUTHORIZATION")

                if auth_header:
                    user_id = RBACTPRMUtils.get_user_id_from_request(request)

                    if not user_id:
                        logger.warning(
                            "[RBAC TPRM DECORATOR] Authorization header present but no user_id extracted"
                        )
                        return JsonResponse(
                            {
                                "error": "Authentication required",
                                "message": "Valid JWT token required",
                            },
                            status=401,
                        )

                    has_permission = RBACTPRMUtils.check_rfp_permission(
                        user_id, permission_type
                    )

                    if not has_permission:
                        logger.warning(
                            f"[RBAC TPRM DECORATOR] User {user_id} denied optional RFP access: {permission_type}"
                        )
                        return JsonResponse(
                            {
                                "error": "Permission denied",
                                "message": f"You do not have permission to perform this RFP action: {permission_type}",
                            },
                            status=403,
                        )

                    logger.info(
                        f"[RBAC TPRM DECORATOR] User {user_id} granted optional RFP access: {permission_type}"
                    )

                return view_func(request, *args, **kwargs)

            except Exception as e:
                logger.error(
                    f"[RBAC TPRM DECORATOR] Error checking optional RFP permission {permission_type}: {e}"
                )
                return JsonResponse(
                    {
                        "error": "Internal server error",
                        "message": "Error checking RFP permissions",
                    },
                    status=500,
                )

        return wrapper

    return decorator


def rbac_contract_required(permission_type):
    """
    Decorator to check contract-specific permissions
    
    Args:
        permission_type: Type of contract permission ('create', 'update', 'delete', 'approve', etc.)
    
    Usage:
        @rbac_contract_required('create')
        def create_contract_view(request):
            # View logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get user_id from request
                user_id = RBACTPRMUtils.get_user_id_from_request(request)
                
                if not user_id:
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check contract permission
                has_permission = RBACTPRMUtils.check_contract_permission(user_id, permission_type)
                
                if not has_permission:
                    logger.warning(f"[RBAC TPRM DECORATOR] User {user_id} denied contract access: {permission_type}")
                    return JsonResponse({
                        'error': 'Permission denied',
                        'message': f'You do not have permission to perform this contract action: {permission_type}'
                    }, status=403)
                
                logger.info(f"[RBAC TPRM DECORATOR] User {user_id} granted contract access: {permission_type}")
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC TPRM DECORATOR] Error checking contract permission {permission_type}: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking contract permissions'
                }, status=500)
        
        return wrapper
    return decorator

def rbac_vendor_required(permission_type):
    """
    Decorator to check vendor-specific permissions
    
    Args:
        permission_type: Type of vendor permission ('view', 'create', 'update', 'delete', etc.)
    
    Usage:
        @rbac_vendor_required('create')
        def create_vendor_view(request):
            # View logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            try:
                # Determine if this is a bound method (ViewSet) or regular function
                actual_request = None
                
                if len(args) > 0:
                    first_arg = args[0]
                    # Check if first argument has 'request' attribute (ViewSet instance)
                    if hasattr(first_arg, 'request'):
                        # This is a ViewSet method, request is the second argument
                        actual_request = args[1] if len(args) > 1 else first_arg.request
                    elif hasattr(first_arg, 'headers'):
                        # This is a request object (regular function)
                        actual_request = first_arg
                    else:
                        # Try next argument in case it's the request
                        if len(args) > 1 and hasattr(args[1], 'headers'):
                            actual_request = args[1]
                        else:
                            actual_request = first_arg
                
                if not actual_request:
                    logger.warning(f"[RBAC TPRM DECORATOR] Could not extract request for permission check: {permission_type}")
                    return JsonResponse({
                        'error': 'Permission denied',
                        'message': f'You do not have permission to perform this vendor action: {permission_type}',
                        'permission_type': permission_type
                    }, status=403)
                
                # Get user_id from request
                user_id = RBACTPRMUtils.get_user_id_from_request(actual_request)
                
                if not user_id:
                    logger.warning(f"[RBAC TPRM DECORATOR] No user_id found for permission check: {permission_type}")
                    return JsonResponse({
                        'error': 'Permission denied',
                        'message': f'You do not have permission to perform this vendor action: {permission_type}',
                        'permission_type': permission_type
                    }, status=403)
                
                # Check vendor permission
                # Use force_refresh=True to always get fresh data from database, bypassing ORM cache
                # This ensures that recently granted permissions are immediately recognized
                has_permission = RBACTPRMUtils.check_vendor_permission(user_id, permission_type, force_refresh=True)
                
                if not has_permission:
                    logger.warning(f"[RBAC TPRM DECORATOR] User {user_id} denied vendor access: {permission_type}")
                    return JsonResponse({
                        'error': 'Permission denied',
                        'message': f'You do not have permission to perform this vendor action: {permission_type}',
                        'permission_type': permission_type
                    }, status=403)
                
                logger.info(f"[RBAC TPRM DECORATOR] User {user_id} granted vendor access: {permission_type}")
                
                # Call the original function with all arguments
                return view_func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC TPRM DECORATOR] Error checking vendor permission {permission_type}: {e}")
                import traceback
                logger.error(f"[RBAC TPRM DECORATOR] Traceback: {traceback.format_exc()}")
                return JsonResponse({
                    'error': 'Permission denied',
                    'message': f'You do not have permission to perform this vendor action: {permission_type}',
                    'permission_type': permission_type
                }, status=403)
        
        return wrapper
    return decorator

def rbac_risk_required(permission_type):
    """
    Decorator to check risk-specific permissions
    
    Args:
        permission_type: Type of risk permission ('assess_vendor', 'view_scores', 'identify_in_plans', etc.)
    
    Usage:
        @rbac_risk_required('assess_vendor')
        def assess_vendor_risk_view(request):
            # View logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get user_id from request
                user_id = RBACTPRMUtils.get_user_id_from_request(request)
                
                if not user_id:
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check risk permission
                has_permission = RBACTPRMUtils.check_risk_permission(user_id, permission_type)
                
                if not has_permission:
                    logger.warning(f"[RBAC TPRM DECORATOR] User {user_id} denied risk access: {permission_type}")
                    return JsonResponse({
                        'error': 'Permission denied',
                        'message': f'You do not have permission to perform this risk action: {permission_type}'
                    }, status=403)
                
                logger.info(f"[RBAC TPRM DECORATOR] User {user_id} granted risk access: {permission_type}")
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC TPRM DECORATOR] Error checking risk permission {permission_type}: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking risk permissions'
                }, status=500)
        
        return wrapper
    return decorator

def rbac_sla_required(permission_type):
    """
    Decorator to check SLA-specific permissions
    
    Args:
        permission_type: Type of SLA permission ('view', 'create', 'update', 'delete', etc.)
    
    Usage:
        @rbac_sla_required('view')
        def view_sla_view(request):
            # View logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get user_id from request
                user_id = RBACTPRMUtils.get_user_id_from_request(request)
                
                if not user_id:
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check SLA permission
                has_permission = RBACTPRMUtils.check_sla_permission(user_id, permission_type)
                
                if not has_permission:
                    logger.warning(f"[RBAC TPRM DECORATOR] User {user_id} denied SLA access: {permission_type}")
                    return JsonResponse({
                        'error': 'Permission denied',
                        'message': f'You do not have permission to perform this SLA action: {permission_type}'
                    }, status=403)
                
                logger.info(f"[RBAC TPRM DECORATOR] User {user_id} granted SLA access: {permission_type}")
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC TPRM DECORATOR] Error checking SLA permission {permission_type}: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking SLA permissions'
                }, status=500)
        
        return wrapper
    return decorator

def rbac_compliance_required(permission_type):
    """
    Decorator to check compliance-specific permissions
    
    Args:
        permission_type: Type of compliance permission ('generate_reports', 'review_regulatory', etc.)
    
    Usage:
        @rbac_compliance_required('generate_reports')
        def generate_compliance_report_view(request):
            # View logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get user_id from request
                user_id = RBACTPRMUtils.get_user_id_from_request(request)
                
                if not user_id:
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check compliance permission
                has_permission = RBACTPRMUtils.check_compliance_permission(user_id, permission_type)
                
                if not has_permission:
                    logger.warning(f"[RBAC TPRM DECORATOR] User {user_id} denied compliance access: {permission_type}")
                    return JsonResponse({
                        'error': 'Permission denied',
                        'message': f'You do not have permission to perform this compliance action: {permission_type}'
                    }, status=403)
                
                logger.info(f"[RBAC TPRM DECORATOR] User {user_id} granted compliance access: {permission_type}")
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC TPRM DECORATOR] Error checking compliance permission {permission_type}: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking compliance permissions'
                }, status=500)
        
        return wrapper
    return decorator

def rbac_bcp_drp_required(permission_type):
    """
    Decorator to check BCP/DRP-specific permissions
    
    Args:
        permission_type: Type of BCP/DRP permission ('create_strategy', 'view_plans', etc.)
    
    Usage:
        @rbac_bcp_drp_required('create_strategy')
        def create_bcp_strategy_view(request):
            # View logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get user_id from request
                user_id = RBACTPRMUtils.get_user_id_from_request(request)
                
                if not user_id:
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check BCP/DRP permission
                has_permission = RBACTPRMUtils.check_bcp_drp_permission(user_id, permission_type)
                
                if not has_permission:
                    logger.warning(f"[RBAC TPRM DECORATOR] User {user_id} denied BCP/DRP access: {permission_type}")
                    return JsonResponse({
                        'error': 'Permission denied',
                        'message': f'You do not have permission to perform this BCP/DRP action: {permission_type}'
                    }, status=403)
                
                logger.info(f"[RBAC TPRM DECORATOR] User {user_id} granted BCP/DRP access: {permission_type}")
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC TPRM DECORATOR] Error checking BCP/DRP permission {permission_type}: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking BCP/DRP permissions'
                }, status=500)
        
        return wrapper
    return decorator

def rbac_module_required(module_name):
    """
    Decorator to check if user has access to a specific module
    
    Args:
        module_name: Name of the module ('rfp', 'contract', 'vendor', 'risk', 'compliance', 'bcp_drp')
    
    Usage:
        @rbac_module_required('rfp')
        def rfp_dashboard_view(request):
            # View logic here
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                # Get user_id from request
                user_id = RBACTPRMUtils.get_user_id_from_request(request)
                
                if not user_id:
                    return JsonResponse({
                        'error': 'Authentication required',
                        'message': 'Valid JWT token required'
                    }, status=401)
                
                # Check module access
                has_access = RBACTPRMUtils.has_module_access(user_id, module_name)
                
                if not has_access:
                    logger.warning(f"[RBAC TPRM DECORATOR] User {user_id} denied access to module: {module_name}")
                    return JsonResponse({
                        'error': 'Module access denied',
                        'message': f'You do not have access to the {module_name.upper()} module'
                    }, status=403)
                
                logger.info(f"[RBAC TPRM DECORATOR] User {user_id} granted access to module: {module_name}")
                return view_func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"[RBAC TPRM DECORATOR] Error checking module access {module_name}: {e}")
                return JsonResponse({
                    'error': 'Internal server error',
                    'message': 'Error checking module access'
                }, status=500)
        
        return wrapper
    return decorator

def rbac_admin_required(view_func):
    """
    Decorator to check if user has admin-level access
    
    Usage:
        @rbac_admin_required
        def admin_dashboard_view(request):
            # View logic here
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            # Get user_id from request
            user_id = RBACTPRMUtils.get_user_id_from_request(request)
            
            if not user_id:
                return JsonResponse({
                    'error': 'Authentication required',
                    'message': 'Valid JWT token required'
                }, status=401)
            
            # Get RBAC record and check admin access
            rbac_record = RBACTPRMUtils.get_user_rbac_record(user_id)
            
            if not rbac_record or not rbac_record.has_admin_access:
                logger.warning(f"[RBAC TPRM DECORATOR] User {user_id} denied admin access")
                return JsonResponse({
                    'error': 'Admin access denied',
                    'message': 'You do not have administrator privileges'
                }, status=403)
            
            logger.info(f"[RBAC TPRM DECORATOR] User {user_id} granted admin access")
            return view_func(request, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"[RBAC TPRM DECORATOR] Error checking admin access: {e}")
            return JsonResponse({
                'error': 'Internal server error',
                'message': 'Error checking admin access'
            }, status=500)
    
    return wrapper
