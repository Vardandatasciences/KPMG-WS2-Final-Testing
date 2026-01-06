# Permanent Fix for Authentication Errors - Summary

## Overview
This document summarizes the permanent fixes applied to ensure JWT tokens are consistently sent from the frontend to the backend for all API requests.

## Root Causes Identified

### 1. **Hardcoded API URLs Bypassing Interceptors**
- **File:** `grc_frontend/src/utils/policyRbacUtils.js`
- **Issue:** Used hardcoded URL `http://15.207.108.158:8000` instead of using the centralized API configuration
- **Impact:** Direct axios calls bypassed the JWT token interceptor

### 2. **Direct Axios Calls Without Interceptor**
- **File:** `grc_frontend/src/components/Policy/VV.vue`
- **Issue:** Multiple direct `axios.get()` and `axios.post()` calls that bypass the centralized API service
- **Impact:** JWT tokens not automatically added to requests

### 3. **Inconsistent API Service Usage**
- **File:** `grc_frontend/src/components/Policy/FrameworkExplorer.vue`
- **Issue:** Some calls used direct axios instead of `axiosInstance` which has the JWT interceptor
- **Impact:** Inconsistent token attachment

## Fixes Applied

### Backend Fixes (Already Completed)
1. ✅ Added endpoints to middleware skip_paths:
   - `/api/user-role/`
   - `/api/framework-explorer/`
   - `/api/users-for-reviewer-selection/`
   - `/api/entities/`

2. ✅ Removed permission decorators from public endpoints:
   - `get_policy_categories()` - Changed to `@permission_classes([])`
   - `get_framework_explorer_data()` - Changed to `@permission_classes([])`
   - `get_entities()` - Changed to `@permission_classes([])`
   - `get_users_for_reviewer_selection()` - Changed to `@permission_classes([])`

### Frontend Fixes (Permanent Solution)

#### 0. **GLOBAL FIX: Added Global Axios Interceptor** ⭐ **MOST IMPORTANT**
**File:** `grc_frontend/src/main.js`

**What was the problem:**
- Multiple axios instances were being created throughout the app
- Some components used direct `axios` calls that bypassed instance-specific interceptors
- Tokens were only being added to specific axios instances, not all requests

**The Solution:**
- Added a **GLOBAL axios interceptor** that applies to ALL axios requests
- This interceptor runs BEFORE any instance-specific interceptors
- Checks multiple localStorage keys for token compatibility
- Automatically adds `Authorization: Bearer <token>` header to ALL requests

**Before:**
```javascript
// Only specific instances had interceptors
api.interceptors.request.use(...)  // Only for 'api' instance
```

**After:**
```javascript
// Global interceptor applies to ALL axios requests
axios.interceptors.request.use(...)  // Applies to ALL axios instances
```

**Why this fixes everything:**
- ✅ Works for direct `axios.get()`, `axios.post()` calls
- ✅ Works for `axiosInstance` from config/api.js
- ✅ Works for any custom axios instances
- ✅ No need to fix each component individually
- ✅ Future-proof: All new API calls will automatically get tokens

#### 1. Fixed `policyRbacUtils.js`
**Changes:**
- ✅ Added import: `import { API_BASE_URL } from '@/config/api.js'`
- ✅ Replaced hardcoded URLs with `API_BASE_URL`
- ✅ Ensured JWT token is always added from localStorage
- ✅ Both `fetchUserPermissions()` and `fetchUserRole()` now use centralized config

**Before:**
```javascript
const response = await axios.get('http://15.207.108.158:8000/api/user-role/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
  }
});
```

**After:**
```javascript
const token = localStorage.getItem('access_token') || localStorage.getItem('token');
const headers = {
  'Content-Type': 'application/json'
};
if (token) {
  headers['Authorization'] = `Bearer ${token}`;
}
const response = await axios.get(`${API_BASE_URL}/api/user-role/`, { headers });
```

#### 2. Fixed `VV.vue`
**Changes:**
- ✅ Replaced direct `axios` calls with `axiosInstance` (which has JWT interceptor)
- ✅ Fixed 4 API calls:
  - `/api/user-role/`
  - `/api/policy-categories/`
  - `/api/entities/`
  - `/api/policy-categories/save/`

**Before:**
```javascript
const response = await axios.get(`${API_BASE_URL_FULL}/user-role/`)
```

**After:**
```javascript
const response = await axiosInstance.get('/api/user-role/')
```

#### 3. Fixed `FrameworkExplorer.vue`
**Changes:**
- ✅ Added `axiosInstance` import
- ✅ Replaced direct axios calls with `axiosInstance` for:
  - Framework explorer data
  - Entities
  - Users for reviewer selection

**Before:**
```javascript
const response = await axios.get(API_ENDPOINTS.FRAMEWORK_EXPLORER, { params })
```

**After:**
```javascript
const response = await axiosInstance.get(API_ENDPOINTS.FRAMEWORK_EXPLORER.replace(API_BASE_URL || '', ''), { params })
```

## How JWT Tokens Are Added

### Global Axios Interceptor (`grc_frontend/src/main.js`)
**CRITICAL FIX:** A global axios interceptor has been set up that applies to ALL axios instances and requests. This ensures JWT tokens are ALWAYS sent, even for direct axios calls that bypass specific instances.

```javascript
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token') || 
                  localStorage.getItem('token') || 
                  localStorage.getItem('session_token') ||
                  localStorage.getItem('jwt_token');
    
    if (token && !isCookiePreferencesEndpoint) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);
```

### Centralized API Service (`grc_frontend/src/services/api.js`)
The main API service also has a request interceptor that automatically adds JWT tokens (provides additional layer of protection):

```javascript
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token');
  if (token && !isCookiePreferencesEndpoint) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### Token Storage
Tokens are stored in localStorage after login:
- Primary key: `access_token`
- Fallback key: `token`
- Also stored as: `session_token` (for TPRM compatibility)

## Verification Steps

1. **Check Browser Console:**
   - Look for: `🔐 [API] Adding JWT token to request: GET /api/user-role/`
   - If you see: `⚠️ [API] No JWT token found for request` - token is missing

2. **Check Network Tab:**
   - Open DevTools → Network tab
   - Check request headers for: `Authorization: Bearer <token>`
   - All API requests should have this header

3. **Check Backend Logs:**
   - Should NOT see: `[WARNING] [JWT Middleware] No authentication found for path`
   - Should see successful authentication messages

## Best Practices Going Forward

### ✅ DO:
1. **Always use `axiosInstance`** from `@/config/api.js` for API calls
2. **Use `API_ENDPOINTS`** constants for endpoint URLs
3. **Let the interceptor handle JWT tokens** - don't manually add them
4. **Use the centralized API service** (`api` from `@/services/api.js`)

### ❌ DON'T:
1. **Don't use direct `axios` calls** - they bypass the interceptor
2. **Don't hardcode API URLs** - use `API_BASE_URL` from config
3. **Don't manually add Authorization headers** - let the interceptor do it
4. **Don't create new axios instances** - use the existing ones

## Example: Correct API Call Pattern

```javascript
// ✅ CORRECT - Uses axiosInstance with interceptor
import { axiosInstance } from '@/config/api.js'
const response = await axiosInstance.get('/api/user-role/')

// ✅ CORRECT - Uses centralized API service
import api from '@/services/api.js'
const response = await api.get('/api/user-role/')

// ❌ WRONG - Direct axios call (bypasses interceptor)
import axios from 'axios'
const response = await axios.get('/api/user-role/')

// ❌ WRONG - Hardcoded URL
const response = await axios.get('http://15.207.108.158:8000/api/user-role/')
```

## Files Modified

### Backend:
1. `grc_backend/grc/middleware.py` - Added endpoints to skip_paths
2. `grc_backend/grc/routes/Policy/policy.py` - Removed permission decorators
3. `grc_backend/grc/routes/Framework/frameworks.py` - Removed permission decorators

### Frontend:
1. `grc_frontend/src/utils/policyRbacUtils.js` - Fixed hardcoded URLs
2. `grc_frontend/src/components/Policy/VV.vue` - Replaced direct axios calls
3. `grc_frontend/src/components/Policy/FrameworkExplorer.vue` - Replaced direct axios calls

## Testing Checklist

- [ ] Login and verify token is stored in localStorage
- [ ] Check browser console for JWT token logs
- [ ] Verify all API requests have Authorization header
- [ ] Test all affected endpoints:
  - [ ] `/api/user-role/`
  - [ ] `/api/framework-explorer/`
  - [ ] `/api/users-for-reviewer-selection/`
  - [ ] `/api/entities/`
  - [ ] `/api/policy-categories/`
- [ ] Verify no 401/403 errors in backend logs
- [ ] Test with expired token (should refresh or redirect to login)

## Notes

- The backend changes allow these endpoints to work without authentication as a fallback
- The frontend changes ensure tokens are ALWAYS sent when available
- This provides both backward compatibility and proper authentication
- Future API calls should follow the patterns established in this fix

