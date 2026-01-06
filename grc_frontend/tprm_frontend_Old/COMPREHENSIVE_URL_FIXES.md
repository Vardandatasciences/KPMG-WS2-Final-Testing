# Comprehensive URL Fixes - TPRM Frontend

## Date: November 29, 2025
## Status: IN PROGRESS

---

## Problem Statement
Multiple TPRM frontend files were using incorrect API base URLs, causing 404, 401, and 403 errors across the application.

### Wrong URLs Found:
- ❌ `/api/v1/...` (old v1 endpoint structure)
- ❌ `/api/contracts/...` (missing `/tprm` prefix)
- ❌ `/api/quick-access/...` (missing `/tprm` prefix)
- ❌ `/api/vendor-core/...` (missing `/tprm` prefix)
- ❌ `/api/rfp-approval/...` (missing `/tprm` prefix)
- ❌ `/api/approval/...` (missing `/tprm` prefix)
- ❌ `http://localhost:3000/api` (wrong port!)

### Correct URL Structure:
- ✅ `/api/tprm/...` (all TPRM endpoints MUST include this prefix)

---

## Files Fixed (Session 2)

### Configuration Files
1. **src/config/api.js** ✅
   - `BASE_URL`: `http://localhost:8000/api` → `http://localhost:8000/api/tprm`
   - `RFP_APPROVAL_BASE`: `http://localhost:8000/api/rfp-approval` → `http://localhost:8000/api/tprm/rfp-approval`

### Service Files (Additional Fixes)
2. **src/services/approvalService.js** ✅
   - `API_BASE_URL`: `http://localhost:3000/api` → `http://localhost:8000/api/tprm`
   - Fixed wrong port (3000 → 8000) AND added `/tprm` prefix

3. **src/services/slaApprovalApi.js** ✅
   - `baseURL`: `http://localhost:8000/api/slas/approvals` → `http://localhost:8000/api/tprm/slas/approvals`

### Vue Component Files
4. **src/views/rfp/KPIs.vue** ✅
   - Changed from `getApiV1BaseUrl()` to `getTprmApiUrl('rfp')`
   - Updated import statement accordingly
   - All KPI endpoints now correctly use `/api/tprm/rfp/kpi/...`

5. **src/views/rfp-approval/MyApprovals.vue** ✅
   - Fixed 2 hardcoded URLs:
     - `http://localhost:8000/api/approval/` → `http://localhost:8000/api/tprm/approval/`
     - `http://localhost:8000/api/rfp-approval/` → `http://localhost:8000/api/tprm/rfp-approval/`

---

## Files Still Requiring Fixes (Detected)

### Vue Components (18 files remain)
The following files still contain old URL patterns and need to be fixed:

6. **src/views/rfp-approval/ProposalEvaluation.vue**
7. **src/views/rfp-approval/CommitteeSelection.vue**
8. **src/views/rfp-approval/CommitteeEvaluation.vue**
9. **src/views/rfp/Phase1Creation.vue**
10. **src/views/rfp-approval/ApprovalWorkflowCreator.vue**
11. **src/views/rfp/RFPList.vue**
12. **src/views/rfp-approval/StageReviewer.vue**
13. **src/pages/vendor/VendorQuestionnaireBuilder.vue**
14. **src/pages/contract/CreateSubcontractAdvanced.vue**
15. **src/pages/contract/CreateSubcontract.vue**
16. **src/pages/contract/CreateContract.vue**
17. **src/pages/Sla/SLACreateEdit.vue**
18. **src/pages/BCP/VendorUpload.vue**
19. **src/pages/BCP/QuestionnaireWorkflow.vue**
20. **src/pages/BCP/PlanEvaluation.vue**
21. **src/pages/BCP/Dashboard.vue**
22. **src/utils/securityUtils.js**

---

## Summary

### ✅ Fixed in This Session: 5 files
1. config/api.js
2. services/approvalService.js
3. services/slaApprovalApi.js
4. views/rfp/KPIs.vue
5. views/rfp-approval/MyApprovals.vue

### ✅ Fixed in Previous Session: 31 files
(See API_URL_FIXES.md for complete list)

### ⚠️ Remaining: 18 files
(Listed above)

---

## Next Steps

1. **Continue fixing Vue component files** - Replace all old URL patterns with correct `/api/tprm/` prefixed URLs
2. **Test all endpoints** after fixes are complete
3. **Clear browser cache** and do a hard refresh
4. **Verify database permissions** for radha.sharma user
5. **Check backend server** is running the latest code

---

## Testing Checklist

After all fixes are complete, test these endpoints:
- [ ] RFP Dashboard: `GET /api/tprm/rfp/...`
- [ ] Vendor Lifecycle: `GET /api/tprm/vendor-lifecycle/...`
- [ ] Contracts: `GET /api/tprm/contracts/...`
- [ ] Quick Access Logs: `POST /api/tprm/quick-access/logs/`
- [ ] Vendor Core: `GET /api/tprm/vendor-core/...`
- [ ] Notifications: `GET /api/tprm/notifications/...`
- [ ] RBAC Permissions: `GET /api/tprm/rbac/...`
- [ ] RFP Approval: `GET /api/tprm/rfp-approval/...`
- [ ] RFP KPIs: `GET /api/tprm/rfp/kpi/...`
- [ ] SLA Approvals: `GET /api/tprm/slas/approvals/...`

---

**Progress**: 36 of 54 files fixed (66.7% complete)


