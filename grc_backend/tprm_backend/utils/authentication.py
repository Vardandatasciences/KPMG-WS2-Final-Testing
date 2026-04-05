"""
Centralized TPRM Authentication and Permission Classes
"""

import logging
import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied

logger = logging.getLogger(__name__)


class SimpleUser:
    """
    A simple user object for TPRM modules that don't need the full User model
    but need compatibility with DRF's authentication system.
    """
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


class JWTAuthentication(BaseAuthentication):
    """
    Standardized JWT Authentication for all TPRM modules.
    Supports Header (Bearer) and Cookie (access_token/session_token) authentication.
    """
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        # Robust cookie fallback: check for multiple possible cookie names
        if not token:
            token = request.COOKIES.get('access_token') or request.COOKIES.get('session_token')
            if token:
                logger.info(f"[TPRM Auth] Using token from cookie: {'access_token' if request.COOKIES.get('access_token') else 'session_token'}")
        
        if not token:
            return None

        try:
            verification_key = getattr(settings, 'JWT_VERIFYING_KEY', None) or getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
            payload = jwt.decode(
                token,
                verification_key,
                algorithms=getattr(settings, 'JWT_ALLOWED_ALGORITHMS', [getattr(settings, 'JWT_ALGORITHM', 'RS256')]),
                issuer=getattr(settings, 'JWT_ISSUER', None),
                audience=getattr(settings, 'JWT_AUDIENCE', None),
            )
            
            # Support multiple user ID keys in payload
            user_id = payload.get('user_id') or payload.get('userid') or payload.get('UserId') or payload.get('sub')
            username = payload.get('username') or payload.get('UserName') or payload.get('name') or 'Unknown'
            
            if not user_id:
                logger.warning("[TPRM Auth] No user_id in JWT payload")
                raise AuthenticationFailed('Invalid token: missing user_id')
            
            # Get tenant_id from User model and set it on request for multi-tenancy
            try:
                from mfa_auth.models import User
                user_obj = User.objects.get(userid=user_id)
                tenant_id = user_obj.tenant_id if hasattr(user_obj, 'tenant_id') else None
                if tenant_id:
                    request.tenant_id = tenant_id
                    logger.info(f"[TPRM Auth] Set tenant_id {tenant_id} on request for user {user_id}")
                else:
                    logger.warning(f"[TPRM Auth] User {user_id} has no tenant_id")
            except Exception as e:
                logger.warning(f"[TPRM Auth] Could not fetch tenant_id for user {user_id}: {e}")
            
            user = SimpleUser(user_id, username)
            logger.info(f"[TPRM Auth] Successfully authenticated user: {user}")
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            logger.warning("[TPRM Auth] JWT token has expired")
            raise AuthenticationFailed('Token has expired')
        except jwt.DecodeError:
            logger.warning("[TPRM Auth] JWT token decode error")
            raise AuthenticationFailed('Error decoding token')
        except Exception as e:
            logger.error(f"[TPRM Auth] JWT authentication error: {e}")
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')


class SimpleAuthenticatedPermission(BasePermission):
    """
    Standardized permission that only checks if user is authenticated and has a valid userid.
    """
    
    def has_permission(self, request, view):
        is_authenticated = bool(
            request.user and 
            request.user.is_authenticated and
            hasattr(request.user, 'userid')
        )
        
        if not is_authenticated:
            logger.warning(f"[TPRM Auth] Access denied: User not properly authenticated: {request.user}")
        
        return is_authenticated
