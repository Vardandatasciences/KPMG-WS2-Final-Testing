# 🚨 CRITICAL: Deployment Fix for CORS Errors

## Problem
The TPRM iframe was loading from `localhost:3000` even after deployment, causing CORS errors.

## ✅ What Was Fixed

### 1. TprmWrapper.vue
- **Changed**: Now defaults to production URL (`https://grc-tprm.vardaands.com`) unless explicitly in development
- **Logic**: 
  - If `NODE_ENV === 'production'` → Always use production
  - If accessing from `vardaands.com` domain → Use production
  - Only uses `localhost:3000` if `NODE_ENV === 'development'` AND on localhost

### 2. API Service Files
- All hardcoded `localhost` URLs removed
- All API calls now use `getTprmApiBaseUrl()` which defaults to production

## 📋 Deployment Checklist

### Step 1: Build the GRC Frontend
```bash
cd grc_frontend
npm run build
```

### Step 2: Build the TPRM Frontend  
```bash
cd grc_frontend/tprm_frontend
npm run build
```

### Step 3: Verify Build Output
- Check `grc_frontend/dist/` exists (GRC build)
- Check `grc_frontend/tprm_frontend/dist/` exists (TPRM build)

### Step 4: Set Environment Variable (Optional but Recommended)
Create `.env.production` in `grc_frontend/`:
```
VUE_APP_TPRM_BASE_URL=https://grc-tprm.vardaands.com
```

### Step 5: Deploy
- Deploy GRC frontend to your web server
- Deploy TPRM frontend to `https://grc-tprm.vardaands.com` (or your TPRM domain)

### Step 6: Verify After Deployment
1. Open browser console
2. Navigate to `/tprm/rfp-dashboard`
3. Check console logs:
   - Should see: `[TprmWrapper] Initialized with BASE_URL: https://grc-tprm.vardaands.com`
   - Should NOT see: `http://localhost:3000`
4. Check Network tab:
   - All API calls should go to `https://grc-tprm.vardaands.com/api/tprm`
   - No CORS errors

## 🔍 Troubleshooting

### Still seeing localhost:3000?
1. **Clear browser cache** - Old JavaScript might be cached
2. **Hard refresh** - Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
3. **Check build output** - Make sure you deployed the NEW build
4. **Check NODE_ENV** - Ensure `NODE_ENV=production` during build

### Still getting CORS errors?
1. **Check backend CORS settings** - Backend must allow requests from `https://grc-tprm.vardaands.com`
2. **Check iframe src** - Should be `https://grc-tprm.vardaands.com/rfp-dashboard` not localhost
3. **Check API calls** - All should go to `https://grc-tprm.vardaands.com/api/tprm`

## ⚠️ Important Notes

- **Default is now PRODUCTION** - The code defaults to production URLs to prevent CORS issues
- **Development requires explicit setup** - Only uses localhost if `NODE_ENV=development` AND on localhost
- **Environment variables override** - `VUE_APP_TPRM_BASE_URL` takes highest priority

## 🎯 Quick Test

After deployment, run this in browser console:
```javascript
// Should return production URL
console.log('TPRM Base URL:', document.querySelector('iframe[title="TPRM Module"]')?.src)

// Should NOT contain localhost
console.log('Contains localhost?', document.querySelector('iframe[title="TPRM Module"]')?.src.includes('localhost'))
```

If the iframe src contains `localhost`, the build wasn't done correctly or old files are cached.








