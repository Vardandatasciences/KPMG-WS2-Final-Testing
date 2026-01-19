"""
Tenant Context Middleware for Multi-Tenancy Support

This middleware automatically extracts and sets the tenant context for each request.
The tenant can be identified through:
1. Subdomain (e.g., acmecorp.grcplatform.com)
2. JWT token (tenant_id claim)
3. User's tenant_id (from authenticated user)
"""

import logging
import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant, Users

logger = logging.getLogger(__name__)


class TenantContextMiddleware(MiddlewareMixin):
    """
    Middleware to set tenant context on every request
    Adds request.tenant attribute for use throughout the application
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        logger.info("✅ Tenant Context Middleware loaded")
    
    def process_request(self, request):
        """
        Extract tenant from request and add to request.tenant
        """
        # Skip tenant resolution for certain public paths
        skip_paths = [
            '/api/login/',
            '/api/jwt/login/',
            '/api/register/',
            '/admin/',
            '/static/',
            '/media/',
            '/api/test-connection/',
        ]
        
        path = request.path_info
        if any(path.startswith(skip_path) for skip_path in skip_paths):
            request.tenant = None
            request.tenant_id = None
            return None
        
        # Try to get tenant from different sources
        tenant = None
        
        # 1. Try to get tenant from subdomain
        tenant = self._get_tenant_from_subdomain(request)
        
        # 2. If not found, try JWT token
        if not tenant:
            tenant = self._get_tenant_from_jwt(request)
        
        # 3. If not found, try authenticated user
        if not tenant and hasattr(request, 'user') and hasattr(request.user, 'UserId'):
            tenant = self._get_tenant_from_user(request.user)
        
        # Set tenant on request
        request.tenant = tenant
        request.tenant_id = tenant.tenant_id if tenant else None
        
        # MULTI-TENANCY: Set tenant context for automatic tenant_id assignment in models
        if tenant:
            from .tenant_context import set_current_tenant
            set_current_tenant(tenant.tenant_id)
            # logger.debug(f"[Tenant Middleware] Resolved tenant: {tenant.name} (ID: {tenant.tenant_id}) for {request.method} {path}")
        else:
            from .tenant_context import clear_current_tenant
            clear_current_tenant()
            # logger.debug(f"[Tenant Middleware] No tenant resolved for {request.method} {path}")
        
        return None
    
    def _get_tenant_from_subdomain(self, request):
        """
        Extract tenant from subdomain
        Example: acmecorp.grcplatform.com -> subdomain='acmecorp'
        """
        try:
            host = request.get_host().split(':')[0]  # Remove port if present
            parts = host.split('.')
            
            # If subdomain exists (more than 2 parts, e.g., acmecorp.grcplatform.com)
            if len(parts) >= 3:
                subdomain = parts[0]
                
                # Skip common subdomains
                if subdomain in ['www', 'api', 'admin']:
                    return None
                
                # Look up tenant by subdomain
                tenant = Tenant.objects.filter(subdomain=subdomain, status='active').first()
                if tenant:
                    # logger.debug(f"[Tenant Middleware] Found tenant by subdomain: {subdomain}")
                    return tenant
                else:
                    logger.warning(f"[Tenant Middleware] No active tenant found for subdomain: {subdomain}")
        except Exception as e:
            logger.error(f"[Tenant Middleware] Error extracting tenant from subdomain: {e}")
        
        return None
    
    def _get_tenant_from_jwt(self, request):
        """
        Extract tenant from JWT token
        JWT payload should contain 'tenant_id' claim
        """
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                # Decode JWT token
                secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                
                tenant_id = payload.get('tenant_id')
                if tenant_id:
                    tenant = Tenant.objects.filter(tenant_id=tenant_id, status='active').first()
                    if tenant:
                        # logger.debug(f"[Tenant Middleware] Found tenant from JWT: {tenant.name}")
                        return tenant
                    else:
                        logger.warning(f"[Tenant Middleware] No active tenant found for tenant_id: {tenant_id}")
        except jwt.ExpiredSignatureError:
            logger.debug("[Tenant Middleware] JWT token expired during tenant extraction")
        except jwt.InvalidTokenError:
            logger.debug("[Tenant Middleware] Invalid JWT token during tenant extraction")
        except Exception as e:
            logger.error(f"[Tenant Middleware] Error extracting tenant from JWT: {e}")
        
        return None
    
    def _get_tenant_from_user(self, user):
        """
        Extract tenant from authenticated user
        """
        try:
            # Check if user has tenant foreign key
            if hasattr(user, 'tenant') and user.tenant:
                tenant = user.tenant
                if tenant.status == 'active':
                    # logger.debug(f"[Tenant Middleware] Found tenant from user: {tenant.name}")
                    return tenant
                else:
                    logger.warning(f"[Tenant Middleware] User's tenant is not active: {tenant.name}")
            
            # Fallback: Query Users model if user doesn't have tenant loaded
            elif hasattr(user, 'UserId'):
                db_user = Users.objects.select_related('tenant').filter(UserId=user.UserId).first()
                if db_user and db_user.tenant and db_user.tenant.status == 'active':
                    # logger.debug(f"[Tenant Middleware] Found tenant from user query: {db_user.tenant.name}")
                    return db_user.tenant
        except Exception as e:
            logger.error(f"[Tenant Middleware] Error extracting tenant from user: {e}")
        
        return None


class TenantIsolationMiddleware(MiddlewareMixin):
    """
    Middleware to enforce tenant isolation
    Checks that tenant is properly set for all authenticated requests
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        logger.info("✅ Tenant Isolation Middleware loaded")
    
    def process_request(self, request):
        """
        Enforce tenant isolation on authenticated requests
        """
        # Skip isolation check for public paths
        skip_paths = [
            '/api/login/',
            '/api/jwt/login/',
            '/api/register/',
            '/admin/',
            '/static/',
            '/media/',
            '/api/test-connection/',
        ]
        
        path = request.path_info
        if any(path.startswith(skip_path) for skip_path in skip_paths):
            return None
        
        # If user is authenticated but no tenant is set, this is a security issue
        if hasattr(request, 'user') and hasattr(request.user, 'UserId'):
            if not hasattr(request, 'tenant') or request.tenant is None:
                logger.warning(f"[Tenant Isolation] Authenticated request without tenant context: {request.method} {path} by user {request.user.UserId}")
                # For now, just log the warning. In production, you might want to return an error:
                # return JsonResponse({'error': 'Tenant context not found'}, status=403)
    
    def process_response(self, request, response):
        """
        Clear tenant context after request is processed
        """
        from .tenant_context import clear_current_tenant
        clear_current_tenant()
        return response


class AutoTenantFilterMiddleware(MiddlewareMixin):
    """
    EXPERIMENTAL: Middleware to automatically filter all queries by tenant
    This is a proof-of-concept and should be used with caution
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.enabled = getattr(settings, 'AUTO_TENANT_FILTER_ENABLED', False)
        if self.enabled:
            logger.info("⚠️  Auto Tenant Filter Middleware loaded (EXPERIMENTAL)")
    
    def process_request(self, request):
        """
        Automatically add tenant filter to all queries (EXPERIMENTAL)
        """
        if not self.enabled:
            return None
        
        # This would require custom QuerySet manager implementation
        # For now, this is just a placeholder
        # In production, you would use django-tenant-schemas or similar
        
        return None

