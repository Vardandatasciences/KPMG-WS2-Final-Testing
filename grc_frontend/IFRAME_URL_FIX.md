# 🔧 Iframe URL Fix - Missing /tprm in URL

## Problem
The TPRM iframe was loading from `https://grc-tprm.vardaands.com/vendor-dashboard` instead of `https://grc-tprm.vardaands.com/tprm/vendor-dashboard`, causing:
- Home page loading inside iframe (wrong content)
- Navigation loops
- Multiple home pages rendering

## Root Cause
The `getTprmBaseUrl()` function was returning `https://grc-tprm.vardaands.com` (without `/tprm` prefix), so the iframe loaded from the wrong path.

## ✅ Fixes Applied

### 1. TprmWrapper.vue - Base URL Logic
**Changed**: `getTprmBaseUrl()` now returns `${origin}/tprm` instead of `https://grc-tprm.vardaands.com`

**Before**:
```javascript
return 'https://grc-tprm.vardaands.com'  // ❌ Missing /tprm
```

**After**:
```javascript
const tprmBaseUrl = `${origin}/tprm`  // ✅ Includes /tprm
return tprmBaseUrl
```

**Result**: Iframe now loads from `https://grc-tprm.vardaands.com/tprm/vendor-dashboard`

### 2. vite.config.js - Base Path Configuration
**Added**: `base: '/tprm/'` to Vite config

**Why**: Tells Vite that the app is deployed at `/tprm` subdirectory, so all asset paths and routing work correctly.

```javascript
export default defineConfig({
  base: '/tprm/', // ✅ Set base path for deployment as subdirectory
  // ...
})
```

## How It Works Now

```
User navigates to /tprm/vendor-dashboard
    ↓
TprmWrapper computes BASE_URL = window.location.origin + '/tprm'
    ↓
Iframe src = BASE_URL + '/vendor-dashboard'
    ↓
Iframe loads: https://grc-tprm.vardaands.com/tprm/vendor-dashboard ✅
    ↓
TPRM app loads correctly (not GRC home page)
```

## Deployment Requirements

1. **TPRM app must be deployed at `/tprm` subdirectory** of the GRC domain
2. **Nginx/server must serve TPRM files from `/tprm` path**
3. **Vite build with `base: '/tprm/'`** ensures all assets load correctly

## Testing

After rebuilding:
1. ✅ Iframe URL should include `/tprm`: `https://grc-tprm.vardaands.com/tprm/vendor-dashboard`
2. ✅ TPRM pages load correctly (not GRC home page)
3. ✅ No navigation loops
4. ✅ Single page load (no multiple instances)

## Rebuild Required

```bash
cd grc_frontend/tprm_frontend
npm run build
```

Then redeploy the TPRM build files to `/tprm` subdirectory.






