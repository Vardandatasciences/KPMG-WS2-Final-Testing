# TPRM RBAC System - Complete Approach Documentation

## 1. System Architecture

### 1.1 Core Philosophy
**Permission-Based Access Control** with granular boolean flags stored in a wide database table (`rbac_tprm`).

### 1.2 Architecture Layers
```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (Views)                        │
│  • tprm_views.py - Core RBAC API endpoints                 │
│  • example_views.py - Protected business logic examples    │
├─────────────────────────────────────────────────────────────┤
│                Decorator Layer                              │
│  • tprm_decorators.py - Permission checking decorators     │
│  • Supports module-specific and generic permission checks  │
├─────────────────────────────────────────────────────────────┤
│                Business Logic Layer                         │
│  • tprm_utils.py - Core permission checking logic          │
│  • Permission mapping and module access validation         │
├─────────────────────────────────────────────────────────────┤
│                Data Access Layer                            │
│  • models.py - RBACTPRM model mapping to rbac_tprm table   │
│  • 100+ boolean permission fields with db_column mapping   │
├─────────────────────────────────────────────────────────────┤
│                Authentication Layer                         │
│  • JWT token validation and user extraction                │
│  • Integration with MFA authentication system              │
└─────────────────────────────────────────────────────────────┘
```

## 2. Database Design

### 2.1 Table Structure
```sql
CREATE TABLE rbac_tprm (
    RBACId INT AUTO_INCREMENT PRIMARY KEY,
    UserId INT NOT NULL,
    UserName VARCHAR(255),
    Role VARCHAR(100),
    
    -- RFP Module (40+ permissions)
    CreateRFP BOOLEAN DEFAULT FALSE,
    EditRFP BOOLEAN DEFAULT FALSE,
    ViewRFP BOOLEAN DEFAULT FALSE,
    DeleteRFP BOOLEAN DEFAULT FALSE,
    -- ... 36+ more RFP permissions
    
    -- Contract Module (20+ permissions)
    ListContracts BOOLEAN DEFAULT FALSE,
    CreateContract BOOLEAN DEFAULT FALSE,
    UpdateContract BOOLEAN DEFAULT FALSE,
    -- ... 17+ more contract permissions
    
    -- Vendor Module (15+ permissions)
    ViewVendors BOOLEAN DEFAULT FALSE,
    CreateVendor BOOLEAN DEFAULT FALSE,
    -- ... 13+ more vendor permissions
    
    -- Risk Module (10+ permissions)
    AssessVendorRisk BOOLEAN DEFAULT FALSE,
    ViewRiskAssessments BOOLEAN DEFAULT FALSE,
    -- ... 8+ more risk permissions
    
    -- Compliance Module (10+ permissions)
    GenerateComplianceReports BOOLEAN DEFAULT FALSE,
    AuditDocuments BOOLEAN DEFAULT FALSE,
    -- ... 8+ more compliance permissions
    
    -- BCP/DRP Module (10+ permissions)
    CreateBCPStrategy BOOLEAN DEFAULT FALSE,
    EvaluateDRPPlans BOOLEAN DEFAULT FALSE,
    -- ... 8+ more BCP/DRP permissions
    
    IsActive CHAR(1) DEFAULT 'Y',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 2.2 Design Principles
- **Wide Table**: One row per user, one column per permission
- **Boolean Values**: Simple 0/1 for permission existence
- **User-Centric**: Each user has complete permission profile
- **Role Reference**: Role stored for administrative purposes
- **Active Status**: Soft delete capability with IsActive flag

## 3. Core Components

### 3.1 Models (`models.py`)
```python
class RBACTPRM(models.Model):
    """Maps to rbac_tprm table with 100+ permission fields"""
    
    rbac_id = models.AutoField(db_column='RBACId', primary_key=True)
    user_id = models.IntegerField(db_column='UserId')
    username = models.CharField(db_column='UserName', max_length=255)
    role = models.CharField(db_column='Role', max_length=100)
    
    # Permission Fields (100+ BooleanField with db_column mapping)
    create_rfp = models.BooleanField(db_column='CreateRFP', default=False)
    view_rfp = models.BooleanField(db_column='ViewRFP', default=False)
    list_contracts = models.BooleanField(db_column='ListContracts', default=False)
    # ... 97+ more permission fields
    
    class Meta:
        db_table = 'rbac_tprm'
        managed = False  # Table exists in database
```

### 3.2 Utilities (`tprm_utils.py`)
```python
class RBACTPRMUtils:
    """Core permission checking and utility methods"""
    
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

### 3.3 Decorators (`tprm_decorators.py`)
```python
def rbac_required(permission_name, module_name=None):
    """Generic permission decorator"""
    
def rbac_rfp_required(permission_type):
    """RFP-specific permission decorator"""
    
def rbac_contract_required(permission_type):
    """Contract-specific permission decorator"""
    
def rbac_vendor_required(permission_type):
    """Vendor-specific permission decorator"""
    
def rbac_risk_required(permission_type):
    """Risk-specific permission decorator"""
    
def rbac_compliance_required(permission_type):
    """Compliance-specific permission decorator"""
    
def rbac_bcp_drp_required(permission_type):
    """BCP/DRP-specific permission decorator"""
    
def rbac_module_required(module_name):
    """Module access decorator"""
    
def rbac_admin_required():
    """Admin access decorator"""
    
def rbac_combined_permission(permissions):
    """Multiple permission decorator"""
```

### 3.4 Views (`tprm_views.py`)
```python
# Core RBAC API endpoints
def get_user_permissions(request):
    """Get user permissions summary"""
    
def check_rfp_permission(request):
    """Check specific RFP permission"""
    
def check_contract_permission(request):
    """Check specific contract permission"""
    
def check_vendor_permission(request):
    """Check specific vendor permission"""
    
def check_risk_permission(request):
    """Check specific risk permission"""
    
def check_compliance_permission(request):
    """Check specific compliance permission"""
    
def check_bcp_drp_permission(request):
    """Check specific BCP/DRP permission"""
    
def bulk_check_permissions(request):
    """Check multiple permissions at once"""
    
def get_user_role(request):
    """Get user role information"""
```

### 3.5 Example Views (`example_views.py`)
```python
# Demonstrates RBAC integration with DRF
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('ViewRFP')
def list_rfps(request):
    """Example RFP listing with RBAC protection"""
    
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('CreateRFP')
def create_rfp(request):
    """Example RFP creation with RBAC protection"""
    
# ... 20+ more example views for all modules
```

## 4. Permission System

### 4.1 Permission Categories

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

### 4.2 Permission Naming Strategy

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

### 4.3 Permission Mapping
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

## 5. Implementation Patterns

### 5.1 Authentication Pattern
```python
def get_user_id_from_request(request):
    """Extract user_id from JWT token or session"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        user = JWTService.get_user_from_token(token)
        return user.userid if user else None
    return None
```

### 5.2 Permission Checking Pattern
```python
def check_permission(user_id, permission_name):
    """Check if user has specific permission"""
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

### 5.3 Decorator Pattern
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

### 5.4 Module Access Pattern
```python
def has_module_access(user_id, module_name):
    """Check if user has any permission in module"""
    rbac_record = get_user_rbac_record(user_id)
    if not rbac_record:
        return False
    
    # Get all permissions for the module
    module_permissions = get_module_permissions(module_name)
    
    # Check if user has any permission in the module
    return any(getattr(rbac_record, perm, False) for perm in module_permissions)
```

## 6. API Reference

### 6.1 Core RBAC Endpoints

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

### 6.2 Module Permission Endpoints

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

### 6.3 Example Protected Endpoints

#### GET `/rbac/example/rfp-dashboard/`
RFP Dashboard (requires ViewRFP permission)

#### POST `/rbac/example/create-rfp/`
Create RFP (requires CreateRFP permission)

#### GET `/rbac/example/admin-dashboard/`
Admin Dashboard (requires admin access)

## 7. Usage Examples

### 7.1 Basic Permission Protection
```python
from rbac.tprm_decorators import rbac_required

@rbac_required('ViewRFP')
def view_rfp_details(request, rfp_id):
    # Only users with ViewRFP permission can access
    rfp = get_rfp_by_id(rfp_id)
    return JsonResponse({'rfp': rfp})
```

### 7.2 Module-Specific Protection
```python
from rbac.tprm_decorators import rbac_rfp_required

@rbac_rfp_required('create')
def create_rfp(request):
    # Only users with CreateRFP permission can access
    rfp_data = request.POST
    rfp = create_new_rfp(rfp_data)
    return JsonResponse({'rfp_id': rfp.id})
```

### 7.3 Module Access Protection
```python
from rbac.tprm_decorators import rbac_module_required

@rbac_module_required('contract')
def contract_dashboard(request):
    # Only users with any contract permission can access
    contracts = get_user_contracts(request.user.id)
    return JsonResponse({'contracts': contracts})
```

### 7.4 Combined Permissions
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

### 7.5 Admin Access Protection
```python
from rbac.tprm_decorators import rbac_admin_required

@rbac_admin_required
def admin_dashboard(request):
    # Only admin users can access
    system_stats = get_system_statistics()
    return JsonResponse({'stats': system_stats})
```

## 8. Security Model

### 8.1 Authentication Security
- **JWT Token Validation**: Every request validates JWT token
- **Token Expiry**: Automatic token expiration handling
- **Secure Extraction**: Safe user_id extraction from tokens
- **Fallback Support**: Session authentication as backup

### 8.2 Permission Security
- **Fail-Safe Default**: Default to deny access
- **Granular Control**: Individual permission checking
- **Module Isolation**: Permissions are module-specific
- **No Permission Inheritance**: Explicit permission assignment

### 8.3 Data Security
- **Database Validation**: All permissions validated against database
- **Active Status Check**: Only active users can access
- **Audit Logging**: All permission decisions logged
- **Error Handling**: Secure error responses

## 9. Deployment Guide

### 9.1 Prerequisites
- Django 3.2+ with DRF
- MySQL database with rbac_tprm table
- JWT authentication system
- Python 3.8+

### 9.2 Installation Steps

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

#### Step 2: URL Configuration
```python
urlpatterns = [
    # ... other URLs
    path('rbac/', include('rbac.tprm_urls')),
    path('rbac/example/', include('rbac.example_urls')),
]
```

#### Step 3: Permission Data Setup
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

## 10. Testing Strategy

### 10.1 Postman Testing
- Use `TPRM_RBAC_Postman_Collection.json`
- Test all endpoints with different user roles
- Verify permission enforcement
- Test error scenarios

### 10.2 Test Scenarios
1. **Valid Permissions**: User has required permission
2. **Invalid Permissions**: User lacks required permission
3. **No Authentication**: Missing JWT token
4. **Invalid Token**: Expired or malformed token
5. **Module Access**: User has module access
6. **Admin Access**: User has admin privileges
7. **Combined Permissions**: Multiple permission requirements

## 11. Troubleshooting

### 11.1 Common Issues

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

### 11.2 Debug Mode
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

## 12. Key Advantages

### 12.1 Flexibility
- **Fine-grained Control**: 100+ individual permission flags
- **Easy Modification**: Add/remove permissions by changing database values
- **Role Flexibility**: Users can have custom permission combinations

### 12.2 Performance
- **Single Query**: One database lookup per permission check
- **Boolean Operations**: Fast boolean field checking
- **Caching Ready**: Easy to implement permission caching

### 12.3 Maintainability
- **Centralized Logic**: All permission logic in utility classes
- **Decorator Pattern**: Clean, reusable permission checking
- **Clear Separation**: Models, utilities, decorators, and views are separate

### 12.4 Scalability
- **Horizontal Scaling**: Add new permissions as new columns
- **Module Expansion**: Easy to add new modules
- **User Growth**: Efficient for large numbers of users

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
