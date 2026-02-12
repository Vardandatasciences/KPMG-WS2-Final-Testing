# Vardaan Security Architecture and Design Review Questionnaire - Responses

## Application & Deployment Architecture

### Question 1: Documentation & Trust Boundaries
**Question:** Is the application designed using a layered or multi-tier architecture with clearly defined trust boundaries?

**Response:**
Yes, the application is designed using a layered multi-tier architecture with clearly defined trust boundaries. The architecture consists of the following layers:

1. **Presentation Layer (Frontend)**
   - Separate frontend applications for GRC and TPRM modules
   - Vue.js-based Single Page Applications (SPAs)
   - Located in `grc_frontend/` directory

2. **API Layer (Views)**
   - RESTful API endpoints in `grc_backend/backend/` and `grc_backend/tprm_backend/`
   - JWT-based authentication middleware
   - Request logging and audit middleware

3. **Decorator Layer**
   - Permission checking decorators for RBAC
   - Module-specific and generic permission checks
   - Located in `grc_backend/tprm_backend/rbac/`

4. **Business Logic Layer**
   - Core business logic and utilities
   - RBAC permission checking logic
   - Risk analysis and compliance modules

5. **Data Access Layer**
   - Django ORM models
   - Database routing for multi-database architecture
   - Tenant-aware data access with automatic filtering

6. **Authentication Layer**
   - JWT validation and user extraction
   - Multi-tenant context middleware
   - Session management

**Trust Boundaries:**
- Frontend applications are isolated from backend APIs through reverse proxy (Nginx)
- Backend services are not directly exposed to the internet
- Database connections are isolated per environment
- Multi-tenant data isolation enforced at middleware level

**Evidence:**
- Architecture documentation in `grc_backend/tprm_backend/rbac/RBAC_APPROACH.md`
- Middleware stack in `grc_backend/backend/settings.py` (lines 134-159)
- Tenant isolation middleware in `grc_backend/grc/tenant_middleware.py`

---

### Question 2: Network Segmentation (Application Modules)
**Question:** Are different application modules logically isolated to prevent cross-module risks?

**Response:**
Yes, different application modules are logically isolated:

1. **Module Separation:**
   - **GRC Module**: Governance, Risk, and Compliance management
   - **TPRM Module**: Third Party Risk Management
   - Both modules have separate frontend applications and backend routes
   - Separate database configurations (GRC uses `grc2` database, TPRM uses `tprm_integration` database)

2. **Logical Isolation Mechanisms:**
   - **URL Routing**: GRC served from root `/`, TPRM served from `/tprm/` path
   - **API Endpoints**: Separate API prefixes (`/api/` for GRC, `/api/tprm/` for TPRM)
   - **Database Routing**: Database router (`TPRMDatabaseRouter`) routes TPRM apps to separate database
   - **Middleware Isolation**: Separate tenant middleware for each module
   - **Frontend Separation**: Separate Vue.js applications with independent build processes

3. **Cross-Module Protection:**
   - Tenant isolation middleware prevents data leakage between tenants
   - RBAC decorators enforce module-specific permissions
   - Database queries automatically filtered by tenant context

**Evidence:**
- Database router configuration in `grc_backend/backend/tprm_router.py`
- Nginx configuration showing separate routing in `grc_frontend/nginx.docker.conf`
- Multi-tenancy implementation in `grc_backend/tprm_backend/TPRM_MULTITENANCY_IMPLEMENTATION.md`

---

### Question 3: Network Segmentation (Environments)
**Question:** Are development, staging, and production environments logically and physically separated?

**Response:**
Yes, development, staging, and production environments are logically separated:

1. **Environment Configuration:**
   - **Production (AWS)**: 
     - Domain: `riskavaire.vardaands.com`
     - Database: AWS RDS instances
     - Environment variable: `ENVIRONMENT = 'aws'`
   - **Development/Local**:
     - Localhost configurations
     - Environment variable: `ENVIRONMENT = 'local'` or `'development'`
     - Separate database connections

2. **Separation Mechanisms:**
   - **Environment Variables**: All sensitive configuration via environment variables
     - Database credentials: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`
     - API URLs: Different base URLs per environment
     - Debug mode: `DEBUG = False` in production, `True` in development
   - **Database Separation**:
     - Production: AWS RDS (`tprmintegration.c1womgmu83di.ap-south-1.rds.amazonaws.com`)
     - Development: Local MySQL or separate RDS instances
   - **Configuration Files**:
     - Frontend: `grc_frontend/src/config/api.js` with environment-based URL selection
     - Backend: `grc_backend/backend/settings.py` with environment variable loading

3. **Physical Separation:**
   - Production deployed on AWS EC2 instances
   - Development environments can run locally or on separate infrastructure
   - Docker containers for consistent deployment across environments

**Evidence:**
- Environment configuration in `grc_frontend/src/config/api.js` (lines 1-36)
- Settings file with environment variable loading in `grc_backend/backend/settings.py`
- Docker compose configuration in `grc_backend/docker-compose.yml`

---

### Question 4: Data Segregation Control
**Question:** Is data segregation enforced between environments to prevent leakage of production data into non-production systems?

**Response:**
Yes, data segregation is enforced between environments through multiple mechanisms:

1. **Database-Level Segregation:**
   - **Separate Database Instances**: Production uses AWS RDS, development uses local or separate RDS instances
   - **Database Credentials**: Environment-specific database credentials via environment variables
   - **Connection Strings**: Different database hosts, names, and credentials per environment
   - **Database Routing**: Separate databases for GRC (`grc2`) and TPRM (`tprm_integration`)

2. **Application-Level Segregation:**
   - **Multi-Tenancy**: Tenant isolation middleware ensures data is filtered by `TenantId` at the application level
   - **Tenant Context Middleware**: Automatically extracts tenant from authenticated user and filters all queries
   - **Tenant Isolation Middleware**: Validates that tenant context is present for all authenticated requests

3. **Configuration Segregation:**
   - **Environment Variables**: All sensitive data (DB credentials, API keys) loaded from environment variables
   - **No Hardcoded Secrets**: Production secrets not stored in codebase
   - **AWS Secrets Manager**: Enterprise key management system supports AWS Secrets Manager for production
   - **Key Management**: Different key management backends for different environments
     - Production: AWS Secrets Manager
     - Development: Environment variables or file-based (local only)

4. **Data Access Controls:**
   - **Automatic Tenant Filtering**: All database queries automatically filtered by tenant context
   - **Middleware Enforcement**: `TenantIsolationMiddleware` logs warnings for requests without tenant context
   - **Database Router**: Routes different apps to appropriate databases

**Evidence:**
- Multi-tenancy implementation: `grc_backend/tprm_backend/TPRM_MULTITENANCY_IMPLEMENTATION.md`
- Tenant middleware: `grc_backend/grc/tenant_middleware.py` and `grc_backend/tprm_backend/core/tenant_middleware.py`
- Key management: `grc_backend/grc/utils/key_management.py` (lines 277-321)
- Database configuration: `grc_backend/backend/settings.py` (lines 200-234)

---

### Question 5: API Gateway / WAF
**Question:** Is a reverse proxy or API gateway used to isolate backend services from direct internet access?

**Response:**
Yes, a reverse proxy (Nginx) is used to isolate backend services from direct internet access:

1. **Reverse Proxy Implementation:**
   - **Nginx**: Primary reverse proxy server
   - **Apache**: Alternative configuration available
   - **Location**: All backend API requests routed through `/api/` path

2. **Configuration Details:**
   - **Backend Isolation**: 
     - Backend services run on internal ports (8000)
     - Nginx proxies `/api/` requests to `http://backend_api:8000` or `http://localhost:8000`
     - Backend not directly accessible from internet
   - **Security Headers**: Nginx adds security headers:
     - `X-Frame-Options: SAMEORIGIN`
     - `X-Content-Type-Options: nosniff`
     - `X-XSS-Protection: 1; mode=block`
     - `Referrer-Policy: no-referrer-when-downgrade`
   - **Proxy Headers**: Proper forwarding of client information:
     - `X-Real-IP`
     - `X-Forwarded-For`
     - `X-Forwarded-Proto`
     - `X-Forwarded-Host`

3. **Traffic Management:**
   - **Upstream Configuration**: Docker-based upstream definitions for load balancing
   - **Timeout Configuration**: Proper timeout settings (60-120 seconds)
   - **Buffering**: Optimized buffer sizes for performance
   - **CORS Handling**: CORS headers configured at proxy level

4. **Frontend Routing:**
   - GRC frontend served from root `/`
   - TPRM frontend served from `/tprm/` path
   - Static assets cached appropriately

**Evidence:**
- Nginx configuration: `grc_frontend/nginx-complete.conf` (lines 57-73)
- Docker nginx config: `grc_frontend/nginx.docker.conf` (lines 45-75)
- Reverse proxy setup: `nginx-reverse-proxy/nginx.conf` (lines 59-84)
- Apache alternative: `grc_frontend/tprm_frontend/apache.conf` (lines 53-56)

---

### Question 6: Traffic Management & Service Mesh Security Control
**Question:** Are load balancers or service meshes implemented to manage traffic securely and efficiently?

**Response:**
Yes, load balancing and traffic management are implemented:

1. **Load Balancing:**
   - **Nginx Upstream Configuration**: 
     - Upstream blocks defined for `grc_frontend`, `tprm_frontend`, and `backend_api`
     - Docker container-based upstream servers
     - Enables horizontal scaling of services
   - **Multiple Backend Instances**: Configuration supports multiple backend instances for load distribution

2. **Traffic Management Features:**
   - **Request Routing**: Intelligent routing based on URL paths
     - `/api/` → Backend API
     - `/tprm/` → TPRM Frontend
     - `/` → GRC Frontend
   - **Timeout Management**: 
     - Connection timeout: 60-120 seconds
     - Send timeout: 60-120 seconds
     - Read timeout: 60-120 seconds
   - **Buffering**: Optimized buffer configuration for performance
     - Buffer size: 4k
     - Number of buffers: 8
     - Busy buffer size: 8k

3. **Security Features:**
   - **Gzip Compression**: Enabled for efficient data transfer
   - **Security Headers**: Applied at proxy level
   - **Connection Management**: Keep-alive connections for efficiency
   - **Client Limits**: `client_max_body_size: 20M` for file uploads

4. **Service Architecture:**
   - **Docker Compose**: Multi-container setup with service discovery
   - **Container Networking**: Services communicate via Docker network
   - **Service Isolation**: Each service (frontend, backend) in separate containers

5. **Note on Service Mesh:**
   - No dedicated service mesh (e.g., Istio, Linkerd) is currently implemented
   - Nginx serves as the primary traffic management and load balancing solution
   - Architecture supports future service mesh integration if needed

**Evidence:**
- Nginx upstream configuration: `nginx-reverse-proxy/nginx.conf` (lines 46-57)
- Docker compose: `grc_backend/docker-compose.yml`
- Traffic management: `grc_frontend/nginx-complete.conf` and `grc_frontend/nginx.docker.conf`
- Timeout and buffering settings in all nginx configuration files

---

## Summary

All questions in the Application & Deployment Architecture section have been answered based on the actual codebase implementation. The system demonstrates:

✅ **Layered Architecture**: Multi-tier architecture with clear separation of concerns
✅ **Module Isolation**: GRC and TPRM modules are logically separated
✅ **Environment Separation**: Development, staging, and production environments are separated
✅ **Data Segregation**: Multi-tenant architecture with tenant-based data isolation
✅ **API Gateway**: Nginx reverse proxy isolates backend services
✅ **Traffic Management**: Load balancing and traffic management via Nginx upstream configuration

---

**Prepared by:** Vardaan Team  
**Date:** 2025-01-27  
**Review Status:** Ready for KPMG Review
