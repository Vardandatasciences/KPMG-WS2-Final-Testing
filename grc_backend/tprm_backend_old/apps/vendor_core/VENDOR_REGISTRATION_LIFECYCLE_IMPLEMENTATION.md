# Vendor Registration Lifecycle Implementation

## Overview
This document describes the implementation of vendor registration lifecycle management with RBAC role checking to show the "Already Registered" screen appropriately.

## Requirements Implemented

### 1. Show "Already Registered" Screen Based on Role and Lifecycle Stage
- **Condition**: If the logged-in user has role "vendor" in `rbac_tprm` table AND `lifecycle_stage != 1` in `temp_vendor` table
- **Result**: Display the "You Have Already Registered" message as shown in the uploaded image

### 2. Lifecycle Stage Management
- **Initial Registration**: `lifecycle_stage = 1` (Registration stage)
- **After Successful Submission**: `lifecycle_stage = 2` (External Screening stage)

## Implementation Details

### Backend Changes

#### 1. Updated `get_user_data` Endpoint (`views.py`)
**File**: `backend/apps/vendor_core/views.py`

**Changes**:
- Added RBAC role checking by querying `rbac_tprm` table
- Returns user role and RBAC permissions in the response
- Ensures lifecycle data is returned in all response scenarios

**Key Code**:
```python
# Get user role from rbac_tprm table
from rbac.models import RBACTPRM

rbac_entry = RBACTPRM.objects.filter(user_id=user_id).first()
if rbac_entry:
    user_role = rbac_entry.role
    user_rbac_permissions = {
        'role': rbac_entry.role,
        'can_register_vendor': rbac_entry.register_vendor if hasattr(rbac_entry, 'register_vendor') else False,
        'can_view_vendor': rbac_entry.view_vendor if hasattr(rbac_entry, 'view_vendor') else False,
        'can_edit_vendor': rbac_entry.edit_vendor if hasattr(rbac_entry, 'edit_vendor') else False,
    }
```

**Response Structure**:
```json
{
  "status": "success",
  "data": {
    "temp_vendor": {...},
    "rfp_response": {...},
    "lifecycle": {
      "current_stage": {
        "stage_id": 2,
        "stage_name": "External Screening",
        "stage_code": "EXT_SCR",
        "description": "..."
      },
      "tracker_entries": [...]
    },
    "user_role": "vendor",
    "user_rbac_permissions": {...}
  }
}
```

#### 2. Updated `vendor_submit_registration` Method (`views.py`)
**File**: `backend/apps/vendor_core/views.py`

**Changes**:
- Initialize `lifecycle_stage` to 1 if not set during registration
- Automatically update `lifecycle_stage` from 1 to 2 after successful submission
- Uses `update_temp_vendor_lifecycle_stage` helper function

**Key Code**:
```python
# Initialize lifecycle_stage to 1 if it's not set
if not vendor_temp_record.lifecycle_stage:
    vendor_temp_record.lifecycle_stage = 1
    vendor_temp_record.save()
    vendor_logger.info(f"Initialized lifecycle_stage to 1 for vendor {vendor_temp_record.id}")

# Update to stage 2 after successful registration
if vendor_temp_record.lifecycle_stage == 1:
    lifecycle_result = update_temp_vendor_lifecycle_stage(vendor_temp_record.id, 2)
    if lifecycle_result['success']:
        vendor_logger.info(f"Updated vendor {vendor_temp_record.id} from stage 1 to stage 2")
```

#### 3. Updated `TempVendorSerializer` (`serializers.py`)
**File**: `backend/apps/vendor_core/serializers.py`

**Changes**:
- Modified `create` method to set initial `lifecycle_stage` to 1 (Registration)
- Creates initial `LifecycleTracker` entry with `ended_at=None` (still in progress)
- Removed automatic completion of registration and screening stages

**Key Code**:
```python
def create(self, validated_data):
    # Set initial lifecycle stage to 1 (Registration) if not provided
    if not validated_data.get('lifecycle_stage'):
        reg_stage = get_lifecycle_stage_id_by_code('REG')
        validated_data['lifecycle_stage'] = reg_stage or 1
    
    # Create the temp vendor record
    temp_vendor = TempVendor.objects.create(**validated_data)
    
    # Create initial lifecycle tracker entry for Registration stage
    LifecycleTracker.objects.create(
        vendor_id=temp_vendor.id,
        lifecycle_stage=validated_data['lifecycle_stage'],
        started_at=timezone.now(),
        ended_at=None  # Still in progress
    )
    
    return temp_vendor
```

### Frontend Changes

#### 1. Updated Form Data Structure (`VendorRegistration.vue`)
**File**: `src/pages/vendor/VendorRegistration.vue`

**Changes**:
- Added `user_role` field to store user role from RBAC
- Added `user_rbac_permissions` field to store user permissions

**Code**:
```javascript
const vendor_formData = reactive({
  // ... existing fields ...
  user_role: null,  // Store user role from RBAC
  user_rbac_permissions: null  // Store user RBAC permissions
})
```

#### 2. Updated Computed Property for Registration Check
**File**: `src/pages/vendor/VendorRegistration.vue`

**Changes**:
- Modified `vendor_hasAlreadyRegistered` computed property
- Now checks BOTH user role AND lifecycle stage
- Only shows "Already Registered" if user is "vendor" AND stage != 1

**Code**:
```javascript
const vendor_hasAlreadyRegistered = computed(() => {
  if (!vendor_formData.lifecycle_data) return false
  
  const currentStage = vendor_formData.lifecycle_data.current_stage?.stage_id
  const userRole = vendor_formData.user_role
  
  // Check if user has "vendor" role (case-insensitive) AND lifecycle_stage is not 1
  const isVendorRole = userRole && userRole.toLowerCase() === 'vendor'
  const hasCompletedRegistration = currentStage && currentStage !== 1
  
  console.log('Checking registration status:', {
    currentStage,
    userRole,
    isVendorRole,
    hasCompletedRegistration,
    shouldShowAlreadyRegistered: isVendorRole && hasCompletedRegistration
  })
  
  return isVendorRole && hasCompletedRegistration
})
```

#### 3. Updated Data Fetching (`VendorRegistration.vue`)
**File**: `src/pages/vendor/VendorRegistration.vue`

**Changes**:
- Modified `vendor_fetchUserData` to store user role and permissions
- Logs role and permission data for debugging

**Code**:
```javascript
// Store user role and RBAC permissions
if (result.data.user_role) {
  vendor_formData.user_role = result.data.user_role
  console.log('User role stored:', result.data.user_role)
}

if (result.data.user_rbac_permissions) {
  vendor_formData.user_rbac_permissions = result.data.user_rbac_permissions
  console.log('User RBAC permissions stored:', result.data.user_rbac_permissions)
}
```

## Lifecycle Stage Flow

### Stage Progression
1. **Stage 1 (REG - Registration)**: 
   - Set when temp_vendor is first created
   - User can fill out registration form
   - Shown to user as "Vendor Registration"

2. **Stage 2 (EXT_SCR - External Screening)**:
   - Set after successful registration submission
   - Automatic screening is performed
   - User sees "You Have Already Registered" message (if role is "vendor")
   - Shown to user as current stage in lifecycle tracker

3. **Subsequent Stages**:
   - Stage 3: Questionnaire Response
   - Stage 4: Risk Scoring
   - Stage 5: Response Approval (as shown in the uploaded image)
   - And so on...

### Database Tables Involved

#### 1. `rbac_tprm` Table
```sql
CREATE TABLE rbac_tprm (
  RBACId INT PRIMARY KEY AUTO_INCREMENT,
  UserId INT,
  UserName VARCHAR(255),
  Role VARCHAR(100),
  -- ... other permission columns ...
);
```

#### 2. `temp_vendor` Table
```sql
CREATE TABLE temp_vendor (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  UserId INT,
  lifecycle_stage BIGINT,
  company_name VARCHAR(255),
  -- ... other vendor fields ...
);
```

#### 3. `lifecycle_tracker` Table
```sql
CREATE TABLE lifecycle_tracker (
  id INT PRIMARY KEY AUTO_INCREMENT,
  vendor_id BIGINT,
  lifecycle_stage BIGINT,
  started_at DATETIME,
  ended_at DATETIME,  -- NULL if stage is in progress
);
```

#### 4. `vendor_lifecycle_stages` Table
```sql
CREATE TABLE vendor_lifecycle_stages (
  stage_id BIGINT PRIMARY KEY AUTO_INCREMENT,
  stage_name VARCHAR(100),
  stage_code VARCHAR(20),
  stage_order INT,
  description TEXT,
  is_active BOOLEAN,
  approval_required BOOLEAN,
  max_duration_days INT
);
```

## Testing Scenarios

### Scenario 1: New Vendor User (First Time Registration)
- **User Role**: "vendor" (in rbac_tprm)
- **Lifecycle Stage**: NULL or 1
- **Expected Behavior**: Show registration form
- **After Submission**: Update to stage 2, show "Already Registered" message

### Scenario 2: Vendor User Who Already Registered
- **User Role**: "vendor" (in rbac_tprm)
- **Lifecycle Stage**: 2, 3, 4, 5, etc. (anything except 1)
- **Expected Behavior**: Show "You Have Already Registered" message with current stage information

### Scenario 3: Non-Vendor User (Admin/Manager)
- **User Role**: "admin", "manager", etc. (NOT "vendor")
- **Lifecycle Stage**: Any value
- **Expected Behavior**: Show registration form (admins can always access the form)

### Scenario 4: User Without RBAC Entry
- **User Role**: NULL (no entry in rbac_tprm)
- **Lifecycle Stage**: Any value
- **Expected Behavior**: Show registration form (fallback behavior)

## API Endpoints

### 1. Get User Data
**Endpoint**: `GET /api/v1/vendor-core/temp-vendors/get_user_data/?user_id={userId}`

**Response**:
```json
{
  "status": "success",
  "message": "User data retrieved successfully",
  "data": {
    "temp_vendor": {
      "id": 123,
      "userid": 60,
      "company_name": "Test Vendor",
      "lifecycle_stage": 2,
      ...
    },
    "lifecycle": {
      "current_stage": {
        "stage_id": 2,
        "stage_name": "External Screening",
        "stage_code": "EXT_SCR"
      },
      "tracker_entries": [...]
    },
    "user_role": "vendor",
    "user_rbac_permissions": {
      "role": "vendor",
      "can_register_vendor": true,
      "can_view_vendor": true,
      "can_edit_vendor": false
    }
  }
}
```

### 2. Submit Registration
**Endpoint**: `POST /api/v1/vendor-core/temp-vendors/vendor_submit_registration/`

**Request Body**:
```json
{
  "company_name": "Test Vendor",
  "legal_name": "Test Vendor LLC",
  "business_type": "corporation",
  ...
  "contacts": [...],
  "documents": [...]
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Vendor registration submitted successfully",
  "data": {
    "id": 123,
    "lifecycle_stage": 2,
    "screening_status": "completed",
    ...
  }
}
```

## Logging

All lifecycle stage changes are logged with the following information:
- Vendor ID
- Old lifecycle stage
- New lifecycle stage
- Timestamp
- User ID (if available)

**Example Log Entry**:
```
[2025-01-27 10:30:15] INFO: Updated vendor 123 from stage 1 to stage 2
[2025-01-27 10:30:15] INFO: User 60 has role: vendor
```

## Error Handling

### 1. Missing User Role
- If no RBAC entry exists for user, log warning
- Allow registration to proceed (fallback behavior)

### 2. Missing Lifecycle Data
- If lifecycle_stage is NULL, initialize to 1
- Create initial lifecycle tracker entry

### 3. Stage Update Failure
- Log error with vendor ID and failure reason
- Continue with registration (don't block user)

## Future Enhancements

1. **Stage-based Permissions**: Add more granular permissions for each lifecycle stage
2. **Stage Notifications**: Send notifications when stage changes occur
3. **Stage Approvals**: Add approval workflow for certain stage transitions
4. **Stage History**: Display full lifecycle history to users
5. **Custom Stage Configurations**: Allow admin to define custom stages per vendor category

## Conclusion

This implementation provides a complete lifecycle management system for vendor registration with proper RBAC integration. The "Already Registered" screen is shown appropriately based on both user role and lifecycle stage, ensuring vendors see the correct interface based on their registration status.





