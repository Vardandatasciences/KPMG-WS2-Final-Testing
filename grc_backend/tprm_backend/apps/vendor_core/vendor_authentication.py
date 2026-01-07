"""
Vendor Authentication and Permission Classes
Similar to RFP authentication but for Vendor module
"""

import logging
import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied

logger = logging.getLogger(__name__)


class JWTAuthentication(BaseAuthentication):
    """
    Custom JWT Authentication for Vendor module
    """
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            logger.warning("[Vendor Auth] No Authorization header provided")
            return None
        
        if not auth_header.startswith('Bearer '):
            logger.warning("[Vendor Auth] Invalid Authorization header format")
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            
            user_id = payload.get('user_id')
            username = payload.get('username', 'Unknown')
            
            if not user_id:
                logger.warning("[Vendor Auth] No user_id in JWT payload")
                raise AuthenticationFailed('Invalid token: missing user_id')
            
            # Get tenant_id from User model and set it on request for multi-tenancy
            try:
                from mfa_auth.models import User
                user_obj = User.objects.get(userid=user_id)
                tenant_id = user_obj.tenant_id if hasattr(user_obj, 'tenant_id') else None
                if tenant_id:
                    request.tenant_id = tenant_id
                    logger.info(f"[Vendor Auth] Set tenant_id {tenant_id} on request for user {user_id}")
                else:
                    logger.warning(f"[Vendor Auth] User {user_id} has no tenant_id")
            except Exception as e:
                logger.warning(f"[Vendor Auth] Could not fetch tenant_id for user {user_id}: {e}")
            
            # Create a simple user object
            class SimpleUser:
                def __init__(self, userid, username):
                    self.userid = userid
                    self.id = userid  # Add id attribute for DRF compatibility
                    self.pk = userid  # Add pk attribute for DRF throttling and other features
                    self.username = username
                    self.is_authenticated = True
                    
                def __str__(self):
                    return f"User({self.username}, id={self.userid})"
                
                def __repr__(self):
                    return f"SimpleUser(pk={self.pk}, username='{self.username}')"
            
            user = SimpleUser(user_id, username)
            logger.info(f"[Vendor Auth] Successfully authenticated user: {user}")
            
            return (user, None)
            
        except jwt.ExpiredSignatureError:
            logger.warning("[Vendor Auth] JWT token has expired")
            raise AuthenticationFailed('Token has expired')
        except jwt.DecodeError:
            logger.warning("[Vendor Auth] JWT token decode error")
            raise AuthenticationFailed('Error decoding token')
        except Exception as e:
            logger.error(f"[Vendor Auth] JWT authentication error: {e}")
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')


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
        # Use force_refresh=True to always get fresh data from database, bypassing ORM cache
        # This ensures that recently granted permissions are immediately recognized
        has_permission = RBACTPRMUtils.check_vendor_permission(user_id, required_permission, force_refresh=True)
        
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
    authentication_classes = [JWTAuthentication]
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

