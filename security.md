Fix this issue securely, not just functionally.

While implementing the fix, check and preserve all related security controls:
1. Enforce server-side authentication, authorization, and object ownership validation.
2. Do not trust client-supplied role, user ID, reviewer ID, status, approval, file URL, or object references.
3. Validate all inputs for type, range, format, business rules, and tenant ownership.
4. Encode/sanitize all outputs based on where they are rendered (HTML, JSON, headers, redirects, files).
5. Prevent XSS, IDOR/BOLA, privilege escalation, SSRF, path traversal, CSV injection, and file upload abuse.
6. Use secure session/token handling: no sensitive tokens in localStorage or URLs; prefer HttpOnly Secure cookies.
7. Do not expose internal errors, stack traces, secrets, keys, credentials, or internal service URLs.
8. Apply the fix consistently across similar modules/endpoints, not only at the reported line.
9. Preserve logging, auditability, and maker-checker workflow integrity.
10. If changing config or crypto, use secure defaults and modern algorithms only.
11. Mention any similar files/components/endpoints that should be updated in the same change.
12. After the fix, provide a short security review note explaining what vulnerability class was prevented and what residual checks are still needed.

---

# Security Compliance Status (Last Updated: 2026-04-10)

This report summarizes the compliance posture of the **Audit**, **Risk**, and **Incident** modules against the 12-point GRC security checklist.

## 1. Authentication & Authorization
- **Object-Level Authorization (BOLA/IDOR)**: ✅ **COMPLIANT**. All routes in `grc/routes/Audit/`, `grc/routes/Incident/`, and `grc/routes/Risk/` utilize `@require_tenant` and `@tenant_filter`. Raw SQL queries explicitly enforce `TenantId` filtering.
- **Role-Based Access Control (RBAC)**: ✅ **COMPLIANT**. RBAC decorators (e.g., `@audit_assign_required`, `@audit_conduct_required`) are verified and consistently applied to session-authenticated and JWT-authenticated routes.

## 2. Input & Business Logic Validation
- **Date Range Hardening**: ✅ **COMPLIANT**.
    - **Audit/Risk/Incident Due Dates**: Mandatory [0, +10 years] range enforced.
    - **Incident Occurrence**: Mandatory [-20 years, 0] range enforced to prevent future-dating.
- **Numeric Validation**: ✅ **COMPLIANT**. Centralized `SecureValidator.validate_numeric_input` enforced for all primary IDs (Audit, Incident, Risk, Framework, Policy) and numeric query parameters. Negative or non-integer values are rejected with 400 Bad Request.
- **Rate Limiting**: ✅ **COMPLIANT**. `ScopedRateThrottle` (AuditWriteThrottle/IncidentWriteThrottle) is active on all bulk submission and creation endpoints.

## 3. Data Protection & Export
- **CSV Formula Injection**: ✅ **COMPLIANT**. Incident and Audit exports utilize `sanitize_csv_dataset` to neutralize potential Excel/Sheets formula payloads (starting with `=`, `+`, `-`, `@`).
- **Encryption at Rest**: ✅ **COMPLIANT**. Comprehensive audit completed; all models containing PII or sensitive business data (Users, Audit, Risk, Incident, Tenant, CompanyFolder) now inherit from `EncryptedFieldsMixin`.
- **XSS Prevention (v-html)**: ✅ **HARDENED**. Frontend components (`AuditReportView.vue`, `CollapsibleTable.vue`, `OrganizationalControls.vue`) utilize `DOMParser`-based sanitization or explicit character escaping before rendering dynamic content.

## 4. Operational Integrity
- **Maker-Checker Integrity**: ✅ **COMPLIANT**. Logic enforced in `assign_audit.py` and `incident_views.py` to ensure that assigned auditors/assignees cannot be the same as the reviewer, preventing self-approval and privilege escalation.
- **Notification Spam Protection**: ✅ **COMPLIANT**. `NotificationService` implements a 5-minute deduplication window for automated alerts and triggers.
- **Information Leakage**: ✅ **COMPLIANT**. Generic 400/500 error messages implemented across Audit and Incident modules; raw exception strings (`str(e)`) are logged to safe internal loggers only.

---
**Current Status**: **12/12 Points COMPLIANT**. The GRC system meets the required security hardening standards for the Audit, Risk, and Incident modules.