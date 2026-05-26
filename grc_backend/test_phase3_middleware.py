"""
Phase 3 Middleware Test Suite
===============================
Tests for:
  3.1 TenantContextMiddleware — entity_id resolution & user-tenant mapping warning
  3.2 ModuleEnforcementMiddleware — block disabled modules
  3.3 EntityAccessMiddleware — block unauthorised entity access
  3.4 TenantSecurityMiddleware — IP restriction enforcement
  3.5 jwt_login() enriched response — tenant context fields

Run with:
    python manage.py test grc.tests.test_phase3_middleware -v 2
"""

import json
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

import django
from django.conf import settings
if not settings.configured:
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    django.setup()

from django.test import RequestFactory
from django.http import JsonResponse


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_user(user_id=1, is_admin=False):
    """Return a lightweight mock user (no DB hit)."""
    user = MagicMock()
    user.UserId = user_id
    user.UserName = f"testuser_{user_id}"
    user.Email = f"testuser_{user_id}@example.com"
    user.IsActive = "Y"
    user.consent_accepted = "1"
    user.license_key = "TEST-KEY"
    user.tenant = None
    user.tenant_id = None
    return user


def _make_tenant(tenant_id=10, status="active"):
    """Return a mock Tenant."""
    t = MagicMock()
    t.tenant_id = tenant_id
    t.name = f"Tenant {tenant_id}"
    t.status = status
    return t


def _get_response_ok(request):
    """Dummy downstream view that always returns 200."""
    from django.http import HttpResponse
    return HttpResponse("OK", status=200)


# ─────────────────────────────────────────────────────────────────────────────
# 3.4  TenantSecurityMiddleware
# ─────────────────────────────────────────────────────────────────────────────

class TenantSecurityMiddlewareTests(unittest.TestCase):
    """TC-SEC-*: IP restriction enforcement."""

    def setUp(self):
        from grc.security_middleware import TenantSecurityMiddleware
        self.middleware = TenantSecurityMiddleware(_get_response_ok)
        self.rf = RequestFactory()

    def _req(self, path="/api/policies/", ip="192.168.1.50", tenant_id=10, user_id=1):
        req = self.rf.get(path, REMOTE_ADDR=ip)
        req.tenant_id = tenant_id
        req.user = _make_user(user_id)
        return req

    # TC-SEC-01: No security settings configured → allow
    @patch("grc.security_middleware.cache")
    def test_no_settings_configured_allows_request(self, mock_cache):
        mock_cache.get.return_value = None
        with patch("grc.security_middleware.TenantSecurityMiddleware._get_security_settings",
                   return_value={}):
            result = self.middleware.process_request(self._req())
        self.assertIsNone(result, "Should allow when no security settings")

    # TC-SEC-02: IP restriction disabled → allow any IP
    @patch("grc.security_middleware.cache")
    def test_ip_restriction_disabled_allows_any_ip(self, mock_cache):
        mock_cache.get.return_value = None
        with patch("grc.security_middleware.TenantSecurityMiddleware._get_security_settings",
                   return_value={"ip_restriction_enabled": False, "allowed_ip_ranges": ["10.0.0.0/8"]}):
            result = self.middleware.process_request(self._req(ip="1.2.3.4"))
        self.assertIsNone(result, "Should allow when IP restriction is disabled")

    # TC-SEC-03: IP in allowed range → allow
    @patch("grc.security_middleware.cache")
    def test_allowed_ip_passes(self, mock_cache):
        mock_cache.get.return_value = None
        with patch("grc.security_middleware.TenantSecurityMiddleware._get_security_settings",
                   return_value={"ip_restriction_enabled": True, "allowed_ip_ranges": ["192.168.1.0/24"]}):
            result = self.middleware.process_request(self._req(ip="192.168.1.50"))
        self.assertIsNone(result, "IP 192.168.1.50 should be within 192.168.1.0/24")

    # TC-SEC-04: IP NOT in allowed range → 403
    @patch("grc.security_middleware.cache")
    def test_blocked_ip_returns_403(self, mock_cache):
        mock_cache.get.return_value = None
        with patch("grc.security_middleware.TenantSecurityMiddleware._get_security_settings",
                   return_value={"ip_restriction_enabled": True, "allowed_ip_ranges": ["10.0.0.0/8"]}), \
             patch("grc.security_middleware.TenantSecurityMiddleware._is_admin", return_value=False):
            result = self.middleware.process_request(self._req(ip="8.8.8.8"))
        self.assertIsInstance(result, JsonResponse)
        self.assertEqual(result.status_code, 403)
        data = json.loads(result.content)
        self.assertIn("IP address not allowed", data["error"])

    # TC-SEC-05: Admin user bypasses IP block
    @patch("grc.security_middleware.cache")
    def test_admin_bypasses_ip_restriction(self, mock_cache):
        mock_cache.get.return_value = None
        with patch("grc.security_middleware.TenantSecurityMiddleware._get_security_settings",
                   return_value={"ip_restriction_enabled": True, "allowed_ip_ranges": ["10.0.0.0/8"]}), \
             patch("grc.security_middleware.TenantSecurityMiddleware._is_admin", return_value=True):
            result = self.middleware.process_request(self._req(ip="8.8.8.8"))
        self.assertIsNone(result, "Admin should bypass IP restriction")

    # TC-SEC-06: Login path is exempt
    def test_login_path_exempt(self):
        req = self._req(path="/api/jwt/login/", ip="8.8.8.8")
        result = self.middleware.process_request(req)
        self.assertIsNone(result, "Login path must be exempt from security middleware")

    # TC-SEC-07: No tenant_id → skip (fail open)
    def test_no_tenant_id_skips(self):
        req = self._req()
        req.tenant_id = None
        result = self.middleware.process_request(req)
        self.assertIsNone(result, "Without tenant_id, middleware must skip")

    # TC-SEC-08: DB exception → fail open
    @patch("grc.security_middleware.cache")
    def test_db_exception_fails_open(self, mock_cache):
        mock_cache.get.return_value = None
        with patch("grc.security_middleware.TenantSecurityMiddleware._get_security_settings",
                   side_effect=Exception("DB down")):
            result = self.middleware.process_request(self._req(ip="1.2.3.4"))
        self.assertIsNone(result, "DB exception must not block request (fail open)")


# ─────────────────────────────────────────────────────────────────────────────
# 3.2  ModuleEnforcementMiddleware
# ─────────────────────────────────────────────────────────────────────────────

class ModuleEnforcementMiddlewareTests(unittest.TestCase):
    """TC-MOD-*: Module gating."""

    def setUp(self):
        from grc.module_middleware import ModuleEnforcementMiddleware
        self.middleware = ModuleEnforcementMiddleware(_get_response_ok)
        self.rf = RequestFactory()

    def _req(self, path="/api/risk/register/", tenant_id=10, user_id=1):
        req = self.rf.get(path)
        req.tenant_id = tenant_id
        req.user = _make_user(user_id)
        return req

    # TC-MOD-01: Module enabled → allow
    @patch("grc.module_middleware.ModuleEnforcementMiddleware._is_module_enabled", return_value=True)
    @patch("grc.module_middleware.ModuleEnforcementMiddleware._is_admin", return_value=False)
    def test_enabled_module_allows_request(self, _admin, _mod):
        result = self.middleware.process_request(self._req(path="/api/risk/register/"))
        self.assertIsNone(result, "Enabled module should allow request")

    # TC-MOD-02: Module explicitly disabled → 403
    @patch("grc.module_middleware.ModuleEnforcementMiddleware._is_module_enabled", return_value=False)
    @patch("grc.module_middleware.ModuleEnforcementMiddleware._is_admin", return_value=False)
    def test_disabled_module_returns_403(self, _admin, _mod):
        result = self.middleware.process_request(self._req(path="/api/risk/register/"))
        self.assertIsInstance(result, JsonResponse)
        self.assertEqual(result.status_code, 403)
        data = json.loads(result.content)
        self.assertEqual(data["module"], "risk")

    # TC-MOD-03: No TenantModule row (None) → allow (fail open)
    @patch("grc.module_middleware.ModuleEnforcementMiddleware._is_module_enabled", return_value=None)
    @patch("grc.module_middleware.ModuleEnforcementMiddleware._is_admin", return_value=False)
    def test_missing_module_record_allows_request(self, _admin, _mod):
        result = self.middleware.process_request(self._req(path="/api/risk/register/"))
        self.assertIsNone(result, "Missing TenantModule row must fail open")

    # TC-MOD-04: Admin bypasses disabled module
    @patch("grc.module_middleware.ModuleEnforcementMiddleware._is_module_enabled", return_value=False)
    @patch("grc.module_middleware.ModuleEnforcementMiddleware._is_admin", return_value=True)
    def test_admin_bypasses_disabled_module(self, _admin, _mod):
        result = self.middleware.process_request(self._req(path="/api/risk/register/"))
        self.assertIsNone(result, "Admin should bypass disabled module block")

    # TC-MOD-05: Path doesn't map to any module → allow
    @patch("grc.module_middleware.ModuleEnforcementMiddleware._is_admin", return_value=False)
    def test_unmapped_path_allows_request(self, _admin):
        result = self.middleware.process_request(self._req(path="/api/rbac/user-permissions/"))
        self.assertIsNone(result, "Non-module path must always pass through")

    # TC-MOD-06: Exempt path (tenants) → always allow
    def test_tenant_management_path_exempt(self):
        result = self.middleware.process_request(self._req(path="/api/tenants/10/modules/"))
        self.assertIsNone(result, "Tenant management paths must be exempt")

    # TC-MOD-07: No tenant_id → skip
    def test_no_tenant_id_skips(self):
        req = self._req(path="/api/risk/register/")
        req.tenant_id = None
        result = self.middleware.process_request(req)
        self.assertIsNone(result, "Without tenant_id, module middleware must skip")

    # TC-MOD-08: Different module paths map correctly
    def test_module_path_mapping(self):
        from grc.module_middleware import ModuleEnforcementMiddleware
        mw = ModuleEnforcementMiddleware(_get_response_ok)
        self.assertEqual(mw._get_module_from_path("/api/policies/"), "policy")
        self.assertEqual(mw._get_module_from_path("/api/frameworks/"), "framework")
        self.assertEqual(mw._get_module_from_path("/api/audits/"), "audit")
        self.assertEqual(mw._get_module_from_path("/api/incidents/"), "incident")
        self.assertEqual(mw._get_module_from_path("/api/compliance/"), "compliance")
        self.assertIsNone(mw._get_module_from_path("/api/rbac/user-permissions/"))

    # TC-MOD-09: DB exception → fail open
    @patch("grc.module_middleware.ModuleEnforcementMiddleware._is_admin", return_value=False)
    def test_db_exception_fails_open(self, _admin):
        with patch("grc.module_middleware.ModuleEnforcementMiddleware._is_module_enabled",
                   side_effect=Exception("DB down")):
            result = self.middleware.process_request(self._req(path="/api/risk/register/"))
        self.assertIsNone(result, "DB exception must not block request (fail open)")


# ─────────────────────────────────────────────────────────────────────────────
# 3.3  EntityAccessMiddleware
# ─────────────────────────────────────────────────────────────────────────────

class EntityAccessMiddlewareTests(unittest.TestCase):
    """TC-ENT-*: Entity-level access control."""

    def setUp(self):
        from grc.entity_middleware import EntityAccessMiddleware
        self.middleware = EntityAccessMiddleware(_get_response_ok)
        self.rf = RequestFactory()

    def _req(self, path="/api/policies/", entity_id=None, tenant_id=10, user_id=1):
        params = {"entity_id": entity_id} if entity_id else {}
        req = self.rf.get(path, params)
        req.tenant_id = tenant_id
        req.user = _make_user(user_id)
        return req

    # TC-ENT-01: No entity_id in request → skip (allow)
    def test_no_entity_id_skips(self):
        result = self.middleware.process_request(self._req())
        self.assertIsNone(result, "No entity_id must skip entity check")

    # TC-ENT-02: User has mapping → allow
    @patch("grc.entity_middleware.EntityAccessMiddleware._has_entity_access", return_value=True)
    @patch("grc.entity_middleware.EntityAccessMiddleware._is_admin", return_value=False)
    def test_mapped_entity_allows_request(self, _admin, _access):
        result = self.middleware.process_request(self._req(entity_id=5))
        self.assertIsNone(result, "Mapped entity should allow request")

    # TC-ENT-03: User has NO mapping (False) → 403
    @patch("grc.entity_middleware.EntityAccessMiddleware._has_entity_access", return_value=False)
    @patch("grc.entity_middleware.EntityAccessMiddleware._is_admin", return_value=False)
    def test_unmapped_entity_returns_403(self, _admin, _access):
        result = self.middleware.process_request(self._req(entity_id=5))
        self.assertIsInstance(result, JsonResponse)
        self.assertEqual(result.status_code, 403)
        data = json.loads(result.content)
        self.assertIn("entity", data["error"].lower())

    # TC-ENT-04: No UserEntityMapping rows at all → fail open (None)
    @patch("grc.entity_middleware.EntityAccessMiddleware._has_entity_access", return_value=None)
    @patch("grc.entity_middleware.EntityAccessMiddleware._is_admin", return_value=False)
    def test_no_mapping_rows_fails_open(self, _admin, _access):
        result = self.middleware.process_request(self._req(entity_id=5))
        self.assertIsNone(result, "None result must fail open")

    # TC-ENT-05: Admin bypasses entity check
    @patch("grc.entity_middleware.EntityAccessMiddleware._has_entity_access", return_value=False)
    @patch("grc.entity_middleware.EntityAccessMiddleware._is_admin", return_value=True)
    def test_admin_bypasses_entity_check(self, _admin, _access):
        result = self.middleware.process_request(self._req(entity_id=5))
        self.assertIsNone(result, "Admin must bypass entity access check")

    # TC-ENT-06: No tenant_id → skip
    def test_no_tenant_id_skips(self):
        req = self._req(entity_id=5)
        req.tenant_id = None
        result = self.middleware.process_request(req)
        self.assertIsNone(result, "Without tenant_id, entity middleware must skip")

    # TC-ENT-07: Exempt path (entities management) → skip
    def test_entity_management_path_exempt(self):
        result = self.middleware.process_request(
            self._req(path="/api/entities/5/", entity_id=5)
        )
        self.assertIsNone(result, "Entity management paths must be exempt")

    # TC-ENT-08: entity_id in POST body is detected
    @patch("grc.entity_middleware.EntityAccessMiddleware._has_entity_access", return_value=False)
    @patch("grc.entity_middleware.EntityAccessMiddleware._is_admin", return_value=False)
    def test_entity_id_from_post_body(self, _admin, _access):
        req = self.rf.post("/api/policies/", data={"entity_id": "5"})
        req.tenant_id = 10
        req.user = _make_user(1)
        result = self.middleware.process_request(req)
        self.assertIsInstance(result, JsonResponse)
        self.assertEqual(result.status_code, 403)

    # TC-ENT-09: DB exception → fail open
    @patch("grc.entity_middleware.EntityAccessMiddleware._is_admin", return_value=False)
    def test_db_exception_fails_open(self, _admin):
        with patch("grc.entity_middleware.EntityAccessMiddleware._has_entity_access",
                   side_effect=Exception("DB down")):
            result = self.middleware.process_request(self._req(entity_id=5))
        self.assertIsNone(result, "DB exception must not block request (fail open)")


# ─────────────────────────────────────────────────────────────────────────────
# 3.1  TenantContextMiddleware — Phase 3.1 additions
# ─────────────────────────────────────────────────────────────────────────────

class TenantContextMiddlewarePhase3Tests(unittest.TestCase):
    """TC-CTX-*: entity_id resolution and user-tenant mapping validation."""

    def setUp(self):
        from grc.tenant_middleware import TenantContextMiddleware
        self.middleware = TenantContextMiddleware(_get_response_ok)
        self.rf = RequestFactory()

    # TC-CTX-01: entity_id in query string is attached to request
    def test_entity_id_from_query_string(self):
        req = self.rf.get("/api/policies/", {"entity_id": "7"})
        req.user = _make_user()
        result = self.middleware._resolve_entity_id(req)
        self.assertEqual(result, "7")

    # TC-CTX-02: entity_id in DRF body (dict) is attached to request
    def test_entity_id_from_drf_data(self):
        req = self.rf.post("/api/policies/")
        req.user = _make_user()
        req.data = {"entity_id": "9"}
        result = self.middleware._resolve_entity_id(req)
        self.assertEqual(result, "9")

    # TC-CTX-03: No entity_id anywhere → returns None
    def test_no_entity_id_returns_none(self):
        req = self.rf.get("/api/policies/")
        req.user = _make_user()
        result = self.middleware._resolve_entity_id(req)
        self.assertIsNone(result)

    # TC-CTX-04: User-tenant mapping warning is non-blocking
    def test_user_tenant_mapping_warning_does_not_block(self):
        req = self.rf.get("/api/policies/")
        req.tenant_id = 10
        req.user = _make_user(user_id=99)

        with patch("grc.models.TenantUserMapping") as MockMapping, \
             patch("django.core.cache.cache") as mock_cache:
            mock_cache.get.return_value = None
            mock_cache.set.return_value = None
            MockMapping.objects.filter.return_value.exists.side_effect = [True, False]
            # Must not raise and must not return a response
            self.middleware._validate_user_tenant_mapping(req)
            # Test passes if no exception raised

    # TC-CTX-05: request.entity_id is set to None when no entity_id in request
    def test_request_entity_id_default_none(self):
        req = self.rf.get("/api/policies/")
        req.user = _make_user()
        result = self.middleware._resolve_entity_id(req)
        self.assertIsNone(result)


# ─────────────────────────────────────────────────────────────────────────────
# 3.5  Login response — tenant context enrichment
# ─────────────────────────────────────────────────────────────────────────────

class LoginTenantContextTests(unittest.TestCase):
    """TC-LOGIN-*: jwt_login() returns enriched tenant context fields."""

    def setUp(self):
        from grc.authentication import _build_tenant_context_for_login
        self.build_ctx = _build_tenant_context_for_login

    # TC-LOGIN-01: Returns empty dict gracefully when tables empty / no data
    @patch("grc.models.TenantUserMapping")
    @patch("grc.models.UserEntityMapping")
    @patch("grc.models.TenantModule")
    def test_empty_db_returns_safe_defaults(self, MockModule, MockEntity, MockMapping):
        MockMapping.objects.filter.return_value.select_related.return_value = []
        MockEntity.objects.filter.return_value.select_related.return_value = []
        MockModule.objects.filter.return_value = []
        user = _make_user()
        ctx = self.build_ctx(user, tenant_id=10)
        self.assertIn("allowed_tenants", ctx)
        self.assertIn("allowed_entities", ctx)
        self.assertIn("enabled_modules", ctx)
        self.assertEqual(ctx["allowed_tenants"], [])
        self.assertEqual(ctx["allowed_entities"], [])
        self.assertEqual(ctx["enabled_modules"], [])

    # TC-LOGIN-02: Allowed tenants populated correctly
    @patch("grc.models.TenantUserMapping")
    def test_allowed_tenants_populated(self, MockMapping):
        mock_tenant = MagicMock()
        mock_tenant.tenant_id = 10
        mock_tenant.name = "Acme Corp"
        mock_m = MagicMock()
        mock_m.tenant_id = 10
        mock_m.tenant = mock_tenant
        mock_m.role = "GRC Administrator"
        MockMapping.objects.filter.return_value.select_related.return_value = [mock_m]
        user = _make_user()
        ctx = self.build_ctx(user, tenant_id=10)
        self.assertEqual(len(ctx["allowed_tenants"]), 1)
        self.assertEqual(ctx["allowed_tenants"][0]["id"], 10)
        self.assertEqual(ctx["allowed_tenants"][0]["role"], "GRC Administrator")

    # TC-LOGIN-03: Enabled modules populated correctly
    @patch("grc.models.TenantModule")
    def test_enabled_modules_populated(self, MockModule):
        m1, m2 = MagicMock(), MagicMock()
        m1.module_code = "risk"
        m2.module_code = "policy"
        MockModule.objects.filter.return_value = [m1, m2]
        user = _make_user()
        ctx = self.build_ctx(user, tenant_id=10)
        self.assertIn("risk", ctx["enabled_modules"])
        self.assertIn("policy", ctx["enabled_modules"])

    # TC-LOGIN-04: DB exception in one block does NOT break entire context
    def test_partial_db_failure_returns_partial_context(self):
        user = _make_user()
        with patch("grc.models.TenantUserMapping",
                   side_effect=Exception("DB down")):
            ctx = self.build_ctx(user, tenant_id=10)
        # Other keys may or may not exist; important thing is no exception raised
        self.assertIsInstance(ctx, dict)

    # TC-LOGIN-05: Security settings included when present
    @patch("grc.models.TenantSecuritySettings")
    def test_security_settings_included(self, MockSec):
        sec = MagicMock()
        sec.mfa_required = True
        sec.session_timeout_minutes = 30
        sec.password_expiry_days = 90
        MockSec.objects.filter.return_value.first.return_value = sec
        user = _make_user()
        ctx = self.build_ctx(user, tenant_id=10)
        self.assertIn("security_settings", ctx)
        self.assertTrue(ctx["security_settings"]["mfa_required"])

    # TC-LOGIN-06: Branding included when present
    @patch("grc.models.TenantBranding")
    def test_branding_included(self, MockBranding):
        b = MagicMock()
        b.logo_url = "https://cdn.example.com/logo.png"
        b.primary_color = "#1976D2"
        b.secondary_color = "#424242"
        b.accent_color = "#82B1FF"
        MockBranding.objects.filter.return_value.first.return_value = b
        user = _make_user()
        ctx = self.build_ctx(user, tenant_id=10)
        self.assertIn("branding", ctx)
        self.assertEqual(ctx["branding"]["logo_url"], "https://cdn.example.com/logo.png")
        self.assertEqual(ctx["branding"]["primary_color"], "#1976D2")


# ─────────────────────────────────────────────────────────────────────────────
# IP helper unit tests
# ─────────────────────────────────────────────────────────────────────────────

class IPHelperTests(unittest.TestCase):
    """TC-IP-*: _is_ip_allowed() and _get_client_ip() helpers."""

    def setUp(self):
        from grc.security_middleware import TenantSecurityMiddleware
        self.mw = TenantSecurityMiddleware(_get_response_ok)

    # TC-IP-01: IP inside single CIDR → allowed
    def test_ip_inside_cidr_allowed(self):
        self.assertTrue(self.mw._is_ip_allowed("192.168.1.100", ["192.168.1.0/24"]))

    # TC-IP-02: IP outside all CIDRs → denied
    def test_ip_outside_cidr_denied(self):
        self.assertFalse(self.mw._is_ip_allowed("8.8.8.8", ["192.168.1.0/24", "10.0.0.0/8"]))

    # TC-IP-03: IP matches second CIDR in list → allowed
    def test_ip_matches_second_range(self):
        self.assertTrue(self.mw._is_ip_allowed("10.5.5.5", ["192.168.0.0/16", "10.0.0.0/8"]))

    # TC-IP-04: Malformed CIDR entry → skip entry, don't crash
    def test_malformed_cidr_skipped(self):
        # Should not raise; malformed CIDR is skipped
        result = self.mw._is_ip_allowed("8.8.8.8", ["not-a-cidr", "10.0.0.0/8"])
        self.assertFalse(result)

    # TC-IP-05: Empty allowed_ranges → denies all
    def test_empty_ranges_denies(self):
        self.assertFalse(self.mw._is_ip_allowed("1.2.3.4", []))

    # TC-IP-06: X-Forwarded-For header is used for client IP
    def test_x_forwarded_for_used(self):
        rf = RequestFactory()
        req = rf.get("/", HTTP_X_FORWARDED_FOR="203.0.113.5, 10.0.0.1")
        ip = self.mw._get_client_ip(req)
        self.assertEqual(ip, "203.0.113.5")

    # TC-IP-07: REMOTE_ADDR fallback used when no proxy header
    def test_remote_addr_fallback(self):
        rf = RequestFactory()
        req = rf.get("/", REMOTE_ADDR="172.16.0.1")
        ip = self.mw._get_client_ip(req)
        self.assertEqual(ip, "172.16.0.1")
