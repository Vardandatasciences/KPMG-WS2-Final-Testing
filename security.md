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