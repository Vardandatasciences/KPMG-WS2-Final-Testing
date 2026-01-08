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

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Simple Request Logging Middleware
    Prints ALL requests directly to stdout - bypasses logging config
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        # Print startup message so we know middleware is loaded
        print("\n" + "="*80, file=sys.stdout, flush=True)
        print("✅ REQUEST LOGGING MIDDLEWARE LOADED - ALL REQUESTS WILL BE LOGGED", file=sys.stdout, flush=True)
        print("="*80 + "\n", file=sys.stdout, flush=True)
    
    def process_request(self, request):
        """Log every incoming request"""
        timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
        # Print directly to stdout - this will ALWAYS show
        print(f"🔵 [{timestamp}] {request.method} {request.path}", file=sys.stdout, flush=True)
        return None
    
    def process_response(self, request, response):
        """Log response status"""
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
        
        # Skip authentication for certain paths
        skip_paths = [
            '/api/login/',
            '/api/jwt/login/',
            '/api/jwt/refresh/',
            '/api/jwt/verify/',
            '/api/jwt/accept-consent/',
            '/api/jwt/test-token-version/',
            '/api/jwt/test-consent-simple/',
            '/api/jwt/mfa/verify-otp/',
            '/api/jwt/mfa/resend-otp/',
            '/api/google/oauth/',  # Allow Google OAuth initiation without authentication
            '/api/google/oauth-callback/',  # Allow Google OAuth callback without authentication
            '/media/',  # Allow access to media files without authentication
            '/api/risks-for-dropdown/',  # Allow access to risks dropdown without authentication
            # '/api/risks/',  # Temporarily allow access to risks creation without authentication for testing
            '/oauth/callback/',  # Allow OAuth callbacks without authentication
            '/api/register/',
            '/api/send-otp/',
            '/api/verify-otp/',
            '/api/reset-password/',
            '/api/get-user-email/',
            '/admin/',
            '/api/test-connection/',
            '/api/departments/',
            '/api/rbac/roles/',
            '/api/policy-categories/',
            '/api/user-role/',  # User role endpoint
            '/api/framework-explorer/',  # Framework explorer endpoint
            '/api/users-for-reviewer-selection/',  # Users for reviewer selection
            '/api/entities/',  # Entities endpoint
            '/api/frameworks/',
            '/api/frameworks/rejected/',
            '/api/frameworks/approved-active/',  # Skip authentication for approved frameworks (home page)
            '/api/frameworks/get-selected/',  # Skip authentication for getting selected framework (home page)
            '/api/frameworks/set-selected/',  # Skip authentication for setting selected framework (home page)
            '/api/home/policies-by-status-public/',  # Skip authentication for public home page policies
            '/api/get-notifications/',
            '/api/push-notification/',
            '/jwt/refresh/',
            '/api/test-submit-review/',  # Add test endpoint to skip list
            '/api/policies/',  # Skip authentication for policy endpoints temporarily
            '/api/tailoring/',  # Skip authentication for tailoring endpoints temporarily
            '/api/policy-approvals/',  # Skip authentication for policy approval endpoints temporarily
            '/api/users/',  # Skip authentication for users endpoint
            '/api/policy-acknowledgements/',  # Skip authentication for policy acknowledgement endpoints
            # '/api/generate-audit-report/',  # Re-enabled authentication for audit report generation
            # External Integration endpoints - some require auth, some don't
            '/api/jira/',
            '/api/test-integration-auth/',
            '/api/streamline/',
            # BambooHR integration endpoints - no authentication required
            '/api/bamboohr/',
            # Public, read-only endpoints
            '/api/compliance/frameworks/public/',
            '/api/audits/public/',
            '/api/compliance/all-for-audit-management/public/',
            # Checked sections endpoints
            '/api/checked-sections/',
            '/api/checked-sections/pdf/',  # Allow PDF access without authentication
            # Save endpoints - allow without authentication for now
            '/api/save-complete-policy-package/',
            '/api/save-framework-to-database/',
            '/api/risk/analytics-with-filters/',
            '/api/risk/dashboard-with-filters/',
            '/api/risk/frameworks-for-filter/',
            '/api/risk/policies-for-filter/',
            '/risk/frameworks-for-filter/',
            '/risk/policies-for-filter/',
            # Document endpoints - allow without authentication
            '/api/documents/',
            '/api/events/archived/',  # Skip authentication for archived events endpoints
            '/api/events/archived-queue-items/',  # Skip authentication for archived queue items endpoints
            '/api/events/',
            # Cookie preferences endpoints - must be accessible without authentication
            '/api/cookie/preferences/',  # Skip authentication for cookie preferences endpoints (save and get)
            '/api/upload-evidence-file/',  # Skip authentication for evidence file uploads (matches existing file upload pattern)
            '/api/incident-categories/',
            '/api/data-subject-requests/',  # Skip authentication for data subject requests (GDPR compliance - users may not be logged in)
            '/api/upload-risk-evidence-file/',  # Skip authentication for incident categories endpoints
            # Risk AI Document Ingestion endpoints - skip authentication for testing
            '/api/ai-risk-doc-upload/',
            '/api/ai-risk-save/',
            '/api/ai-risk-test/',
            '/api/ai-risk-test-upload/',
            # Risk Instance AI Document Ingestion endpoints - skip authentication (no permission required)
            '/api/ai-risk-instance-upload/',
            '/api/ai-risk-instance-save/',
            '/api/ai-risk-instance-test/',
            # Incident AI Document Ingestion endpoints - skip authentication (no permission required)
            '/api/ai-incident-upload/',
            '/api/ai-incident-save/',
            '/api/ai-incident-test/',
            # AI Upload endpoints - allow without authentication for default data loading
            '/api/ai-upload/',  # Allow all AI upload endpoints including load-default-data
            # Risk KPI endpoints - allow without authentication for development
            '/api/risk/kpi-data/',
            '/api/risk/active-risks-kpi/',
            '/api/risk/exposure-trend/',
            '/api/risk/reduction-trend/',
            '/api/risk/high-criticality/',
            '/api/risk/mitigation-completion-rate/',
            '/api/risk/avg-remediation-time/',
            '/api/risk/recurrence-rate/',
            '/api/risk/avg-incident-response-time/',
            '/api/risk/classification-accuracy/',
            '/api/risk/severity/',
            '/api/risk/exposure-score/',
            '/api/risk/assessment-frequency/',
            '/api/risk/assessment-consensus/',
            '/api/risk/identification-rate/',
            '/api/risk/register-update-frequency/',
            '/api/risk/recurrence-probability/',
            '/api/risk/tolerance-thresholds/',
            '/api/risk/appetite/',
            '/auth/sentinel/',
            '/auth/sentinel/callback/',
            '/api/sentinel/status/',
            '/api/sentinel/',
            # TPRM API paths - let DRF authentication handle these
            '/api/tprm/',
            '/api/v1/vendor-',

        ]
        
        # Check if path should be skipped
        path = request.path_info
        
        # Explicitly skip data subject requests (GDPR compliance - users may not be logged in)
        if path.startswith('/api/data-subject-requests/'):
            logger.debug(f"[JWT Middleware] Skipping authentication for data subject request endpoint: {path}")
            return None
        
        # Explicitly skip MFA endpoints (they don't require authentication during login)
        if path.startswith('/api/jwt/mfa/'):
            logger.debug(f"[JWT Middleware] Skipping authentication for MFA endpoint: {path}")
            return None
        
        # Skip all TPRM API paths - let DRF authentication handle them
        if path.startswith('/api/tprm/') or path.startswith('/api/v1/vendor-'):
            return None
        
        # Special handling for OAuth callback - exact match
        if path == '/oauth/callback' or path == '/oauth/callback/':
            #logger.debug(f"[JWT Middleware] Skipping authentication for OAuth callback: {path}")
            return None
        # Special handling for Gmail OAuth callback - skip authentication
        if path.startswith('/api/gmail/oauth-callback'):
            #logger.debug(f"[JWT Middleware] Skipping authentication for Gmail OAuth callback: {path}")
            return None
       
        # Special handling for Gmail test headers - skip authentication for debugging (temporary)
        if path.startswith('/api/gmail/test-headers'):
            #logger.debug(f"[JWT Middleware] Skipping authentication for Gmail test headers: {path}")
            return None
        # Special handling for external applications - skip all external app endpoints
        if path.startswith('/api/external-applications/'):
            #logger.debug(f"[JWT Middleware] Skipping authentication for external applications: {path}")
            return None

        # Special handling for vendor portal endpoints - skip authentication
        # Check both with and without trailing slash, and handle query parameters
        path_without_query = path.split('?')[0]  # Remove query string if present
        
        # Check for vendor invitation redirect (old URL format)
        if re.match(r'^/rfp/\d+/invitation/?$', path_without_query):
            logger.info(f"[JWT Middleware] Skipping authentication for vendor invitation redirect: {path}")
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
            logger.info(f"[JWT Middleware] Skipping authentication for vendor portal path: {path}")
            return None
        
        # Check other skip paths - use startswith for more reliable matching
        # Also handle paths with or without trailing slashes
        path_normalized = path.rstrip('/')
        for skip_path in skip_paths:
            skip_path_normalized = skip_path.rstrip('/')
            if path.startswith(skip_path) or path_normalized == skip_path_normalized:
                logger.debug(f"[JWT Middleware] Skipping authentication for path: {path}")
                return None
        
        # Try JWT authentication first
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            #logger.debug(f"[JWT Middleware] Processing JWT token for path: {path}")
            #logger.debug(f"[JWT Middleware] Token length: {len(token)}")
            #logger.debug(f"[JWT Middleware] Token starts with: {token[:20]}...")
            #logger.debug(f"[JWT Middleware] Full Authorization header: {auth_header}")
            
            try:
                # Verify JWT token using custom verification (since tokens are generated with custom method)
                payload = verify_jwt_token(token)
                user_id = payload.get('user_id') if payload else None
                
                if payload and user_id:
                    logger.debug(f"[JWT Middleware] Successfully decoded token with custom verification, user_id: {user_id}")
                else:
                    # For TPRM paths, let DRF handle authentication if JWT verification fails
                    if path.startswith('/api/tprm/') or path.startswith('/api/v1/vendor-'):
                        logger.debug(f"[JWT Middleware] JWT verification failed for TPRM path {path}, letting DRF handle authentication")
                        return None
                    logger.warning(f"[JWT Middleware] No user_id in JWT payload for path: {path}")
                    return JsonResponse({'error': 'Invalid token payload'}, status=401)
                
                if payload and user_id:
                    # Get user from database
                    user = Users.objects.get(UserId=user_id)

                    # ========================================
                    # SESSION TIMEOUT CHECK
                    # ========================================
                    # Set to 1 hour (3600 seconds)
                    login_time = payload.get('login_time')
                    if login_time:
                        current_time = time.time()
                        elapsed_time = current_time - login_time
                        SESSION_TIMEOUT_SECONDS = 3600  # 1 hour
                        
                        if elapsed_time >= SESSION_TIMEOUT_SECONDS:
                            logger.info(f"⏰ JWT Session timeout: User ID {user_id} logged out after {SESSION_TIMEOUT_SECONDS} seconds (elapsed: {elapsed_time:.2f}s)")
                            return JsonResponse({
                                'status': 'error',
                                'message': 'Session expired. Please login again.',
                                'session_expired': True,
                                'logout_reason': f'Session timeout after {SESSION_TIMEOUT_SECONDS} seconds'
                            }, status=401)

                    # Version enforcement: block outdated tokens if min_ver is set
                    token_version = payload.get('ver')
                    min_supported_obj = ProductVersion.get_min_supported()
                    min_supported_version = min_supported_obj.version if min_supported_obj else None
                    if min_supported_version and token_version:
                        if _compare_versions(token_version, min_supported_version) < 0:
                            logger.warning(f"[JWT Middleware] Token version {token_version} below min supported {min_supported_version}")
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
                        #logger.info(f"[JWT Middleware] User {user.UserName} (ID: {user.UserId}) authenticated via JWT for {request.method} {path}")
                        return None
                    else:
                        logger.warning(f"[JWT Middleware] Inactive user {user.UserName} (ID: {user.UserId}) attempted access")
                        return JsonResponse({'error': 'User account is inactive'}, status=401)
                else:
                    logger.warning(f"[JWT Middleware] No user_id in JWT payload for path: {path}")
                    return JsonResponse({'error': 'Invalid token payload'}, status=401)
            except Users.DoesNotExist:
                logger.warning(f"[JWT Middleware] User not found in database for path: {path}")
                return JsonResponse({'error': 'User not found'}, status=401)
            except Exception as e:
                # For TPRM paths, let DRF handle authentication errors
                if path.startswith('/api/tprm/') or path.startswith('/api/v1/vendor-'):
                    logger.debug(f"[JWT Middleware] JWT verification failed for TPRM path {path}, letting DRF handle authentication: {str(e)}")
                    return None
                
                logger.error(f"[JWT Middleware] JWT authentication error for path {path}: {str(e)}")
                logger.error(f"[JWT Middleware] Exception type: {type(e).__name__}")
                logger.error(f"[JWT Middleware] Exception details: {str(e)}")
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
                    #logger.info(f"[JWT Middleware] User {user.UserName} (ID: {user.UserId}) authenticated via session for {request.method} {path}")
                    return None
                else:
                    logger.warning(f"[JWT Middleware] Inactive user {user.UserName} (ID: {user.UserId}) attempted access via session")
                    return JsonResponse({'error': 'User account is inactive'}, status=401)
                    
            except Users.DoesNotExist:
                logger.warning(f"[JWT Middleware] Session user not found in database: {user_id}")
                return JsonResponse({'error': 'User not found'}, status=401)
            except Exception as e:
                logger.error(f"[JWT Middleware] Session authentication error: {str(e)}")
                return JsonResponse({'error': 'Authentication error'}, status=401)
        
        # No authentication found
        logger.warning(f"[JWT Middleware] No authentication found for path: {path}")
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    def process_response(self, request, response):
        """Process outgoing response"""
        # Add CORS headers if needed
        if hasattr(response, 'headers'):
            # Instead of hardcoding '*', use the Origin from the request
            origin = request.headers.get('Origin')
            if origin:
                response.headers['Access-Control-Allow-Origin'] = origin
            else:
                response.headers['Access-Control-Allow-Origin'] = '*'
                
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRFToken'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response

class CORSMiddleware(MiddlewareMixin):
    """
    CORS Middleware for handling preflight requests
    """
    
    def process_request(self, request):
        """Handle preflight OPTIONS requests"""
        if request.method == 'OPTIONS':
            response = JsonResponse({})
            # Get the Origin header from the request
            origin = request.headers.get('Origin')
            if origin:
                response['Access-Control-Allow-Origin'] = origin
            else:
                response['Access-Control-Allow-Origin'] = '*'
                
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRFToken'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response
        return None

class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Session Timeout Middleware
    Automatically logs out users after 1 hour (3600 seconds) regardless of activity.
    """
    
    # Session timeout in seconds (1 hour)
    SESSION_TIMEOUT_SECONDS = 3600  # 1 hour
    
    def process_request(self, request):
        """Check if session has expired and force logout if needed"""
        
        # Skip timeout check for login/logout endpoints
        skip_paths = [
            '/api/login/',
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
        
        # Only check if user has a session
        if not request.session or not request.session.get('user_id'):
            return None
        
        # Check if session creation time exists
        session_created_at = request.session.get('session_created_at')
        
        if session_created_at:
            # Calculate elapsed time
            current_time = time.time()
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
            # If session_created_at doesn't exist, set it now (for existing sessions)
            # This handles sessions that were created before this middleware was added
            request.session['session_created_at'] = time.time()
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
    Logs user actions for audit purposes
    """
    
    def process_request(self, request):
        """Log request details"""
        # Skip logging for certain paths
        skip_paths = [
            '/api/jwt/verify/',
            '/api/test-connection/',
            '/admin/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Get user from request
        user = getattr(request, 'user', None)
        if user and hasattr(user, 'UserId'):
            logger.info(f"User {user.UserName} (ID: {user.UserId}) accessing {request.method} {request.path}")
        
        return None


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
        response['X-Frame-Options'] = 'DENY'
        
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
        
        # =====================================================================
        # 6. Strict-Transport-Security (HSTS): Force HTTPS in production
        # =====================================================================
        # Forces browsers to use HTTPS for future requests (prevents MITM attacks)
        # Only enable in production with HTTPS
        if self.is_production:
            # max-age=31536000 = 1 year
            # includeSubDomains = Apply to all subdomains
            # preload = Eligible for HSTS preload list
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        # In development/debug mode, don't set this header (allows HTTP)
        
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
        # Allow same-origin scripts and inline scripts (needed for some apps)
        # In production, consider removing 'unsafe-inline' and using nonces
        directives.append("script-src 'self' 'unsafe-inline' 'unsafe-eval'")
        
        # style-src: Where CSS can be loaded from
        # Allow same-origin styles and inline styles (needed for dynamic styles)
        directives.append("style-src 'self' 'unsafe-inline'")
        
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
        # Deny all iframes by default (prevent clickjacking)
        directives.append("frame-src 'none'")
        
        # frame-ancestors: Where this page can be embedded
        # Deny all (prevent embedding in iframes)
        directives.append("frame-ancestors 'none'")
        
        # object-src: Where plugins can be loaded from
        # Deny all (prevent Flash, Java applets, etc.)
        directives.append("object-src 'none'")
        
        # base-uri: Where <base> tag can point to
        # Only allow same-origin
        directives.append("base-uri 'self'")
        
        # form-action: Where forms can submit to
        # Only allow same-origin
        directives.append("form-action 'self'")
        
        # upgrade-insecure-requests: Automatically upgrade HTTP to HTTPS
        if self.is_production:
            directives.append("upgrade-insecure-requests")
        
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