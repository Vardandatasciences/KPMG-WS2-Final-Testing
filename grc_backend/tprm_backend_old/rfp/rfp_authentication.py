"""
RFP Authentication Module
Provides JWT authentication and RBAC integration for RFP views
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from django.conf import settings
import jwt
import logging

# Use Unified JWT Authentication from GRC
from grc.jwt_auth import UnifiedJWTAuthentication

logger = logging.getLogger(__name__)


# REMOVED BUGGY LOCAL JWT CLASS - Using UnifiedJWTAuthentication from grc.jwt_auth instead


class SimpleAuthenticatedPermission(BasePermission):
    """Custom permission class that checks for authenticated users"""
    def has_permission(self, request, view):
        # Just check if user object exists and is authenticated
        # UnifiedJWTAuthentication handles GRC/TPRM user verification
        if request.user and hasattr(request.user, 'is_authenticated'):
            return request.user.is_authenticated
        return False



class RFPPermission(BasePermission):
    """
    Custom permission class that checks both authentication and RBAC permissions
    This is specifically for RFP ViewSets
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
        
        # Map HTTP methods to RFP permissions
        permission_map = {
            'GET': 'view_rfp',
            'HEAD': 'view_rfp',
            'OPTIONS': 'view_rfp',
            'POST': 'create_rfp',
            'PUT': 'edit_rfp',
            'PATCH': 'edit_rfp',
            'DELETE': 'delete_rfp',
        }
        
        required_permission = permission_map.get(request.method, 'view_rfp')
        
        logger.info(f"[RFP Permission] Checking {required_permission} for user {user_id}, method {request.method}")
        
        # Check if user has the required permission
        has_permission = RBACTPRMUtils.check_rfp_permission(user_id, required_permission)
        
        if not has_permission:
            logger.warning(f"[RFP Permission] User {user_id} denied RFP access: {required_permission}")
            raise PermissionDenied(f'You do not have permission to {required_permission.replace("_", " ")}')
        
        logger.info(f"[RFP Permission] User {user_id} granted RFP access: {required_permission}")
        return True


# For backward compatibility with existing RFP views that use DRF viewsets
class RFPAuthenticationMixin:
    """
    Mixin to add JWT authentication and RBAC to RFP viewsets
    Usage: class MyViewSet(RFPAuthenticationMixin, viewsets.ModelViewSet):
    """
    authentication_classes = [UnifiedJWTAuthentication]
    permission_classes = [RFPPermission]  # Changed from SimpleAuthenticatedPermission to RFPPermission


# Export the authentication classes
__all__ = [
    'UnifiedJWTAuthentication',
    'SimpleAuthenticatedPermission',
    'RFPPermission',
    'RFPAuthenticationMixin'
]

