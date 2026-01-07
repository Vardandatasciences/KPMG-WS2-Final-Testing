# 🔧 Development Server Fix - Conditional Base Path

## Problem
After adding `base: '/tprm/'` to Vite config, the development server was broken with error:
```
a public base URL of /tprm/ - did you mean to visit /tprm/rfp-dashboard instead?
```

## Root Cause
The `base: '/tprm/'` configuration was applied to both development and production, but:
- **Development**: Vite dev server runs on `http://localhost:3000` without base path
- **Production**: Built app is served from `/tprm/` subdirectory

## ✅ Fix Applied

### vite.config.js - Conditional Base Path
**Changed**: Made base path conditional based on `NODE_ENV`

**Before**:
```javascript
base: '/tprm/', // ❌ Applied to both dev and production
```

**After**:
```javascript
base: process.env.NODE_ENV === 'production' ? '/tprm/' : '/',
// ✅ Only use /tprm/ in production builds
// ✅ Use / (root) in development
```

## How It Works Now

### Development Mode
- Vite dev server: `http://localhost:3000` (no base path)
- TprmWrapper loads iframe from: `http://localhost:3000/vendor-dashboard`
- ✅ Works correctly

### Production Mode
- Built app served from: `/tprm/` subdirectory
- TprmWrapper loads iframe from: `https://grc-tprm.vardaands.com/tprm/vendor-dashboard`
- ✅ Works correctly

## Testing

### Local Development
1. Start TPRM dev server: `cd grc_frontend/tprm_frontend && npm run dev`
2. Start GRC dev server (in separate terminal)
3. Navigate to TPRM pages in GRC
4. ✅ Should load from `http://localhost:3000/vendor-dashboard`

### Production Build
1. Build TPRM: `cd grc_frontend/tprm_frontend && npm run build`
2. Deploy to `/tprm/` subdirectory
3. ✅ Assets and routing work correctly with `/tprm/` base path

## No Rebuild Needed
Since this only affects the build configuration, you only need to:
- **Restart the dev server** (if it's running) - no rebuild needed for development
- **Rebuild for production** when deploying







