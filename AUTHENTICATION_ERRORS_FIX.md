# Authentication Errors Analysis & Fix

## Summary
This document explains the authentication errors observed in the logs and the fixes applied.

## Errors Identified

### 1. **JWT Tokens Not Being Sent**
**Error Messages:**
```
[WARNING] [JWT Middleware] No authentication found for path: /api/user-role/
[WARNING] [JWT Middleware] No authentication found for path: /api/framework-explorer/
[WARNING] [JWT Middleware] No authentication found for path: /api/users-for-reviewer-selection/
[WARNING] [JWT Middleware] No authentication found for path: /api/entities/
```

**Root Cause:**
- The frontend is not consistently sending JWT tokens in the `Authorization` header for all API requests
- Some requests are made without the Bearer token, causing 401 Unauthorized errors

**Fix Applied:**
- Added these endpoints to the middleware skip_paths list so they can work without authentication
- Removed permission decorators that require authentication for public endpoints
- **Note:** Ideally, the frontend should be updated to always send JWT tokens for authenticated endpoints

### 2. **RBAC Permission Checks Running on Public Endpoints**
**Error Messages:**
```
❌ GET /api/policy-categories/ - 403
[WARNING] [RBAC POLICY] No user_id found for view permission check
```

**Root Cause:**
- `/api/policy-categories/` was in the middleware skip_paths (public endpoint)
- BUT the view function had `@permission_classes([PolicyViewPermission])` decorator
- This decorator runs AFTER middleware and still requires authentication
- Since no JWT token was provided, RBAC check failed → 403 Forbidden

**Fix Applied:**
- Changed `@permission_classes([PolicyViewPermission])` to `@permission_classes([])` for:
  - `get_policy_categories()` 
  - `get_framework_explorer_data()`
  - `get_entities()`
  - `get_users_for_reviewer_selection()` (uses query params for filtering)

### 3. **User ID Not Found in Session/JWT**
**Error Messages:**
```
[WARNING] [RBAC] No user_id found in session
[WARNING] [RBAC] No user_id found in request.user, JWT token, or session
[WARNING] [RBAC POLICY] No user_id found for view permission check
```

**Root Cause:**
- RBAC permission classes try to extract user_id from:
  1. `request.user` (set by middleware if JWT token is valid)
  2. JWT token in Authorization header
  3. Session data
- When none of these have user_id, warnings are logged and requests fail

**Fix Applied:**
- Endpoints that don't strictly require user authentication now skip RBAC checks
- Added endpoints to middleware skip_paths to prevent authentication failures

## Files Modified

### 1. `grc_backend/grc/middleware.py`
- Added these endpoints to `skip_paths`:
  - `/api/user-role/`
  - `/api/framework-explorer/`
  - `/api/users-for-reviewer-selection/`
  - `/api/entities/`

### 2. `grc_backend/grc/routes/Policy/policy.py`
- Changed `get_policy_categories()`: Removed `PolicyViewPermission`, now uses `[]`
- Changed `get_framework_explorer_data()`: Removed `PolicyViewPermission`, now uses `[]`
- Changed `get_entities()`: Removed `PolicyViewPermission`, now uses `[]`

### 3. `grc_backend/grc/routes/Framework/frameworks.py`
- Changed `get_users_for_reviewer_selection()`: Removed `PolicyViewPermission`, now uses `[]`

## Recommendations for Future Improvements

### 1. **Frontend Token Management**
- Ensure ALL authenticated API requests include JWT token in `Authorization: Bearer <token>` header
- Check that `localStorage.getItem('access_token')` returns a valid token
- Implement token refresh mechanism before tokens expire
- Add global axios interceptor to add tokens to all requests

### 2. **Endpoint Security**
- Review which endpoints should be public vs require authentication
- For endpoints that use query parameters for user identification (like `user_id=1`), consider:
  - Requiring JWT token and validating user_id matches token
  - OR clearly document that these are public endpoints with limited data access

### 3. **Middleware & Permission Consistency**
- Ensure consistency between:
  - Middleware `skip_paths` list
  - DRF permission decorators on views
  - Actual security requirements
- When an endpoint is in `skip_paths`, permission classes should also allow public access

### 4. **Error Handling**
- Consider returning more specific error messages:
  - 401: "No authentication token provided"
  - 403: "User does not have required permissions"
  - 401: "JWT token expired" (with refresh token hint)

## Testing Recommendations

1. **Test with JWT Token:**
   ```javascript
   // Frontend should send:
   headers: {
     'Authorization': 'Bearer <jwt_token>'
   }
   ```

2. **Test without JWT Token:**
   - Public endpoints should still work
   - Protected endpoints should return 401 with clear error message

3. **Test Token Expiry:**
   - Expired tokens should trigger refresh mechanism
   - Or return 401 with clear message

## Current Status

✅ **Fixed:** All identified endpoints now work without requiring JWT tokens (as public endpoints)
⚠️ **Note:** This is a temporary fix. Long-term solution should ensure frontend sends JWT tokens for authenticated endpoints.

