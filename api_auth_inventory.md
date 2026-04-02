# API Authentication Inventory (GRC + TPRM)

Date: 2026-03-26

## Scope
- Backend route entrypoints and security-relevant API handlers under `grc_backend`.
- Classification: `Public`, `Protected`, `Needs Review`.

## What Was Fixed

### Framework-level hardening
- `grc_backend/grc/middleware.py`
  - Enforced secure-by-default auth flow in `JWTAuthenticationMiddleware`.
  - Removed broad public bypasses for sensitive prefixes (`/api/documents/`, `/api/jira/`, `/api/get-notifications/`, `/api/external-applications/`, `/api/users/`).
  - Kept narrow public allowlist for login/OTP/OAuth/static/media.
  - Allowed `OPTIONS` preflight only.

### Sensitive endpoint hardening
- `grc_backend/grc/routes/DocumentHandling/document.py`
  - `get_documents`, `get_document_counts`, `upload_document` now require `IsAuthenticated`.
- `grc_backend/grc/routes/Integrations/jira.py`
  - `jira_users` now requires authenticated caller.
  - `jira_stored_data` now enforces self-or-admin access; removed implicit default-user behavior.
- `grc_backend/grc/routes/Integrations/event_integration.py`
  - Added auth resolution helper and enforced auth + self/admin checks for external app endpoints.
  - Removed default `user_id=1` behavior in sensitive flows.

### Global DRF defaults hardened
- `grc_backend/backend/settings.py`
- `grc_backend/tprm_backend/config/settings.py`
- `grc_backend/tprm_backend/tprm_project/settings.py`
  - `DEFAULT_PERMISSION_CLASSES` changed from `AllowAny` to `IsAuthenticated`.

### High-risk admin API hardening
- `grc_backend/tprm_backend/admin_access/views.py`
  - `get_all_users`, `get_user_permissions`, `update_user_permissions`, `get_all_permission_fields`, `bulk_update_permissions` now require `IsAuthenticated`.

## Current Classification Snapshot

### Protected (post-fix)
- `/api/documents/upload/`
- `/api/documents/list/`
- `/api/documents/counts/`
- `/api/users/`
- `/api/get-notifications/`
- `/api/jira/users/`
- `/api/jira/stored-data/`
- `/api/external-applications/` and related connect/disconnect/details/refresh endpoints
- `/api/tprm/admin-access/*` (authentication required)

### Intentionally Public (expected)
- Login/OTP/password reset endpoints.
- OAuth initiation/callback endpoints required for provider redirects.
- Static/media/public tokenized flows (where explicitly designed).

### Needs Review (recommended next pass)
- Endpoints decorated with `AllowAny` across:
  - `grc_backend/grc/routes/Global/user_profile.py`
  - `grc_backend/tprm_backend/rbac/access_request_views.py`
  - `grc_backend/tprm_backend/apps/vendor_questionnaire/views.py`
  - Other module-specific public/test/debug endpoints.

## Verification Checklist
- Unauthenticated call to sensitive endpoints returns `401/403`.
- Authenticated call with valid JWT/session succeeds.
- Query-parameter user switching is blocked for non-admin users.
- No sensitive data in unauthenticated error responses.

## QA Evidence Targets
- `test_cases.md` section: `Missing Authentication — Protected API endpoints (framework-level)`.
- Save API response screenshots for:
  - Without token: `401/403`
  - With token: `200`

