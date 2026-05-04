# Auditor Module — Pinia State Management Audit & Migration Plan

**Scope requested:** Auditor sidebar block in `grc_frontend/src/components/Policy/Sidebar.vue` (lines 198–241).  
**Frontend scope analyzed:** `grc_frontend/src/components/Auditor/` + related router entries in `src/router/index.js`.  
**Backend scope note:** `grc_backend/grc/routes/Auditor/` is not present in this repo path; auditor APIs appear routed via broader audit endpoints in other backend route files.

---

## 1. Page/Module Summary

### 1.1 What this module does

The Auditor module supports:

- Audit list/dashboard access
- Audit assignment workflow
- AI audit document upload and processing
- Audit review workflow and confirmations
- Audit report generation/view/download
- Auditor performance analysis (KPI + dashboard)

### 1.2 Sidebar routes and mapped pages

From `Sidebar.vue:198-241`:

| Sidebar menu | Route | Component |
|---|---|---|
| Audits | `/auditor/dashboard` | `AuditorDashboard.vue` |
| Assign Audit | `/auditor/assign` | `AssignAudit.vue` |
| AI Audit Upload | `/auditor/ai-audit/2075/upload` (template route uses `:auditId`) | `AIAuditDocumentUpload.vue` |
| Review Audits | `/auditor/reviews` | `Reviewer.vue` |
| Audit Reports | `/auditor/reports` | `AuditReport.vue` |
| KPIs Analysis | `/auditor/performance/kpi` | `KPIAnalysis` route target (`KpiAnalysis.vue`) |
| Dashboard | `/auditor/performance/userdashboard` | `UserDashboard.vue` |

### 1.3 Additional auditor routes involved in same module

- `/auditor/reviewer` → `Reviewer.vue`
- `/auditor/audits` → `Audits.vue`
- `/audit-report/:id` → `AuditReportView.vue`
- `/audit-reports/:auditId` → `AuditReportsView.vue`
- `/audit-versions/:auditId` → `AuditVersionsView.vue`
- `/audit-findings/:id` → `AuditFindingDetailsView.vue`
- `/reviewer/task/:auditId` / `/auditor/task/:auditId` style flows via `TaskView.vue`, `ReviewTaskView.vue`, `ReviewConfirmation.vue`

### 1.4 Parent/layout

- Loaded in global app shell (`App.vue` with `Sidebar.vue` + `router-view`).
- No dedicated Auditor layout component; route-level pages hold own state logic.

### 1.5 Workflow category mapping

- Audit workflow, reviewer workflow, reporting, dashboard/KPI, AI-assisted evidence/document processing, RBAC-gated actions.

---

## 2. Current Vue Implementation Summary

### 2.1 API style

Mixed Options API and `script setup` across auditor pages.

### 2.2 Existing Pinia usage

- `UserDashboard.vue` uses `useDashboardsStore` and `useAppDataStore`.
- No dedicated `auditStore`/`auditorStore` yet.

### 2.3 Existing cache pattern outside Pinia

- `src/services/auditorService.js` caches audits/business units.
- Several components use `window.auditorDataFetchPromise` + `auditorDataService.fetchAllAuditorData()` (notably `AIAuditDocumentUpload.vue`, also integration points in `AssignAudit.vue`).

### 2.4 API orchestration location

- Most API calls are still component-level via `apiService` + `API_ENDPOINTS`.
- Very large API surface concentrated in `AIAuditDocumentUpload.vue`.

### 2.5 RBAC checks

- Route-level permission metadata exists for key auditor routes (`view_audit_reports`, `assign_audit`, `conduct_audit`, `review_audit`).
- Component-level permission/role branching still appears in some pages and should be standardized.

---

## 3. Current Data Flow

1. Route loads an auditor component.
2. Component fetches framework/audit/review/report data directly.
3. Some pages first attempt service cache via `auditorDataService`.
4. Mutations (assign, review submit, status update, document actions) trigger local refreshes.
5. Dashboard pages use `dashboardsStore` but data flow is not fully centralized in one audit store.

### Current risks

- Duplicate API calls across routes
- `window.*` fetch-promise anti-pattern outside Pinia
- inconsistent cache invalidation after create/assign/review operations

---

## 4. Variable Inventory (Grouped)

| Variable group | Examples | Type | Keep local | Move to Pinia |
|---|---|---|---|---|
| Audit collections | audits list, report list, review queue | API shared data | No | Yes |
| Scope selectors | framework/policy/subpolicy/current audit context | shared workflow state | Partial | Yes |
| AI upload process state | processing stage flags, job ids, polling result lists | mixed | local UI parts yes | job/result shared parts yes |
| Dashboard cards/charts | completion rate, open/completed counts, category/status distributions | API shared | No | Yes |
| Modals/dropdowns | visibility flags, chooser state | local UI | Yes | No |
| Form fields | assign-audit form, reviewer comments | local form | Yes | No (unless cross-page draft needed) |

---

## 5. State Classification

### 5.1 Keep local

- Modal open/close
- Temporary input values
- Inline button loading for isolated actions
- Local chart display preferences (if not shared)

### 5.2 Move to Pinia

- Shared audit lists and lookup data used across Assign/Review/Reports/Dashboard
- Current audit context when reused across nested flows
- Export/report status where user navigates across pages

### 5.3 API/server data through Pinia actions

- Audit list/detail
- Reviewer assignments and review progress
- Report metadata
- Dashboard/KPI metrics
- AI audit process summaries (not all raw transient internals)

---

## 6. API Call Inventory (Major families)

Observed in auditor components:

- `AUDIT_MY_AUDITS`, `/api/audits/`, `AUDITS_PUBLIC`
- `AUDIT_CREATE`, `AUDIT_TASK_DETAILS`, `AUDIT_SAVE_REVIEW_PROGRESS`, `UPDATE_AUDIT_REVIEW_STATUS`
- `AUDIT_REPORTS`, `AUDIT_REPORT`, `GENERATE_AUDIT_REPORT`
- `AUDIT_COMPLETION_RATE`, `AUDIT_TOTAL_AUDITS`, `AUDIT_OPEN_AUDITS`, `AUDIT_COMPLETED_AUDITS`, category/status distribution, recent activities
- `USERS_FOR_REVIEWER_SELECTION`, `BUSINESS_UNITS`
- AI audit endpoints: upload/documents/status/job status/schedule/actions/results/relevance checks
- `PUSH_NOTIFICATION`

Recommendation: move all reusable families into Pinia actions; keep only highly local one-off calls in components.

---

## 7. Recommended Pinia Store Plan

### 7.1 `auditStore` (new, primary)

Suggested file: `src/stores/audit.js`

**Purpose:** central source for auditor module shared state.

**State fields:** see detailed section in **Section 8** (source blueprint for implementation)

### 7.2 `dashboardsStore` (existing)

- Keep as KPI summary cache for `audit` domain.
- Make `auditStore` the orchestrator that writes into `dashboardsStore`.

### 7.3 `appDataStore` (existing)

- `fetchAudits()` already aggregates via `auditorDataService`.
- Align with `auditStore` so there is one authoritative fetch path.

### 7.4 `frameworkStore` (existing, optional integration)

- Use only when framework context genuinely drives auditor screens; avoid per-component `FRAMEWORK_GET_SELECTED` duplication.

---

## 8. Recommended State Design

```js
state: () => ({
  // Core audit datasets
  audits: [],                              // primary audit list
  auditDetailsById: {},                    // auditId -> detail payload
  auditsByScope: {
    all: [],
    assignedToMe: [],
    createdByMe: []
  },

  // Review workflow data
  reviews: {
    queue: [],                             // reviewer queue list
    reviewerTasksByAuditId: {},            // auditId -> task[]
    progressByAuditId: {},                 // auditId -> draft/progress snapshot
    summary: null,                         // counts by status/type
    lastQuery: null
  },

  // Reporting data
  reports: {
    list: [],                              // audit reports table data
    byAuditId: {},                         // auditId -> report[]
    reportById: {},                        // reportId -> report
    generationJobsByAuditId: {},           // auditId -> latest generation job/status
    downloadsByReportId: {}                // reportId -> url/meta cache
  },

  // Shared lookups and context
  lookups: {
    businessUnits: [],
    reviewers: [],
    frameworks: [],
    categories: []
  },
  selectedAuditId: null,
  selectedReviewerId: null,

  // AI audit upload/process state shared across upload/review/report views
  aiAudit: {
    summariesByAuditId: {},                // auditId -> AI summary
    jobsByAuditId: {},                     // auditId -> processing jobs
    documentsByAuditId: {},                // auditId -> uploaded doc list
    resultsByAuditId: {},                  // auditId -> extraction/evaluation results
    relevanceChecksByAuditId: {}           // auditId -> relevance status/details
  },

  // Dashboard / KPI analytics
  dashboardMetrics: null,                  // cards + aggregates
  dashboardWidgets: {},                    // widget-level split cache
  kpiMetrics: null,                        // raw KPI payload
  kpiSeriesByMetric: {},                   // transformed chart series
  dashboardFilters: null,                  // persistent cross-widget filters

  // Mutation loading flags for precise button-level UX
  mutationStatus: {
    assignAudit: false,
    saveReviewProgress: false,
    submitReviewStatus: false,
    generateReport: false,
    aiUpload: false
  },

  // Generic async + error handling
  status: 'idle', // idle | loading | success | error
  isLoading: false,
  isRefreshing: false,
  error: null,
  errorByScope: {
    audits: null,
    reviewQueue: null,
    reports: null,
    lookups: null,
    aiAudit: null,
    dashboard: null,
    kpi: null
  },

  // TTL timestamps and request de-duplication
  lastFetched: {
    audits: null,
    auditDetails: {},
    reviews: null,
    reports: null,
    lookups: null,
    aiAuditSummaryByAudit: {},
    dashboard: null,
    kpi: null
  },
  inFlightRequests: {}                     // requestKey -> Promise
})
```

---

## 9. Recommended Getters

- `auditById: (state) => (auditId) => state.auditDetailsById[auditId] || null`

- `selectedAudit`  
  - Returns selected audit detail using `selectedAuditId`.

- `auditsForScope: (state) => (scope = 'all') => state.auditsByScope[scope] || []`

- `pendingReviewCount`  
  - Derived pending count from `reviews.queue`.

- `reviewCountByStatus`  
  - Grouped count object for queue badges/cards.

- `reportsForAudit: (state) => (auditId) => state.reports.byAuditId[auditId] || []`

- `latestReportForAudit: (state) => (auditId) => { ... }`

- `aiAuditSummary: (state) => (auditId) => state.aiAudit.summariesByAuditId[auditId]`

- `aiAuditJobStatus: (state) => (auditId) => state.aiAudit.jobsByAuditId[auditId] || null`

- `openAuditsCount` / `completedAuditsCount`  
  - Status-based derived counters for dashboard cards.

- `dashboardCards`  
  - Normalized dashboard metrics projection for UI cards.

- `kpiSeriesByType: (state) => (metricKey) => state.kpiSeriesByMetric[metricKey] || []`

- `isScopeFresh: (state) => (scope, ttlMs) => boolean`  
  - Generic TTL freshness helper using `lastFetched`.

- `isAuditsFresh`  
  - Specialized freshness getter for audit list.

- `hasAnyError` / `errorForScope: (state) => (scope) => state.errorByScope[scope]`

- `isAnyMutationInProgress`  
  - `true` if any `mutationStatus` flag is active.

---

## 10. Recommended Actions

### 10.1 Audit list/detail and shared context

- `fetchAudits({ scope = 'all', filters = {}, force = false, ttlMs })`  
  - Loads list(s) and hydrates `audits` + `auditsByScope`.

- `fetchAuditDetails(auditId, { force = false, ttlMs })`  
  - Loads and caches detail payload per audit.

- `setSelectedAudit(auditId)` / `clearSelectedAudit()`

### 10.2 Review workflow actions

- `fetchReviewQueue({ filters = {}, force = false, ttlMs })`  
  - Reviewer/review queue fetch with query snapshot.

- `fetchReviewerTasks(auditId, { force = false, ttlMs })`  
  - Task items for a given audit.

- `saveReviewProgress(auditId, payload)`  
  - Saves in-progress review draft and refreshes relevant caches.

- `submitReviewStatus(auditId, payload)`  
  - Final status action (approve/reject/rework), invalidates queue + detail.

- `assignAudit(payload)`  
  - Assignment workflow; refreshes list and queue scopes.

### 10.3 Report workflow actions

- `fetchReports({ filters = {}, force = false, ttlMs })`  
  - Report table/list loader.

- `fetchReportsForAudit(auditId, { force = false, ttlMs })`

- `generateReport(auditId, payload)`  
  - Triggers report generation, tracks job status, refreshes report scopes.

- `fetchReportDownloadLink(reportId, { force = false })`

### 10.4 Lookup and AI-audit actions

- `fetchLookups({ force = false })`  
  - Loads business units/reviewer users/framework/category lookups.

- `fetchAiAuditSummary(auditId, { force = false, ttlMs })`

- `fetchAiAuditJobs(auditId, { force = false })`

- `uploadAiAuditDocument(auditId, formData)`  
  - Handles upload state and updates audit AI documents.

- `fetchAiAuditResults(auditId, { force = false })`

- `runRelevanceCheck(auditId, payload)`

### 10.5 Dashboard/KPI actions

- `fetchDashboardMetrics({ filters = {}, force = false, ttlMs })`  
  - Loads dashboard cards and aggregates.

- `fetchKpiMetrics({ filters = {}, force = false, ttlMs })`  
  - Loads KPI payload and computes `kpiSeriesByMetric`.

- `refreshAnalytics()`  
  - Combined dashboard + KPI refresh helper.

### 10.6 Utility and lifecycle actions

- `prefetchAuditDomain({ includeReviews = true, includeReports = true, force = false })`  
  - Replaces `window.auditorDataFetchPromise`; centralized prefetch with de-dupe.

- `invalidateAuditCache(scopeOrScopes)`  
  - Scope-level invalidation (`audits`, `reviews`, `reports`, `lookups`, `aiAudit`, `dashboard`, `kpi`).

- `setScopeError(scope, error)` / `clearScopeError(scope)`

- `withRequestDedup(requestKey, executor)`  
  - Internal helper using `inFlightRequests`.

- `resetAuditState({ keepLookups = true } = {})`  
  - Clear module state on logout/tenant switch.

---

## 11. Cache-first Implementation Plan

Use Pinia-first logic:
1. return cache if fresh (`lastFetched` + TTL),
2. use `isRefreshing` when stale-but-present,
3. use `isLoading` when empty,
4. allow `force` refresh,
5. invalidate on assign/create/review-submit/report-generate as needed.

Suggested TTL:
- audits/reviews: 30–90 sec
- dashboard/kpi: 1–5 min
- business units: 15–30 min
- audit detail: 30–60 sec (or force after mutation)

---

## 12. Repeated API Calls / Patterns to Fix

| Repeated pattern | Current files | Problem | Pinia fix |
|---|---|---|---|
| `window.auditorDataFetchPromise` + `auditorDataService.fetchAllAuditorData()` | `AIAuditDocumentUpload.vue`, integrations in `AssignAudit.vue` | global mutable flow outside Pinia | `auditStore.prefetchAuditDomain()` with internal de-dupe |
| Repeated dashboard metric API calls in component | `UserDashboard.vue` | duplicated query assembly/state handling | `auditStore.fetchDashboardMetrics` |
| Repeated report fetch/generate calls | `AuditReport.vue`, `AuditReportView.vue`, `AuditReportsView.vue` | fragmented error/loading/caching | `auditStore` report actions |
| Repeated review progress submit logic | `ReviewTaskView.vue` | duplicate submit/status handling | centralized action + retry/error wrapper |

---

## 13. Prop Drilling Analysis

No major deep prop-drilling hotspot is dominant; biggest issue is orchestration duplication and mixed cache ownership.

---

## 14. Forms Analysis

### Assign Audit form (`AssignAudit.vue`)
- Keep raw form inputs local.
- Move shared lookups (audits, frameworks/policies scope lists, business units) to store actions.
- Move submission side effects/invalidation to store.

### Review forms (`ReviewTaskView.vue`)
- Keep comment/checkbox local until submit.
- submit/restore progress via store action.

---

## 15. Tables / Filters / Pagination

- Keep table-only UI state local unless reused across routes.
- Server-side filters should be action parameters.
- Persist only if user experience needs cross-navigation memory.

---

## 16. Dashboard / Chart Plan

- `UserDashboard.vue` currently already touches Pinia (`dashboardsStore`, `appDataStore`).
- Introduce `auditStore` as single fetch orchestrator and push cached summary into `dashboardsStore`.
- Keep visualization-local settings (selected chart tab) local.

---

## 17. RBAC / Permission Plan

- Keep route-level `requiresPermission` checks.
- Add/extend permission store/composable with `can(permissionName)` for component-level controls.
- Reduce direct role-string branching in components.

---

## 18. Async UI Improvement Plan

- Standardize loading states (`isLoading` vs `isRefreshing`)
- Add retry for key API failures (reviews/reports/dashboard)
- Prevent duplicate submits for review actions and assignment creation
- Maintain clear empty states for no audits/no reports

---

## 19. Optimistic UI Possibilities

Use cautiously:
- UI-only toggles

Avoid optimistic updates for:
- review status submissions
- assignment creation
- audit report generation final-state transitions

---

## 20. Smart vs Presentational Plan

Priority smart/container candidates:
- `AssignAudit.vue`
- `AIAuditDocumentUpload.vue`
- `Reviewer.vue` / `ReviewTaskView.vue`
- `AuditReport.vue`
- `UserDashboard.vue`

Presentational components should only render props + emit events.

---

## 21. State Normalization Recommendations

If list size and mutation complexity grow:
- `auditsById`
- `auditIdsByScope`
- `reportsByAuditId`
- `reviewItemsByAuditId`

Do not over-normalize first pass.

---

## 22. What / Where / Why Plan

### Improvement 1
**What:** Create `auditStore` and centralize shared audit data/actions.  
**Where:** `src/stores/audit.js`, consumed by all routes in sidebar auditor section.  
**Why:** Remove duplicate component-level orchestration and keep audit state consistent.  
**Priority:** High.

### Improvement 2
**What:** Remove `window.auditorDataFetchPromise` usage.  
**Where:** `AIAuditDocumentUpload.vue` and other components using service-global promise.  
**Why:** Avoid global mutable state and improve testability/traceability in Pinia DevTools.  
**Priority:** High.

### Improvement 3
**What:** Consolidate dashboard metric calls into store actions, cache in `dashboardsStore`.  
**Where:** `UserDashboard.vue`, possibly `PerformanceAnalysis` children.  
**Why:** Faster revisit, less repeated API traffic, uniform loading/error behavior.  
**Priority:** High.

### Improvement 4
**What:** Keep form/modal/table UI state local.  
**Where:** Assign/review/report pages.  
**Why:** Avoid unnecessary global-state complexity.  
**Priority:** Medium.

---

## 23. File-by-file Migration Plan (Sidebar-focused)

| File | Current issue | Change needed | Priority |
|---|---|---|---|
| `AssignAudit.vue` | heavy API orchestration local | use `auditStore` fetch + submit actions | High |
| `AIAuditDocumentUpload.vue` | very large state + global promise cache pattern | split into store/composable + remove `window.*` | High |
| `Reviewer.vue` / `ReviewTaskView.vue` | review progress/status calls local | centralized review actions | High |
| `AuditReport.vue` / `AuditReportView.vue` / `AuditReportsView.vue` | report API logic spread across files | report actions in store | High |
| `UserDashboard.vue` | mixed local + appData + dashboards | route fetch orchestration through `auditStore` | High |
| `AuditorDashboard.vue` / `Audits.vue` | potential repeated list fetch logic | reuse `fetchAudits` | Medium |

---

## 24. Step-by-step Implementation Plan

1. Create `auditStore` with base state and status fields.
2. Add cache-first actions for audits/reviews/reports/dashboard.
3. Migrate `UserDashboard.vue` to store-driven fetch.
4. Migrate `AssignAudit.vue` lookup + submit flows.
5. Migrate reviewer pages (`Reviewer.vue`, `ReviewTaskView.vue`).
6. Migrate report pages.
7. Remove `window.auditorDataFetchPromise` usage.
8. Add invalidation hooks post-submit/update.
9. Validate RBAC guard + component permission checks.
10. Remove dead/duplicate fetch code.

---

## 25. Testing Checklist

- [ ] All sidebar auditor routes load correctly
- [ ] Shared audits list remains consistent across pages
- [ ] Cache-first logic works and avoids duplicate calls
- [ ] Force refresh bypasses cache
- [ ] Loading/refresh/error/empty states render correctly
- [ ] Assign audit flow updates downstream review/report pages correctly
- [ ] Review submit updates status and queue correctly
- [ ] Report generation/download works after store migration
- [ ] Permission gates still enforce expected access
- [ ] Pinia DevTools show expected state transitions

---

## 26. Priority Matrix

- **High:** `auditStore`, remove `window.*` promise pattern, migrate dashboard/assign/review/report core flows
- **Medium:** normalization and component split refinements
- **Low:** minor UI state persistence preferences

---

## 27. Final Developer Guidelines

1. Keep local UI states local.
2. Move shared audit server data to Pinia actions/state.
3. Avoid global `window.*` fetch coordination.
4. Use getters for derived counts and selected entities.
5. Use actions for API calls + invalidation.
6. Keep route guards and unify component permissions through helper/store.
7. Start refactor with `auditStore` + `UserDashboard.vue` and `AssignAudit.vue`.
8. Verify checklist before moving to next module.

