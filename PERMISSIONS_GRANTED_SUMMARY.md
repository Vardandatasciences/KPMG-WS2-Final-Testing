# BCP/DRP Questionnaire Permissions - Successfully Granted

## ✅ Permissions Granted Successfully

The following permissions have been granted to **User ID: 2 (vikram.patel, Relationship Manager)**:

### Granted Permissions:
- ✅ `create_questionnaire_for_testing` - **TRUE**
- ✅ `view_plans_and_documents` - **TRUE**
- ✅ `create_bcp_drp_strategy_and_plans` - **TRUE**
- ✅ `is_active` - **Y** (Active)

## 🔧 What Was Fixed

### 1. JWT Token includes tenant_id (Fixed Earlier)
**File**: `grc_backend/tprm_backend/mfa_auth/jwt_service.py`
- JWT tokens now include `tenant_id` in the payload
- This allows the TenantContextMiddleware to resolve the tenant correctly

### 2. RBAC Permissions Granted (Just Now)
**Database**: `rbac_tprm` table
- Added required BCP/DRP permissions for user 2
- User can now create questionnaire templates
- User has full access to BCP/DRP module

## 🧪 Testing Instructions

### Step 1: Refresh Your Browser
Since the JWT token already includes tenant_id (from earlier fix), you just need to:
1. **Refresh your browser** (F5 or Ctrl+R)
2. The permissions will take effect immediately

### Step 2: Try Creating Questionnaire Template
1. Navigate to Contract Creation page
2. Add a term (Payment, Liability, etc.)
3. Click "Create Questionnaires" for that term
4. You should be redirected to Questionnaire Templates page
5. Fill out the form:
   - Template Name: e.g., "Payment Term Questionnaire"
   - Module Type: CONTRACT
   - Add questions
6. Click "Save Template"
7. **Expected Result**: ✅ Success! Template saved successfully

### Step 3: Check Backend Logs
When you save the template, you should see these logs in the backend terminal:

```
[Tenant Middleware] ✅ Resolved tenant: Tenant 2 (ID: 2) for POST /bcpdrp/questionnaire-templates/save/
[RBAC TPRM DECORATOR] User 2 granted BCP/DRP access: create_questionnaire
[Questionnaire Template Save] Request received from user: 2
[Questionnaire Template Save] Request tenant_id: 2
```

## 📊 Verification

### Check Your Permissions in Database
Run this command to verify your permissions anytime:
```bash
cd grc_backend
python manage.py shell -c "from tprm_backend.rbac.models import RBACTPRM; rbac = RBACTPRM.objects.get(user_id=2); print(f'create_questionnaire_for_testing: {rbac.create_questionnaire_for_testing}')"
```

**Expected Output**: `create_questionnaire_for_testing: True`

### Check JWT Token Contains tenant_id
Open browser console and run:
```javascript
const token = localStorage.getItem('session_token')
const payload = JSON.parse(atob(token.split('.')[1]))
console.log('tenant_id:', payload.tenant_id)
console.log('user_id:', payload.user_id)
```

**Expected Output**:
```
tenant_id: 2
user_id: 2
```

## 🚨 If It Still Doesn't Work

### Issue: 403 Forbidden Error Persists
**Possible Causes**:
1. Browser cache not cleared
2. Old JWT token still in use
3. Different user logged in

**Solutions**:
1. **Hard refresh** the browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. **Clear browser cache** and cookies for localhost
3. **Log out and log back in** to get a fresh JWT token
4. Check the Network tab in browser DevTools to see the actual 403 response details

### Issue: Different User ID
If you're logged in as a different user (not user 2), grant permissions to that user:

```bash
cd grc_backend
python manage.py shell -c "from tprm_backend.rbac.models import RBACTPRM; user_id = YOUR_USER_ID; rbac, created = RBACTPRM.objects.get_or_create(user_id=user_id, defaults={'username': f'user_{user_id}', 'role': 'admin', 'is_active': 'Y'}); rbac.create_questionnaire_for_testing = True; rbac.view_plans_and_documents = True; rbac.save(); print(f'✅ Granted permissions to user {user_id}')"
```

Replace `YOUR_USER_ID` with the actual user ID from the frontend console.

### Issue: Module Not Found Errors
If you see "ModuleNotFoundError" in the backend:
1. Make sure you're in the `grc_backend` directory
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Restart the Django server

## 📝 Summary of All Fixes

### Fix #1: JWT Token includes tenant_id
- **File**: `grc_backend/tprm_backend/mfa_auth/jwt_service.py`
- **Change**: Added `tenant_id` to JWT token payload
- **Status**: ✅ Complete

### Fix #2: Enhanced Error Logging
- **File**: `grc_backend/tprm_backend/core/tenant_utils.py`
- **Change**: Better error messages for missing tenant
- **Status**: ✅ Complete

### Fix #3: Debug Logging in View
- **File**: `grc_backend/tprm_backend/bcpdrp/views.py`
- **Change**: Added debug logging to questionnaire_template_save_view
- **Status**: ✅ Complete

### Fix #4: RBAC Permissions Granted
- **Database**: `rbac_tprm` table, user_id=2
- **Change**: Granted create_questionnaire_for_testing permission
- **Status**: ✅ Complete (Just now)

### Fix #5: Term Lookup Error Fixed
- **File**: `grc_frontend/tprm_frontend/src/pages/contract/CreateContract.vue`
- **Change**: Better term validation and error handling
- **Status**: ✅ Complete

## 🎉 Expected Behavior After All Fixes

1. **Login**: User logs in → JWT token includes tenant_id ✅
2. **Tenant Resolution**: Middleware resolves tenant from JWT ✅
3. **Permission Check**: RBAC decorator checks and grants access ✅
4. **View Executes**: questionnaire_template_save_view runs ✅
5. **Success**: Template saved to database ✅

## 🔗 Related Documentation

- `QUESTIONNAIRE_TEMPLATE_403_FIX.md` - JWT token tenant_id fix
- `TERM_NOT_FOUND_FIX.md` - Term lookup error fix
- `RBAC_APPROACH.md` - RBAC system documentation

## 📞 Support

If you continue to have issues after following these steps:
1. Check all backend terminal logs
2. Check browser console logs
3. Verify JWT token payload has tenant_id
4. Verify user_id matches the user with permissions
5. Try logging out and logging back in

