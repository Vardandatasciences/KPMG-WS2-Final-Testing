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
Yes, data segregation is enforced through multiple mechanisms:

1. **Database-Level Segregation:**
   - Separate database instances (Production: AWS RDS, Development: local or separate RDS)
   - Environment-specific database credentials via environment variables
   - Different database hosts, names, and credentials per environment
   - Separate databases for GRC (`grc2`) and TPRM (`tprm_integration`)

2. **Application-Level Segregation:**
   - Multi-tenant architecture with tenant isolation middleware
   - Tenant context middleware automatically filters all queries by `TenantId`
   - Tenant isolation middleware validates tenant context for all authenticated requests

3. **Configuration Segregation:**
   - All sensitive data (DB credentials, API keys) loaded from environment variables
   - No hardcoded secrets in codebase
   - AWS Secrets Manager support for production key management
   - Different key management backends for different environments

4. **Data Access Controls:**
   - Automatic tenant filtering on all database queries
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
Nginx/Apache used as reverse proxy for backend APIs.

**Detailed Response:**
Yes, Nginx reverse proxy is used:
- Backend services run on internal ports (8000)
- Nginx proxies `/api/` requests to backend services
- Backend not directly accessible from internet
- Security headers added: `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`
- Proper forwarding of client information (`X-Real-IP`, `X-Forwarded-For`, etc.)
- CORS headers configured at proxy level
- Apache alternative configuration available

**Evidence:**
- Nginx configuration: `grc_frontend/nginx-complete.conf`, `grc_frontend/nginx.docker.conf`
- Reverse proxy setup: `nginx-reverse-proxy/nginx.conf`
- Apache alternative: `grc_frontend/tprm_frontend/apache.conf`

---

### Row 6: Traffic Management & Service Mesh Security Control
**Question:** Are load balancers or service meshes implemented to manage traffic securely and efficiently?

**Answer:**
Yes, load balancing and traffic management are implemented:

1. **Load Balancing:**
   - Nginx upstream configuration for `grc_frontend`, `tprm_frontend`, and `backend_api`
   - Docker container-based upstream servers
   - Supports horizontal scaling of services
   - Multiple backend instances for load distribution

2. **Traffic Management Features:**
   - Intelligent routing: `/api/` → Backend API, `/tprm/` → TPRM Frontend, `/` → GRC Frontend
   - Timeout management: Connection, send, and read timeouts (60-120 seconds)
   - Optimized buffer configuration (4k buffer size, 8 buffers, 8k busy buffer)

3. **Security Features:**
   - Gzip compression enabled
   - Security headers applied at proxy level
   - Keep-alive connections for efficiency
   - Client limits: `client_max_body_size: 20M` for file uploads

4. **Service Architecture:**
   - Docker Compose multi-container setup with service discovery
   - Container networking for service communication
   - Service isolation in separate containers

5. **Note on Service Mesh:**
   - No dedicated service mesh (e.g., Istio, Linkerd) currently implemented
   - Nginx serves as primary traffic management and load balancing solution
   - Architecture supports future service mesh integration if needed

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

**Prepared by:** Vardaan Team  
**Date:** 2025-01-27  
**Review Status:** Ready for KPMG Review
