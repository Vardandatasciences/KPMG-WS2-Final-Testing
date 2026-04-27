"""
Tenant Utilities for Multi-Tenancy Support

This module provides helper functions and decorators to ensure
all database queries are filtered by tenant.
"""

import logging
import json
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
    Get tenant_id from request object.
    
    PRIMARY SOURCE OF TRUTH: request.user (resolved by UnifiedJWTAuthentication)
    """
    # 1. Prioritize pre-resolved tenant on request (set by middleware or previous decorators)
    if hasattr(request, "tenant_id") and request.tenant_id:
        return request.tenant_id
    
    if hasattr(request, "tenant") and request.tenant:
        if hasattr(request.tenant, "tenant_id"):
            return request.tenant.tenant_id
        return request.tenant

    # 2. Extract from Authenticated User
    if hasattr(request, 'user') and request.user and request.user.is_authenticated:
        # Check for tenant_id attribute on User object
        tid = getattr(request.user, 'tenant_id', None)
        if tid:
            request.tenant_id = tid # Cache it for subsequent calls
            return tid
        
        # Fallback: Query Users model if not on request.user
        try:
            from .models import Users
            user_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))
            if user_id:
                user_obj = Users.objects.filter(UserId=user_id).first()
                if user_obj and user_obj.tenant_id:
                    request.tenant_id = user_obj.tenant_id
                    return user_obj.tenant_id
        except Exception:
            pass

    # 3. Fallback: resolve tenant from JWT in cookie/header.
    # Some endpoints (like multipart uploads) intentionally disable DRF auth classes,
    # so request.user may not be hydrated even though auth cookies are present.
    try:
        token = None
        if hasattr(request, "COOKIES"):
            token = request.COOKIES.get("access_token") or request.COOKIES.get("session_token")

        if not token:
            auth_header = request.headers.get("Authorization", "") or request.META.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()

        if token:
            from .authentication import verify_jwt_token
            payload = verify_jwt_token(token)
            if payload:
                tid = payload.get("tenant_id") or payload.get("tenantId")
                if tid:
                    request.tenant_id = tid
                    return tid
    except Exception:
        pass

    # 4. Fallback: resolve tenant from session user_id when JWT is unavailable.
    try:
        from .models import Users
        session_user_id = None
        if hasattr(request, "session"):
            session_user_id = request.session.get("user_id") or request.session.get("userid")
        if session_user_id:
            user_obj = Users.objects.filter(UserId=session_user_id).first()
            if user_obj and user_obj.tenant_id:
                request.tenant_id = user_obj.tenant_id
                return user_obj.tenant_id
    except Exception:
        pass

    # 5. Fallback: try the advanced resolver from tenant_context (JWT/Subdomain resolution)

    try:
        from .utils.tenant_context import (
            get_tenant_id_from_request as resolve_tenant_from_context,
        )
        resolved_tid = resolve_tenant_from_context(request)
        if resolved_tid:
            request.tenant_id = resolved_tid
            return resolved_tid
    except Exception:
        pass

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
    SECURE decorator to ensure request has valid tenant context.
    
    ENFORCEMENT RULES:
    1. ALWAYS resolve tenant from authenticated session (JWT/Cookies) first.
    2. If a tenant_id is passed by client (body/params), VALIDATE it matches session.
    3. REJECT request if tenant context is missing or mismatched (BOLA protection).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        from .models import Users, Tenant
        
        # 1. Resolve Secure Tenant Context (Server-Side)
        session_tenant_id = None
        
        # Check authenticated user
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            session_tenant_id = getattr(request.user, 'tenant_id', None)
            if not session_tenant_id:
                try:
                    user_id = getattr(request.user, 'UserId', getattr(request.user, 'id', None))
                    user_obj = Users.objects.filter(UserId=user_id).first()
                    if user_obj:
                        session_tenant_id = user_obj.tenant_id
                except Exception:
                    pass
        
        # Try JWT fallback if no user object (early auth stage). Prefer HttpOnly cookie over Bearer.
        if not session_tenant_id:
            cookie_tok = None
            if hasattr(request, 'COOKIES'):
                cookie_tok = request.COOKIES.get('access_token')
            auth_header = request.headers.get('Authorization', '') or request.META.get('HTTP_AUTHORIZATION', '')
            header_tok = auth_header.split(' ', 1)[1].strip() if auth_header.startswith('Bearer ') else None
            try:
                from .authentication import verify_jwt_token
                for raw in (cookie_tok, header_tok):
                    if not raw:
                        continue
                    payload = verify_jwt_token(raw)
                    if payload:
                        session_tenant_id = payload.get('tenant_id') or payload.get('tenantId')
                        if session_tenant_id:
                            break
            except Exception:
                pass

        # 2. Extract Client-Supplied Tenant (for validation purposes)
        client_tenant_id = None
        if request.method == 'GET':
            client_tenant_id = request.GET.get('tenant_id') or request.GET.get('tenantId')
        elif request.method in ['POST', 'PUT', 'PATCH']:
            if getattr(request, 'data', None) and isinstance(request.data, dict):
                client_tenant_id = request.data.get('tenant_id') or request.data.get('tenantId')
            elif request.content_type and 'application/json' in request.content_type:
                try:
                    raw_body = getattr(request, 'body', None)
                    if raw_body:
                        data = json.loads(raw_body)
                        client_tenant_id = data.get('tenant_id') or data.get('tenantId')
                except Exception:
                    pass
            elif hasattr(request, 'POST'):
                client_tenant_id = request.POST.get('tenant_id') or request.POST.get('tenantId')

        # 3. Security Validation (Cross-Check)
        if session_tenant_id:
            # Normalize to integer if possible
            try: session_tenant_id = int(session_tenant_id)
            except: pass
            
            if client_tenant_id:
                try: client_tenant_id = int(client_tenant_id)
                except: pass
                
                # BOLA PROTECTION: Client-supplied ID MUST match session ID
                if str(client_tenant_id) != str(session_tenant_id):
                    logger.warning(f"[SECURITY BOLA] Tenant mismatch for user {getattr(request.user, 'UserId', 'Unknown')}. Session: {session_tenant_id}, Client: {client_tenant_id}")
                    return JsonResponse({
                        'error': 'Access Denied',
                        'detail': 'Tenant context mismatch'
                    }, status=403)
            
            # Context is valid
            request.tenant_id = session_tenant_id
            
            # Optional: Hydrate request.tenant object if not already present
            if not hasattr(request, 'tenant') or request.tenant is None:
                try:
                    request.tenant = Tenant.objects.get(tenant_id=session_tenant_id, status='active')
                except Tenant.DoesNotExist:
                    # If tenant record missing/inactive, still allow through if we have the ID, 
                    # but let views handle "No tenant found" if needed.
                    pass
            
            return view_func(request, *args, **kwargs)
        
        # 4. Fail-Safe: No valid tenant context found
        logger.warning(f"[Tenant Utils] Tenant required but missing for {request.method} {request.path}")
        try:
            if request.method == 'POST' and hasattr(request, 'POST'):
                logger.warning(
                    "[Tenant Utils] POST data when tenant missing: keys=%s user_id=%s",
                    list(request.POST.keys()),
                    request.POST.get('user_id'),
                )
        except Exception as log_err:
            logger.warning(f"[Tenant Utils] Error while logging missing tenant details: {log_err}")
        if hasattr(request, 'data'):
            from rest_framework.response import Response
            return Response({
                'error': 'Authentication required',
                'detail': 'This endpoint requires a valid session or tenant context'
            }, status=401)
        return JsonResponse({
            'error': 'Authentication required',
            'detail': 'This endpoint requires a valid session or tenant context'
        }, status=401)

    # Preserve DRF attributes for @api_view (walk __wrapped__ — csrf_exempt etc. may sit in the chain)
    _chain = []
    _f = view_func
    while _f is not None:
        _chain.append(_f)
        _f = getattr(_f, '__wrapped__', None)
    for _attr in ('authentication_classes', 'permission_classes', 'schema'):
        for _inner in _chain:
            if hasattr(_inner, _attr):
                setattr(wrapper, _attr, getattr(_inner, _attr))
                break
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
                    from ..models import Users
                    # Try to get user_id from request
                    user_id = None
                    if hasattr(request.user, 'UserId'):
                        user_id = request.user.UserId
                    elif hasattr(request.user, 'id'):
                        user_id = request.user.id
                    elif hasattr(request.user, 'user_id'):
                        user_id = request.user.user_id
                    
                    # Extract from JWT if available
                    if not user_id:
                        auth_header = request.headers.get('Authorization', '')
                        if auth_header.startswith('Bearer '):
                            try:
                                from ..authentication import verify_jwt_token
                                token = auth_header.split(' ')[1]
                                payload = verify_jwt_token(token)
                                if payload and 'user_id' in payload:
                                    user_id = payload['user_id']
                            except:
                                pass
                    
                    # Get tenant from user
                    if user_id:
                        try:
                            user = Users.objects.get(UserId=user_id)
                            if hasattr(user, 'tenant_id'):
                                tenant_id = user.tenant_id
                            elif hasattr(user, 'tenant') and user.tenant:
                                tenant_id = user.tenant.tenant_id
                        except Users.DoesNotExist:
                            pass
                except Exception:
                    # If anything fails, tenant_id remains None
                    pass
            
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


# Example usage in views:
"""
from grc.tenant_utils import require_tenant, tenant_filter, get_tenant_aware_queryset

@require_tenant  # Ensures tenant is present
@tenant_filter  # Adds tenant_id to request
@api_view(['GET'])
def list_frameworks(request):
    # Option 1: Manual filtering
    frameworks = Framework.objects.filter(tenant_id=request.tenant_id)
    
    # Option 2: Using helper function
    frameworks = get_tenant_aware_queryset(Framework, request)
    
    # Option 3: Direct filter
    frameworks = filter_queryset_by_tenant(Framework.objects.all(), request.tenant_id)
    
    # ... rest of view
"""

