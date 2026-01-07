# 🔧 CORS Fix - Added localhost:3000 Support

## Problem
TPRM iframe was loading from `http://localhost:3000` (correct for development), but the backend was blocking CORS requests from this origin, causing errors:
```
Access to fetch at 'https://grc-tprm.vardaands.com/api/tprm/...' from origin 'http://localhost:3000' has been blocked by CORS policy
```

## ✅ Fix Applied

### grc_backend/backend/settings.py

**Added `localhost:3000` to CORS_ALLOWED_ORIGINS**:
```python
CORS_ALLOWED_ORIGINS = [
    "https://grc-tprm.vardaands.com",
    "http://localhost:3000",  # ✅ TPRM frontend development server (ADDED)
    "http://localhost:8081",
    "http://localhost:8080",
    "http://127.0.0.1:3000",  # ✅ TPRM frontend development server (127.0.0.1) (ADDED)
    "http://127.0.0.1:8080",
    # ... rest of origins
]
```

**Added `localhost:3000` to CSRF_TRUSTED_ORIGINS**:
```python
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",  # ✅ TPRM frontend development server (ADDED)
    "http://localhost:8081",
    "http://localhost:8080",
    "http://127.0.0.1:3000",  # ✅ TPRM frontend development server (127.0.0.1) (ADDED)
    # ... rest of origins
]
```

## Why This Was Needed

1. **TPRM Dev Server**: Runs on `http://localhost:3000` (Vite dev server)
2. **API Calls**: TPRM frontend makes API calls to the backend
3. **CORS Policy**: Backend needs to explicitly allow requests from `localhost:3000`
4. **CSRF Protection**: Django CSRF middleware also needs to trust this origin

## Next Steps

**Restart the Django backend server** for the changes to take effect:

```bash
cd grc_backend
python manage.py runserver
```

After restarting, the CORS errors should be resolved and the TPRM iframe should work correctly in local development.

## Note

The TPRM backend (`grc_backend/tprm_backend/vendor_guard_hub/settings.py`) already has:
- `CORS_ALLOW_ALL_ORIGINS = True` (line 313) - allows all origins in development
- `localhost:3000` in the default CORS_ALLOWED_ORIGINS config

So the TPRM backend should work fine. This fix is specifically for the GRC backend.







