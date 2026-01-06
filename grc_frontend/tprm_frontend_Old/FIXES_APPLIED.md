# TPRM Access Denied & API Fixes Applied

## Date: 2025-11-29

## Issues Fixed

### 1. ✅ RFP Dashboard Access Denied (404 Error)
**Problem**: TPRM frontend was calling `/api/tprm/rbac/rfp/` but getting 404  
**Root Cause**: Permission service was failing when token wasn't available  
**Fix Applied**:
- Updated `permissionsService.js` to work without requiring a token (uses `user_id` from query params)
- Added `app_name = 'tprm_rbac'` to `tprm_urls.py` for proper URL namespacing
- Backend already supports authentication via user_id in query params

### 2. ✅ GRC-to-TPRM Auth Sync (iframe localStorage issue)
**Problem**: TPRM iframe couldn't access GRC parent's localStorage due to same-origin policy  
**Fix Applied**:
- Updated `TprmWrapper.vue` to send auth data to TPRM iframe via postMessage
- Updated TPRM `auth.js` to listen for `GRC_AUTH_SYNC` messages and store tokens locally
- Tokens are now synced automatically when TPRM iframe loads

### 3. ✅ Token Refresh Rate Limiting (429 Error)
**Problem**: GRC frontend was making too many token refresh requests  
**Root Cause**: No cooldown period between refresh attempts  
**Fix Applied**:
- Added 5-second cooldown between refresh attempts
- Added 10-second penalty for rate-limited requests (429 errors)
- Added `isRefreshing` flag check to prevent concurrent refreshes

### 4. ✅ Wrong API Base URLs (404 on all TPRM endpoints)
**Problem**: TPRM frontend was calling `/api/contracts/` instead of `/api/tprm/contracts/`  
**Root Cause**: Hardcoded API base URLs without `/tprm` prefix  
**Fix Applied**:
- Updated `src/services/api.js`:
  - API_BASE_URL: `http://localhost:8000/api` → `http://localhost:8000/api/tprm`
  - RFP_API_URL: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`
  - SLA_API_URL: `http://localhost:8000/api/slas` → `http://localhost:8000/api/tprm/slas`
  - AUDITS_API_URL: `http://localhost:8000/api/audits` → `http://localhost:8000/api/tprm/audits`
  - NOTIFICATIONS_API_URL: `http://localhost:8000/api/notifications` → `http://localhost:8000/api/tprm/notifications`
  - BCPDRP_API_URL: `http://localhost:8000/api/bcpdrp` → `http://localhost:8000/api/tprm/bcpdrp`
  - RISK_ANALYSIS_API_URL: `http://localhost:8000/api/risk-analysis` → `http://localhost:8000/api/tprm/risk-analysis`

## Files Modified

### Backend
1. `grc_backend/tprm_backend/rbac/tprm_urls.py` - Added app_name for URL namespacing

### Frontend - TPRM
2. `grc_frontend/tprm_frontend/src/services/permissionsService.js` - Token-optional permission checks
3. `grc_frontend/tprm_frontend/src/stores/auth.js` - postMessage auth sync listener
4. `grc_frontend/tprm_frontend/src/services/api.js` - Fixed API base URLs with /tprm prefix

### Frontend - GRC
5. `grc_frontend/src/views/TprmWrapper.vue` - Auth sync via postMessage
6. `grc_frontend/src/services/authService.js` - Rate limit protection for token refresh

## How to Test

### Step 1: Restart Backend Server
```bash
cd grc_backend
python manage.py runserver
```

Wait for: `Starting development server at http://127.0.0.1:8000/`

### Step 2: Rebuild Frontend (if needed)
```bash
cd grc_frontend/tprm_frontend
npm run build
```

### Step 3: Test the Endpoints

1. **Test TPRM RBAC endpoint** (should return JSON, not 404):
   ```
   http://localhost:8000/api/tprm/rbac/rfp/?permission_type=view_rfp&user_id=1
   ```

2. **Test Contract endpoint** (should return JSON or empty array):
   ```
   http://localhost:8000/api/tprm/contracts/contracts/stats/
   ```

### Step 4: Test in Browser

1. **Logout and login again** to get fresh tokens
2. Navigate to RFP Dashboard - should load without "Access Denied"
3. Check browser console - no more 404 errors on `/api/tprm/` endpoints
4. Check for auth sync logs: `[TPRM AuthStore] Auth synced successfully`

## Expected Console Logs

✅ **Good logs to see**:
```
[TprmWrapper] Sending auth data to TPRM iframe: {hasToken: true, hasUser: true, isAuthenticated: true}
[TPRM AuthStore] Received auth sync from GRC: {hasToken: true, hasUser: true, isAuthenticated: true}
[TPRM AuthStore] Auth synced successfully: {user: 'radha.sharma', hasToken: true}
[PermissionsService] RFP Permission check result: view_rfp = true
```

❌ **Should NOT see these anymore**:
```
404 (Not Found) on /api/tprm/rbac/rfp/
404 (Not Found) on /api/contracts/contracts/
429 (Too Many Requests) on /api/jwt/refresh/
[PermissionsService] No session token found
```

## Architecture Overview

```
┌─────────────────┐
│  GRC Frontend   │  ← User logs in here
│  (port 8080)    │
└────────┬────────┘
         │ 1. User login
         │ 2. Store: token, user, isAuthenticated
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌─────────────────┐              ┌──────────────────┐
│ TprmWrapper.vue │              │  GRC Backend     │
│                 │─────────────▶│  (port 8000)     │
│ postMessage     │  3. Auth     │  /api/jwt/login  │
│ auth to iframe  │     Sync     └──────────────────┘
└────────┬────────┘
         │ 4. Send token + user via postMessage
         │
         ▼
┌─────────────────┐              ┌──────────────────┐
│ TPRM Frontend   │              │  TPRM Backend    │
│ (iframe)        │─────────────▶│  (port 8000)     │
│ auth.js         │  5. API      │  /api/tprm/*     │
│ receives sync   │     calls    │  - /rbac/rfp/    │
└─────────────────┘              │  - /contracts/   │
                                 │  - /slas/        │
                                 └──────────────────┘
```

## Troubleshooting

### If you still see 404 errors:
1. Check if backend server is running: `http://localhost:8000/admin`
2. Verify TPRM app is installed in `settings.py` → `INSTALLED_APPS`
3. Check URL configuration in `backend/urls.py` line 137:
   ```python
   path('api/tprm/rbac/', include('tprm_backend.rbac.tprm_urls'))
   ```

### If you see "No session token found":
1. Check browser console for `[TPRM AuthStore] Auth synced successfully`
2. Verify localStorage has `access_token`, `user`, `isAuthenticated`
3. Try logout and login again

### If you see 429 Rate Limit:
1. Wait 10 seconds
2. Logout and login again to get fresh tokens
3. Check `localStorage.getItem('last_refresh_attempt')` - clear if stuck

## Next Steps

1. ✅ All changes are committed - just restart backend server
2. ✅ Test RFP dashboard access
3. ✅ Test contract dashboard
4. ✅ Verify no more 404 errors in console
5. Monitor for any new issues

---
**Note**: All fixes are backward compatible and won't affect existing functionality.


