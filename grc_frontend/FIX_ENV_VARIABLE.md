# 🔧 Fix: VUE_APP_TPRM_BASE_URL Set to Localhost

## Problem Found
Your console shows:
```
VUE_APP_TPRM_BASE_URL: http://localhost:3000
```

This environment variable is **hardcoded to localhost** and is overriding the production URL.

## ✅ Solution

### Option 1: Remove the Variable (Recommended)
The code now auto-detects production, so you don't need this variable.

**Find and delete this line from:**
- `.env` file
- `.env.production` file  
- `.env.local` file
- Any other `.env*` files in `grc_frontend/`

**Look for:**
```
VUE_APP_TPRM_BASE_URL=http://localhost:3000
```
or
```
VUE_APP_TPRM_BASE_URL=http://Localhost:3000
```

**Delete the entire line.**

### Option 2: Set to Production URL
If you want to keep the variable, change it to:

```
VUE_APP_TPRM_BASE_URL=https://grc-tprm.vardaands.com
```

## Where to Look

### Check These Files:
1. `grc_frontend/.env`
2. `grc_frontend/.env.production`
3. `grc_frontend/.env.local`
4. `grc_frontend/.env.development`
5. Server environment variables (if set on server)

### Quick Search Command:
```bash
cd grc_frontend
# Windows PowerShell
Get-ChildItem -Recurse -Filter ".env*" | Select-String "VUE_APP_TPRM_BASE_URL"

# Linux/Mac
grep -r "VUE_APP_TPRM_BASE_URL" .env* 2>/dev/null
```

## After Fixing

1. **Delete the old build:**
   ```bash
   cd grc_frontend
   rm -rf dist
   ```

2. **Rebuild:**
   ```bash
   npm run build
   ```

3. **Redeploy** the new `dist/` folder

4. **Clear browser cache** and check console again

## What Changed in Code

The code now **ignores localhost values** in `VUE_APP_TPRM_BASE_URL` when running on production domain. So even if the env var is set wrong, it will use production URL.

But it's still better to **remove or fix the env variable** to avoid confusion.

## Verification

After rebuilding and deploying, check console:
```
[TprmWrapper] BASE_URL: https://grc-tprm.vardaands.com ✅
```

Should NOT see:
```
[TprmWrapper] BASE_URL: http://localhost:3000 ❌
```








