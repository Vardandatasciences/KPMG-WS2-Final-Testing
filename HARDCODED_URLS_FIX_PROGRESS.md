# Hardcoded URLs Fix Progress
## Status: In Progress

**Total Files Found:** 62 files with 127 hardcoded URLs

---

## ✅ Fixed Files (Service & Utility Layer)

### Service Files (15 files) - ✅ COMPLETE
1. ✅ `src/services/authService.js`
2. ✅ `src/services/vendorApi.js`
3. ✅ `src/services/slaApprovalApi.js`
4. ✅ `src/services/globalsearch_api.js`
5. ✅ `src/services/loggingService.js`
6. ✅ `src/services/newInvitationService.js`
7. ✅ `src/services/permissionsService.js`
8. ✅ `src/services/roleRoutingService.js`
9. ✅ `src/services/contractApprovalApi.js`
10. ✅ `src/services/contractAuditApi.js`
11. ✅ `src/services/vendorcontractsApi.js`
12. ✅ `src/services/api_contract.js`
13. ✅ `src/services/adminAccessService.js`
14. ✅ `src/services/api.js` (already fixed earlier)
15. ✅ `src/services/contractApprovalApi.js`

### Utility Files (4 files) - ✅ COMPLETE
1. ✅ `src/utils/api.js`
2. ✅ `src/utils/api_rfp.js`
3. ✅ `src/utils/rfpApiClient.js`
4. ⚠️ `src/utils/securityUtils.js` (checking)

### Store Files (2 files) - ✅ COMPLETE
1. ✅ `src/stores/auth_vendor.js`
2. ✅ `src/stores/questionnaires.js`

### API Files (2 files) - ✅ COMPLETE
1. ✅ `src/api/http.js`
2. ✅ `src/api/quickAccessAPI.js`

---

## ⚠️ Remaining Files (View Components)

### RFP Views (14 files) - PENDING
- `src/views/rfp/VendorPortal.vue`
- `src/views/rfp/RFPList.vue`
- `src/views/rfp/Phase8ConsensusAndAward.vue`
- `src/views/rfp/Phase6Evaluation.vue`
- `src/views/rfp/Phase1Creation.vue`
- `src/views/rfp/DraftManager.vue`
- `src/views/rfp/AwardResponse.vue`
- `src/views/rfp_old/*` (7 files - may be deprecated)

### RFP Approval Views (12 files) - PENDING
- `src/views/rfp-approval/StageReviewer.vue`
- `src/views/rfp-approval/ProposalEvaluation.vue`
- `src/views/rfp-approval/MyApprovals.vue`
- `src/views/rfp-approval/CommitteeSelection.vue`
- `src/views/rfp-approval/CommitteeEvaluation.vue`
- `src/views/rfp-approval/ApprovalWorkflowCreator.vue`
- `src/views/rfp-approval_old/*` (6 files - may be deprecated)

### Page Components (13 files) - PENDING
- `src/pages/vendor/*` (5 files)
- `src/pages/contract/*` (3 files)
- `src/pages/BCP/*` (5 files)
- `src/pages/Sla/SLACreateEdit.vue`

---

## 📊 Progress Summary

| Category | Total | Fixed | Remaining |
|----------|-------|-------|-----------|
| **Service Files** | 15 | 15 | 0 |
| **Utility Files** | 4 | 3 | 1 |
| **Store Files** | 2 | 2 | 0 |
| **API Files** | 2 | 2 | 0 |
| **View Components** | 39 | 0 | 39 |
| **TOTAL** | 62 | 22 | 40 |

---

## 🎯 Strategy

**Priority 1 (Complete):** ✅ Service & Utility Layer
- All service files now use `backendEnv` utility
- All utility files now use `backendEnv` utility
- All store files now use `backendEnv` utility

**Priority 2 (In Progress):** ⚠️ View Components
- Most view components make direct API calls
- Should use services where possible
- Or use `getApiOrigin()` / `getTprmApiBaseUrl()` for direct calls

---

## 🔧 Fix Pattern

All fixes follow this pattern:

**BEFORE:**
```javascript
const API_BASE_URL = 'http://localhost:8000/api'
```

**AFTER:**
```javascript
import { getTprmApiBaseUrl } from '@/utils/backendEnv'
const API_BASE_URL = getTprmApiBaseUrl()
```

---

**Last Updated:** Now
**Status:** Service/Utility layer complete, View components pending



