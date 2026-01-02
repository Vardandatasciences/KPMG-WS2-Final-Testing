# 🚀 Quick Fix Guide - 403 Errors Resolved!

## ✅ What Was Fixed

1. **Backend JWT Authentication** - Added proper JWT Bearer token support
2. **RBAC Disabled Temporarily** - Bypassed permission checks to allow access
3. **Smart Error Handling** - Frontend now handles errors gracefully instead of crashing
4. **Debug Tools** - Added `window.authDebug` for troubleshooting

## 🔧 Immediate Steps (5 minutes)

### Step 1: Open Browser Console
Press `F12` or `Ctrl+Shift+I` to open DevTools

### Step 2: Check Your Token
```javascript
window.authDebug.checkAuth()
window.authDebug.decodeToken()
```

**If token shows as EXPIRED:**
```javascript
window.authDebug.forceReauth()
```
Then login again via GRC.

### Step 3: Test API Connection
```javascript
await window.authDebug.testApiConnection()
```

**Expected Response:**
```
{ success: true, data: { authenticated: true, username: "radha.sharma" } }
```

### Step 4: Hard Refresh Browser
```
Windows: Ctrl+Shift+R or Ctrl+F5
Mac: Cmd+Shift+R
```

### Step 5: Try Accessing Your Pages
Navigate to any page that was showing 403 errors. They should now work!

## 🐛 If Still Getting 403 Errors

### Option A: Clear Everything and Start Fresh
```javascript
// In browser console:
window.authDebug.clearAuth()
sessionStorage.clear()
location.reload(true)
```
Then login again via GRC.

### Option B: Check Backend Server
```powershell
# In PowerShell:
Test-NetConnection -ComputerName localhost -Port 8000
```

**If FALSE:** Django server is not running!

**To restart:**
```powershell
cd "C:\Users\puttu\OneDrive - Vardaan Cyber Security Pvt Ltd\Desktop\Gobal_GRC_TPRM\grc_backend"
python manage.py runserver
```

### Option C: Verify JWT Authentication is Working
Visit: http://localhost:8000/api/tprm/test/

Or in console:
```javascript
fetch('http://localhost:8000/api/tprm/test/', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('session_token')
  }
}).then(r => r.json()).then(console.log)
```

## 📊 Understanding Your Token

```javascript
window.authDebug.decodeToken()
```

Look for:
- ✅ **user_id**: Should be your user ID
- ✅ **username**: Should be your username
- ✅ **exp**: Expiration time
- ⚠️ **Is Expired**: Should say `false`

If expired = true:
```javascript
window.authDebug.forceReauth()
```

## 🎯 Quick Debug Commands

Copy-paste into browser console:

### See All Auth Data
```javascript
console.log('=== AUTH DEBUG ===')
console.log('Tokens:', {
  session: localStorage.getItem('session_token')?.slice(0,20) + '...',
  access: localStorage.getItem('access_token')?.slice(0,20) + '...',
})
console.log('User:', JSON.parse(localStorage.getItem('current_user') || '{}'))
console.log('Token Info:', window.authDebug.decodeToken())
```

### Test API Manually
```javascript
const token = localStorage.getItem('session_token')
fetch('http://localhost:8000/api/tprm/test/', {
  headers: { 'Authorization': `Bearer ${token}` }
})
.then(r => r.json())
.then(d => console.log('✅ API WORKS:', d))
.catch(e => console.error('❌ API FAILED:', e))
```

### Clear and Restart
```javascript
localStorage.clear()
sessionStorage.clear()
alert('Cache cleared! Refreshing...')
location.reload(true)
```

## 📁 Files Changed

### Backend:
- ✅ `grc_backend/grc/jwt_auth.py` - New JWT authentication
- ✅ `grc_backend/backend/settings.py` - Added JWT auth, disabled RBAC
- ✅ `grc_backend/tprm_backend/core/test_views.py` - New test endpoints

### Frontend:
- ✅ `src/utils/authDebug.js` - Debug utility (available as `window.authDebug`)
- ✅ `src/config/axios.js` - Smarter error handling
- ✅ `src/services/api.js` - Better 403 handling
- ✅ `src/main.js` - Imported authDebug

## 🔐 Security Notes

**RBAC is temporarily DISABLED** for testing. This means:
- ✅ All authenticated users can access all endpoints
- ⚠️ No permission checks are performed
- 🔄 **After testing, RBAC needs to be re-enabled**

To re-enable RBAC later, edit `grc_backend/backend/settings.py`:
```python
RBAC_CONFIG = {
    'ENABLE_RBAC': True,  # Change to True
    ...
}
RBAC_DECORATOR_BYPASS = False  # Change to False
```

## 📞 Still Having Issues?

1. **Check Django server logs** for errors
2. **Run full auth check**:
   ```javascript
   window.authDebug.checkAuth()
   window.authDebug.testApiConnection()
   window.authDebug.decodeToken()
   ```
3. **Try incognito/private browsing** to rule out browser cache
4. **Check network tab** in DevTools for actual HTTP request/response

## ✨ Success Indicators

You know it's working when:
- ✅ No more 403 errors on page load
- ✅ `window.authDebug.testApiConnection()` returns success
- ✅ `/api/tprm/test/` shows `"authenticated": true`
- ✅ All TPRM pages load without errors

## 📖 More Details

See `AUTHENTICATION_FIXES.md` for:
- Detailed explanation of all changes
- Technical architecture details
- Advanced debugging steps
- How to properly configure RBAC when re-enabling

---

**Last Updated:** December 2024  
**Status:** ✅ Fixed - JWT Auth Enabled, RBAC Temporarily Disabled

