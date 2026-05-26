"""
Entity Access Middleware (Phase 3.3)

Validates that the authenticated user has access to the entity_id
passed in the request (query param or POST body).
DESIGN: Only activates when entity_id is explicitly provided.
        Always fails open when data is missing. Platform admins bypass.
"""

import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Paths where entity_id in the query does NOT mean entity access check
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
    # Tenant management APIs themselves manage entity mappings
    '/api/tenants/',
    '/api/entities/',
    '/api/business-units/',
    '/api/departments/',
    '/api/support-access/',
    '/api/tenant-admins/',
]


class EntityAccessMiddleware(MiddlewareMixin):
    """
    When a request includes entity_id (GET param, POST body, or JSON body),
    verify the user has an active UserEntityMapping for that entity+tenant.
    Blocks with 403 only when mapping is explicitly absent in the DB.
    When table/data is missing → allows through.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        logger.info("✅ Entity Access Middleware loaded")

    def process_request(self, request):
        try:
            if request.method == 'OPTIONS':
                return None

            path = request.path_info
            if any(path.startswith(p) for p in _EXEMPT_PATHS):
                return None

            # Only enforce for authenticated users with resolved tenant
            tenant_id = getattr(request, 'tenant_id', None)
            if not tenant_id:
                return None
            if not hasattr(request, 'user') or not hasattr(request.user, 'UserId'):
                return None

            # Platform admins bypass entity access checks
            if self._is_admin(request.user):
                return None

            # Resolve entity_id from request
            entity_id = self._extract_entity_id(request)
            if not entity_id:
                return None  # No entity_id in request → nothing to check

            user_id = request.user.UserId

            # Check access
            has_access = self._has_entity_access(user_id, entity_id, tenant_id)
            if has_access is False:  # Explicitly False means denied
                logger.warning(
                    "[Entity Middleware] User %s denied access to entity %s (tenant %s)",
                    user_id, entity_id, tenant_id
                )
                return JsonResponse(
                    {'error': 'Access denied: you do not have access to this entity'},
                    status=403
                )

        except Exception as exc:
            logger.error("[Entity Middleware] Unexpected error (failing open): %s", exc)

        return None

    # ── Helpers ────────────────────────────────────────────────────────────

    def _extract_entity_id(self, request):
        """Pull entity_id from GET params, then POST body, then JSON body."""
        # 1. Query string
        entity_id = request.GET.get('entity_id')
        if entity_id:
            return entity_id

        # 2. POST body (form-encoded)
        if hasattr(request, 'POST'):
            entity_id = request.POST.get('entity_id')
            if entity_id:
                return entity_id

        # 3. DRF parsed data (JSON body)
        if hasattr(request, 'data') and isinstance(request.data, dict):
            entity_id = request.data.get('entity_id')
            if entity_id:
                return entity_id

        return None

    def _has_entity_access(self, user_id, entity_id, tenant_id):
        """
        Return True/False/None:
          True  → user has active mapping
          False → mapping explicitly absent (deny)
          None  → table missing or error (fail open)
        Cached 60 seconds per user+entity+tenant.
        """
        cache_key = f"entity_access_{user_id}_{entity_id}_{tenant_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            from .models import UserEntityMapping
            exists = UserEntityMapping.objects.filter(
                user_id=user_id,
                entity_id=entity_id,
                tenant_id=tenant_id,
                status='active',
                is_deleted=False,
            ).exists()
            # If the UserEntityMapping table exists but has no rows at all for this
            # tenant, it likely means the feature isn't configured yet → allow.
            if not exists:
                total = UserEntityMapping.objects.filter(tenant_id=tenant_id).count()
                if total == 0:
                    cache.set(cache_key, True, 60)
                    return True  # Feature not configured yet → open
            result = exists
            cache.set(cache_key, result, 60)
            return result
        except Exception as exc:
            logger.debug("[Entity Middleware] Could not check entity access: %s", exc)
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
