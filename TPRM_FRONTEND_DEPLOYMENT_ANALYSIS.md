# TPRM Frontend Deployment Analysis Report
## CURRENT vs NEW Frontend Comparison

**Date:** November 2024  
**Purpose:** Identify all deployment-related differences between CURRENT and NEW frontend

---

## 🔍 Executive Summary

### Critical Differences Found: **7 Major Issues**

1. ❌ **Production Base Path Missing** - NEW frontend lacks `/tprm/` base path configuration
2. ❌ **Production API URLs Missing** - NEW frontend uses hardcoded `localhost:8000` instead of production URLs
3. ❌ **Router Base Path Missing** - NEW frontend router doesn't configure production base path
4. ❌ **Environment Variable Support Missing** - NEW frontend lacks environment-aware URL resolution
5. ❌ **Dockerfile Missing** - NEW frontend has no Dockerfile for deployment
6. ⚠️ **Package.json Scripts** - Missing cleanup scripts
7. ⚠️ **Dependency Difference** - Missing `"frontend": "file:.."` dependency

---

## 📋 Detailed Comparison

### 1. **vite.config.js** - CRITICAL ⚠️

#### CURRENT Frontend (`grc_frontend/tprm_frontend/vite.config.js`):
```javascript
export default defineConfig({
  // Only use /tprm/ base path in production builds
  // In development, Vite dev server runs on its own port (3000) without base path
  base: process.env.NODE_ENV === 'production' ? '/tprm/' : '/',
  // ... rest of config
})
```

#### NEW Frontend (`frontend/vite.config.js`):
```javascript
export default defineConfig({
  // ❌ MISSING: base path configuration
  plugins: [
    // ... rest of config
  ],
})
```

**Impact:** 
- ❌ Production builds will fail to load assets correctly
- ❌ Routes won't work in production deployment
- ❌ Frontend won't be accessible at `https://grc-tprm.vardaands.com/tprm`

**Fix Required:** Add base path configuration

---

### 2. **src/router/index.js** - CRITICAL ⚠️

#### CURRENT Frontend:
```javascript
// Configure router base path to match Vite base configuration
// In production, Vite uses /tprm/ base, so router must match
// In development, both use / (root)
const routerBase = import.meta.env.MODE === 'production' ? '/tprm/' : '/'

const router = createRouter({
  history: createWebHistory(routerBase),
  // ...
})
```

#### NEW Frontend:
```javascript
const router = createRouter({
  history: createWebHistory(), // ❌ MISSING: routerBase parameter
  // ...
})
```

**Impact:**
- ❌ Router won't work correctly in production
- ❌ All routes will fail when deployed
- ❌ Navigation will break

**Fix Required:** Add router base path configuration

---

### 3. **src/config/api.js** - CRITICAL ⚠️

#### CURRENT Frontend:
```javascript
const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 
            import.meta.env.VITE_TPRM_API_BASE_URL || 
            'https://grc-tprm.vardaands.com/api/tprm',
  RFP_APPROVAL_BASE: import.meta.env.VITE_RFP_APPROVAL_BASE || 
                     `${import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_TPRM_API_BASE_URL || 'https://grc-tprm.vardaands.com/api/tprm'}/rfp-approval`,
  // ...
}
```

#### NEW Frontend:
```javascript
const API_CONFIG = {
  BASE_URL: 'http://localhost:8000/api', // ❌ HARDCODED localhost
  RFP_APPROVAL_BASE: 'http://localhost:8000/api/rfp-approval', // ❌ HARDCODED localhost
  // ...
}
```

**Impact:**
- ❌ Frontend will try to connect to `localhost:8000` in production (will fail)
- ❌ All API calls will fail in production
- ❌ No environment variable support

**Fix Required:** Add environment variable support with production fallback

---

### 4. **src/services/api.js** - CRITICAL ⚠️

#### CURRENT Frontend:
```javascript
import { getTprmApiBaseUrl, getApiOrigin } from '@/utils/backendEnv'

// Use environment-aware URL resolution - defaults to production
const TPRM_BASE = getTprmApiBaseUrl();
const API_BASE_URL = TPRM_BASE;
const RFP_API_URL = `${TPRM_BASE}/rfp`;
// ... uses environment-aware functions
```

#### NEW Frontend:
```javascript
const API_BASE_URL = 'http://localhost:8000/api'; // ❌ HARDCODED localhost
const RFP_API_URL = 'http://localhost:8000/api/v1'; // ❌ HARDCODED localhost
// ... all URLs hardcoded to localhost
```

**Impact:**
- ❌ All API services will fail in production
- ❌ No environment variable support
- ❌ Missing `backendEnv.js` utility usage

**Fix Required:** 
- Add `backendEnv.js` utility import
- Replace all hardcoded URLs with environment-aware functions

---

### 5. **src/utils/backendEnv.js** - MISSING ⚠️

#### CURRENT Frontend:
- ✅ Has `backendEnv.js` utility file
- ✅ Provides `getTprmApiBaseUrl()` function
- ✅ Provides `getApiOrigin()` function
- ✅ Handles environment variable resolution
- ✅ Defaults to production URLs

#### NEW Frontend:
- ❌ Has `backendEnv.js` but with different implementation
- ❌ Returns `'http://localhost:8000'` as default
- ❌ Missing production URL fallback

**Impact:**
- ❌ Environment utility doesn't work for production
- ❌ All dependent services will use localhost

**Fix Required:** Update `backendEnv.js` to match CURRENT implementation

---

### 6. **package.json** - MINOR ⚠️

#### CURRENT Frontend:
```json
{
  "scripts": {
    // ... other scripts
    "clean": "node -e \"require('fs').rmSync('node_modules/.vite', {recursive: true, force: true}); require('fs').rmSync('dist', {recursive: true, force: true})\"",
    "clean:cache": "node -e \"require('fs').rmSync('node_modules/.vite', {recursive: true, force: true})\""
  },
  "dependencies": {
    // ... other deps
    "frontend": "file:..", // ✅ Has this dependency
  }
}
```

#### NEW Frontend:
```json
{
  "scripts": {
    // ❌ MISSING: clean and clean:cache scripts
  },
  "dependencies": {
    // ❌ MISSING: "frontend": "file:.." dependency
  }
}
```

**Impact:**
- ⚠️ Minor: Missing cleanup scripts (not critical)
- ⚠️ Minor: Missing dependency (may affect build)

**Fix Required:** Add missing scripts and dependency (optional)

---

### 7. **Dockerfile** - MISSING ⚠️

#### CURRENT Frontend:
- ✅ Has `Dockerfile` for Docker deployment
- ✅ Multi-stage build configuration
- ✅ Nginx serving configuration

#### NEW Frontend:
- ❌ No `Dockerfile` found

**Impact:**
- ❌ Cannot deploy using Docker
- ❌ No containerized deployment option

**Fix Required:** Copy Dockerfile from CURRENT frontend (if Docker deployment needed)

---

### 8. **nginx.docker.conf** - MISSING ⚠️

#### CURRENT Frontend:
- ✅ Has `nginx.docker.conf` for Docker deployment
- ✅ Configured for `/tprm/` base path
- ✅ API proxy to `grc_tprm:8000`

#### NEW Frontend:
- ❌ No `nginx.docker.conf` found

**Impact:**
- ❌ Docker deployment won't work
- ❌ Nginx configuration missing

**Fix Required:** Copy `nginx.docker.conf` from CURRENT frontend

---

### 9. **main.js** - IDENTICAL ✅

Both frontends have identical `main.js` files (except CURRENT has `authDebug` import which is minor).

**Status:** ✅ No changes needed

---

### 10. **nginx.conf** - IDENTICAL ✅

Both frontends have identical `nginx.conf` files.

**Status:** ✅ No changes needed

---

## 📊 Summary Statistics

| Category | CURRENT | NEW | Status |
|----------|---------|-----|--------|
| **Production Base Path** | ✅ Configured | ❌ Missing | **CRITICAL** |
| **Production API URLs** | ✅ Configured | ❌ Missing | **CRITICAL** |
| **Router Base Path** | ✅ Configured | ❌ Missing | **CRITICAL** |
| **Environment Variables** | ✅ Supported | ❌ Missing | **CRITICAL** |
| **backendEnv.js Utility** | ✅ Production-ready | ❌ Localhost-only | **CRITICAL** |
| **Dockerfile** | ✅ Present | ❌ Missing | **HIGH** |
| **nginx.docker.conf** | ✅ Present | ❌ Missing | **HIGH** |
| **package.json Scripts** | ✅ Complete | ⚠️ Missing 2 | **LOW** |
| **Dependencies** | ✅ Complete | ⚠️ Missing 1 | **LOW** |

---

## 🚨 Critical Issues to Fix

### Priority 1: CRITICAL (Must Fix)
1. ✅ Add production base path to `vite.config.js`
2. ✅ Add router base path to `src/router/index.js`
3. ✅ Update `src/config/api.js` with environment variables
4. ✅ Update `src/services/api.js` to use `backendEnv.js`
5. ✅ Fix `src/utils/backendEnv.js` to default to production URLs

### Priority 2: HIGH (Should Fix)
6. ✅ Copy `Dockerfile` from CURRENT frontend
7. ✅ Copy `nginx.docker.conf` from CURRENT frontend

### Priority 3: LOW (Optional)
8. ⚠️ Add cleanup scripts to `package.json`
9. ⚠️ Add `"frontend": "file:.."` dependency (if needed)

---

## 📝 Files That Need Modification

1. **frontend/vite.config.js** - Add base path
2. **frontend/src/router/index.js** - Add router base path
3. **frontend/src/config/api.js** - Add environment variable support
4. **frontend/src/services/api.js** - Use backendEnv utility
5. **frontend/src/utils/backendEnv.js** - Fix production defaults
6. **frontend/package.json** - Add missing scripts (optional)
7. **frontend/Dockerfile** - Copy from CURRENT (if needed)
8. **frontend/nginx.docker.conf** - Copy from CURRENT (if needed)

---

## 🔧 Additional Files to Check

The grep results show that many other files in NEW frontend have hardcoded `localhost:8000` URLs. These will also need to be updated:

- `src/views/rfp/*.vue` - Multiple files with hardcoded URLs
- `src/views/rfp-approval/*.vue` - Multiple files with hardcoded URLs
- `src/services/*.js` - Multiple service files with hardcoded URLs
- `src/stores/*.js` - Store files with hardcoded URLs
- `src/utils/*.js` - Utility files with hardcoded URLs

**Estimated Files to Update:** 50+ files

---

## ✅ Next Steps

1. **Immediate:** Fix critical configuration files (vite.config.js, router, api.js)
2. **High Priority:** Update backendEnv.js utility
3. **High Priority:** Update all service files to use environment variables
4. **Medium Priority:** Copy Docker deployment files
5. **Low Priority:** Add optional package.json scripts

---

**END OF ANALYSIS REPORT**





