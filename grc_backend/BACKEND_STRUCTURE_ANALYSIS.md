# Backend Structure Analysis

## 📋 Overview

The backend is a **multi-project Django application** that combines GRC (Governance, Risk, and Compliance) and TPRM (Third-Party Risk Management) functionalities into a unified system.

---

## 🏗️ Directory Structure

```
grc_backend/
├── manage.py                          # Root manage.py (uses backend.settings)
├── requirements.txt                   # Main Python dependencies
├── docker-compose.yml                # Docker configuration
├── Dockerfile                         # Docker image definition
│
├── tprm_backend/                      # Main TPRM backend directory
│   ├── manage.py                      # Main TPRM manage.py (uses vendor_guard_hub.settings)
│   ├── manage_vendor.py               # Vendor-specific manage.py
│   ├── manage_rfp.py                  # RFP-specific manage.py
│   ├── manage_ocr.py                  # OCR-specific manage.py
│   ├── manage_contract.py             # Contract-specific manage.py
│   ├── manage_bcp.py                  # BCP/DRP-specific manage.py
│   │
│   ├── vendor_guard_hub/              # Main Django project (PRIMARY)
│   │   ├── settings.py                # Main settings file
│   │   ├── urls.py                    # Main URL routing
│   │   ├── wsgi.py                    # WSGI configuration
│   │   ├── asgi.py                    # ASGI configuration
│   │   └── celery.py                  # Celery configuration
│   │
│   ├── config/                        # Alternative Django project
│   │   ├── settings.py                # Alternative settings
│   │   ├── urls.py                    # Alternative URL routing
│   │   ├── wsgi.py
│   │   └── celery.py
│   │
│   ├── tprm_project/                  # Another project configuration
│   │   └── settings.py
│   │
│   ├── mfa_project/                   # MFA-specific project
│   │   └── settings.py
│   │
│   ├── ocr_microservice/              # OCR microservice project
│   │   └── settings.py
│   │
│   ├── apps/                          # Vendor-related apps (namespaced)
│   │   ├── vendor_core/               # Core vendor functionality
│   │   ├── vendor_auth/                # Vendor authentication
│   │   ├── vendor_risk/                # Vendor risk management
│   │   ├── vendor_questionnaire/       # Vendor questionnaires
│   │   ├── vendor_dashboard/           # Vendor dashboard
│   │   ├── vendor_lifecycle/           # Vendor lifecycle management
│   │   └── vendor_approval/            # Vendor approval workflows
│   │
│   ├── core/                          # Core TPRM functionality
│   ├── slas/                          # SLA management
│   ├── audits/                        # Audit management
│   ├── audits_contract/               # Contract audits
│   ├── compliance/                    # Compliance tracking
│   ├── bcpdrp/                        # Business Continuity/Disaster Recovery
│   ├── risk_analysis/                 # Risk analysis
│   ├── contract_risk_analysis/        # Contract risk analysis
│   ├── contracts/                     # Contract management
│   ├── rfp/                           # RFP (Request for Proposal) management
│   ├── rfp_approval/                  # RFP approval workflows
│   ├── rfp_risk_analysis/             # RFP risk analysis
│   ├── mfa_auth/                      # Multi-factor authentication
│   ├── rbac/                          # Role-Based Access Control
│   ├── admin_access/                  # Admin access control
│   ├── notifications/                 # Notification system
│   ├── quick_access/                  # Quick access features
│   ├── global_search/                 # Global search functionality
│   ├── ocr_app/                       # OCR application
│   ├── risk_analysis_vendor/          # Vendor risk analysis
│   ├── users/                         # User management
│   ├── vendors/                       # Vendor models (legacy)
│   ├── analytics/                     # Analytics (disabled)
│   ├── performance/                   # Performance monitoring (disabled)
│   │
│   ├── middleware/                    # Custom middleware
│   ├── utils/                         # Utility functions
│   ├── database/                      # Database utilities
│   ├── tasks/                         # Celery tasks
│   ├── scripts/                       # Management scripts
│   ├── logs/                          # Log files
│   ├── media/                         # Media files
│   ├── staticfiles/                   # Static files
│   ├── backups/                       # Backup files
│   │
│   ├── vendor_router.py               # Database router for vendor apps
│   ├── s3.py                          # AWS S3 integration
│   ├── tprm_logging.py                # Logging configuration
│   └── requirements.txt               # TPRM-specific requirements
│
└── backend/                           # GRC backend (if exists)
    └── settings.py
```

---

## 🎯 Django Projects

### 1. **vendor_guard_hub** (PRIMARY PROJECT)
- **Settings**: `tprm_backend/vendor_guard_hub/settings.py`
- **URLs**: `tprm_backend/vendor_guard_hub/urls.py`
- **Purpose**: Main TPRM Django project
- **Used by**: `tprm_backend/manage.py`

**Key Features**:
- Combines all TPRM apps
- Vendor management apps
- SLA, Audit, Compliance, BCP/DRP modules
- RFP and Contract management
- Risk analysis modules
- MFA and RBAC

### 2. **config** (ALTERNATIVE PROJECT)
- **Settings**: `tprm_backend/config/settings.py`
- **URLs**: `tprm_backend/config/urls.py`
- **Purpose**: Alternative configuration for vendor-specific operations
- **Focus**: Vendor apps with enhanced security middleware

### 3. **tprm_project** (LEGACY PROJECT)
- **Settings**: `tprm_backend/tprm_project/settings.py`
- **Purpose**: Legacy project configuration

### 4. **mfa_project** (MFA PROJECT)
- **Settings**: `tprm_backend/mfa_project/settings.py`
- **Purpose**: MFA-specific Django project

### 5. **ocr_microservice** (OCR PROJECT)
- **Settings**: `tprm_backend/ocr_microservice/settings.py`
- **Purpose**: OCR microservice Django project

---

## 📦 Application Organization

### **Vendor Apps** (in `apps/` directory)
All vendor-related apps are namespaced under `apps/`:

1. **apps.vendor_core**
   - Core vendor functionality
   - Vendor registration and profiles
   - Health check endpoints

2. **apps.vendor_auth**
   - Vendor authentication
   - JWT token management

3. **apps.vendor_risk**
   - Vendor risk assessment
   - Risk scoring and analysis

4. **apps.vendor_questionnaire**
   - Questionnaire management
   - Vendor responses

5. **apps.vendor_dashboard**
   - Vendor dashboard data
   - Analytics and metrics

6. **apps.vendor_lifecycle**
   - Vendor lifecycle stages
   - Stage transitions

7. **apps.vendor_approval**
   - Vendor approval workflows
   - Approval management

### **Core TPRM Apps** (at root level)

1. **core** - Core functionality and utilities
2. **slas** - Service Level Agreement management
3. **audits** - Audit management and tracking
4. **audits_contract** - Contract-specific audits
5. **compliance** - Compliance framework management
6. **bcpdrp** - Business Continuity and Disaster Recovery Planning
7. **risk_analysis** - General risk analysis
8. **contract_risk_analysis** - Contract risk assessment
9. **contracts** - Contract repository and management
10. **rfp** - Request for Proposal management
11. **rfp_approval** - RFP approval workflows
12. **rfp_risk_analysis** - RFP risk analysis
13. **mfa_auth** - Multi-factor authentication
14. **rbac** - Role-Based Access Control
15. **admin_access** - Admin access control (no RBAC/MFA dependency)
16. **notifications** - Notification system
17. **quick_access** - Quick access features
18. **global_search** - Global search across modules
19. **ocr_app** - OCR document processing
20. **risk_analysis_vendor** - Vendor-specific risk analysis

### **Disabled/Inactive Apps**
- `performance` - Temporarily disabled (model conflicts)
- `analytics` - Temporarily disabled (model conflicts)
- `vendors` - Temporarily disabled (model conflicts)
- `users` - Temporarily disabled (model conflicts)

---

## 🔌 API Endpoint Structure

### **Main API Routes** (from `vendor_guard_hub/urls.py`)

```
/api/
├── auth/                              # Authentication (MFA)
├── rbac/                              # Role-Based Access Control
├── admin-access/                      # Admin access control
├── global-search/                     # Global search
├── ocr/                               # OCR services
├── slas/                              # SLA management
├── audits/                            # Audit management
├── notifications/                     # Notifications
├── quick-access/                      # Quick access
├── compliance/                        # Compliance
├── bcpdrp/                            # BCP/DRP
├── risk-analysis/                     # Risk analysis
├── contracts/                         # Contract management
├── audits-contract/                   # Contract audits
├── contract-risk-analysis/            # Contract risk analysis
│
├── v1/
│   ├── vendor-core/                   # Vendor core APIs
│   ├── vendor-auth/                   # Vendor authentication
│   ├── vendor-risk/                   # Vendor risk
│   ├── vendor-questionnaire/          # Vendor questionnaires
│   ├── vendor-dashboard/              # Vendor dashboard
│   ├── vendor-lifecycle/              # Vendor lifecycle
│   ├── vendor-approval/               # Vendor approval
│   └── [rfp routes]                   # RFP management
│
├── vendor-core/                       # Vendor API aliases
├── vendor-auth/
├── vendor-risk/
├── vendor-questionnaire/
├── vendor-dashboard/
├── vendor-lifecycle/
├── vendor-approval/
│
├── approval/                          # RFP approval
├── rfp-approval/                      # RFP approval (alias)
└── docs/                              # API documentation (Swagger)
```

---

## 🗄️ Database Configuration

### **Database Router**
- **File**: `tprm_backend/vendor_router.py`
- **Purpose**: Routes vendor apps to appropriate database
- **Apps Routed**:
  - `apps.vendor_core`
  - `apps.vendor_auth`
  - `apps.vendor_risk`
  - `apps.vendor_questionnaire`
  - `apps.vendor_dashboard`
  - `apps.vendor_lifecycle`
  - `apps.vendor_approval`
  - `risk_analysis_vendor`

### **Database Setup**
- **Primary Database**: MySQL (configured in settings)
- **Database Name**: `tprm_integration` (default)
- **Connection**: AWS RDS (ap-south-1)

---

## 🔧 Multiple Manage.py Files

The backend uses **multiple manage.py files** for different purposes:

1. **`grc_backend/manage.py`**
   - Uses: `backend.settings`
   - Purpose: Root-level Django management

2. **`tprm_backend/manage.py`**
   - Uses: `vendor_guard_hub.settings`
   - Purpose: Main TPRM project management

3. **`tprm_backend/manage_vendor.py`**
   - Uses: `vendor_guard_hub.settings`
   - Purpose: Vendor-specific operations

4. **`tprm_backend/manage_rfp.py`**
   - Uses: `vendor_guard_hub.settings`
   - Purpose: RFP-specific operations

5. **`tprm_backend/manage_ocr.py`**
   - Uses: `ocr_microservice.settings`
   - Purpose: OCR microservice management

6. **`tprm_backend/manage_contract.py`**
   - Uses: `vendor_guard_hub.settings`
   - Purpose: Contract-specific operations

7. **`tprm_backend/manage_bcp.py`**
   - Uses: `settings_bcp.py`
   - Purpose: BCP/DRP-specific operations

---

## 🛠️ Technology Stack

### **Core Framework**
- **Django**: 4.2.7
- **Django REST Framework**: 3.14.0+
- **Python**: 3.8+

### **Database**
- **MySQL**: Primary database
- **SQLAlchemy**: ORM for complex queries
- **Redis**: Caching and Celery broker

### **Authentication & Security**
- **JWT**: Simple JWT for authentication
- **MFA**: Multi-factor authentication
- **RBAC**: Role-Based Access Control
- **CORS**: Cross-origin resource sharing

### **Background Tasks**
- **Celery**: Async task processing
- **Celery Beat**: Scheduled tasks

### **AI/ML**
- **LangChain**: AI framework
- **OpenAI**: AI provider
- **ChromaDB**: Vector database
- **Sentence Transformers**: Embeddings

### **Document Processing**
- **OCR**: Tesseract (pytesseract)
- **PDF**: PyPDF2, PyMuPDF, pdfplumber
- **Office**: openpyxl, python-docx

### **Storage**
- **AWS S3**: File storage (via boto3)
- **Django Storages**: S3 integration

### **API Documentation**
- **drf-yasg**: Swagger/OpenAPI documentation

---

## 🔐 Security Features

### **Middleware Stack**
1. SecurityMiddleware
2. WhiteNoiseMiddleware (static files)
3. CorsMiddleware
4. SessionMiddleware
5. CommonMiddleware
6. CsrfViewMiddleware
7. **VendorSecurityMiddleware** (custom)
8. **VendorInputValidationMiddleware** (custom)
9. **VendorRateLimitMiddleware** (custom)
10. **VendorAccessControlMiddleware** (custom)
11. AuthenticationMiddleware
12. MessagesMiddleware
13. **VendorLoggingMiddleware** (custom)

### **Security Components**
- Input validation
- Rate limiting
- Access control
- Security logging
- CSRF protection
- CORS configuration

---

## 📊 Key Features

### **1. Vendor Management**
- Vendor registration and onboarding
- Vendor lifecycle management
- Vendor approval workflows
- Vendor risk assessment
- Vendor questionnaires
- Vendor dashboard

### **2. Contract Management**
- Contract repository
- Contract risk analysis
- Contract audits
- Contract approval workflows

### **3. RFP Management**
- RFP creation and management
- Vendor selection
- RFP risk analysis
- RFP approval workflows
- Vendor portal for RFP responses

### **4. Risk Management**
- General risk analysis
- Contract risk analysis
- RFP risk analysis
- Vendor risk assessment
- AI-powered risk analysis

### **5. Compliance**
- Compliance framework management
- Audit management
- Evidence collection
- Compliance tracking

### **6. SLA Management**
- SLA definition and tracking
- SLA compliance monitoring
- SLA violations
- Performance metrics

### **7. BCP/DRP**
- Business Continuity Planning
- Disaster Recovery Planning
- BCP/DRP workflows

### **8. Authentication & Authorization**
- Multi-factor authentication (MFA)
- Role-Based Access Control (RBAC)
- JWT token management
- Admin access control

### **9. Document Processing**
- OCR for document extraction
- PDF processing
- Document analysis
- AI-powered document understanding

### **10. Notifications & Search**
- Notification system
- Global search across modules
- Quick access features

---

## 🚀 Deployment

### **Docker Configuration**
- **Dockerfile**: Container definition
- **docker-compose.yml**: Multi-container setup
- **Port**: 8000 (backend)
- **Volumes**: MEDIA_ROOT, TEMP_MEDIA_ROOT, Reports

### **Environment Variables**
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `REDIS_URL`: Redis connection URL

---

## ⚠️ Known Issues & Notes

1. **Multiple Django Projects**: The backend has multiple Django project configurations, which can cause confusion. The primary project is `vendor_guard_hub`.

2. **Disabled Apps**: Some apps (performance, analytics, vendors, users) are temporarily disabled due to model conflicts.

3. **Database Router**: Vendor apps use a database router, but it currently routes to 'default' database.

4. **Middleware**: Some vendor-specific middleware is commented out in the main settings but active in config settings.

5. **Multiple Manage.py**: Multiple manage.py files exist for different purposes, which can be confusing.

6. **Settings Files**: Multiple settings files exist across different project directories.

---

## 📝 Recommendations

1. **Consolidate Projects**: Consider consolidating multiple Django projects into a single unified project.

2. **Standardize Settings**: Use a single settings file with environment-based configuration.

3. **Unify Manage.py**: Use a single manage.py with command-line arguments for different operations.

4. **Enable Disabled Apps**: Resolve model conflicts and re-enable disabled apps.

5. **Documentation**: Add comprehensive API documentation and architecture diagrams.

6. **Testing**: Add unit tests and integration tests for all modules.

7. **Database Strategy**: Clarify database routing strategy and document it.

---

## 🔍 Key Files to Review

1. **`tprm_backend/vendor_guard_hub/settings.py`** - Main settings
2. **`tprm_backend/vendor_guard_hub/urls.py`** - Main URL routing
3. **`tprm_backend/vendor_router.py`** - Database routing
4. **`grc_backend/requirements.txt`** - Dependencies
5. **`grc_backend/docker-compose.yml`** - Deployment config

---

**Last Updated**: 2024-12-22
**Analysis Version**: 1.0

