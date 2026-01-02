# TPRM Platform - Integrated Risk Management System

> A comprehensive enterprise platform for Third-Party Risk Management, RFP Management, Vendor Lifecycle Management, Contract Management, and Business Continuity Planning.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen.svg)](https://vuejs.org/)
[![Django](https://img.shields.io/badge/Django-4.x-green.svg)](https://www.djangoproject.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-blue.svg)](https://www.mysql.com/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Modules](#system-modules)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Security](#security)
- [Contributing](#contributing)
- [Support](#support)
- [License](#license)

---

## 🌟 Overview

The TPRM Platform is an enterprise-grade, multi-module system designed to streamline and automate risk management, vendor management, RFP processes, contract lifecycle management, and business continuity planning. Built with modern technologies, it provides a scalable, secure, and user-friendly solution for organizations of all sizes.

### **What Makes This Platform Unique?**

- **Integrated Modules**: All risk management functions in one platform
- **Intelligent Automation**: AI-powered risk analysis and contract processing
- **Role-Based Access Control**: Granular permissions and approval workflows
- **Real-Time Collaboration**: Multi-stakeholder evaluation and approval processes
- **OCR & Document Processing**: Automated contract extraction and analysis
- **Advanced Analytics**: Comprehensive dashboards and reporting
- **Vendor Portal**: Self-service portal for vendor interactions
- **Audit Trail**: Complete tracking of all activities and decisions

---

## 🚀 Key Features

### **Multi-Tenant Architecture**
- Support for multiple organizations
- Isolated data and configurations
- Shared or dedicated resources

### **Advanced Security**
- Role-based access control (RBAC)
- Multi-factor authentication (MFA)
- SOC 2 compliance ready
- Encrypted data storage
- Audit logging

### **Intelligent Workflows**
- Customizable approval workflows
- Automated notifications
- Escalation mechanisms
- SLA monitoring

### **Analytics & Reporting**
- Real-time dashboards
- Custom report builder
- Data export capabilities
- Trend analysis
- Risk scoring

### **Integration Ready**
- REST API
- Webhook support
- SSO integration
- Third-party system connectors

---

## 🏗️ System Modules

### 1. **RFP Management System**

Streamline your entire RFP lifecycle from creation to award.

**Features:**
- ✅ **9-Phase RFP Workflow**
  - Phase 1: RFP Creation & Planning
  - Phase 2: Requirement Definition
  - Phase 3: Vendor Selection & Invitation
  - Phase 4: Document Distribution
  - Phase 5: Question & Answer Management
  - Phase 6: Proposal Submission & Tracking
  - Phase 7: Evaluation & Scoring
  - Phase 8: Consensus Building
  - Phase 9: Award & Notification

- ✅ **Vendor Portal**
  - Secure document upload (S3 integration)
  - Real-time submission status
  - Q&A interaction
  - Proposal templates

- ✅ **Evaluation System**
  - Multi-criteria scoring
  - Weighted evaluation
  - Consensus ranking
  - Shortlisting mechanism

- ✅ **Award Notification**
  - Automated email notifications
  - Acceptance/rejection tracking
  - Next vendor selection
  - Audit trail

**Tech Highlights:**
- Vue.js 3 with Composition API
- Vuetify 3 UI framework
- Real-time collaboration
- Document version control

---

### 2. **Vendor Management System (VendorGuard Hub)**

Complete vendor lifecycle management from onboarding to offboarding.

**Features:**
- ✅ **Vendor Onboarding**
  - Digital application forms
  - Document verification
  - Compliance checks
  - Background screening

- ✅ **Vendor Assessment**
  - Risk questionnaires
  - Financial health monitoring
  - Performance tracking
  - Compliance validation

- ✅ **Vendor Portal**
  - Self-service profile management
  - Document uploads
  - Communication center
  - Request tracking

- ✅ **Vendor Lifecycle**
  - Approval workflows
  - Status management
  - Renewal tracking
  - Offboarding processes

**Tech Highlights:**
- Vue 3 with Pinia state management
- Element Plus components
- Real-time status updates
- Advanced search and filtering

---

### 3. **Contract Management System (ContractHub)**

Enterprise contract lifecycle management with AI-powered features.

**Features:**
- ✅ **Contract Repository**
  - Centralized storage
  - Version control
  - Full-text search
  - Metadata management

- ✅ **OCR Processing**
  - Automated contract extraction
  - Key clause identification
  - Data validation
  - Structured data export

- ✅ **Contract Analysis**
  - Risk identification
  - Entity extraction
  - Clause comparison
  - Compliance checking

- ✅ **Audit Management**
  - Activity tracking
  - Change history
  - Compliance reports
  - Access logs

**Tech Highlights:**
- Django REST Framework
- OCR microservice
- LLaMA AI integration
- PostgreSQL/MySQL support

---

### 4. **Business Continuity Planning (BCP/DRP)**

Comprehensive business continuity and disaster recovery planning.

**Features:**
- ✅ **Plan Management**
  - BCP/DRP creation
  - Template library
  - Section management
  - Version control

- ✅ **OCR Plan Submission**
  - Document upload
  - Automated extraction
  - Data validation
  - Review workflow

- ✅ **Questionnaire Workflow**
  - Custom questionnaires
  - Section-based responses
  - Progress tracking
  - Approval process

- ✅ **Dashboard & Analytics**
  - Plan status overview
  - Compliance tracking
  - Gap analysis
  - Reporting

**Tech Highlights:**
- Vue 3 with Vuex
- Vuetify 3 UI
- Real-time updates
- PDF generation

---

### 5. **SLA Management**

Service Level Agreement tracking and monitoring.

**Features:**
- ✅ **SLA Creation**
  - Template management
  - Metric definition
  - Threshold configuration
  - Vendor assignment

- ✅ **Monitoring & Tracking**
  - Real-time compliance
  - Performance metrics
  - Breach detection
  - Alert notifications

- ✅ **Notifications**
  - Automated alerts
  - Escalation workflows
  - Email/SMS notifications
  - Dashboard updates

- ✅ **Reporting**
  - Performance reports
  - Trend analysis
  - Compliance dashboards
  - Export capabilities

**Tech Highlights:**
- Vue 3 components
- Chart.js visualizations
- Real-time monitoring
- Notification system

---

### 6. **Risk Analysis**

AI-powered risk assessment and analysis.

**Features:**
- ✅ **Vendor Risk Analysis**
  - Automated risk scoring
  - Multi-dimensional assessment
  - Historical tracking
  - Risk heatmaps

- ✅ **Contract Risk Analysis**
  - LLaMA AI integration
  - Clause risk identification
  - Entity extraction
  - Comprehensive risk reports

- ✅ **RFP Risk Analysis**
  - Proposal risk scoring
  - Comparative analysis
  - Risk mitigation suggestions
  - Decision support

**Tech Highlights:**
- LLaMA AI service
- Python-based analysis
- Real-time processing
- API integration

---

## 💻 Technology Stack

### **Frontend**

| Technology | Version | Purpose |
|------------|---------|---------|
| Vue.js | 3.5.22 | Progressive JavaScript framework |
| Vuetify | 3.10.3 | Material Design component library |
| Element Plus | 2.11.4 | Vue 3 component library |
| Vue Router | 4.5.1 | Official router for Vue.js |
| Pinia | 2.3.1 | State management |
| Vuex | 4.1.0 | Legacy state management |
| Axios | 1.12.2 | HTTP client |
| Chart.js | 4.5.0 | Data visualization |
| Recharts | 2.15.4 | React charts (for Contract module) |
| Vite | 5.4.20 | Build tool and dev server |

### **Backend**

| Technology | Version | Purpose |
|------------|---------|---------|
| Django | 4.x | Python web framework |
| Django REST Framework | - | RESTful API development |
| MySQL | 8.0 | Primary database |
| PostgreSQL | - | Alternative database (JSONB support) |
| Celery | - | Async task processing |
| Redis | - | Caching and message broker |
| AWS S3 | - | Document storage |
| Python | 3.11+ | Backend language |

### **AI/ML**

| Technology | Purpose |
|------------|---------|
| LLaMA | Contract analysis and entity extraction |
| Custom NLP | Risk analysis and scoring |
| OCR Services | Document processing |

### **DevOps & Infrastructure**

| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Nginx | Web server and reverse proxy |
| Apache | Alternative web server |
| Git | Version control |
| CI/CD | Automated deployment |

---

## 🏛️ Architecture

### **Multi-Page Application (MPA)**

The platform uses a Multi-Page Application architecture with separate entry points:

```
┌─────────────────────────────────────────────┐
│          Nginx / Apache (Reverse Proxy)     │
└─────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼──────┐
│   Frontend     │    │   Backend     │
│   (Vue.js)     │    │   (Django)    │
├────────────────┤    ├───────────────┤
│ • RFP Module   │    │ • REST API    │
│ • Vendor Hub   │    │ • Business    │
│ • Contract Hub │◄───┤   Logic       │
│ • BCP Module   │    │ • Auth/RBAC   │
│ • SLA Module   │    │ • OCR Service │
└────────────────┘    └───────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
           ┌────────▼──────┐  ┌──────▼──────┐
           │   MySQL DB    │  │   AWS S3    │
           │               │  │  (Storage)  │
           └───────────────┘  └─────────────┘
```

### **Database Schema**

**Core Tables:**
- `users` - User accounts and authentication
- `vendors` - Vendor profiles and information
- `rfps` - RFP records and metadata
- `rfp_responses` - Vendor proposal submissions
- `contracts` - Contract repository
- `slas` - Service level agreements
- `notifications` - System notifications
- `audit_logs` - Activity tracking
- `approval_workflows` - Workflow definitions
- `approval_requests` - Approval instances

---

## 📦 Installation

### **Prerequisites**

- **Node.js** >= 18.0.0
- **Python** >= 3.11
- **MySQL** >= 8.0 or **PostgreSQL** >= 13
- **Redis** (for caching and Celery)
- **AWS Account** (for S3 storage)
- **Git**

### **Step 1: Clone Repository**

```bash
git clone https://github.com/your-org/tprm-platform.git
cd tprm-platform
```

### **Step 2: Backend Setup**

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp (contract).env .env

# Update database settings in .env
# DATABASE_NAME=tprm_integration
# DATABASE_USER=your_user
# DATABASE_PASSWORD=your_password
# DATABASE_HOST=localhost
# DATABASE_PORT=3306

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Start development server
python manage.py runserver
```

### **Step 3: Frontend Setup**

```bash
# Navigate to project root
cd ..

# Install Node dependencies
npm install

# Start development server
npm run dev
```

### **Step 4: Additional Modules**

For specific modules, you can start individual dev servers:

```bash
# RFP Module
npm run dev:rfp

# Vendor Module
npm run dev:vendor

# Contract Module
npm run dev:contract

# BCP Module
npm run dev:bcp
```

---

## ⚙️ Configuration

### **Environment Variables**

Create a `.env` file in the backend directory:

```env
# Database Configuration
DATABASE_NAME=tprm_integration
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=3306

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Configuration (for notifications)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@example.com

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# LLaMA AI Service (optional)
LLAMA_API_URL=http://localhost:8080
LLAMA_API_KEY=your-api-key
```

### **Frontend Configuration**

Update API endpoints in frontend configuration files:

**For RFP Module:**
```javascript
// src/config/api.js
export const API_BASE_URL = 'http://localhost:8000/api/v1'
export const S3_BUCKET_URL = 'https://your-bucket.s3.amazonaws.com'
```

### **Database Setup**

```sql
-- Create database
CREATE DATABASE tprm_integration CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (if needed)
CREATE USER 'tprm_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON tprm_integration.* TO 'tprm_user'@'localhost';
FLUSH PRIVILEGES;
```

---

## 🎯 Usage

### **Access Points**

After starting both backend and frontend servers:

- **Main Dashboard**: http://localhost:3000/
- **RFP Management**: http://localhost:3000/rfp-dashboard
- **Vendor Management**: http://localhost:3000/vendor-dashboard
- **Contract Management**: http://localhost:3000/contract-dashboard
- **BCP Management**: http://localhost:3000/bcp-dashboard
- **SLA Management**: http://localhost:3000/sla-management
- **Admin Panel**: http://localhost:8000/admin

### **User Roles**

The platform supports multiple user roles:

1. **Super Admin** - Full system access
2. **Admin** - Module-level administration
3. **Manager** - Department-level management
4. **User** - Standard user access
5. **Vendor** - Vendor portal access
6. **Auditor** - Read-only audit access

### **Quick Start Guide**

#### **Creating an RFP**

1. Navigate to RFP Dashboard
2. Click "Create New RFP"
3. Follow the 9-phase wizard:
   - Define RFP details
   - Add requirements and criteria
   - Select vendors
   - Distribute documents
   - Manage Q&A
   - Receive proposals
   - Evaluate submissions
   - Build consensus
   - Award to winner

#### **Managing Vendors**

1. Navigate to Vendor Management
2. Add new vendor or import from CSV
3. Configure approval workflow
4. Track vendor lifecycle
5. Monitor compliance and performance

#### **Processing Contracts**

1. Navigate to Contract Management
2. Upload contract document
3. OCR automatically extracts data
4. Review and validate extracted information
5. Perform risk analysis
6. Store in repository

---

## 📚 API Documentation

### **Base URL**

```
http://localhost:8000/api/v1
```

### **Authentication**

All API requests require authentication using JWT tokens:

```bash
# Login to get token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token in subsequent requests
curl -X GET http://localhost:8000/api/v1/rfps/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### **Key Endpoints**

#### **RFP Management**

```
GET    /api/v1/rfps/                    # List all RFPs
POST   /api/v1/rfps/                    # Create new RFP
GET    /api/v1/rfps/{id}/               # Get RFP details
PUT    /api/v1/rfps/{id}/               # Update RFP
DELETE /api/v1/rfps/{id}/               # Delete RFP
POST   /api/v1/rfps/{id}/publish/       # Publish RFP
GET    /api/v1/rfps/{id}/responses/     # Get responses
POST   /api/v1/rfps/{id}/award-notification/ # Send award
```

#### **Vendor Management**

```
GET    /api/v1/vendors/                 # List vendors
POST   /api/v1/vendors/                 # Create vendor
GET    /api/v1/vendors/{id}/            # Get vendor details
PUT    /api/v1/vendors/{id}/            # Update vendor
POST   /api/v1/vendors/{id}/approve/    # Approve vendor
```

#### **Contract Management**

```
GET    /api/v1/contracts/               # List contracts
POST   /api/v1/contracts/upload/        # Upload contract
POST   /api/v1/contracts/{id}/ocr/      # Process OCR
GET    /api/v1/contracts/{id}/analysis/ # Risk analysis
```

#### **SLA Management**

```
GET    /api/v1/slas/                    # List SLAs
POST   /api/v1/slas/                    # Create SLA
GET    /api/v1/slas/{id}/metrics/       # Get metrics
POST   /api/v1/slas/{id}/breach/        # Report breach
```

For complete API documentation, visit: http://localhost:8000/api/docs

---

## 🚢 Deployment

### **Production Build**

#### **Frontend**

```bash
# Build all modules
npm run build

# Build specific module
npm run build:rfp
npm run build:vendor
npm run build:contract
npm run build:bcp
```

This generates optimized static files in the `dist/` directory.

#### **Backend**

```bash
# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create cache tables
python manage.py createcachetable
```

### **Docker Deployment**

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### **Nginx Configuration**

Use the provided `nginx.conf` for production deployment:

```nginx
# See nginx.conf in project root
```

### **Apache Configuration**

Alternatively, use the provided `apache.conf`:

```apache
# See apache.conf in project root
```

---

## 🔒 Security

### **Security Features**

- ✅ **Role-Based Access Control (RBAC)**
- ✅ **Multi-Factor Authentication (MFA)**
- ✅ **Data Encryption at Rest**
- ✅ **SSL/TLS Encryption in Transit**
- ✅ **CSRF Protection**
- ✅ **XSS Prevention**
- ✅ **SQL Injection Protection**
- ✅ **Rate Limiting**
- ✅ **Audit Logging**
- ✅ **Session Management**

### **Best Practices**

1. **Environment Variables**: Never commit sensitive data
2. **HTTPS**: Always use HTTPS in production
3. **Database**: Use strong passwords and limited access
4. **API Keys**: Rotate regularly
5. **Backups**: Implement regular backup strategy
6. **Updates**: Keep dependencies updated
7. **Monitoring**: Implement security monitoring

### **Compliance**

The platform is designed to support:
- SOC 2 compliance
- GDPR compliance
- HIPAA compliance (with additional configuration)
- ISO 27001 standards

---

## 🧪 Testing

### **Backend Tests**

```bash
cd backend
python manage.py test

# Run specific tests
python manage.py test rfp.tests
python manage.py test vendors.tests

# Coverage report
coverage run --source='.' manage.py test
coverage report
```

### **Frontend Tests**

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### **Development Workflow**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Code Standards**

- **Frontend**: Follow Vue.js style guide
- **Backend**: Follow PEP 8 Python style guide
- **Commits**: Use conventional commit messages
- **Documentation**: Update relevant docs

### **Pull Request Process**

1. Update README.md with details of changes
2. Update API documentation if applicable
3. Ensure all tests pass
4. Get approval from maintainers

---

## 📊 Performance

### **Benchmarks**

- **Page Load**: < 2 seconds
- **API Response**: < 200ms (average)
- **Concurrent Users**: 1000+ (with proper scaling)
- **Database Queries**: Optimized with indexing
- **File Upload**: Supports files up to 100MB

### **Optimization**

- Lazy loading of modules
- Code splitting
- CDN for static assets
- Database query optimization
- Redis caching
- Gzip compression

---

## 🐛 Troubleshooting

### **Common Issues**

#### **Frontend Won't Start**

```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### **Backend Database Connection Error**

```bash
# Check database is running
mysql -u root -p

# Verify credentials in .env file
# Run migrations again
python manage.py migrate
```

#### **Award Notification Not Sending**

See detailed debugging guide: [AWARD_NOTIFICATION_DEBUGGING.md](AWARD_NOTIFICATION_DEBUGGING.md)

#### **File Upload Failures**

- Check AWS S3 credentials
- Verify bucket permissions
- Check file size limits

For more issues, see our [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

---

## 📖 Documentation

- **API Documentation**: `/docs/API.md`
- **User Guide**: `/docs/USER_GUIDE.md`
- **Admin Guide**: `/docs/ADMIN_GUIDE.md`
- **Development Guide**: `/docs/DEVELOPMENT.md`
- **Deployment Guide**: `/docs/DEPLOYMENT.md`

Additional Resources:
- [Award Notification Debugging](AWARD_NOTIFICATION_DEBUGGING.md)
- [Award Notification Fix Guide](AWARD_NOTIFICATION_FIX_GUIDE.md)
- [Changes Summary](CHANGES_SUMMARY.md)
- [Vendor Portal Response Structure](VENDOR_PORTAL_RESPONSE_STRUCTURE.md)

---

## 🎓 Training & Support

### **Training Resources**

- Video tutorials (coming soon)
- Interactive demos
- Documentation portal
- Sample data sets

### **Support Channels**

- **Email**: support@tprm-platform.com
- **Slack**: [Join our community](#)
- **GitHub Issues**: For bug reports and feature requests
- **Stack Overflow**: Tag `tprm-platform`

### **Professional Services**

- Implementation consulting
- Custom development
- Training sessions
- Dedicated support

---

## 🗺️ Roadmap

### **Q2 2025**
- [ ] Mobile application (iOS/Android)
- [ ] Advanced AI/ML features
- [ ] Enhanced reporting engine
- [ ] API v2 with GraphQL

### **Q3 2025**
- [ ] Blockchain integration for audit trail
- [ ] Advanced analytics dashboard
- [ ] Third-party integrations (SAP, Oracle)
- [ ] Multi-language support

### **Q4 2025**
- [ ] Advanced workflow builder
- [ ] Custom module framework
- [ ] Enhanced mobile features
- [ ] AI-powered recommendations

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 TPRM Platform

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- Vue.js team for the amazing framework
- Django team for the robust backend framework
- All open-source contributors
- Our amazing community

---

## 📞 Contact

**Development Team**
- Website: https://tprm-platform.com
- Email: dev@tprm-platform.com
- Twitter: @TPRMPlatform
- LinkedIn: TPRM Platform

**Project Maintainer**
- GitHub: @your-username
- Email: khairunnisa.s@vardaanglobal.com

---

## ⭐ Star History

If you find this project useful, please consider giving it a star!

[![Star History Chart](https://api.star-history.com/svg?repos=your-org/tprm-platform&type=Date)](https://star-history.com/#your-org/tprm-platform&Date)

---

<div align="center">

**Built with ❤️ by the TPRM Platform Team**

[Documentation](docs/) · [Report Bug](issues/) · [Request Feature](issues/)

</div>
