# KPMG Security Issues — Resolution Plan

**Date:** 2026-05-26
**Status:** Open
**Risk Class:** API4, API8

---

## Executive Summary

This document details the root-cause analysis and remediation plan for four outstanding security findings reported by the KPMG testing team. All four issues remain reproducible against the current codebase (`riskavaire.vardaands.com`). Each section includes the exact file path to change, the specific code delta, and verification steps.

---

## 1. Missing Rate Limiting on Audit Creation

| Field | Value |
|-------|-------|
| **Finding ID** | 6 |
| **Severity** | Medium |
| **OWASP Category** | API4 - Unrestricted Resource Consumption |
| **Endpoint** | `POST /api/create-audit/` |

### 1.1 Root Cause

The `create_audit` endpoint in `assign_audit.py` is decorated with `@api_view(['POST'])` but **does not apply any DRF throttle class**. While `backend/settings.py` already defines a scoped throttle named `audit_write` (`10/minute`), the view itself never references it, so DRF silently skips rate-limit enforcement.

An attacker can therefore create hundreds of audit records (and trigger downstream notification spam) with a single authenticated session.

### 1.2 Required Changes

**File:** `grc_backend/grc/routes/Audit/assign_audit.py`

Add the DRF `ScopedRateThrottle` decorator and `throttle_scope` attribute to the view:

```python
from rest_framework.decorators import throttle_classes
from rest_framework.throttling import ScopedRateThrottle

@api_view(['POST'])
@throttle_classes([ScopedRateThrottle])      # <-- ADD
@authentication_classes([CsrfExemptSessionAuthentication, BasicAuthentication])
@permission_classes([AuditAssignPermission])
@audit_assign_required
@require_consent('create_audit')
@require_tenant
@tenant_filter
def create_audit(request):
    """Create new Audit instances …"""
    # No functional change to the body of the view.
```

**File:** `grc_backend/backend/settings.py`

Ensure the scoped throttle rate is present (it already is, but verify it has not been removed):

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '10000/hour',
        'anon': '2000/hour',
        'audit_write': '10/minute',   # <-- KEEP / VERIFY
        ...
    },
}
```

### 1.3 Verification

1. Restart the Gunicorn / Django application.
2. Issue 11 consecutive `POST /api/create-audit/` requests with a valid JWT.
3. The 11th request must return `429 Too Many Requests`.
4. Confirm that other audit read endpoints (e.g., `GET /api/audit/…`) are **not** throttled by this scope.

---

## 2. Server Banner Disclosure

| Field | Value |
|-------|-------|
| **Finding ID** | 10 |
| **Severity** | Low |
| **OWASP Category** | API8 - Security Misconfiguration |

### 2.1 Root Cause

The production host-level Nginx configurations (`deploy/nginx-riskavaire.vardaands.com.conf` and `deploy/nginx-riskavaire.vardaands.com.docker-host.conf`) and the reusable snippet `deploy/nginx-snippets/security-headers.conf` **do not contain** `server_tokens off;`. The frontend container configs (`grc_frontend/nginx.docker.conf`, `grc_frontend/nginx-complete.conf`) already have it, but the host-facing proxy (which is the layer that actually responds to the internet) omits it.

### 2.2 Required Changes

**File:** `deploy/nginx-riskavaire.vardaands.com.conf`

Add inside the `server { }` block (or at the `http` level if this file is included there):

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name riskavaire.vardaands.com;

    server_tokens off;                          # <-- ADD
    include /etc/nginx/snippets/security-headers.conf;
    ...
}
```

**File:** `deploy/nginx-riskavaire.vardaands.com.docker-host.conf`

Add inside the `server { }` block:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name riskavaire.vardaands.com;

    server_tokens off;                          # <-- ADD
    include /etc/nginx/snippets/security-headers.conf;
    ...
}
```

**File:** `deploy/nginx-snippets/security-headers.conf`

Append the server-token directive so that any future vhost that includes this snippet is automatically protected:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

server_tokens off;                            # <-- ADD
```

### 2.3 Verification

1. Deploy the updated Nginx configs and reload (`sudo nginx -t && sudo systemctl reload nginx`).
2. Run: `curl -I https://riskavaire.vardaands.com`
3. Confirm that the `Server:` header is absent or shows only `nginx` with **no version number**.
4. Run: `curl -I https://riskavaire.vardaands.com/api/create-audit/`
5. Confirm the same for API responses.

---

## 3. Content Security Policy (CSP) — unsafe-inline and unsafe-eval

| Field | Value |
|-------|-------|
| **Finding ID** | 11 |
| **Severity** | Low |
| **OWASP Category** | API8 - Security Misconfiguration |

### 3.1 Root Cause

The application emits a **weakened CSP** from two layers:

1. **Nginx (Docker frontend)** — `grc_frontend/nginx.docker.conf` sets:
   - `script-src 'self' 'unsafe-eval'`
   - `style-src 'self' 'unsafe-inline'`
2. **Nginx (complete / fallback)** — `grc_frontend/nginx-complete.conf` sets:
   - `style-src 'self' 'unsafe-inline'`
3. **Django Middleware** — `EnterpriseSecurityHeadersMiddleware._build_csp_policy` in `grc/middleware.py` sets:
   - `script-src 'self' 'unsafe-eval'`

Because the production stack currently serves traffic through `nginx.docker.conf`, browsers receive `unsafe-eval` (permits dynamic code execution such as `eval()` and `new Function()`) and `unsafe-inline` (permits inline `<style>` blocks). Both directives defeat the primary purpose of CSP.

### 3.2 Required Changes

#### 3.2.1 Nginx — `grc_frontend/nginx.docker.conf`

Replace the two CSP header lines (lines 94 and 106) with a hardened policy. The current lines:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-eval' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; font-src 'self' data:; connect-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; frame-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'self'" always;
```

**New value** (remove `'unsafe-eval'` from `script-src` and `'unsafe-inline'` from `style-src`):

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; img-src 'self' data: https:; style-src 'self'; font-src 'self' data:; connect-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; frame-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'self'" always;
```

#### 3.2.2 Nginx — `grc_frontend/nginx-complete.conf`

Replace line 109:

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; img-src 'self' data: https:; style-src 'self' 'unsafe-inline'; font-src 'self' data:; connect-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; frame-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'" always;
```

**New value** (remove `'unsafe-inline'` from `style-src`):

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; img-src 'self' data: https:; style-src 'self'; font-src 'self' data:; connect-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; frame-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'" always;
```

#### 3.2.3 Django Middleware — `grc_backend/grc/middleware.py`

In `EnterpriseSecurityHeadersMiddleware._build_csp_policy` (around line 981), change:

```python
# BEFORE
        directives.append("script-src 'self' 'unsafe-eval'")
```

```python
# AFTER
        directives.append("script-src 'self'")
```

> **Note:** If the Vue.js runtime or any other dependency legitimately requires `unsafe-eval` (e.g., runtime template compilation), migrate to a build that pre-compiles templates so the directive is unnecessary. If a temporary exception is required, use a **nonce** or **hash** instead of `'unsafe-eval'`.

#### 3.2.4 Inline Styles / Scripts (Follow-up)

Audit the SPA build output (`grc_frontend/dist/`) and Django templates for:
- Inline `<script>` blocks
- Inline `style="…"` attributes
- `<style>` tags inside HTML

Replace with external `.js` / `.css` files. If inline content is unavoidable, generate CSP nonces server-side and inject them into the response headers and the corresponding HTML tags.

### 3.3 Verification

1. Rebuild / redeploy the frontend container and/or reload Nginx.
2. Restart the Django application.
3. Run: `curl -I https://riskavaire.vardaands.com`
4. Inspect the `Content-Security-Policy` header.
5. Confirm:
   - `script-src` does **not** contain `'unsafe-eval'`
   - `style-src` does **not** contain `'unsafe-inline'`
6. Open the application in a browser, open DevTools → Console, and verify that **no CSP violation reports** are emitted on the login page or the dashboard. If violations appear, trace the violating inline resource and externalize it.

---

## 4. Duplicate CORS Configuration

| Field | Value |
|-------|-------|
| **Finding ID** | 13 |
| **Severity** | Informational Only |
| **OWASP Category** | API8 - Security Misconfiguration |

### 4.1 Root Cause

Two audit-related views (`assign_audit.py` and `auditing.py`) **manually inject** `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`, and `Access-Control-Allow-Credentials` into the `HttpResponse` object. At the same time, `corsheaders.middleware.CorsMiddleware` (installed in `INSTALLED_APPS` and `MIDDLEWARE`) computes and attaches the **same** headers based on `settings.CORS_ALLOWED_ORIGINS`.

Because Django headers allow multiple values for the same key, the browser receives **duplicate CORS headers**, creating ambiguous policy interpretation. Additionally, the hard-coded origin in the manual injection (`http://localhost:8080`) is invalid for production and one occurrence is malformed (`http://:8080`).

The correct design is to centralize CORS entirely in `django-cors-headers` and remove all ad-hoc manual injections.

### 4.2 Required Changes

**File:** `grc_backend/grc/routes/Audit/assign_audit.py`

Remove **all** manual CORS header blocks. There are three occurrences:

1. **Lines 988–995** (inside the `OPTIONS` preflight handler):

```python
# REMOVE this entire block:
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
        return response
```

> `corsheaders.middleware.CorsMiddleware` already handles `OPTIONS` preflight automatically; this block is redundant.

2. **Lines 1302–1307** (success response):

```python
# REMOVE these four lines:
        response["Access-Control-Allow-Origin"] = "http://localhost:8080"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
```

3. **Lines 1323–1327** (error response):

```python
# REMOVE these four lines:
        response["Access-Control-Allow-Origin"] = "http://:8080"   # malformed
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
```

**File:** `grc_backend/grc/routes/Audit/auditing.py`

Remove the manual CORS block around lines 1203–1207:

```python
# REMOVE these four lines:
                response["Access-Control-Allow-Origin"] = "http://localhost:8080"
                response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
                response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
                response["Access-Control-Allow-Credentials"] = "true"
```

**File:** `grc_backend/backend/settings.py`

Ensure the centralized CORS configuration is locked down (already correct, but verify):

```python
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://riskavaire.vardaands.com",
    "https://riskavairegrc.vardaands.com",
    "https://grc-tprm.vardaands.com",
    # … other explicit origins …
]
```

**File:** `grc_backend/grc/middleware.py` (optional cleanup)

Delete the legacy no-op `CORSMiddleware` class to prevent accidental future activation:

```python
# REMOVE this entire class:
class CORSMiddleware(MiddlewareMixin):
    def process_request(self, request):
        return None
```

### 4.3 Verification

1. Restart the Django application.
2. Run: `curl -I -X OPTIONS -H "Origin: https://riskavaire.vardaands.com" -H "Access-Control-Request-Method: POST" https://riskavaire.vardaands.com/api/create-audit/`
3. Inspect the response headers.
4. Confirm:
   - Only **one** `Access-Control-Allow-Origin` header is present.
   - Its value is `https://riskavaire.vardaands.com` (not `*` and not duplicated).
   - `Access-Control-Allow-Methods` and `Access-Control-Allow-Headers` appear **once** each.
5. Repeat the curl for `POST /api/create-audit/` with the same `Origin` header and verify the same single-header behaviour on the actual response.
6. Send a request from an **untrusted origin** (e.g., `Origin: https://evil.com`) and confirm that `Access-Control-Allow-Origin` is **absent** (proving `CORS_ALLOW_ALL_ORIGINS = False` is enforced).

---

## Implementation Order & Rollback

| Priority | Issue | File(s) | Rollback |
|----------|-------|---------|----------|
| P1 | 4 - Duplicate CORS | `assign_audit.py`, `auditing.py` | Revert deleted lines |
| P2 | 1 - Rate Limiting | `assign_audit.py`, `settings.py` | Remove `@throttle_classes` decorator |
| P3 | 2 - Server Banner | `nginx*.conf`, `security-headers.conf` | Comment out `server_tokens off;` |
| P4 | 3 - CSP | `nginx.docker.conf`, `nginx-complete.conf`, `middleware.py` | Restore previous `add_header` values |

> **Deployment Tip:** Because Issues 2, 3, and 4 involve Nginx config changes, validate with `nginx -t` before reloading. Issue 1 and Issue 4 (Python changes) require only a Gunicorn / uWSGI reload.

---

## Post-Fix KPMG Re-Test Checklist

- [ ] `POST /api/create-audit/` returns `429` after 11 rapid requests from the same authenticated user.
- [ ] `Server` header no longer discloses the Nginx version on any path (`/` and `/api/…`).
- [ ] `Content-Security-Policy` header does **not** contain `'unsafe-eval'` or `'unsafe-inline'`.
- [ ] `Access-Control-Allow-Origin` appears **exactly once** per response and never equals `*`.
- [ ] No functional regression in audit creation, frontend SPA loading, or CORS preflight from legitimate origins.
