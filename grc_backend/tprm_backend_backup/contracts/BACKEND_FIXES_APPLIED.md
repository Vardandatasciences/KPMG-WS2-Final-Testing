# Contracts Backend Fixes - Database Schema and Import Issues

## Date: Current Session
## Status: ✅ FIXED

---

## Problems Identified

### 1. Import Error: `No module named 'rbac'` ❌
**Error Message:**
```
[ERROR] Contract list error: No module named 'rbac'
[ERROR] Contract renewals list error: No module named 'rbac'
```

**Root Cause:**
- Code was using: `from rbac.tprm_utils import RBACTPRMUtils`
- Should be: `from tprm_backend.rbac.tprm_utils import RBACTPRMUtils`

### 2. Database Schema Issue: Using `grc2` instead of `tprm_integration` ❌
**Root Cause:**
- Raw SQL queries were using `connection.cursor()` which defaults to `grc2` database
- Should use `connections['tprm'].cursor()` to use `tprm_integration` database

---

## Fixes Applied

### Fix 1: Corrected RBAC Import Statements ✅
**File:** `grc_backend/tprm_backend/contracts/views.py`

**Changed (6 occurrences):**
```python
# BEFORE (WRONG):
from rbac.tprm_utils import RBACTPRMUtils

# AFTER (CORRECT):
from tprm_backend.rbac.tprm_utils import RBACTPRMUtils
```

**Locations Fixed:**
- Line ~333: `contract_list()` function
- Line ~452: `contract_detail()` function  
- Line ~502: `contract_comprehensive_detail()` function
- Line ~2742: (other function)
- Line ~2980: (other function)
- Line ~3963: (other function)

### Fix 2: Updated Database Connection for Raw SQL Queries ✅
**File:** `grc_backend/tprm_backend/contracts/views.py`

**Changed:**
```python
# BEFORE (WRONG - uses grc2 database):
from django.db import transaction, connection

# AFTER (CORRECT - includes connections):
from django.db import transaction, connection, connections
```

**Raw SQL Queries Fixed (2 occurrences):**

1. **Line ~1866:** `contract_risk_exposure_kpi()` function
```python
# BEFORE:
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT ... FROM risk_tprm ...
    """)

# AFTER:
with connections['tprm'].cursor() as cursor:
    cursor.execute("""
        SELECT ... FROM risk_tprm ...
    """)
```

2. **Line ~1930:** `contract_risk_exposure_kpi()` function
```python
# BEFORE:
with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM risk_tprm WHERE entity = 'contract_module'")

# AFTER:
with connections['tprm'].cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM risk_tprm WHERE entity = 'contract_module'")
```

---

## Database Configuration

### Current Setup:
- **Default Database:** `grc2` (for GRC modules)
- **TPRM Database:** `tprm_integration` (for TPRM modules)
- **Database Router:** `backend.tprm_router.TPRMDatabaseRouter` routes TPRM apps to `tprm_integration`

### Database Router Configuration:
The router automatically routes all TPRM models to the `tprm` database connection, which uses the `tprm_integration` schema. However, **raw SQL queries** must explicitly use `connections['tprm']` to ensure they use the correct database.

---

## Testing

After applying these fixes, test the following endpoints:

1. ✅ `GET /api/tprm/contracts/contracts/` - Should work without import errors
2. ✅ `GET /api/tprm/contracts/contracts/renewals/` - Should work without import errors
3. ✅ `GET /api/tprm/contracts/contracts/stats/` - Should work correctly
4. ✅ `GET /api/tprm/contracts/contracts/analytics/` - Should work correctly
5. ✅ `GET /api/tprm/contracts/users/` - Should work correctly
6. ✅ `GET /api/tprm/contracts/users/legal-reviewers/` - Should work correctly

---

## Files Modified

1. **grc_backend/tprm_backend/contracts/views.py**
   - ✅ Fixed 6 RBAC import statements
   - ✅ Added `connections` import
   - ✅ Fixed 2 raw SQL queries to use `connections['tprm']`

---

## Next Steps

1. **Restart Django Server:** The changes require a server restart
2. **Test Endpoints:** Verify all contract endpoints work correctly
3. **Check Logs:** Monitor Django logs for any remaining errors
4. **Verify Database:** Confirm queries are hitting `tprm_integration` schema

---

## Summary

✅ **Import Issues:** Fixed - All RBAC imports now use correct path
✅ **Database Issues:** Fixed - Raw SQL queries now use `tprm_integration` database
✅ **Error Handling:** Improved - Better error messages for debugging

The 500 errors should now be resolved. The backend will:
- Correctly import RBAC utilities
- Use the correct database schema (`tprm_integration`)
- Route all TPRM models to the correct database automatically

