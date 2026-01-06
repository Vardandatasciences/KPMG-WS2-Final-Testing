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

logger = logging.getLogger(__name__)


class JWTAuthentication(BaseAuthentication):
    """JWT Authentication for RFP endpoints - matches contract module implementation"""
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        # Debug logging
        logger.info(f"[RFP JWT Auth] Path: {request.path}")
        logger.info(f"[RFP JWT Auth] Authorization header present: {bool(auth_header)}")
        
        # If no authorization header, return None to allow other auth methods
        if not auth_header:
            logger.warning(f"[RFP JWT Auth] No Authorization header for {request.path}")
            return None
        
        # If authorization header exists but doesn't start with Bearer, raise error
        if not auth_header.startswith('Bearer '):
            raise AuthenticationFailed('Invalid authentication header format. Expected: Bearer <token>')
        
        try:
            token = auth_header.split(' ')[1]
            logger.info(f"[RFP JWT Auth] Token extracted: {token[:20]}...")
            
            # Use JWT_SECRET_KEY from settings
            secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            logger.info(f"[RFP JWT Auth] Token decoded successfully, user_id: {user_id}")
            
            if user_id:
                try:
                    from mfa_auth.models import User
                    user = User.objects.get(userid=user_id)
                    # Add is_authenticated attribute for DRF compatibility
                    user.is_authenticated = True
                    logger.info(f"[RFP JWT Auth] User authenticated: {user.username}")
                    return (user, token)
                except (User.DoesNotExist, ImportError):
                    # If User model doesn't exist or user not found, create a mock user
                    logger.warning(f"[RFP JWT Auth] User {user_id} not found, creating mock user")
                    
                    class MockUser:
                        def __init__(self, user_id):
                            self.userid = user_id
                            self.username = f"user_{user_id}"
                            self.is_authenticated = True
                    
                    return (MockUser(user_id), token)
            else:
                logger.error("[RFP JWT Auth] Token does not contain user_id")
                raise AuthenticationFailed('Token does not contain user_id')
                
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            logger.error(f"JWT authentication error: {str(e)}")
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return 'Bearer realm="api"'


class SimpleAuthenticatedPermission(BasePermission):
    """Custom permission class that checks for authenticated users"""
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        is_authenticated = bool(
            request.user and 
            request.user.is_authenticated and
            hasattr(request.user, 'userid')
        )
        
        # If not authenticated, we need to check if it's because no auth was provided
        # or because auth failed. If request.user is AnonymousUser, no auth was provided.
        if not is_authenticated:
            from django.contrib.auth.models import AnonymousUser
            if isinstance(request.user, AnonymousUser):
                # No authentication was provided - return 401
                raise NotAuthenticated('Authentication credentials were not provided.')
        
        return is_authenticated


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
        from rbac.tprm_utils import RBACTPRMUtils
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [RFPPermission]  # Changed from SimpleAuthenticatedPermission to RFPPermission


# Export the authentication classes
__all__ = [
    'JWTAuthentication',
    'SimpleAuthenticatedPermission',
    'RFPPermission',
    'RFPAuthenticationMixin'
]

