"""
Tenant Security Enforcement Middleware (Phase 3.4)

Enforces per-tenant security settings (IP restrictions only for now).
DESIGN: Always fails open - if DB is unavailable or settings missing,
        the request is allowed through. Never breaks existing flows.
"""

import logging
import ipaddress
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Skip security checks for these paths
_SKIP_PATHS = [
    '/api/login/',
    '/api/jwt/login/',
    '/api/jwt/refresh/',
    '/api/jwt/verify/',
    '/api/jwt/accept-consent/',
    '/api/jwt/mfa/',
    '/api/register/',
    '/api/send-otp/',
    '/api/verify-otp/',
    '/api/reset-password/',
    '/api/get-user-email/',
    '/api/google/',
    '/api/google-oauth/',
    '/oauth/callback',
    '/api/gmail/',
    '/admin/',
    '/static/',
    '/media/',
    '/api/test-connection/',
    '/api/public/',
    '/rfp/',
    '/api/data-subject-requests/',
]


class TenantSecurityMiddleware(MiddlewareMixin):
    """
    Enforces per-tenant security policies from TenantSecuritySettings.
    Currently enforces: IP restrictions.
    Runs AFTER TenantContextMiddleware so request.tenant_id is available.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        logger.info("✅ Tenant Security Middleware loaded")

    def process_request(self, request):
        try:
            path = request.path_info

            # Skip for public / auth paths
            if request.method == 'OPTIONS':
                return None
            if any(path.startswith(p) for p in _SKIP_PATHS):
                return None

            # Only enforce if tenant context is resolved
            tenant_id = getattr(request, 'tenant_id', None)
            if not tenant_id:
                return None

            # Only enforce for authenticated users
            if not hasattr(request, 'user') or not hasattr(request.user, 'UserId'):
                return None

            # Skip for platform / system admins
            if self._is_admin(request.user):
                return None

            # Load security settings (cached)
            settings_obj = self._get_security_settings(tenant_id)
            if not settings_obj:
                return None  # No settings configured → allow

            # ── IP Restriction ─────────────────────────────────────────────
            if settings_obj.get('ip_restriction_enabled'):
                allowed_ranges = settings_obj.get('allowed_ip_ranges', [])
                if allowed_ranges:
                    client_ip = self._get_client_ip(request)
                    if not self._is_ip_allowed(client_ip, allowed_ranges):
                        logger.warning(
                            "[Security Middleware] IP %s blocked for tenant %s",
                            client_ip, tenant_id
                        )
                        return JsonResponse(
                            {'error': 'Access denied: IP address not allowed for this tenant'},
                            status=403
                        )

        except Exception as exc:
            # Never block requests due to middleware errors
            logger.error("[Security Middleware] Unexpected error (failing open): %s", exc)

        return None

    # ── Helpers ────────────────────────────────────────────────────────────

    def _get_security_settings(self, tenant_id):
        """Return dict of security settings for tenant, cached 60 s."""
        cache_key = f"tenant_security_settings_{tenant_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        try:
            from .models import TenantSecuritySettings
            obj = TenantSecuritySettings.objects.filter(tenant_id=tenant_id).first()
            if not obj:
                cache.set(cache_key, {}, 60)
                return {}
            data = {
                'ip_restriction_enabled': bool(obj.ip_restriction_enabled),
                'allowed_ip_ranges': obj.allowed_ip_ranges or [],
            }
            cache.set(cache_key, data, 60)
            return data
        except Exception as exc:
            logger.debug("[Security Middleware] Could not load security settings: %s", exc)
            return None  # None = skip enforcement (table may not exist yet)

    def _is_admin(self, user):
        """Return True if user is GRC Administrator (bypasses checks)."""
        try:
            from .rbac.utils import RBACUtils
            user_id = getattr(user, 'UserId', None)
            if user_id:
                return RBACUtils.is_system_admin(user_id)
        except Exception:
            pass
        return False

    def _get_client_ip(self, request):
        """Extract real client IP, respecting proxy headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    def _is_ip_allowed(self, client_ip, allowed_ranges):
        """Check whether client_ip falls in any of the allowed CIDR ranges."""
        if not client_ip:
            return True  # Cannot determine IP → allow
        try:
            client_addr = ipaddress.ip_address(client_ip)
            for cidr in allowed_ranges:
                try:
                    if client_addr in ipaddress.ip_network(cidr, strict=False):
                        return True
                except ValueError:
                    # Malformed CIDR → skip entry, don't block
                    logger.debug("[Security Middleware] Malformed CIDR %s, skipping", cidr)
            return False
        except ValueError:
            logger.debug("[Security Middleware] Could not parse client IP %s", client_ip)
            return True  # Unparseable IP → allow
