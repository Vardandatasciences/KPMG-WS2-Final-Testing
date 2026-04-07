"""
Unified JWT Authentication for GRC and TPRM
This module provides a single, robust JWT authentication class that works for both GRC and TPRM modules.
"""
import jwt
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from .utils.log_sanitize import sanitize_for_log

logger = logging.getLogger(__name__)


class UnifiedJWTAuthentication(BaseAuthentication):
    """
    Custom JWT authentication for DRF that authenticates users based on JWT tokens.
    Works for both GRC and TPRM modules with GRC user credentials.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        Checks for JWT token in:
        1. Authorization header (Bearer <token>)
        2. 'access_token' cookie
        3. 'session_token' cookie
        """
        from rest_framework.exceptions import AuthenticationFailed
        from .authentication import _is_session_token_valid
        
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            raw_token = auth_header.split(' ')[1]
            # Filter out degenerate tokens from stale frontend storage (e.g. "null", "undefined")
            if raw_token and raw_token.lower() not in ('null', 'undefined', '', 'none', '[object object]'):
                token = raw_token
        
        # Fallback to cookies if no valid token in header (prioritize secure HttpOnly cookies)
        if not token:
            token = request.COOKIES.get('access_token') or request.COOKIES.get('session_token')
            if token:
                logger.info("[Unified JWT Auth] Using token from secure cookies")
        
        if not token:
            return None
        
        try:
            # Decode JWT token with centralized algorithm/key configuration.
            verification_key = getattr(settings, 'JWT_VERIFYING_KEY', None) or getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
            payload = jwt.decode(
                token,
                verification_key,
                algorithms=getattr(settings, 'JWT_ALLOWED_ALGORITHMS', [getattr(settings, 'JWT_ALGORITHM', 'RS256')]),
                issuer=getattr(settings, 'JWT_ISSUER', None),
                audience=getattr(settings, 'JWT_AUDIENCE', None),
            )
            
            user_id = payload.get('user_id')
            username = payload.get('username')
            session_token = payload.get('jti')
            
            logger.info(f"[Unified JWT Auth] Token decoded successfully, user_id: {user_id}, username: {username}")
            
            if not user_id:
                logger.warning("[Unified JWT Auth] Token does not contain user_id")
                raise AuthenticationFailed('Token does not contain user_id')

            # Enforce single active session across devices/browsers.
            if not _is_session_token_valid(user_id, session_token):
                logger.warning(
                    "[Unified JWT Auth] Session invalidated for user_id %s",
                    sanitize_for_log(user_id, 32),
                )
                raise AuthenticationFailed('Session invalidated due to newer login')
            
            # Try to get the user from the database
            User = get_user_model()
            
            try:
                user = User.objects.get(pk=user_id)
                
                # Ensure the user object has is_authenticated property
                if not hasattr(user, 'is_authenticated'):
                    user.is_authenticated = True
                
                # Add userid and UserId for compatibility across all GRC/TPRM modules
                if not hasattr(user, 'userid'):
                    user.userid = user.pk
                if not hasattr(user, 'UserId'):
                    user.UserId = user.pk
                
                logger.info(
                    "[Unified JWT Auth] GRC User authenticated: %s",
                    sanitize_for_log(user.username, 128),
                )
                return (user, token)
                
            except User.DoesNotExist:
                logger.warning(
                    "[Unified JWT Auth] User with ID %s not found in database. Creating MockUser.",
                    sanitize_for_log(user_id, 32),
                )
                
                # Create a mock user for cases where user might not exist in local DB
                class MockUser:
                    def __init__(self, user_id, username):
                        self.pk = user_id
                        self.id = user_id
                        self.userid = user_id
                        self.username = username if username else f"user_{user_id}"
                        self.is_authenticated = True
                        self.is_active = True
                        self.is_staff = False
                        self.is_superuser = False
                    
                    def __str__(self):
                        return self.username
                    
                    def get_full_name(self):
                        return self.username
                    
                    def get_short_name(self):
                        return self.username
                
                mock_user = MockUser(user_id, username)
                logger.info(
                    "[Unified JWT Auth] MockUser created: %s",
                    sanitize_for_log(mock_user.username, 128),
                )
                return (mock_user, token)
                
            except Exception:
                logger.exception(
                    "[Unified JWT Auth] Database error during user lookup for user_id=%s",
                    sanitize_for_log(user_id, 32),
                )

                # For database errors, still create a MockUser to allow access
                class MockUser:
                    def __init__(self, user_id, username):
                        self.pk = user_id
                        self.id = user_id
                        self.userid = user_id
                        self.username = username if username else f"user_{user_id}"
                        self.is_authenticated = True
                        self.is_active = True
                        self.is_staff = False
                        self.is_superuser = False
                    
                    def __str__(self):
                        return self.username
                    
                    def get_full_name(self):
                        return self.username
                    
                    def get_short_name(self):
                        return self.username
                
                mock_user = MockUser(user_id, username)
                logger.warning(
                    "[Unified JWT Auth] Database error, using MockUser: %s",
                    sanitize_for_log(mock_user.username, 128),
                )
                return (mock_user, token)
        
        except jwt.ExpiredSignatureError:
            logger.warning("[Unified JWT Auth] JWT token expired")
            raise AuthenticationFailed('Token expired')
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"[Unified JWT Auth] Invalid JWT token: {e}")
            raise AuthenticationFailed('Invalid token')
        
        except Exception as e:
            logger.error(f"[Unified JWT Auth] Unexpected error during JWT authentication: {e}")
            raise AuthenticationFailed(f"Authentication error: {e}")
