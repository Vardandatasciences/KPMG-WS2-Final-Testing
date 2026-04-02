# Security Test Cases — Cross-check (VAPT / Post-implementation)

Coverage: **TLS cipher hardening**, **CSP (`script-src`)**, **secure cookie flags** (`backend/settings.py` + production env), and deployment notes.

---

## 1. TLS / weak cipher suites (production / staging HTTPS endpoint)

**Issue addressed:** Disable weak cipher suites (e.g. AES-CBC with SHA-1 such as `AES128-SHA` / `AES256-SHA`); enforce TLS 1.2+ with AEAD (e.g. AES-GCM, ChaCha20-Poly1305).

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| TLS-01 | TLS 1.2 only offers strong ciphers | Run SSL Labs (or equivalent) on the public HTTPS hostname (e.g. `https://<your-domain>/`). Review **Cipher Suites** under TLS 1.2. | No suites flagged **WEAK** for CBC+SHA1; no `AES128-SHA` / `AES256-SHA` in the offered list. Prefer AES-GCM / ChaCha20-Poly1305. |
| TLS-02 | TLS 1.0 / 1.1 disabled | Same scan → **Protocols** section. | Only **TLS 1.2** and (if enabled) **TLS 1.3**; TLS 1.0 and 1.1 **not** offered. |
| TLS-03 | Weak cipher handshake fails | On a Linux/macOS shell with OpenSSL, against production host and port 443: `openssl s_client -connect <host>:443 -tls1_2 -cipher AES256-SHA` | Handshake **fails** (e.g. “no shared cipher” / connection error). |
| TLS-04 | Weak cipher handshake fails (128) | Same as TLS-03 with: `openssl s_client -connect <host>:443 -tls1_2 -cipher AES128-SHA` | Handshake **fails**. |
| TLS-05 | Strong cipher handshake succeeds | `openssl s_client -connect <host>:443 -tls1_2` (no bad cipher), or use `-cipher 'ECDHE:AESGCM'` if supported. | Handshake **succeeds**; certificate chain valid. |
| TLS-06 | Nginx config applied | On the server: `sudo nginx -t` then reload (`systemctl reload nginx` or `nginx -s reload`). | `nginx -t` reports **syntax ok**; no reload errors; site loads over HTTPS. |
| TLS-07 | App smoke after change | Browser: open main URL, login, open a few pages, API-heavy screen. | No SSL errors; functionality normal. |

**Note:** Local `http://127.0.0.1:8000` often has **no HTTPS**; run TLS-01–TLS-05 against the **same host** where users hit HTTPS (Nginx `listen 443 ssl`, load balancer, etc.).

---

## 2. Content Security Policy — script-src (API / app responses)

**Issue addressed:** Remove `'unsafe-inline'` and `'unsafe-eval'` from **`script-src`**; keep policy testable via response headers.

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| CSP-01 | CSP present on API JSON | DevTools → **Network** → select an API call (e.g. `GET /api/.../counts/`) → **Headers** → **Response Headers**. | Header **`Content-Security-Policy`** exists. |
| CSP-02 | No unsafe script directives | In that same header, read **`script-src`**. | Contains **`script-src 'self'`** (or `'self'` plus explicit **nonces/hashes** only). **Must not** contain **`unsafe-inline`** or **`unsafe-eval`**. |
| CSP-03 | CSP on HTML document | DevTools → **Network** → select the **document** request (Type `document`, first page load / `index.html`). | Same as CSP-01–CSP-02 for **`script-src`**. |
| CSP-04 | Inline script blocked | DevTools → **Console** on the app origin: append inline script programmatically (see snippet below). | Browser logs CSP violation / **Refused to execute inline script**; test flag **not** set. |
| CSP-05 | `eval` blocked | Console: `eval("2+2")` | **Refused** message (CSP blocks `unsafe-eval`); no successful `eval` execution. |
| CSP-06 | Style note (informational) | Read **`style-src`** in CSP. | May still include **`unsafe-inline`** for styles (separate from script finding); confirm **script** side is hardened per CSP-02. |
| CSP-07 | `connect-src` and API | Use app from frontend (e.g. `http://localhost:8080`) calling API on `http://127.0.0.1:8000`. | No CSP console error **Refused to connect** due to `connect-src`; API calls return expected status (e.g. 200). If blocked, **`connect-src`** must include the API origin. |
| CSP-08 | Regression smoke | Login, navigation, refresh, upload if applicable. | No blank screen; no unexpected CSP blocks in **Console** for critical flows. |

**Snippet for CSP-04 (run in browser console on the SPA origin):**

```javascript
const s = document.createElement('script');
s.text = "window.__csp_inline_test = true;";
document.head.appendChild(s);
window.__csp_inline_test;
```

**Expected:** CSP blocks execution; `window.__csp_inline_test` is **not** `true` (often `undefined`).

---

## 3. Insecure Cookie Storage (HttpOnly / Secure / SameSite)

**Issue addressed:** Ensure session/sensitive cookies are issued with `HttpOnly`, `Secure` (on HTTPS), and appropriate `SameSite`; avoid storing sensitive values directly in cookies.

**Implementation reference (this repo):**
- Django: `grc_backend/backend/settings.py` — `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_*`, HSTS-related `SECURE_*` (driven by env).
- Production env template: `grc_backend/.env.production` — sets `DJANGO_DEBUG=false`, `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`, `CSRF_COOKIE_SECURE=True`, `SESSION_COOKIE_SAMESITE=Lax`, etc.
- **Session cookie name:** `grc_sessionid` (use this in CK-01 / CK-04 instead of generic `sessionid`).
- **Deployment:** `load_dotenv()` loads **`.env`** by default. Ensure production either uses a `.env` file with the same variables, sets OS env vars, or copies/symlinks from `.env.production` — otherwise cookie flags will not match what you tested locally.

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| CK-01 | Session cookie has HttpOnly | DevTools → **Application** → **Cookies** → API origin after login. Find **`grc_sessionid`**. | **HttpOnly = true**; JS cannot read session ID from `document.cookie`. |
| CK-02 | Session cookie has Secure on HTTPS | Same as CK-01 on **HTTPS** (prod/staging). | **`grc_sessionid`**: **Secure = true**. |
| CK-03 | Cookie has SameSite set | DevTools cookie table for `grc_sessionid` and `csrftoken`. | **SameSite** = **Lax** (or Strict if you changed env). `None` only for explicit cross-site flows and must include **Secure**. |
| CK-04 | Session not visible from JS | Console: `document.cookie` after login. | **`grc_sessionid` does not appear** in the string (HttpOnly). |
| CK-05 | Set-Cookie on login response | **Network** → login (or first `Set-Cookie`) → **Response Headers** → `Set-Cookie`. | For **`grc_sessionid`**: `HttpOnly`, `Secure` (HTTPS), `SameSite=Lax` (or your configured value). |
| CK-06 | CSRF cookie vs scanner nuance | Inspect cookie **`csrftoken`**. | **`Secure=true`** on HTTPS. **HttpOnly** may be **false** by design (Vue/axios reads token from cookie for `X-CSRFToken`). If a scanner still flags `csrftoken` for no HttpOnly, track as **known exception** or refactor CSRF delivery (separate task). |
| CK-07 | `DJANGO_DEBUG` drives Secure defaults | Confirm production env has **`DJANGO_DEBUG=false`** (or `SESSION_COOKIE_SECURE=True` explicitly). | With HTTPS, session cookie is **Secure**; with `DEBUG` off, defaults assume production cookies unless env overrides. |
| CK-08 | HTTP endpoint does not leak Secure cookies | If both HTTP and HTTPS exist, use **HTTP** URL once. | **Secure** cookies not sent on plaintext HTTP; prefer **301** to HTTPS. |
| CK-09 | Cookie scope | Inspect `Domain` / `Path` on `Set-Cookie`. | Reasonable scope (e.g. path `/`, domain matches app). |
| CK-10 | Logout invalidates session | Logout → recheck cookies / call protected API. | Session ended; no access until login again. |
| CK-11 | Session identifier changes on login | Compare `grc_sessionid` value before vs after login. | Value changes (mitigates fixation where applicable). |
| CK-12 | No secrets in cookie values | Visual / base64 check only — do not log prod secrets. | Opaque session id only; no passwords/PII in cookie payload. |

**Localhost note (important):**
- On plain `http://localhost` or `http://127.0.0.1`, **`Secure` may be false or omitted** — that is expected without HTTPS.
- Run CK-02 / CK-05 / Secure checks on the **real HTTPS** URL (e.g. `https://riskavaire.vardaands.com` or staging).

---

## 4. Sensitive Data in Browser Storage (LocalStorage)

**Issue addressed:** Tokens and sensitive session data should not persist in `localStorage`; keep them in `sessionStorage` (tab lifetime) and avoid long-lived browser persistence.

**Why it was used earlier:** `localStorage` survives reload/restart and made “stay logged in” easier, but it is readable by JavaScript and therefore high-risk in XSS scenarios.

**Implementation reference (this repo):**
- `grc_frontend/src/services/authService.js` and `grc_frontend/tprm_frontend/src/services/authService.js`
- `grc_frontend/src/services/apiService.js`
- `grc_frontend/src/config/api.js`
- `grc_frontend/tprm_frontend/src/services/api.js`
- `grc_frontend/tprm_frontend/src/App.vue`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| LS-01 | Login stores tokens in sessionStorage only | Login, then DevTools → Application → Storage → inspect `sessionStorage` and `localStorage`. | `access_token` / `refresh_token` / `session_token` present in **sessionStorage**; absent from **localStorage**. |
| LS-02 | Legacy localStorage tokens are migrated/cleared | Before login, manually add `localStorage.access_token`; reload app. | Token is moved to `sessionStorage` (or cleared) and removed from localStorage. |
| LS-03 | API auth still works with sessionStorage token | After login, perform API actions (list pages, create/update action). | Requests include `Authorization: Bearer <token>` and return expected success codes. |
| LS-04 | Refresh flow writes refreshed tokens to sessionStorage | Force token refresh path (wait/trigger 401 then refresh). | New `access_token`/`refresh_token` values update in **sessionStorage**; no sensitive token in localStorage. |
| LS-05 | Logout clears sensitive browser storage | Logout and inspect both storages. | Sensitive keys (`session_token`, `access_token`, `refresh_token`, `current_user`) removed from sessionStorage and localStorage. |
| LS-06 | Browser restart/tab close clears sessionStorage tokens | Close tab/browser and reopen app. | User must re-authenticate (unless cookie/session mechanism still valid server-side); token keys are not persisted like localStorage. |
| LS-07 | No sensitive profile blob in localStorage | Inspect `localStorage` values after login. | No full user object/profile containing auth/session secrets; only minimal non-sensitive UI state remains. |
| LS-08 | Console check for localStorage token exposure | Console: `localStorage.getItem('access_token')`, `localStorage.getItem('refresh_token')`. | Returns `null` for sensitive auth tokens. |

**Note:** This control reduces persistence risk but does not replace XSS prevention; CSP + output encoding are still required.

---

## Quick sign-off checklist

- [ ] **TLS:** External scan shows no weak CBC/SHA1 script-related ciphers on HTTPS; OpenSSL weak-cipher tests fail.

- [ ] **CSP:** `script-src` has no `unsafe-inline` / `unsafe-eval` on both 
**document** and **sample API** responses.

- [ ] **CSP:** Console tests CSP-04 / CSP-05 behave as expected; app still works (CSP-08).

- [ ] **Cookies:** **`grc_sessionid`**: HttpOnly + Secure (on HTTPS) + SameSite; **`document.cookie`** does not expose session id.

- [ ] **Cookies:** Production env loaded (`DJANGO_DEBUG=false`, cookie vars applied on server — not only in a file that Django never reads).

- [ ] **Cookies (optional):** If report still flags **`csrftoken`** for HttpOnly, see CK-06 — acceptable until CSRF flow is refactored.

- [ ] **Browser Storage:** Sensitive auth/session data is no longer persisted in localStorage; sessionStorage-only behavior verified (LS-01 to LS-08).

---

## 5. Race Condition Attack — Duplicate user registration (email/username)

**Issue addressed:** Concurrent user-creation requests could bypass “already exists” checks and create duplicate `Users` records.  
**Fix expectation:** Server enforces **database-level uniqueness** (atomic under concurrency) and returns a safe duplicate error for the losing request.

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| RC-01 | Single request rejects duplicate username | Create user `username=A`, then try create again with same username (any email). | Second request fails with `400` and message like **Username already exists**. |
| RC-02 | Single request rejects duplicate email | Create user `email=a@x.com`, then try create again with same email (any username). | Second request fails with `400` and message like **Email already exists**. |
| RC-03 | Parallel requests cannot create duplicates (username) | In Burp Repeater: send **2+ concurrent** `POST /register/` requests with same username + different random other fields. | Exactly **1 succeeds**, others fail with duplicate error; DB has **1** user for that username. |
| RC-04 | Parallel requests cannot create duplicates (email) | Same as RC-03 but keep email same. | Exactly **1 succeeds**, others fail; DB has **1** user for that email. |
| RC-05 | Replay safety (same request body) | Capture a valid create-user request and replay it rapidly (10–50 times). | At most **1** user created; all replays fail with duplicate error; no server 500s. |
| RC-06 | Concurrency regression smoke (admin UI) | Create user via UI, then immediately attempt create same username/email again. | UI shows validation error; no duplicates created. |
| RC-07 | DB uniqueness is actually enabled (pre-req for RC-03/RC-04) | On server (repo root): run `python grc_backend/backfill_user_hashes.py` then `python grc_backend/backfill_user_hashes.py --enforce`. | Script reports columns exist + backfill done; enforce step succeeds (NOT NULL + UNIQUE). |
| RC-08 | Duplicate detection blocks constraint enforcement | Intentionally create duplicates in a non-prod DB (two users with same email/username) then run `python grc_backend/backfill_user_hashes.py --enforce`. | Script prints duplicates and **does not** enforce UNIQUE until duplicates are resolved. |

**Notes for verification:**
- Confirm via DB query or admin “user list” that duplicates are not present.
- If migration fails due to existing duplicates, remove/merge duplicates first, then re-run migrations.

**Burp parallel-send procedure (for RC-03/RC-04):**
- Capture the **admin create-user** request (typically `POST /register/`).
- Create 2–5 Repeater tabs with the same request.
- Keep **exact same** `username` and `email` in all tabs.
- Use Burp “Send group in parallel” (or equivalent) to fire simultaneously.
- Validate outcomes: **1 success**, remaining responses are `400` with duplicate message; confirm only **1** user exists in UI/DB.

---

## 6. Access Token in URL — Google SSO callback hardening

**Issue addressed:** JWT/access tokens must never be transmitted in URL query/fragment during Google OAuth callback.

**Implementation reference (this repo):**
- Backend callback redirect: `grc_backend/grc/authentication.py` (`google_oauth_callback`)
- Backend one-time payload endpoint: `grc_backend/grc/authentication.py` (`google_oauth_callback_payload`)
- Frontend callback handling: `grc_frontend/src/components/Login/GoogleOAuthCallback.vue`
- Frontend OAuth service: `grc_frontend/src/services/authService.js`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| OAUTH-URL-01 | No token in frontend callback URL | Execute Google SSO login and stop on frontend callback page load (`/auth/google/callback`). Inspect browser address bar + DevTools network redirect chain. | URL does **not** contain `access_token`, `refresh_token`, `id_token`, `token`, `session_token` in query or fragment. |
| OAUTH-URL-02 | Backend redirect is token-free | Capture response for `/api/google/oauth-callback/` in Network tab. | `Location` header points to `/auth/google/callback` only (no token-bearing params). |
| OAUTH-URL-03 | Frontend URL scrubbing works defensively | Manually open `/auth/google/callback?access_token=test123&refresh_token=test456` and `/auth/google/callback#access_token=test123`. | App removes token-like params/hash from visible URL immediately; no token remains in address bar/history entry. |
| OAUTH-URL-04 | Callback payload fetched from server-side session only | On callback load, inspect API call to `/api/google-oauth/callback-payload/`. | Response returns payload once; second call returns not found/already consumed behavior. |
| OAUTH-URL-05 | No token in frontend logs | Run callback flow and inspect browser console output. | No console line prints raw access/refresh token values. |
| OAUTH-URL-06 | No token leak via Referer on follow-up requests | During callback flow, inspect request headers for subsequent API/navigation requests. | `Referer` never contains token-bearing query/fragment values. |
| OAUTH-URL-07 | Existing login behavior remains intact | Complete Google SSO end-to-end (including consent-required and consent-already-accepted paths). | User is authenticated, routed correctly, and receives expected session data without token-in-URL usage. |

---

## 6A. Session/Auth Token in URL — Integration OAuth callback hardening (Jira/BambooHR)

**Issue addressed:** OAuth access/session tokens must never be present in integration callback URLs (`/integration/jira`, `/integration/bamboohr`).

**Implementation reference (this repo):**
- `grc_backend/grc/routes/Integrations/Bamboohr/flask_oauth_server.py`
- `grc_backend/grc/routes/Integrations/server.js`
- `grc_frontend/src/components/Integrations/BambooHR/bamboohr.vue`
- `grc_frontend/src/components/Integrations/JIRA/server.js`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| INT-URL-01 | BambooHR callback URL is token-free | Complete BambooHR OAuth and inspect final browser URL + network redirects. | URL contains only non-sensitive parameters (for example `success=true`, `subdomain`, `user_id`); no `token`, `access_token`, `refresh_token`, `session_token`, `id_token`. |
| INT-URL-02 | Jira callback URL is token-free | Complete Jira OAuth and inspect redirect to `/integration/jira`. | Redirect has no token-bearing query parameter or fragment. |
| INT-URL-03 | Frontend rejects tokenized BambooHR URLs | Manually open `/integration/bamboohr?token=test123` and `/integration/bamboohr?access_token=test123`. | UI blocks flow with safe error and immediately removes token-like query params from visible URL. |
| INT-URL-04 | No auth token appears in referer logs | During integration callback flow, inspect subsequent API request headers in browser DevTools. | `Referer` header does not include any token-bearing query string values. |
| INT-URL-05 | Backend integration still works after hardening | After successful OAuth callback, load integration data (BambooHR employees / Jira projects). | Integration loads from backend-stored connection and functions normally without URL token transport. |

---

## 7. Stored XSS via public vendor portal (RFP responses)

**Issue addressed:** Vendor-submitted rich-text responses in the public RFP vendor portal were stored and later rendered inside the authenticated TPRM UI using `v-html` without proper sanitization, allowing Stored XSS from an unauthenticated entry point.

**Implementation reference (this repo):**
- Backend vendor submission endpoint: `grc_backend/tprm_backend/rfp/views_rfp_responses.py` (`create_rfp_response`)
- Backend server-side HTML neutralization: `sanitize_html_value` / `sanitize_response_documents` in the same file
- Frontend proposal evaluation view (where internal users read vendor proposals): `grc_frontend/tprm_frontend/src/views/rfp-approval/ProposalEvaluation.vue` (`sanitizeVendorHtml` and `v-html` usage)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| XSS-RFP-01 | Baseline reproduction no longer works | Use the vendor invite flow to generate a public vendor portal URL. In the vendor portal, answer the questionnaire and, via browser devtools or Burp, inject a payload like `<img src=x onerror="alert('xss1')">` into a rich-text response field (so it ends up in `htmlContent`). Submit, then as an internal evaluator open the same proposal in `ProposalEvaluation` (RFP evaluation UI). | The proposal loads correctly, **no alert box or script executes**; the payload appears as harmless content (image placeholder or escaped text) or is stripped. |
| XSS-RFP-02 | Script tag is fully neutralized | Repeat XSS-RFP-01 but inject `<script>alert('xss2')</script>` in a response. | The `<script>` tag is stripped server-side and/or on render; **no JavaScript executes**, and no browser console CSP/XSS errors except expected sanitization-related logs. |
| XSS-RFP-03 | Event handler attributes are removed | Inject markup like `<a href="#" onclick="alert('xss3')">Click me</a>` in a vendor response. | Link renders visually, but clicking it **does not trigger** `alert` or any inline handler; `onclick` is removed in the DOM. |
| XSS-RFP-04 | `javascript:` URLs are blocked | Inject `<a href="javascript:alert('xss4')">JS link</a>` into a response. | Rendered link **does not contain** a `javascript:` URL (attribute removed or replaced); clicking the link does not execute JavaScript. |
| XSS-RFP-05 | Non-HTML text is preserved | Submit a response that contains characters like `<` and `>` but is intended as plain text (for example, `1 < 2 && 3 > 1`). | In the evaluation view, the text is readable and not interpreted as HTML/JS; no XSS is triggered. |
| XSS-RFP-06 | Existing stored responses are safe on re-open | Using an environment that previously had malicious `htmlContent` stored (before the fix), open historical proposals in the `ProposalEvaluation` view. | Legacy proposals render without executing any stored XSS payload; previously stored `<script>`, event handlers, or `javascript:` URLs are stripped or harmless. |
| XSS-RFP-07 | Regression guard on vendor portal submission | From the vendor portal, submit normal rich-text content (bold, lists, paragraphs) without any scripts. | Content still renders with basic formatting for evaluators; no functional regression to the vendor workflow while XSS protections remain in place. |

**Notes for verification:**
- Run tests on both a **fresh** proposal (submitted after deploying the fix) and, if available, an environment with **existing** stored proposals to ensure the render-time sanitization protects old data as well.
- Always test using accounts with evaluator/reviewer/admin roles, since those are the victims in a Stored XSS scenario.
- Keep browser DevTools console open during tests to catch any unexpected CSP violations or JavaScript errors that might indicate broken rendering logic.

### 7A. Stored XSS via RFI vendor portal (RFI responses)

**Issue addressed:** RFI vendor responses submitted via the public RFI portal were stored in `RFIResponse.response_documents` and rendered for internal users; `documents` could carry script payloads if not neutralized.

**Implementation reference (this repo):**
- Backend RFI response endpoint: `grc_backend/tprm_backend/rfp/rfi/views_invitations.py` (`create_rfi_response`, `_sanitize_rfi_response_documents`)
- Frontend RFI responses view: `grc_frontend/tprm_frontend/src/views/rfi/RFIResponses.vue` (renders only plain fields; no `v-html`)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| XSS-RFI-01 | Baseline RFI XSS no longer works | Use an RFI invitation link to open the **RFIVendorPortal**, submit a response with `documents` or long-text fields containing `<img src=x onerror="alert('xss-rfi')">`. Then open the corresponding response in the internal `RFIResponses` UI. | Response details page loads with no alert/JS execution; UI shows data or document links normally. |
| XSS-RFI-02 | Script tags in documents are neutralized | Submit an RFI response where document metadata or long-text includes `<script>alert('rfi2')</script>`. | Stored data does not execute when listed or viewed; no script runs, and logs show no XSS. |
| XSS-RFI-03 | Existing RFI responses remain safe | If you have pre‑fix RFI responses with malicious HTML, load them in `RFIResponses`. | No stored XSS executes; any script-like content is inert. |

### 7B. Stored / Reflected XSS via shared `v-html` components (TPRM & core app)

**Issue addressed:** Several shared components used `v-html` to render text from APIs/user content (tables, audit reports, search results, tree labels, popup icons), which could be abused for XSS if not sanitized/encoded.

**Implementation reference (this repo):**
- Collapsible sections table: `grc_frontend/src/components/CollapsibleTable.vue` (`sanitizeCellHtml` + `v-html="sanitizeCellHtml(...)"`)
- Audit report viewer: `grc_frontend/src/components/Auditor/AuditReportView.vue` (`sanitizeReportHtml(formatReportContent(...))`)
- Popup modals (icons):  
  - `grc_frontend/src/modules/popus/PopupModal.vue` (`sanitizeIcon`)  
  - `grc_frontend/src/modules/popup/PopupModal.vue` (`sanitizeIcon`)  
  - `grc_frontend/tprm_frontend/src/popup/PopupModal.vue` (`sanitizeIcon`)
- Policy tree highlighting: `grc_frontend/src/components/Compliance/OrganizationalControls.vue` (`highlightText` now HTML‑encodes base text first)
- Global search card: `grc_frontend/tprm_frontend/src/components_globalsearch/SearchResultCard_TPRM.vue` (`highlightText` HTML‑encodes then adds safe `<mark>`)
- Vendor sidebar layout: `grc_frontend/tprm_frontend/src/components/VendorLayout.vue` (`sanitizeIcon` for sidebar SVG strings)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| XSS-COMP-01 | Collapsible table cell HTML neutralization | In any screen using `CollapsibleTable`, inject values like `<img src=x onerror="alert('tbl1')">` or `<script>alert('tbl2')</script>` into `criticality` / `priority` / `status` fields via API or test data. | Table renders without executing JS; the content is either stripped or shown harmlessly. |
| XSS-COMP-02 | Audit report content cannot execute script | Create or edit an audit report so `Report` contains `<script>alert('audit1')</script>` or an `<img onerror>` payload. Open `AuditReportView`. | The “Report Details” section shows no alerts/popups; script tags/handlers are stripped; layout still renders. |
| XSS-COMP-03 | Popup icons safe from injection | Programmatically trigger a popup (core app and TPRM) with `icon` deliberately set to `<img src=x onerror="alert('icon1')">`. | Popup renders without JS execution; icon appears as plain content or is safely stripped. |
| XSS-COMP-04 | Policy tree highlight does not inject HTML | In `OrganizationalControls`, ensure some policy ID/name contains `<b>TEST</b>` or `"><img src=x onerror=alert('pol1')>`. Search for a term that matches inside that string. | Highlighting appears, but no new HTML elements are injected beyond `<mark>`; no script executes. |
| XSS-COMP-05 | Global search snippet/title safe | Index a record whose `title` or `snippet` includes `<script>alert('search1')</script>` or `<img src=x onerror="alert('search2')">`. Search so it appears in `SearchResultCard_TPRM`. | Card renders text with highlight only; no script or inline handler runs. |
| XSS-COMP-06 | Vendor sidebar icon strings are safe | Temporarily modify a vendor navigation item’s `icon` in `VendorLayout` to `<img src=x onerror="alert('nav1')">` and reload TPRM vendor portal. | Sidebar loads normally with sanitized icon; no alert or JS execution. |


## 7. Denial of Service — `/api/incidents/export/` payload hardening

**Issue addressed:** Untrusted export payloads (especially `Description` content) can trigger heavy template/render behavior or malformed processing in PDF export and lead to resource exhaustion.

**Implementation reference (this repo):**
- Backend export endpoint: `grc_backend/grc/routes/Incident/incident_views.py` (`export_incidents`, `export_audit_findings`)
- Export utility path: `grc_backend/grc/routes/Global/s3_fucntions.py`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| DOS-EXP-01 | Baseline export still works | From incident dashboard export normal dataset as PDF. | `200` success and valid downloadable file URL. |
| DOS-EXP-02 | Reject invalid JSON in `data` | Send `POST /api/incidents/export/` with `data` set to broken JSON string. | `400` with validation error (no server crash / no hang). |
| DOS-EXP-03 | Reject oversized payload | Send `data` > 1MB (e.g., repeated long description field). | `400` with payload-size validation error; request completes quickly. |
| DOS-EXP-04 | Reject excessive record count | Send `data` array > 2000 records in one request. | `400` with record-limit validation error. |
| DOS-EXP-05 | Reject deep nesting payload | Send nested JSON payload depth > 6 in `data` or `options`. | `400` with nested-depth validation error. |
| DOS-EXP-06 | Template token neutralization | In `Description`, include tokens like `{{7*7}}`, `{% for i in range(9999999) %}x{% endfor %}` and export PDF. | Request returns success/failure gracefully; service remains responsive; output treats payload as plain text (no loop execution). |
| DOS-EXP-07 | Concurrency resilience | Fire 20+ parallel export requests with mixed normal + malicious payloads (Burp Intruder/Repeater group). | No worker crash; malicious requests return `400`; normal requests continue to succeed. |
| DOS-EXP-08 | Error handling does not leak internals | Trigger a forced export failure (unsupported shape/type). | Error response is bounded and safe (no stack trace, no secrets). |
| DOS-EXP-09 | Audit findings export protected too | Repeat DOS-EXP-02..DOS-EXP-06 on `/audit-findings/export/` endpoint used by UI. | Same defensive behavior (`400` on invalid payloads, no service unavailability). |
| DOS-EXP-10 | Performance guardrail | Measure response time for malicious payload attempts under load. | Requests terminate within acceptable SLA and do not cause sustained CPU/memory spike. |
| DOS-EXP-11 | Compliance export hardening parity | Repeat DOS-EXP-02..DOS-EXP-06 against compliance export APIs (`/api/export/compliances/...` and compliance management export endpoints). | Invalid/malicious payloads are rejected or safely processed; service remains responsive. |
| DOS-EXP-12 | Risk export hardening parity | Repeat DOS-EXP-02..DOS-EXP-06 against risk export API (`/api/risk-register/export/`). | Invalid/malicious payloads are rejected or safely processed; normal exports still succeed. |




---

## 8. OTP Bypass / 2FA Bypass — Forgot Password flow hardening

**Issue addressed:** OTP verification must be enforced only on backend state. Frontend/UI state or tampered API responses must not allow password reset.

**Implementation reference (this repo):**
- Backend reset OTP flow: `grc_backend/grc/views.py` (`send_otp`, `verify_otp`, `reset_password`, `update_password`)
- Frontend flow caller: `grc_frontend/src/components/Login/ForgotPassword.vue`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| OTP-01 | Invalid OTP cannot proceed | Start forgot password, submit wrong OTP in `/api/verify-otp/`. | API returns `400` with invalid OTP message; password reset is blocked. |
| OTP-02 | Response tampering does not bypass backend | Intercept `/api/verify-otp/` wrong OTP response and modify body to `{ "success": true }`; then continue to `/api/reset-password/`. | `/api/reset-password/` still returns `400` (`OTP verification required...` or equivalent). |
| OTP-03 | OTP challenge bound to same session | Request OTP in Browser A, then use same email+OTP from Browser B/new incognito for `/api/verify-otp/` or `/api/reset-password/`. | Verification/reset fails due to missing server-side challenge in that session. |
| OTP-04 | Reset allowed only after server-side verification | Call `/api/reset-password/` directly without prior successful `/api/verify-otp/`. | `400` rejection; password not changed in DB. |
| OTP-05 | OTP expiry enforced | Request OTP, wait >5 minutes, then call `/api/verify-otp/`. | `400` with expiry message; must request new OTP. |
| OTP-06 | Verify window expiry enforced | Verify OTP successfully, wait >15 minutes, then call `/api/reset-password/`. | `400` with verification expired message; must restart OTP flow. |
| OTP-07 | One-time challenge replay blocked | Verify OTP and reset password once; replay same `/api/reset-password/` request (same session and email). | Replay fails (`challenge already used` / verification required). |
| OTP-08 | Email mismatch blocked | Verify OTP for `email_A`, attempt reset with `email_B`. | `400` (`Email does not match...`); no password change. |
| OTP-09 | Rate limit on OTP send | Trigger `/api/send-otp/` repeatedly (> configured threshold) within 5 minutes from same IP/email. | API returns `429`; no unlimited OTP sends. |
| OTP-10 | Rate limit on OTP verify brute force | Submit multiple invalid OTPs rapidly for same email/session. | API returns `429` after threshold; brute-force attempts throttled. |
| OTP-11 | Rate limit on reset endpoint abuse | Call `/api/reset-password/` repeatedly without valid verified challenge. | API returns `429` after threshold. |
| OTP-12 | Regression smoke (valid flow) | Normal forgot-password journey: send OTP → verify correct OTP → reset with compliant new password → login with new password. | End-to-end succeeds; old password fails; new password works. |

---

## 9. IDOR — User details disclosure (email / permissions)

**Issue addressed:** Insecure Direct Object Reference (IDOR) allowed attackers to disclose other users’ **email addresses** and **permission details** by manipulating user identifiers.

**Fix expectation:** Object-level authorization is enforced consistently:
- A user can only access **their own** user-scoped resources.
- Only **system admins** can access/modify other users’ sensitive data (e.g., list all users, update RBAC).
- Public forgot-password endpoints do **not** disclose whether a user exists or reveal full emails.

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| IDOR-EMAIL-01 | Forgot-password lookup does not disclose email | Call `GET /api/get-user-email/?username=<valid>` and `GET /api/get-user-email/?username=<invalid>` (or POST). | Both responses are **generic**; response does **not** include `full_email` and does not confirm user existence. |
| IDOR-EMAIL-02 | User ID enumeration blocked (no email leak) | Call `GET /api/get-user-email/?username=1`, then `2`, `3`… | Responses remain **generic**; no other users’ emails are returned. |
| IDOR-PERM-01 | Permission enumeration blocked (non-admin) | Login as normal user A. Call the user-permissions-by-id endpoint with user B’s id (the one mapping to `get_user_permissions(request, user_id)`). | Returns **403 Forbidden**; does not return user B permissions. |
| IDOR-PERM-02 | Self permission access allowed | Login as user A. Call the user-permissions-by-id endpoint with user A’s id. | Returns `200` and permissions for user A only. |
| IDOR-USERLIST-01 | Listing users requires admin | Login as normal user A. Call `GET /api/users/`. | Returns **403 Forbidden** (or 401 if missing auth); does not return user list. |
| IDOR-USERLIST-02 | Admin can list users | Login as system admin. Call `GET /api/users/`. | Returns `200` with user list. |
| IDOR-RBAC-UPDATE-01 | Updating user permissions requires admin | Login as normal user A. Call the RBAC-update endpoint (mapping to `update_user_permissions(request, user_id)`) for user B. | Returns **403 Forbidden**; no permission change occurs. |
| IDOR-RBAC-UPDATE-02 | Admin can update permissions | Login as system admin. Repeat IDOR-RBAC-UPDATE-01. | Returns `200` and permissions updated as intended. |

| IDOR-FRAMEWORK-01 | Framework-level guard blocks any `<user_id>` path tampering | Login as normal user A. Pick any endpoint shaped like `/api/.../<user_id>/...` (profile, approvals, tasks, exports). Replace `<user_id>` with user B’s id. | Returns **403** consistently across modules (unless endpoint is explicitly public/token-based). |

---

## 10. Invalid input validation — Evidence URL (`aws-file_link`) allow-list (iframe/link injection)

**Issue addressed:** The application accepted a user-controlled URL parameter (e.g. `aws-file_link`) and later rendered it inside the application (observed as embedded/preview content). By replacing the URL with an attacker-controlled external URL, the app would load attacker content inside an iframe (or equivalent embedded viewer), enabling phishing/content spoofing.

**Fix expectation (framework-level):**
- Backend **rejects** any evidence URL not on a strict allow-list (trusted storage domains only, HTTPS only by default).
- Backend never stores attacker-supplied evidence URLs; it stores only trusted storage URLs/identifiers derived from upload results.
- CSP `frame-src` only allows **trusted domains** (defense in depth).

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| EVI-01 | Submit assessment rejects external evidence URL | Reproduce the Burp flow: upload a document, then on assessment submit replace `aws-file_link` with `https://attacker.example/poc.html`. | API returns **400** with generic error (e.g. “Invalid evidence URL”); record is **not** stored/updated. |
| EVI-02 | Submit assessment allows trusted S3/CloudFront URL | Repeat flow but keep the S3/CloudFront URL returned by upload response. | API returns **200** (or success response); evidence is stored and available. |
| EVI-03 | Host allow-list enforced (suffix match) | Try evidence URL like `https://evil-amazonaws.com/x` (looks similar but different domain). | **400** rejection (host not in allow-list). |
| EVI-04 | Scheme enforcement | Try `http://<trusted-host>/...` where `<trusted-host>` is not explicitly allow-listed for HTTP. | **400** rejection (“only https URLs allowed”). |
| EVI-05 | Linked evidence placeholder unaffected | Use a linked-evidence item (URL like `#linked-event-<id>`). | UI continues to work; backend accepts placeholder where applicable (no network fetch). |
| EVI-06 | UI does not render blocked evidence link (defense-in-depth) | If a legacy record already contains an external URL (from pre-fix data), open the workflow screen that lists evidence. | UI shows “Blocked untrusted evidence URL” (or no link), and does **not** embed/load it. |
| EVI-07 | CSP frame-src blocks untrusted domains | In browser DevTools, attempt to programmatically create an iframe to `https://attacker.example`. | Browser blocks with a CSP violation; untrusted iframe does not load. |

---

## 11. CSV Injection — export formula neutralization

**Issue addressed:** User-controlled values exported to CSV can be interpreted as spreadsheet formulas when cells begin with `=`, `+`, `-`, or `@`.

**Fix expectation:** All CSV export paths sanitize cells by prefixing dangerous leading characters with a single quote (`'`), so spreadsheet apps render text instead of executing formulas.

**Implementation reference (this repo):**
- Shared sanitizer: `grc_backend/grc/utils/csv_security.py`
- Incident/global CSV exporter path: `grc_backend/grc/routes/Global/s3_fucntions.py` (`export_to_csv`)
- Additional CSV services: `grc_backend/grc/routes/Global/export_service1.py`, `grc_backend/grc/routes/Global/export_service_compliance.py`
- Direct risk CSV responses: `grc_backend/grc/routes/Risk/risk_views.py`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| CSV-01 | Incident title starting with `=` is neutralized | Create incident title `=2+5`, export incidents as CSV, open in Excel/Sheets. | Cell value is shown as literal text (for example `'=2+5`); no formula execution/result `7`. |
| CSV-02 | Incident title starting with `+` is neutralized | Title `+SUM(1,2)` then CSV export. | Rendered as text; no evaluation to `3`. |
| CSV-03 | Incident title starting with `-` is neutralized | Title `-10+5` then CSV export. | Rendered as text; no expression evaluation. |
| CSV-04 | Incident title starting with `@` is neutralized | Title `@SUM(1,1)` then CSV export. | Rendered as text; no formula execution. |
| CSV-05 | Leading space does not bypass sanitizer | Title ` =2+2` (space then formula) and export CSV. | Value is treated safely as text in target spreadsheet policy; no executable formula is run. |
| CSV-06 | Normal values remain unchanged | Title `Quarterly incident review` and export CSV. | Value remains identical (no extra leading quote added unnecessarily). |
| CSV-07 | Multi-column payload is sanitized consistently | Populate other user-controlled fields (description, owner, comments) with formula-leading values and export CSV. | Every dangerous cell is neutralized in all exported columns. |
| CSV-08 | Risk register CSV path also sanitized | Export risk register/compliance management CSV with formula-leading values in user-controlled fields. | Dangerous cells are prefixed and rendered as text. |
| CSV-09 | JSON/PDF/XLSX exports unaffected | Export same dataset in JSON/PDF/XLSX. | Non-CSV exports still succeed and format behavior remains unchanged. |
| CSV-10 | Regression under load | Export large incident dataset containing mixed normal + formula-like values. | Export completes successfully; sanitized cells remain safe in output. |
| CSV-11 | TPRM workflow/vendor CSV exports sanitized | In TPRM modules (All Approvals, Vendor Lifecycle, Vendor Selection, Vendor Risk, URL Generation), include values beginning with `=`, `+`, `-`, `@` and export CSV. | Exported cells are neutralized as text across all TPRM CSV downloads. |
| CSV-12 | TPRM backend CSV fallbacks sanitized | Trigger backend CSV fallbacks (vendor dashboard CSV fallback, management risks CSV fallback) with formula-leading values. | Dangerous cells are prefixed and do not execute when opened in spreadsheet apps. |

### CSV Injection execution checklist (QA sign-off)

- [ ] **Seed payloads:** Create/update test records using these exact leading values in user-editable fields: `=2+5`, `+SUM(1,2)`, `-10+5`, `@SUM(1,1)`.
- [ ] **GRC incidents CSV:** Export incidents from incident dashboard and confirm dangerous cells are rendered as text (not evaluated).
- [ ] **GRC risk/compliance CSV:** Export risk register and compliance CSV endpoints and confirm no formula execution.
- [ ] **GRC frontend CSV exports:** Verify `EventsDashboard` and `AcknowledgementReport` CSV downloads neutralize dangerous leading characters.
- [ ] **TPRM frontend CSV exports:** Verify All Approvals, Vendor Lifecycle, Vendor Selection, Phase4 URL Generation, and Vendor Risk CSVs are neutralized.
- [ ] **TPRM backend CSV fallbacks:** Verify management/vendor-dashboard CSV fallback responses also neutralize dangerous values.
- [ ] **Safe data regression:** Export normal text-only data and confirm no unnecessary data corruption.
- [ ] **Cross-client open test:** Open downloaded CSV in Excel and Google Sheets; ensure values remain plain text in both.
- [ ] **No functional breakage:** Confirm JSON/PDF/XLSX exports still work where available.
- [ ] **Evidence capture:** Attach screenshots of source input + exported cell view for each module tested.

---

## 12. Weak JWT Algorithm (HS256) -> RS256 hardening

**Issue addressed:** JWT signing/verification used symmetric `HS256`. If shared secret is weak/leaked, attackers can forge valid tokens.  
**Fix expectation:** Use asymmetric signing (`RS256`), private key for signing only, public key for verification, and strict claim validation (`iss`, `aud`, `exp`).

**Implementation reference (this repo):**
- `grc_backend/backend/settings.py`
- `grc_backend/grc/jwt_auth.py`
- `grc_backend/grc/authentication.py`
- `grc_backend/grc/tenant_middleware.py`
- `grc_backend/grc/rbac/decorators.py`
- `grc_backend/tprm_backend/core/tenant_middleware.py`
- `grc_backend/tprm_backend/mfa_auth/jwt_service.py`
- `grc_backend/tprm_backend/config/settings.py`
- `grc_backend/tprm_backend/vendor_guard_hub/settings.py`
- `grc_backend/tprm_backend/tprm_project/settings.py`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| JWT-ALG-01 | Tokens are issued with RS256 | Login and decode JWT header (`jwt.io` or local decode script without secret). | Header `alg` is `RS256` (not `HS256`). |
| JWT-ALG-02 | Server rejects HS256 token | Forge or reuse an HS256 token signed with old shared secret and call protected API. | API returns `401` / invalid token; no access granted. |
| JWT-ALG-03 | Server accepts valid RS256 token only | Use normal login-issued token and call protected API endpoint. | API returns `200` for authorized user. |
| JWT-ALG-04 | Issuer validation enforced | Use token with incorrect/missing `iss` claim. | API returns `401` / invalid issuer. |
| JWT-ALG-05 | Audience validation enforced | Use token with incorrect/missing `aud` claim. | API returns `401` / invalid audience. |
| JWT-ALG-06 | Expired token blocked | Use token with past `exp` claim. | API returns `401` / token expired. |
| JWT-ALG-07 | Wrong key pair fails verification | Sign token with a different private key than configured public key pair. | API returns `401`; signature verification fails. |
| JWT-ALG-08 | Tenant extraction still works with RS256 | Call tenant-scoped endpoint with valid RS256 token containing `tenant_id`. | Tenant context resolves correctly; authorized access works. |
| JWT-ALG-09 | RBAC path still works with RS256 | Access RBAC-protected endpoint with valid RS256 token. | Permission checks continue to work; correct `200/403` behavior. |
| JWT-ALG-10 | MFA token refresh still works | Login via MFA path and trigger refresh endpoint. | New access token issued successfully with `RS256`. |
| JWT-ALG-11 | Key material is not hardcoded in code | Review settings/env usage and deployment env vars. | Private/public keys come from environment/secret store, not plaintext code constants. |
| JWT-ALG-12 | Rotation readiness | Replace JWT key pair in non-prod and restart service. Validate new tokens; old tokens behavior as per policy. | New tokens validate; rotation process is repeatable and documented. |

### Weak JWT execution checklist (QA sign-off)

- [ ] Configure `JWT_ALGORITHM=RS256`, `JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`, `JWT_ISSUER`, `JWT_AUDIENCE` in runtime environment.
- [ ] Login and verify new token header has `alg=RS256`.
- [ ] Confirm protected endpoints reject crafted/legacy `HS256` tokens.
- [ ] Confirm issuer/audience/expiry validation errors are enforced (`401`) with tampered claims.
- [ ] Confirm core auth flows work (standard login, tenant APIs, RBAC APIs, MFA refresh).
- [ ] Confirm no private key is exposed in logs, response payloads, frontend storage, or repository.

---

## 13. CORS Misconfiguration (Wildcard + Credentials) hardening

**Issue addressed:** Cross-origin policy allowed wildcard/dynamic origin behavior while credentialed requests were enabled, which can expose authenticated responses to untrusted origins.  
**Fix expectation:** Only explicit trusted origins receive CORS headers; no wildcard `Access-Control-Allow-Origin` when credentials are enabled.

**Implementation reference (this repo):**
- `grc_backend/backend/settings.py`
- `grc_backend/grc/middleware.py`
- `grc_backend/tprm_backend/tprm_project/settings.py`
- `grc_frontend/tprm_frontend/nginx.conf`
- `grc_frontend/tprm_frontend/nginx.docker.conf`
- `grc_frontend/tprm_frontend/express-server.js`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| CORS-01 | Wildcard header is not returned | Call any API endpoint and inspect response headers. | `Access-Control-Allow-Origin` is never `*` for API responses. |
| CORS-02 | Untrusted origin is blocked | In Burp/Proxy Repeater, add `Origin: https://evil.example` to a protected API request. | Response does not include `Access-Control-Allow-Origin: https://evil.example`; browser blocks cross-origin read. |
| CORS-03 | Trusted origin is allowed | Send same request with a known allowed origin (for example the deployed frontend domain). | Response includes that exact allowed origin in `Access-Control-Allow-Origin`. |
| CORS-04 | Credentials policy is consistent | With `withCredentials=true` from frontend, call authenticated API from trusted origin. | Response includes `Access-Control-Allow-Credentials: true` and succeeds for valid session/JWT. |
| CORS-05 | Preflight from untrusted origin is denied | Send `OPTIONS` with `Origin: https://evil.example` and `Access-Control-Request-Method: POST`. | Preflight response does not grant cross-origin access to untrusted origin. |
| CORS-06 | Preflight from trusted origin succeeds | Send `OPTIONS` with trusted `Origin` and valid requested method/headers. | Preflight includes expected CORS allow headers and browser proceeds with actual request. |
| CORS-07 | Origin reflection is not unconditional | Repeat CORS requests with multiple random origins in Burp. | Server does not blindly mirror arbitrary `Origin` values. |
| CORS-08 | Proxy layer does not override backend CORS | Hit API through Nginx/Express route and inspect headers. | No additional wildcard CORS header from proxy; backend CORS policy remains authoritative. |
| CORS-09 | Non-browser clients still work | Call API with Postman/curl without `Origin` header. | API behavior unchanged; auth/business responses continue to work. |
| CORS-10 | Regression check for login/session flows | Login from trusted frontend and access core modules (GRC + TPRM) requiring auth. | No functional break in authenticated flows after CORS hardening. |

### CORS hardening execution checklist (QA sign-off)

- [ ] Confirm no API response returns `Access-Control-Allow-Origin: *`.
- [ ] Confirm untrusted origins do not get CORS allow headers (Burp/browser verification).
- [ ] Confirm trusted origins still work for normal frontend operations.
- [ ] Confirm credentialed requests (`cookies`/`Authorization`) work only for trusted origins.
- [ ] Confirm preflight behavior is correct for both trusted and untrusted origins.
- [ ] Confirm proxy deployments (Nginx/Express) do not reintroduce wildcard CORS headers.

---

## 10. HTML Injection — Vendor invitation custom message (RFP / RFI)

**Issue addressed:** The free-text **custom message** field in RFP/RFI vendor invitations was injected directly into rich HTML email bodies, allowing testers to include raw HTML tags (`<b>`, `<i>`, `<a>`, `<img>`, etc.) that the email client rendered. This enabled content spoofing and phishing-style manipulation of the invitation email layout and links.

**Implementation reference (this repo):**
- RFP invitation HTML builder: `grc_backend/tprm_backend/rfp/email_templates.py` (`generate_rich_html_email`)
- RFI invitation HTML builder: `grc_backend/tprm_backend/rfp/rfi/email_templates.py` (`generate_rfi_rich_html_email`)
- Legacy RFP HTML builder (kept for safety): `grc_backend/tprm_backend/rfp_old/email_templates.py`
- RFP invitation persistence: `grc_backend/tprm_backend/rfp/models.py` (`VendorInvitation.custom_message`)
- RFI invitation persistence: `grc_backend/tprm_backend/rfp/rfi/models.py` (`RFIVendorInvitation.custom_message`)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| HTML-INV-01 | Baseline RFP invite still works with plain text | In the RFP Workflow module, go to **URL Generation / Vendor Invitation**, leave **Custom Message** empty or enter `Welcome to our RFP.` and send invitations. Inspect received email in a common client (e.g. Outlook, Gmail). | Email renders as the designed HTML template; custom message appears as plain paragraph text, no layout issues or errors. |
| HTML-INV-02 | HTML tags in custom message are rendered as text, not HTML (RFP) | In the same screen, set Custom Message to `Please review <b>carefully</b> and visit <a href="https://attacker.test">this link</a>.` Send the invite and open the received email. | The string `<b>carefully</b>` and the `<a ...>` markup are shown literally (escaped) in the **Additional Message** section; they do **not** bold the text or create a clickable hyperlink. |
| HTML-INV-03 | Image tag is neutralized (RFP) | Set Custom Message to `Tracking test <img src="https://attacker.test/pixel.png" onerror="alert(1)">`. Send invitation and open in an HTML-capable client. | The `<img ...>` markup appears as plain text; no external image is loaded, and no JavaScript executes. |
| HTML-INV-04 | Long multi-line message is preserved safely (RFP) | Enter a multi-line message with bullets and special characters (e.g. `Line 1\n- bullet <test>\n- bullet & other > stuff`). | All lines and special characters render as readable text, with angle brackets and `&` escaped; email layout around the custom-message box remains intact. |
| HTML-INV-05 | RFI invitations escape custom message HTML | From the RFI workflow (RFI invitation / URL generation), set the **Custom Message** in the UI using the same payloads as HTML-INV-02 and HTML-INV-03, send RFI invitations, and inspect emails. | RFI invitation emails show the custom message as plain text; any `<b>`, `<a>`, `<img>`, or inline event handlers are displayed literally and not interpreted by the client. |
| HTML-INV-06 | Legacy/old RFP paths are also safe | If any legacy RFP URL-generation screens are still reachable (e.g. routes using `rfp_old` views), repeat HTML-INV-02 with `<b>` and `<a>` payloads. | Resulting invitation emails do **not** render the injected HTML; tags appear as text in the additional-message section. |
| HTML-INV-07 | Other invitation fields rendered in HTML are safely encoded | In RFP/RFI flows, set `RFP Title`, `RFP Number`, `Company Name`, and vendor display name to include characters like `<`, `>`, `"`, `'`, and `&` (e.g. `ACME <Test> & Co.`). Generate and send invitations. | These fields render correctly in the HTML email (e.g. `ACME <Test> & Co.` is readable), and do not break layout or inject markup. |
| HTML-INV-08 | No regression in plain-text fallback content | Where plain-text email variants exist (e.g. logging or text-only bodies that also include the custom message), repeat HTML-INV-02 but inspect the text body (source / “view original”). | Custom message appears as literal text; presence of `<b>` / `<a>` tags is acceptable because they are not interpreted by the text-only part. |

**Notes for verification:**
- Use at least two different email clients (e.g. Outlook desktop and Gmail web) to avoid client-specific quirks.
- When validating, also inspect the **raw MIME source** (“view original” / “view message source”) to confirm that the custom message is HTML-escaped at the point where it is injected into the rich HTML templates.
- Re-run the original VAPT reproduction steps (URL generation → enter HTML in custom message → send invite) and confirm that the previously observed HTML injection behavior is no longer reproducible.

### Detailed CORS test cases (step + expected result)

| ID | Request / Step | Expected result |
|----|----------------|-----------------|
| CORS-DET-01 | **Burp Repeater:** `GET /api/<protected-endpoint>` with headers `Origin: https://evil.example` and valid session/JWT. | Response may return app status (`200/401/403` based on auth), but **must not** include `Access-Control-Allow-Origin: https://evil.example`. No wildcard `*`. |
| CORS-DET-02 | **Burp Repeater:** Same request with `Origin: https://grc-tprm.vardaands.com` (trusted). | Response includes `Access-Control-Allow-Origin: https://grc-tprm.vardaands.com`. For authenticated request, `Access-Control-Allow-Credentials: true` present. |
| CORS-DET-03 | **Preflight (untrusted):** `OPTIONS /api/<endpoint>` with `Origin: https://evil.example`, `Access-Control-Request-Method: POST`, `Access-Control-Request-Headers: content-type,authorization`. | Preflight must not grant untrusted origin (no matching `Access-Control-Allow-Origin` for evil origin). Browser should block follow-up cross-origin read. |
| CORS-DET-04 | **Preflight (trusted):** same OPTIONS request with trusted origin. | Preflight returns allowed CORS headers for that trusted origin and requested method/headers. Browser allows follow-up request. |

---

## 14. Maker–Checker / Self‑Approval Bypass (Reviewer ID tampering)

**Issue addressed:** A creator could capture the policy/framework (or similar) approval request and modify the `reviewer_id` to their own user ID, allowing them to self‑approve and bypass the maker–checker control.

**Implementation reference (this repo):**
- GRC core:
  - `grc_backend/grc/routes/Policy/policy.py` (policy + framework approval flows, self‑approval checks)
  - `grc_backend/grc/routes/Framework/frameworks.py` (framework approval creation, reviewer assignment)
  - `grc_backend/grc/routes/Compliance/compliance.py` (compliance reviewer assignment, self‑approval guard)
  - `grc_backend/grc/routes/Risk/risk_views.py` (risk reviewer/approver flows, framework‑aware)
  - `grc_backend/grc/routes/Incident/incident_views.py` (incident assignment/review, reviewer validation)
- TPRM:
  - `grc_backend/tprm_backend/contracts/contractapproval/views.py` (contract approvals)
  - `grc_backend/tprm_backend/slas/slaapproval/views.py` (SLA approvals)
  - `grc_backend/tprm_backend/audits/views.py`, `tprm_backend/audits_contract/views.py` (audit review maker–checker)
  - `grc_backend/tprm_backend/rfp/views.py`, `tprm_backend/rfp/rfi/views.py` (RFP/RFI approval flows)

### 14.1 Generic self‑approval bypass test (framework‑level behavior)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| MC-BASE-01 | UI prevents obvious self‑selection | In the GRC UI (e.g. `Policy > VV` or `Framework Explorer`), start a new framework/policy and try to select yourself as reviewer. | Frontend warns or prevents selection (creator and reviewer cannot be the same); form does not submit with self as reviewer. |
| MC-BASE-02 | Backend enforces maker–checker on create | Use Burp/DevTools to intercept the **framework/policy creation or send‑for‑approval** request. Modify payload so `ReviewerId`/`reviewer_id` equals your own `user_id`. | API returns `400/403` with an error like **Self‑approval is not allowed. Please select a different reviewer.** Record is not created/updated in an approved state. |
| MC-BASE-03 | Backend enforces maker–checker on approve | As the original creator, capture the **approve** request for your own policy/framework/record and replay it (or edit `approver_id`/`reviewer_id` to yourself). | API again returns `400/403` self‑approval error; item stays pending/unapproved. |
| MC-BASE-04 | Reviewer list excludes current user (server‑side) | For endpoints that return available reviewers (e.g. `USERS_FOR_REVIEWER_SELECTION`), call them directly with `current_user_id=<your id>`. | Response list does **not** include your own user record as a valid reviewer for that module. |

### 14.2 GRC module‑specific tests (policy, framework, compliance, risk, incidents)

| ID | Area | Test case | How to verify | Expected result (pass) |
|----|------|-----------|---------------|-------------------------|
| MC-GRC-POL-01 | Policy | Create a policy via `Policy > Create new policy` with a normal different reviewer, then intercept the **approval** API and change `reviewer_id`/`ReviewerId` to your own user ID. | API rejects with self‑approval error (from `policy.py`); you cannot approve your own policy. |
| MC-GRC-POL-02 | Policy | Repeat MC-GRC-POL-01 but during **send for approval / deactivation** flows that use framework approval helpers. | Same self‑approval rejection; no policy ends up approved by its creator. |
| MC-GRC-FW-01 | Framework | For a framework you created, trigger a deactivation/approval request and tamper `ReviewerId` to your own ID. | Endpoint in `frameworks.py` enforces `creator_id_int != reviewer_id_int`; returns `400` self‑approval error. |
| MC-GRC-COMP-01 | Compliance | Create or edit a compliance item and assign a reviewer; intercept the submit and set `reviewer_id` equal to `user_id` (creator). | `compliance.py` logs and blocks with **Self‑approval is not allowed**; item remains unapproved. |
| MC-GRC-RISK-01 | Risk | From risk workflow modal/system risks, send a risk for approval but tamper `reviewer_id` to current user. | `risk_views.py` `assign_reviewer` endpoint rejects when `reviewer_id_int == creator_id_int`; 400 with self‑approval message. |
| MC-GRC-RISK-02 | Risk | For a pending risk approval assigned to another reviewer, try to change `ApproverId` or equivalent to your own ID in the approval API. | Risk approval flow still enforces maker–checker; creator cannot mark their own risk as approved. |
| MC-GRC-INC-01 | Incidents | Assign an incident to yourself as both assignee and reviewer by tampering the assignment request (`reviewer_id` == `assigner_id`). | `incident_views.py` returns 400 **Self‑approval is not allowed** and does not persist invalid assignment. |

### 14.3 TPRM module‑specific tests (contracts, SLAs, audits, RFP/RFI)

| ID | Area | Test case | How to verify | Expected result (pass) |
|----|------|-----------|---------------|-------------------------|
| MC-TPRM-CT-01 | Contracts | Create a contract approval where you are the creator; intercept the **approve** request and ensure `current_user_id` equals `creator_id`. | `contractapproval/views.py` blocks with self‑approval error; contract status is not moved to approved. |
| MC-TPRM-SLA-01 | SLA | As SLA owner, capture the SLA approval request and submit it with yourself as assigned approver. | `slaapproval/views.py` treats this as self‑approval and returns 403; SLA remains unapproved. |
| MC-TPRM-AUD-01 | Audits | For contract/core audits where you are assignee, tamper the review action (`approve`) so you approve your own audit as reviewer. | Audit endpoints (`audits/views.py`, `audits_contract/views.py`) log self‑approval attempt and reject with 400/403. |
| MC-TPRM-RFP-01 | RFP | As the RFP creator, intercept the approval call and change `approver_id` to your own user ID. | `rfp/views.py` returns 403 **Self‑approval is not allowed**; RFP stays pending. |
| MC-TPRM-RFI-01 | RFI | Repeat MC-TPRM-RFP-01 for RFI approvals. | `rfp/rfi/views.py` blocks the action with self‑approval error; no self‑approved RFI. |

### 14.4 Regression / logging checks

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| MC-LOG-01 | Self‑approval attempts are logged | Perform any of the above tampering attempts against lower environment. Review backend logs for messages like `Self-approval attempt detected` per module. | Logs clearly record self‑approval attempts with user id, entity id, and module context for auditability. |
| MC-REG-01 | Normal maker–checker flows still work | For each module (policy, framework, compliance, risk, contracts, SLA, audits, RFP/RFI), perform a normal flow where **creator A** submits and **reviewer B** approves. | Submissions and approvals succeed without error; only self‑approval attempts are blocked. |

---

<!-- End of maker–checker / self‑approval test cases -->
| CORS-DET-05 | **Origin reflection check:** Repeat same request with random origins (`https://a.example`, `https://b.example`, `null`, malformed origin). | Server does not blindly mirror arbitrary origin values. Only allowlisted origins get CORS allow headers. |
| CORS-DET-06 | **Credentialed browser call:** Frontend sends `withCredentials=true` (or cookie-based request) from trusted domain. | Request works for valid auth; headers are consistent (`Access-Control-Allow-Origin` exact trusted origin, `Access-Control-Allow-Credentials: true`). |
| CORS-DET-07 | **Credentialed browser call from untrusted page:** host a simple JS page on untrusted domain and call API with credentials. | Browser blocks response due to CORS policy; data is not readable by untrusted page. |
| CORS-DET-08 | **No-Origin client:** call API from Postman/curl without `Origin` header. | API behavior unchanged (business logic/auth works as before). CORS controls do not break server-to-server usage. |
| CORS-DET-09 | **Proxy path verification:** Access API via deployment reverse proxy path used in prod. | Proxy does not inject wildcard `Access-Control-Allow-Origin`; backend allowlist remains source of truth. |
| CORS-DET-10 | **Regression smoke:** Login, dashboard load, key CRUD actions in GRC + TPRM from trusted frontend. | No CORS errors in browser console/network for normal allowed flows; application functionality remains intact. |

---

## 14. Concurrent Login Control (single active session)

**Issue addressed:** Same credentials were usable in multiple browsers at the same time.  
**Fix expectation:** Only one active session token (`jti`) is valid per user; a newer login invalidates older sessions and forces re-authentication.

**Implementation reference (this repo):**
- `grc_backend/grc/authentication.py`
- `grc_backend/grc/middleware.py`
- `grc_backend/grc/jwt_auth.py`
- `grc_frontend/src/services/apiService.js`
- `grc_frontend/src/services/authService.js`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| CONC-01 | New login invalidates old browser session | Login in Browser A. Login with same user in Browser B. In Browser A, call any protected API or refresh page. | Browser A receives `401` (`session_invalidated=true`) and is redirected to login. Browser B stays active. |
| CONC-02 | Refresh token from old session is blocked | After CONC-01, use Browser A to trigger `/api/jwt/refresh/` (or wait for refresh path). | Refresh fails with `401` and message that session was invalidated due to newer login. |
| CONC-03 | Latest session refresh still works | After CONC-01, trigger refresh from Browser B. | Refresh succeeds and issues fresh tokens. |
| CONC-04 | Logout invalidates current session | Login, then call `/api/jwt/logout/`, then retry protected API with previous token. | Protected API fails with `401`; session token is no longer valid. |
| CONC-05 | MFA login also enforces single active session | Complete MFA login in Browser A, then MFA login in Browser B with same account. Retry API in Browser A. | Browser A is invalidated (`401`), Browser B remains active. |
| CONC-06 | Google SSO login also enforces single active session | Google SSO login in Browser A, repeat in Browser B, then use Browser A on protected route. | Browser A becomes unauthorized and must re-login; Browser B remains valid. |
| CONC-07 | Token replay after re-login fails | Capture old access token before second login; replay it in Postman/curl after second login. | API returns `401` because `jti` no longer matches active session token. |
| CONC-08 | Audit trail for login/logout remains present | Perform logins/logouts and inspect system logs UI/table. | `LOGIN_SUCCESS`/`LOGOUT` entries are still written with user and IP metadata. |
| CONC-09 | Multi-tab in same browser remains usable | Login once and open multiple tabs in same browser profile. | Tabs continue working (same active session) until a new login occurs elsewhere. |
| CONC-10 | Regression smoke after enforcement | Validate normal auth flows: login, dashboard, CRUD action, refresh, logout. | No functional regression for normal single-session usage. |

---

## 15. Missing Authentication — Protected API endpoints (framework-level)

**Issue addressed:** Multiple API endpoints were accessible without authentication and returned sensitive data (users, documents, notifications, Jira stored data/tokens, external applications).

**Fix expectation:** All sensitive `/api/` endpoints require a valid session/JWT. Unauthenticated requests return **401** (or **403** depending on policy), and do not leak data. OAuth **callbacks** remain publicly reachable, but must not disclose secrets without a user-bound session.

**Implementation reference (this repo):**
- Framework-level enforcement: `grc_backend/grc/middleware.py` (`JWTAuthenticationMiddleware`)
- Endpoint routing: `grc_backend/grc/urls.py`, `grc_backend/backend/urls.py`

| ID | Endpoint | Test case | How to verify | Expected result (pass) |
|----|----------|-----------|---------------|-------------------------|
| AUTH-API-01 | `/api/documents/upload/` | Upload blocked without auth | Send `POST` without `Authorization` header and without session cookies. | `401` (or `403`); no upload occurs; no file URL/metadata leaked. |
| AUTH-API-02 | `/api/documents/list/` | List blocked without auth | Send `GET` without auth. | `401/403`; response does not include document list. |
| AUTH-API-03 | `/api/documents/counts/` | Counts blocked without auth | Send `GET` without auth. | `401/403`; no counts returned. |
| AUTH-API-04 | `/api/users/` | User list blocked without auth | Send `GET` without auth. | `401/403`; no user data returned. |
| AUTH-API-05 | `/api/get-notifications/?user_id=2` | Notifications blocked without auth | Send `GET` without auth; attempt enumeration by changing `user_id`. | `401/403` for all; no notification data leaked. |
| AUTH-API-06 | `/api/jira/users/` | Jira users blocked without auth | Send `GET` without auth. | `401/403`; no Jira data/token leakage. |
| AUTH-API-07 | `/api/jira/stored-data/` | Jira stored data blocked without auth | Send `GET` without auth. | `401/403`; no stored data returned. |
| AUTH-API-08 | `/api/jira/stored-data/?user_id=1` | Jira stored data enumeration blocked | Send `GET` without auth; change `user_id`. | `401/403`; no data leakage. |
| AUTH-API-09 | `/api/external-applications/` | External apps blocked without auth | Send `GET` without auth. | `401/403`; no integration status/data leaked. |
| AUTH-API-10 | (all above) | Authenticated access still works | Repeat each request with valid `Authorization: Bearer <access_token>` (or valid session cookie). | `200` (or expected success) and correct data returned for authorized user. |
| AUTH-API-11 | OAuth callbacks (e.g. `/api/jira/oauth-callback/`) | Callback still reachable without existing JWT | Hit callback endpoint from provider redirect without auth headers. | Endpoint returns expected redirect/response for the OAuth flow; does not expose stored tokens to unauthenticated callers. |

### Execution checklist (QA sign-off)

- [ ] Verify **401/403** for each endpoint when called without `Authorization` or session cookie.
- [ ] Verify endpoints return **200** when called with a valid token/session.
- [ ] Verify no sensitive payload fragments appear in error bodies (no tokens, no user details, no stack traces).
- [ ] Verify CORS **preflight** (`OPTIONS`) succeeds (browser should be able to complete auth-bearing requests from trusted frontend origin).

---

## 16. Invalid URL validation — Vendor invitation `baseUrl` allow-list (RFP / Vendor portal)

**Issue addressed:** The RFP vendor onboarding invitation flow accepted a **`baseUrl`** parameter from the client and used it directly when generating invitation links in emails. By tampering with this parameter (e.g. in Burp), an attacker could cause vendor invitations to contain arbitrary attacker-controlled URLs instead of the official Riskavaire portal, enabling phishing and brand impersonation.

**Implementation reference (this repo):**
- Backend invitation generation (new URI method): `grc_backend/tprm_backend/rfp/views_invitation_generation.py` (`generate_invitations_new_format`, `_get_safe_frontend_base_url`)
- Backend unmatched-vendor/open-flow URLs: `grc_backend/tprm_backend/rfp/views_rfp_responses.py` (`build_dynamic_urls`, `_get_safe_vendor_portal_base_url`)
- RFP URL Generation UI / service: `grc_frontend/tprm_frontend/src/views/rfp/Phase4URLGeneration.vue`, `grc_frontend/tprm_frontend/src/services/vendorInvitationService.js`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| INV-BASEURL-01 | Baseline invite uses Riskavaire domain | From the RFP Workflow → **URL Generation / Vendor Invitation**, select vendors and generate invitations without intercepting the request. Inspect the email invite link and the stored `invitation_url` via API/DB. | The hostname of the invitation URL matches the configured Riskavaire application domain (from `EXTERNAL_BASE_URL`), e.g. `riskavaire.vardaands.com`; no unexpected external host appears. |
| INV-BASEURL-02 | Tampered `baseUrl` host is rejected (RFP invitations) | Repeat the QA team’s Burp step: intercept the `POST /vendor-invitations/create/...` (or `generate_invitations_new_format`) request and change `baseUrl` to `https://attacker.example/vendor-portal`. Send the request and inspect the resulting `invitation_url` in the response/email. | Despite the tampered `baseUrl`, the generated `invitation_url` host remains the legitimate Riskavaire domain; the attacker host is ignored and not reflected in the email link. |
| INV-BASEURL-03 | Tampered `baseUrl` host is rejected (unmatched/open vendor flow) | In the open/unmatched vendor submission flow that calls `create_unmatched_vendor` (or equivalent), intercept the request body and set `baseUrl` to `https://attacker.example/vendor-portal`. | The URLs produced by `build_dynamic_urls` (`invitation_url`, `acknowledgment_url`, `submission_url`) all retain the Riskavaire domain; none of them point to `attacker.example`. |
| INV-BASEURL-04 | Malformed `baseUrl` does not break flow | Intercept the same requests and set `baseUrl` to malformed values such as `not-a-url`, `javascript:alert(1)`, or an empty string. | Backend falls back to the configured `EXTERNAL_BASE_URL`; invitations are generated successfully using the legitimate domain, and no server error/500 occurs. |
| INV-BASEURL-05 | Path and query tampering are ignored | Intercept the `baseUrl` and set it to `https://riskavaire.vardaands.com.evil.com/fake-path` or `https://riskavaire.vardaands.com/other-app?next=https://attacker.example`. | Invitations still use the canonical Riskavaire origin and server-controlled paths (e.g. `/tprm/submit` or `/vendor-portal`); attacker-supplied subdomains or path/query segments are not reflected in the final links. |
| INV-BASEURL-06 | Logging/monitoring captures rejected `baseUrl` attempts | With application logs enabled, repeat INV-BASEURL-02/03 using clearly attacker-style hosts. | Server logs include a security warning similar to **"Rejected untrusted baseUrl host for invitations/vendor portal"** with the attempted value, allowing SOC/VAPT teams to detect tampering attempts. |
| INV-BASEURL-07 | Legacy invitations and portal flows still work | Execute normal RFP vendor invitation flows (including unmatched vendor creation and vendor portal access) without tampering `baseUrl`. | Invitations are generated and emails delivered as before; vendors can open the official portal links and complete onboarding without regression. |

### Vendor `baseUrl` validation execution checklist (QA sign-off)

- [ ] Confirm that every RFP vendor invitation email link uses the official Riskavaire hostname from `EXTERNAL_BASE_URL` (no arbitrary external domains).
- [ ] Using Burp/Proxy, verify that changing `baseUrl` to external hosts in RFP URL Generation and unmatched-vendor flows does **not** change the host of the generated links.
- [ ] Confirm that malformed `baseUrl` inputs are handled gracefully (no 500s), with safe fallback to the configured domain.
- [ ] Confirm that path/query tricks on `baseUrl` do not allow redirecting vendors to attacker-controlled routes.
- [ ] Confirm from logs that untrusted `baseUrl` host attempts are captured with clear security messages.
- [ ] Re-run the original VAPT reproduction steps and verify that the issue (malicious vendor onboarding links via `baseurl` tampering) is no longer reproducible.

---

## 17. Improper error handling & debug stack traces (RFP Evaluation / `evaluator_id`)

**Issue addressed:** In the RFP evaluation workflow, tampering the `evaluator_id` parameter to a non-integer (e.g. string) caused Django/DRF to surface verbose error output and, in some environments, a full debug stack trace. This leaks framework internals (file paths, view names, query structure) and makes reconnaissance easier for attackers.

**Implementation reference (this repo):**
- Backend project settings: `grc_backend/backend/settings.py` (`DJANGO_DEBUG` and DRF `REST_FRAMEWORK`).
- TPRM project settings: `grc_backend/tprm_backend/tprm_project/settings.py` (`REST_FRAMEWORK['EXCEPTION_HANDLER']` now points to `tprm_backend.utils.vendor_exception_handler.vendor_custom_exception_handler`).
- Central exception handler: `grc_backend/tprm_backend/utils/vendor_exception_handler.py`.
- RFP approval helper endpoint: `grc_backend/tprm_backend/rfp_approval/views.py` (`get_proposal_id_from_approval` generic 500 response).

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| ERR-DEBUG-01 | Global debug disabled in non‑dev | In the production/staging environment, confirm `DJANGO_DEBUG=false` (and `DEBUG=false` where applicable) in the process environment or `.env` used by `backend` / `tprm_project`. Restart the app. | `settings.DEBUG` is `False` for both the core GRC backend and TPRM backend; Django no longer shows HTML debug pages. |
| ERR-DEBUG-02 | RFP Evaluation – invalid `evaluator_id` via UI | From the UI: go to **RFP Workflow → Evaluation**, start an evaluation normally so that an evaluation save/submit request is sent. Intercept the request in Burp, change the `evaluator_id` field in the JSON body to a non-integer string (e.g. `"abc"`), then replay. | The API responds with a 4xx or 5xx JSON error **without** an HTML stack trace. Response body contains only generic error fields (e.g. `{"error": "...generic message..."}`); no file paths, no full trace, no ORM/SQL details. |
| ERR-DEBUG-03 | RFP Approval helper – invalid `evaluator_id` in query | Hit the proposal helper endpoint that uses `get_proposal_id_from_approval`, capturing an existing `approval_id` and then calling `GET /api/.../rfp-approval/get-proposal-id/<approval_id>/?stage_id=<valid>&evaluator_id=not-an-int` (exact base path may vary by deployment). | The endpoint either falls back to safe behavior or returns a sanitized JSON error. No Django HTML debug page or raw exception type/trace is visible in the client. |
| ERR-DEBUG-04 | Central DRF exception handler used | Using any DRF JSON API in the TPRM project (e.g. an RFP or approval endpoint), deliberately trigger a server error (e.g. by omitting required fields or sending malformed JSON). Verify via logs that `vendor_custom_exception_handler` logged the exception. | Client sees a consistent JSON format (fields like `error`, `message`, `timestamp`); detailed exception info only appears in **server logs**, not in the HTTP response. |
| ERR-DEBUG-05 | No stack traces in HTTP responses (spot check) | Manually review a sample of failing API calls across RFP / TPRM endpoints (400, 403, 404, 500) in the browser’s Network tab and via Burp. | Error responses are machine-readable JSON, not HTML, and contain no Python file paths, module names, or stack trace frames. |
| ERR-DEBUG-06 | Logs restricted but detailed | Using server-side logs (not API responses), verify that exceptions during evaluation flows (including invalid `evaluator_id`) are recorded by the `vendor_security` logger with type, message, path, method and user metadata. | Security/ops teams can see rich diagnostic info in logs while attackers cannot obtain it via HTTP. |

### Execution checklist (QA sign-off)

- [ ] Confirm `DJANGO_DEBUG` / `DEBUG` are **false** in all non‑development environments for both core GRC and TPRM Django projects.
- [ ] Re-run the original VAPT reproduction: tamper `evaluator_id` to a string in RFP Evaluation and verify that no HTML stack trace or internal paths are returned.
- [ ] Confirm that RFP evaluation, approval, and related flows still work normally when inputs are valid (no regression).
- [ ] Spot-check several error scenarios (400/403/404/500) and verify responses are JSON, generic, and free of stack traces or file paths.
- [ ] Verify from logs that detailed error information is captured only in server-side logs (e.g. `vendor_security`) and not exposed to clients.

---

## 18. Server-Side Request Forgery (SSRF) — Incident PDF export hardening

**Issue addressed:** The incident dashboard **PDF export** endpoint (`/api/incidents/export/` → `export_incidents` → `export_data` → `export_to_pdf`) must not make outbound HTTP requests based on attacker-controlled input (for example crafted URLs or HTML/JS inside the export payload).

**Implementation reference (this repo):**
- Backend incident export endpoint: `grc_backend/grc/routes/Incident/incident_views.py` (`export_incidents`, `_sanitize_export_payload`, `_validate_and_sanitize_client_export_data`)
- Shared export utility: `grc_backend/grc/routes/Global/s3_fucntions.py` (`export_data`, `export_to_pdf`)
- PDF post-processing / S3 download (fixed, non-user-controlled URL): `grc_backend/grc/routes/Global/s3_fucntions.py` (`_process_pdf_after_upload`, `_extract_text_from_pdf`, `_extract_pdf_metadata`)

### 18.1 Functional / negative tests (no SSRF via incident PDF export)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SSRF-INC-01 | Baseline incident PDF export still works | From the Incident Dashboard UI, click **Export** → **PDF** (no tampering). Capture the request (`POST /api/incidents/export/`) and response in Burp/DevTools. | Response is `200` with a JSON body containing `success=true` and a `file_url` pointing to the configured S3/CloudFront domain; incidents PDF downloads and opens correctly. |
| SSRF-INC-02 | Malicious URL inside `data` treated as plain text | Intercept `POST /api/incidents/export/` and, inside `data` (either client-provided JSON or DB-fetched payload), inject fields containing URLs like `http://169.254.169.254/latest/meta-data/` and `http://127.0.0.1:22/` into `Description` / `Title`. Complete export and monitor backend logs/network. | Export either succeeds or fails **without** any server-side HTTP calls to those attacker URLs. Generated PDF shows the URL **only as plain text**; no additional outbound requests to `169.254.169.254`, `127.0.0.1`, or arbitrary host are observed. |
| SSRF-INC-03 | Malicious URL inside `options` treated as data only | Intercept the same export request and set `options` (JSON) to include keys like `"callbackUrl": "http://169.254.169.254/latest/meta-data/"` or `"logoUrl": "http://attacker.example/logo.png"`. | API response remains bounded (200/400) and no outbound HTTP calls are made to those URLs. `export_data` only uses `options` for filename/metadata; URLs inside `options` are not dereferenced. |
| SSRF-INC-04 | JSON string `data` with nested URL payloads | Set `data` to a JSON string representing an array of incidents where nested fields (`details.link`, `history[0].url`, etc.) contain internal URLs (`http://10.0.0.5:8080/`, `http://[::1]/`). | Request passes through `_validate_and_sanitize_client_export_data` without causing outbound HTTP requests to those hosts. PDF, if generated, treats URLs as text only. |
| SSRF-INC-05 | Payload exceeding SSRF-related limits still returns safe error | Create a very large `data` payload containing thousands of URL-looking strings (mixed internal + external). | Endpoint responds with `400` and a validation error such as **"Export data exceeds maximum..."** or **"Export payload has too many list items"**. No long-running requests or spikes in outbound HTTP traffic are observed. |

### 18.2 Platform-level / outbound network tests (defensive posture)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SSRF-PLAT-01 | Export cannot reach cloud metadata IP | In a non-production environment where you can monitor egress, repeat SSRF-INC-02 with `http://169.254.169.254/latest/meta-data/` and inspect firewall/proxy logs. | No connection attempts from the application server to `169.254.169.254` are observed. |
| SSRF-PLAT-02 | Export cannot reach private RFC1918 ranges | Repeat SSRF-INC-02 with URLs to `http://10.0.0.1/`, `http://172.16.0.1/`, `http://192.168.0.1/` in incident fields. | No outbound connections from the app to these private ranges are observed in network logs. |
| SSRF-PLAT-03 | Only allow-listed S3/CloudFront host used for export | For multiple PDF exports, capture the backend’s outbound traffic (proxy/egress logs). | Outbound HTTP(S) requests related to incident exports go only to the configured S3/CloudFront host used by `RenderS3Client`; no other hosts from export payloads appear. |

### 18.3 Regression / cross-module checks

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SSRF-REG-01 | Other export formats remain functional | Repeat SSRF-INC-01 but choose **XLSX**, **CSV**, **JSON**, and **TXT**. | All formats still export successfully with expected content and no regression from SSRF hardening. |
| SSRF-REG-02 | Audit findings export path has same behavior | From UI or via API, call `/api/audit-findings/export/` (or equivalent) and inject the same URL payloads in `data` as SSRF-INC-02. | Behavior matches incident export: URLs are rendered as text only; no outbound HTTP(S) calls to attacker-controlled hosts are observed. |
| SSRF-REG-03 | Existing DoS export hardening remains effective | Re-run DOS-EXP-02..DOS-EXP-06 from section 7 against `/api/incidents/export/` after SSRF hardening. | All DoS-related protections still pass (invalid/oversized payloads rejected quickly; no resource exhaustion or service unavailability). |

---

## 19. Ollama LLM — Unauthorized access & network exposure

**Issue addressed:** The Ollama LLM service was reachable over the network (e.g. `http://<public-ip>:11434`) without authentication, exposing management and inference endpoints (`/api/tags`, `/api/generate`, `/api/chat`, `/api/create`, `/api/delete`) directly to unauthenticated clients.

**Implementation reference (this repo):**
- Runtime configuration: `grc_backend/.env.production` (`RISK_AI_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`)  
- Risk AI / document AI calls: `grc_backend/grc/routes/Risk/risk_ai_doc_optimized.py`, `grc_backend/grc/routes/Risk/risk_instance_ai.py`  
- Global document summarization / PDF AI: `grc_backend/grc/routes/Global/s3_fucntions.py` (`_call_ollama`, AI summary helpers)  
- Audit AI API (legacy direct calls): `grc_backend/grc/routes/Audit/ai_audit_api.py` (`_call_ollama_api`)  
- TPRM risk analysis (Llama service): `grc_backend/tprm_backend/risk_analysis/llama_service.py`

### 19.1 Network exposure & access control

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| OLLAMA-NET-01 | Ollama not reachable from the public internet | From a machine **outside** the private network/VPC (VAPT box or external VPN), run `curl -v http://<public-ip-or-dns>:11434/api/tags` and `curl -v http://<public-ip-or-dns>:11434/api/generate -d '{}'`. | Connection **fails** (timeout / TCP reset / blocked by firewall) or returns a non-200 error from a reverse proxy; no direct Ollama JSON response is visible. |
| OLLAMA-NET-02 | Ollama bound to localhost or private address only | On the server where Ollama runs, execute `ss -tulpn | grep 11434` (Linux) or `netstat -ano | findstr 11434` (Windows). | Ollama listens only on `127.0.0.1` or a private VPC IP (e.g. `10.x.x.x`); it is **not** bound to `0.0.0.0` on a public interface. |
| OLLAMA-NET-03 | Security group / firewall restricts port 11434 | Inspect cloud security groups / firewall rules for the Ollama host. | Inbound on port **11434** is limited to the application servers/jump-box subnets; there is **no** rule allowing `0.0.0.0/0` or broad internet to 11434. |
| OLLAMA-NET-04 | Optional reverse proxy requires auth | If Ollama is exposed behind Nginx/HTTP proxy (e.g. `/ollama/` path), call that URL from a browser or `curl` without credentials. | Access is blocked with `401/403` (e.g. HTTP Basic or token check); management APIs are not callable anonymously. |

### 19.2 Application behavior and configuration

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| OLLAMA-APP-01 | Backend uses internal/base URL only | Check runtime `OLLAMA_BASE_URL` (`env` or admin shell) and compare to deployment topology. | Value is an internal URL (e.g. `http://127.0.0.1:11434` or `http://ollama.internal:11434`); it is **not** a raw public IP/hostname reachable from the internet. |
| OLLAMA-APP-02 | Risk AI routes do not re-expose Ollama endpoints | From external clients, call risk AI endpoints (e.g. risk ingestion, risk instance AI) and inspect responses. | APIs return only **business JSON**; they never proxy raw `/api/tags` / `/api/generate` / `/api/chat` responses or allow arbitrary Ollama path/URL selection from user input. |
| OLLAMA-APP-03 | Global PDF/summary routes do not leak Ollama URL | Use `s3_fucntions`-backed endpoints (incident/compliance exports, AI summaries) and inspect responses and logs. | Client-facing responses do **not** contain `OLLAMA_BASE_URL` or raw Ollama host/port; only application-level data (summaries, file URLs) is returned. |
| OLLAMA-APP-04 | Audit AI / legacy Llama service calls stay internal | Trigger audit AI and TPRM risk analysis features that use `_call_ollama_api` or `LlamaService`. | Requests from clients always hit your normal Django API endpoints; there is no separate public endpoint exposing Ollama directly. |

### 19.3 Hardening & monitoring

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| OLLAMA-HARD-01 | Authentication layer in front of any shared Ollama instance | If multiple apps share the same Ollama cluster, verify that they connect via mTLS, VPN, or an authenticated proxy (token/header-based). | Only trusted backends can reach Ollama; attempts from arbitrary hosts are rejected at network or proxy layer. |
| OLLAMA-HARD-02 | Access logs monitored for abuse | Enable request logging on Ollama or its reverse proxy and generate a small number of test calls. | Logs record requests (IP, path, status); monitoring/alerting exists for unusual spikes or unknown source IPs hitting `/api/generate` / `/api/chat` / `/api/create` / `/api/delete`. |
| OLLAMA-HARD-03 | Management endpoints not used in production flows | Review code/infra paths for any use of `/api/create`, `/api/delete`, `/api/pull`, `/api/push` in production workloads. | Production app uses only inference endpoints (`/api/generate`, `/api/chat`) for serving traffic; model management endpoints are disabled, blocked, or restricted to admin-only networks. |
| OLLAMA-HARD-04 | Fallback to OpenAI or other provider still works | Set `RISK_AI_PROVIDER=openai` (or equivalent) and restart backend in non-prod. Exercise key AI flows (risk ingestion, risk instance AI, global summaries). | App continues to function using the alternate provider; disabling Ollama in a given environment does not break core workflows. |

### 19.4 Quick sign-off checklist (Ollama)

- [ ] `OLLAMA_BASE_URL` points to **localhost or private VPC host**, not a raw public IP/port.  
- [ ] Port **11434** is **not** exposed to the internet; only app subnets/jump-boxes can reach it.  
- [ ] No public-facing URL (Nginx, load balancer, API gateway) routes directly to `/api/tags`, `/api/generate`, `/api/chat`, `/api/create`, or `/api/delete` on Ollama.  
- [ ] If a reverse proxy exposes Ollama for admin use, it enforces strong **authentication + authorization**.  
- [ ] Logs for Ollama (or its proxy) are enabled and monitored for abuse, brute-force prompts, or unknown clients.  
- [ ] AI features in GRC/TPRM work normally after hardening (risk AI, document AI, audit AI, TPRM risk analysis).

---

## 20. Self-Approval via Reviewer ID Tampering (Frameworks & Policies)

**Issue addressed:** A creator could modify the `ReviewerId` field in API requests (via Burp/DevTools) to set themselves as reviewer, allowing self‑approval of frameworks and policies and bypassing maker–checker control.

**Implementation reference (this repo):**
- `grc_backend/grc/routes/Framework/frameworks.py` — framework approval creation (`FrameworkApproval.objects.create` with `UserId` and `ReviewerId`)
- `grc_backend/grc/routes/Policy/policy.py` — policy and framework+policy creation flows that create `PolicyApproval` / `FrameworkApproval` with client-supplied reviewer IDs
- Frontend policy UI:
  - `grc_frontend/src/components/Policy/FrameworkExplorer.vue`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SELF-APPROVE-01 | Framework creation cannot self-assign reviewer | In the UI, create a new framework with a normal reviewer selected (different user). Capture the approval-creation request in Burp and change `ReviewerId` in the JSON body to the **creator's own user id**. Replay the request. | API returns `400` (or `403`) with an error like **"Self-approval is not allowed. Please select a different reviewer."** No new `FrameworkApproval` is created with `UserId == ReviewerId`. UI does not show this framework as awaiting review by the creator. |
| SELF-APPROVE-02 | Policy creation cannot self-assign reviewer | From the Policy module, create a new policy under an approved framework. When the request that creates the initial `PolicyApproval` is sent, intercept it and set `Reviewer` / `ReviewerId` equal to the creator's user id. | API rejects the request with a 4xx error and message similar to **"Self-approval is not allowed"**. No `PolicyApproval` record exists where `UserId == ReviewerId` for that policy version. |
| SELF-APPROVE-03 | Review endpoint blocks creator from approving own policy | As the policy creator, try to use the reviewer/approval screen (or direct API) to approve your own policy by sending an approval request where the current authenticated user id equals the original `UserId` on the policy. | API returns `403` (or suitable 4xx) and does not create a reviewer-version `PolicyApproval` where `UserId == ReviewerId`. UI should show an error and keep the policy in pending state until a different reviewer acts. |
| SELF-APPROVE-04 | Legitimate reviewer assignment still works | Login as User A (creator). Assign User B as reviewer using the normal UI flow and do not tamper the request. Then login as User B and approve the framework/policy. | Approval is created successfully with `UserId=A` and `ReviewerId=B`. Framework/policy status transitions correctly; no regression for valid maker–checker flows. |

**Checklist (sign-off):**

- [ ] Attempts to set `ReviewerId` equal to the creator's id for frameworks are rejected (SELF-APPROVE-01).
- [ ] Attempts to set `Reviewer` / `ReviewerId` equal to the creator's id for policies are rejected (SELF-APPROVE-02).
- [ ] Creator cannot approve their own policy via review endpoints; server enforces `creator_id != reviewer_id` (SELF-APPROVE-03).
- [ ] Normal flows with different reviewer users continue to work without regression (SELF-APPROVE-04).

---

## 21. Self-Approval via Reviewer ID Tampering (Compliance, Incidents)

**Issue addressed:** Creators/assignees of compliance items or incidents could potentially manipulate reviewer assignment (e.g. via tampered `ReviewerId` or implicit session fields) to approve their own compliance records or incident assessments.

**Implementation reference (this repo):**
- Compliance:
  - `grc_backend/grc/models.py` (`ComplianceApproval`)
  - `grc_backend/grc/routes/Compliance/compliance.py`
  - `grc_backend/grc/routes/Compliance/compliance_views.py`
- Incidents:
  - `grc_backend/grc/models.py` (`IncidentApproval`)
  - `grc_backend/grc/routes/Incident/incident_views.py`

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SELF-APPROVE-COMP-01 | Compliance creator cannot self-assign as reviewer during initial approval creation | Create or edit a compliance item in the UI so that a new `ComplianceApproval` is triggered. In Burp, intercept the request that results in `ComplianceApproval.objects.create(...)` (see `compliance.py` / `compliance_views.py`) and force the `ReviewerId` (or underlying session-derived reviewer) to equal the same numeric id used as `UserId` for that approval. | API responds with `400` and a message like **"Self-approval is not allowed. Please select a different reviewer."** No `ComplianceApproval` row exists with `UserId == ReviewerId` for that identifier/version. |
| SELF-APPROVE-COMP-02 | Compliance review endpoint does not allow creator to approve their own item | As the user who originally submitted the compliance (creator), attempt to approve it using the review UI or direct API. Confirm that the backend enforces maker–checker by comparing the stored creator id on the relevant `ComplianceApproval` with the current reviewer id. | If creator and reviewer ids are equal, the API returns `403`/`400` and no reviewer-version `ComplianceApproval` is created with `UserId == ReviewerId`. |
| SELF-APPROVE-INC-01 | Incident assignee cannot be their own reviewer on assessment submission | Start an incident assessment as a normal user (assignee). When the assessment submit request hits `/api/incidents/...` in `incident_views.py`, intercept it and tamper any reviewer-related field so that the resolved reviewer id equals the current user id (assignee). | API returns `400` with an error like **"Self-approval is not allowed. Please select a different reviewer."** The created `IncidentApproval` row for that incident never has `AssigneeId` equal to `ReviewerId` for that assessment version. |
| SELF-APPROVE-INC-02 | Legitimate incident assessment with different reviewer still works | Configure an incident so that User A is assignee and User B is reviewer. Submit the assessment as User A without tampering, then complete the review as User B. | Both creation of the `IncidentApproval` and subsequent review/processing succeed. At no point is there an `IncidentApproval` with `AssigneeId == ReviewerId` unless that combination was present before this hardening and is only read (not newly created). |

**Checklist (sign-off):**

- [ ] Attempts to force `ComplianceApproval.UserId == ReviewerId` via tampering are rejected (SELF-APPROVE-COMP-01).
- [ ] Compliance review flows prevent creators from approving their own changes (SELF-APPROVE-COMP-02).
- [ ] Incident assessment submissions cannot produce `IncidentApproval` rows where the current assignee is also stored as reviewer (SELF-APPROVE-INC-01).
- [ ] Normal compliance and incident approval flows with distinct reviewer users function without regression (SELF-APPROVE-INC-02).

---

## 22. Self-Approval via Approver ID Tampering (Risk Approvals)

**Issue addressed:** In the risk module, approver assignment and approval records are stored via the `risk_approval` table (`RiskApproval` model), using `UserId` (creator) and `ApproverId` (reviewer/approver). An attacker could attempt to set `ApproverId` equal to the creator’s user id when assigning a reviewer or creating an approval record, enabling self-approval of risk assessments.

**Implementation reference (this repo):**
- `grc_backend/grc/models.py` (`RiskApproval`)
- `grc_backend/grc/routes/Risk/risk_views.py` — particularly:
  - `assign_reviewer` flow that accepts `user_id` / `reviewer_id` from the client and writes to `risk_approval` (via direct SQL insert).

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SELF-APPROVE-RISK-01 | Risk creator cannot assign themselves as approver | From the risk UI, submit a risk so that `assign_reviewer` is called. In Burp, intercept the request to the risk reviewer assignment endpoint (`risk_views.assign_reviewer`) and set `ReviewerId`/`reviewer_id` equal to the same id that is sent/derived as `UserId`/`user_id`. | API returns `400` with an error like **"Self-approval is not allowed. Please select a different reviewer."** No new row is inserted into `risk_approval` where `UserId == ApproverId` for that risk instance. |
| SELF-APPROVE-RISK-02 | Risk approval insert path respects maker–checker | Trigger a normal risk submission that sets `create_approval_record=true` so the backend goes through the `INSERT INTO grc2.risk_approval (RiskInstanceId, version, ExtractedInfo, UserId, ApproverId, ...)` path in `risk_views.py`. Attempt to tamper the request so `ReviewerId` equals the creator id. | The maker–checker check added in `assign_reviewer` rejects the request before the INSERT runs; no `risk_approval` row is written with `UserId == ApproverId`. |
| SELF-APPROVE-RISK-03 | Reviewer tasks list still shows correct items | As a legitimate reviewer (User B) assigned to risks created by User A, open the “My Risk Reviews” / reviewer tasks view. | Reviewer tasks are still populated from `risk_approval` using `ApproverId=B`; no regression in listing logic after the new check. |
| SELF-APPROVE-RISK-04 | Normal risk workflow with different reviewer still works | Configure a risk where User A is the creator (`UserId`) and User B is assigned as reviewer (`ReviewerId`). Submit the risk and complete the review as User B without tampering. | Risk approval records are created as expected, with `UserId=A` and `ApproverId=B`. Risk status and versioning behave as before; only self-approval attempts are blocked. |

**Checklist (sign-off):**

- [ ] Attempts to assign the same person as both risk creator and approver are rejected by `assign_reviewer` (SELF-APPROVE-RISK-01).
- [ ] No new records in `risk_approval` are created where `UserId == ApproverId` due to client-side tampering (SELF-APPROVE-RISK-02).
- [ ] Reviewer task listings (`ApproverId`-based) still function correctly after hardening (SELF-APPROVE-RISK-03).
- [ ] Normal risk approval flows with separate creator and reviewer/approver users continue to function without regression (SELF-APPROVE-RISK-04).

---

## 23. Self-Approval Controls in TPRM RFP & BCP/DRP Modules

**Issue addressed:** In TPRM workflows (RFP approvals and BCP/DRP questionnaires), creators could potentially approve or review their own items if creator and approver/reviewer identities were not enforced strictly on the server side, or if reviewer ids were taken directly from client input.

**Implementation reference (this repo):**
- RFP core approval flow: `grc_backend/tprm_backend/rfp/views.py` (`RFPViewSet.approve`)
- BCP/DRP questionnaire review: `grc_backend/tprm_backend/bcpdrp/views.py` (`questionnaire_review_save_view`)
- TPRM questionnaire model: `grc_backend/tprm_backend/bcpdrp/models.py` (`Questionnaire.created_by_user_id`, `reviewer_user_id`)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SELF-APPROVE-TPRM-RFP-01 | RFP creator cannot approve their own RFP via `/approve` | Create an RFP as User A (so `created_by` = A). Move it to `IN_REVIEW` normally. Then, as User A, call the RFP approve endpoint (via UI or direct `POST` to `.../rfps/<id>/approve/`). | API returns `403` with an error like **"Self-approval is not allowed. Please assign a different reviewer to approve this RFP."** `status` and `approved_by` remain unchanged; RFP is not marked approved by its creator. |
| SELF-APPROVE-TPRM-RFP-02 | Non-creator reviewer can approve an RFP | Create an RFP as User A, ensure it reaches `IN_REVIEW`, then login as User B (designated reviewer/approver) and call the approve endpoint without tampering. | API returns `200` and sets `status` to `PUBLISHED` (or `APPROVED` per workflow) with `approved_by = B`. Approval workflows for stages assigned to B move to `approved` status. |
| SELF-APPROVE-TPRM-RFP-03 | Auto-approve path remains explicitly controlled | Configure an RFP with `auto_approve=true` and submit it for review as User A. Trigger approval via `/approve` and observe behavior. | Auto-approve still works as designed (status moves to `APPROVED`), but usage is documented as an explicit exception to maker–checker (for cases where auto-approval is an intentional business configuration). |
| SELF-APPROVE-TPRM-BCP-01 | Questionnaire creator cannot review their own BCP/DRP questionnaire | Create a BCP/DRP questionnaire as User A (so `created_by_user_id = A`) and assign it for review. Then, as User A, call `PUT questionnaire_review_save_view` (UI or Burp) with any `reviewer_comment`, and optionally try to spoof `reviewer_user_id` in the body. | API returns `403` with a message like **"Self-review is not allowed. Please assign a different reviewer."** `reviewer_comment` and `reviewer_user_id` are not updated for that questionnaire. |
| SELF-APPROVE-TPRM-BCP-02 | Reviewer identity is taken from server-side auth, not client | As a legitimate reviewer User B (different from creator), intercept the questionnaire review save request and change `reviewer_user_id` in the JSON body to some other id (e.g. A or `999`). | API still succeeds (`200`), but the stored `reviewer_user_id` equals User B's authenticated id, **not** the tampered value from the request body. |
| SELF-APPROVE-TPRM-BCP-03 | Normal BCP/DRP review flow with separate reviewer still works | Create a questionnaire as User A and assign User B as reviewer. As User B, submit a valid review comment through the UI without tampering. | API returns `200`; questionnaire `reviewer_comment` is saved and `reviewer_user_id` is set to B. No regression in normal reviewer workflows. |

**Checklist (sign-off):**

- [ ] Creator of an RFP cannot successfully call the RFP approve endpoint for their own RFP (SELF-APPROVE-TPRM-RFP-01).
- [ ] Non-creator reviewers can approve RFPs as expected (SELF-APPROVE-TPRM-RFP-02).
- [ ] Any reliance on `auto_approve` in TPRM is documented as an intentional exception to maker–checker, and still functions as configured (SELF-APPROVE-TPRM-RFP-03).
- [ ] BCP/DRP questionnaire creators cannot save review comments on their own questionnaires; backend enforces creator != reviewer (SELF-APPROVE-TPRM-BCP-01).
- [ ] `reviewer_user_id` for questionnaires is always derived from the authenticated user, not from client-supplied body fields (SELF-APPROVE-TPRM-BCP-02).
- [ ] Normal TPRM questionnaire review flows with distinct creator and reviewer users continue to function without regression (SELF-APPROVE-TPRM-BCP-03).

---

## 24. Self-Approval Controls in TPRM RFP Submodules (RFI / Approval Versions)

**Issue addressed:** In TPRM RFI flows and RFP approval-version workflows, the same user who created an item/version could potentially approve it themselves if the backend does not enforce maker–checker.

**Implementation reference (this repo):**
- RFI approve endpoint: `grc_backend/tprm_backend/rfp/rfi/views.py` (`RFIViewSet.approve`)
- RFP approval versions: `grc_backend/tprm_backend/rfp_approval/views.py` (`approve_version`)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SELF-APPROVE-TPRM-RFI-01 | RFI creator cannot approve their own RFI via `/approve` | Create an RFI as User A (so `created_by = A`). Move it to `IN_REVIEW` normally. Then, as User A, call the RFI approve endpoint (`POST /rfi/<id>/approve/`) via UI or Burp. | API returns `403` with an error like **"Self-approval is not allowed. Please assign a different reviewer to approve this RFI."** `status` and `approved_by` do not change; the RFI is not approved by its creator. |
| SELF-APPROVE-TPRM-RFI-02 | Non-creator reviewer can approve an RFI | Create an RFI as User A and ensure it reaches `IN_REVIEW`. Then login as User B and call the approve endpoint without tampering. | API returns `200` with `"RFI approved"`; `status` becomes `APPROVED` and `approved_by = B`. |
| SELF-APPROVE-TPRM-VERS-01 | Only authorized approvers can mark a version as approved | Identify an approval request version tied to an RFP created by User A. Login as a user B who is allowed to approve (has `approve_rfp` permission) and call `POST /api/tprm/rfp-approval/versions/<version_id>/approve/` (exact path per deployment). | API returns `200` and sets `version.is_approved = True` for that version; normal approver workflows still function. |

**Checklist (sign-off):**

- [ ] RFI creators cannot approve their own RFIs through the RFI approve endpoint (SELF-APPROVE-TPRM-RFI-01).
- [ ] Non-creator users with appropriate permissions can approve RFIs as expected (SELF-APPROVE-TPRM-RFI-02).
- [ ] Approval-version flows (`approve_version`) continue to work correctly for authorized approvers and reflect the right approval state (SELF-APPROVE-TPRM-VERS-01).

---

## 25. Self-Approval Controls in TPRM Audits (Vendor & Contract Audits)

**Issue addressed:** In TPRM vendor audits and contract audits, the same user who is assigned to perform the audit (`assignee_id`) could attempt to approve/reject their own audit via the review endpoints if the backend does not enforce maker–checker.

**Implementation reference (this repo):**
- Vendor audits: `grc_backend/tprm_backend/audits/views.py` (`review_audit`)
- Contract audits: `grc_backend/tprm_backend/audits_contract/views.py` (`review_contract_audit`)
- Audit models: `grc_backend/tprm_backend/audits/models.py` (`Audit.assignee_id`, `review_status`), `grc_backend/tprm_backend/audits_contract/models.py` (`ContractAudit.assignee_id`, `review_status`)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SELF-APPROVE-TPRM-AUDIT-01 | Vendor audit assignee cannot approve their own audit | Create a vendor audit with `assignee_id = A` (User A), complete the questionnaire so status moves to `under_review`, then as User A call `POST /api/tprm/audits/<audit_id>/review/` with body `{ "action": "approve", "comments": "OK" }`. | API returns `403` with an error like **"Self-approval is not allowed. Please assign a different reviewer for this audit."** `review_status` and `status` do not move to approved/completed for that call. |
| SELF-APPROVE-TPRM-AUDIT-02 | Different reviewer can approve a vendor audit | Using the same audit, login as User B (not equal to `assignee_id`) with `PerformContractAudit` permission and call the same review endpoint with `"action": "approve"`. | API returns `200`; audit `status` becomes `completed`, `review_status = approved`, and `completion_date`/`review_date` are set. |
| SELF-APPROVE-TPRM-AUDIT-03 | Vendor audit rejection by assignee is allowed only as rejection, not approval | As User A (assignee), call the review endpoint with `"action": "reject"` instead of approve. | API allows rejection (per business rules) and sets `review_status = rejected`, `status = rejected`; no path lets User A approve their own audit. |
| SELF-APPROVE-TPRM-CAUDIT-01 | Contract audit assignee cannot approve their own contract audit | Create a contract audit with `assignee_id = A` and move it to review. As User A, call `POST /api/tprm/contract-audits/<audit_id>/review/` (or the deployed path) with `"action": "approve"`. | API returns `403` with message like **"Self-approval is not allowed. Please assign a different reviewer for this contract audit."** `status` and `review_status` are unchanged. |
| SELF-APPROVE-TPRM-CAUDIT-02 | Different reviewer can approve a contract audit | As User B (different from `assignee_id`) with the appropriate contract audit permission, call the contract audit review endpoint with `"action": "approve"`. | API returns `200`; contract audit `status` becomes `completed`, `review_status = approved`, and dates are set correctly. |
| SELF-APPROVE-TPRM-CAUDIT-03 | Contract audit rejection by assignee is allowed only as rejection, not approval | As User A (assignee), call the contract audit review endpoint with `"action": "reject"`. | API allows rejection and updates `status`/`review_status` to rejected, but there is no way for User A to approve their own contract audit. |

**Checklist (sign-off):**

- [ ] Vendor audit assignees cannot approve their own audits via `review_audit` (SELF-APPROVE-TPRM-AUDIT-01).
- [ ] Non-assignee reviewers can approve vendor audits as expected (SELF-APPROVE-TPRM-AUDIT-02).
- [ ] Any allowed rejection behavior for vendor audits by the assignee is confirmed and documented; no self-approval path exists (SELF-APPROVE-TPRM-AUDIT-03).
- [ ] Contract audit assignees cannot approve their own audits via `review_contract_audit` (SELF-APPROVE-TPRM-CAUDIT-01).
- [ ] Non-assignee reviewers can approve contract audits as expected (SELF-APPROVE-TPRM-CAUDIT-02).
- [ ] Any allowed rejection behavior for contract audits by the assignee is confirmed and documented; no self-approval path exists (SELF-APPROVE-TPRM-CAUDIT-03).

---

## 26. Self-Approval Controls in TPRM Contracts (Core Contract Approvals)

**Issue addressed:** In TPRM contracts, the same user who owns/created a contract (e.g. `contract_owner`) or created its terms/clauses could potentially also act as the approver via the central contract approval engine (`ContractApproval`), bypassing maker–checker.

**Implementation reference (this repo):**
- Contract approval endpoint: `grc_backend/tprm_backend/contracts/contractapproval/views.py` (`approve_contract`)
- Contract models: `grc_backend/tprm_backend/contracts/models.py` (`VendorContract.contract_owner`, `ContractTerm.created_by`, `ContractClause.created_by`)
- Contract approval model: `grc_backend/tprm_backend/contracts/models.py` (`ContractApproval.assignee_id`, `ContractApproval.approved_date`)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SELF-APPROVE-TPRM-CONTRACT-01 | Contract owner cannot approve their own contract via approval engine | Create a contract where `contract_owner = A` (User A) and have an approval entry in `ContractApproval` assigned to User A (`assignee_id = A`). Move the contract into the state where approval is expected, then as User A call `POST /api/tprm/contracts/approvals/<approval_id>/approve/` (path per deployment). | API returns `403` with an error like **"Self-approval is not allowed. Please assign a different approver for this contract."** Approval `status`/`approved_date` remain unchanged and the contract is not marked approved by its owner. |
| SELF-APPROVE-TPRM-CONTRACT-02 | Only the assigner can approve, and must be different from creator | Configure an approval where `assigner_id = B` and the related contract is owned by User A (`contract_owner = A`). As User C (neither assigner nor owner) call the approve endpoint. | API returns `403` with **"You can only approve contracts you assigned"**; approval is not applied. As User B (assigner, not owner), call the approve endpoint and verify approval succeeds. |
| SELF-APPROVE-TPRM-CONTRACT-03 | Normal approval by non-owner assigner still works | Using the previous setup (`contract_owner = A`, `assigner_id = B`), as User B call the approve endpoint. | API returns `200` with success; `ContractApproval.status = 'APPROVED'`, `approved_date` is set, and the referenced `VendorContract` and its terms/clauses transition to the approved/compliant states as implemented. |

**Checklist (sign-off):**

- [ ] Contract owners cannot approve their own contracts via `approve_contract` in the approval engine (SELF-APPROVE-TPRM-CONTRACT-01).
- [ ] Only the assigner can approve a contract, and they must not be the original contract owner/creator (SELF-APPROVE-TPRM-CONTRACT-02).
- [ ] Normal approval flows where assigner and creator are different users continue to function without regression (SELF-APPROVE-TPRM-CONTRACT-03).

---

## 27. Self-Approval Controls in TPRM SLAs (SLA Approvals)

**Issue addressed:** In TPRM SLAs, the same user who created/owns an SLA could also act as its approver via the SLA approval engine (`SLAApproval`), especially if assigned as `assignee_id`, which would break maker–checker.

**Implementation reference (this repo):**
- SLA approval endpoint: `grc_backend/tprm_backend/slas/slaapproval/views.py` (`approve_sla`)
- SLA approval model: `grc_backend/tprm_backend/slas/slaapproval/models.py` (`SLAApproval.assignee_id`)
- SLA model: `grc_backend/tprm_backend/slas/models.py` (`VendorSLA` — owner/creator field such as `created_by` if present)

| ID | Test case | How to verify | Expected result (pass) |
|----|-----------|---------------|-------------------------|
| SELF-APPROVE-TPRM-SLA-01 | SLA creator/owner cannot approve their own SLA via SLAApproval | Create a Vendor SLA as User A (so the SLA’s owner/creator field maps to A) and generate an `SLAApproval` where `assignee_id = A`. As User A, call `POST /api/tprm/slas/approvals/<approval_id>/approve/` (path per deployment). | API returns `403` with an error like **"Self-approval is not allowed. Please assign a different approver for this SLA."** `SLAApproval.status` and the underlying `VendorSLA` status do not change to approved/active for that call. |
| SELF-APPROVE-TPRM-SLA-02 | Assigned approver who is not creator can approve SLA | For an SLA created by User A, create an `SLAApproval` with `assignee_id = B` (User B). As User B, call the SLA approve endpoint without tampering. | API returns `200`; `SLAApproval.status/approval_status` are set to `APPROVED`, and the SLA moves to `ACTIVE`/`APPROVED` as implemented. |
| SELF-APPROVE-TPRM-SLA-03 | Users with ApproveContract permission can approve SLA but still not if they are the SLA creator | Grant User C the `ApproveContract` permission. For an SLA created by User A, create an approval assigned to User B. As User C, call the approve endpoint. Then repeat with an SLA created by User C. | For the SLA created by A, C can approve (due to permission). For an SLA where C is the creator/owner, the endpoint returns `403` self‑approval error, even though C has `ApproveContract`. |

**Checklist (sign-off):**

- [ ] SLA creators/owners cannot approve their own SLAs via `approve_sla` (SELF-APPROVE-TPRM-SLA-01).
- [ ] Assigned approvers who are not the SLA creators can approve as expected (SELF-APPROVE-TPRM-SLA-02).
- [ ] Global approvers (with `ApproveContract` permission) can approve SLAs they did not create, but are blocked from approving their own SLAs (SELF-APPROVE-TPRM-SLA-03).
