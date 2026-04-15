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

A. Authentication, login, OTP, SSO, and session security
All APIs are authenticated by default unless explicitly intended to be public.
Public endpoints are documented, justified, and reviewed.
OTP verification is validated only on the backend.
OTP is bound to user, session, expiry, and attempt count.
Google SSO and any other SSO flow do not expose tokens in URL/query string/hash in an unsafe way.
Session tokens are never passed in query strings.
Access tokens, refresh tokens, and session tokens are not stored in localStorage or sessionStorage.
Sensitive auth state is moved to Secure, HttpOnly cookies or safe server-side session handling.
Cookies consistently use HttpOnly, Secure, and appropriate SameSite settings.
Session identifiers are regenerated after login.
Session lifetime, browser-close expiry, and persistence are reviewed.
Concurrent session policy is implemented or actively monitored.
Session hijack resistance is improved with device binding/fingerprinting where appropriate.
All login, logout, password reset, OTP, and session events are audited.
JWT signing uses hardened algorithms such as RS256/ES256 where required.
JWT issuer, audience, expiry, revocation, blacklist, and rotation are enforced.
Refresh token rotation is implemented consistently.
MFA is mandatory for administrators.
MFA is mandatory for external or vendor users where policy requires.
MFA cannot be silently disabled in production through unsafe configuration.
Role-based MFA policies are defined and enforced.
Stronger MFA options are available where email OTP alone is insufficient.
Failed login monitoring includes anomaly detection.
Suspicious login, geolocation anomaly, or risky sign-in alerting is enabled.
B. Authorization, RBAC, ABAC, object-level access, and workflow control
Every sensitive endpoint validates whether the requester is allowed to view or modify the target object.
User profile, user permission, approval, audit, policy, risk, event, and report APIs enforce object-level authorization.
IDs from request parameters are never trusted by themselves.
Low-privileged users cannot retrieve other users’ or admin details by changing IDs.
Permission-changing APIs validate actor privileges on the server side.
Standard users cannot promote themselves or change privileged roles.
Admin APIs are not exposed with permissive settings.
Bulk permission updates verify actor privileges server-side.
“My approvals” and similar APIs derive the acting user from session/token, not from query parameters.
Approval-related fields such as reviewer_id, approved_by, status, and approver assignments are server-controlled.
Creator cannot approve their own record.
Maker-checker flow is enforced consistently across framework, policy, approval, vendor, and RFP flows.
Approval state changes happen only through verified workflow actions.
Session-scoped UI state (for example selected framework via `POST /api/frameworks/set-selected/`) resolves the acting user from the authenticated JWT and server session only; a client-supplied `userId` or `user_id` in the body cannot switch context to another user and is rejected when it does not match the authenticated actor.
Sensitive object access is logged with actor, time, old value, and new value.
All RBAC and object-level endpoints are re-tested for IDOR/BOLA after fixes.
C. Input validation, business validation, and safe error handling
All user input is validated on the backend, not only in UI.
All numeric fields have logical min/max range validation.
Negative values are rejected where not valid, including SLA thresholds and compliance values.
Financial, compliance, and score metrics are range validated.
Due dates cannot be before created date or unrealistically far in the future.
Workflow state fields cannot be altered directly by client input unless explicitly allowed.
RFP evaluation and similar business forms validate input types and ranges.
Invalid inputs return safe generic errors only.
Stack traces and verbose debug errors are hidden in production.
Production error handling is centralized and sanitized.
D. Frontend rendering, XSS, template safety, and browser-side trust
innerHTML, v-html, and equivalent unsafe rendering are removed for untrusted data.
User-controlled content is output-encoded before display.
Rich text content is sanitized with strict allow-listing if rich HTML must be supported.
Backend-generated HTML uses safe templating/escaping.
Integration outputs are sanitized before rendering.
localStorage or browser-stored values are treated as untrusted input.
Debug HTML/token test pages are removed from production.
DOM insertion uses safe binding or textContent by default.
Stored XSS risks in vendor/onboarding/invite/response flows are removed.


. API security, integrations, SSRF, redirect safety, and outbound control
Redirect URI validation is strict and exact-match based.
Open redirect risks in callbacks, invites, and integration flows are removed.
Base URLs and redirect targets are server-controlled or allow-listed.
Query string reflection is blocked or safely encoded.
Response headers never reflect raw user input.
Sensitive APIs use replay-resistant controls such as nonce/request signing where appropriate.
API governance for versioning and deprecation is documented.
REST API versioning is introduced where required.
Outbound URLs from client input are never fetched directly server-side.
Outbound destinations are allow-listed.
Internal/private IPs and metadata services are blocked.
Dangerous URL schemes like file://, ftp://, gopher:// are blocked.
DNS/IP resolution checks are performed before outbound requests where needed.
Egress filtering exists for backend services.
API abuse/anomaly monitoring is implemented.
API logs feed into alerting/SIEM.
Integrations sanitize all external inputs like file URLs, next links, project IDs, cloud IDs, and callback parameters.
H. Secrets, keys, cryptography, and secure configuration
No hardcoded secrets remain in frontend, backend, scripts, or config files.
No fallback weak session secret remains.
App fails safely when required secrets are missing.
All database, API, cloud, and third-party credentials are stored in environment variables or secret manager.
All exposed credentials are rotated.
Repository history is reviewed for leaked secrets.
Test users do not rely on hardcoded passwords.
Password history/reuse logic does not log sensitive hash material unsafely.
Data encryption uses modern authenticated encryption where possible.
AES-GCM or equivalent is preferred over CBC for new implementations.
Shared secret exposure risk is reduced.
Crypto choices align with regulatory/compliance requirements.
Key rotation and key lifecycle are documented and implemented.
JWT signing and cryptographic controls are reviewed for stronger asymmetric methods where required.
I. Infr