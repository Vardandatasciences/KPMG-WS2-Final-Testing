# Admin Access Control System

## Overview

The Admin Access Control System provides a comprehensive, functionality-based access control mechanism for the TPRM platform. This system allows administrators to manage user permissions at a granular level without relying on predefined roles.

## Key Features

✅ **No RBAC/MFA Dependency**: Accessible by default for admin configuration
✅ **Functionality-Based Permissions**: 170+ granular permission controls
✅ **Module-Organized**: Permissions grouped by RFP, Contract, Vendor, Risk, BCP/DRP, SLA, Compliance, and System modules
✅ **Real-time Updates**: Changes reflect immediately in user frontend experience
✅ **Bulk Operations**: Update permissions for multiple users simultaneously
✅ **Search & Filter**: Easy user discovery and management
✅ **Role Management**: Optional role labels for organizational purposes

## Architecture

### Backend Components

#### 1. Models (`backend/admin_access/models.py`)
- **User**: Maps to existing `users` table
- **RBACTPRM**: Maps to existing `rbac_tprm` table with 170+ permission fields

#### 2. Serializers (`backend/admin_access/serializers.py`)
- **UserSerializer**: User information with permission counts
- **RBACTPRMSerializer**: Permission data organized by module
- **PermissionUpdateSerializer**: Validation for permission updates
- **PermissionFieldSerializer**: Permission field metadata

#### 3. Views (`backend/admin_access/views.py`)
All endpoints use `@permission_classes([AllowAny])` for admin configuration access:

- `GET /api/admin-access/users/` - List all active users
- `GET /api/admin-access/users/<user_id>/permissions/` - Get user permissions
- `POST /api/admin-access/permissions/update/` - Update user permissions
- `POST /api/admin-access/permissions/bulk-update/` - Bulk permission updates
- `GET /api/admin-access/permissions/fields/` - Get permission field metadata

### Frontend Components

#### 1. Service Layer (`src/services/adminAccessService.js`)
Handles all API communication for permission management:
```javascript
- getAllUsers(params)
- getUserPermissions(userId)
- updateUserPermissions(data)
- bulkUpdatePermissions(data)
- getPermissionFields()
```

#### 2. UI Component (`src/pages/AdminAccess.vue`)
Full-featured admin interface with:
- User list with search and pagination
- Permission editor organized by module
- Quick actions (Select All, Deselect All)
- Module-level permission toggles
- Real-time save functionality

#### 3. Router Integration (`src/router/index.js`)
```javascript
{
  path: '/admin-access',
  name: 'AdminAccess',
  component: () => import('@/pages/AdminAccess.vue'),
  meta: { requiresAuth: true }
}
```

#### 4. Sidebar Menu (`src/components/layout/AppSidebar.vue`)
Added to Management section with Shield icon

## Database Schema

### Users Table
```sql
CREATE TABLE users (
  UserId INT PRIMARY KEY AUTO_INCREMENT,
  UserName VARCHAR(255),
  Password VARCHAR(255),
  Email VARCHAR(100),
  FirstName VARCHAR(45),
  LastName VARCHAR(45),
  IsActive VARCHAR(45),
  DepartmentId INT,
  session_token VARCHAR(1045),
  consent_accepted VARCHAR(1),
  license_key VARCHAR(255),
  CreatedAt TIMESTAMP,
  UpdatedAt TIMESTAMP
);
```

### RBAC_TPRM Table
```sql
CREATE TABLE rbac_tprm (
  RBACId INT PRIMARY KEY AUTO_INCREMENT,
  UserId INT,
  UserName VARCHAR(255),
  Role VARCHAR(100),
  
  -- 170+ Permission Columns (BooleanField)
  CreateRFP TINYINT(1) DEFAULT 0,
  ViewRFP TINYINT(1) DEFAULT 0,
  EditRFP TINYINT(1) DEFAULT 0,
  -- ... more permissions ...
  
  CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  IsActive VARCHAR(1) DEFAULT 'Y'
);
```

## Permission Modules

### 1. RFP Management (17+ permissions)
- Create, Edit, View, Delete RFP
- Approval workflows
- Vendor selection and invitation
- Response evaluation and scoring
- Analytics and reporting

### 2. Contract Management (14+ permissions)
- Create, Update, Delete contracts
- Contract terms and renewals
- Approval workflows
- OCR and NLP analysis
- Dashboard and search

### 3. Vendor Management (10+ permissions)
- View, Create, Update, Delete vendors
- Approval workflows
- Risk assessment
- Lifecycle tracking
- Contact and document management

### 4. Risk Management (7+ permissions)
- View and create risk assessments
- Recalculate risk scores
- Risk identification and mitigation
- Risk profile management

### 5. BCP/DRP Management (6+ permissions)
- Create strategies and plans
- Plan evaluation and approval
- OCR extraction
- Status monitoring

### 6. Questionnaire Management (6+ permissions)
- Create and view questionnaires
- Assignment and response handling
- Review and approval

### 7. SLA Management (6+ permissions)
- View, Create, Update, Delete SLAs
- Activate/Deactivate
- Performance monitoring

### 8. Compliance & Audit (5+ permissions)
- Generate compliance reports
- Regulatory compliance review
- Audit management
- Compliance status monitoring

### 9. System Administration (6+ permissions)
- System configuration
- User role management
- Access control management
- Health checks and bulk operations

## Usage Examples

### Fetch All Users
```javascript
import adminAccessService from '@/services/adminAccessService';

const users = await adminAccessService.getAllUsers({
  search: 'john',
  page: 1,
  page_size: 20
});
```

### Get User Permissions
```javascript
const permissions = await adminAccessService.getUserPermissions(userId);
// Returns:
// {
//   userId: 1,
//   userName: "testuser1",
//   role: "Manager",
//   permissions: {
//     rfp: { create_rfp: true, view_rfp: true, ... },
//     contracts: { ... },
//     ...
//   }
// }
```

### Update Permissions
```javascript
await adminAccessService.updateUserPermissions({
  user_id: 1,
  role: "Admin",
  permissions: {
    create_rfp: true,
    edit_rfp: true,
    view_rfp: true,
    approve_rfp: true,
    create_contract: true,
    view_vendors: true
  }
});
```

### Bulk Update
```javascript
await adminAccessService.bulkUpdatePermissions({
  user_ids: [1, 2, 3],
  role: "Manager",
  permissions: {
    view_rfp: true,
    view_contracts: true,
    view_vendors: true
  }
});
```

## Security Considerations

### Backend Security
- Models use `managed = False` to prevent accidental schema changes
- All endpoints use `AllowAny` permission for admin configuration access
- Input validation through serializers
- Transaction-wrapped updates for data integrity
- Comprehensive error logging

### Frontend Security
- Authentication required via router meta
- User session validation
- Secure API communication
- No client-side permission enforcement (server validates all actions)

## API Response Formats

### User List Response
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/admin-access/users/?page=2",
  "previous": null,
  "results": [
    {
      "userid": 1,
      "username": "testuser1",
      "email": "test@example.com",
      "firstname": "John",
      "lastname": "Doe",
      "full_name": "John Doe",
      "isactive": "Y",
      "departmentid": 1,
      "total_permissions": 45
    }
  ]
}
```

### Permission Response
```json
{
  "userId": 1,
  "userName": "testuser1",
  "fullName": "John Doe",
  "email": "test@example.com",
  "departmentId": 1,
  "role": "Manager",
  "permissions": {
    "rfp": {
      "create_rfp": true,
      "edit_rfp": true,
      "view_rfp": true,
      "delete_rfp": false
    },
    "contracts": {
      "list_contracts": true,
      "create_contract": true
    }
  }
}
```

### Permission Fields Response
```json
{
  "rfp": {
    "name": "RFP Management",
    "permissions": [
      {
        "field": "create_rfp",
        "display": "Create RFP",
        "description": "Create new RFPs"
      }
    ]
  }
}
```

## Deployment Instructions

### 1. Backend Setup
```bash
# Add to INSTALLED_APPS (already done)
# backend/vendor_guard_hub/settings.py
LOCAL_APPS = [
    ...
    'admin_access',
]

# Verify URL routing (already done)
# backend/vendor_guard_hub/urls.py
path('api/admin-access/', include('admin_access.urls')),

# No migrations needed (uses existing tables)
```

### 2. Frontend Setup
```bash
# Already configured:
# - Service: src/services/adminAccessService.js
# - Component: src/pages/AdminAccess.vue
# - Route: src/router/index.js
# - Menu: src/components/layout/AppSidebar.vue
```

### 3. Testing
```bash
# Start backend
cd backend
python manage.py runserver

# Start frontend
cd ../
npm run dev

# Access at: http://localhost:5173/admin-access
```

## Troubleshooting

### Issue: Users not loading
- Verify database connection
- Check that `users` table exists and has `IsActive = 'Y'` records
- Check browser console for API errors

### Issue: Permissions not saving
- Verify `rbac_tprm` table exists
- Check that user has an active RBAC record
- Review backend logs for save errors

### Issue: 404 on API calls
- Verify backend URL in `adminAccessService.js`
- Check that admin_access is in INSTALLED_APPS
- Verify URL routing in `urls.py`

## Future Enhancements

- [ ] Permission templates (save/load common permission sets)
- [ ] Permission history tracking
- [ ] Export/Import user permissions
- [ ] Role-based permission presets
- [ ] Audit logging for permission changes
- [ ] Department-based permission filters
- [ ] Permission comparison between users
- [ ] Scheduled permission reviews

## Support

For issues or questions, please contact the TPRM development team.

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Author**: TPRM Development Team

