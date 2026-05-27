import jwt
import logging
import sys
import time
import re
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import Users, ProductVersion
from .authentication import verify_jwt_token, _compare_versions
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .rbac.utils import RBACUtils
from django.core.cache import cache
import hmac
import hashlib
import json
from urllib.parse import urlparse
from .utils.log_sanitize import sanitize_for_log, mask_sensitive_data

logger = logging.getLogger(__name__)


def _safe_path_for_log(path: str) -> str:
    return sanitize_for_log(path or "", max_len=512)

class ObjectLevelAuthorizationMiddleware(MiddlewareMixin):
    """
    Framework-level IDOR protection.

    If a URL contains a user identifier (e.g. /.../<user_id>/...), enforce:
    - self access is allowed
    - system admin can access any user
    - all others are denied (403)
    """

    USER_ID_KWARG_NAMES = ("user_id", "userid", "userId")
    USER_ID_QUERY_PARAM_NAMES = ("user_id", "userId", "UserId", "current_user_id")

    def process_view(self, request, view_func, view_args, view_kwargs):
        try:
            requested_user_id = None

            # 1) URL path params (/<user_id>/)
            if view_kwargs:
                for key in self.USER_ID_KWARG_NAMES:
                    if key in view_kwargs:
                        requested_user_id = view_kwargs.get(key)
                        break

            # 2) Query params (?user_id=...) — enforce on GET to prevent IDOR enumeration.
            if requested_user_id is None and request.method == "GET":
                for key in self.USER_ID_QUERY_PARAM_NAMES:
                    if key in request.GET:
                        requested_user_id = request.GET.get(key)
                        break

                # DRF Request compatibility (some views use request.query_params)
                if requested_user_id is None and hasattr(request, "query_params"):
                    for key in self.USER_ID_QUERY_PARAM_NAMES:
                        v = request.query_params.get(key)
                        if v is not None:
                            requested_user_id = v
                            break

            if requested_user_id is None:
                return None

            # Allow known public flows that include user identifiers via other mechanisms
            # (We keep this narrow. Token-based public endpoints should not use user_id in path.)
            path = request.path_info or ""
            if path.startswith("/api/get-user-email/"):
                return None

            requester_user_id = RBACUtils.get_user_id_from_request(request)
            if not requester_user_id:
                return JsonResponse({"error": "Authentication required"}, status=401)

            try:
                requested_user_id_int = int(str(requested_user_id))
                requester_user_id_int = int(str(requester_user_id))
            except (TypeError, ValueError):
                return JsonResponse({"error": "Invalid user id"}, status=400)

            if requester_user_id_int == requested_user_id_int:
                return None

            if RBACUtils.is_system_admin(requester_user_id_int):
                return None

            return JsonResponse({"error": "Forbidden"}, status=403)
        except Exception as e:
            logger.error(f"[ObjectLevelAuthorizationMiddleware] Error: {e}")
            # Fail closed: if we can't evaluate, deny access to avoid IDOR.
            return JsonResponse({"error": "Forbidden"}, status=403)

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Simple Request Logging Middleware
    Only logs when ENABLE_DEBUG_LOGGING=true (controlled via env)
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        if getattr(settings, 'ENABLE_DEBUG_LOGGING', False):
            print("\n" + "="*80, file=sys.stdout, flush=True)
            print("✅ REQUEST LOGGING MIDDLEWARE LOADED - ALL REQUESTS WILL BE LOGGED", file=sys.stdout, flush=True)
            print("="*80 + "\n", file=sys.stdout, flush=True)
    
    def process_request(self, request):
        """Log every incoming request (only when ENABLE_DEBUG_LOGGING=true)"""
        if not getattr(settings, 'ENABLE_DEBUG_LOGGING', False):
            return None
        timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
        print(f"🔵 [{timestamp}] {request.method} {request.path}", file=sys.stdout, flush=True)
        return None
    
    def process_response(self, request, response):
        """Log response status (only when ENABLE_DEBUG_LOGGING=true)"""
        if not getattr(settings, 'ENABLE_DEBUG_LOGGING', False):
            return response
        timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
        status_code = response.status_code
        status_emoji = "✅" if 200 <= status_code < 300 else "❌"
        print(f"{status_emoji} [{timestamp}] {request.method} {request.path} - {status_code}", file=sys.stdout, flush=True)
        return response

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """
    JWT Authentication Middleware
    Verifies JWT tokens and sets user in request
    Supports both JWT and session authentication
    """
    
    def process_request(self, request):
        """Process incoming request and verify JWT token or session"""
        
        # Framework-level policy: authenticate by default.
        # Only allow a narrow, explicit set of public endpoints here.
        #
        # IMPORTANT: Do not add broad prefixes like `/api/documents/`, `/api/jira/`,
        # `/api/external-applications/`, or `/api/users/` to this list. Those are sensitive.
        public_path_prefixes = [
            # Auth / session bootstrap
            '/api/login/',
            '/api/v1.0/login/',  # Versioned login (v1.0)
            '/api/v2.0/login/',  # Versioned login (v2.0)
            '/api/jwt/login/',
            '/api/jwt/refresh/',
            '/api/jwt/verify/',
            '/api/jwt/accept-consent/',
            '/api/jwt/mfa/',  # OTP verify/resend during login
            '/api/register/',
            '/api/send-otp/',
            '/api/verify-otp/',
            '/api/reset-password/',
            '/api/get-user-email/',

            # OAuth callbacks must be reachable without existing JWT
            '/api/google/oauth/',
            '/api/google/oauth-callback/',
            '/api/google/oauth-callback-payload/',
            '/api/google-oauth/initiate/',
            '/api/google-oauth/callback/',
            '/api/google-oauth/callback-payload/',
            '/oauth/callback/',
            '/api/gmail/oauth-initiate',
            '/api/gmail/oauth-callback',

            # Static/media/admin
            '/media/',
            '/static/',
            '/admin/',
            '/favicon.ico',

            # Health/test connectivity (keep narrow; prefer removing in production)
            '/api/test-connection/',

            # Vendor invitation redirect (handled below via regex as well)
            '/rfp/',
        ]
        
        # Check if path should be skipped
        path = request.path_info

        # Always allow CORS preflight to pass through (CORS middleware will answer it).
        # Business endpoints still require auth on the subsequent actual request.
        if request.method == 'OPTIONS':
            return None
        
        # Explicitly skip data subject requests (GDPR compliance - users may not be logged in)
        if path.startswith('/api/data-subject-requests/'):
            logger.debug(
                "[JWT Middleware] Skipping authentication for data subject request endpoint: %s",
                _safe_path_for_log(path),
            )
            return None
        
        # For TPRM API paths, we still want to process authentication here so that
        # plain Django views (not just DRF views) get request.user and request.tenant.
        # However, we inject the cookie token as an Authorization header if missing
        # so that this middleware (and DRF downstream) can use it.
        if path.startswith('/api/tprm/') or path.startswith('/api/v1/vendor-'):
            try:
                if not request.headers.get('Authorization'):
                    cookie_token = request.COOKIES.get('access_token') if hasattr(request, 'COOKIES') else None
                    if cookie_token:
                        request.META['HTTP_AUTHORIZATION'] = f"Bearer {cookie_token}"
            except Exception:
                # Never block requests due to header injection failures.
                pass
            # Removed: return None 
            # We continue processing so request.user is populated.
        
        # Special handling for OAuth callback - exact match
        if path == '/oauth/callback' or path == '/oauth/callback/':
            #logger.debug(f"[JWT Middleware] Skipping authentication for OAuth callback: {path}")
            return None
        # Special handling for Gmail OAuth endpoints - skip authentication
        # Initiate + callback must both work even if JWT in browser has expired
        if path.startswith('/api/gmail/oauth-initiate'):
            #logger.debug(f"[JWT Middleware] Skipping authentication for Gmail OAuth initiate: {path}")
            return None
        if path.startswith('/api/gmail/oauth-callback'):
            #logger.debug(f"[JWT Middleware] Skipping authentication for Gmail OAuth callback: {path}")
            return None
       
        # Special handling for Gmail test headers - skip authentication for debugging (temporary)
        if path.startswith('/api/gmail/test-headers'):
            #logger.debug(f"[JWT Middleware] Skipping authentication for Gmail test headers: {path}")
            return None
        # /api/external-applications/ removed from bypass — requires authentication

        # Special handling for vendor portal endpoints - skip authentication
        # Check both with and without trailing slash, and handle query parameters
        path_without_query = path.split('?')[0]  # Remove query string if present
        
        # Check for vendor invitation redirect (old URL format)
        if re.match(r'^/rfp/\d+/invitation/?$', path_without_query):
            logger.info(
                "[JWT Middleware] Skipping authentication for vendor invitation redirect: %s",
                _safe_path_for_log(path),
            )
            return None
        
        if (path_without_query.startswith('/api/tprm/rfp/rfp-details/') or \
            path_without_query.startswith('/api/tprm/rfp/rfp-responses/') or \
            path_without_query.startswith('/api/tprm/rfp/open-rfp/') or \
            path_without_query.startswith('/api/tprm/rfp/invitations/') or \
            path_without_query.startswith('/api/tprm/rfp/s3-files/') or \
            path_without_query.startswith('/api/tprm/rfp/upload-document/') or \
            '/evaluation-criteria/' in path_without_query or \
            '/upload-document/' in path_without_query or \
            '/create-unmatched-vendor/' in path_without_query):
            logger.info(
                "[JWT Middleware] Skipping authentication for vendor portal path: %s",
                _safe_path_for_log(path),
            )
            return None

        # Cookie preferences: anonymous users only have session_id (query/body). If user_id is in the
        # query, require normal JWT so ObjectLevel + DRF can enforce access.
        path_no_q = path.split('?')[0]
        if path_no_q.startswith('/api/cookie/preferences/'):
            uid_in_query = None
            try:
                uid_in_query = (
                    request.GET.get('user_id')
                    or request.GET.get('userId')
                    or request.GET.get('UserId')
                )
            except Exception:
                uid_in_query = None
            if not uid_in_query:
                logger.debug(
                    "[JWT Middleware] Skipping authentication for cookie preferences (no user_id in query): %s",
                    _safe_path_for_log(path),
                )
                return None
        
        # Check public allowlist (prefix match)
        for public_prefix in public_path_prefixes:
            if path.startswith(public_prefix):
                logger.debug(
                    "[JWT Middleware] Skipping authentication for public path: %s",
                    _safe_path_for_log(path),
                )
                return None
        
        # Regex-based bypass for any versioned login route: /api/v{major}.{minor}/login/
        # This handles v1.0, v2.0, and future versions without explicit list updates
        if re.match(r'^/api/v\d+\.\d+/login/', path):
            logger.debug(
                "[JWT Middleware] Skipping authentication for versioned login path: %s",
                _safe_path_for_log(path),
            )
            return None
        
        # Try JWT authentication first.
        # Prefer HttpOnly access_token cookie over Authorization: Bearer (matches UnifiedJWTAuthentication).
        # Stale tokens in localStorage must not block a valid cookie from the latest login.
        auth_header = request.headers.get('Authorization')
        header_token = None
        if auth_header and auth_header.startswith('Bearer '):
            ht = auth_header.split(' ', 1)[1].strip()
            if ht and ht.lower() not in ('null', 'undefined', '', 'none', '[object object]'):
                header_token = ht
        cookie_token = None
        if hasattr(request, 'COOKIES'):
            ct = request.COOKIES.get('access_token')
            if ct and str(ct).strip():
                cookie_token = str(ct).strip()

        jwt_candidates = []
        if cookie_token:
            jwt_candidates.append(cookie_token)
        if header_token and header_token not in jwt_candidates:
            jwt_candidates.append(header_token)

        payload = None
        token = None
        for cand in jwt_candidates:
            p = verify_jwt_token(cand, check_session=True)
            if p and p.get('user_id'):
                payload = p
                token = cand
                break

        if token:
            #logger.debug(f"[JWT Middleware] Processing JWT token for path: {path}")
            try:
                user_id = payload.get('user_id') if payload else None

                if payload and user_id:
                    logger.debug(
                        "[JWT Middleware] Successfully decoded token with custom verification, user_id: %s",
                        sanitize_for_log(user_id, 32),
                    )
                else:
                    # For TPRM paths, let DRF handle authentication if JWT verification fails
                    if path.startswith('/api/tprm/') or path.startswith('/api/v1/vendor-'):
                        logger.debug(
                            "[JWT Middleware] JWT verification failed for TPRM path %s, letting DRF handle authentication",
                            _safe_path_for_log(path),
                        )
                        return None
                    logger.warning(
                        "[JWT Middleware] No user_id in JWT payload for path: %s",
                        _safe_path_for_log(path),
                    )
                    return JsonResponse({
                        'error': 'Invalid token payload or session invalidated',
                        'session_invalidated': True
                    }, status=401)

                if payload and user_id:
                    # Get user from database
                    user = Users.objects.get(UserId=user_id)

                    # ========================================
                    # SESSION TIMEOUT CHECK
                    # ========================================
                    # Get session timeout from settings (which reads from env vars)
                    # These MUST be set in .env file
                    session_timeout_enabled = getattr(settings, 'SESSION_TIMEOUT_ENABLED', None)
                    session_timeout_seconds = getattr(settings, 'SESSION_TIMEOUT_SECONDS', None)
                    
                    if session_timeout_enabled is None or session_timeout_seconds is None:
                        logger.error("❌ Session timeout configuration missing from .env file")
                        return None
                    
                    login_time = payload.get('login_time')
                    if login_time and session_timeout_enabled:
                        current_time = time.time()
                        elapsed_time = current_time - login_time
                        
                        if elapsed_time >= session_timeout_seconds:
                            logger.info(
                                "JWT Session timeout: User ID %s logged out after %s seconds (elapsed: %.2fs)",
                                sanitize_for_log(user_id, 32),
                                session_timeout_seconds,
                                elapsed_time,
                            )
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Session expired. Please login again.',
                                'session_expired': True,
                                'logout_reason': f'Session timeout after {session_timeout_seconds} seconds'
                            }, status=401)

                    # Version enforcement: block outdated tokens if min_ver is set
                    token_version = payload.get('ver')
                    min_supported_obj = ProductVersion.get_min_supported()
                    min_supported_version = min_supported_obj.version if min_supported_obj else None
                    if min_supported_version and token_version:
                        if _compare_versions(token_version, min_supported_version) < 0:
                            logger.warning(
                                "[JWT Middleware] Token version %s below min supported %s",
                                sanitize_for_log(token_version, 64),
                                sanitize_for_log(min_supported_version, 64),
                            )
                            return JsonResponse(
                                {
                                    'error': 'Client version not supported. Please update your application.',
                                    'required_version': min_supported_version,
                                    'current_version': token_version,
                                },
                                status=426  # Upgrade Required
                            )
                    
                    # Check if user is active
                    is_active = user.IsActive
                    if isinstance(is_active, str):
                        is_active = is_active.upper() == 'Y'
                    elif isinstance(is_active, bool):
                        is_active = is_active
                    else:
                        is_active = False
                    
                    if is_active:
                        # Set user in request for Django REST Framework
                        request.user = user
                        # Also store on a custom attribute so DRF views can read it
                        # even after DRF's _not_authenticated() overwrites request.user
                        request._grc_user = user
                        
                        # MULTI-TENANCY: Attach tenant context from JWT to request
                        tenant_id = payload.get('tenant_id')
                        tenant_name = payload.get('tenant_name')
                        if tenant_id:
                            request.tenant_id = tenant_id
                            request.tenant = getattr(user, 'tenant', None)
                            # Set thread-local context for safety
                            from .utils.tenant_context import set_current_tenant_id
                            set_current_tenant_id(tenant_id)
                        
                        #logger.info(f"[JWT Middleware] User {user.UserName} (ID: {user.UserId}) authenticated via JWT for {request.method} {path}")
                        return None
                    else:
                        logger.warning(
                            "[JWT Middleware] Inactive user %s (ID: %s) attempted access",
                            sanitize_for_log(user.UserName, 128),
                            sanitize_for_log(user.UserId, 32),
                        )
                        return JsonResponse({'error': 'User account is inactive'}, status=401)
                else:
                    logger.warning(
                        "[JWT Middleware] No user_id in JWT payload for path: %s",
                        _safe_path_for_log(path),
                    )
                    return JsonResponse({'error': 'Invalid token payload'}, status=401)
            except Users.DoesNotExist:
                logger.warning(
                    "[JWT Middleware] User not found in database for path: %s",
                    _safe_path_for_log(path),
                )
                return JsonResponse({'error': 'User not found'}, status=401)
            except Exception as e:
                # For TPRM paths, let DRF handle authentication errors
                if path.startswith('/api/tprm/') or path.startswith('/api/v1/vendor-'):
                    logger.debug(
                        "[JWT Middleware] JWT verification failed for TPRM path %s, letting DRF handle authentication: %s",
                        _safe_path_for_log(path),
                        sanitize_for_log(e, 300),
                    )
                    return None

                logger.exception(
                    "[JWT Middleware] JWT authentication error for path %s",
                    _safe_path_for_log(path),
                )
                return JsonResponse({'error': 'Authentication error'}, status=401)
        
        # Try session authentication as fallback
        elif request.session.get('user_id'):
            user_id = request.session['user_id']
            #logger.debug(f"[JWT Middleware] Processing session authentication for user ID: {user_id}")
            
            try:
                user = Users.objects.get(UserId=user_id)
                
                # Check if user is active
                is_active = user.IsActive
                if isinstance(is_active, str):
                    is_active = is_active.upper() == 'Y'
                elif isinstance(is_active, bool):
                    is_active = is_active
                else:
                    is_active = False
                
                if is_active:
                    # Set user in request for Django REST Framework
                    request.user = user
                    # Also store on a custom attribute so DRF views can read it
                    # even after DRF's _not_authenticated() overwrites request.user
                    request._grc_user = user
                    #logger.info(f"[JWT Middleware] User {user.UserName} (ID: {user.UserId}) authenticated via session for {request.method} {path}")
                    return None
                else:
                    logger.warning(
                        "[JWT Middleware] Inactive user %s (ID: %s) attempted access via session",
                        sanitize_for_log(user.UserName, 128),
                        sanitize_for_log(user.UserId, 32),
                    )
                    return JsonResponse({'error': 'User account is inactive'}, status=401)
                    
            except Users.DoesNotExist:
                logger.warning(
                    "[JWT Middleware] Session user not found in database: %s",
                    sanitize_for_log(user_id, 32),
                )
                return JsonResponse({'error': 'User not found'}, status=401)
            except Exception:
                logger.exception("[JWT Middleware] Session authentication error")
                return JsonResponse({'error': 'Authentication error'}, status=401)

        # No authentication found
        logger.warning(
            "[JWT Middleware] No authentication found for path: %s",
            _safe_path_for_log(path),
        )
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    def process_response(self, request, response):
        """Process outgoing response"""
        # CORS is handled centrally by django-cors-headers.
        # Do not inject dynamic/wildcard CORS headers here.
        return response

class CORSMiddleware(MiddlewareMixin):
    """
    CORS Middleware for handling preflight requests
    """
    
    def process_request(self, request):
        """Handle preflight OPTIONS requests"""
        # Legacy no-op middleware retained for backwards compatibility.
        # Active CORS behavior is implemented by `corsheaders.middleware.CorsMiddleware`.
        return None

class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Session Timeout Middleware
    Automatically logs out users after configured timeout period.
    Configuration is controlled via environment variables:
    - SESSION_TIMEOUT_ENABLED: Enable/disable session timeout (default: true)
    - SESSION_TIMEOUT_SECONDS: Session timeout duration in seconds (default: 3600 = 1 hour)
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        # Get session timeout configuration from settings (which reads from env vars)
        # These MUST be set in .env file - no defaults
        self.SESSION_TIMEOUT_ENABLED = getattr(settings, 'SESSION_TIMEOUT_ENABLED', None)
        self.SESSION_TIMEOUT_SECONDS = getattr(settings, 'SESSION_TIMEOUT_SECONDS', None)
        
        if self.SESSION_TIMEOUT_ENABLED is None:
            raise ValueError("❌ ERROR: SESSION_TIMEOUT_ENABLED must be set in .env file")
        if self.SESSION_TIMEOUT_SECONDS is None:
            raise ValueError("❌ ERROR: SESSION_TIMEOUT_SECONDS must be set in .env file")
        
        if self.SESSION_TIMEOUT_ENABLED:
            logger.info(f"⏰ Session timeout middleware enabled: {self.SESSION_TIMEOUT_SECONDS} seconds ({self.SESSION_TIMEOUT_SECONDS / 3600:.1f} hours)")
        else:
            logger.info("⏰ Session timeout middleware DISABLED")
    
    def process_request(self, request):
        """Check if session has expired and force logout if needed"""
        
        # If session timeout is disabled, skip all checks
        if not self.SESSION_TIMEOUT_ENABLED:
            return None
        
        # Skip timeout check for login/logout endpoints
        skip_paths = [
            '/api/login/',
            '/api/v1.0/login/',  # Versioned login (v1.0)
            '/api/v2.0/login/',  # Versioned login (v2.0)
            '/api/jwt/login/',
            '/api/logout/',
            '/api/jwt/logout/',
            '/api/register/',
            '/api/send-otp/',
            '/api/verify-otp/',
            '/api/reset-password/',
            '/api/jwt/refresh/',
            '/api/jwt/verify/',
            '/api/jwt/accept-consent/',
            '/api/test-connection/',
            '/admin/',
            '/media/',
            '/static/',
        ]
        
        path = request.path_info
        # Skip timeout check for these paths
        for skip_path in skip_paths:
            if path.startswith(skip_path):
                return None
        
        # Regex-based bypass for any versioned login route: /api/v{major}.{minor}/login/
        if re.match(r'^/api/v\d+\.\d+/login/', path):
            return None
        
        # Only check if user has a session
        if not request.session or not request.session.get('user_id'):
            return None
        
        # Check if session creation time exists
        session_created_at = request.session.get('session_created_at')
        current_time = time.time()
        
        if session_created_at:
            # Calculate elapsed time
            elapsed_time = current_time - session_created_at
            
            # If timeout period has passed, force logout
            if elapsed_time >= self.SESSION_TIMEOUT_SECONDS:
                user_id = request.session.get('user_id')
                logger.info(f"⏰ Session timeout: User ID {user_id} logged out after {self.SESSION_TIMEOUT_SECONDS} seconds (elapsed: {elapsed_time:.2f}s)")
                
                # Clear session
                request.session.flush()
                request.session.delete()
                
                # Return logout response
                return JsonResponse({
                    'status': 'error',
                    'message': 'Session expired. Please login again.',
                    'session_expired': True,
                    'logout_reason': f'Session timeout after {self.SESSION_TIMEOUT_SECONDS} seconds'
                }, status=401)
            else:
                # Session is still valid - reset the timer to extend session
                # This allows users to extend their session by making any API call
                request.session['session_created_at'] = current_time
                request.session.save()
        else:
            # If session_created_at doesn't exist, set it now (for existing sessions)
            # This handles sessions that were created before this middleware was added
            request.session['session_created_at'] = current_time
            request.session.save()
        
        # Store session timeout info in request for process_response
        request._session_timeout_seconds = self.SESSION_TIMEOUT_SECONDS
        if session_created_at:
            request._session_created_at = session_created_at
        
        return None
    
    def process_response(self, request, response):
        """Add session expiration headers to response"""
        # Only add headers for authenticated sessions
        if hasattr(request, '_session_created_at') and hasattr(request, '_session_timeout_seconds'):
            session_created_at = request._session_created_at
            timeout_seconds = request._session_timeout_seconds
            current_time = time.time()
            elapsed_time = current_time - session_created_at
            remaining_time = timeout_seconds - elapsed_time
            
            # Add headers for frontend to track session expiration
            response['X-Session-Timeout-Seconds'] = str(timeout_seconds)
            response['X-Session-Remaining-Seconds'] = str(max(0, int(remaining_time)))
            response['X-Session-Created-At'] = str(int(session_created_at))
        
        return response

class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Audit Logging Middleware
    Logs user actions for audit purposes to grc_logs table
    """
    
    def process_request(self, request):
        """Log request details to database"""
        # Skip logging for certain paths
        skip_paths = [
            '/api/jwt/verify/',
            '/api/test-connection/',
            '/api/ai-incident-upload/',
            '/api/ai-incident-save/',
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        # Get user from request
        user = getattr(request, 'user', None)
        if user and hasattr(user, 'UserId'):
            logger.info(f"User {user.UserName} (ID: {user.UserId}) accessing {request.method} {request.path}")
        # Store request info for process_response
        request._audit_log_info = {
            'path': request.path,
            'method': request.method,
            'start_time': time.time()
        }
        
        return None
    
    def process_response(self, request, response):
        """Log response to database"""
        # Skip if we don't have audit log info
        if not hasattr(request, '_audit_log_info'):
            return response
        
        # Skip logging for certain paths
        skip_paths = [
            '/api/jwt/verify/',
            '/api/test-connection/',
            '/api/ai-incident-upload/',
            '/api/ai-incident-save/',
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return response
        
        try:
            from .routes.Global.logging_service import send_log, get_client_ip
            from .rbac.utils import RBACUtils
            from .models import Framework
            
            # Get user info
            user_id = RBACUtils.get_user_id_from_request(request)
            user_name = None
            
            # Ensure user_id is numeric (not encrypted) - convert to int then string
            numeric_user_id = None
            if user_id:
                try:
                    # Convert to int first to ensure it's numeric, then to string
                    if isinstance(user_id, int):
                        numeric_user_id = str(user_id)
                    elif isinstance(user_id, str):
                        # Try to convert to int to validate it's numeric
                        try:
                            int_val = int(user_id)
                            numeric_user_id = str(int_val)
                        except (ValueError, TypeError):
                            # If it's not numeric, skip UserId
                            numeric_user_id = None
                    else:
                        try:
                            int_val = int(str(user_id))
                            numeric_user_id = str(int_val)
                        except (ValueError, TypeError):
                            numeric_user_id = None
                except:
                    numeric_user_id = None
                
                if numeric_user_id:
                    try:
                        from .models import Users
                        user = Users.objects.filter(UserId=int(numeric_user_id)).first()
                        if user:
                            user_name = getattr(user, 'UserName_plain', None) or getattr(user, 'UserName', None)
                    except:
                        pass
            
            # Get client IP
            client_ip = get_client_ip(request)
            
            # Determine module from path
            path = request.path
            module = 'System'
            action_type = f'{request.method}_REQUEST'
            
            if '/api/user-profile' in path or '/user-profile' in path:
                module = 'User Profile'
                if request.method == 'GET':
                    action_type = 'VIEW_PROFILE'
                elif request.method in ['PUT', 'PATCH', 'POST']:
                    action_type = 'UPDATE_PROFILE'
            elif '/api/access-requests' in path or '/access-requests' in path:
                module = 'Access Request'
                if request.method == 'GET':
                    action_type = 'VIEW_ACCESS_REQUESTS'
                elif request.method == 'POST':
                    action_type = 'CREATE_ACCESS_REQUEST'
                elif request.method in ['PUT', 'PATCH']:
                    action_type = 'UPDATE_ACCESS_REQUEST'
            elif '/api/data-subject-requests' in path or '/data-subject-requests' in path:
                module = 'Data Subject Request'
                if request.method == 'GET':
                    action_type = 'VIEW_DATA_SUBJECT_REQUESTS'
                elif request.method == 'POST':
                    action_type = 'CREATE_DATA_SUBJECT_REQUEST'
                elif request.method in ['PUT', 'PATCH']:
                    action_type = 'UPDATE_DATA_SUBJECT_REQUEST'
            elif '/api/policy' in path or '/policy' in path:
                module = 'Policy'
                if request.method == 'GET':
                    action_type = 'VIEW_PAGE'
            elif '/api/compliance' in path or '/compliance' in path:
                module = 'Compliance'
                if request.method == 'GET':
                    action_type = 'VIEW_PAGE'
            elif '/api/risk' in path or '/risk' in path:
                module = 'Risk'
                if request.method == 'GET':
                    action_type = 'VIEW_PAGE'
            elif '/api/audit' in path or '/audit' in path:
                module = 'Audit'
                if request.method == 'GET':
                    action_type = 'VIEW_PAGE'
            elif '/api/incident' in path or '/incident' in path:
                module = 'Incident'
                if request.method == 'GET':
                    action_type = 'VIEW_PAGE'
            elif '/api/dashboard' in path or '/dashboard' in path:
                module = 'Dashboard'
                if request.method == 'GET':
                    action_type = 'VIEW_PAGE'
            elif '/api/system-logs' in path or '/system-logs' in path:
                module = 'System Logs'
                if request.method == 'GET':
                    action_type = 'VIEW_PAGE'
            
            # Create description
            description = f"{request.method} request to {path}"
            if response.status_code >= 400:
                description += f" - Status: {response.status_code}"
            
            # Get framework
            framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
            if not framework:
                framework = Framework.objects.first()
            
            if framework:
                # Log to database
                send_log(
                    module=module,
                    actionType=action_type,
                    description=description,
                    userId=numeric_user_id,
                    userName=user_name,
                    logLevel='INFO' if response.status_code < 400 else 'WARNING',
                    ipAddress=client_ip,
                    additionalInfo={
                        'path': sanitize_for_log(path, max_len=512),
                        'method': request.method,
                        'status_code': response.status_code,
                        'response_time_ms': int((time.time() - request._audit_log_info['start_time']) * 1000) if hasattr(request, '_audit_log_info') else None,
                        # Recursively mask any sensitive data in query params or headers that might have been captured
                        'query_params': mask_sensitive_data(dict(request.GET.items())),
                    },
                    frameworkId=framework.FrameworkId
                )
        except Exception as e:
            # Don't break the request if logging fails
            logger.error(f"Error in AuditLoggingMiddleware: {str(e)}")
        
        return response


class EnterpriseSecurityHeadersMiddleware(MiddlewareMixin):
    """
    Enterprise-Grade Security Headers Middleware
    
    Adds comprehensive security headers to all HTTP responses to protect against:
    - XSS (Cross-Site Scripting) attacks
    - Clickjacking attacks
    - MIME type sniffing attacks
    - Man-in-the-middle attacks
    - Data injection attacks
    
    This middleware implements defense-in-depth security by adding multiple layers
    of protection through HTTP security headers.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.is_debug = getattr(settings, 'DEBUG', False)
        self.is_production = not self.is_debug
        
        # Get allowed hosts for CSP configuration
        self.allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        
    def process_response(self, request, response):
        """
        Add enterprise-grade security headers to all responses
        """
        
        # =====================================================================
        # 1. X-Content-Type-Options: Prevent MIME type sniffing
        # =====================================================================
        # Prevents browser from guessing MIME types, reducing risk of XSS
        response['X-Content-Type-Options'] = 'nosniff'
        
        # =====================================================================
        # 2. X-Frame-Options: Prevent clickjacking attacks
        # =====================================================================
        # Prevents page from being embedded in iframes (clickjacking protection)
        # Changed from 'DENY' to 'SAMEORIGIN' to allow framing within the same domain (e.g., GRC framing TPRM)
        response['X-Frame-Options'] = 'SAMEORIGIN'
        
        # =====================================================================
        # 3. X-XSS-Protection: Enable browser XSS filter
        # =====================================================================
        # Enables browser's built-in XSS protection (legacy, but still useful)
        response['X-XSS-Protection'] = '1; mode=block'
        
        # =====================================================================
        # 4. Referrer-Policy: Control referrer information
        # =====================================================================
        # Controls how much referrer information is sent with requests
        # 'strict-origin-when-cross-origin' - Only send full URL for same-origin, 
        #                                      send only origin for cross-origin
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # =====================================================================
        # 5. Permissions-Policy (formerly Feature-Policy): Disable unnecessary features
        # =====================================================================
        # Disables browser features that aren't needed (geolocation, camera, etc.)
        # Reduces attack surface
        permissions_policy = [
            'geolocation=()',
            'microphone=()',
            'camera=()',
            'payment=()',
            'usb=()',
            'magnetometer=()',
            'gyroscope=()',
            'accelerometer=()',
            'ambient-light-sensor=()',
            'autoplay=()',
            'fullscreen=(self)',
            'picture-in-picture=()',
        ]
        response['Permissions-Policy'] = ', '.join(permissions_policy)
        
        # HSTS is applied by django.middleware.security.SecurityMiddleware from
        # SECURE_HSTS_SECONDS / SECURE_HSTS_INCLUDE_SUBDOMAINS / SECURE_HSTS_PRELOAD in settings.
        
        # =====================================================================
        # 7. Content-Security-Policy (CSP): Prevent XSS and data injection
        # =====================================================================
        # Restricts which resources can be loaded (most powerful XSS protection)
        csp_directives = self._build_csp_policy(request)
        if csp_directives:
            response['Content-Security-Policy'] = csp_directives
        
        # =====================================================================
        # 8. Cross-Origin-Embedder-Policy (COEP): Isolate resources
        # =====================================================================
        # Prevents documents from loading cross-origin resources
        response['Cross-Origin-Embedder-Policy'] = 'require-corp'
        
        # =====================================================================
        # 9. Cross-Origin-Opener-Policy (COOP): Isolate browsing contexts
        # =====================================================================
        # Isolates the browsing context from cross-origin documents
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        
        # =====================================================================
        # 10. Cross-Origin-Resource-Policy (CORP): Control resource loading
        # =====================================================================
        # Prevents resources from being loaded by other origins
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        # =====================================================================
        # 11. Cache-Control for sensitive responses
        # =====================================================================
        # Prevent caching of sensitive data (auth tokens, user data, etc.)
        if self._is_sensitive_response(request, response):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response
    
    def _build_csp_policy(self, request):
        """
        Build Content-Security-Policy based on request context
        """
        # Get current origin for CSP 'self' reference
        scheme = 'https' if self.is_production else request.scheme
        host = request.get_host()
        current_origin = f"{scheme}://{host}"
        
        # Base CSP directives (restrictive by default)
        directives = []
        
        # default-src: Fallback for other directive types
        # Only allow resources from same origin
        directives.append("default-src 'self'")
        
        # script-src: Where JavaScript can be loaded from
        # Hardened: disallow inline scripts but allow dynamic code evaluation for Vue runtime
        directives.append("script-src 'self'")
        
        # style-src: Where CSS can be loaded from
        # Allow same-origin styles and inline styles (needed for dynamic styles)
        # SECURITY: do not allow inline styles.
        directives.append("style-src 'self'")
        
        # img-src: Where images can be loaded from
        # Allow same-origin, data URIs (base64 images), and HTTPS images
        directives.append("img-src 'self' data: https:")
        
        # font-src: Where fonts can be loaded from
        directives.append("font-src 'self' data:")
        
        # connect-src: Where AJAX/fetch requests can go
        # Allow same-origin and current origin
        connect_sources = ["'self'", current_origin]
        directives.append(f"connect-src {' '.join(connect_sources)}")
        
        # frame-src: Where iframes can be loaded from
        # Allow-list iframe sources. Some workflows legitimately embed trusted PDFs (e.g., internal docs/storage).
        frame_sources = ["'self'"]
        trusted_hosts = getattr(settings, "TRUSTED_EVIDENCE_URL_HOSTS", []) or []
        trusted_suffixes = getattr(settings, "TRUSTED_EVIDENCE_URL_HOST_SUFFIXES", []) or []

        for h in trusted_hosts:
            h = str(h).strip()
            if h:
                frame_sources.append(f"https://{h}")

        for s in trusted_suffixes:
            s = str(s).strip().lstrip(".")
            if s:
                # Allow both apex and subdomains (e.g., bucket.s3...amazonaws.com)
                frame_sources.append(f"https://{s}")
                frame_sources.append(f"https://*.{s}")

        # Note: http is intentionally not allowed for iframes; keep evidence rendering HTTPS-only in production.
        directives.append(f"frame-src {' '.join(sorted(set(frame_sources)))}")
        
        # frame-ancestors: Where this page can be embedded
        # Changed from 'none' to "'self'" to allow framing within the same domain
        directives.append("frame-ancestors 'self'")
        
        # object-src: Where plugins can be loaded from
        # Deny all (prevent Flash, Java applets, etc.)
        directives.append("object-src 'none'")
        
        # base-uri: Where <base> tag can point to
        # Hardened: disallow <base> tag to prevent URL rewriting attacks
        directives.append("base-uri 'none'")
        
        # form-action: Where forms can submit to
        # Only allow same-origin
        directives.append("form-action 'self'")
        
        # upgrade-insecure-requests: Automatically upgrade HTTP to HTTPS
        if self.is_production:
            directives.append("upgrade-insecure-requests")
        
        # block-all-mixed-content: Prevent loading resources via HTTP
        if self.is_production:
            directives.append("block-all-mixed-content")
        
        return '; '.join(directives)
    
    def _is_sensitive_response(self, request, response):
        """
        Determine if response contains sensitive data that shouldn't be cached
        """
        sensitive_paths = [
            '/api/jwt/',
            '/api/login/',
            '/api/user/',
            '/api/users/',
            '/api/auth/',
            '/admin/',
        ]
        
        # Check if path contains sensitive endpoints
        if any(request.path.startswith(path) for path in sensitive_paths):
            return True
        
        # Check if response contains authentication-related headers
        if 'Authorization' in request.headers or 'X-Session-Token' in request.headers:
            return True
        
        # Check content type - JSON responses might contain sensitive data
        content_type = response.get('Content-Type', '')
        if 'application/json' in content_type:
            # For JSON responses from API, assume sensitive (can be refined)
            if request.path.startswith('/api/'):
                return True
        
        return False

class RequestSignatureVerificationMiddleware(MiddlewareMixin):
    """
    Enforce nonce + HMAC request signature verification to prevent replay and tampering.

    Required headers when enabled:
    - X-Request-Nonce: random, unique per request (server will reject re-use)
    - X-Request-Timestamp: UNIX epoch seconds (within tolerance window)
    - X-Request-Signature: hex HMAC-SHA256(method|path|timestamp|nonce|body) using shared secret

    Configuration (settings.py):
    - REQUEST_SIGNATURE_ENABLED: bool
    - REQUEST_SIGNATURE_SECRET: str
    - REQUEST_SIGNATURE_TOLERANCE_SECONDS: int (recommended: 300)
    - REQUEST_SIGNATURE_EXEMPT_PATH_PREFIXES: list[str]
    - REQUEST_SIGNATURE_ENFORCE_METHODS: list[str] (default: ['POST','PUT','PATCH','DELETE'])
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.enabled = getattr(settings, "REQUEST_SIGNATURE_ENABLED", False)
        self.secret = getattr(settings, "REQUEST_SIGNATURE_SECRET", None)
        self.tolerance = int(getattr(settings, "REQUEST_SIGNATURE_TOLERANCE_SECONDS", 300))
        self.exempt_prefixes = getattr(settings, "REQUEST_SIGNATURE_EXEMPT_PATH_PREFIXES", [
            "/admin/", "/static/", "/media/",
            "/api/login/", "/api/jwt/", "/api/register/",
            "/api/send-otp/", "/api/verify-otp/", "/api/reset-password/",
            "/api/google/", "/api/gmail/", "/oauth/",
            "/api/tprm/", "/api/v1/vendor-",
        ])
        self.methods = set(getattr(settings, "REQUEST_SIGNATURE_ENFORCE_METHODS", ["POST", "PUT", "PATCH", "DELETE"]))

    def _is_exempt(self, path: str) -> bool:
        try:
            for prefix in self.exempt_prefixes:
                if path.startswith(prefix):
                    return True
        except Exception:
            pass
        return False

    def _cache_nonce_key(self, nonce: str) -> str:
        return f"reqsig:nonce:{nonce}"

    def _body_bytes(self, request) -> bytes:
        try:
            # DRF may have parsed; fallback to raw body
            body = request.body
            if isinstance(body, bytes):
                return body
            if body is None:
                return b""
            return bytes(str(body), "utf-8")
        except Exception:
            return b""

    def _compute_signature(self, secret: str, method: str, path: str, ts: str, nonce: str, body: bytes) -> str:
        msg = "|".join([method.upper(), path, ts, nonce]).encode("utf-8") + b"|" + (body or b"")
        mac = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
        return mac

    def process_request(self, request):
        if not self.enabled:
            return None

        if request.method not in self.methods:
            return None

        path = request.path_info or ""
        if self._is_exempt(path):
            return None

        # Extract headers
        nonce = request.headers.get("X-Request-Nonce")
        ts = request.headers.get("X-Request-Timestamp")
        signature = request.headers.get("X-Request-Signature")

        if not nonce or not ts or not signature:
            return JsonResponse({"error": "Missing required request signature headers"}, status=400)

        # Timestamp freshness
        try:
            ts_int = int(ts)
        except Exception:
            return JsonResponse({"error": "Invalid X-Request-Timestamp"}, status=400)

        now = int(time.time())
        if abs(now - ts_int) > self.tolerance:
            return JsonResponse({"error": "Request timestamp outside allowed window"}, status=401)

        # Nonce replay check
        nonce_key = self._cache_nonce_key(nonce)
        if cache.get(nonce_key):
            return JsonResponse({"error": "Replay detected (nonce already used)"}, status=401)

        # Signature verification
        if not self.secret:
            return JsonResponse({"error": "Server signature secret not configured"}, status=500)

        body = self._body_bytes(request)
        expected = self._compute_signature(self.secret, request.method, path, ts, nonce, body)
        # Constant-time compare
        if not hmac.compare_digest(expected, signature):
            return JsonResponse({"error": "Invalid request signature"}, status=401)

        # Record nonce to prevent re-use
        # Use tolerance as TTL to cover window; add small buffer
        cache.set(nonce_key, True, timeout=self.tolerance + 30)
        return None


class ApiAbuseDetectionMiddleware(MiddlewareMixin):
    """
    Lightweight API abuse detector with real-time alerting.

    Features:
    - Per-IP request rate windowing; alert on excessive RPS
    - Error spike detection per-IP and per-path

    Configuration:
    - API_ABUSE_DETECTION_ENABLED: bool
    - API_ABUSE_RPS_THRESHOLD: int (requests per minute per IP)
    - API_ABUSE_ERROR_THRESHOLD: int (errors per minute per IP)
    - SECURITY_ALERT_EMAIL: email to notify
    - SECURITY_ALERT_WEBHOOK_URL: optional webhook (Slack/Teams) URL
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.enabled = getattr(settings, "API_ABUSE_DETECTION_ENABLED", True)
        self.rps_threshold = int(getattr(settings, "API_ABUSE_RPS_THRESHOLD", 300))
        self.err_threshold = int(getattr(settings, "API_ABUSE_ERROR_THRESHOLD", 30))
        self.window_seconds = int(getattr(settings, "API_ABUSE_WINDOW_SECONDS", 60))
        self.skip_prefixes = getattr(settings, "API_ABUSE_EXEMPT_PATH_PREFIXES", ["/admin/", "/static/", "/media/"])
        self.alert_email = getattr(settings, "SECURITY_ALERT_EMAIL", None)
        self.webhook = getattr(settings, "SECURITY_ALERT_WEBHOOK_URL", None)

    def _client_ip(self, request) -> str:
        try:
            xfwd = request.META.get("HTTP_X_FORWARDED_FOR")
            if xfwd:
                return xfwd.split(",")[0].strip()
            return request.META.get("REMOTE_ADDR", "") or ""
        except Exception:
            return ""

    def _k(self, kind: str, ip: str) -> str:
        return f"abuse:{kind}:{ip}"

    def _incr(self, key: str, ttl: int):
        try:
            val = cache.get(key) or 0
            val = int(val) + 1
            cache.set(key, val, timeout=ttl)
            return val
        except Exception:
            return 0

    def _send_alert(self, subject: str, body: str):
        try:
            if self.alert_email:
                from django.core.mail import send_mail
                send_mail(subject, body, getattr(settings, "DEFAULT_FROM_EMAIL", None), [self.alert_email], fail_silently=True)
        except Exception:
            logger.warning("Failed to send abuse alert email")
        try:
            if self.webhook:
                import urllib.request
                import urllib.error
                data = json.dumps({"text": f"{subject}\n{body}"}).encode("utf-8")
                req = urllib.request.Request(self.webhook, data=data, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=5)
        except Exception:
            logger.warning("Failed to send abuse webhook alert")

    def process_request(self, request):
        if not self.enabled:
            return None
        path = request.path_info or ""
        for p in self.skip_prefixes:
            if path.startswith(p):
                return None
        ip = self._client_ip(request) or "unknown"

        rps_key = self._k("rps", ip)
        rps = self._incr(rps_key, self.window_seconds)
        if rps == self.rps_threshold + 1:
            self._send_alert(
                "API abuse: high request rate detected",
                f"IP={ip} exceeded {self.rps_threshold}/min (path example: {path})"
            )
        return None

    def process_response(self, request, response):
        if not self.enabled:
            return response
        try:
            status = response.status_code
            if status >= 400:
                ip = self._client_ip(request) or "unknown"
                err_key = self._k("err", ip)
                errs = self._incr(err_key, self.window_seconds)
                if errs == self.err_threshold + 1:
                    self._send_alert(
                        "API abuse: error spike detected",
                        f"IP={ip} observed {self.err_threshold}+ errors/min (latest path: {request.path})"
                    )
        except Exception:
            pass
        return response


class OutgoingRedirectValidationMiddleware(MiddlewareMixin):
    """
    Validate any HttpResponseRedirect targets against a strict allowlist to prevent open redirects.

    Configuration:
    - REDIRECT_ALLOWLIST_HOSTS: list[str] (default: FRONTEND_URL host)
    - REDIRECT_ENFORCE_ON_PREFIXES: list[str] (default: ['/api/', '/oauth/'])
    - In production, only https scheme is allowed.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.prefixes = getattr(settings, "REDIRECT_ENFORCE_ON_PREFIXES", ["/api/", "/oauth/"])
        frontend = getattr(settings, "FRONTEND_URL", "http://localhost:8080")
        parsed = urlparse(frontend)
        default_host = parsed.hostname
        self.allow_hosts = set(getattr(settings, "REDIRECT_ALLOWLIST_HOSTS", [h for h in [default_host] if h]))
        self.is_production = not getattr(settings, "DEBUG", False)

    def _should_check(self, path: str) -> bool:
        for p in self.prefixes:
            if path.startswith(p):
                return True
        return False

    def process_response(self, request, response):
        try:
            status = int(getattr(response, "status_code", 200))
            location = response.get("Location")
            if not location or status not in (301, 302, 303, 307, 308):
                return response

            path = request.path_info or ""
            if not self._should_check(path):
                return response

            parsed = urlparse(location)
            host = parsed.hostname
            scheme = parsed.scheme or "http"

            if host and host not in self.allow_hosts:
                logger.warning(f"Blocked redirect to unapproved host: {location}")
                return JsonResponse({"error": "Unapproved redirect host"}, status=400)

            if self.is_production and scheme != "https":
                logger.warning(f"Blocked non-HTTPS redirect in production: {location}")
                return JsonResponse({"error": "Insecure redirect blocked"}, status=400)

            return response
        except Exception as ex:
            logger.warning(f"Redirect validation failed: {ex}")
            return response