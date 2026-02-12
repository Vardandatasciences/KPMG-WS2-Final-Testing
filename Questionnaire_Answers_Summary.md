# Vardaan Security Architecture and Design Review Questionnaire - Answer Summary

## Application & Deployment Architecture

### Row 1: Documentation & Trust Boundaries
**Question:** Is the application designed using a layered or multi-tier architecture with clearly defined trust boundaries?

**Answer:**
Multi-tier architecture separating client, backend and data layers were clearly defined. However, explicit trust boundaries (e.g. network segmentation, private subnets, firewall rules, security zones) are not documented.

**Detailed Response:**
Yes, the application uses a multi-tier architecture with:
- Presentation Layer (Vue.js frontends for GRC and TPRM)
- API Layer (RESTful APIs with JWT authentication)
- Decorator Layer (RBAC permission checking)
- Business Logic Layer (Core business logic and risk analysis)
- Data Access Layer (Django ORM with multi-database routing)
- Authentication Layer (JWT validation and multi-tenant context)

Trust boundaries exist but need explicit documentation of network segmentation, private subnets, firewall rules, and security zones.

---

### Row 2: Network Segmentation (Application Modules)
**Question:** Are different application modules logically isolated to prevent cross-module risks?

**Answer:**
GRC and TPRM are separate backend modules with separate frontends.

**Detailed Response:**
Yes, modules are logically isolated:
- Separate frontend applications (GRC at `/`, TPRM at `/tprm/`)
- Separate API endpoints (`/api/` for GRC, `/api/tprm/` for TPRM)
- Separate databases (GRC uses `grc2`, TPRM uses `tprm_integration`)
- Database router ensures proper routing
- Tenant isolation middleware prevents cross-tenant data leakage
- RBAC decorators enforce module-specific permissions

---

### Row 3: Network Segmentation (Environments)
**Question:** Are development, staging, and production environments logically and physically separated?

**Answer:**
Separate production, staging, and development environments defined.

**Detailed Response:**
Yes, environments are separated:
- **Production (AWS)**: Domain `riskavaire.vardaands.com`, AWS RDS databases, `ENVIRONMENT = 'aws'`
- **Development/Local**: Localhost configurations, `ENVIRONMENT = 'local'` or `'development'`
- Environment-specific database credentials via environment variables
- Different database hosts and connection strings per environment
- Production deployed on AWS EC2, development can run locally or on separate infrastructure
- Docker containers ensure consistent deployment across environments

---

### Row 4: Data Segregation Control
**Question:** Is data segregation enforced between environments to prevent leakage of production data into non-production systems?

**Answer:**
Yes, data segregation is enforced through separate database instances with environment-specific credentials (Production: AWS RDS, Development: local/separate RDS), all sensitive configuration managed via environment variables with no hardcoded secrets, AWS Secrets Manager for production key management, and tenant isolation middleware that automatically filters all database queries by tenant context.
   - Middleware enforcement logs warnings for requests without tenant context
   - Database router routes different apps to appropriate databases

**Evidence:**
- Multi-tenancy implementation documentation
- Tenant middleware in `grc_backend/grc/tenant_middleware.py` and `grc_backend/tprm_backend/core/tenant_middleware.py`
- Key management in `grc_backend/grc/utils/key_management.py`
- Database configuration in `grc_backend/backend/settings.py`

---

### Row 5: API Gateway/WAF
**Question:** Is a reverse proxy or API gateway used to isolate backend services from direct internet access?

**Answer:**
Yes, Nginx reverse proxy is used to isolate backend services from direct internet access, with backend services running on internal ports (8000) and Nginx proxying `/api/` requests while adding security headers (`X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`), proper client information forwarding (`X-Real-IP`, `X-Forwarded-For`, etc.), and CORS headers configured at proxy level, with Apache as an alternative configuration option.

**Evidence:**
- Nginx configuration: `grc_frontend/nginx-complete.conf`, `grc_frontend/nginx.docker.conf`
- Reverse proxy setup: `nginx-reverse-proxy/nginx.conf`
- Apache alternative: `grc_frontend/tprm_frontend/apache.conf`

---

### Row 6: Traffic Management & Service Mesh Security Control
**Question:** Are load balancers or service meshes implemented to manage traffic securely and efficiently?

**Answer:**
Yes, load balancing and traffic management are implemented through Nginx upstream configuration for `grc_frontend`, `tprm_frontend`, and `backend_api` with Docker container-based upstream servers supporting horizontal scaling, intelligent routing (`/api/` → Backend API, `/tprm/` → TPRM Frontend, `/` → GRC Frontend), timeout management (60-120 seconds), optimized buffering, gzip compression, security headers, and Docker Compose multi-container setup with service discovery, though no dedicated service mesh (Istio, Linkerd) is currently implemented.

**Evidence:**
- Nginx upstream configuration: `nginx-reverse-proxy/nginx.conf`
- Docker compose: `grc_backend/docker-compose.yml`
- Traffic management: `grc_frontend/nginx-complete.conf` and `grc_frontend/nginx.docker.conf`

---

## Summary

All 6 questions in the Application & Deployment Architecture section have been answered. The system demonstrates:

✅ **Layered Architecture**: Multi-tier architecture with clear separation of concerns  
✅ **Module Isolation**: GRC and TPRM modules are logically separated  
✅ **Environment Separation**: Development, staging, and production environments are separated  
✅ **Data Segregation**: Multi-tenant architecture with tenant-based data isolation  
✅ **API Gateway**: Nginx reverse proxy isolates backend services  
✅ **Traffic Management**: Load balancing and traffic management via Nginx upstream configuration

---

## Authentication & Account Management

### Row 1: Strong Authentication Mechanisms
**Question:** Are strong authentication mechanisms implemented?

**Answer:**
Yes, strong authentication mechanisms are implemented including JWT-based authentication with access and refresh tokens, password hashing using Django's PBKDF2 algorithm, MFA with OTP sent via email, Google SSO support, and session-based authentication with secure session management.

---

### Row 2: MFA Enforcement
**Question:** Is MFA enforcement mandatory for administrators and external users?

**Answer:**
MFA is enabled by default (`MFA_ENABLED = 'true'`) and applies to all users when enabled, with OTP sent via email for verification, though it can be disabled via environment variable and is not specifically differentiated between administrators and external users.

---

### Row 3: Token Lifetimes
**Question:** Are access and refresh token lifetimes clearly defined?

**Answer:**
Yes, token lifetimes are clearly defined with access token lifetime of 1 hour (3600 seconds) and refresh token lifetime of 7 days (604800 seconds) configured in `backend/settings.py`, with alternative configurations supporting 3-day access tokens and 7-day refresh tokens in authentication modules.

---

### Row 4: Refresh Token Rotation and Revocation
**Question:** Is refresh token rotation and revocation supported?

**Answer:**
Yes, refresh token rotation and revocation are supported with `ROTATE_REFRESH_TOKENS = True` and `BLACKLIST_AFTER_ROTATION = True` configured, where old refresh tokens are automatically blacklisted when new tokens are issued, preventing token reuse and ensuring security.

---

### Row 5: Brute-Force Protection
**Question:** Is brute-force protection implemented for authentication endpoints?

**Answer:**
Yes, brute-force protection is implemented with rate limiting of 10 login attempts per minute per IP address, account lockout after 5 failed attempts per username (15-minute lockout period), failed login attempts logged to `grc_logs` table with IP address and attempt count, and rate limiting middleware for additional protection.

---

### Row 6: CAPTCHA Protection
**Question:** Is CAPTCHA or equivalent control used to mitigate automated login attacks?

**Answer:**
Yes, reCAPTCHA is implemented and verified on the backend before login processing, with CAPTCHA token required for username/userid login (not required for Google SSO), verification against Google's reCAPTCHA API, and frontend integration with Google reCAPTCHA widget.

---

### Row 7: Password Policies
**Question:** Are password policies defined and enforced (complexity, expiration, reuse prevention)?

**Answer:**
Yes, password policies are enforced with minimum 8 characters requiring uppercase, lowercase, number, and special character, password expiration checked on login with forced reset for expired passwords (default 90 days), and password reuse prevention checking the last 3-5 passwords to prevent reuse of recent passwords.

---

### Row 8: Identity Lifecycle Management
**Question:** Is identity lifecycle management defined (provisioning, de-provisioning, suspension)?

**Answer:**
Yes, identity lifecycle management is defined with user provisioning through admin interfaces and API endpoints, user de-provisioning via `IsActive` status update (admin-only), account suspension through status change to 'N', tenant-level activation/suspension support, and user status management endpoints with RBAC permission checks.

---

### Row 9: Authentication Log Monitoring
**Question:** Are authentication logs monitored for anomalies (e.g., failed login attempts, unusual geolocation)?

**Answer:**
Yes, failed login attempts are logged to `grc_logs` table with IP address, username, attempt count, and reason, with rate limiting (5 failed attempts triggers account lockout, 10 attempts per IP per minute), though specific geolocation monitoring and automated anomaly detection alerts are not currently implemented.

---

### Row 10: Inactive Account Management
**Question:** Are inactive or stale accounts automatically disabled or flagged for review?

**Answer:**
Yes, inactive account management is implemented with a management command `deactivate_inactive_users` that automatically deactivates users who haven't logged in for a specified number of days (default 90 days), configurable inactivity threshold via `USER_INACTIVITY_DAYS` setting, and support for dry-run mode to preview users that would be deactivated.

---

## Session Management

### Row 1: Session Hijacking Prevention
**Question:** Is session hijacking prevention implemented to prevent attackers from stealing or reusing session identifiers to impersonate users (e.g., secure cookie flags, token binding)?

**Answer:**
Yes, session hijacking prevention is implemented through secure cookie attributes (HttpOnly, Secure, SameSite flags configured per environment), JWT tokens with session tokens stored in cache for validation, refresh token rotation with blacklisting to prevent token reuse, and session timeout middleware that automatically invalidates expired sessions, though token binding to specific IP addresses is not currently implemented.

---

### Row 2: Session-Based Authentication
**Question:** Is session-based authentication used in addition to token-based authentication?

**Answer:**
Yes, session-based authentication is used alongside JWT token-based authentication, with Django session middleware enabled (`django.contrib.sessions.middleware.SessionMiddleware`), database-backed sessions (`SESSION_ENGINE = 'django.contrib.sessions.backends.db'`), user information stored in session for compatibility, and both authentication methods supported for different use cases.

---

### Row 3: Session Lifetimes
**Question:** Are session lifetimes explicitly configured?

**Answer:**
Yes, session lifetimes are explicitly configured via environment variables (`SESSION_TIMEOUT_ENABLED` and `SESSION_TIMEOUT_SECONDS`), with session cookie age matching timeout duration (`SESSION_COOKIE_AGE = SESSION_TIMEOUT_SECONDS`), configurable timeout enforced by `SessionTimeoutMiddleware`, and session expiration checked on each request with automatic logout when timeout is exceeded.

---

### Row 4: Secure Cookie Attributes
**Question:** Are secure cookie attributes enforced for sessions in production (Secure, HttpOnly, SameSite)?

**Answer:**
Yes, secure cookie attributes are enforced with `SESSION_COOKIE_SECURE = True` in production (enabled when `DEBUG = False`), `SESSION_COOKIE_HTTPONLY = True` to prevent JavaScript access, `SESSION_COOKIE_SAMESITE = 'Strict'` in production for CSRF protection, and `CSRF_COOKIE_SECURE = True` and `CSRF_COOKIE_HTTPONLY = True` in production, though development settings allow JavaScript access for SPA compatibility.

---

### Row 5: CSRF Protections
**Question:** Are CSRF protections enabled?

**Answer:**
Yes, CSRF protections are enabled through Django's `CsrfViewMiddleware` in the middleware stack, CSRF trusted origins configured for allowed domains, CSRF tokens required for state-changing operations, and frontend CSRF protection utilities that extract and include CSRF tokens in requests, though some API endpoints use `@csrf_exempt` decorator for specific use cases.

---

### Row 6: Session Identifier Regeneration
**Question:** Are session identifiers regenerated after login?

**Answer:**
Session identifiers are managed through Django's session framework which handles session key generation, with new session data created on successful login including user information and session creation timestamp, though explicit session key regeneration via `request.session.cycle_key()` is not currently implemented in the login flow.

---

### Row 7: CORS Origins Restriction
**Question:** Are CORS origins restricted to trusted domains to prevent unauthorized domains from making authenticated requests?

**Answer:**
Yes, CORS origins are restricted to trusted domains through `CORS_ALLOWED_ORIGINS` configuration listing specific domains (production domain `riskavaire.vardaands.com`, development localhost variants, and deployment IPs), with `CORS_ALLOW_ALL_ORIGINS = True` only in development mode, `CORS_ALLOW_CREDENTIALS = True` for authenticated requests, and `CSRF_TRUSTED_ORIGINS` configured to match CORS allowed origins.

---

### Row 8: Idle Session Timeouts
**Question:** Are idle session timeouts enforced (automatic logout after inactivity)?

**Answer:**
Yes, idle session timeouts are enforced through `SessionTimeoutMiddleware` that checks session age on each request, configurable timeout duration via `SESSION_TIMEOUT_SECONDS` environment variable, automatic logout when timeout is exceeded with session flush and deletion, frontend session timeout service with warning popup before expiration, and session timer reset on activity to extend session.

---

### Row 9: Concurrent Session Management
**Question:** Are concurrent sessions for the same user monitored or restricted?

**Answer:**
Concurrent session management infrastructure exists with `UserSession` model tracking sessions (IP address, user agent, created_at, last_activity), session token storage in cache for multi-session validation, though multi-session enforcement is currently disabled (users can stay logged in across multiple locations), and session tracking available for audit purposes but not actively restricting concurrent sessions.

---

### Row 10: Session Invalidation on Logout
**Question:** Is session invalidation on logout implemented to ensure tokens and sessions cannot be reused after logout?

**Answer:**
Yes, session invalidation on logout is implemented through `jwt_logout` endpoint that clears session data via `request.session.flush()`, session token invalidation in cache via `_invalidate_user_session()`, refresh token blacklisting when rotation is enabled, logout events logged to `grc_logs` table for audit trail, and frontend token removal from localStorage/sessionStorage on logout.

---

## Authorization & Access Control

### Row 1: Server-Side RBAC Enforcement
**Question:** Is RBAC enforced server-side (to ensure authorization cannot be bypassed at the client level)?

**Answer:**
Yes, RBAC is enforced server-side through decorators (`@rbac_required`, `@rbac_module_required`) and permission classes (`BasePolicyPermission`, `RFPPermission`, `RBACPermission`) that check permissions on the backend before processing requests, with all authorization checks performed server-side using database-backed RBAC tables (`rbac` for GRC, `rbac_tprm` for TPRM), and frontend permission checks are disabled/for UI only with server-side validation as the source of truth.

---

### Row 2: Object-Level Authorization (IDOR Prevention)
**Question:** Is object-level authorization implemented to prevent Insecure Direct Object Reference (IDOR) attacks, which could allow unauthorized access to sensitive records?

**Answer:**
Yes, object-level authorization is implemented through tenant isolation middleware that automatically filters database queries by `tenant_id`, object permission checks in DRF viewsets (`has_object_permission` methods), tenant access validation utilities (`validate_tenant_access`) that verify user access to specific objects, and contract audit detail permissions that check if user is assignee, auditor, or reviewer before allowing access to specific audit objects.

---

### Row 3: API Layer Permission Enforcement
**Question:** Are permissions consistently enforced at the API layer, ensuring that every endpoint validates user roles and privileges?

**Answer:**
Yes, permissions are consistently enforced at the API layer through RBAC decorators applied to view functions (`@rbac_required`, `@rbac_module_required`), DRF permission classes (`BasePermission` subclasses) that check permissions before view execution, permission mapping that maps HTTP methods to required permissions (GET→view, POST→create, PUT/PATCH→edit, DELETE→delete), and consistent 403 Forbidden responses when permissions are denied, though some endpoints may have `@csrf_exempt` for specific use cases while still enforcing RBAC.

---

### Row 4: Development Authorization Bypasses
**Question:** Are development-only authorization bypasses present, and if so, are they disabled in production to prevent accidental exposure of sensitive functions?

**Answer:**
Yes, development-only authorization bypasses are present with `RBAC_DECORATOR_BYPASS = True` in settings for development, `RBAC_CONFIG['ENABLE_RBAC'] = False` temporarily disabled, frontend permission checks bypassed (returning `true` always) with TODO comments to re-enable, and `VendorAccessControlMiddleware` that bypasses permission checks for development, though these should be disabled in production via environment variables and `DEBUG = False` settings.

---

### Row 5: Least Privilege Enforcement
**Question:** Is least privilege enforced, ensuring users and services only have the minimum permissions required for their roles?

**Answer:**
Yes, least privilege is enforced through granular boolean permission flags in RBAC tables (100+ permission fields per user), role-based permission assignment where users only receive permissions for their specific role, module-specific access checks that verify users have access to specific modules before allowing operations, and permission inheritance through roles with explicit permission flags rather than broad access grants, though default permission values are `False` requiring explicit assignment.

---

### Row 6: Authorization Consistency Across Modules
**Question:** Is authorization consistent across all modules, preventing discrepancies that could allow privilege escalation between different application components?

**Answer:**
Yes, authorization is consistent across modules with separate but similar RBAC systems for GRC (`rbac` table) and TPRM (`rbac_tprm` table) using the same decorator pattern, consistent permission checking utilities (`RBACUtils` for GRC, `RBACTPRMUtils` for TPRM), module-specific decorators (`@rbac_module_required`) that enforce module boundaries, and tenant isolation middleware that prevents cross-tenant access across all modules, though the two systems use different database tables and permission schemas.

---

### Row 7: HTTP Response Security Headers
**Question:** Are HTTP response security headers centrally enforced at the application or web server layer, to mitigate common web attacks (XSS, clickjacking, MIME sniffing)?

**Answer:**
Yes, HTTP response security headers are centrally enforced through `EnterpriseSecurityHeadersMiddleware` that adds comprehensive security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`), Nginx configuration adding security headers at reverse proxy level, `VendorSecurityMiddleware` and `SecurityHeadersMiddleware` in TPRM modules, and Content-Security-Policy headers configured in multiple middleware layers for defense-in-depth.

---

### Row 8: Administrative Functions Isolation
**Question:** Are administrative functions isolated from regular user functions, ensuring that privileged operations are accessible only through secure, restricted interfaces?

**Answer:**
Yes, administrative functions are isolated through `@rbac_admin_required` decorator that checks for administrator privileges, `is_user_administrator()` helper functions that verify admin roles from RBAC tables, admin-only endpoints for user status updates and tenant management, role-based checks that verify users have 'GRC Administrator' or 'Administrator' roles before allowing privileged operations, and separate admin access control middleware that restricts administrative endpoints.

---

### Row 9: Authorization Decision Logging
**Question:** Are authorization decisions logged and monitored, to detect suspicious privilege use or abuse?

**Answer:**
Yes, authorization decisions are logged through `log_permission_access()` function that logs both granted and denied access attempts with endpoint name, user ID, and reason, permission checks logged in decorators with warning/info levels for denied/granted access, audit logging middleware (`AuditLoggingMiddleware`, `VendorLoggingMiddleware`) that logs security events, and `GRCLog` table storing authorization-related events, though automated anomaly detection alerts for suspicious privilege use are not currently implemented.

---

## API & Integration Security

### Row 1: API Authentication and Authorization
**Question:** Are APIs protected using authentication and authorization controls (to ensure only legitimate users and services can access sensitive endpoints)?

**Answer:**
Yes, APIs are protected through JWT authentication middleware (`JWTAuthenticationMiddleware`) that verifies tokens on all requests, RBAC decorators (`@rbac_required`, `@rbac_module_required`) that enforce permissions before endpoint execution, DRF permission classes (`BasePermission` subclasses) that validate user roles, and explicit skip lists for public endpoints (login, registration, OAuth callbacks) with all other endpoints requiring authentication.

---

### Row 2: Public API Minimization
**Question:** Are public APIs minimized (to reduce the attack surface and prevent accidental exposure of sensitive functionality)?

**Answer:**
Public APIs are minimized with explicit skip paths defined in `JWTAuthenticationMiddleware` for authentication endpoints (`/api/login/`, `/api/register/`, `/api/jwt/login/`), OAuth callbacks (`/api/google/oauth-callback/`, `/api/jira/oauth-callback/`), password reset flows (`/api/reset-password/`, `/api/send-otp/`), and public read-only endpoints (`/api/frameworks/approved-active/`, `/api/compliance/frameworks/public/`), with all other endpoints requiring authentication, though some integration endpoints may be temporarily public for development.

---

### Row 3: API Usage Limits
**Question:** Are API usage limits enforced to prevent abuse (e.g., brute force, denial-of-service, or resource exhaustion attacks)?

**Answer:**
Yes, API usage limits are enforced through DRF throttling classes (`AnonRateThrottle: 100/hour`, `UserRateThrottle: 1000/hour`), custom rate limiting middleware (`VendorRateLimitMiddleware`) with burst protection and lockout mechanisms, request queuing utilities (`request_queue.py`) that limit concurrent requests per user/IP, and per-endpoint rate limiting in authentication flows (10 login attempts per minute per IP, 5 failed attempts per username triggers 15-minute lockout).

---

### Row 4: OAuth Redirect and Callback Endpoints
**Question:** Are OAuth redirect and callback endpoints explicitly defined (to prevent open redirect vulnerabilities and unauthorized redirection)?

**Answer:**
Yes, OAuth redirect and callback endpoints are explicitly defined with dedicated callback URLs (`/api/google/oauth-callback/`, `/api/jira/oauth-callback/`, `/api/bamboohr/oauth-callback/`), redirect URIs configured in settings (`GOOGLE_REDIRECT_URI`, `JIRA_REDIRECT_URI`, `BAMBOOHR_REDIRECT_URI`) with environment-specific values, state parameter validation to prevent CSRF attacks, and redirect URIs validated against whitelist before OAuth flow initiation, though redirect validation could be strengthened to prevent open redirects.

---

### Row 5: Error Message Sanitization
**Question:** Are error messages sanitized (to avoid leaking sensitive information such as stack traces, database details, or internal logic to attackers)?

**Answer:**
Yes, error messages are sanitized through custom exception handlers (`vendor_custom_exception_handler`) that provide generic error messages in production, `SecureOutputEncoder.sanitize_error_message()` that removes sensitive patterns (passwords, tokens, secrets, database details), debug mode checks that only show detailed errors when `DEBUG = True`, and sanitized error responses that hide stack traces, database connection strings, and internal file paths from production responses.

---

### Row 6: API Versioning
**Question:** Are APIs versioned (to ensure backward compatibility, controlled deprecation and secure migration)?

**Answer:**
API versioning is implemented through product versioning model (`ProductVersion`) that tracks active, deprecated, and blocked versions, version-based enforcement for policy and compliance objects with major/minor version calculation, contract versioning with versioned contract numbers (`contract_number-v1.0`), and framework versioning with version history tracking, though REST API URL versioning (e.g., `/api/v1/`, `/api/v2/`) is not currently implemented in the URL structure.

---

### Row 7: Input Validation
**Question:** Is input validation documented and enforced (to prevent injection attacks, malformed requests, and ensure data integrity)?

**Answer:**
Yes, input validation is enforced through `VendorInputValidationMiddleware` that validates and sanitizes all incoming request data, Django ORM parameterized queries that prevent SQL injection, input validation utilities (`validate_contract_data`, `validate_incident_data`, `validate_tailored_framework_data`) that check for SQL injection patterns and validate JSON fields, regex pattern validation for safe text inputs, and context-appropriate encoding (HTML escaping, shell quoting) based on output context.

---

### Row 8: OAuth Callback Validation
**Question:** Are OAuth callbacks validated for authenticity (to prevent attackers from hijacking the OAuth flow and redirecting tokens to malicious endpoints)?

**Answer:**
Yes, OAuth callbacks are validated through state parameter verification that compares received state with session-stored state to prevent CSRF attacks, redirect URI validation against configured whitelist before token exchange, authorization code validation before token exchange, and session-based state storage with explicit session save to persist state across redirects, though some OAuth implementations have optional state verification bypass for development (`SKIP_OAUTH_STATE_VERIFICATION`).

---

### Row 9: Replay Attack Protection
**Question:** Are APIs protected against replay attacks (e.g., using nonce, timestamp validation, or signature verification)?

**Answer:**
Replay attack protection is implemented through JWT token expiration (access tokens expire after 1 hour, refresh tokens after 7 days), refresh token rotation with blacklisting that prevents reuse of old tokens, timestamp validation in JWT tokens (`exp` claim) that automatically rejects expired tokens, and session token validation that checks token validity on each request, though explicit nonce-based replay protection and request signature verification are not currently implemented for all endpoints.

---

### Row 10: Third-Party Integration Authentication
**Question:** Are third-party integrations authenticated and authorized (to ensure external services cannot misuse APIs)?

**Answer:**
Yes, third-party integrations are authenticated through OAuth flows for external services (Google, Jira, BambooHR, Sentinel) with client ID/secret validation, integration-specific authentication endpoints (`/api/jira/oauth/`, `/api/bamboohr/oauth/`) that require user authentication before initiating OAuth, stored connection tokens encrypted in database with access control, and `ExternalApplicationConnection` model that tracks authenticated integrations per user with token expiration management, though some integration endpoints may temporarily allow unauthenticated access for development.

---

### Row 11: API Monitoring and Logging
**Question:** Are APIs monitored and logged (to detect anomalies, unauthorized access attempts, or abuse patterns)?

**Answer:**
Yes, APIs are monitored and logged through `RequestLoggingMiddleware` that logs all API requests with method, path, and status code, `VendorLoggingMiddleware` that provides comprehensive audit logging with security context (IP address, user ID, action type), failed authentication attempts logged to `grc_logs` table with IP address and attempt count, rate limiting violations logged with warning levels, and authorization decisions logged through `log_permission_access()` function, though automated anomaly detection and real-time alerting for abuse patterns are not currently implemented.

---

## Data Protection & Privacy

### Row 1: Managed Database Security
**Question:** Is sensitive data stored in managed databases (to ensure vendor-provided security controls, patching, and compliance certifications are leveraged)?

**Answer:**
Yes, sensitive data is stored in managed AWS RDS MySQL databases (`grc2` for GRC, `tprm_integration` for TPRM) hosted on AWS RDS, which provides automated backups, automated patching, encryption capabilities, network isolation through VPCs, and compliance certifications (SOC, ISO, PCI DSS), with database credentials managed via environment variables and connection health checks enabled.

---

### Row 2: Data Segregation Between Modules
**Question:** Is data logically segregated between modules (to prevent cross-module data leakage and enforce least privilege access)?

**Answer:**
Yes, data is logically segregated between modules through separate database instances (GRC uses `grc2`, TPRM uses `tprm_integration`), database router (`TPRMDatabaseRouter`) that automatically routes TPRM apps to TPRM database, separate database credentials per module, and tenant isolation middleware that filters all queries by `tenant_id` to prevent cross-tenant data access, though both modules share the same database engine (MySQL) and may share some infrastructure.

---

### Row 3: Encryption at Rest for Databases
**Question:** Is encryption at rest enabled for databases (to protect sensitive data if storage media is compromised)?

**Answer:**
Yes, encryption at rest is implemented through field-level encryption using `EncryptedFieldsMixin` that automatically encrypts sensitive fields (emails, phone numbers, addresses, names, tokens) before saving to database, Fernet symmetric encryption (AES-128 in CBC mode) with Base64 URL-safe encoding, encryption keys managed via environment variables (`TPRM_ENCRYPTION_KEY`) with AWS Secrets Manager support for production, and automatic decryption on retrieval through serializers, though AWS RDS encryption at the storage layer should also be enabled for additional protection.

---

### Row 4: Database Public Accessibility
**Question:** Is the database publicly accessible, and what are the network exposure details (to ensure databases are not exposed directly to the internet)?

**Answer:**
Databases are not publicly accessible and are hosted on AWS RDS within VPCs with security groups restricting access to application servers only, database hosts configured via environment variables (`DB_HOST`, `TPRM_DB_HOST`) pointing to RDS endpoints (e.g., `tprmintegration.c1womgmu83di.ap-south-1.rds.amazonaws.com`), connection timeouts and health checks configured, and database credentials stored securely in environment variables, though explicit documentation of security group rules and VPC configuration would strengthen the response.

---

### Row 5: Object Storage Access Controls
**Question:** Is object storage used for document data, and are appropriate access controls applied (to prevent unauthorized access to files)?

**Answer:**
Yes, AWS S3 is used for object storage with AWS credentials stored in `AWSCredentials` model (encrypted fields), S3 bucket configuration via environment variables (`AWS_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), file upload functions that use boto3 S3 client with proper content type and disposition headers, and S3 file references stored in `FileOperations` and `S3Files` models, though explicit S3 bucket policies, IAM roles, and public access block settings should be documented to demonstrate access control enforcement.

---

### Row 6: Tenant Isolation
**Question:** Is tenant isolation documented and enforced (to prevent one tenant's data from being accessed by another in multi-tenant environments)?

**Answer:**
Yes, tenant isolation is documented and enforced through `TenantContextMiddleware` that extracts tenant from authenticated user and sets tenant context on all requests, `TenantIsolationMiddleware` that validates tenant context is present for authenticated requests and logs warnings for missing context, automatic tenant filtering in database queries via `@tenant_filter` decorator that adds `tenant_id` to all queries, `validate_tenant_access()` utilities that verify user access to specific tenant objects, and comprehensive documentation in `TPRM_MULTITENANCY_IMPLEMENTATION.md` explaining the multi-tenant architecture.

---

### Row 7: Database-Level Access Controls
**Question:** Are database-level access controls enforced (to restrict queries and operations based on user roles)?

**Answer:**
Yes, database-level access controls are enforced through database router (`TPRMDatabaseRouter`) that routes different apps to appropriate databases, tenant-based filtering that automatically adds `tenant_id` to all queries preventing cross-tenant access, Django ORM parameterized queries that prevent SQL injection, application-level RBAC that restricts operations based on user roles before database queries, and database user credentials with least privilege access (application users only, not admin), though database user role-based access control (GRANT/REVOKE) at the MySQL level is not explicitly documented.

---

### Row 8: JWT Token Storage Security
**Question:** Are JWT tokens stored securely?

**Answer:**
JWT tokens are stored in browser storage (localStorage and sessionStorage) with access tokens stored in `localStorage` (`access_token`, `token`, `session_token` keys) and refresh tokens stored in `sessionStorage` for some implementations, though browser storage is vulnerable to XSS attacks and tokens should ideally be stored in httpOnly cookies or memory-only storage, with token expiration enforced (1 hour for access tokens, 7 days for refresh tokens) and token rotation with blacklisting implemented to mitigate risks of stored tokens.

---

### Row 9: Data Retention and Deletion Policies
**Question:** Are data retention and deletion policies defined (to comply with GDPR, HIPAA, and other privacy regulations)?

**Answer:**
Yes, data retention and deletion policies are defined through `RetentionTimeline` model that tracks retention periods per record with status (Active, Expired, Disposed, Archived, Paused), `RetentionModulePageConfig` model that configures retention policies per module, `delete_expired_records` management command that automatically deletes records whose retention period has expired (when `auto_delete_enabled=True` and not paused/archived), data subject request endpoints for GDPR compliance, and retention expiry dates stored on records (e.g., `retentionExpiry` field on Policy, Framework models), though specific retention periods per data category should be explicitly documented.

---

### Row 10: Data Masking and Anonymization
**Question:** Is sensitive data masked or anonymized in non-production environments (to prevent leakage during testing or development)?

**Answer:**
Yes, data masking and anonymization capabilities are implemented through `DataMaskingService` that provides email masking, phone masking, address masking, name masking, and user ID pseudonymization, anonymization API endpoints (`/api/anonymize/logs/`, `/api/anonymize/data/`) that allow administrators to anonymize sensitive data, masking functions that preserve data format while hiding sensitive information (e.g., `jo**@example.com` for emails), and reversible pseudonymization for user IDs using secure hashing, though automatic masking of production data when copied to non-production environments is not currently implemented and should be considered.

---

## Cryptography & Key Management

### Row 1: Cryptographic Keys Configuration
**Question:** Are cryptographic keys configurable via secure configuration?

**Answer:**
Yes, cryptographic keys are configurable via secure configuration through `EnterpriseKeyManager` that supports multiple backends (AWS Secrets Manager for production, environment variables for staging/development, file-based for local development only), encryption keys loaded from environment variables (`GRC_ENCRYPTION_KEY`, `TPRM_ENCRYPTION_KEY`, `JWT_SECRET_KEY`) with fallback to Django `SECRET_KEY` for development, and keys never stored in code or configuration files, with backend priority order ensuring most secure backend is used first.

---

### Row 2: Centralized Key Management Service
**Question:** Is a centralized key management service documented (to provide secure storage, rotation, and auditing of keys instead of relying on local or ad-hoc storage)?

**Answer:**
Yes, a centralized key management service is documented and implemented through `AWSSecretsManagerBackend` that integrates with AWS Secrets Manager for production environments, `EnterpriseKeyManager` class that provides unified interface for key management with multiple backends, key management system documented in `grc_backend/grc/utils/key_management.py` with support for secure storage, retrieval, and rotation, and AWS Secrets Manager providing encryption at rest, access control via IAM, automatic rotation capabilities, and audit logging, though explicit key rotation schedules and audit logging procedures should be documented.

---

### Row 3: Cryptographic Algorithms
**Question:** Are cryptographic algorithms explicitly defined and aligned with industry best practices?

**Answer:**
Yes, cryptographic algorithms are explicitly defined with JWT using HS256 (HMAC-SHA256) algorithm configured in `JWT_ALGORITHM = 'HS256'` across all authentication modules, data encryption using Fernet symmetric encryption (AES-128 in CBC mode) with Base64 URL-safe encoding for field-level encryption, password hashing using Django's PBKDF2 algorithm with SHA-256, and OTP hashing using SHA-256 for MFA challenges, though consideration should be given to upgrading to RS256 for JWT in high-security scenarios and AES-256 for data encryption.

---

### Row 4: Key Rotation
**Question:** Is key rotation documented and enforced (to limit the impact of compromised keys and meet compliance requirements for periodic rotation)?

**Answer:**
Yes, key rotation is supported through `DataEncryptionService` that supports multiple encryption keys in priority order (comma-separated `GRC_ENCRYPTION_KEYS` environment variable) allowing new keys to be added while old keys remain for decryption, refresh token rotation enabled (`ROTATE_REFRESH_TOKENS = True`) with blacklisting of old tokens after rotation, and AWS Secrets Manager backend supporting automatic key rotation for secrets stored in Secrets Manager, though explicit key rotation schedules, procedures, and compliance requirements documentation should be formalized.

---

### Row 5: RBAC for Encryption Keys
**Question:** Are encryption keys protected with role-based access controls (to ensure only authorized services and personnel can access them)?

**Answer:**
Encryption keys are protected through AWS Secrets Manager IAM policies that restrict access to secrets based on IAM roles and policies, environment variable access restricted to application processes and system administrators, and key management operations logged through `EnterpriseKeyManager` with backend-specific logging, though explicit RBAC documentation for key access, separation of duties for key management operations, and audit trails for key access should be formalized to demonstrate role-based access control enforcement.

---

### Row 6: Keys Encrypted at Rest and in Transit
**Question:** Are keys encrypted at rest and in transit (to prevent interception or theft during storage or transmission)?

**Answer:**
Yes, keys are encrypted at rest and in transit through AWS Secrets Manager encrypting secrets at rest using AWS KMS (Key Management Service), HTTPS/TLS used for all key retrieval operations from AWS Secrets Manager and environment variable transmission, database credentials and API keys stored in environment variables with filesystem permissions restricting access, and application-to-database connections using encrypted connections (MySQL SSL/TLS), though explicit documentation of encryption in transit for all key transmission paths would strengthen the response.

---

### Row 7: Key Revocation Process
**Question:** Is there a process for revoking compromised keys immediately (to prevent continued misuse if a key is exposed)?

**Answer:**
Key revocation capabilities exist through AWS Secrets Manager that allows immediate deletion or rotation of compromised secrets, refresh token blacklisting that immediately invalidates compromised refresh tokens when rotation is enabled, and environment variable updates that can be changed to revoke access, though explicit key revocation procedures, incident response playbooks for compromised keys, automated alerting for key compromise detection, and documentation of revocation timelines should be formalized.

---

### Row 8: Cryptographic Library Updates
**Question:** Are cryptographic libraries and dependencies regularly updated (to patch vulnerabilities in underlying crypto implementations)?

**Answer:**
Yes, cryptographic libraries are managed through `requirements.txt` files that specify version constraints for crypto libraries (`cryptography>=41.0.7`, `PyJWT>=2.8.0`, `bcrypt>=4.1.2`), dependency management via pip with version pinning for security-critical packages, and library versions tracked in requirements files for both GRC and TPRM backends, though automated dependency scanning, vulnerability monitoring (e.g., Dependabot, Snyk), and documented update procedures for crypto libraries should be implemented to ensure timely patching of vulnerabilities.

---

## Secure Configuration & Secrets Management

### Row 1: Hardcoded Secrets
**Question:** Are any secrets, API keys, or credentials hardcoded in the application codebase?

**Answer:**
No, secrets are not hardcoded in production code with security warnings in `settings.py` files explicitly stating "DO NOT hardcode any secrets, API keys, passwords, or tokens", all sensitive values loaded from environment variables (`os.environ.get()`) with fallback to development-only defaults, and `.env` files used for local development with `.gitignore` preventing commit of secrets, though some development configuration files may contain example credentials that should be excluded from production deployments.

---

### Row 2: Secrets Rotation Policy
**Question:** Are secrets rotated regularly, and what is the defined rotation policy?

**Answer:**
Secrets rotation is supported through AWS Secrets Manager that provides automatic rotation capabilities for secrets stored in Secrets Manager, refresh token rotation enabled (`ROTATE_REFRESH_TOKENS = True`) with automatic blacklisting of old tokens, and multi-key encryption support in `DataEncryptionService` that allows adding new encryption keys while maintaining old keys for decryption, though explicit rotation schedules (e.g., quarterly, annually), documented rotation procedures, and compliance-driven rotation requirements should be formalized.

---

### Row 3: Centralized Secrets Manager
**Question:** Is a centralized secrets manager (e.g., AWS Secrets Manager, Azure Key Vault, HashiCorp Vault) used for managing secrets instead of environment variables (to provide encryption, access control, rotation, and audit logging)?

**Answer:**
Yes, a centralized secrets manager is implemented through `AWSSecretsManagerBackend` that integrates with AWS Secrets Manager for production environments, `EnterpriseKeyManager` that provides unified interface with multiple backends (AWS Secrets Manager for production, environment variables for staging/development, file-based for local development only), AWS Secrets Manager providing encryption at rest via AWS KMS, IAM-based access control, automatic rotation capabilities, and audit logging, though production deployments should ensure `USE_AWS_SECRETS_MANAGER = True` is configured to use the centralized service.

---

### Row 4: Environment-Specific Configuration Separation
**Question:** Are environment-specific configurations stored separately and securely (to prevent accidental leakage of production secrets into development or staging environments)?

**Answer:**
Yes, environment-specific configurations are stored separately through different database instances per environment (Production: AWS RDS endpoints, Development: localhost or separate RDS), environment-specific credentials loaded via environment variables (`DB_HOST`, `DB_USER`, `DB_PASSWORD` for production vs development), separate `.env` files per environment with `.gitignore` preventing commit, `ENVIRONMENT` variable distinguishing environments (`'aws'` for production, `'local'` for development), and AWS Secrets Manager used for production secrets while environment variables used for development, ensuring no production secrets in development configurations.

---

### Row 5: Secrets in Logs and Error Messages
**Question:** Are secrets prevented from appearing in logs or error messages?

**Answer:**
Yes, secrets are prevented from appearing in logs through `VendorLoggingMiddleware` that sanitizes sensitive fields (passwords, tokens, secrets, API keys, encryption keys) before logging, `SecureOutputEncoder.sanitize_error_message()` that removes sensitive patterns (password, token, secret, key, auth, session, database, SQL) from error messages, custom exception handlers (`vendor_custom_exception_handler`) that provide generic error messages in production without sensitive details, and data masking service (`mask_log_data()`) that masks sensitive information in log entries before saving to database, though comprehensive testing should verify all logging paths sanitize secrets.

---

### Row 6: Secrets Encryption and Access Controls
**Question:** Are secrets encrypted at rest and in transit? Are access controls enforced for secrets? Is there a process for immediate revocation of compromised secrets?

**Answer:**
Yes, secrets are encrypted and protected through AWS Secrets Manager encrypting secrets at rest using AWS KMS, HTTPS/TLS used for all secret retrieval operations from AWS Secrets Manager, IAM policies restricting access to secrets based on roles and policies, environment variables stored with filesystem permissions restricting access, and AWS Secrets Manager allowing immediate deletion or rotation of compromised secrets, though explicit documentation of access control policies, revocation procedures, incident response playbooks for compromised secrets, and automated alerting for unauthorized access attempts should be formalized.

---

## Logging, Monitoring & Incident Response

### Row 1: Authentication & Activity Logging
**Question:** Are authentication events and user actions logged consistently across the application?

**Answer:**
Yes, authentication events and user actions are logged consistently through `AuditLoggingMiddleware` that logs all API requests with user context, `MfaAuditLog` model that tracks MFA challenge events (issued, success, failure) with IP address and user agent, `GRCLog` model that records user actions across modules (Compliance, Policy, Audit, Risk, Incident) with action type and entity details, `VendorAuditLog` model for TPRM vendor actions, and `send_log()` utility function used throughout the application to create standardized log entries with user ID, IP address, and action details.

---

### Row 2: Immutable Audit Trails
**Question:** Is a complete audit trail maintained for critical operations?

**Answer:**
Yes, a complete audit trail is maintained through `AuditLog` model (TPRM) and `GRCLog` model (GRC) that record create, update, delete, login, logout, approve, reject, and escalate actions with user, entity type, entity ID, old/new values, IP address, user agent, and status, `DataLifecycleAuditLog` that tracks retention lifecycle actions (create, archive, delete, backup) with before/after status and performed_by user, Django signal handlers (`handle_compliance_changes`, `handle_audit_changes`, `handle_incident_changes`) that automatically log model changes, and `VendorLoggingMiddleware` that provides comprehensive audit logging with security context for all vendor-related operations.

---

### Row 3: Centralized Logging & SIEM Ingestion
**Question:** Are logs centralized using a log aggregation system? What are the log retention periods and SIEM ingestion details?

**Answer:**
Yes, logs are centralized through Django logging configuration with file handlers (`logs/django.log`, `logs/vendor_audit.log`, `logs/vendor_security.log`) and console handlers for structured logging, database-backed logging via `GRCLog` and `AuditLog` models with `retentionExpiry` fields for retention management, Microsoft Sentinel integration implemented with OAuth authentication and Defender API service for incident and alert ingestion, and log retention configured through `RetentionTimeline` model with configurable retention periods per module, though specific log retention periods and automated SIEM ingestion workflows should be formally documented.

---

### Row 4: Incident Management & Response
**Question:** Does the system support incident management and incident response workflows?

**Answer:**
Yes, the system supports incident management through `Incident` model (GRC) with comprehensive fields for incident tracking (title, description, status, severity, criticality, mitigation, assignee, reviewer, due dates, classification, impact assessment, root cause, corrective actions), `VendorIncident` model (TPRM) for vendor-specific incidents with incident types (service outage, security breach, data loss, performance degradation, compliance violation), incident workflow endpoints (`create_incident`, `update_incident_status`, `incident_dashboard`, `incident_analytics`), incident approval workflow with `IncidentApproval` model, and integration with Microsoft Sentinel for external incident ingestion and correlation.

---

### Row 5: Log Integrity & Tamper Protection
**Question:** Are security logs protected against tampering?

**Answer:**
Yes, security logs are protected against tampering through database-level encryption using `EncryptedFieldsMixin` on log models (`GRCLog`, `AuditLog`, `MfaAuditLog`, `DataLifecycleAuditLog`) that encrypt sensitive fields (IP addresses, user agents, descriptions, additional info), database access controls through RBAC and tenant isolation middleware that restrict log access to authorized users, file-based logs stored with restricted filesystem permissions, and audit log models with auto-generated timestamps (`auto_now_add=True`) and immutable primary keys that prevent modification, though explicit log integrity verification (hash-based tamper detection) and write-once log storage mechanisms are not currently implemented.

---

### Row 6: User-Focused Threat Detection
**Question:** Are alerts generated for suspicious activity for individual accounts?

**Answer:**
Yes, alerts are generated for suspicious activity through account lockout email notifications sent when 5 consecutive failed login attempts occur, `_log_failed_login()` function that logs failed authentication attempts with IP address, username, attempt count, and reason to `grc_logs` table, rate limiting violations logged with warning levels when API rate limits are exceeded, `VendorAlertsAPIView` that provides real-time vendor alerts for OFAC-flagged vendors, performance alerts, and exceptions, and Microsoft Sentinel integration that ingests security alerts and incidents from Defender API for correlation and analysis, though automated real-time alerting for individual account anomalies (unusual geolocation, time-based patterns) is not currently implemented.

---

### Row 7: SIEM Integration
**Question:** Is integration with a SIEM platform supported?

**Answer:**
Yes, SIEM integration is supported through Microsoft Sentinel integration implemented with OAuth 2.0 authentication flow using Azure AD, `DefenderAPIService` class that retrieves incidents and alerts from Microsoft Defender API, Sentinel endpoints (`get_sentinel_incidents`, `get_sentinel_alerts`, `save_sentinel_incident`) that fetch and store security incidents, alert transformation and enrichment functionality that maps Sentinel alerts to internal incident format, and frontend integration components (`Sentinel.vue`) that display connection status and allow users to view and manage Sentinel incidents, though automated log forwarding to SIEM, real-time alert correlation, and integration with other SIEM platforms (Splunk, QRadar) are not currently implemented.

---

## Secure SDLC & DevSecOps

### Row 1: Containerized Workloads
**Question:** Is containerization used for deploying application workloads?

**Answer:**
Yes, containerization is used for deploying application workloads through Docker containers with `Dockerfile` for backend (Python 3.10-slim base image) and frontend (Node.js base image), `docker-compose.yml` for local development with service definitions and volume mounts, GitHub Actions CI/CD workflow (`.github/workflows/main.yml`) that builds Docker images and pushes to AWS ECR, container deployment to AWS EC2 with Docker network isolation (`grc_tprm_network`), and container orchestration with restart policies (`--restart unless-stopped`) and health checks, ensuring consistent deployment across environments.

---

### Row 2: Vulnerability Management
**Question:** Are security testing tools (SAST, DAST, SCA) documented and integrated into the pipeline?

**Answer:**
Security testing tools are partially implemented with file upload security validation (`SecureFileUploadHandler`) that performs malware scanning placeholders (ClamAV integration prepared), file header validation, and MIME type checking, though Static Application Security Testing (SAST), Dynamic Application Security Testing (DAST), and Software Composition Analysis (SCA) tools are not currently integrated into the CI/CD pipeline, and formal documentation of security testing procedures, automated security scanning in build pipelines, and vulnerability reporting workflows should be implemented.

---

### Row 3: Environment-Separated CI/CD Pipelines
**Question:** Are separate CI/CD pipelines defined for each environment (dev, QA, staging, prod) to prevent accidental deployment of insecure or untested code into production?

**Answer:**
CI/CD pipelines are partially separated through GitHub Actions workflow (`.github/workflows/main.yml`) that triggers on `main` and `master` branches with manual workflow dispatch, environment-specific configuration via external `config.env` file (`--env-file /home/ec2-user/config.env`) that separates secrets per environment, and AWS ECR image tagging that allows environment-specific image versions, though separate pipeline definitions for dev, QA, staging, and production environments, environment-specific approval gates, and automated testing stages before production deployment should be implemented to prevent accidental deployment of insecure code.

---

### Row 4: Dependency Governance & Vulnerability Scanning
**Question:** Are dependencies (libraries, packages, modules) managed and scanned for vulnerabilities using automated tools (to prevent exploitation of known CVEs and supply chain attacks)?

**Answer:**
Dependencies are managed through `requirements.txt` files for Python packages with version constraints (`cryptography>=41.0.7`, `PyJWT>=2.8.0`, `bcrypt>=4.1.2`), `package.json` files for Node.js dependencies in frontend applications, and pip/npm package managers for dependency installation, though automated vulnerability scanning tools (e.g., Dependabot, Snyk, OWASP Dependency-Check), CVE monitoring and alerting, automated dependency updates for security patches, and documented procedures for addressing vulnerable dependencies are not currently integrated into the CI/CD pipeline.

---

### Row 5: Runtime Secrets Handling
**Question:** Are secrets and sensitive configuration values excluded from CI/CD pipelines?

**Answer:**
Yes, secrets and sensitive configuration values are excluded from CI/CD pipelines through external environment file (`--env-file /home/ec2-user/config.env`) that is not committed to the repository, GitHub Actions secrets management for AWS credentials (ECR login uses `aws ecr get-login-password` with IAM credentials), no hardcoded secrets in workflow files (all sensitive values loaded from external sources), and `.gitignore` preventing commit of `.env` files and configuration files containing secrets, though explicit documentation of secret management procedures, secret rotation in CI/CD, and audit logging of secret access in pipelines should be formalized.

---

### Row 6: CI/CD Rollback & Recovery Control
**Question:** Is rollback or recovery defined in CI/CD (to ensure rapid restoration if a deployment introduces vulnerabilities or breaks functionality)?

**Answer:**
Rollback and recovery capabilities exist at the application level through RFP versioning system (`rollback_rfp_version` endpoint) that allows rolling back to previous versions with transaction safety, database backup and restore functionality (`DatabaseBackupManager`, `contract_restore` endpoint), and Docker container rollback capability (stopping and removing containers before deploying new versions), though explicit CI/CD rollback procedures, automated rollback triggers on health check failures, version tagging for easy rollback to previous Docker images, and documented incident response procedures for deployment failures should be formalized in the CI/CD pipeline.

---

## Infrastructure & Cloud Security

### Row 1: Cloud Hosting Posture
**Question:** Is the application hosted on a major cloud provider such as AWS, Azure, or GCP?

**Answer:**
Yes, the application is hosted on AWS with production deployment on AWS EC2 instances, AWS RDS MySQL databases (`grc2` for GRC, `tprm_integration` for TPRM) hosted in AWS RDS, AWS S3 for object storage with bucket configuration via environment variables, AWS ECR for Docker container registry (images pushed to `480940871468.dkr.ecr.ap-south-1.amazonaws.com`), and production domain `riskavaire.vardaands.com` served from AWS infrastructure in `ap-south-1` region.

---

### Row 2: Managed Database Services Usage
**Question:** Are managed database services (RDS, Cloud SQL, Cosmos DB, etc.) used?

**Answer:**
Yes, managed database services are used through AWS RDS MySQL for both GRC (`grc-db.c1womgmu83di.ap-south-1.rds.amazonaws.com`) and TPRM (`tprmintegration.c1womgmu83di.ap-south-1.rds.amazonaws.com`) databases, which provides automated backups, automated patching, encryption capabilities, network isolation through VPCs, connection health checks, and compliance certifications (SOC, ISO, PCI DSS), with database credentials managed via environment variables.

---

### Row 3: Network Segmentation
**Question:** Is network-level security configuration documented (VPC, subnets, security groups, ACLs, firewalls) to demonstrate segmentation and defense-in-depth?

**Answer:**
Network-level security is partially implemented with AWS RDS databases hosted within VPCs with security groups restricting access to application servers only, Docker network isolation (`grc_tprm_network`) for container-to-container communication, Nginx reverse proxy isolating backend services from direct internet access, and backend services running on internal ports (8000) not directly exposed, though explicit documentation of VPC configuration, subnet design, security group rules, network ACLs, and firewall policies should be formalized to demonstrate complete network segmentation and defense-in-depth.

---

### Row 4: HTTPS Enforcement
**Question:** Are all client-backend communications encrypted using HTTPS, with HTTP redirected to HTTPS?

**Answer:**
Yes, HTTPS enforcement is implemented through Nginx configuration (`grc_tptm.conf`) that redirects HTTP (port 80) to HTTPS (port 443) with `return 301 https://$host$request_uri`, SSL certificates from Let's Encrypt (`/etc/letsencrypt/live/riskavaire.vardaands.com/fullchain.pem`), Django settings (`SECURE_SSL_REDIRECT = not DEBUG`) that redirect HTTP to HTTPS in production, HSTS headers (`SECURE_HSTS_SECONDS = 31536000`) that force HTTPS for future requests, and secure cookie flags (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`) enabled in production, though development environments may use HTTP for local testing.

---

### Row 5: Strong TLS Configuration
**Question:** Are strong TLS versions and cipher suites enforced?

**Answer:**
TLS configuration is implemented through Nginx SSL configuration with Let's Encrypt certificates, Django security settings (`SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`) that enforce HTTPS, and `EnterpriseSecurityHeadersMiddleware` that adds HSTS headers in production, though explicit TLS version restrictions (TLS 1.2+, disabling TLS 1.0/1.1), cipher suite configuration, and SSL/TLS configuration documentation should be formalized to demonstrate strong TLS enforcement and alignment with industry best practices.

---

### Row 6: Internal Service Encryption
**Question:** Are internal service-to-service communications encrypted (e.g., RDS, Redis, S3 connections) to prevent lateral movement attacks inside the cloud environment?

**Answer:**
Internal service encryption is partially implemented with AWS RDS connections using MySQL SSL/TLS capabilities (connection options configured in Django settings), AWS S3 connections using HTTPS/TLS for all S3 API operations via boto3 client, and Redis connections configured via `REDIS_URL` environment variable, though explicit enforcement of SSL/TLS for all database connections, Redis TLS configuration, and documentation of encryption in transit for all internal service communications should be formalized to prevent lateral movement attacks.

---

### Row 7: Server & OS Hardening
**Question:** Are servers hardened following CIS or other approved security baselines? Provide OS hardening details.

**Answer:**
Server hardening is partially implemented through Docker containers using official base images (Python 3.10-slim, Node.js) that provide minimal attack surface, container isolation with Docker network segmentation, and application-level security controls (RBAC, encryption, audit logging), though explicit documentation of OS hardening procedures, CIS baseline compliance, security patch management procedures, and server hardening configuration details should be formalized to demonstrate adherence to security baselines.

---

### Row 8: Web Application Firewall
**Question:** Is a Web Application Firewall (WAF) enabled to protect APIs (e.g., AWS WAF, Azure Front Door, Cloud Armor)?

**Answer:**
WAF protection is partially implemented through Nginx reverse proxy that provides basic request filtering and security headers, application-level rate limiting and input validation, and security middleware (`EnterpriseSecurityHeadersMiddleware`, `VendorSecurityMiddleware`) that adds protection layers, though dedicated WAF services (AWS WAF, Azure Front Door, Cloud Armor) are not currently configured, and explicit WAF rules, DDoS protection, and automated threat detection should be implemented for comprehensive API protection.

---

### Row 9: Object Storage Public Access Controls
**Question:** Is object storage (e.g., S3 buckets) protected from public access, and what bucket policies are applied?

**Answer:**
Object storage access controls are implemented through AWS S3 with AWS credentials stored in `AWSCredentials` model (encrypted fields), S3 bucket configuration via environment variables (`AWS_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), and file upload functions using boto3 S3 client with proper content type and disposition headers, though explicit S3 bucket policies, IAM roles for S3 access, public access block settings, and bucket policy documentation should be formalized to demonstrate comprehensive access control enforcement and prevention of unauthorized public access.

---

### Row 10: OWASP Top 10 Controls
**Question:** Are file uploads scanned for malware before being processed or stored?

**Answer:**
Yes, file uploads are scanned for malware through `SecureFileUploadHandler` class that performs malware scanning with ClamAV integration prepared (`_scan_with_clamav()` method), file header validation that checks file signatures against declared MIME types, suspicious pattern detection (blocking `.exe`, `.bat`, `.cmd`, `.scr`, `.vbs`, `.js` files), file size validation (10MB max), and secure file storage outside web root with proper permissions, though production deployment should ensure ClamAV or equivalent malware scanning service is actively running and integrated.

---

### Row 11: Encryption at Rest
**Question:** Is encryption at rest enabled (SSE-S3, KMS, etc.) for all stored data?

**Answer:**
Yes, encryption at rest is implemented through field-level encryption using `EncryptedFieldsMixin` that automatically encrypts sensitive fields (emails, phone numbers, addresses, names, tokens) before saving to database with Fernet symmetric encryption (AES-128 in CBC mode), AWS Secrets Manager encrypting secrets at rest using AWS KMS, and encryption keys managed via environment variables with AWS Secrets Manager support for production, though AWS RDS encryption at the storage layer (SSE-S3, KMS) should also be enabled for additional protection of database storage.

---

### Row 12: Redis Security
**Question:** Is Redis protected with authentication (password + TLS), and is Redis non-publicly exposed?

**Answer:**
Redis security is partially implemented through Redis URL configuration via environment variables (`REDIS_URL=redis://localhost:6379/2`), Redis connection health checks and timeout configuration in `get_redis_client()` function, and Redis used for caching and session management with connection pooling, though explicit Redis authentication (password protection), TLS encryption for Redis connections, network isolation (non-publicly exposed), and Redis security configuration documentation should be formalized to demonstrate comprehensive Redis security.

---

### Row 13: Workload Isolation
**Question:** Are workloads isolated using containers or VMs?

**Answer:**
Yes, workloads are isolated using Docker containers with `Dockerfile` for backend (Python 3.10-slim base image) and frontend (Node.js base image), `docker-compose.yml` for local development with service definitions, Docker network isolation (`grc_tprm_network`) for container-to-container communication, container deployment to AWS EC2 with restart policies (`--restart unless-stopped`), and GitHub Actions CI/CD workflow that builds and deploys Docker images to AWS ECR, ensuring consistent workload isolation across environments.

---

### Row 14: Network Segmentation
**Question:** Is network segmentation documented across environments and services?

**Answer:**
Network segmentation is partially documented through environment separation (Production: AWS RDS, Development: local/separate RDS), Docker network isolation (`grc_tprm_network`) for container communication, Nginx reverse proxy isolating backend services from direct internet access, and separate database instances per module (GRC uses `grc2`, TPRM uses `tprm_integration`), though explicit documentation of network segmentation architecture, VPC design, subnet configuration, security group rules, and network segmentation across all environments and services should be formalized.

---

### Row 15: IAM Role Governance
**Question:** Are IAM roles, permissions, and access control policies documented?

**Answer:**
IAM role governance is partially implemented through AWS Secrets Manager IAM policies that restrict access to secrets based on IAM roles, AWS ECR access using IAM credentials for Docker image push operations, and application-level RBAC systems (GRC `rbac` table, TPRM `rbac_tprm` table) with comprehensive permission documentation, though explicit documentation of AWS IAM roles, IAM policies for EC2, RDS, S3 access, least privilege access principles, and IAM role governance procedures should be formalized to demonstrate comprehensive access control.

---

### Row 16: SIEM & Alerting
**Question:** Are cloud-native monitoring and alerting tools (e.g., AWS CloudWatch, GuardDuty, Security Hub) enabled (to detect anomalies and threats in real time)?

**Answer:**
Cloud-native monitoring is partially implemented through Microsoft Sentinel integration with OAuth 2.0 authentication and Defender API service for security incident ingestion, application-level logging (`RequestLoggingMiddleware`, `VendorLoggingMiddleware`) that logs all API requests and security events, and database-backed logging (`GRCLog`, `AuditLog` models) with retention management, though explicit AWS CloudWatch integration, AWS GuardDuty threat detection, AWS Security Hub compliance monitoring, and automated alerting for cloud security anomalies should be implemented for comprehensive cloud-native security monitoring.

---

### Row 17: IaC & Drift Management
**Question:** Are infrastructure changes managed via Infrastructure as Code (IaC) with security scanning? - IaC misconfigurations are a leading cause of cloud breaches.

**Answer:**
Infrastructure as Code is partially implemented through GitHub Actions CI/CD workflow (`.github/workflows/main.yml`) that automates Docker image building and deployment, Docker Compose configuration for local development, and Dockerfile definitions for consistent container builds, though explicit IaC tools (Terraform, CloudFormation, CDK), infrastructure configuration versioning, IaC security scanning tools (Checkov, tfsec, Snyk IaC), and drift detection mechanisms should be implemented to prevent misconfigurations and ensure infrastructure changes are managed securely and auditable.

---

## Compliance & Regulatory Controls

### Row 1: Compliance Workflow Support
**Question:** Does the platform support required compliance management workflows?

**Answer:**
Yes, the platform supports comprehensive compliance management workflows through `Compliance` model that tracks compliance items with status, maturity levels, and risk assessment, compliance approval workflows with `ComplianceApproval` model and `submit_compliance_review` endpoint, compliance mapping to frameworks and policies via `ComplianceMapping` model, compliance checking APIs (`check_document_compliance`, `real_time_compliance_check`) that verify compliance against requirements, and compliance reporting and analytics endpoints that generate compliance status reports and dashboards.

---

### Row 2: GDPR Operationalization
**Question:** Are GDPR-related workflows implemented (data subject requests, consent management, data deletion)?

**Answer:**
Yes, GDPR-related workflows are implemented through `DataSubjectRequest` model that tracks data subject requests (Access, Rectification, Erasure, Portability) with status tracking and verification, data subject request endpoints (`create_data_subject_request`, `get_data_subject_requests`, `update_data_subject_request_status`) that handle GDPR requests, `ConsentAcceptance` and `ConsentWithdrawal` models that track user consent for specific actions with GDPR Article 7(3) compliance, `CookiePreferences` model for GDPR cookie consent management, and data deletion capabilities through retention management system with `dispose_and_delete_record()` method, though automated data portability export and comprehensive GDPR compliance reporting should be enhanced.

---

### Row 3: Data Retention Policies
**Question:** Are data retention policies documented for all data categories?

**Answer:**
Yes, data retention policies are documented and implemented through `RetentionTimeline` model that tracks retention periods per record with status (Active, Expired, Disposed, Archived, Paused), `RetentionModulePageConfig` model that configures retention policies per module and sub-page, `compute_retention_expiry()` function that calculates retention expiry dates from configuration, `delete_expired_records` management command that automatically deletes records whose retention period has expired, and retention expiry dates stored on records (e.g., `retentionExpiry` field on Policy, Framework, Audit models), though explicit documentation of retention periods per data category (e.g., Policy: 7 years, Audit: 5 years) should be formalized.

---

### Row 4: Security Logging
**Question:** Are audit-log retention requirements defined and followed?

**Answer:**
Yes, audit-log retention requirements are defined and followed through `GRCLog` and `AuditLog` models with `retentionExpiry` fields that store retention expiry dates per log entry, `RetentionTimeline` model that tracks retention periods for audit logs with status management, `DataLifecycleAuditLog` that tracks retention lifecycle actions (create, archive, delete, backup) with before/after status, `cleanup_old_data` Celery task that automatically cleans up old audit logs (2 years retention) and file uploads (1 year retention), and retention management endpoints that allow administrators to configure and manage log retention periods, though explicit audit-log retention policies (e.g., security logs: 1 year, compliance logs: 7 years) should be documented per log category.

---

### Row 5: Audit Evidence Generation
**Question:** Is evidence generation supported for internal or external audits?

**Answer:**
Yes, evidence generation is supported through `generate_evidence_pack()` function (SEBI AI Auditor) that creates audit-ready evidence packs with clause-wise evidence, timestamped proof, disclosure timelines, and risk anomaly logs, `generate_audit_report()` endpoint that generates comprehensive audit reports with evidence, `AuditDocument` and `AuditDocumentMapping` models that map document sections to compliance requirements with AI analysis and confidence scores, compliance checking APIs that extract evidence from documents and database records, and audit report export functionality that generates PDF and Excel reports for external auditors, though automated evidence collection workflows and evidence pack templates for different audit types should be enhanced.

---

### Row 6: Standards Mapping & Gaps
**Question:** Are compliance certifications (e.g., ISO 27001, SOC 2, PCI DSS) documented and mapped to platform controls (to demonstrate alignment with industry standards)?

**Answer:**
Yes, compliance certifications are documented and mapped through `Framework` model that supports multiple compliance frameworks (ISO 27001, PCI DSS, NIST 800-53, Basel III, TCFD), `ComplianceMapping` model that maps SLAs and controls to frameworks with compliance status and scores, `CrossFrameworkMappingService` that provides cross-framework mapping capabilities, `OrganizationalControl` model that tracks organizational controls mapped to frameworks, framework content configuration (`frameworkContent.js`) that documents framework controls and compliance status, and compliance checking APIs that verify alignment with framework requirements, though explicit control-to-certification mapping documentation (e.g., ISO 27001 A.9.2.1 → JWT Authentication) should be formalized to demonstrate complete alignment.

---

### Row 7: Vendor Risk Management
**Question:** Are third-party integrations assessed for compliance risks (to ensure vendors and partners meet the same regulatory standards)?

**Answer:**
Yes, third-party integrations are assessed for compliance risks through `VendorRiskAssessments` model that tracks vendor risk assessments with overall scores and category-specific scores (financial, operational, cybersecurity, compliance, reputational), `VendorRiskAssessment` model (TPRM) with risk scoring, assessment factors, and mitigation actions, vendor screening integration with external screening results (`ExternalScreeningResult`, `ScreeningMatch`) that check vendors against OFAC and PEP lists, compliance mapping for vendors via `ComplianceMapping` model that tracks vendor compliance status against frameworks, and risk analysis services that generate comprehensive vendor risks, though explicit vendor compliance risk assessment procedures, vendor compliance certification tracking, and automated vendor compliance monitoring should be formalized.

---

### Row 8: Compliance Change Monitoring Control
**Question:** Is there a process for monitoring regulatory changes and updating workflows accordingly (to ensure ongoing compliance as laws evolve)? - Regulations change frequently; Without a monitoring process, compliance gaps may emerge.

**Answer:**
Yes, regulatory change monitoring is partially implemented through `framework_update_checker.py` that uses Perplexity API to check for framework updates and amendments, `ChangeManagementService` that tracks framework changes and amendments, framework versioning system (`FrameworkVersion` model) that maintains version history of compliance frameworks, compliance change tracking through `handle_compliance_changes` signal handler that automatically creates events for compliance status changes, and framework update detection that identifies when frameworks have been updated after a specified date, though automated regulatory change monitoring workflows, alerting for regulatory updates, and documented procedures for updating compliance workflows based on regulatory changes should be formalized to ensure ongoing compliance as laws evolve.

---

## Business Continuity & Disaster Recovery

### Row 1: Backup Strategy
**Question:** Is a backup strategy defined for all critical systems and data?

**Answer:**
Yes, a backup strategy is defined through `VendorBackupManager` that creates database backups using Django's `dbbackup` command with timestamped backup files, `DatabaseBackupManager` that creates backups before critical operations (contracts, RFPs) with JSON export of data, scheduled backup tasks (`vendor_create_scheduled_backup`) that run automatically via Celery, emergency backup functionality (`vendor_create_emergency_backup`) triggered on system failures, backup retention policy (`BACKUP_RETENTION_DAYS: 30`) that keeps backups for 30 days, and backup cleanup configuration (`DBBACKUP_CLEANUP_KEEP: 10`) that maintains the 10 most recent backups, with backup files stored in `backups/` directory.

---

### Row 2: RPO and RTO Definitions
**Question:** What are the defined RPO (Recovery Point Objective) and RTO (Recovery Time Objective) for critical systems (to measure how much data loss and downtime is acceptable during a disaster)?

**Answer:**
Yes, RPO and RTO targets are defined through `DrpDetails` model that stores `rto_targets` and `rpo_targets` as JSON fields for different systems (e.g., `{"Critical Systems":"2h","Applications":"4h","Databases":"1h","Network":"30m","Security":"6h"}` for RTO, `{"Critical Systems":"30m","Applications":"1h","Databases":"15m","Network":"5m","Security":"2h"}` for RPO), `BcpDetails` model that also tracks RTO and RPO targets for business continuity planning, BCP/DRP plan extraction and evaluation workflows that capture RTO/RPO from vendor plans, and plan evaluation questionnaires that assess whether RTO/RPO targets are realistic and tested, though explicit RTO/RPO targets for the application's own infrastructure should be documented separately from vendor plan management.

---

### Row 3: DR Drills and Testing
**Question:** Are Disaster Recovery (DR) drills performed regularly?

**Answer:**
Yes, DR drills and testing are supported through `DrpDetails` model that stores `testing_validation_schedule` field (e.g., "Monthly DR testing with annual comprehensive exercise"), `BcpDetails` model that tracks `training_testing_schedule` (e.g., "Annual BCP training for all staff, quarterly tabletop exercises, and semi-annual full-scale testing"), `maintenance_review_cycle` fields that document review and update cycles (e.g., "Monthly review with quarterly updates"), BCP/DRP plan evaluation questionnaires that assess testing frequency and validation, and plan extraction workflows that capture testing schedules from vendor DRP documents, though explicit documentation of actual DR drill execution, results, and remediation actions for the application's own infrastructure should be formalized.

---

### Row 4: High Availability Implementation
**Question:** Is High Availability (HA) implemented for critical components?

**Answer:**
Yes, High Availability is partially implemented through Nginx load balancing with upstream configuration for multiple backend instances enabling horizontal scaling, Docker container orchestration with restart policies (`--restart unless-stopped`) that automatically restart failed containers, AWS RDS MySQL with automated backups and multi-AZ deployment capabilities (though explicit multi-AZ configuration should be verified), database connection health checks that monitor database availability, and Nginx reverse proxy that provides redundancy and failover capabilities, though explicit multi-region deployment, automated failover mechanisms, and documented HA architecture for all critical components should be formalized to ensure complete high availability coverage.

---

### Row 5: Ransomware Protection
**Question:** Is ransomware protection implemented (immutable backups, snapshots, threat detection)?

**Answer:**
Ransomware protection is partially implemented through database backup functionality (`VendorBackupManager`, `DatabaseBackupManager`) that creates regular backups before critical operations, AWS RDS automated backups that provide point-in-time recovery capabilities, file upload malware scanning with ClamAV integration (`_scan_with_clamav` method) that scans uploaded files for threats, secure file upload handlers that validate file types and MIME types to prevent malicious file uploads, and backup retention policies that maintain multiple backup versions, though explicit immutable backup storage (write-once, read-many), automated snapshot creation with retention policies, real-time threat detection and alerting, and documented ransomware response procedures should be formalized to provide comprehensive ransomware protection.

---

### Row 6: Backup Encryption and Offsite Storage
**Question:** Are backups encrypted and stored offsite or in multiple regions (to protect against physical disasters and comply with data protection regulations)?

**Answer:**
Yes, backup encryption and offsite storage are implemented through AWS RDS automated backups that are encrypted at rest using AWS KMS encryption, database backups stored in AWS RDS with automatic backup retention (7 days by default, configurable up to 35 days), AWS RDS backups stored in the same region as the database with cross-region replication capabilities available, field-level encryption (`EncryptedFieldsMixin`) that encrypts sensitive data before backup, and backup files stored in `backups/` directory with filesystem-level encryption available, though explicit cross-region backup replication, documented backup encryption key management, and verification of backup restoration procedures from offsite locations should be formalized to ensure complete protection against physical disasters and compliance with data protection regulations.

---

### Row 7: Disaster Communication Plan
**Question:** Is there a documented communication plan for disaster scenarios (to ensure stakeholders, customers, and regulators are informed promptly)?

**Answer:**
Yes, disaster communication plans are documented through `BcpDetails` model that stores `communication_plan_internal` field for internal stakeholder communication (e.g., "Executive Team → Department Heads → Team Leads → Staff" with email, phone, SMS channels), `communication_plan_bank` field for external communication including customer notifications and regulatory reporting (e.g., "Customer notifications via website, mobile app, email, and SMS. Regulatory notifications sent within 24 hours"), `roles_responsibilities` JSON field that defines communication roles (e.g., "Incident Commander", "Communication Lead", "Technical Lead"), BCP/DRP plan extraction workflows that capture communication plans from vendor documents, and plan evaluation questionnaires that assess communication plan completeness, though explicit communication plan documentation for the application's own disaster scenarios, stakeholder contact lists, and regulatory notification procedures should be formalized separately from vendor plan management.

---

### Row 8: Third-Party Dependencies in BC/DR Plan
**Question:** Are third-party dependencies (cloud providers, SaaS services) included in the BC/DR plan (to ensure vendor outages don't cripple operations)?

**Answer:**
Yes, third-party dependencies are included in BC/DR planning through `DrpDetails` model that stores `third_party_services` JSON field listing external dependencies (e.g., "Cloud Provider", "SMS Gateway", "Email Service", "Credit Bureau", "Regulatory Reporting"), `BcpDetails` model that tracks `dependencies_external` JSON field for external vendor dependencies, BCP/DRP plan extraction workflows that capture third-party service dependencies from vendor plans, plan evaluation questionnaires that assess vendor dependency risks and mitigation strategies, and vendor risk management workflows that evaluate vendor BC/DR capabilities, though explicit BC/DR plan documentation for the application's own third-party dependencies (AWS, email services, SMS gateways), vendor outage contingency plans, and alternative service provider arrangements should be formalized to ensure vendor outages don't cripple operations.

---

**Prepared by:** Vardaan Team  
**Date:** 2025-01-27  
**Review Status:** Ready for KPMG Review
