# API URL Fixes - TPRM Frontend

## Problem
Multiple TPRM frontend services were using incorrect API base URLs, causing 404 errors:
- ❌ `/api/v1/...` (old URL)
- ❌ `/api/contracts/...` (missing `/tprm` prefix)
- ❌ `/api/quick-access/...` (missing `/tprm` prefix)
- ❌ `/api/vendor-core/...` (missing `/tprm` prefix)

## Solution
All API URLs have been updated to use the correct TPRM prefix:
- ✅ `/api/tprm/...` (correct URL)

---

## Files Modified (28 files)

### Services (11 files)
1. **src/services/api.js**
   - ✅ `API_BASE_URL`: `http://localhost:8000/api/tprm`
   - ✅ `RFP_API_URL`: `http://localhost:8000/api/tprm/rfp`
   - ✅ `SLA_API_URL`: `http://localhost:8000/api/tprm/slas`
   - ✅ `AUDITS_API_URL`: `http://localhost:8000/api/tprm/audits`
   - ✅ `NOTIFICATIONS_API_URL`: `http://localhost:8000/api/tprm/notifications`
   - ✅ `BCPDRP_API_URL`: `http://localhost:8000/api/tprm/bcpdrp`
   - ✅ `RISK_ANALYSIS_API_URL`: `http://localhost:8000/api/tprm/risk-analysis`
   - ✅ Axios export `baseURL`: `http://localhost:8000/api/tprm`

2. **src/services/vendorApi.js**
   - ✅ `VENDOR_BASE_URL`: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm`

3. **src/services/loggingService.js**
   - ✅ `LOGGING_API_URL`: `http://localhost:8000/api/quick-access/logs/` → `http://localhost:8000/api/tprm/quick-access/logs/`

4. **src/services/adminAccessService.js**
   - ✅ `API_BASE_URL`: `http://localhost:8000/api/admin-access` → `http://localhost:8000/api/tprm/admin-access`

5. **src/services/vendorcontractsApi.js**
   - ✅ `API_BASE_URL`: `http://localhost:8000/api` → `http://localhost:8000/api/tprm`

6. **src/services/contractAuditApi.js**
   - ✅ `API_BASE_URL`: `http://localhost:8000/api` → `http://localhost:8000/api/tprm`

7. **src/services/contractApprovalApi.js**
   - ✅ `baseURL`: `http://localhost:8000/api` → `http://localhost:8000/api/tprm`

8. **src/services/api_contract.js**
   - ✅ `baseURL`: `http://localhost:8000/api` → `http://localhost:8000/api/tprm`

9. **src/services/globalsearch_api.js**
   - ✅ `baseURL`: `http://localhost:8000/api` → `http://localhost:8000/api/tprm`

10. **src/services/newInvitationService.js**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

11. **src/services/contractsApi.js**
    - ✅ Uses `api` from `./api` (already fixed above)

### Utils & API (2 files)
12. **src/utils/rfpApiClient.js**
    - ✅ `baseURL`: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm`

13. **src/api/quickAccessAPI.js**
    - ✅ `API_BASE_URL`: `http://localhost:8000/api/quick-access` → `http://localhost:8000/api/tprm/quick-access`

### Stores (1 file)
14. **src/stores/questionnaires.js**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

### Vendor Pages (4 files)
15. **src/pages/vendor/VendorRegistration.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1/vendor-core` → `http://localhost:8000/api/tprm/vendor-core`

16. **src/pages/vendor/VendorRiskScoring.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm`

17. **src/pages/vendor/VendorLifecycleTracker.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm`

18. **src/pages/vendor/VendorExternalScreening.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm`

### RFP Views (8 files)
19. **src/views/rfp/RFPList.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

20. **src/views/rfp/VendorPortal.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

21. **src/views/rfp/Phase9Award.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

22. **src/views/rfp/Phase8ConsensusAndAward.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

23. **src/views/rfp/Phase8Consensus.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

24. **src/views/rfp/Phase6Evaluation.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

25. **src/views/rfp/Phase1Creation.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

26. **src/views/rfp/DraftManager.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

27. **src/views/rfp/AwardResponse.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

### RFP Approval Views (4 files)
28. **src/views/rfp-approval/ApprovalWorkflowCreator.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

29. **src/views/rfp-approval/ProposalEvaluation.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

30. **src/views/rfp-approval/CommitteeSelection.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

31. **src/views/rfp-approval/CommitteeEvaluation.vue**
    - ✅ All hardcoded URLs: `http://localhost:8000/api/v1` → `http://localhost:8000/api/tprm/rfp`

---

## Backend URL Configuration
All TPRM backend URLs are correctly configured in `grc_backend/backend/urls.py`:

```python
# TPRM routes are all prefixed with /api/tprm/
path('api/tprm/rbac/', include('tprm_backend.rbac.tprm_urls')),
path('api/tprm/admin-access/', include('tprm_backend.admin_access.urls')),
path('api/tprm/global-search/', include('tprm_backend.global_search.urls')),
path('api/tprm/core/', include('tprm_backend.core.urls')),
path('api/tprm/ocr/', include('tprm_backend.ocr_app.urls')),
path('api/tprm/slas/', include('tprm_backend.slas.urls')),
path('api/tprm/audits/', include('tprm_backend.audits.urls')),
path('api/tprm/notifications/', include('tprm_backend.notifications.urls')),
path('api/tprm/quick-access/', include('tprm_backend.quick_access.urls')),
path('api/tprm/compliance/', include('tprm_backend.compliance.urls')),
path('api/tprm/bcpdrp/', include('tprm_backend.bcpdrp.urls')),
path('api/tprm/risk-analysis/', include('tprm_backend.risk_analysis.urls')),
path('api/tprm/contracts/', include('tprm_backend.contracts.urls')),
path('api/tprm/audits-contract/', include('tprm_backend.audits_contract.urls')),
path('api/tprm/contract-risk-analysis/', include('tprm_backend.contract_risk_analysis.urls')),
path('api/tprm/rfp/', include('tprm_backend.rfp.urls')),
path('api/tprm/rfp-approval/', include('tprm_backend.rfp_approval.urls')),
path('api/tprm/rfp-risk-analysis/', include('tprm_backend.rfp_risk_analysis.urls')),
path('api/tprm/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),
path('api/tprm/vendor-auth/', include('tprm_backend.apps.vendor_auth.urls')),
path('api/tprm/vendor-risk/', include('tprm_backend.apps.vendor_risk.urls')),
path('api/tprm/vendor-questionnaire/', include('tprm_backend.apps.vendor_questionnaire.urls')),
path('api/tprm/vendor-dashboard/', include('tprm_backend.apps.vendor_dashboard.urls')),
path('api/tprm/vendor-lifecycle/', include('tprm_backend.apps.vendor_lifecycle.urls')),
path('api/tprm/vendor-approval/', include('tprm_backend.apps.vendor_approval.urls')),
path('api/tprm/risk-analysis-vendor/', include('tprm_backend.risk_analysis_vendor.urls')),
```

---

## Testing Required
After these changes, test the following endpoints:
1. ✅ RFP Dashboard: `GET /api/tprm/rfp/...`
2. ✅ Vendor Lifecycle: `GET /api/tprm/vendor-lifecycle/...`
3. ✅ Contracts: `GET /api/tprm/contracts/...`
4. ✅ Quick Access Logs: `POST /api/tprm/quick-access/logs/`
5. ✅ Vendor Core: `GET /api/tprm/vendor-core/...`
6. ✅ Notifications: `GET /api/tprm/notifications/...`
7. ✅ RBAC Permissions: `GET /api/tprm/rbac/...`

---

## Next Steps
1. **Hard refresh browser** (Ctrl+Shift+R or Cmd+Shift+R) to clear cached JavaScript
2. **Verify all API calls** are now hitting `/api/tprm/...` instead of `/api/v1/...`
3. **Check browser console** for any remaining 404 errors
4. **Test all TPRM modules** (RFP, Contracts, Vendor, SLA, etc.)

---

**Date**: November 29, 2025  
**Status**: ✅ COMPLETE - All 31 files updated


