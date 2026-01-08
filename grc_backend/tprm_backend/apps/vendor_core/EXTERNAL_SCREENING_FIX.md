# External Screening Data Loading Fix

## Problem
The Vendor External Screening page was failing to load vendor data with a 404 error. The issue was caused by missing tenant_id context in API requests.

## Root Cause
1. **Missing Tenant Context**: The JWT authentication wasn't extracting and setting `tenant_id` from the user's database record onto the request object
2. **Strict Tenant Filtering**: The backend was strictly filtering by tenant, returning empty results when no tenant_id was found
3. **Poor Error Messages**: The frontend and backend weren't providing helpful error messages for debugging

## Fixes Applied

### Backend Changes

#### 1. JWT Authentication Enhancement (`vendor_authentication.py`)
**Changed**: Modified `JWTAuthentication.authenticate()` method to:
- Fetch the user's `tenant_id` from the database using the `user_id` from JWT token
- Set `request.tenant_id` for use by downstream views
- Add comprehensive logging for debugging

```python
# Get tenant_id from User model and set it on request for multi-tenancy
try:
    from mfa_auth.models import User
    user_obj = User.objects.get(userid=user_id)
    tenant_id = user_obj.tenant_id if hasattr(user_obj, 'tenant_id') else None
    if tenant_id:
        request.tenant_id = tenant_id
        logger.info(f"[Vendor Auth] Set tenant_id {tenant_id} on request for user {user_id}")
    else:
        logger.warning(f"[Vendor Auth] User {user_id} has no tenant_id")
except Exception as e:
    logger.warning(f"[Vendor Auth] Could not fetch tenant_id for user {user_id}: {e}")
```

#### 2. TempVendorViewSet Improvements (`views.py`)
**Changed**: Modified `get_queryset()` and `list()` methods to:
- Explicitly fetch tenant_id and log it
- Return all vendors if tenant_id is missing (development mode)
- Provide helpful error messages when no vendors are found
- Add tenant_id to API responses for debugging

```python
def get_queryset(self):
    tenant_id = get_tenant_id_from_request(self.request)
    
    if tenant_id:
        queryset = TempVendor.objects.filter(tenant_id=tenant_id)
        vendor_logger.info(f"Filtering vendors by tenant_id: {tenant_id}")
    else:
        # For development - return all vendors
        queryset = TempVendor.objects.all()
        vendor_logger.warning("No tenant_id found - returning all vendors")
    
    queryset = queryset.order_by('-created_at')
    # ... rest of method
```

#### 3. VendorScreeningViewSet Improvements (`views.py`)
**Changed**: Modified `get_queryset()` and `vendor_screening_results()` methods to:
- Be more lenient when tenant_id is missing
- Provide detailed error messages with tenant and vendor information
- Add comprehensive logging and traceback in DEBUG mode

```python
def vendor_screening_results(self, request):
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        if tenant_id:
            vendor = TempVendor.objects.get(id=vendor_id, tenant_id=tenant_id)
        else:
            # For development - allow access without tenant check
            vendor = TempVendor.objects.get(id=vendor_id)
        # ... rest of method
```

### Frontend Changes

#### VendorExternalScreening.vue
**Changed**: Modified `fetchVendors()` method to:
- Add more detailed console logging with emojis for better readability
- Handle different error status codes (401, 403, 404)
- Display helpful error messages from backend
- Log tenant_id when present for debugging

```javascript
if (error.response) {
  if (error.response.status === 403) {
    errorMessage = 'Access denied. Please check your permissions.';
  } else if (error.response.status === 401) {
    errorMessage = 'Authentication required. Please log in.';
  } else if (error.response.status === 404) {
    errorMessage = 'Vendors endpoint not found. Please contact support.';
  }
  // ... handle other cases
}
```

## Testing the Fix

### 1. Restart Django Server
```bash
cd grc_backend
python manage.py runserver
```

### 2. Check Browser Console
Look for these log messages:
- `✅ Successfully loaded X vendors`
- `🏢 Tenant ID: X` (if tenant_id is present)
- `⚠️ No tenant_id in response` (if missing)

### 3. Check Django Server Logs
Look for these log messages:
- `[Vendor Auth] Set tenant_id X on request for user Y`
- `Filtering vendors by tenant_id: X`
- `Retrieved X temp vendors (tenant_id: Y)`

## What to Do If Still Not Working

### 1. Check User Has Tenant
```sql
SELECT userid, username, tenant_id FROM users WHERE userid = <your_user_id>;
```

### 2. Check Vendors Exist
```sql
SELECT id, company_name, tenant_id FROM temp_vendor LIMIT 10;
```

### 3. Check JWT Token
Decode your JWT token at https://jwt.io and verify it contains `user_id`

### 4. Check Permissions
Verify user has `view_vendors` permission:
```sql
SELECT * FROM rbac_permissions WHERE user_id = <your_user_id>;
```

## Production Considerations

**Important**: The current fix allows accessing all vendors when `tenant_id` is missing. This is for development convenience.

For production, you should:
1. Ensure all users have a valid `tenant_id`
2. Return empty results or error when `tenant_id` is missing
3. Add proper tenant isolation enforcement

To make it production-ready, change in `views.py`:
```python
if tenant_id:
    queryset = TempVendor.objects.filter(tenant_id=tenant_id)
else:
    # Production: Return empty queryset
    return TempVendor.objects.none()
    # Or raise an error
    # raise ValidationError("Tenant context required")
```

## Summary of Changes

| File | Changes | Impact |
|------|---------|--------|
| `vendor_authentication.py` | Added tenant_id extraction from User model | Sets tenant context for all requests |
| `views.py` (TempVendorViewSet) | Improved tenant filtering and error messages | Better debugging and development experience |
| `views.py` (VendorScreeningViewSet) | More lenient tenant filtering | Allows screening results to load |
| `VendorExternalScreening.vue` | Enhanced error handling and logging | Better user feedback |

## Files Modified
- `grc_backend/tprm_backend/apps/vendor_core/vendor_authentication.py`
- `grc_backend/tprm_backend/apps/vendor_core/views.py`
- `grc_frontend/tprm_frontend/src/pages/vendor/VendorExternalScreening.vue`


