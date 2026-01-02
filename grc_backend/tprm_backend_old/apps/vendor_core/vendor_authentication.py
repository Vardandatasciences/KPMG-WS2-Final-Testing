"""
Vendor Authentication and Permission Classes
Similar to RFP authentication but for Vendor module
"""

import logging
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

# Use Unified JWT Authentication from GRC
from grc.jwt_auth import UnifiedJWTAuthentication

logger = logging.getLogger(__name__)

# REMOVED BUGGY LOCAL JWT CLASS - Using UnifiedJWTAuthentication from grc.jwt_auth instead
# For backward compatibility, export UnifiedJWTAuthentication as JWTAuthentication
JWTAuthentication = UnifiedJWTAuthentication


class SimpleAuthenticatedPermission(BasePermission):
    """
    Basic permission that only checks if user is authenticated
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        is_authenticated = bool(
            request.user and 
            request.user.is_authenticated and
            hasattr(request.user, 'userid')
        )
        
        if not is_authenticated:
            from django.contrib.auth.models import AnonymousUser
            if isinstance(request.user, AnonymousUser):
                logger.warning("[Vendor Auth] Anonymous user attempting access")
            else:
                logger.warning(f"[Vendor Auth] User not properly authenticated: {request.user}")
        
        return is_authenticated


class VendorPermission(BasePermission):
    """
    Custom permission class that checks both authentication and RBAC permissions
    This is specifically for Vendor ViewSets
    """
    
    def has_permission(self, request, view):
        # First check authentication
        is_authenticated = bool(
            request.user and 
            request.user.is_authenticated and
            hasattr(request.user, 'userid')
        )
        
        if not is_authenticated:
            from django.contrib.auth.models import AnonymousUser
            if isinstance(request.user, AnonymousUser):
                raise NotAuthenticated('Authentication credentials were not provided.')
            return False
        
        # Then check RBAC permissions
        from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
        from rest_framework.exceptions import PermissionDenied
        
        user_id = request.user.userid
        
        # Map HTTP methods to Vendor permissions
        permission_map = {
            'GET': 'view_vendors',
            'HEAD': 'view_vendors',
            'OPTIONS': 'view_vendors',
            'POST': 'create_vendor',
            'PUT': 'update_vendor',
            'PATCH': 'update_vendor',
            'DELETE': 'delete_vendor',
        }
        
        required_permission = permission_map.get(request.method, 'view_vendors')
        
        logger.info(f"[Vendor Permission] Checking {required_permission} for user {user_id}, method {request.method}")
        
        # Check if user has the required permission
        has_permission = RBACTPRMUtils.check_vendor_permission(user_id, required_permission)
        
        if not has_permission:
            logger.warning(f"[Vendor Permission] User {user_id} denied Vendor access: {required_permission}")
            raise PermissionDenied(f'You do not have permission to {required_permission} vendors')
        
        logger.info(f"[Vendor Permission] User {user_id} granted Vendor access: {required_permission}")
        return True


# For backward compatibility with existing Vendor views that use DRF viewsets
class VendorAuthenticationMixin:
    """
    Mixin to add JWT authentication and vendor permission to viewsets
    """
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [VendorPermission]
    
    def get_authenticators(self):
        """
        Instantiates and returns the list of authenticators that this view can use
        """
        return [auth() for auth in self.authentication_classes]
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires
        """
        return [permission() for permission in self.permission_classes]

