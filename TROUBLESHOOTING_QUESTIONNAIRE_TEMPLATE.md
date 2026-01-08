# Questionnaire Template 403/500 Error - Complete Fix

## Problem Summary
- Original Issue: 403 Forbidden when saving questionnaire templates
- Root Cause: Wrong API URL (missing `/api/tprm/` prefix) + Missing CSRF exemption
- Current Issue: Module loading errors preventing frontend from working

## All Changes Made

### 1. Backend - CSRF Exemption ✅
**File:** `grc_backend/tprm_backend/bcpdrp/views.py` (line ~3728)
```python
@csrf_exempt  # Added this
@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_bcp_drp_required('create_questionnaire')
@require_tenant
@tenant_filter
def questionnaire_template_save_view(request):
```

### 2. Frontend - API URL Fix ✅
**File:** `grc_frontend/tprm_frontend/src/services/api_bcp.js`
```javascript
// Changed from: '/bcpdrp/questionnaire-templates/save/'
// Changed to:   'bcpdrp/questionnaire-templates/save/'
// (Removed leading slash so axios uses baseURL)

questionnaireTemplates: {
  list: (params) => http.get('bcpdrp/questionnaire-templates/', { params }),
  get: (id) => http.get(`bcpdrp/questionnaire-templates/${id}/`),
  save: (data) => http.post('bcpdrp/questionnaire-templates/save/', data),
},
```

### 3. JWT - Tenant ID ✅
**File:** `grc_backend/tprm_backend/mfa_auth/jwt_service.py`
- JWT tokens now include `tenant_id` and `tenant_name` in payload

## Complete Solution to Module Errors

### Step 1: Hard Refresh Browser Cache
1. Open Chrome/Edge DevTools (F12)
2. Right-click the refresh button
3. Select **"Empty Cache and Hard Reload"**
4. OR clear cache manually:
   - Press Ctrl+Shift+Delete
   - Select "Cached images and files"
   - Click "Clear data"

### Step 2: Clear Frontend Build Cache (If Still Not Working)
```bash
cd C:\Users\Admin\Desktop\GRC_KPMG\GRC_TPRM_0801\GRC_TPRM\grc_frontend\tprm_frontend

# Stop the dev server first (Ctrl+C)

# Clear node_modules/.vite cache
Remove-Item -Recurse -Force node_modules\.vite -ErrorAction SilentlyContinue

# Restart dev server
npm run dev
```

### Step 3: Verify in Browser Network Tab
1. Open DevTools (F12) → Network tab
2. Clear network log (trash icon)
3. Try saving questionnaire template
4. Look for POST request

**Expected URL:**
```
http://localhost:8000/api/tprm/bcpdrp/questionnaire-templates/save/
```

**Expected Result:**
- Status: 201 Created
- Response: Template saved successfully

### Step 4: Check Backend Logs
After trying to save, check the Django server terminal for:
```
[BCP JWT Auth] Path: /api/tprm/bcpdrp/questionnaire-templates/save/
[Questionnaire Template Save] Request received from user: 2
✅ [Date/Time] POST /api/tprm/bcpdrp/questionnaire-templates/save/ - 201
```

## If Still Getting Errors

### 500 Internal Server Error
- Check backend terminal for stack trace
- Look for Python exceptions
- Share the error message

### 403 Forbidden
- Verify user has `create_questionnaire_for_testing` permission
- Check if RBAC record exists for user_id=2

### 404 Not Found
- Verify the URL in Network tab matches:
  `http://localhost:8000/api/tprm/bcpdrp/questionnaire-templates/save/`
- If different, share the actual URL being called

## Debugging Checklist

- [ ] Backend Django server is running
- [ ] Frontend Vue dev server is running  
- [ ] Browser cache cleared (Ctrl+Shift+R)
- [ ] No console errors in browser
- [ ] JWT token exists in localStorage (key: `session_token`)
- [ ] Network tab shows correct URL
- [ ] User has correct RBAC permissions

## Test the Fix

1. Navigate to: http://localhost:3000/contracts/create
2. Add a contract term
3. Click "Edit Questionnaires"
4. Add questions
5. Click "Save"
6. Expected: ✅ Success message!

## Contact Points for Support

If the issue persists, provide:
1. Screenshot of browser Network tab (showing the POST request)
2. Screenshot of backend terminal (Django logs)
3. Screenshot of browser Console tab (any errors)
4. The exact error message shown to the user

