# Vendor Management - All Vendors Listing

This module provides comprehensive vendor listing functionality with 4 distinct vendor types based on their onboarding status and RFP participation.

## Overview

The All Vendors feature categorizes vendors into 4 types:

1. **Vendor Onboarded with RFP** - Exists in both `vendors` and `temp_vendor` tables with a `response_id`
2. **Vendor Onboarded without RFP** - Exists in both `vendors` and `temp_vendor` tables without a `response_id`
3. **Temporary Vendor with RFP** - Only in `temp_vendor` table with a `response_id`
4. **Temporary Vendor without RFP** - Only in `temp_vendor` table without a `response_id`

## Database Tables

### vendors Table
Contains fully onboarded vendors with complete information including:
- Company details (name, legal name, business type)
- Financial information (annual revenue, employee count)
- Risk assessment (risk level, critical vendor flags)
- Lifecycle management (onboarding date, assessment dates)
- Access permissions (data access, system access)

### temp_vendor Table
Contains temporary vendor records during registration/onboarding:
- Basic company information
- Contact information (JSON field)
- Documents (JSON field)
- Response ID (links to RFP responses)

## API Endpoints

### GET `/api/v1/management/vendors/all/`
Lists all vendors with their categorization.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "vendor_id": 1,
      "vendor_code": "VEN001",
      "company_name": "Example Corp",
      "vendor_type": "ONBOARDED_WITH_RFP",
      "vendor_type_label": "Vendor Onboarded with RFP",
      "is_temporary": false,
      "risk_level": "MEDIUM",
      "status": "APPROVED",
      ...
    }
  ],
  "total": 10,
  "counts": {
    "onboarded_with_rfp": 3,
    "onboarded_without_rfp": 2,
    "temporary_with_rfp": 3,
    "temporary_without_rfp": 2
  }
}
```

### GET `/api/v1/management/vendors/<vendor_code>/`
Retrieves detailed information for a specific vendor.

**Response:**
```json
{
  "success": true,
  "data": {
    "vendor_code": "VEN001",
    "company_name": "Example Corp",
    "vendor_type": "ONBOARDED_WITH_RFP",
    "vendor_type_label": "Vendor Onboarded with RFP",
    "is_temporary": false,
    // ... all vendor fields
  }
}
```

## Frontend Components

### AllVendors.vue
Main listing page with:
- **View Modes**: Card view and Table view
- **Filters**: 
  - Vendor Type
  - Risk Level
  - Status
  - Search (by name, code)
- **Statistics**: Count cards for each vendor type
- **Actions**: View vendor details

### VendorDetailModal.vue
Modal component displaying comprehensive vendor information with tabs:
- **Company Info**: All company and business details
- **Risk & Status**: Risk level, status, lifecycle, access flags
- **Contacts**: Contact information (for temporary vendors)
- **Documents**: Document list (for temporary vendors)
- **Audit Trail**: Created/updated information

## Implementation Details

### Vendor Type Logic

The vendor type is determined by:

```python
# Check if vendor exists in vendors table
vendor_in_vendors = Vendors.objects.filter(vendor_code=code).exists()

# Check if vendor exists in temp_vendor table
temp_vendor = TempVendor.objects.filter(vendor_code=code).first()

if vendor_in_vendors and temp_vendor:
    if temp_vendor.response_id:
        type = "ONBOARDED_WITH_RFP"
    else:
        type = "ONBOARDED_WITHOUT_RFP"
elif temp_vendor:
    if temp_vendor.response_id:
        type = "TEMPORARY_WITH_RFP"
    else:
        type = "TEMPORARY_WITHOUT_RFP"
```

### Multi-tenancy

All queries are filtered by `tenant_id` to ensure data isolation between tenants.

### Data Source Priority

- For onboarded vendors (types 1 & 2): Data comes from `vendors` table
- For temporary vendors (types 3 & 4): Data comes from `temp_vendor` table

## Styling

The frontend uses color-coding for different vendor types:

- **Onboarded with RFP**: Green (#10b981)
- **Onboarded without RFP**: Blue (#3b82f6)
- **Temporary with RFP**: Amber (#f59e0b)
- **Temporary without RFP**: Purple (#8b5cf6)

## Routes

### TPRM Frontend
```javascript
{
  path: '/all-vendors',
  name: 'AllVendors',
  component: () => import('@/pages/management/AllVendors.vue'),
  meta: { requiresPermission: 'view' }
}
```

### Main GRC Frontend
```javascript
{
  path: '/management/all-vendors',
  name: 'AllVendors',
  component: () => import('../views/TprmWrapper.vue'),
  meta: { requiresAuth: true }
}
```

## Usage

### Backend
```python
# In your Django app
from tprm_backend.apps.management.views import AllVendorsListView

# The view handles all the vendor categorization logic
```

### Frontend
```javascript
// Navigate to All Vendors page
router.push('/all-vendors')

// Or from main GRC app
router.push('/management/all-vendors')
```

## Permissions

Requires `view` permission in the vendor module for RBAC-enabled routes.

## Future Enhancements

1. Export functionality (CSV, Excel)
2. Bulk operations
3. Advanced filtering (date ranges, custom fields)
4. Vendor comparison
5. Quick onboarding from temporary to full vendor
