# Questionnaire Template 403 Forbidden Error - Fix Summary

## Problem
Users were getting a **403 Forbidden** error when trying to create questionnaire templates via the `/bcpdrp/questionnaire-templates/save/` endpoint.

### Error Message
```
Failed to load resource: the server responded with a status of 403 (Forbidden)
http://127.0.0.1:8000/bcpdrp/questionnaire-templates/save/
```

## Root Cause
The TPRM MFA authentication system (`grc_backend/tprm_backend/mfa_auth/jwt_service.py`) was **NOT including `tenant_id` in the JWT token payload** when users logged in. This caused:

1. The `TenantContextMiddleware` couldn't extract `tenant_id` from the JWT token
2. The `@require_tenant` decorator returned 403 because `request.tenant` was `None`
3. The request never reached the actual view function or RBAC permission check

## Files Modified

### 1. `grc_backend/tprm_backend/mfa_auth/jwt_service.py`
**Issue**: JWT tokens generated for TPRM users did not include `tenant_id` claim

**Fix**: Added `tenant_id` to JWT token payload in three places:
- `generate_tokens()` method - Added tenant_id to both access and refresh token payloads
- `refresh_access_token()` method - Added tenant_id when generating new access token

**Changes**:
```python
# MULTI-TENANCY: Get tenant_id from user
tenant_id = None
if hasattr(user, 'tenant_id') and user.tenant_id:
    tenant_id = user.tenant_id
elif hasattr(user, 'TenantId') and user.TenantId:
    tenant_id = user.TenantId

# Add to payload
access_payload = {
    'user_id': user.userid,
    'username': user.username,
    'email': user.email,
    'tenant_id': tenant_id,  # MULTI-TENANCY: Include tenant_id
    # ... other fields
}
```

### 2. `grc_backend/tprm_backend/core/tenant_utils.py`
**Issue**: Error messages from `@require_tenant` decorator were not helpful for debugging

**Fix**: Enhanced error logging and response to include:
- User ID
- Auth header presence
- Request path
- Debug information in JSON response

**Changes**:
```python
logger.warning(f"[Tenant Utils] Tenant required but not found for {request.method} {request.path}")
logger.warning(f"[Tenant Utils] User ID: {user_id}, Auth header present: {bool(auth_header)}")

return JsonResponse({
    'error': 'Tenant context not found',
    'detail': 'This endpoint requires tenant authentication. Please ensure your JWT token includes tenant_id.',
    'debug_info': {
        'user_id': user_id,
        'has_auth': bool(auth_header),
        'path': request.path
    }
}, status=403)
```

### 3. `grc_backend/tprm_backend/bcpdrp/views.py`
**Issue**: No debug logging to help identify where the 403 was coming from

**Fix**: Added comprehensive debug logging at the start of `questionnaire_template_save_view()`

**Changes**:
```python
# DEBUG: Log request details
logger.info(f"[Questionnaire Template Save] Request received from user: {getattr(request.user, 'userid', 'unknown')}")
logger.info(f"[Questionnaire Template Save] Request tenant_id: {getattr(request, 'tenant_id', 'not set')}")
logger.info(f"[Questionnaire Template Save] Request data keys: {list(request.data.keys()) if request.data else 'no data'}")
```

## How the Fix Works

### Before Fix:
1. User logs in via TPRM MFA → JWT token generated **WITHOUT** `tenant_id`
2. Frontend makes POST request to `/bcpdrp/questionnaire-templates/save/` with JWT token
3. `TenantContextMiddleware` tries to extract tenant from JWT → **FAILS** (no tenant_id in token)
4. `@require_tenant` decorator checks `request.tenant` → **None**
5. Returns **403 Forbidden** before RBAC or view logic runs

### After Fix:
1. User logs in via TPRM MFA → JWT token generated **WITH** `tenant_id`
2. Frontend makes POST request to `/bcpdrp/questionnaire-templates/save/` with JWT token
3. `TenantContextMiddleware` extracts tenant from JWT → **SUCCESS**
4. `@require_tenant` decorator checks `request.tenant` → **Valid tenant object**
5. `@rbac_bcp_drp_required` checks permissions → **Passes if user has permission**
6. View function executes → **Creates questionnaire template**

## Testing Instructions

### 1. Restart Backend Server
The JWT service changes require a server restart:
```bash
cd grc_backend
python manage.py runserver
```

### 2. Re-login to Get New JWT Token
**IMPORTANT**: Existing JWT tokens in localStorage do NOT have `tenant_id`. Users must:
1. Log out of the application
2. Log back in to get a new JWT token with `tenant_id`

### 3. Test Questionnaire Template Creation
1. Navigate to the Contract Creation page
2. Add a contract term
3. Click "Create Questionnaires" for that term
4. You should be redirected to the Questionnaire Templates page
5. Fill in the form and click "Save Template"
6. **Expected**: Success message, template created
7. **Previous**: 403 Forbidden error

### 4. Verify JWT Token Contains tenant_id
Open browser console and run:
```javascript
const token = localStorage.getItem('session_token')
const payload = JSON.parse(atob(token.split('.')[1]))
console.log('JWT Payload:', payload)
console.log('Has tenant_id:', 'tenant_id' in payload)
console.log('tenant_id value:', payload.tenant_id)
```

**Expected Output**:
```
JWT Payload: {user_id: 8, username: "...", email: "...", tenant_id: 2, ...}
Has tenant_id: true
tenant_id value: 2
```

### 5. Check Backend Logs
Look for these log messages in the backend terminal:
```
[Tenant Middleware] JWT payload tenant_id: 2
[Tenant Middleware] ✅ Found tenant from JWT: Tenant 2 (ID: 2)
[Tenant Middleware] ✅ Resolved tenant: Tenant 2 (ID: 2) for POST /bcpdrp/questionnaire-templates/save/
[Questionnaire Template Save] Request received from user: 8
[Questionnaire Template Save] Request tenant_id: 2
```

## Additional Notes

### User Model
The `User` model in `grc_backend/tprm_backend/mfa_auth/models.py` has a `tenant_id` field:
```python
tenant_id = models.IntegerField(db_column="TenantId", null=True, blank=True)
```

This field is used to determine which tenant a user belongs to.

### RBAC Permissions
The endpoint requires the `create_questionnaire` permission, which maps to `create_questionnaire_for_testing` in the RBAC system. Ensure users have this permission in the `rbac_tprm` table.

### Decorator Order
The decorators on the view are executed in reverse order:
1. `@tenant_filter` - Adds tenant_id to request
2. `@require_tenant` - Checks tenant exists (was failing before fix)
3. `@rbac_bcp_drp_required` - Checks RBAC permissions
4. `@permission_classes` - Checks DRF permissions
5. `@authentication_classes` - Authenticates user
6. `@api_view` - Handles HTTP method

## Related Endpoints
This fix also resolves 403 errors for any other endpoints that use `@require_tenant` decorator when accessed by TPRM MFA authenticated users.

## Rollback Instructions
If this fix causes issues, revert the changes to:
1. `grc_backend/tprm_backend/mfa_auth/jwt_service.py`
2. `grc_backend/tprm_backend/core/tenant_utils.py`
3. `grc_backend/tprm_backend/bcpdrp/views.py`

Then restart the backend server.

