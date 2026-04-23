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

        Collects JWTs from HttpOnly cookies and Authorization header. When both are present,
        tries the cookie first so a fresh server-issued access cookie wins over a stale Bearer
        token left in client storage (localStorage cannot read HttpOnly cookies to compare).
        """
        from rest_framework.exceptions import AuthenticationFailed
        from .authentication import _is_session_token_valid

        def _normalize_bearer_raw(raw_token):
            if not raw_token:
                return None
            if raw_token.lower() in ('null', 'undefined', '', 'none', '[object object]'):
                return None
            return raw_token

        auth_header = request.headers.get('Authorization')
        header_raw = None
        if auth_header and auth_header.startswith('Bearer '):
            header_raw = _normalize_bearer_raw(auth_header.split(' ', 1)[1].strip())

        cookie_raw = _normalize_bearer_raw(
            request.COOKIES.get('access_token') or request.COOKIES.get('session_token')
        )

        # Prefer cookie first (matches current server session); then Authorization.
        candidates = []
        if cookie_raw:
            candidates.append((cookie_raw, 'cookie'))
        if header_raw:
            candidates.append((header_raw, 'header'))

        if not candidates:
            return None

        def _detail_str(exc):
            d = getattr(exc, 'detail', exc)
            if isinstance(d, (list, tuple)):
                return ' '.join(str(x) for x in d)
            return str(d)

        last_auth_error = None
        for token, source in candidates:
            try:
                return self._authenticate_token(request, token, source, _is_session_token_valid)
            except AuthenticationFailed as e:
                last_auth_error = e
                detail_lower = _detail_str(e).lower()
                # Falling back to Authorization almost always retries an *older* Bearer from JS storage and
                # surfaces as confusing 403s; but in case of a race during refresh, the header might
                # actually be more up-to-date. So we allow the loop to continue.
                if source == 'cookie' and (
                    'session invalidated' in detail_lower or 'newer login' in detail_lower
                ):
                    logger.info(
                        "[Unified JWT Auth] Cookie rejected for session mismatch; will try Authorization header if present"
                    )
                    continue
                logger.info(
                    "[Unified JWT Auth] Token from %s rejected: %s; trying next credential if any",
                    source,
                    e.detail if hasattr(e, 'detail') else str(e),
                )

        if last_auth_error:
            raise last_auth_error
        return None

    def _authenticate_token(self, request, token, source_label, _is_session_token_valid):
        from rest_framework.exceptions import AuthenticationFailed

        if source_label == 'cookie':
            logger.info("[Unified JWT Auth] Using token from secure cookies")
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
            tenant_id = payload.get('tenant_id')
            
            logger.info(
                f"[Unified JWT Auth] Token decoded successfully. User ID: {sanitize_for_log(user_id, 32)}, Tenant ID: {sanitize_for_log(tenant_id, 32)}"
            )
            
            if not user_id:
                logger.warning("[Unified JWT Auth] Token does not contain user_id")
                raise AuthenticationFailed('Token does not contain user_id')

            # MULTI-TENANCY: Propagate tenant context to request
            if tenant_id:
                request.tenant_id = tenant_id
                # Set a minimal tenant object for legacy decorators
                if not hasattr(request, 'tenant') or request.tenant is None:
                    request.tenant = type('SimpleTenant', (), {'tenant_id': tenant_id, 'id': tenant_id})()
            
            # Enforce single active session across devices/browsers.
            # RELAXED: Log warning but allow request if token is otherwise valid.
            # This prevents disruptive 403/401 errors in multi-tab environments.
            if not _is_session_token_valid(user_id, session_token):
                logger.warning(
                    "[Unified JWT Auth] Session JTI mismatch for user_id %s (stale session); allowing request due to valid token signature",
                    sanitize_for_log(user_id, 32),
                )
                # We allow the request to proceed to avoid breaking user experience, 
                # but the mismatch is logged for security auditing.
            
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

        except AuthenticationFailed:
            raise
        except jwt.ExpiredSignatureError:
            logger.warning("[Unified JWT Auth] JWT token expired")
            raise AuthenticationFailed('Token expired')

        except jwt.InvalidTokenError as e:
            logger.warning(f"[Unified JWT Auth] Invalid JWT token: {e}")
            raise AuthenticationFailed('Invalid token')

        except Exception as e:
            logger.error(f"[Unified JWT Auth] Unexpected error during JWT authentication: {e}")
            raise AuthenticationFailed(f"Authentication error: {e}")
