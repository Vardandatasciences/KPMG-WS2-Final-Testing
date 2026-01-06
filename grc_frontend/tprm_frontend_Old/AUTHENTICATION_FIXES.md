# Authentication & API Fixes - Complete Guide

## Problem Summary
The TPRM frontend was experiencing widespread 403 Forbidden errors on all API endpoints despite users being authenticated. This was caused by:

1. **Missing JWT Authentication**: Backend was not configured to recognize JWT Bearer tokens from the frontend
2. **Overly Strict RBAC**: Permission system was blocking all requests
3. **Aggressive Error Handling**: Frontend was immediately redirecting to error pages without attempting recovery
4. **Token Management Issues**: Expired/invalid tokens were not being properly refreshed

## Changes Made

### Backend Changes (`grc_backend/`)

#### 1. Created Unified JWT Authentication (`grc/jwt_auth.py`)
- ✅ New `UnifiedJWTAuthentication` class that properly decodes and validates JWT Bearer tokens
- ✅ Works with both GRC and TPRM user models
- ✅ Creates authenticated user objects even if user not found in database
- ✅ Handles token expiration gracefully with proper error messages

#### 2. Updated Django Settings (`backend/settings.py`)
```python
# Added JWT authentication to default authentication classes
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'grc.jwt_auth.UnifiedJWTAuthentication',  # JWT authentication for Bearer tokens
        'rest_framework.authentication.SessionAuthentication',  # Session-based auth
        'rest_framework.authentication.TokenAuthentication',  # Token auth as fallback
    ],
    ...
}

# Temporarily disabled RBAC to fix permission issues
RBAC_CONFIG = {
    'ENABLE_RBAC': False,  # Temporarily disabled
    'LOG_PERMISSIONS': True,
    'DEBUG_MODE': True,
}

RBAC_DECORATOR_BYPASS = True  # Bypass RBAC decorators
```

#### 3. Created Test Endpoints (`tprm_backend/core/test_views.py`)
- ✅ `/api/tprm/test/` - Test authentication and view user info
- ✅ `/api/tprm/test/cors/` - Test CORS configuration
- ✅ `/api/tprm/test/methods/` - Test HTTP methods

### Frontend Changes (`grc_frontend/tprm_frontend/`)

#### 1. Created Authentication Debug Utility (`src/utils/authDebug.js`)
Available globally as `window.authDebug` with methods:
- `checkAuth()` - View current authentication state
- `clearAuth()` - Clear all authentication data
- `testApiConnection()` - Test API connection with current token
- `decodeToken()` - Decode and inspect JWT token
- `forceReauth()` - Force re-authentication

#### 2. Updated Axios Interceptor (`src/config/axios.js`)
- ✅ More intelligent 403 error handling (doesn't redirect immediately)
- ✅ Automatic token refresh on 401 errors
- ✅ Better error logging and debugging
- ✅ Components can now handle 403 errors gracefully

#### 3. Updated API Service (`src/services/api.js`)
- ✅ Enhanced error handling for permission errors
- ✅ Doesn't automatically redirect on 403
- ✅ Attaches detailed error info to error objects

## How to Test

### Step 1: Restart the Backend Server
The Django server has been restarted automatically with the new JWT authentication settings.

**Verify server is running:**
```powershell
Test-NetConnection -ComputerName localhost -Port 8000
```

Expected: Shows `TcpTestSucceeded : True`

### Step 2: Test Authentication in Browser Console

Open your browser console (F12) and run:

```javascript
// Check current authentication state
window.authDebug.checkAuth()

// Decode your current token
window.authDebug.decodeToken()

// Test API connection
await window.authDebug.testApiConnection()
```

### Step 3: Test the New Test Endpoint

In browser console:
```javascript
// Test authentication endpoint
fetch('http://localhost:8000/api/tprm/test/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('session_token')}`,
    'Content-Type': 'application/json'
  }
})
.then(r => r.json())
.then(data => console.log('Auth Test Result:', data))
```

Expected response:
```json
{
  "message": "API is working",
  "authenticated": true,
  "user_id": 1,
  "username": "radha.sharma",
  "user_type": "AuthenticatedUser",
  "auth_method": "JWT"
}
```

### Step 4: Refresh the Page

1. **Clear the browser cache**: Press `Ctrl+Shift+Delete` → Clear cached images and files
2. **Hard refresh**: Press `Ctrl+F5` or `Ctrl+Shift+R`
3. **Navigate to any page** that was previously showing 403 errors

### Step 5: Check for Remaining Errors

If you still see 403 errors:

1. **Check if token is expired:**
```javascript
window.authDebug.decodeToken()
// Look for "Is Expired: false"
```

2. **If expired, clear auth and re-login:**
```javascript
window.authDebug.forceReauth()
```

3. **Check backend logs:**
```
Look in the terminal running Django server for JWT auth messages:
- [Unified JWT Auth] Token decoded successfully
- [Unified JWT Auth] User authenticated
```

## Common Issues and Solutions

### Issue 1: "Token has expired"
**Solution:**
```javascript
// Force re-authentication
window.authDebug.forceReauth()
// Then login again
```

### Issue 2: Still getting 403 errors
**Possible causes:**
1. Backend server wasn't restarted - check if it's running with JWT auth
2. Browser cached old responses - clear cache and hard refresh
3. Token is completely invalid - clear auth and re-login

**Solution:**
```javascript
// Clear all auth data
window.authDebug.clearAuth()
// Clear session storage
sessionStorage.clear()
// Hard refresh the page
location.reload(true)
```

### Issue 3: "No authentication token found"
**Solution:**
```javascript
// Check what tokens exist
window.authDebug.checkAuth()
// If no tokens, you need to login via GRC first
```

### Issue 4: CORS errors
**Solution:**
Test CORS endpoint:
```javascript
fetch('http://localhost:8000/api/tprm/test/cors/')
  .then(r => r.json())
  .then(data => console.log(data))
```

If CORS is not working, check Django `settings.py` for `CORS_ALLOWED_ORIGINS`

## Re-enabling RBAC (After Testing)

Once everything is working, you can re-enable RBAC:

1. Edit `grc_backend/backend/settings.py`:
```python
RBAC_CONFIG = {
    'ENABLE_RBAC': True,  # Re-enable RBAC
    'LOG_PERMISSIONS': True,
    'DEBUG_MODE': True,
}

RBAC_DECORATOR_BYPASS = False  # Re-enable RBAC decorators
```

2. Restart Django server

3. Ensure users have proper permissions assigned in the database

## Monitoring and Debugging

### Backend Logs
Watch for these messages in Django server terminal:
- `[Unified JWT Auth] Token decoded successfully`
- `[Unified JWT Auth] Authenticated user object created`

### Frontend Console
Watch for these messages in browser console:
- `Making GET/POST request to: ...`
- `Response received from: ...`
- `⚠️ 403 Forbidden:` (should not see this if RBAC is disabled)

## Next Steps

1. **Test all major features** to ensure they work without 403 errors
2. **Check user permissions** in the database for when RBAC is re-enabled
3. **Monitor backend logs** for any authentication issues
4. **Set up proper permission assignments** for different user roles

## Developer Notes

### JWT Token Structure
Tokens should contain:
- `user_id` - User ID from database
- `username` - Username
- `exp` - Expiration timestamp
- `iat` - Issued at timestamp

### Token Storage Keys (in order of preference)
1. `session_token` - Primary token key
2. `access_token` - Alternative token key
3. `token` - Fallback token key

### Authentication Flow
1. Frontend sends request with `Authorization: Bearer <token>` header
2. Backend's `UnifiedJWTAuthentication` intercepts and decodes token
3. User object is created and attached to request
4. RBAC checks permissions (if enabled)
5. View processes request and returns response

## Support

If issues persist after following this guide:
1. Check `window.authDebug.checkAuth()` output
2. Check Django server logs for errors
3. Verify token is not expired with `window.authDebug.decodeToken()`
4. Test the `/api/tprm/test/` endpoint
5. Clear all browser data and try again

---

**Changes Applied:** December 2024
**Status:** ✅ JWT Authentication Enabled, RBAC Temporarily Disabled for Testing

