# Vendor External Screening URL Fix

## Problem
The Vendor External Screening page was getting a **404 Not Found** error when trying to fetch vendors. The error showed:
```
Failed to load resource: the server responded with a status of 404 (Not Found)
http://127.0.0.1:8000/api/tprm/v1/vendor-core/temp-vendors/
```

## Root Cause
**URL Mismatch**: The frontend was using `getTprmApiUrl()` which generates URLs with `/api/tprm/v1/` prefix, but the backend is configured at `/api/v1/vendor-core/` (without the `/tprm` prefix).

### Backend URL Configuration
From `tprm_project/urls.py`:
```python
path('api/v1/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),
```

So the correct endpoint is: `/api/v1/vendor-core/temp-vendors/`

### Frontend Was Using
- `getTprmApiUrl('v1/vendor-core/temp-vendors/')` 
- Which generates: `/api/tprm/v1/vendor-core/temp-vendors/` ❌

### Should Use
- `getApiV1Url('vendor-core/temp-vendors/')`
- Which generates: `/api/v1/vendor-core/temp-vendors/` ✅

## Fix Applied

Changed all API calls in `VendorExternalScreening.vue` from:
- `getTprmApiUrl('v1/vendor-core/...')` 
- To: `getApiV1Url('vendor-core/...')`

### Files Changed
1. **VendorExternalScreening.vue** - Updated 6 API endpoint calls:
   - `fetchVendors()` - Line 481
   - `onVendorChange()` - Line 652
   - `updateMatchStatus()` - Line 855
   - `markAsCleared()` - Line 931
   - `addNote()` - Line 958

## Testing

After the fix, reload the page and check:

1. **Browser Console** should show:
   ```
   🔍 Fetching vendors from: http://127.0.0.1:8000/api/v1/vendor-core/temp-vendors/
   ✅ Successfully loaded X vendors
   ```

2. **Network Tab** should show:
   - Request URL: `http://127.0.0.1:8000/api/v1/vendor-core/temp-vendors/`
   - Status: `200 OK` (not 404)

3. **Vendor Dropdown** should populate with vendors

## Summary

| Before | After |
|--------|-------|
| `/api/tprm/v1/vendor-core/temp-vendors/` ❌ | `/api/v1/vendor-core/temp-vendors/` ✅ |
| `getTprmApiUrl('v1/vendor-core/...')` | `getApiV1Url('vendor-core/...')` |

The fix ensures all API calls match the backend URL configuration.


