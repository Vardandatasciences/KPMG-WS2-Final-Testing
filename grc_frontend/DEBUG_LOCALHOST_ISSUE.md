# 🔍 Debug Guide: Why is localhost:3000 Still Showing?

## Quick Check in Browser Console

After deploying, open browser console and look for this log block:

```
[TprmWrapper] ========== DEBUG INFO ==========
[TprmWrapper] BASE_URL: <-- CHECK THIS VALUE
[TprmWrapper] NODE_ENV: <-- Should be 'production' in production build
[TprmWrapper] VUE_APP_TPRM_BASE_URL: <-- Should be set or undefined
[TprmWrapper] window.location.hostname: <-- Where you're accessing from
[TprmWrapper] window.location.href: <-- Full URL
[TprmWrapper] =================================
```

## What Each Value Means

### If BASE_URL is `http://localhost:3000`:

**Check 1: NODE_ENV**
- If `NODE_ENV: 'development'` → Build wasn't done for production
- **Fix**: Run `npm run build` (not `npm run serve`)

**Check 2: window.location.hostname**
- If `hostname: 'localhost'` → You're accessing from localhost
- **Fix**: The code should still use production if NODE_ENV is production
- If it's still using localhost, there's a bug in the logic

**Check 3: VUE_APP_TPRM_BASE_URL**
- If this is set to `http://localhost:3000` → Environment variable is wrong
- **Fix**: Set `VUE_APP_TPRM_BASE_URL=https://grc-tprm.vardaands.com` in `.env.production`

## Common Issues

### Issue 1: Old Build Deployed
**Symptom**: Console shows old BASE_URL even after code changes
**Fix**: 
1. Delete `dist/` folder
2. Run `npm run build` again
3. Deploy the NEW `dist/` folder
4. Clear browser cache (Ctrl+Shift+R)

### Issue 2: Development Server Running
**Symptom**: `NODE_ENV: 'development'` in console
**Fix**: 
- Make sure you're running `npm run build` not `npm run serve`
- Check your build script in `package.json`

### Issue 3: Environment Variable Set Wrong
**Symptom**: `VUE_APP_TPRM_BASE_URL: 'http://localhost:3000'`
**Fix**:
1. Check `.env.production` file
2. Should be: `VUE_APP_TPRM_BASE_URL=https://grc-tprm.vardaands.com`
3. Or delete the variable to use auto-detection

### Issue 4: Browser Cache
**Symptom**: Old JavaScript file still loading
**Fix**:
1. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Or clear browser cache completely
3. Or use incognito/private window

## Expected Values in Production

After a correct build and deployment:

```
[TprmWrapper] BASE_URL: https://grc-tprm.vardaands.com ✅
[TprmWrapper] NODE_ENV: production ✅
[TprmWrapper] VUE_APP_TPRM_BASE_URL: undefined (or https://grc-tprm.vardaands.com) ✅
[TprmWrapper] window.location.hostname: <your-domain> (not localhost) ✅
```

## Manual Override (Temporary Fix)

If you need to force production URL immediately, add this to `TprmWrapper.vue`:

```javascript
// FORCE PRODUCTION - TEMPORARY FIX
const BASE_URL = 'https://grc-tprm.vardaands.com'
```

Then rebuild and redeploy.

## Build Command Checklist

```bash
# 1. Clean old build
cd grc_frontend
rm -rf dist  # or delete dist folder manually

# 2. Build for production
npm run build

# 3. Verify build output
ls -la dist/  # Should see built files

# 4. Check one of the JS files (optional)
# Search for "localhost:3000" - should NOT find it
grep -r "localhost:3000" dist/ || echo "✅ No localhost found"

# 5. Deploy dist/ folder to server
```

## Still Not Working?

1. **Check the actual JavaScript file**:
   - Open `dist/js/app.*.js` in a text editor
   - Search for "localhost:3000"
   - If found, the build is using old code

2. **Check build process**:
   - Make sure `NODE_ENV=production` during build
   - Vue CLI should set this automatically with `npm run build`

3. **Check deployment**:
   - Make sure you're deploying the NEW `dist/` folder
   - Not the old one from previous deployment

4. **Check server configuration**:
   - Make sure server is serving the new files
   - Not caching old JavaScript files








