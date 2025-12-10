# Google SSO RBAC and Refresh Token Fix Summary

## Issues Fixed

### 1. **Refresh Token Blacklisting Issue (401 Errors)**
   - **Problem**: Refresh token was being blacklisted before generating new tokens, causing 401 errors when frontend tried to refresh multiple times
   - **Fix**: Changed order to generate new tokens FIRST, then blacklist old token
   - **File**: `grc_backend/grc/authentication.py` (lines 554-578)

### 2. **Frontend Refresh Token Handling**
   - **Problem**: Multiple simultaneous refresh attempts causing race conditions
   - **Fix**: 
     - Added timeout protection (10 seconds)
     - Better error handling to not log out if access token is still valid
     - Improved refresh attempt tracking
   - **File**: `grc_frontend/src/services/authService.js` (lines 483-554)

### 3. **RBAC FrameworkId Handling**
   - **Problem**: RBAC assignment would fail if user doesn't have a FrameworkId
   - **Fix**: 
     - Added fallback to use first available framework if user doesn't have one
     - Added warning logs if no framework is available
   - **File**: `grc_backend/grc/authentication.py` (lines 30-35, 68-84)

## RBAC Permissions for Google SSO Users

### GRC RBAC Permissions (View Only)
- `ViewAllCompliance` = True
- `ViewAllPolicy` = True
- `ViewAuditReports` = True
- `ViewAllRisk` = True
- `ViewAllIncident` = True
- `ViewAllEvents` = True
- All other permissions = False (view only)

### TPRM RBAC Permissions (View Only)
- All `View*` permissions = True
- `ListContracts`, `ListContractTerms`, `ListContractRenewals` = True
- All other permissions = False (view only)

## How It Works

1. **User logs in via Google SSO**
2. **Backend creates/updates user in `users` table**
3. **Backend automatically assigns RBAC permissions** via `assign_default_rbac_permissions_for_google_sso(user)`
4. **Frontend receives tokens and stores them**
5. **Frontend initializes RBAC service** to load permissions
6. **User can now access all modules with view permissions**

## Testing

1. **Test Google SSO Login:**
   - Login with Google account
   - Check backend logs for: `✅ Created GRC RBAC entry with view permissions for Google SSO user: <username>`
   - Check backend logs for: `✅ Created TPRM RBAC entry with view permissions for Google SSO user: <username>`

2. **Verify RBAC Permissions:**
   ```sql
   -- Check GRC RBAC
   SELECT * FROM grc2.rbac WHERE UserId = <user_id>;
   
   -- Check TPRM RBAC
   SELECT * FROM grc2.rbac_tprm WHERE UserId = <user_id>;
   ```

3. **Verify User Can Access Platform:**
   - User should see navbar and sidebar
   - User should be able to view all modules
   - User should NOT be able to create/edit/delete (view only)

## SQL Queries to Manually Update Existing Users

If you need to manually update RBAC for existing Google SSO users, use the queries in:
- `AUTO_INSERT_RBAC_FOR_GOOGLE_USERS.sql`
- `UPDATE_RBAC_GOOGLE_SSO.sql`

## Notes

- RBAC permissions are automatically assigned during Google OAuth callback
- If RBAC assignment fails, login still succeeds (error is logged but doesn't block login)
- Refresh token is rotated on each refresh for security
- Access token is valid for 1 hour
- Refresh token is valid for 7 days

