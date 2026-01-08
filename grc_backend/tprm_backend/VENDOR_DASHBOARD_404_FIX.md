# Vendor Dashboard 404 Error Fix

## Problem
All vendor dashboard API endpoints were returning **404 Not Found** errors:
- `/api/tprm/v1/vendor-dashboard/screening-match-rate/`
- `/api/tprm/v1/vendor-dashboard/questionnaire-overdue-rate/`
- `/api/tprm/v1/vendor-dashboard/vendors-flagged-ofac-pep/`
- `/api/tprm/v1/vendor-dashboard/vendor-acceptance-time/`
- `/api/tprm/v1/vendor-dashboard/vendor-registration-completion-rate/`
- `/api/tprm/v1/vendor-dashboard/vendor-registration-time/`
- `/api/tprm/v1/vendor-dashboard/alerts/`
- `/api/tprm/v1/vendor-dashboard/kpi-categories/`

## Root Cause
There was a **mismatch between the app name in `settings.py` and `apps.py`**:

### In `vendor_guard_hub/settings.py` (BEFORE FIX):
```python
VENDOR_APPS = [
    'apps.vendor_core',      # ← Short path
    'apps.vendor_auth',      # ← Short path
    'apps.vendor_risk',      # ← Short path
    'apps.vendor_questionnaire',  # ← Short path
    'apps.vendor_dashboard',  # ← Short path (doesn't match apps.py)
    'apps.vendor_lifecycle',  # ← Short path
    'apps.vendor_approval',   # ← Short path
    'risk_analysis_vendor',
]
```

### In `apps/vendor_dashboard/apps.py`:
```python
class VendorDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.apps.vendor_dashboard'  # ← Full path (doesn't match settings)
    verbose_name = 'Vendor Dashboard'
```

**The Problem:** Django couldn't import `apps.vendor_dashboard` because Python can't find `apps` as a top-level module. The `name` in `apps.py` must match what's in `INSTALLED_APPS`.

## Solution Applied

### 1. Fixed `vendor_guard_hub/settings.py`:
Changed all vendor apps in `INSTALLED_APPS` to use full paths to match their `apps.py` configurations:

```python
VENDOR_APPS = [
    'tprm_backend.apps.vendor_core',      # ✅ Full path
    'tprm_backend.apps.vendor_auth',      # ✅ Full path
    'tprm_backend.apps.vendor_risk',      # ✅ Full path
    'tprm_backend.apps.vendor_questionnaire',  # ✅ Full path
    'tprm_backend.apps.vendor_dashboard',  # ✅ Full path (now matches apps.py)
    'tprm_backend.apps.vendor_lifecycle',  # ✅ Full path
    'tprm_backend.apps.vendor_approval',   # ✅ Full path
    'risk_analysis_vendor',
]
```

### 2. Verified `apps/vendor_dashboard/apps.py`:
Confirmed it uses the full path (already correct):

```python
class VendorDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tprm_backend.apps.vendor_dashboard'  # ✅ Matches settings.py now
    verbose_name = 'Vendor Dashboard'
```

## Files Modified
1. ✅ `grc_backend/tprm_backend/vendor_guard_hub/settings.py` - Updated `VENDOR_APPS` to use full paths

## Next Steps - RESTART REQUIRED

**⚠️ IMPORTANT: You MUST restart the Django development server for these changes to take effect!**

### How to Restart:
1. **Stop the current server** (Press `Ctrl+C` in the terminal running the server)
2. **Clear Python cache** (optional but recommended):
   ```powershell
   Get-ChildItem -Path "grc_backend\tprm_backend" -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force
   ```
3. **Start the server again**:
   ```powershell
   cd grc_backend\tprm_backend
   python manage.py runserver
   ```

### Verification
After restarting, the following endpoints should work:
- ✅ `http://localhost:8000/api/tprm/v1/vendor-dashboard/screening-match-rate/`
- ✅ `http://localhost:8000/api/tprm/v1/vendor-dashboard/questionnaire-overdue-rate/`
- ✅ `http://localhost:8000/api/tprm/v1/vendor-dashboard/vendors-flagged-ofac-pep/`
- ✅ `http://localhost:8000/api/tprm/v1/vendor-dashboard/vendor-acceptance-time/`
- ✅ `http://localhost:8000/api/tprm/v1/vendor-dashboard/vendor-registration-completion-rate/`
- ✅ `http://localhost:8000/api/tprm/v1/vendor-dashboard/vendor-registration-time/`
- ✅ `http://localhost:8000/api/tprm/v1/vendor-dashboard/alerts/`
- ✅ `http://localhost:8000/api/tprm/v1/vendor-dashboard/kpi-categories/`

## Technical Details

### URL Routing Flow:
1. Request: `/api/tprm/v1/vendor-dashboard/screening-match-rate/`
2. Main URLs (`vendor_guard_hub/urls.py`):
   ```python
   path('api/tprm/v1/vendor-dashboard/', include('apps.vendor_dashboard.urls')),
   ```
3. App URLs (`apps/vendor_dashboard/urls.py`):
   ```python
   path('screening-match-rate/', ScreeningMatchRateAPIView.as_view(), name='screening-match-rate'),
   ```
4. View: `ScreeningMatchRateAPIView` in `apps/vendor_dashboard/views.py`

### Why This Caused 404:
Django couldn't properly load the `apps.vendor_dashboard` app because:
- Settings registered it as `'apps.vendor_dashboard'` (short path)
- But `apps.py` declared it as `'tprm_backend.apps.vendor_dashboard'` (full path)
- When Django tried to import `apps.vendor_dashboard`, Python couldn't find the `apps` module
- This mismatch prevented Django from recognizing the app
- Therefore, the URL patterns from `apps/vendor_dashboard/urls.py` were never loaded
- Result: All requests to those endpoints returned 404

## Consistency Check
All vendor apps now use consistent full paths:
- ✅ `tprm_backend.apps.vendor_core` → `name = 'tprm_backend.apps.vendor_core'` ✅ **NOW CONSISTENT**
- ✅ `tprm_backend.apps.vendor_auth` → `name = 'tprm_backend.apps.vendor_auth'` ✅ **NOW CONSISTENT**
- ✅ `tprm_backend.apps.vendor_dashboard` → `name = 'tprm_backend.apps.vendor_dashboard'` ✅ **NOW FIXED & CONSISTENT**

## Status
- [x] Issue identified
- [x] Root cause found
- [x] Fix applied
- [ ] **Server restart required** ← **YOU NEED TO DO THIS**
- [ ] Verification pending

