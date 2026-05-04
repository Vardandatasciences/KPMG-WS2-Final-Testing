# Compliance Store — Getters & Actions Blueprint

This document captures the detailed **Pinia getters and actions** blueprint for a proposed `complianceStore`.

Suggested store file path:

- `grc_frontend/src/stores/compliance.js`

---

## 1) Detailed Getters

## A. Selection + Context Getters

- `activeFrameworkId(state)`  
  Returns currently selected framework id.

- `activePolicyId(state)`  
  Returns currently selected policy id.

- `activeSubpolicyId(state)`  
  Returns currently selected subpolicy id.

- `activeComplianceId(state)`  
  Returns currently selected compliance id.

- `selectedCompliance(state)`  
  Returns `compliancesById[selectedComplianceId]` or `null`.

---

## B. Hierarchy Data Getters

- `policiesForFramework: (state) => (frameworkId)`  
  Returns `policiesByFrameworkId[frameworkId] || []`.

- `subpoliciesForPolicy: (state) => (policyId)`  
  Returns `subpoliciesByPolicyId[policyId] || []`.

- `compliancesForSubpolicy: (state) => (subpolicyId)`  
  Returns `compliancesBySubpolicyId[subpolicyId] || []`.

- `complianceById: (state) => (complianceId)`  
  Returns `compliancesById[complianceId] || null`.

---

## C. Derived Counters / KPI Helpers

- `totalCompliances(state)`
- `activeCompliances(state)`
- `inactiveCompliances(state)`
- `underReviewCompliances(state)`
- `approvedCompliances(state)`
- `rejectedCompliances(state)`

- `complianceCountByFramework: (state) => (frameworkId)`  
  Derived count from framework-linked hierarchy.

- `approvalRate(state)`  
  Derived approval percentage based on available approval statuses.

---

## D. Approval Flow Getters

- `reviewerPendingItems(state)`
- `reviewerCompletedItems(state)`
- `userPendingApprovals(state)`
- `userRejectedApprovals(state)`

- `canReviewCompliance: (state) => (complianceId, userId)`  
  Returns true/false from assignment and review status data.

- `approvalItemById: (state) => (approvalId)`

---

## E. Baseline/Cross-Framework/Org Controls Getters

- `baselineConfigsForFramework: (state) => (frameworkId)`
- `baselineVersionsForFramework: (state) => (frameworkId)`
- `crossFrameworkComparison(state)`
- `organizationalControlsForFramework: (state) => (frameworkId)`
- `organizationalStatsForFramework: (state) => (frameworkId)`

---

## F. Export Getters

- `complianceRegisterExportJob(state)`
- `auditManagementExportJob(state)`
- `isExportInProgress(state)`
- `exportDownloadUrl: (state) => (jobType)`

---

## G. Cache Freshness Getters

- `isFrameworksFresh: (state) => (ttlMs = 15 * 60 * 1000)`
- `isHierarchyFresh: (state) => (ttlMs = 5 * 60 * 1000)`
- `isApprovalsFresh: (state) => (ttlMs = 60 * 1000)`
- `isDashboardFresh: (state) => (ttlMs = 5 * 60 * 1000)`
- `isKpiFresh: (state) => (ttlMs = 5 * 60 * 1000)`
- `isComplianceDetailFresh: (state) => (complianceId, ttlMs = 60 * 1000)`
- `isBaselineFresh: (state) => (frameworkId, ttlMs = 10 * 60 * 1000)`
- `isOrgControlsFresh: (state) => (frameworkId, ttlMs = 5 * 60 * 1000)`

---

## H. Loading/Error Helpers

- `isAnyLoading(state)`
- `hasAnyError(state)`
- `errorFor: (state) => (scope)`
- `isLoadingScope: (state) => (scope)`

---

## 2) Detailed Actions

## 2.1 Local Context / Non-API Actions

- `setSelectedFramework(frameworkId)`
- `setSelectedPolicy(policyId)`
- `setSelectedSubpolicy(subpolicyId)`
- `setSelectedCompliance(complianceId)`
- `setApprovalFilters(filtersPatch)`
- `resetApprovalFilters()`
- `resetSelection()`

---

## 2.2 Cache Utility Actions

- `markLoading(scope, value)`
- `setScopeError(scope, error)`
- `clearScopeError(scope)`
- `markFetched(scope, key?)`
- `invalidate(scope)`  
  Scope examples: `frameworks`, `hierarchy`, `approvals`, `dashboard`, `kpi`, `baseline`, `orgControls`, `exports`.

- `invalidateComplianceDetail(complianceId)`
- `resetState()`

---

## 2.3 Framework + Hierarchy Fetch Actions

- `fetchFrameworks({ force = false } = {})`
- `fetchPoliciesByFramework(frameworkId, { force = false } = {})`
- `fetchSubpoliciesByPolicy(policyId, { force = false } = {})`
- `fetchCompliancesBySubpolicy(subpolicyId, { force = false } = {})`

- `fetchHierarchy({ frameworkId, policyId, subpolicyId, force = false } = {})`  
  Orchestrates the hierarchy chain fetch.

- `prefetchComplianceDomain({ force = false } = {})`  
  Replaces global `window.*` promise style patterns.

---

## 2.4 Compliance Detail/View Actions

- `fetchComplianceDetails(complianceId, { force = false } = {})`
- `fetchComplianceViewByType({ type, id, force = false })`  
  Route usage: `/compliance/view/:type/:id/:name`

- `fetchComplianceAuditViewByType({ type, id, force = false })`  
  Route usage: `/compliance/audit/:type/:id/:name`

- `fetchAuditInfoForCompliance(complianceId, { force = false } = {})`

---

## 2.5 Approval Actions

- `fetchApprovalsAsUser({ userId, page, limit, status, force = false })`
- `fetchApprovalsAsReviewer({ userId, page, limit, status, force = false })`
- `fetchRejectedApprovals({ reviewerId, force = false })`
- `submitComplianceReview({ approvalId, approved, comments })`
- `resubmitComplianceApproval({ approvalId, payload })`
- `refreshApprovalsAfterMutation()`

---

## 2.6 CRUD/Mutation Actions

- `createCompliance(payload)`
- `updateCompliance({ complianceId, payload })`
- `cloneCompliance({ complianceId, payload })`
- `toggleComplianceVersion(complianceId)`
- `deactivateCompliance({ complianceId, payload })`
- `approveComplianceDeactivation({ approvalId, payload })`
- `rejectComplianceDeactivation({ approvalId, payload })`

Expected invalidation after successful mutation:

- `invalidate('hierarchy')`
- `invalidateComplianceDetail(complianceId)` (when applicable)
- `invalidate('dashboard')`
- `invalidate('kpi')`

---

## 2.7 Audit Management / Status Actions

- `fetchAuditManagementList({ frameworkId, filters, force = false })`
- `fetchAuditStatusList({ filters, force = false })`
- `fetchAllForAuditManagementPublic({ force = false })`
- `refreshAuditManagement()`

---

## 2.8 Dashboard + KPI Actions

- `fetchComplianceDashboard({ frameworkId, filters, force = false })`
- `fetchComplianceKpi({ frameworkId, filters, force = false })`
- `fetchKpiBundle({ frameworkId, filters, force = false })`
- `syncDashboardCacheWithDashboardsStore()` (optional)

---

## 2.9 Baseline Configuration Actions

- `fetchBaselineConfigs(frameworkId, { force = false })`
- `createBaselineVersion(payload)`
- `fetchBaselineVersions(frameworkId, { force = false })`
- `refreshBaselineForFramework(frameworkId)`

---

## 2.10 Cross-Framework Mapping Actions

- `fetchCrossFrameworkList({ force = false })`
- `fetchCrossFrameworkMapping(frameworkId, { side = 'left', force = false })`
- `compareFrameworkVersions(payload)`
- `clearCrossFrameworkComparison()`

---

## 2.11 Organizational Controls Actions

- `fetchOrganizationalControls(frameworkId, { force = false })`
- `fetchOrganizationalStats(frameworkId, { force = false })`
- `uploadOrganizationalControls(formData)`
- `saveOrganizationalControls(payload)`
- `runOrganizationalAudit(payload)`
- `refreshOrganizationalControls(frameworkId)`

---

## 2.12 Export Actions

- `startComplianceRegisterExport(payload)`
- `startAuditManagementExport(payload)`
- `pollExportStatus({ taskId, type })`
- `clearExportJob(type)`

---

## 3) Action Naming Convention

Use consistent verbs:

- `fetch*` for read APIs
- `create*`, `update*`, `delete*`, `toggle*` for mutations
- `refresh*` for forced reload
- `invalidate*` for cache invalidation
- `set*`, `reset*` for local store state

---

## 4) Recommended Implementation Order

1. Context + cache utility actions
2. `fetchFrameworks` + hierarchy actions
3. approval actions
4. detail/view actions
5. dashboard/KPI actions
6. mutation actions + invalidation hooks
7. baseline/cross-framework/org-controls
8. export actions

This keeps migration safe while page-by-page rollout continues.

