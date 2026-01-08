"""
Tenant Utilities for Multi-Tenancy Support

This module provides helper functions and decorators to ensure
all database queries are filtered by tenant.
"""

import logging
from functools import wraps
from django.http import JsonResponse
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


def get_tenant_from_request(request):
    """
    Get tenant from request object
    Returns tenant object or None
    """
    if hasattr(request, 'tenant'):
        return request.tenant
    return None


def get_tenant_id_from_request(request):
    """
    Get tenant_id from request object
    Returns tenant_id (int) or None
    """
    if hasattr(request, 'tenant_id'):
        return request.tenant_id
    elif hasattr(request, 'tenant') and request.tenant:
        return request.tenant.tenant_id
    return None


def filter_queryset_by_tenant(queryset, tenant_id):
    """
    Filter a Django QuerySet by tenant_id
    
    Args:
        queryset: Django QuerySet to filter
        tenant_id: Tenant ID to filter by
    
    Returns:
        Filtered QuerySet
    """
    if tenant_id is None:
        logger.warning("[Tenant Utils] Attempting to filter queryset with tenant_id=None")
        return queryset
    
    # Check if model has tenant field
    model = queryset.model
    if hasattr(model, 'tenant'):
        return queryset.filter(tenant_id=tenant_id)
    else:
        logger.warning(f"[Tenant Utils] Model {model.__name__} does not have tenant field")
        return queryset


def require_tenant(view_func):
    """
    Decorator to ensure request has tenant context
    Returns 403 error if tenant is not found
    
    Usage:
        @require_tenant
        @api_view(['GET'])
        def my_view(request):
            tenant = request.tenant
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'tenant') or request.tenant is None:
            # Get user info for debugging
            user_id = getattr(request.user, 'userid', None) if hasattr(request, 'user') else None
            auth_header = request.headers.get('Authorization', 'No auth header')
            
            logger.warning(f"[Tenant Utils] Tenant required but not found for {request.method} {request.path}")
            logger.warning(f"[Tenant Utils] User ID: {user_id}, Auth header present: {bool(auth_header and auth_header != 'No auth header')}")
            logger.warning(f"[Tenant Utils] Request has tenant attr: {hasattr(request, 'tenant')}, Tenant value: {getattr(request, 'tenant', 'not set')}")
            
            return JsonResponse({
                'error': 'Tenant context not found',
                'detail': 'This endpoint requires tenant authentication. Please ensure your JWT token includes tenant_id.',
                'debug_info': {
                    'user_id': user_id,
                    'has_auth': bool(auth_header and auth_header != 'No auth header'),
                    'path': request.path
                }
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def tenant_filter(view_func):
    """
    Decorator to automatically add tenant filtering to view function
    Adds 'tenant_id' to request for easy filtering
    
    Usage:
        @tenant_filter
        @api_view(['GET'])
        def list_frameworks(request):
            tenant_id = request.tenant_id
            frameworks = Framework.objects.filter(tenant_id=tenant_id)
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Add tenant_id to request for easy access
        if hasattr(request, 'tenant') and request.tenant:
            request.tenant_id = request.tenant.tenant_id
        else:
            # Try to get tenant from user if available
            tenant_id = None
            if hasattr(request, 'user') and request.user:
                try:
                    # Get user_id from request
                    user_id = None
                    if hasattr(request.user, 'userid'):
                        user_id = request.user.userid
                    elif hasattr(request.user, 'id'):
                        user_id = request.user.id
                    elif hasattr(request.user, 'UserId'):
                        user_id = request.user.UserId
                    elif hasattr(request.user, 'user_id'):
                        user_id = request.user.user_id
                    
                    # Extract from JWT if available
                    if not user_id:
                        auth_header = request.headers.get('Authorization', '')
                        if auth_header.startswith('Bearer '):
                            try:
                                import jwt
                                from django.conf import settings
                                token = auth_header.split(' ')[1]
                                secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
                                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                                if payload and 'user_id' in payload:
                                    user_id = payload['user_id']
                            except Exception as e:
                                logger.debug(f"[Tenant Utils] JWT decode error: {e}")
                                pass
                    
                    # Get tenant from user by querying users table directly from tprm_integrations database
                    if user_id:
                        from django.db import connections
                        
                        try:
                            with connections['default'].cursor() as cursor:
                                # Query users table to get tenant_id
                                cursor.execute("""
                                    SELECT TenantId
                                    FROM users
                                    WHERE UserId = %s
                                    LIMIT 1
                                """, [user_id])
                                
                                result = cursor.fetchone()
                                
                                if result and result[0]:
                                    tenant_id = result[0]
                                    logger.debug(f"[Tenant Utils] Found tenant_id {tenant_id} from users table for user_id: {user_id}")
                                else:
                                    logger.debug(f"[Tenant Utils] No tenant_id found in users table for user_id: {user_id}")
                        except Exception as db_error:
                            logger.debug(f"[Tenant Utils] Error querying users table: {db_error}")
                            # Fallback to model-based lookup if raw SQL fails
                            try:
                                from mfa_auth.models import User
                                user = User.objects.get(userid=user_id)
                                if hasattr(user, 'tenant_id'):
                                    tenant_id = user.tenant_id
                                elif hasattr(user, 'tenant') and user.tenant:
                                    tenant_id = user.tenant.tenant_id
                            except Exception as e:
                                logger.debug(f"[Tenant Utils] mfa_auth.User model lookup also failed: {e}")
                                pass
                except Exception as e:
                    logger.error(f"[Tenant Utils] Error extracting tenant: {e}")
            
            request.tenant_id = tenant_id
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


class TenantQuerySet(QuerySet):
    """
    Custom QuerySet that automatically filters by tenant
    
    Usage in models:
        objects = TenantManager()
        
        class Meta:
            base_manager_name = 'objects'
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tenant_id = None
    
    def for_tenant(self, tenant_id):
        """
        Filter queryset by tenant_id
        """
        if hasattr(self.model, 'tenant'):
            return self.filter(tenant_id=tenant_id)
        return self
    
    def for_request(self, request):
        """
        Filter queryset by tenant from request
        """
        tenant_id = get_tenant_id_from_request(request)
        if tenant_id:
            return self.for_tenant(tenant_id)
        return self


def get_tenant_aware_queryset(model, request):
    """
    Get a queryset filtered by tenant from request
    
    Args:
        model: Django model class
        request: Django request object
    
    Returns:
        QuerySet filtered by tenant
    """
    tenant_id = get_tenant_id_from_request(request)
    
    if tenant_id and hasattr(model, 'tenant'):
        return model.objects.filter(tenant_id=tenant_id)
    else:
        return model.objects.all()


def create_with_tenant(model, request, **kwargs):
    """
    Create a model instance with tenant from request
    
    Args:
        model: Django model class
        request: Django request object
        **kwargs: Model field values
    
    Returns:
        Created model instance
    """
    tenant = get_tenant_from_request(request)
    
    if tenant and hasattr(model, 'tenant'):
        kwargs['tenant'] = tenant
    
    return model.objects.create(**kwargs)


def bulk_create_with_tenant(model, request, instances):
    """
    Bulk create model instances with tenant from request
    
    Args:
        model: Django model class
        request: Django request object
        instances: List of model instances (not yet saved)
    
    Returns:
        List of created model instances
    """
    tenant = get_tenant_from_request(request)
    
    if tenant and hasattr(model, 'tenant'):
        for instance in instances:
            instance.tenant = tenant
    
    return model.objects.bulk_create(instances)


def validate_tenant_access(request, obj):
    """
    Validate that user has access to object based on tenant
    
    Args:
        request: Django request object
        obj: Model instance to check
    
    Returns:
        True if access is allowed, False otherwise
    """
    tenant_id = get_tenant_id_from_request(request)
    
    if tenant_id is None:
        logger.warning("[Tenant Utils] Cannot validate tenant access without tenant_id")
        return False
    
    if not hasattr(obj, 'tenant_id'):
        logger.warning(f"[Tenant Utils] Object {obj.__class__.__name__} does not have tenant_id")
        return True  # Allow access if object doesn't have tenant_id
    
    return obj.tenant_id == tenant_id


def get_or_404_with_tenant(model, request, **kwargs):
    """
    Get object filtered by tenant or return 404
    
    Args:
        model: Django model class
        request: Django request object
        **kwargs: Filter criteria
    
    Returns:
        Model instance or raises Http404
    """
    from django.shortcuts import get_object_or_404
    
    tenant_id = get_tenant_id_from_request(request)
    
    if tenant_id and hasattr(model, 'tenant'):
        kwargs['tenant_id'] = tenant_id
    
    return get_object_or_404(model, **kwargs)

