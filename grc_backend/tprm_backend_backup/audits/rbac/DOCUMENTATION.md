# TPRM RBAC System - Complete Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Design](#architecture-design)
3. [Database Schema](#database-schema)
4. [Core Components](#core-components)
5. [Permission System](#permission-system)
6. [Implementation Patterns](#implementation-patterns)
7. [API Reference](#api-reference)
8. [Usage Examples](#usage-examples)
9. [Security Model](#security-model)
10. [Deployment Guide](#deployment-guide)
11. [Testing Strategy](#testing-strategy)
12. [Troubleshooting](#troubleshooting)

## 1. System Overview

### 1.1 Purpose
The TPRM (Third Party Risk Management) RBAC system provides granular, permission-based access control for enterprise TPRM applications. It manages user permissions across 6 core modules with 100+ individual permission flags.

### 1.2 Key Features
- **Granular Permissions**: 100+ boolean permission flags
- **Module-Based Organization**: 6 distinct TPRM modules
- **JWT Integration**: Secure token-based authentication
- **Decorator Pattern**: Clean, reusable permission checking
- **Comprehensive Logging**: Full audit trail of permission decisions
- **Flexible Mapping**: Support for multiple permission naming conventions

### 1.3 Supported Modules
1. **RFP (Request for Proposal)** - 40+ permissions
2. **Contract Management** - 20+ permissions  
3. **Vendor Management** - 15+ permissions
4. **Risk Management** - 10+ permissions
5. **Compliance & Audit** - 10+ permissions
6. **BCP/DRP** - 10+ permissions

## 2. Architecture Design

### 2.1 Layered Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  (Views, API Endpoints, Frontend Integration)              │
├─────────────────────────────────────────────────────────────┤
│                    Decorator Layer                          │
│  (Permission Checking Decorators)                          │
├─────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                     │
│  (RBAC Utilities, Permission Logic)                        │
├─────────────────────────────────────────────────────────────┤
│                    Data Access Layer                        │
│  (Models, Database Queries)                                │
├─────────────────────────────────────────────────────────────┤
│                    Authentication Layer                     │
│  (JWT Validation, User Extraction)                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Relationships
```
Views → Decorators → Utilities → Models → Database
  ↓         ↓           ↓         ↓         ↓
API    Permission   Business   Data     Storage
Layer   Checking    Logic     Access
```

## 3. Database Schema

### 3.1 Table Structure
```sql
CREATE TABLE rbac_tprm (
    RBACId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    UserName VARCHAR(255),
    Role VARCHAR(100),
    
    -- RFP Permissions (40+ fields)
    CreateRFP BOOLEAN DEFAULT FALSE,
    EditRFP BOOLEAN DEFAULT FALSE,
    ViewRFP BOOLEAN DEFAULT FALSE,
    DeleteRFP BOOLEAN DEFAULT FALSE,
    -- ... 36 more RFP permissions
    
    -- Contract Permissions (20+ fields)
    ListContracts BOOLEAN DEFAULT FALSE,
    CreateContract BOOLEAN DEFAULT FALSE,
    UpdateContract BOOLEAN DEFAULT FALSE,
    -- ... 17 more contract permissions
    
    -- Vendor Permissions (15+ fields)
    ViewVendors BOOLEAN DEFAULT FALSE,
    CreateVendor BOOLEAN DEFAULT FALSE,
    -- ... 13 more vendor permissions
    
    -- Risk Permissions (10+ fields)
    AssessVendorRisk BOOLEAN DEFAULT FALSE,
    ViewRiskAssessments BOOLEAN DEFAULT FALSE,
    -- ... 8 more risk permissions
    
    -- Compliance Permissions (10+ fields)
    GenerateComplianceReports BOOLEAN DEFAULT FALSE,
    AuditDocuments BOOLEAN DEFAULT FALSE,
    -- ... 8 more compliance permissions
    
    -- BCP/DRP Permissions (10+ fields)
    CreateBCPStrategy BOOLEAN DEFAULT FALSE,
    EvaluateDRPPlans BOOLEAN DEFAULT FALSE,
    -- ... 8 more BCP/DRP permissions
    
    IsActive CHAR(1) DEFAULT 'Y',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 3.2 Design Principles
- **Wide Table Design**: One row per user, one column per permission
- **Boolean Values**: Simple 0/1 for permission existence
- **User-Centric**: Each user has complete permission profile
- **Role Reference**: Role stored for administrative purposes
- **Active Status**: Soft delete capability with IsActive flag

## 4. Core Components

### 4.1 Models (`models.py`)
```python
class RBACTPRM(models.Model):
    """
    Maps to rbac_tprm table with 100+ permission fields
    Provides helper properties for module access
    """
    
    # Primary Key
    rbac_id = models.AutoField(db_column='RBACId', primary_key=True)
    
    # User Information
    user_id = models.IntegerField(db_column='UserId')
    username = models.CharField(db_column='UserName', max_length=255)
    role = models.CharField(db_column='Role', max_length=100)
    
    # Permission Fields (100+ BooleanField with db_column mapping)
    create_rfp = models.BooleanField(db_column='CreateRFP', default=False)
    view_rfp = models.BooleanField(db_column='ViewRFP', default=False)
    # ... 98+ more permission fields
    
    class Meta:
        db_table = 'rbac_tprm'
        managed = False  # Table exists in database
```

### 4.2 Utilities (`tprm_utils.py`)
```python
class RBACTPRMUtils:
    """
    Core permission checking and utility methods
    """
    
    @staticmethod
    def get_user_id_from_request(request):
        """Extract user_id from JWT token or session"""
        
    @staticmethod
    def check_permission(user_id, permission_name):
        """Check if user has specific permission"""
        
    @staticmethod
    def check_rfp_permission(user_id, permission_type):
        """Check RFP-specific permissions with mapping"""
        
    @staticmethod
    def get_user_permissions_summary(user_id):
        """Get comprehensive permission summary by module"""
        
    @staticmethod
    def has_module_access(user_id, module_name):
        """Check if user has any permission in module"""
```

### 4.3 Decorators (`tprm_decorators.py`)
```python
def rbac_required(permission_name, module_name=None):
    """Generic permission decorator"""
    
def rbac_rfp_required(permission_type):
    """RFP-specific permission decorator"""
    
def rbac_module_required(module_name):
    """Module access decorator"""
    
def rbac_admin_required():
    """Admin access decorator"""
    
def rbac_combined_permission(permissions):
    """Multiple permission decorator"""
```

### 4.4 Views (`tprm_views.py`)
```python
# Core RBAC API endpoints
def get_user_permissions(request):
    """Get user permissions summary"""
    
def check_rfp_permission(request):
    """Check specific RFP permission"""
    
def bulk_check_permissions(request):
    """Check multiple permissions at once"""
    
def get_user_role(request):
    """Get user role information"""
```

### 4.5 Example Views (`example_views.py`)
```python
# Demonstrates RBAC integration with DRF
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('ViewRFP')
def list_rfps(request):
    """Example RFP listing with RBAC protection"""
```

## 5. Permission System

### 5.1 Permission Categories

#### RFP Module (40+ permissions)
- **Basic Operations**: Create, Edit, View, Delete, Clone
- **Workflow**: Submit for Review, Approve, Reject
- **Management**: Assign Reviewers, View Status, Manage Versions
- **Documents**: Upload, Download, Preview, Validate
- **Evaluation**: Score Responses, Rank Vendors, Finalize
- **Analytics**: View Analytics, Generate Reports
- **Communication**: Send Notifications, Broadcast Messages

#### Contract Module (20+ permissions)
- **Basic Operations**: List, Create, Update, Delete
- **Workflow**: Approve, Reject, Manage Terms
- **Analysis**: OCR Processing, NLP Analysis
- **Documents**: Upload, Download, Preview
- **Renewals**: Manage Renewals, Track Expiry

#### Vendor Module (15+ permissions)
- **Basic Operations**: View, Create, Update, Delete
- **Workflow**: Submit for Approval, Approve, Reject
- **Integration**: RFP Integration, Risk Assessment
- **Screening**: Vendor Screening, Integration

#### Risk Module (10+ permissions)
- **Assessment**: Assess Vendor Risk, View Assessments
- **Planning**: Risk Mitigation Planning
- **Scoring**: Risk Scoring, Analytics

#### Compliance Module (10+ permissions)
- **Reports**: Generate Compliance Reports
- **Audit**: Regulatory Compliance Review, Document Auditing
- **Legal**: Legal Aspect Review

#### BCP/DRP Module (10+ permissions)
- **Strategy**: Create BCP Strategy, Evaluate DRP Plans
- **Management**: Manage Questionnaires, OCR Extraction
- **Review**: Plan Review, Approval

### 5.2 Permission Naming Strategy

#### Database Column Names (PascalCase)
```python
'CreateRFP', 'ViewRFP', 'ListContracts', 'CreateContract'
```

#### Model Field Names (snake_case)
```python
'create_rfp', 'view_rfp', 'list_contracts', 'create_contract'
```

#### Simplified Names (for coding)
```python
'create', 'view', 'list', 'update'
```

### 5.3 Permission Mapping
```python
# RFP Permission Mapping
rfp_permissions = {
    'create': 'create_rfp',
    'edit': 'edit_rfp', 
    'view': 'view_rfp',
    'delete': 'delete_rfp',
    'clone': 'clone_rfp',
    'submit': 'submit_rfp_for_review',
    'approve': 'approve_rfp',
    'reject': 'reject_rfp',
    # ... 32+ more mappings
}

# Contract Permission Mapping
contract_permissions = {
    'list': 'list_contracts',
    'create': 'create_contract',
    'update': 'update_contract',
    'delete': 'delete_contract',
    'approve': 'approve_contract',
    'reject': 'reject_contract',
    # ... 14+ more mappings
}
```

## 6. Implementation Patterns

### 6.1 Authentication Pattern
```python
# JWT Token Extraction
def get_user_id_from_request(request):
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        user = JWTService.get_user_from_token(token)
        return user.userid if user else None
    return None
```

### 6.2 Permission Checking Pattern
```python
# Single Permission Check
def check_permission(user_id, permission_name):
    rbac_record = RBACTPRM.objects.filter(
        user_id=user_id, 
        is_active='Y'
    ).first()
    
    if not rbac_record:
        return False
    
    # Convert permission name to model field
    field_name = get_model_field_name_from_db_column(permission_name)
    return getattr(rbac_record, field_name, False)
```

### 6.3 Decorator Pattern
```python
def rbac_required(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_id = get_user_id_from_request(request)
            if not user_id:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            has_permission = check_permission(user_id, permission_name)
            if not has_permission:
                return JsonResponse({'error': 'Permission denied'}, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 6.4 Module Access Pattern
```python
def has_module_access(user_id, module_name):
    rbac_record = get_user_rbac_record(user_id)
    if not rbac_record:
        return False
    
    # Get all permissions for the module
    module_permissions = get_module_permissions(module_name)
    
    # Check if user has any permission in the module
    return any(getattr(rbac_record, perm, False) for perm in module_permissions)
```

## 7. API Reference

### 7.1 Core RBAC Endpoints

#### GET `/rbac/permissions/`
Get user permissions summary
```json
{
    "success": true,
    "permissions": {
        "rfp": {
            "has_access": true,
            "permissions": {
                "create_rfp": true,
                "view_rfp": true,
                "edit_rfp": false
            }
        },
        "contract": {
            "has_access": true,
            "permissions": {
                "list_contracts": true,
                "create_contract": false
            }
        }
    }
}
```

#### GET `/rbac/role/`
Get user role information
```json
{
    "success": true,
    "role": "Admin",
    "username": "testuser3"
}
```

#### POST `/rbac/bulk-check/`
Check multiple permissions
```json
{
    "permissions": ["ViewRFP", "CreateContract", "ViewVendors"]
}
```

### 7.2 Module Permission Endpoints

#### GET `/rbac/rfp/?permission_type=create`
Check RFP permission
```json
{
    "success": true,
    "has_permission": true,
    "permission": "CreateRFP"
}
```

#### GET `/rbac/contract/?permission_type=list`
Check contract permission
```json
{
    "success": true,
    "has_permission": true,
    "permission": "ListContracts"
}
```

### 7.3 Example Protected Endpoints

#### GET `/rbac/example/rfp-dashboard/`
RFP Dashboard (requires ViewRFP permission)

#### POST `/rbac/example/create-rfp/`
Create RFP (requires CreateRFP permission)

#### GET `/rbac/example/admin-dashboard/`
Admin Dashboard (requires admin access)

## 8. Usage Examples

### 8.1 Basic Permission Protection
```python
from rbac.tprm_decorators import rbac_required

@rbac_required('ViewRFP')
def view_rfp_details(request, rfp_id):
    # Only users with ViewRFP permission can access
    rfp = get_rfp_by_id(rfp_id)
    return JsonResponse({'rfp': rfp})
```

### 8.2 Module-Specific Protection
```python
from rbac.tprm_decorators import rbac_rfp_required

@rbac_rfp_required('create')
def create_rfp(request):
    # Only users with CreateRFP permission can access
    rfp_data = request.POST
    rfp = create_new_rfp(rfp_data)
    return JsonResponse({'rfp_id': rfp.id})
```

### 8.3 Module Access Protection
```python
from rbac.tprm_decorators import rbac_module_required

@rbac_module_required('contract')
def contract_dashboard(request):
    # Only users with any contract permission can access
    contracts = get_user_contracts(request.user.id)
    return JsonResponse({'contracts': contracts})
```

### 8.4 Combined Permissions
```python
from rbac.tprm_decorators import rbac_combined_permission

@rbac_combined_permission(['CreateRFP', 'SelectVendorsForRFP'])
def create_rfp_with_vendors(request):
    # Requires both permissions
    rfp_data = request.POST
    vendor_ids = request.POST.getlist('vendor_ids')
    
    rfp = create_rfp(rfp_data)
    assign_vendors_to_rfp(rfp.id, vendor_ids)
    
    return JsonResponse({'rfp_id': rfp.id})
```

### 8.5 Admin Access Protection
```python
from rbac.tprm_decorators import rbac_admin_required

@rbac_admin_required
def admin_dashboard(request):
    # Only admin users can access
    system_stats = get_system_statistics()
    return JsonResponse({'stats': system_stats})
```

## 9. Security Model

### 9.1 Authentication Security
- **JWT Token Validation**: Every request validates JWT token
- **Token Expiry**: Automatic token expiration handling
- **Secure Extraction**: Safe user_id extraction from tokens
- **Fallback Support**: Session authentication as backup

### 9.2 Permission Security
- **Fail-Safe Default**: Default to deny access
- **Granular Control**: Individual permission checking
- **Module Isolation**: Permissions are module-specific
- **No Permission Inheritance**: Explicit permission assignment

### 9.3 Data Security
- **Database Validation**: All permissions validated against database
- **Active Status Check**: Only active users can access
- **Audit Logging**: All permission decisions logged
- **Error Handling**: Secure error responses

### 9.4 API Security
- **CSRF Protection**: CSRF exempt for API endpoints
- **Method Validation**: HTTP method validation
- **Input Validation**: Query parameter validation
- **Rate Limiting**: Built-in rate limiting support

## 10. Deployment Guide

### 10.1 Prerequisites
- Django 3.2+ with DRF
- MySQL database with rbac_tprm table
- JWT authentication system
- Python 3.8+

### 10.2 Installation Steps

#### Step 1: Add to Django Settings
```python
INSTALLED_APPS = [
    # ... other apps
    'rbac',
]

# JWT Settings
JWT_SECRET_KEY = 'your-secret-key'
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24
JWT_REFRESH_EXPIRY_DAYS = 7
```

#### Step 2: Database Setup
```sql
-- Ensure rbac_tprm table exists with correct schema
-- Populate with user permission data
-- Set appropriate indexes
```

#### Step 3: URL Configuration
```python
urlpatterns = [
    # ... other URLs
    path('rbac/', include('rbac.tprm_urls')),
    path('rbac/example/', include('rbac.example_urls')),
]
```

#### Step 4: Permission Data Setup
```python
# Create RBAC records for users
from rbac.models import RBACTPRM

RBACTPRM.objects.create(
    user_id=3,
    username='testuser3',
    role='Admin',
    view_rfp=True,
    create_rfp=True,
    # ... set other permissions
    is_active='Y'
)
```

### 10.3 Configuration Options

#### Environment Variables
```bash
# Database
DB_NAME=tprm
DB_USER=your_username
DB_PASSWORD=your_password

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_EXPIRY_HOURS=24
JWT_REFRESH_EXPIRY_DAYS=7

# Logging
RBAC_LOG_LEVEL=INFO
```

#### Django Settings
```python
# RBAC Configuration
RBAC_SETTINGS = {
    'DEFAULT_MODULE': 'rfp',
    'LOG_PERMISSION_CHECKS': True,
    'CACHE_PERMISSIONS': False,
    'PERMISSION_TIMEOUT': 300,  # 5 minutes
}
```

## 11. Testing Strategy

### 11.1 Unit Testing
```python
from django.test import TestCase
from rbac.tprm_utils import RBACTPRMUtils

class RBACUtilsTest(TestCase):
    def test_check_permission(self):
        # Test permission checking logic
        user_id = 3
        permission = 'ViewRFP'
        result = RBACTPRMUtils.check_permission(user_id, permission)
        self.assertTrue(result)
```

### 11.2 Integration Testing
```python
from django.test import TestCase, Client
from django.urls import reverse

class RBACViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.token = 'valid-jwt-token'
    
    def test_get_user_permissions(self):
        response = self.client.get(
            reverse('get_user_permissions'),
            HTTP_AUTHORIZATION=f'Bearer {self.token}'
        )
        self.assertEqual(response.status_code, 200)
```

### 11.3 Postman Testing
- Use `TPRM_RBAC_Postman_Collection.json`
- Test all endpoints with different user roles
- Verify permission enforcement
- Test error scenarios

### 11.4 Test Scenarios
1. **Valid Permissions**: User has required permission
2. **Invalid Permissions**: User lacks required permission
3. **No Authentication**: Missing JWT token
4. **Invalid Token**: Expired or malformed token
5. **Module Access**: User has module access
6. **Admin Access**: User has admin privileges
7. **Combined Permissions**: Multiple permission requirements

## 12. Troubleshooting

### 12.1 Common Issues

#### Permission Denied Errors
**Problem**: User getting 403 Permission Denied
**Solution**: 
1. Check user has permission in database
2. Verify JWT token is valid
3. Check user is active in RBAC system
4. Review permission mapping

#### Database Connection Issues
**Problem**: Cannot connect to rbac_tprm table
**Solution**:
1. Verify database credentials
2. Check table exists and is accessible
3. Ensure proper database permissions
4. Check Django database configuration

#### JWT Token Issues
**Problem**: Authentication failures
**Solution**:
1. Check token expiration
2. Verify token format
3. Check JWT secret key configuration
4. Validate token payload structure

### 12.2 Debug Mode
Enable debug logging for detailed troubleshooting:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'rbac': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### 12.3 Performance Optimization
1. **Database Indexing**: Index on user_id and is_active
2. **Permission Caching**: Cache frequently checked permissions
3. **Query Optimization**: Use select_related for related data
4. **Connection Pooling**: Configure database connection pooling

### 12.4 Monitoring
1. **Permission Check Logs**: Monitor permission decision logs
2. **Performance Metrics**: Track permission check response times
3. **Error Rates**: Monitor authentication and permission errors
4. **User Activity**: Track permission usage patterns

---

## Conclusion

This RBAC system provides a comprehensive, secure, and scalable solution for managing permissions in TPRM applications. The modular design, granular permissions, and flexible implementation patterns make it suitable for enterprise-level applications with complex access control requirements.

The system's strength lies in its:
- **Granularity**: 100+ individual permission flags
- **Flexibility**: Support for multiple permission naming conventions
- **Security**: Comprehensive authentication and authorization
- **Maintainability**: Clean separation of concerns and modular design
- **Scalability**: Efficient database design and caching support

For implementation support, refer to the example views and Postman collection for practical usage patterns.
