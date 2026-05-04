# Incident Module — Pinia State Management Audit & Migration Plan

**Scope requested:** Incident section in `grc_frontend/src/components/Policy/Sidebar.vue` (lines 242–294).  
**Frontend scope analyzed:** `grc_frontend/src/components/Incident/` + related routes in `src/router/index.js`.  
**Backend context scope:** `grc_backend/grc/routes/Incident/`.

---

## 1. Page/Module Summary

### 1.1 What this module does

The Incident module (from sidebar lines 242–294) supports:

- Incident list and detail management
- Create incident workflow
- Audit findings list + detail in incident context
- Incident user-task handling workflow
- AI import for incidents
- Incident KPI analysis and dashboard/performance analysis

### 1.2 Sidebar routes → pages

| Sidebar label | Route | Component |
|---|---|---|
| Incident List | `/incident/incident` | `Incident.vue` |
| Create Incident | `/incident/create` | `CreateIncident.vue` |
| Audit Findings | `/incident/audit-findings` | `AuditFindings.vue` |
| Incident Handling | `/incident/user-tasks` | `IncidentUserTasks.vue` |
| Incident AI Import | `/incident/ai-import` | `incident_ai_import.vue` |
| KPIs Analysis | `/incident/dashboard` | `IncidentDashboard.vue` |
| Dashboard | `/incident/performance/dashboard` | `IncidentPerformanceDashboard.vue` |

### 1.3 Additional connected routes

- `/incident/:id` → `IncidentDetails.vue`
- `/incident/audit-finding-details/:id` → `AuditFindingDetails.vue`

### 1.4 Parent layout

- Route-level pages loaded via `App.vue` + `Sidebar.vue` shell.

### 1.5 Workflow category mapping

- Incident management
- Audit-finding linked incident flow
- Reviewer/task workflow
- Dashboard/KPI analytics
- AI-assisted import/analysis

---

## 2. Current Vue Implementation Summary

### 2.1 API style

Mixed Options API and setup-style files across incident components.

### 2.2 Existing Pinia usage

- `IncidentPerformanceDashboard.vue` uses `useDashboardsStore` and `useAppDataStore`.
- No dedicated `incidentStore` currently.

### 2.3 Existing non-Pinia cache pattern

- `src/services/incidentService.js` provides centralized in-memory data cache.
- Multiple incident pages use `window.incidentDataFetchPromise` + `incidentService.fetchAllIncidentData()`.
- Similar architecture pattern as policy/compliance/auditor modules before migration.

### 2.4 API orchestration pattern

- Heavy component-level API calls through `apiService` + `API_ENDPOINTS`.
- Significant analytics and chart logic embedded directly in dashboard components.

### 2.5 RBAC and access handling

- `CreateIncident.vue` and `IncidentPerformanceDashboard.vue` use `AccessUtils` for permission/error handling.
- Permission checks are not fully centralized in a store/helper pattern.

---

## 3. Current Data Flow

1. Route loads incident page.
2. Page calls API directly or tries `incidentService` cache first.
3. Some pages initialize/await `window.incidentDataFetchPromise`.
4. List/detail/task/dashboard state kept mostly local to each page.
5. Mutations trigger local refreshes without unified invalidation lifecycle.

### Current risks

- Duplicate API calls across incident pages
- Global `window.*` promise coordination outside Pinia
- Potential stale mismatch between incident list/tasks/dashboard/audit-findings views

---

## 4. Variable Inventory (Grouped)

| Variable group | Examples | Type | Keep local | Move to Pinia |
|---|---|---|---|---|
| Incident collections | incidents, audit findings, task queues | shared API data | No | Yes |
| Lookup data | users, business units, categories, frameworks | shared API data | No | Yes |
| Dashboard chart payloads | counts, MTTR/MTTD/MTTC metrics, chart series | shared API data | No | Yes |
| Task form inputs | comments, assessments, selected task flags | local form state | Yes | No |
| Modal/dropdown states | visibility, expanded row flags | local UI state | Yes | No |
| AI import transient UI | upload progress, local parsing states | local UI + process state | mostly local | partial shared by audit trail/job metadata |

---

## 5. State Classification

### 5.1 Keep local

- Modal visibility
- Inline form validation
- Small action loading states
- Table UI-only preferences

### 5.2 Move to Pinia

- Shared incident/audit-finding datasets
- Reviewer/user task queues
- Shared lookup lists (users/business units/categories/frameworks)
- Dashboard/KPI summary + derived chart source data

### 5.3 API/server data via Pinia actions

- Incidents list/detail
- Audit findings list/detail (incident-linked)
- Incident task and mitigation/review datasets
- Dashboard/KPI endpoints

---

## 6. API Call Inventory (Major families)

Observed across incident pages:

- Incident CRUD/list/detail (`INCIDENT_CREATE`, `INCIDENT_INCIDENTS`, `/incident/:id`)
- Audit findings (`AUDIT_FINDINGS`, audit-finding detail/review data/mitigations endpoints)
- User tasks (`INCIDENT_REVIEWER_TASKS`, `AUDIT_FINDING_REVIEWER_TASKS`, user incidents/findings)
- Assessment/review submit endpoints
- Lookup endpoints (`BUSINESS_UNITS`, categories, users, compliances)
- Dashboard and KPI analytics (`INCIDENT_*` metrics, `/api/incidents/dashboard/`, `/dashboard/analytics/`)
- AI import related endpoints (`incident_ai_import.vue`)

Recommendation: centralize reusable API families inside `incidentStore` actions.

---

## 7. Recommended Pinia Stores

### 7.1 `incidentStore` (new, primary)

Suggested path: `src/stores/incident.js`

**Purpose:** single shared state for incident module pages in sidebar scope.

**State fields:** see detailed section in **Section 8** (source blueprint for implementation)

### 7.2 `dashboardsStore` (existing)

- Continue using `incident` slice for cached dashboard summary.
- Make `incidentStore` the orchestrator that writes to it.

### 7.3 `appDataStore` (existing)

- `fetchIncidents()` currently uses `incidentDataService`.
- Align to one orchestration source (either appData delegates to incidentStore or incidentStore delegates to appData, but avoid parallel ownership).

---

## 8. Recommended State Design

```js
state: () => ({
  // Primary incident datasets
  incidents: [],                              // list view payload
  incidentDetailsById: {},                    // incidentId -> details
  incidentsByStatus: {
    open: [],
    inProgress: [],
    resolved: [],
    closed: []
  },

  // Audit-finding linkage and task workflows
  auditFindings: {
    list: [],
    byId: {},
    idsByIncidentId: {},                      // incidentId -> findingId[]
    detailsById: {}
  },
  userTasks: {
    list: [],                                 // mixed tasks list
    byUserId: {},                             // userId -> task[]
    byIncidentId: {},                         // incidentId -> task[]
    summary: null,                            // pending/completed breakdown
    lastQuery: null
  },

  // Shared lookups consumed by create/tasks/filters
  lookups: {
    users: [],
    businessUnits: [],
    categories: [],
    frameworks: [],
    compliances: [],
    severities: [],
    priorities: []
  },

  // Selection/context state
  selectedIncidentId: null,
  selectedFindingId: null,
  selectedTaskId: null,

  // AI import/process data
  aiImport: {
    jobs: [],                                 // active/recent import jobs
    jobById: {},                              // jobId -> job details
    resultsByJobId: {},                       // jobId -> parsed incidents/findings
    importHistory: []                         // audit trail/history
  },

  // Dashboard/KPI analytics
  dashboard: {
    summary: null,                            // cards/high-level counts
    charts: {},                               // raw chart payloads
    analytics: null,                          // advanced analytics endpoint payload
    filters: null                             // persisted dashboard-level filters
  },
  kpiSeriesByMetric: {},                      // transformed chart series map

  // Button-level mutation loaders
  mutationStatus: {
    createIncident: false,
    updateIncident: false,
    submitAssessment: false,
    completeReview: false,
    aiImportUpload: false
  },

  // Generic async and scoped error state
  status: 'idle', // idle | loading | success | error
  isLoading: false,
  isRefreshing: false,
  error: null,
  errorByScope: {
    incidents: null,
    findings: null,
    tasks: null,
    lookups: null,
    aiImport: null,
    dashboard: null,
    analytics: null
  },

  // TTL timestamps and in-flight request de-duplication
  lastFetched: {
    incidents: null,
    incidentDetails: {},
    findings: null,
    tasks: null,
    lookups: null,
    dashboard: null,
    analytics: null,
    aiImport: null
  },
  inFlightRequests: {}                        // requestKey -> Promise
})
```

---

## 9. Recommended Getters

- `incidentById: (state) => (id) => state.incidentDetailsById[id] || null`

- `selectedIncident`  
  - Returns selected incident detail by `selectedIncidentId`.

- `auditFindingById: (state) => (id) => state.auditFindings.byId[id] || null`

- `findingsForIncident: (state) => (incidentId) => { ... }`  
  - Resolves finding list via `idsByIncidentId`.

- `tasksForUser: (state) => (userId) => state.userTasks.byUserId[userId] || []`

- `tasksForIncident: (state) => (incidentId) => state.userTasks.byIncidentId[incidentId] || []`

- `pendingTasksCount`  
  - Derived pending task count from `userTasks.list`.

- `incidentCountByStatus`  
  - Grouped counts for open/in-progress/resolved/closed.

- `incidentsByStatusView: (state) => (status) => state.incidentsByStatus[status] || []`

- `dashboardKpiCards`  
  - Normalized dashboard card projection.

- `chartDataByType: (state) => (type) => state.dashboard.charts[type] || []`

- `kpiSeriesByType: (state) => (metricKey) => state.kpiSeriesByMetric[metricKey] || []`

- `latestAiImportJobs`  
  - Recent AI import jobs sorted by updated time.

- `isScopeFresh: (state) => (scope, ttlMs) => boolean`  
  - Generic TTL helper from `lastFetched`.

- `isIncidentsFresh`  
  - Specialized freshness getter for incident list.

- `hasAnyError` / `errorForScope: (state) => (scope) => state.errorByScope[scope]`

- `isAnyMutationInProgress`  
  - `true` when any flag in `mutationStatus` is active.

---

## 10. Recommended Actions

### 10.1 Core incidents and details

- `fetchIncidents({ filters = {}, force = false, ttlMs })`  
  - Loads incident list and hydrates status buckets.

- `fetchIncidentDetails(id, { force = false, ttlMs })`

- `setSelectedIncident(id)` / `clearSelectedIncident()`

- `createIncident(payload)`  
  - Creates incident, invalidates list/dashboard scopes.

- `updateIncident(id, payload)`  
  - Updates detail/list caches with reconciliation.

### 10.2 Findings and task workflow

- `fetchAuditFindings({ filters = {}, force = false, ttlMs })`

- `fetchAuditFindingDetails(id, { force = false, ttlMs })`

- `fetchUserTasks({ userId, filters = {}, force = false, ttlMs })`  
  - Loads reviewer/user incident tasks and stores query snapshot.

- `submitIncidentAssessment(payload)`  
  - Submits assessment and refreshes affected task/finding scopes.

- `completeIncidentReview(payload)`  
  - Completes workflow step and invalidates dependent views.

### 10.3 Shared lookups

- `fetchLookups({ force = false })`  
  - Loads users/business units/categories/frameworks/compliances/priorities.

- `fetchIncidentUsers({ force = false })`  
  - Optional split action when users endpoint is heavy.

### 10.4 Dashboard and analytics

- `fetchDashboardSummary({ filters = {}, force = false, ttlMs })`

- `fetchDashboardCharts({ filters = {}, force = false, ttlMs })`

- `fetchDashboardAnalytics({ filters = {}, force = false, ttlMs })`  
  - For advanced KPI/analytics endpoints.

- `refreshIncidentAnalytics()`  
  - Combined dashboard/charts/analytics refresh helper.

### 10.5 AI import actions

- `fetchAiImportJobs({ force = false, ttlMs })`

- `startAiImport(formData)`  
  - Upload/import trigger action.

- `fetchAiImportJobStatus(jobId, { force = false })`

- `fetchAiImportResults(jobId, { force = false })`

### 10.6 Utility and lifecycle

- `prefetchIncidentDomain({ includeIncidents = true, includeFindings = true, includeTasks = true, force = false })`  
  - Replaces `window.incidentDataFetchPromise` with store-level de-dupe orchestration.

- `invalidateIncidentCache(scopeOrScopes)`  
  - Supports scopes: `incidents`, `findings`, `tasks`, `lookups`, `dashboard`, `analytics`, `aiImport`.

- `setScopeError(scope, error)` / `clearScopeError(scope)`

- `withRequestDedup(requestKey, executor)`  
  - Internal helper using `inFlightRequests`.

- `resetIncidentState({ keepLookups = true } = {})`

---

## 11. Cache-first Implementation Plan

Pinia-first approach:
1. Check existing store data.
2. Validate `lastFetched` against TTL.
3. Fresh: return cached.
4. Stale-but-present: `isRefreshing = true`, show old data.
5. Empty: `isLoading = true`.
6. On success: update data + timestamp.
7. On failure: keep old data if present + set `error`.
8. Force refresh support via `force: true`.

Suggested TTL:
- incidents/findings/tasks: 30–90 sec
- dashboard/kpi: 1–5 min
- lookup data: 15–30 min

---

## 12. Repeated API Calls / Patterns to Fix

| Repeated pattern | Current files | Problem | Pinia action |
|---|---|---|---|
| `window.incidentDataFetchPromise` + `incidentService.fetchAllIncidentData()` | `IncidentDashboard.vue`, `IncidentPerformanceDashboard.vue`, `IncidentUserTasks.vue` | global mutable pattern outside store | `incidentStore.prefetchIncidentDomain` |
| Dashboard metric calls and analytics split in component | `IncidentDashboard.vue`, `IncidentPerformanceDashboard.vue` | duplicated filter/query handling | `fetchDashboardSummary` + `fetchDashboardCharts` |
| User task + findings combined fetch logic repeated | `IncidentUserTasks.vue` | complex orchestration in view layer | `fetchUserTasks` action family |
| Lookup data fetching (users/categories/business units/frameworks) | `CreateIncident.vue` and others | repeated retrieval and error handling | `fetchLookups` |

---

## 13. Prop Drilling Analysis

Major issue is data orchestration duplication, not deep prop drilling.
Local prop chains are acceptable; prioritize store consistency first.

---

## 14. Forms Analysis

### Create Incident form (`CreateIncident.vue`)
- Keep form inputs local.
- Move shared dropdown data + submission side-effects to store actions.

### Incident task assessment forms (`IncidentUserTasks.vue`)
- Keep transient comments/assessment inputs local.
- Centralize submit and refresh/invalidation in store.

---

## 15. Tables / Filters / Pagination

- Keep table-only state local by default.
- Move to store only if filters must persist across routes/widgets.
- Use action params for server-side filter/search/pagination.

---

## 16. Dashboard and Chart State Plan

- Use `incidentStore` to fetch KPI/analytics and write final dashboard summary into `dashboardsStore` (`incident` domain).
- Remove direct dependency on `window.incidentDataFetchPromise`.
- Keep chart rendering-only preferences local to dashboard components.

---

## 17. RBAC/Permission Plan

- Keep route-level guards.
- Consolidate component-level checks with permission helper/store (`can(permissionName)`).
- Continue `AccessUtils` for standard error handling until permission store rollout is complete.

---

## 18. Async UI Improvement Plan

- Distinguish `isLoading` vs `isRefreshing`.
- Add consistent retry states for task and dashboard APIs.
- Ensure duplicate-submit prevention for assessment/review completion.
- Add standard empty states for no incidents/no findings/no tasks.

---

## 19. Optimistic UI Possibilities

Safe:
- minor UI toggles/preferences

Avoid optimistic:
- incident assessment submission
- review completion
- incident create/edit operations with workflow impact

---

## 20. Smart vs Presentational Plan

Priority smart/container candidates:
- `IncidentUserTasks.vue`
- `IncidentDashboard.vue`
- `IncidentPerformanceDashboard.vue`
- `CreateIncident.vue`
- `incident_ai_import.vue`

Presentational children should only render props and emit events.

---

## 21. State Normalization Recommendations

If data volume grows:
- `incidentsById`
- `incidentIdsByStatus`
- `auditFindingsById`
- `taskIdsByUserId`

Start with simpler shape first; optimize after behavior stabilizes.

---

## 22. What / Where / Why Plan

### Improvement 1
**What:** Introduce `incidentStore` for shared incident module state and API actions.  
**Where:** `src/stores/incident.js` + all incident sidebar route pages.  
**Why:** Single source of truth; reduced repeated API calls.  
**Priority:** High.

### Improvement 2
**What:** Replace `window.incidentDataFetchPromise` usage with store-level de-dupe.  
**Where:** `IncidentDashboard.vue`, `IncidentPerformanceDashboard.vue`, `IncidentUserTasks.vue`.  
**Why:** Avoid global mutable state and improve reliability/debugging.  
**Priority:** High.

### Improvement 3
**What:** Centralize dashboard and KPI analytics fetches into store actions and cache summary in `dashboardsStore`.  
**Where:** `IncidentDashboard.vue`, `IncidentPerformanceDashboard.vue`.  
**Why:** Consistent loading/error/cache behavior and fewer duplicate requests.  
**Priority:** High.

### Improvement 4
**What:** Keep form and modal states local, move shared lookups into store.  
**Where:** `CreateIncident.vue`, `IncidentUserTasks.vue`.  
**Why:** Balanced architecture: simple local UI, centralized shared data.  
**Priority:** Medium.

---

## 23. File-by-file Migration Plan (sidebar-focused)

| File | Current problem | Change needed | Priority |
|---|---|---|---|
| `Incident.vue` | local list orchestration | consume `incidentStore.fetchIncidents` | High |
| `CreateIncident.vue` | lookup + create orchestration local | move lookups/mutation side-effects to store actions | High |
| `AuditFindings.vue` | findings fetch local | use `incidentStore.fetchAuditFindings` | High |
| `IncidentUserTasks.vue` | heavy task/finding orchestration + global fetch promise | centralized task actions + invalidate flows | High |
| `incident_ai_import.vue` | likely local-heavy import orchestration | split shared fetches into store/composable | Medium |
| `IncidentDashboard.vue` | repeated KPI fetching + global promise pattern | dashboard actions in store | High |
| `IncidentPerformanceDashboard.vue` | mixed dashboardsStore + incidentService + window promise | store-first orchestration, dashboardsStore as cache sink | High |

---

## 24. Step-by-step Implementation Plan

1. Create `incidentStore` with status/TTL/cache fields.
2. Add fetch actions for incidents/findings/tasks/lookups.
3. Migrate dashboard pages to store-driven fetch.
4. Migrate task page (`IncidentUserTasks.vue`) orchestration.
5. Migrate create/list/findings pages.
6. Remove `window.incidentDataFetchPromise` usage.
7. Add mutation invalidation and force-refresh hooks.
8. Verify RBAC and error handling consistency.
9. Cleanup duplicate local fetch logic.
10. Final regression across all incident routes.

---

## 25. Testing Checklist

- [ ] All sidebar incident routes load correctly
- [ ] Incident list/detail consistency after create/update
- [ ] User tasks reflect latest assessment/review changes
- [ ] Audit findings data consistent across list/detail/task views
- [ ] Dashboard/KPI cache-first behavior works
- [ ] Force refresh works
- [ ] Loading/refresh/error/empty states are correct
- [ ] No duplicate API bursts from multiple pages
- [ ] Permission-denied paths handled correctly
- [ ] Pinia DevTools state transitions are as expected

---

## 26. Priority Matrix

- **High:** incidentStore creation, removal of `window.*` promise pattern, dashboard/task centralization
- **Medium:** AI import shared state extraction, optional normalization
- **Low:** minor UI-state persistence improvements

---

## 27. Final Developer Guidelines

1. Keep component-only UI/form state local.
2. Move shared incident server data to Pinia actions/state.
3. Eliminate global `window.incidentDataFetchPromise`.
4. Use getters for reusable derived counts/charts.
5. Use actions for all incident API orchestration and invalidation.
6. Keep route guards and centralize component-level permission checks.
7. Start implementation with `incidentStore` + dashboard/task pages.
8. Validate full checklist before moving to next module.

