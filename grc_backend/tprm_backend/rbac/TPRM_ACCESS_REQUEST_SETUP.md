# TPRM Access Request System - Setup Guide

## Overview
This document explains how to set up and troubleshoot the TPRM Access Request system.

## Prerequisites

### 1. Database Table Creation
**CRITICAL:** The `AccessRequestTPRM` table must be created in the `tprm_integration` database before the system will work.

Run the SQL script:
```sql
-- File: grc_backend/tprm_backend/rbac/create_access_request_table.sql
CREATE TABLE IF NOT EXISTS `AccessRequestTPRM` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `requested_url` VARCHAR(500) NULL,
    `requested_feature` VARCHAR(255) NULL,
    `required_permission` VARCHAR(255) NULL,
    `requested_role` VARCHAR(100) NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'REQUESTED',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `approved_by` INT NULL,
    `audit_trail` JSON NULL,
    `message` TEXT NULL,
    INDEX `idx_user_id_created_at` (`user_id`, `created_at`),
    INDEX `idx_status` (`status`),
    INDEX `idx_approved_by` (`approved_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**To run the script:**
1. Connect to the `tprm_integration` database
2. Execute the SQL script above
3. Verify the table was created: `SHOW TABLES LIKE 'AccessRequestTPRM';`

## API Endpoints

### Create Access Request
- **URL:** `POST /api/tprm/rbac/access-requests/`
- **Headers:** 
  - `Authorization: Bearer <token>`
  - `Content-Type: application/json`
- **Body:**
```json
{
  "requested_url": "/tprm/my-contract-approvals",
  "requested_feature": "My Contract Approvals",
  "required_permission": "contract.view_contracts",
  "requested_role": "",
  "message": "Requesting access to My Contract Approvals"
}
```

### Get Access Requests
- **URL:** `GET /api/tprm/rbac/access-requests/<user_id>/`
- **Headers:** `Authorization: Bearer <token>`

### Update Access Request Status (Admin Only)
- **URL:** `PUT /api/tprm/rbac/access-requests/<request_id>/status/`
- **Headers:** `Authorization: Bearer <token>`
- **Body:**
```json
{
  "status": "APPROVED"  // or "REJECTED"
}
```

## Troubleshooting

### Issue: "No data added to table"

**Possible Causes:**

1. **Table doesn't exist**
   - **Solution:** Run the SQL script to create the table
   - **Check:** Query `SHOW TABLES LIKE 'AccessRequestTPRM';` in `tprm_integration` database

2. **Wrong database connection**
   - **Check:** Backend logs should show: `[TPRM Access Request] Using database connection: tprm`
   - **Solution:** Ensure `connections['tprm']` is configured in Django settings

3. **Authentication failure**
   - **Check:** Backend logs for `User not authenticated` error
   - **Solution:** Ensure JWT token is valid and user_id is extracted correctly

4. **Database error**
   - **Check:** Backend logs for database errors
   - **Solution:** Check database connection and table structure

### Issue: "Request not showing in user profile"

**Possible Causes:**

1. **No user profile component for TPRM**
   - **Solution:** Create a user profile component similar to GRC's UserProfile.vue
   - **Location:** `grc_frontend/tprm_frontend/src/components/UserProfile.vue` (needs to be created)

2. **API endpoint not called**
   - **Check:** Browser console for API errors
   - **Solution:** Ensure `GET_ACCESS_REQUESTS` endpoint is called in user profile component

## Testing Steps

1. **Test Table Exists:**
   ```sql
   USE tprm_integration;
   SHOW TABLES LIKE 'AccessRequestTPRM';
   DESCRIBE AccessRequestTPRM;
   ```

2. **Test API Endpoint:**
   ```bash
   curl -X POST http://localhost:8000/api/tprm/rbac/access-requests/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "requested_url": "/tprm/test",
       "requested_feature": "Test Feature",
       "message": "Test request"
     }'
   ```

3. **Check Database:**
   ```sql
   SELECT * FROM AccessRequestTPRM ORDER BY created_at DESC LIMIT 10;
   ```

## Next Steps

1. **Create User Profile Component for TPRM** (if it doesn't exist)
   - Add a "Requests" tab
   - Display access requests using `GET_ACCESS_REQUESTS` endpoint
   - Allow admins to approve/reject requests

2. **Add Admin Interface**
   - Create admin page to view all access requests
   - Add approve/reject functionality

3. **Add Notifications**
   - Notify admins when new access requests are created
   - Notify users when their requests are approved/rejected

