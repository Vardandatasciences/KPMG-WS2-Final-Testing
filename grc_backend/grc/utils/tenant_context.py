"""
Tenant Context Utility

Provides utilities to get tenant_id from request context.
This is used to automatically inject tenant_id when saving models.
"""

from typing import Optional
from django.http import HttpRequest


def get_tenant_id_from_request(request: Optional[HttpRequest] = None) -> Optional[int]:
    """
    Get tenant_id from request context.
    
    Tries multiple methods:
    1. From request.tenant (set by middleware)
    2. From JWT token (tenant_id in payload)
    3. From user's tenant_id (if user has tenant_id field)
    4. From session
    
    Args:
        request: Django request object
        
    Returns:
        tenant_id (int) or None if not found
    """
    if not request:
        return None
    
    # Method 1: Check if middleware set request.tenant
    if hasattr(request, 'tenant') and request.tenant:
        if hasattr(request.tenant, 'tenant_id'):
            return request.tenant.tenant_id
        elif isinstance(request.tenant, int):
            return request.tenant
    
    # Method 2: Check JWT token for tenant_id
    try:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            from ..authentication import verify_jwt_token
            token = auth_header.split(' ')[1]
            payload = verify_jwt_token(token)
            if payload and 'tenant_id' in payload:
                return payload['tenant_id']
    except Exception:
        pass
    
    # Method 3: Get tenant_id from user
    try:
        user_id = None
        
        # Try to get user_id from various sources
        if hasattr(request, 'user') and hasattr(request.user, 'id'):
            user_id = request.user.id
        elif hasattr(request, 'session') and 'user_id' in request.session:
            user_id = request.session.get('user_id')
        elif hasattr(request, 'headers') and 'X-User-Id' in request.headers:
            user_id = request.headers.get('X-User-Id')
        
        if user_id:
            from ..models import Users
            try:
                user = Users.objects.get(UserId=user_id)
                # Check if user has tenant_id field
                if hasattr(user, 'tenant_id') and user.tenant_id:
                    return user.tenant_id
            except Users.DoesNotExist:
                pass
    except Exception:
        pass
    
    # Method 4: Check session for tenant_id
    if hasattr(request, 'session') and 'tenant_id' in request.session:
        return request.session.get('tenant_id')
    
    return None


def get_current_tenant_id() -> Optional[int]:
    """
    Get tenant_id from thread-local context.
    This is set by middleware or view context.
    """
    try:
        from threading import local
        if not hasattr(local, 'tenant_context'):
            return None
        return local.tenant_context.get('tenant_id')
    except Exception:
        return None


def set_current_tenant_id(tenant_id: int):
    """
    Set tenant_id in thread-local context.
    Used by middleware to set tenant context.
    """
    try:
        from threading import local
        if not hasattr(local, 'tenant_context'):
            local.tenant_context = {}
        local.tenant_context['tenant_id'] = tenant_id
    except Exception:
        pass


