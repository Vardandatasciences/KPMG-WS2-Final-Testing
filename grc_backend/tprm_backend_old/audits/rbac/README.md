# TPRM RBAC System

## Overview

The TPRM (Third Party Risk Management) RBAC system provides comprehensive role-based access control for managing permissions across all TPRM modules. This system is built to work with the `rbac_tprm` database table and provides granular permission control for enterprise TPRM applications.

## Table Structure

The system works with the `rbac_tprm` table which contains:

- **Primary Key**: `RBACId` (Auto-increment)
- **User Information**: `UserId`, `UserName`, `Role`
- **Module Permissions**: 100+ boolean permission fields
- **Timestamps**: `CreatedAt`, `UpdatedAt`
- **Status**: `IsActive`

## Modules Supported

### 1. **RFP (Request for Proposal)**
- Create, Edit, View, Delete RFP
- Clone, Submit for Review, Approve/Reject
- Assign Reviewers, View Approval Status
- Manage Versions, Documents, Responses
- Evaluation, Scoring, Vendor Ranking

### 2. **Contract Management**
- List, Create, Update, Delete Contracts
- Approve/Reject Contracts
- Manage Contract Terms and Renewals
- OCR, NLP Analysis, Document Management

### 3. **Vendor Management**
- View, Create, Update, Delete Vendors
- Submit for Approval, Approve/Reject
- RFP Integration, Risk Assessment
- Screening and Integration

### 4. **Risk Management**
- Vendor Risk Assessment
- Risk Identification in Plans
- Risk Mitigation Planning
- Risk Scoring and Analytics

### 5. **Compliance & Audit**
- Generate Compliance Reports
- Regulatory Compliance Review
- Document Auditing
- Legal Aspect Review

### 6. **BCP/DRP (Business Continuity/Disaster Recovery)**
- Strategy and Plan Creation
- Plan Evaluation and Approval
- Questionnaire Management
- OCR Extraction and Review

## Core Components

### 1. **Models** (`models.py`)
```python
class RBACTPRM(models.Model):
    # Maps to rbac_tprm table
    # Contains all permission fields as BooleanField
    # Provides helper properties for module access
```

### 2. **Utilities** (`tprm_utils.py`)
```python
class RBACTPRMUtils:
    # Core permission checking methods
    # Module-specific permission validation
    # User permission summaries
    # Debug and logging utilities
```

### 3. **Views** (`tprm_views.py`)
```python
# REST API endpoints for:
# - Getting user permissions
# - Checking specific permissions
# - Module access validation
# - Bulk permission checking
```

### 4. **Decorators** (`tprm_decorators.py`)
```python
# View decorators for:
# - Module-level access control
# - Specific permission requirements
# - Admin access control
# - Combined permission checks
```

## Usage Examples

### Basic Permission Check
```python
from rbac.tprm_decorators import rbac_rfp_required

@rbac_rfp_required('create')
def create_rfp_view(request):
    # Only users with create_rfp permission can access
    pass
```

### Module Access Check
```python
from rbac.tprm_decorators import rbac_module_required

@rbac_module_required('rfp')
def rfp_dashboard(request):
    # Only users with any RFP permission can access
    pass
```

### Admin Access Check
```python
from rbac.tprm_decorators import rbac_admin_required

@rbac_admin_required
def admin_dashboard(request):
    # Only admin users can access
    pass
```

### Combined Permissions
```python
@rbac_rfp_required('create')
@rbac_vendor_required('select_for_rfp')
def create_rfp_with_vendors(request):
    # Requires both permissions
    pass
```

## API Endpoints

### Core RBAC
- `GET /rbac/permissions/` - Get user permissions summary
- `GET /rbac/role/` - Get user role information
- `POST /rbac/bulk-check/` - Check multiple permissions

### Module Permission Checks
- `GET /rbac/rfp/?permission_type=create` - Check RFP permission
- `GET /rbac/contract/?permission_type=create` - Check contract permission
- `GET /rbac/vendor/?permission_type=create` - Check vendor permission
- `GET /rbac/risk/?permission_type=assess_vendor` - Check risk permission
- `GET /rbac/compliance/?permission_type=generate_reports` - Check compliance permission
- `GET /rbac/bcp-drp/?permission_type=create_strategy` - Check BCP/DRP permission

### Module Access Checks
- `GET /rbac/module-access/?module_name=rfp` - Check module access

### Example Views (Protected by RBAC)
- `GET /rbac/example/rfp-dashboard/` - RFP Dashboard
- `POST /rbac/example/create-rfp/` - Create RFP
- `GET /rbac/example/admin-dashboard/` - Admin Dashboard

## Permission Mapping

### RFP Permissions
```python
rfp_permissions = {
    'create': 'create_rfp',
    'edit': 'edit_rfp',
    'view': 'view_rfp',
    'delete': 'delete_rfp',
    'clone': 'clone_rfp',
    'submit': 'submit_rfp_for_review',
    'approve': 'approve_rfp',
    'reject': 'reject_rfp',
    'assign_reviewers': 'assign_rfp_reviewers',
    # ... more permissions
}
```

### Contract Permissions
```python
contract_permissions = {
    'list': 'list_contracts',
    'create': 'create_contract',
    'update': 'update_contract',
    'delete': 'delete_contract',
    'approve': 'approve_contract',
    'reject': 'reject_contract',
    # ... more permissions
}
```

## Database Integration

### Table Name
```sql
rbac_tprm
```

### Key Fields
```sql
RBACId int AI PK
UserId int
UserName varchar(255)
Role varchar(100)
-- 100+ boolean permission fields
IsActive varchar(1)
```

### Sample Query
```sql
SELECT * FROM rbac_tprm 
WHERE UserId = ? AND IsActive = 'Y'
```

## Security Features

### 1. **JWT Integration**
- Extracts user_id from JWT tokens
- Supports both JWT and session authentication
- Secure token validation

### 2. **Permission Granularity**
- 100+ individual permission fields
- Module-level access control
- Role-based permission inheritance

### 3. **Audit Logging**
- Comprehensive logging of permission checks
- Debug information for troubleshooting
- Security event tracking

### 4. **Error Handling**
- Graceful permission denial
- Detailed error messages
- Security-conscious error responses

## Testing

### Postman Collection
Use the `TPRM_RBAC_Postman_Collection.json` file to test all RBAC endpoints.

### Test Flow
1. **Authenticate** with MFA system to get JWT token
2. **Set token** in Postman collection variables
3. **Test permissions** using various endpoints
4. **Verify access control** with different user roles

### Test Scenarios
- User with no permissions
- User with specific module permissions
- User with admin access
- Invalid/expired tokens
- Permission combinations

## Configuration

### Django Settings
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'rbac',
]

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'tprm',
        # ... other settings
    }
}
```

### Environment Variables
```bash
# Database
DB_NAME=tprm
DB_USER=your_username
DB_PASSWORD=your_password

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_EXPIRY_HOURS=24
JWT_REFRESH_EXPIRY_DAYS=7
```

## Deployment

### 1. **Database Setup**
- Ensure `rbac_tprm` table exists
- Populate with user permission data
- Set appropriate indexes for performance

### 2. **Django Migration**
```bash
python manage.py makemigrations rbac
python manage.py migrate
```

### 3. **Permission Data**
- Import existing RBAC data
- Set up default roles and permissions
- Configure admin users

### 4. **Testing**
- Test all endpoints with Postman
- Verify permission enforcement
- Check error handling

## Best Practices

### 1. **Permission Design**
- Use descriptive permission names
- Group related permissions logically
- Avoid overly granular permissions

### 2. **Security**
- Always validate permissions server-side
- Use HTTPS in production
- Implement rate limiting

### 3. **Performance**
- Cache permission results when appropriate
- Use database indexes for user lookups
- Minimize database queries

### 4. **Maintenance**
- Regular permission audits
- Update permissions for new features
- Monitor access patterns

## Troubleshooting

### Common Issues

#### 1. **Permission Denied Errors**
- Check user has required permissions in database
- Verify JWT token is valid
- Check user is active in RBAC system

#### 2. **Database Connection Issues**
- Verify database credentials
- Check table exists and is accessible
- Ensure proper database permissions

#### 3. **JWT Token Issues**
- Check token expiration
- Verify token format
- Check JWT secret key configuration

### Debug Mode
Enable debug logging to see detailed permission check information:
```python
LOGGING = {
    'level': 'DEBUG',
    'handlers': ['console'],
}
```

## Support

For issues or questions:
1. Check the logs for detailed error information
2. Verify database permissions and data
3. Test with Postman collection
4. Review permission mappings

## Version History

- **v1.0.0** - Initial TPRM RBAC implementation
- **v1.1.0** - Added comprehensive permission checking
- **v1.2.0** - Enhanced decorators and utilities
- **v1.3.0** - Added example views and testing tools
