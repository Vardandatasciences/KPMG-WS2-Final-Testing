"""
Module Enforcement Middleware (Phase 3.2)

Blocks API calls to modules that are disabled for the tenant via TenantModule.
DESIGN: Always fails open - if module data is missing, the request is allowed.
        Platform admins (GRC Administrator) bypass all checks.
"""

import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Maps URL path prefix → module_code in TenantModule
MODULE_PATH_MAP = {
    '/api/frameworks': 'framework',
    '/api/framework': 'framework',
    '/api/policies': 'policy',
    '/api/policy': 'policy',
    '/api/compliances': 'compliance',
    '/api/compliance': 'compliance',
    '/api/audits': 'audit',
    '/api/audit': 'audit',
    '/api/risk': 'risk',
    '/api/system-risks': 'risk',
    '/api/incidents': 'incident',
    '/api/incident': 'incident',
    '/api/events': 'event',
    '/api/event': 'event',
}

# Paths that are always exempt from module checks
_EXEMPT_PATHS = [
    '/api/login/',
    '/api/jwt/',
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
    '/api/rbac/',
    '/api/user-role',
    '/api/users/',
    '/api/tenants/',
    '/api/entities/',
    '/api/business-units/',
    '/api/departments/',
    '/api/support-access/',
    '/api/tenant-admins/',
    '/api/modules/available/',
    '/api/product-version/',
    '/api/security/',
    '/api/notifications',
    '/api/cookie/',
    '/api/data-analysis',
]


class ModuleEnforcementMiddleware(MiddlewareMixin):
    """
    Checks if the accessed module is enabled for the current tenant.
    Returns 403 only when: module data explicitly shows is_enabled=False.
    Otherwise (no data, error, admin user) → allows request through.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        logger.info("✅ Module Enforcement Middleware loaded")

    def process_request(self, request):
        try:
            if request.method == 'OPTIONS':
                return None

            path = request.path_info

            # Skip exempt paths
            if any(path.startswith(p) for p in _EXEMPT_PATHS):
                return None

            # Resolve which module this path belongs to
            module_code = self._get_module_from_path(path)
            if not module_code:
                return None  # Path doesn't map to any module

            # Only enforce for authenticated users with a resolved tenant
            tenant_id = getattr(request, 'tenant_id', None)
            if not tenant_id:
                return None

            if not hasattr(request, 'user') or not hasattr(request.user, 'UserId'):
                return None

            # Platform admins bypass module checks
            if self._is_admin(request.user):
                return None

            # Check module status (cached)
            is_enabled = self._is_module_enabled(tenant_id, module_code)
            if is_enabled is False:  # Explicitly False means disabled
                logger.info(
                    "[Module Middleware] Module '%s' disabled for tenant %s — blocked %s",
                    module_code, tenant_id, path
                )
                return JsonResponse(
                    {
                        'error': 'Module not enabled for this tenant',
                        'module': module_code,
                    },
                    status=403
                )

        except Exception as exc:
            # Never block requests due to middleware errors
            logger.error("[Module Middleware] Unexpected error (failing open): %s", exc)

        return None

    # ── Helpers ────────────────────────────────────────────────────────────

    def _get_module_from_path(self, path):
        """Map a URL path to a module_code. Returns None if no match."""
        for prefix, code in MODULE_PATH_MAP.items():
            if path.startswith(prefix):
                return code
        return None

    def _is_module_enabled(self, tenant_id, module_code):
        """
        Return True/False/None:
          True  → module is enabled
          False → module is explicitly disabled (block)
          None  → no data found (fail open → allow)
        Result is cached per tenant+module for 60 seconds.
        """
        cache_key = f"tenant_module_{tenant_id}_{module_code}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached  # True or False (stored bools)

        try:
            from .models import TenantModule
            obj = TenantModule.objects.filter(
                tenant_id=tenant_id,
                module_code=module_code
            ).first()
            if obj is None:
                # No record means module not yet configured → allow
                cache.set(cache_key, True, 60)
                return True
            result = bool(obj.is_enabled)
            cache.set(cache_key, result, 60)
            return result
        except Exception as exc:
            logger.debug("[Module Middleware] Could not check module status: %s", exc)
            return None  # Fail open

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
