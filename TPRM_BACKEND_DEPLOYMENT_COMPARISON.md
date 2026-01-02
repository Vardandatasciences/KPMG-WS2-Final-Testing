# TPRM Backend Deployment Comparison Report
## NEW Backend vs CURRENT Backend (Deployment-Related Code)

**Date:** November 2024  
**Purpose:** Compare deployment-related configurations between NEW standalone TPRM backend and CURRENT integrated backend

---

## Executive Summary

**Key Finding:** The NEW backend (`backend/`) is a **standalone TPRM deployment**, while the CURRENT backend (`grc_backend/tprm_backend/`) is **integrated into GRC** with additional API prefix routes.

**Critical Differences:**
1. **URL Configuration:** CURRENT has `/api/tprm/` prefix routes for integration
2. **CORS Configuration:** Different default origins
3. **Frontend URL:** Different production URLs
4. **Vendor MFA:** Different default settings
5. **Directory Structure:** NEW has `rfp_old/` and `rfp_approval_old/` directories (cleanup needed)

---

## 1. Settings Configuration Comparison

### File: `vendor_guard_hub/settings.py`

#### 1.1 CORS Configuration (Line 311)

**NEW Backend (`backend/vendor_guard_hub/settings.py`):**
```python
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173', cast=lambda v: [s.strip() for s in v.split(',')])
```

**CURRENT Backend (`grc_backend/tprm_backend/vendor_guard_hub/settings.py`):**
```python
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,https://grc-tprm.vardaands.com/tprm,,https://grc-tprm.vardaands.com,http://localhost:3000,http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173', cast=lambda v: [s.strip() for s in v.split(',')])
```

**DIFFERENCE:**
- **CURRENT** includes production URLs: `https://grc-tprm.vardaands.com/tprm` and `https://grc-tprm.vardaands.com`
- **NEW** only has development URLs

**ACTION REQUIRED:** Add production URLs to NEW backend if deploying standalone.

---

#### 1.2 Frontend URL Configuration (Line 584)

**NEW Backend:**
```python
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')
```

**CURRENT Backend:**
```python
FRONTEND_URL = config('FRONTEND_URL', default='https://grc-tprm.vardaands.com/tprm')
```

**DIFFERENCE:**
- **NEW** uses localhost (standalone deployment)
- **CURRENT** uses production URL (integrated deployment)

**ACTION REQUIRED:** Update NEW backend with production URL if deploying standalone.

---

#### 1.3 Vendor MFA Configuration (Line 586)

**NEW Backend:**
```python
ENABLE_VENDOR_MFA = config('ENABLE_VENDOR_MFA', default=True, cast=bool)
```

**CURRENT Backend:**
```python
# MFA removed from TPRM vendor experience (single-step login only)
ENABLE_VENDOR_MFA = False
```

**DIFFERENCE:**
- **NEW** has MFA enabled by default
- **CURRENT** has MFA disabled (single-step login)

**ACTION REQUIRED:** Decide which approach to use. CURRENT backend explicitly disabled MFA for vendor experience.

---

#### 1.4 All Other Settings

**STATUS:** ✅ **IDENTICAL**

All other settings are identical:
- Database configuration
- INSTALLED_APPS
- MIDDLEWARE
- REST_FRAMEWORK
- SIMPLE_JWT
- Security settings
- Logging configuration
- Email configuration
- OCR configuration
- Vendor settings

---

## 2. URL Configuration Comparison

### File: `vendor_guard_hub/urls.py`

#### 2.1 TPRM API Prefix Routes

**NEW Backend (`backend/vendor_guard_hub/urls.py`):**
- ❌ **DOES NOT HAVE** `/api/tprm/` prefix routes
- Routes are directly under `/api/`

**CURRENT Backend (`grc_backend/tprm_backend/vendor_guard_hub/urls.py`):**
- ✅ **HAS** `/api/tprm/` prefix routes (Lines 115-139)
- Additional routes for integration:
  ```python
  # TPRM API prefix routes (for frontend compatibility - /api/tprm/*)
  path('api/tprm/rfp/', include('rfp.urls')),
  path('api/tprm/global-search/', include('global_search.urls')),
  path('api/tprm/vendor-core/', include('apps.vendor_core.urls')),
  path('api/tprm/vendor-auth/', include('apps.vendor_auth.urls')),
  path('api/tprm/vendor-risk/', include('apps.vendor_risk.urls')),
  path('api/tprm/vendor-questionnaire/', include('apps.vendor_questionnaire.urls')),
  path('api/tprm/vendor-dashboard/', include('apps.vendor_dashboard.urls')),
  path('api/tprm/vendor-lifecycle/', include('apps.vendor_lifecycle.urls')),
  path('api/tprm/vendor-approval/', include('apps.vendor_approval.urls')),
  path('api/tprm/risk-analysis-vendor/', include('risk_analysis_vendor.urls')),
  path('api/tprm/slas/', include('slas.urls')),
  path('api/tprm/audits/', include('audits.urls')),
  path('api/tprm/notifications/', include('notifications.urls')),
  path('api/tprm/quick-access/', include('quick_access.urls')),
  path('api/tprm/compliance/', include('compliance.urls')),
  path('api/tprm/bcpdrp/', include('bcpdrp.urls')),
  path('api/tprm/risk-analysis/', include('risk_analysis.urls')),
  path('api/tprm/contracts/', include('contracts.urls')),
  path('api/tprm/audits-contract/', include('audits_contract.urls')),
  path('api/tprm/contract-risk-analysis/', include('contract_risk_analysis.urls')),
  path('api/tprm/rfp-approval/', include('rfp_approval.urls')),
  ```

**DIFFERENCE:**
- **CURRENT** has integration routes for GRC frontend compatibility
- **NEW** is standalone, doesn't need prefix routes

**ACTION REQUIRED:**
- If NEW backend will be integrated into GRC, add these routes
- If NEW backend will be standalone, no action needed

---

#### 2.2 All Other URL Routes

**STATUS:** ✅ **IDENTICAL**

All other routes are identical:
- Admin routes
- API documentation routes
- Authentication routes
- RBAC routes
- All app routes (SLA, Audit, Contract, RFP, Vendor, etc.)
- MPA routes for RFP

---

## 3. WSGI/ASGI Configuration

### Files: `vendor_guard_hub/wsgi.py` and `vendor_guard_hub/asgi.py`

**STATUS:** ✅ **IDENTICAL**

Both files are identical in both backends:
- Same Django settings module reference
- Same application initialization
- No differences

---

## 4. Manage.py Configuration

### File: `manage.py`

**STATUS:** ✅ **IDENTICAL**

Both files are identical:
- Same Django settings module reference
- Same error handling
- No differences

---

## 5. Requirements/Dependencies

### File: `requirements.txt`

**STATUS:** ✅ **IDENTICAL**

Both files have identical dependencies:
- Same package versions
- Same package list
- No differences

---

## 6. Directory Structure Differences

### 6.1 Old/Backup Directories

**NEW Backend HAS:**
- `rfp_old/` - Old RFP implementation (65 files)
- `rfp_approval_old/` - Old RFP approval implementation (8 files)

**CURRENT Backend DOES NOT HAVE:**
- These directories were cleaned up

**ACTION REQUIRED:** Remove old directories from NEW backend before deployment:
```bash
# Remove old directories
rm -rf backend/rfp_old/
rm -rf backend/rfp_approval_old/
```

---

### 6.2 Logs Directory

**NEW Backend:**
- ❌ Does not have `logs/` directory

**CURRENT Backend:**
- ✅ Has `logs/` directory with log files:
  - `django.log`
  - `vendor_security.log`
  - `vendor_tprm.log`

**ACTION REQUIRED:** Ensure logs directory is created (settings.py line 603-604 creates it automatically, but verify it exists).

---

### 6.3 All Other Directories

**STATUS:** ✅ **IDENTICAL**

All other directories are identical:
- All app directories (core, slas, audits, contracts, rfp, vendor apps, etc.)
- Config directories
- Utils, scripts, database directories

---

## 7. Deployment-Specific Differences

### 7.1 Standalone vs Integrated Deployment

**NEW Backend:**
- ✅ **Standalone deployment** - Can run independently
- ✅ Direct API routes (`/api/slas/`, `/api/rfp/`, etc.)
- ✅ No integration dependencies

**CURRENT Backend:**
- ✅ **Integrated deployment** - Part of GRC system
- ✅ Has `/api/tprm/` prefix routes for integration
- ✅ Compatible with GRC frontend

---

### 7.2 Environment Variables

**Both backends use same environment variables:**
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `CORS_ALLOWED_ORIGINS`
- `FRONTEND_URL`
- `EMAIL_*` variables
- `AZURE_AD_*` variables
- `REDIS_URL`
- `OLLAMA_URL`
- `LLAMA_MODEL_NAME`
- `VENDOR_ENCRYPTION_KEY`

**NO DIFFERENCES** - Same environment variable structure.

---

## 8. Summary of Required Changes

### For NEW Backend (if deploying standalone):

1. **CORS Configuration (Line 311)**
   - ✅ **OPTIONAL:** Add production URLs if deploying to production
   - Current: Only development URLs
   - Recommended: Add production URLs for production deployment

2. **Frontend URL (Line 584)**
   - ✅ **OPTIONAL:** Update default to production URL
   - Current: `http://localhost:3000`
   - Recommended: `https://your-production-domain.com` for production

3. **Vendor MFA (Line 586)**
   - ⚠️ **DECISION REQUIRED:** Choose MFA approach
   - NEW: `ENABLE_VENDOR_MFA = True` (default)
   - CURRENT: `ENABLE_VENDOR_MFA = False` (explicitly disabled)
   - **Recommendation:** Follow CURRENT approach (disable MFA for vendor experience)

4. **Cleanup Old Directories**
   - ✅ **REQUIRED:** Remove `rfp_old/` and `rfp_approval_old/` directories
   - These are not needed and add confusion

5. **TPRM API Prefix Routes**
   - ✅ **NOT NEEDED** for standalone deployment
   - Only needed if integrating with GRC frontend

---

### For CURRENT Backend (if keeping integrated):

1. **No changes needed** - Already configured for integration
2. ✅ Has all TPRM API prefix routes
3. ✅ Has production URLs configured
4. ✅ Has MFA disabled for vendor experience
5. ✅ Clean directory structure (no old directories)

---

## 9. Deployment Checklist

### NEW Backend Deployment:

- [ ] Remove `rfp_old/` directory
- [ ] Remove `rfp_approval_old/` directory
- [ ] Update `CORS_ALLOWED_ORIGINS` with production URLs (if deploying to production)
- [ ] Update `FRONTEND_URL` with production URL (if deploying to production)
- [ ] Decide on `ENABLE_VENDOR_MFA` setting (recommend `False` to match CURRENT)
- [ ] Verify `logs/` directory is created (auto-created by settings.py)
- [ ] Set environment variables for production
- [ ] Test all API endpoints
- [ ] Verify database connection
- [ ] Verify static files serving
- [ ] Verify media files serving

### CURRENT Backend Deployment:

- [ ] ✅ Already configured for integration
- [ ] Verify environment variables are set
- [ ] Test all API endpoints (both `/api/` and `/api/tprm/` routes)
- [ ] Verify database connection
- [ ] Verify static files serving
- [ ] Verify media files serving

---

## 10. Critical Notes

1. **Integration Routes:** CURRENT backend has additional routes for GRC integration. If NEW backend needs to integrate, add these routes.

2. **MFA Setting:** CURRENT backend explicitly disables MFA for vendor experience. NEW backend has it enabled by default. This is a **functional difference** that may affect user experience.

3. **Production URLs:** NEW backend only has development URLs in defaults. Must be updated for production deployment.

4. **Old Directories:** NEW backend has old RFP directories that should be removed before deployment.

5. **Logs Directory:** Both backends create logs directory automatically, but verify it exists and has proper permissions.

---

## 11. Recommendations

### If Using NEW Backend for Standalone Deployment:

1. ✅ Remove old directories
2. ✅ Update CORS with production URLs
3. ✅ Update FRONTEND_URL with production URL
4. ✅ Set `ENABLE_VENDOR_MFA = False` to match CURRENT behavior
5. ✅ Test thoroughly before deployment

### If Using CURRENT Backend (Already Integrated):

1. ✅ No changes needed
2. ✅ Already configured correctly
3. ✅ Has all integration routes
4. ✅ Has production URLs configured

### If Merging NEW Backend into CURRENT:

1. ✅ Keep CURRENT backend's URL configuration (has integration routes)
2. ✅ Keep CURRENT backend's CORS configuration (has production URLs)
3. ✅ Keep CURRENT backend's MFA setting (`False`)
4. ✅ Copy any new features from NEW backend
5. ✅ Remove old directories from NEW backend before merging

---

## 12. File-by-File Comparison Summary

| File | Status | Differences |
|------|--------|-------------|
| `vendor_guard_hub/settings.py` | ⚠️ **3 DIFFERENCES** | CORS origins, Frontend URL, Vendor MFA |
| `vendor_guard_hub/urls.py` | ⚠️ **1 DIFFERENCE** | TPRM API prefix routes (CURRENT has, NEW doesn't) |
| `vendor_guard_hub/wsgi.py` | ✅ **IDENTICAL** | No differences |
| `vendor_guard_hub/asgi.py` | ✅ **IDENTICAL** | No differences |
| `manage.py` | ✅ **IDENTICAL** | No differences |
| `requirements.txt` | ✅ **IDENTICAL** | No differences |
| Directory structure | ⚠️ **2 DIFFERENCES** | NEW has old directories, CURRENT has logs directory |

---

**END OF REPORT**



