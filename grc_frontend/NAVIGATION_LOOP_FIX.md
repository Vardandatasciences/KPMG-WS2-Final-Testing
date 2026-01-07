# 🔄 Navigation Loop Fix - Multiple Home Pages Issue

## Problem
When clicking TPRM module pages, multiple home pages were loading due to a navigation redirect loop:
1. User clicks TPRM link → navigates to `/tprm/vendor-dashboard`
2. TPRM iframe loads and sends navigation message
3. Something triggers navigation to `/vendor-dashboard` (without `/tprm` prefix)
4. Catch-all route catches `/vendor-dashboard` → redirects to `/tprm/vendor-dashboard`
5. This causes TPRM wrapper to reload → creates multiple instances

## ✅ Fixes Applied

### 1. Router Catch-All Route (`grc_frontend/src/router/index.js`)
- **Added check**: If already on `/tprm/*` route, don't redirect (return false)
- **Prevents loop**: TPRM routes won't trigger catch-all redirects anymore
- **TPRM pattern detection**: Routes like `/vendor-*`, `/rfp-*` redirect to `/tprm/{path}` only once

### 2. TPRM Wrapper Navigation Sync (`grc_frontend/src/views/TprmWrapper.vue`)
- **Changed `router.push` to `router.replace`**: Prevents adding to history stack
- **Reduces navigation loops**: Using `replace` doesn't create new history entries
- **Better error handling**: Ignores navigation duplicates and already-navigating errors

### 3. Iframe Sandbox Attributes
- **Added sandbox attribute**: `allow-same-origin allow-scripts allow-forms allow-popups allow-modals`
- **Security**: Prevents iframe from navigating parent window directly

## How It Works Now

```
User clicks TPRM link
    ↓
Navigates to /tprm/vendor-dashboard
    ↓
TPRM wrapper loads iframe
    ↓
TPRM router navigates internally to /vendor-dashboard
    ↓
TPRM sends navigation message to parent
    ↓
Parent router updates to /tprm/vendor-dashboard (using replace, not push)
    ↓
✅ No redirect loop - stays on TPRM page
```

## Testing

After rebuilding, verify:
1. ✅ Click TPRM module links - should navigate correctly
2. ✅ No multiple home pages loading
3. ✅ URL stays as `/tprm/{page}` 
4. ✅ No redirect loops in console
5. ✅ Page loads once, not multiple times

## Rebuild Required

```bash
cd grc_frontend
npm run build:all
```

Then redeploy the new build files.








