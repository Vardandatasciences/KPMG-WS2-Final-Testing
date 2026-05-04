# Policy Module — Pinia State Management Audit & Migration Plan

**Scope requested:** Policy section in `grc_frontend/src/components/Policy/Sidebar.vue` (lines 22–111) and related route pages.  
**Primary frontend scope:** `grc_frontend/src/components/Policy/` + policy-related route targets from `src/router/index.js`.  
**Backend context scope:** `grc_backend/grc/routes/Policy/`.

---

## 1) Page/Module Summary

### 1.1 Module purpose

The Policy module (as represented by sidebar lines 22–111) supports:

- Policy creation lifecycle (manual create, AI upload, tailoring, versioning)
- Framework explorer and domain mapping
- Policy + framework approvals and status-change workflows
- Policy performance analytics (KPI + user dashboard)
- Data workflow tree view

### 1.2 Routes used by the sidebar section

| Sidebar item | Route | Component |
|---|---|---|
| Create New Policy | `/create-policy/create` | `CreatePolicy.vue` |
| AI Policy Creation | `/create-policy/upload-framework` | `UploadFramework.vue` |
| Tailoring & Templating | `/create-policy/tailoring` | `TT.vue` |
| Versioning | `/create-policy/versioning` | `VV.vue` |
| Framework Explorer | `/framework-explorer` | `FrameworkExplorer.vue` |
| Domains | `/domains` | `../Login/domian.vue` |
| Policy Approval | `/policy/approval` | `PolicyApprover.vue` |
| Framework Approval | `/framework-approval` | `../Framework/FrameworkApprover.vue` |
| Status Change Requests | `/framework-status-changes` | `StatusChangeRequests.vue` |
| Data Workflow | `/policy/data-workflow` | `../DataWorkflow/DataWorkflowTree.vue` |
| KPIs Analysis | `/policy/performance/kpis` | `KPIDashboard.vue` |
| User Dashboard | `/policy/performance/dashboard` | `PolicyDashboard.vue` |

### 1.3 Parent layout

- Main shell: `src/App.vue` with `Sidebar.vue` + `<router-view>`.
- Policy pages are route-level views, not children of a dedicated policy layout wrapper.

### 1.4 Workflow type mapping

- **Framework + policy + sub-policy**
- **Approval / reviewer workflow**
- **Dashboard / KPI**
- **RBAC-sensitive operations**
- **Notification side-effects** (push notifications on approval/status flows)

---

## 2) Current Vue.js Implementation Summary

### 2.1 API style

Mixed:
- `script setup`: `FrameworkExplorer.vue`, `FrameworkPolicies.vue`, `AllPolicies.vue`, `StatusChangeRequests.vue`, `TreePolicies.vue`
- Options API / classic `<script>`: `CreatePolicy.vue`, `TT.vue`, `VV.vue`, `PolicyApprover.vue`, `PolicyDashboard.vue`, `KPIDashboard.vue`, etc.

### 2.2 State primitives currently used

- `ref`, `computed`, `watch` in setup pages
- `data`, `computed`, watchers/methods in options pages
- Props/emits used in modal/child components

### 2.3 Existing Pinia usage

- `useFrameworkStore` used in some policy pages (`CreatePolicy.vue`, `PolicyDashboard.vue`, `Sidebar.vue`)
- `useDashboardsStore` and `useAppDataStore` used in `PolicyDashboard.vue`
- No dedicated `policyStore` yet

### 2.4 Existing service-layer caching (outside Pinia)

- `src/services/policyService.js` maintains an in-memory cache
- Repeated pattern in many pages:
  - `window.policyDataFetchPromise`
  - `policyDataService.fetchAllPolicyData()`
- This is functional but creates **global mutable state outside Pinia**

### 2.5 API call patterns

- Heavy direct page-level API usage via `apiService` and `API_ENDPOINTS`
- Multiple pages call `FRAMEWORK_GET_SELECTED` / `FRAMEWORK_SET_SELECTED` separately

### 2.6 Permissions / RBAC patterns

- Router meta permissions exist for key policy routes (`create_policy`, `approve_policy`, `view_all_policy`)
- Pages still perform direct role calls (`API_ENDPOINTS.USER_ROLE`) and role branching
- Needs centralization via store helper/composable for consistency

---

## 3) Current Data Flow (Policy sidebar module)

1. Route mount in a policy page.
2. Page checks selected framework via backend session endpoint and/or local state.
3. Page fetches framework/policy/subpolicy/summary data directly.
4. Some pages use `policyDataService` cached values first.
5. Mutations (create/update/status/approval) refresh local data ad hoc.

### Current risks

- Duplicate framework/session fetches across pages
- Multiple data sources: component local state vs `policyDataService` vs `appDataStore`
- Potential stale mismatch after mutation

---

## 4) Variable Inventory (high-impact grouped)

| Variable group | Typical examples | Classification | Keep local? | Move to Pinia? |
|---|---|---|---|---|
| Framework context | `selectedFrameworkId`, `selectedFrameworkName` | Shared state | No | Yes (`frameworkStore`) |
| Hierarchy lists | frameworks/policies/subpolicies arrays | API shared data | No | Yes (`policyStore`) |
| Dashboard data | cards/charts summary payloads | API shared data | No | Yes (`dashboardsStore` + `policyStore`) |
| Approval queues | reviewer/user lists and filters | Shared workflow data | Partly | Yes |
| Form fields | Create/TT/VV form models | Local UI/form state | Yes | No (unless draft-resume needed) |
| Modals/dropdowns | open/close flags | Local UI | Yes | No |
| Table-only state | sort, visible columns, local search | Local UI | Yes | No unless cross-page persistence required |

---

## 5) State Classification

### 5.1 Keep local (`ref`/`reactive`)

- Modal visibility
- Inline validation state
- Single-view filter chips
- Column chooser
- Temporary tailoring/versioning form input buffers

### 5.2 Move to shared Pinia

- Selected framework context (single source of truth)
- Shared policy data cache used by explorer/approver/dashboard/kpi/data workflow
- Approval task datasets reused across pages

### 5.3 API server data in Pinia actions

- Framework explorer datasets
- Policy and subpolicy lists by framework/version
- Policy dashboard and KPI summaries
- Status-change requests and approval queues

---

## 6) API Call Inventory (consolidated)

Common families used in this sidebar module pages:

- `API_ENDPOINTS.FRAMEWORK_GET_SELECTED` / `FRAMEWORK_SET_SELECTED`
- `API_ENDPOINTS.FRAMEWORKS`, `FRAMEWORK_EXPLORER`, framework details/policies
- Policy creation/update/tailoring/versioning endpoints in `CreatePolicy.vue`, `TT.vue`, `VV.vue`
- Approval and reviewer selection endpoints (`USERS_FOR_REVIEWER_SELECTION`, policy review submit)
- Dashboard/KPI endpoints (`POLICY_DASHBOARD_SUMMARY`, KPI stats)
- Status change / toggle endpoints (framework/policy status change in explorer/status pages)
- Notification endpoint (`PUSH_NOTIFICATION`)

Recommendation: route all reusable policy API calls through `policyStore` actions; keep component calls only for truly isolated one-off operations.

---

## 7) Recommended Pinia Stores (for this module)

### 7.1 `frameworkStore` (existing, mandatory usage)
- **Purpose:** selected framework session state
- **Action usage:** `loadFrameworkFromSession`, `setFramework`, `resetFramework`
- **Note:** eliminate repetitive per-page framework session logic

### 7.2 `policyStore` (new)
- **File:** `src/stores/policy.js`
- **Purpose:** policy domain shared state for sidebar routes
- **State fields:** see detailed section in **Section 8** (source blueprint for implementation)

### 7.3 `dashboardsStore` (existing)
- Keep as cache sink for `policy` dashboard summary payload.

### 7.4 `appDataStore` (existing)
- Already has `fetchPolicies` using `policyDataService`.
- Align architecture so `policyStore` and `appDataStore` do not diverge (one orchestrator pattern).

### 7.5 `permissionStore` (recommended)
- Central `can(permissionName)` checks for button/menu-level consistency.

---

## 8) Recommended State Design

```js
state: () => ({
  // Framework context snapshots for policy module views
  frameworksList: [],                  // list used by selectors/dropdowns
  selectedFrameworkSnapshot: null,     // optional details snapshot for quick UI reads

  // Explorer and hierarchy data
  explorer: {
    frameworks: [],                    // explorer table/list payload
    frameworkDetailsById: {},          // frameworkId -> details payload
    summary: null,                     // explorer summary cards
    lastQuery: null                    // last explorer filters/sort/search params
  },

  hierarchy: {
    policiesByFrameworkId: {},         // frameworkId -> policy[]
    policyById: {},                    // policyId -> policy
    policyIdsByFrameworkId: {},        // frameworkId -> policyId[]
    subpoliciesByPolicyId: {},         // policyId -> subpolicy[]
    subpolicyById: {},                 // subpolicyId -> subpolicy
    subpolicyIdsByPolicyId: {}         // policyId -> subpolicyId[]
  },

  // Approval and review queues
  approvals: {
    reviewerItems: [],                 // approver's pending/processed queue
    userItems: [],                     // requester-side approval items
    selectedReviewers: [],             // shared reviewer pick list
    reviewerOptions: [],               // fetched users for reviewer assignment
    reviewSummary: null,               // counts by status/type
    lastQuery: null                    // mode + filter + pagination snapshot
  },

  // Status-change workflow
  statusRequests: [],                  // status change request list
  statusRequestsMeta: {
    total: 0,
    page: 1,
    pageSize: 10
  },

  // Dashboards / analytics
  dashboardSummary: null,              // policy dashboard aggregate payload
  dashboardWidgets: {},                // widget-level split cache if required
  kpiData: null,                       // KPI endpoint raw payload
  kpiSeriesByMetric: {},               // transformed chart-friendly series
  dashboardFilters: null,              // persisted cross-widget filter state

  // Operation-specific progress map for button-level loading UX
  mutationStatus: {
    createPolicy: false,
    updatePolicy: false,
    submitReview: false,
    requestStatusChange: false,
    toggleStatus: false
  },

  // Generic async and error state
  status: 'idle', // idle | loading | success | error
  isLoading: false,
  isRefreshing: false,
  error: null,
  errorByScope: {
    frameworks: null,
    explorer: null,
    hierarchy: null,
    approvals: null,
    statusRequests: null,
    dashboard: null,
    kpi: null
  },

  // Fetch metadata for TTL-based cache and de-dupe
  lastFetched: {
    frameworks: null,
    frameworkDetails: {},
    explorer: null,
    hierarchyByFramework: {},
    subpoliciesByPolicy: {},
    approvals: null,
    statusRequests: null,
    dashboard: null,
    kpi: null
  },
  inFlightRequests: {}                 // key -> Promise guard for de-duplication
})
```

---

## 9) Recommended Getters

- `activeFrameworkId`  
  - Read-through from `frameworkStore`; single source for framework-aware selectors.

- `activeFrameworkPolicies`  
  - Returns policies for current framework without repeating `frameworkId` in each component.

- `policiesForFramework: (state) => (frameworkId) => []`  
  - Parameterized getter for route views that are not bound to current framework context.

- `subpoliciesForPolicy: (state) => (policyId) => []`  
  - Used by tree/detail views.

- `policyById: (state) => (policyId) => state.hierarchy.policyById[policyId]`

- `subpolicyById: (state) => (subpolicyId) => state.hierarchy.subpolicyById[subpolicyId]`

- `reviewerQueue` / `requesterQueue`  
  - Pre-split queue accessors from `approvals.reviewerItems` and `approvals.userItems`.

- `pendingApprovalCount`  
  - Count of queue items with pending statuses.

- `approvalCountByStatus`  
  - Returns grouped counts (pending/approved/rejected/rework) for badges/cards.

- `statusRequestCount`  
  - Total status requests, either derived from list length or metadata total.

- `dashboardCards`  
  - Normalized cards projection consumed by `PolicyDashboard.vue`.

- `kpiSeriesByPolicy`  
  - Chart-ready transformed KPI series grouped by policy or metric type.

- `isScopeFresh: (state) => (scope, ttlMs) => boolean`  
  - Generic TTL check against `lastFetched[scope]`.

- `isFrameworksFresh`  
  - Specialized freshness getter for framework dropdown and explorer dependencies.

- `hasAnyError` / `errorForScope: (state) => (scope) => state.errorByScope[scope]`

- `isAnyMutationInProgress`  
  - `true` when any operation in `mutationStatus` is running.

---

## 10) Recommended Actions

### 10.1 Framework and explorer

- `fetchFrameworks({ force = false, ttlMs })`  
  - Loads framework list for selectors and explorer dependency.

- `fetchFrameworkDetails(frameworkId, { force = false, ttlMs })`  
  - Optional detailed framework payload cache.

- `fetchFrameworkExplorer({ params = {}, force = false, ttlMs })`  
  - Fetches explorer table/list + summary and stores `explorer.lastQuery`.

### 10.2 Policy hierarchy

- `fetchPoliciesByFramework(frameworkId, { force = false, ttlMs })`  
  - Fetches policy list, hydrates `policyById` + id map.

- `fetchSubpoliciesByPolicy(policyId, { force = false, ttlMs })`  
  - Fetches subpolicies and hydrates normalized maps.

- `prefetchPolicyDomain({ frameworkId, includeSubpolicies = true, force = false })`  
  - Replaces global promise pattern; orchestrates framework + hierarchy calls with de-dupe.

### 10.3 Policy mutations

- `createPolicy(payload)`  
  - Creates policy, then invalidates hierarchy/dashboard scopes.

- `updatePolicy(policyId, payload)`  
  - Updates policy and reconciles local normalized cache.

- `createSubpolicy(payload)` / `updateSubpolicy(subpolicyId, payload)`  
  - For hierarchy edits in create/tailoring/versioning flows.

- `deletePolicy(policyId)` / `deleteSubpolicy(subpolicyId)` (if supported by backend)

### 10.4 Approval and review flows

- `fetchApprovalQueue({ mode = 'reviewer', filters = {}, force = false, ttlMs })`  
  - Gets queue data for reviewer or requester mode.

- `fetchReviewerOptions({ force = false })`  
  - Loads users for reviewer assignment selectors.

- `assignReviewers({ policyId, reviewerIds })`  
  - Sends reviewer assignment and refreshes impacted queue/data.

- `submitPolicyReview(payload)`  
  - Approval/reject/rework action; includes post-success cache invalidation.

### 10.5 Status-change workflow

- `fetchStatusRequests({ filters = {}, force = false, ttlMs })`  
  - Loads status change requests list + metadata.

- `requestFrameworkStatusChange(payload)`  
  - Creates status-change request and refreshes requests.

- `toggleFrameworkStatus(payload)`  
  - Executes status change where backend allows direct toggle; invalidates explorer/hierarchy.

### 10.6 Dashboard and KPI

- `fetchPolicyDashboard({ filters = {}, force = false, ttlMs })`  
  - Loads dashboard summary + optional widget splits.

- `fetchPolicyKpi({ params = {}, force = false, ttlMs })`  
  - Loads KPI payload and computes `kpiSeriesByMetric`.

- `refreshAnalyticsForFramework(frameworkId)`  
  - Helper to refetch dashboard + KPI after major mutations.

### 10.7 Utilities and lifecycle

- `invalidatePolicyCache(scopeOrScopes)`  
  - Scope-level invalidation (`frameworks`, `explorer`, `hierarchy`, `approvals`, `statusRequests`, `dashboard`, `kpi`).

- `setScopeError(scope, error)` / `clearScopeError(scope)`  
  - Standardized error handling.

- `withRequestDedup(requestKey, executor)`  
  - Internal utility action using `inFlightRequests` map.

- `resetPolicyState({ keepFrameworks = false } = {})`  
  - Used on logout/module switch.

---

## 11) Cache-first Plan (Pinia-only)

For each fetch action:
1. Check store data exists.
2. Check `lastFetched[scope]`.
3. If fresh (TTL), return cached.
4. If stale and data exists, set `isRefreshing`.
5. If no data, set `isLoading`.
6. On success, update state + timestamp.
7. On failure, preserve stale data if any + set `error`.
8. Allow `force: true`.

Suggested TTL:
- Framework lists/explorer: 5–15 min
- Approvals/status requests: 30–60 sec
- Dashboard/KPI: 1–5 min

---

## 12) Repeated API Calls (high-value fixes)

| Repeated API | Current files | Problem | Recommended action |
|---|---|---|---|
| `FRAMEWORK_GET_SELECTED` / `FRAMEWORK_SET_SELECTED` | `PolicyDashboard`, `KPIDashboard`, `AllPolicies`, `FrameworkExplorer`, `TreePolicies`, `TT`, `VV`, etc. | repeated session sync logic | use `frameworkStore` everywhere |
| `policyDataService.fetchAllPolicyData` + `window.policyDataFetchPromise` | `AllPolicies`, `FrameworkExplorer`, `StatusChangeRequests`, `TreePolicies`, `PolicyApprover`, `TT`, `KPIDashboard` | global non-Pinia cache + duplication | move de-dupe and cache into `policyStore` |
| `USER_ROLE` checks | `PolicyApprover`, `PolicyDetails`, `CreatePolicy`, `TT`, `VV`, `StatusChangeRequests` | inconsistent role branching | central permission store/composable |

---

## 13) Prop Drilling Analysis

No severe deep prop drilling pattern is dominant.  
Main issue is **data-source scattering** rather than prop depth.  
Pinia should solve consistency first; component split can follow.

---

## 14) Forms Analysis (sidebar scope)

Forms in `CreatePolicy`, `TT`, `VV`, `UploadFramework`:

- Keep raw input form models local.
- Move only shared lookup data to store (frameworks, reviewers, categories).
- If product requires navigation-resume drafts, add explicit draft state in store with manual save/clear.

---

## 15) Tables / Filters / Pagination

- Keep table-only sort/search/page local by default.
- Move filters to store only when they must persist across route changes or coordinate with dashboard widgets.
- Use store actions for server-side filters.

---

## 16) Dashboard and Chart State Plan

- `PolicyDashboard.vue`: continue using `dashboardsStore` but route fetch orchestration through `policyStore` to avoid mixed responsibilities.
- `KPIDashboard.vue`: centralize KPI fetch + framework dependency in `policyStore`.
- Update both when framework changes from `frameworkStore`.

---

## 17) RBAC / Permission Plan

Current:
- Router meta has good starts.
- Components still fetch role directly and branch with string roles.

Recommended:
- Add/extend `permissionStore` with `can(permissionName)` getter.
- Use route guards + component helpers via same source.
- Remove hardcoded role-name checks incrementally.

---

## 18) Async UI Improvement Plan

- Distinguish `isLoading` vs `isRefreshing`.
- Add retry buttons for failed list/dashboard calls.
- Ensure duplicate submit prevention on approval/status actions.
- Keep existing toast patterns but centralize error formatting.

---

## 19) Optimistic UI Possibilities

Safe:
- lightweight UI preference toggles

Avoid optimistic:
- policy approval submit
- framework status approvals
- workflow-significant status transitions

---

## 20) Smart vs Presentational Separation

Start candidates:
- `FrameworkExplorer.vue`
- `PolicyApprover.vue`
- `StatusChangeRequests.vue`
- `CreatePolicy.vue` (extract API orchestration into store + composable)

Pattern:
- Smart container calls store actions and handles loading/error
- Presentational components render lists/forms and emit events only

---

## 21) State Normalization Recommendations

Use only where it helps:
- `policiesById`
- `policyIdsByFrameworkId`
- `subpoliciesById`
- `subpolicyIdsByPolicyId`

Do not over-normalize first iteration; prioritize consistency and duplicate call reduction.

---

## 22) What / Where / Why Plan

### Improvement 1
**What:** Unify selected framework state in Pinia (`frameworkStore`) for all policy sidebar pages.  
**Where:** All routes in sidebar policy section.  
**Why:** Prevent divergent framework context between explorer/dashboard/approver/versioning.  
**Priority:** High.

### Improvement 2
**What:** Replace `window.policyDataFetchPromise` + service cache orchestration with `policyStore.prefetchPolicyDomain`.  
**Where:** `AllPolicies`, `FrameworkExplorer`, `StatusChangeRequests`, `TreePolicies`, `PolicyApprover`, `TT`, `KPIDashboard`.  
**Why:** Centralized cache lifecycle, easier invalidation, Pinia DevTools visibility.  
**Priority:** High.

### Improvement 3
**What:** Move reusable dashboard + KPI fetch logic into `policyStore` actions and continue writing cache to `dashboardsStore`.  
**Where:** `PolicyDashboard.vue`, `KPIDashboard.vue`.  
**Why:** Single source for dashboard state transitions and TTL logic.  
**Priority:** High.

### Improvement 4
**What:** Keep local form and modal state local.  
**Where:** `CreatePolicy`, `TT`, `VV`, `UploadFramework`, modal components.  
**Why:** Avoid unnecessary global store complexity.  
**Priority:** Medium.

### Improvement 5
**What:** Introduce permission getter pattern (`can('approve_policy')`).  
**Where:** `PolicyApprover`, `PolicyDetails`, `StatusChangeRequests`, create/tailoring/versioning pages.  
**Why:** Remove hardcoded role branching and improve RBAC consistency.  
**Priority:** High.

---

## 23) File-by-file Migration Plan (sidebar routes focus)

| File | Current problem | Change needed | Priority |
|---|---|---|---|
| `CreatePolicy.vue` | heavy local orchestration + role fetch | use `frameworkStore` + store actions for shared data; keep form local | High |
| `UploadFramework.vue` | large API orchestration in component | move reusable fetch/state to `policyStore`/composable | Medium |
| `TT.vue` | repeated framework + cache + role logic | policyStore actions + frameworkStore + permissionStore | High |
| `VV.vue` | same as TT | same pattern | High |
| `FrameworkExplorer.vue` | direct explorer and status calls | centralize in policyStore | High |
| `PolicyApprover.vue` | role + cache + approvals all local | split into store-driven queue + local UI controls | High |
| `StatusChangeRequests.vue` | repeated framework cache + role checks | store-driven status requests + permission helper | High |
| `PolicyDashboard.vue` | mixed local + appData + dashboards | orchestrate through policyStore action | High |
| `KPIDashboard.vue` | repeated framework+KPI fetches | policyStore KPI action bundle | High |
| `Sidebar.vue` | local menu toggles | keep local (optional persistence only) | Low |

---

## 24) Step-by-step Implementation Plan

1. Create `src/stores/policy.js` with base state + TTL fields.
2. Add framework-dependent fetch actions.
3. Move policy prefetch dedupe from `window.policyDataFetchPromise` to `policyStore`.
4. Migrate one pilot page: `FrameworkExplorer.vue`.
5. Migrate dashboard/KPI pages.
6. Migrate approver/status pages.
7. Migrate create/tailoring/versioning shared lookups.
8. Add invalidation after mutations.
9. Add permission getter adoption incrementally.
10. Remove dead global cache patterns after validation.

---

## 25) Testing Checklist

- [ ] Each sidebar policy route loads successfully.
- [ ] Framework selection is consistent across all policy pages.
- [ ] Cache-first works and avoids duplicate API calls.
- [ ] Force refresh bypasses cache.
- [ ] Loading and refreshing states are distinct.
- [ ] Error/retry works on explorer/dashboard/approver flows.
- [ ] Create/update/approval actions invalidate and refresh affected data.
- [ ] RBAC checks remain correct.
- [ ] No stale mismatch between dashboard and list pages.
- [ ] Pinia DevTools shows expected policy store transitions.

---

## 26) Priority Matrix

- **High:** framework context unification, policyStore creation, global promise removal, approvals/status/dashboard centralization
- **Medium:** upload-framework reusable extraction, deeper normalization
- **Low:** menu state persistence, cosmetic cleanup

---

## 27) Final Developer Guidelines

1. Keep component-only UI state local.
2. Move shared policy server data to Pinia actions/state.
3. Use `frameworkStore` as the only selected-framework source.
4. Use getters for reused derived counts/selections.
5. Use actions for all API orchestration + cache invalidation.
6. Avoid global `window.*` cache coordination.
7. First implement `policyStore` + migrate `FrameworkExplorer.vue`.
8. Then migrate `PolicyDashboard.vue` and `KPIDashboard.vue`.
9. Validate with checklist before moving to another module.

---

## Backend RBAC Context (reference)

- `grc_backend/grc/routes/Policy/policy_views.py` uses permission classes (e.g., `PolicyViewPermission`) and tenant-aware decorators.
- Frontend permission helpers should align with backend permission semantics rather than string role assumptions.

