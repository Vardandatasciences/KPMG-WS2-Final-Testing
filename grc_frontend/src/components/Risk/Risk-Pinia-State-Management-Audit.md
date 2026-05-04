# Risk Module — Pinia State Management Audit & Migration Plan

**Scope requested:** Risk section in `grc_frontend/src/components/Policy/Sidebar.vue` (lines 295–391).  
**Frontend scope analyzed:** `grc_frontend/src/components/Risk/` + related risk routes in `src/router/index.js`.  
**Backend context scope:** `grc_backend/grc/routes/Risk/`.

---

## 1. Page/Module Summary

### 1.1 What this module does

Risk module in the sidebar covers:

- Risk register list and create risk
- Risk register AI document upload
- Risk instances list and create instance
- Risk instance AI upload and risk scoring
- Risk handling/resolution flow
- Risk analytics dashboard/KPI/Basel KPI
- System identified risks workflow and risk threshold management

### 1.2 Sidebar routes → components (from `Sidebar.vue:295-391`)

| Sidebar item | Route | Component |
|---|---|---|
| Risk Register List | `/risk/riskregister-list` | `RiskRegisterList.vue` |
| Create Risk | `/risk/create-risk` | `CreateRisk.vue` |
| Risk Register AI | `/risk/ai-document-upload` | `risk_ai.vue` |
| Risk Incidents | `/risk/riskinstances-list` | `RiskInstances.vue` |
| Create Risk Incident | `/risk/create-instance` | `CreateRiskInstance.vue` |
| Risk Instance AI | `/risk/ai-instance-upload` | `risk_ai_instance.vue` |
| Risk Scoring | `/risk/scoring` | `RiskScoring.vue` |
| Risk Handling | `/risk/resolution` | `RiskResolution.vue` |
| Dashboard | `/risk/riskdashboard` | `RiskDashboard.vue` |
| KPI Dashboard | `/risk/riskkpi` | `RiskKPI.vue` |
| Basel KPIs (conditional) | `/risk/baselkpis` | `baselkpi.vue` |
| System Identified Risks | `/risk/system-identified-risks` | `SystemIdentifiedRisks.vue` |
| Risk Threshold | `/risk/threshold` | `RiskThreshold.vue` |

### 1.3 Additional connected risk routes

- `/risk/riskregister` (redirect)
- `/risk/riskinstances` (redirect)
- `/risk/workflow` → `RiskWorkflow.vue`
- `/risk/scoring-details/:riskId` → `ScoringDetails.vue`
- `/risk/tailoring` → `TailoringRisk.vue`
- `/view-risk/:id` → `ViewRisk.vue`
- `/view-instance/:id` (if routed in project variant) → `ViewInstance.vue`

### 1.4 Parent layout

- Loaded via global shell (`App.vue`) with `Sidebar.vue` + `router-view`.
- Risk pages are route-level screens with mostly local orchestration.

### 1.5 Workflow category mapping

- Risk register lifecycle
- Risk instance lifecycle
- AI ingestion/analysis
- Risk scoring and analytics
- Workflow/approval-like handling for system-identified risks

---

## 2. Current Vue Implementation Summary

### 2.1 API style

Mixed Options API and setup pages across risk module.

### 2.2 Existing Pinia usage

- `RiskDashboard.vue` uses `useDashboardsStore` and `useAppDataStore`.
- No dedicated `riskStore` yet.

### 2.3 Existing service-level cache (outside Pinia)

- `src/services/riskService.js` caches `risks` + `riskInstances`.
- Components like `RiskRegisterList.vue`, `RiskInstances.vue`, `CreateRisk.vue` directly use `riskDataService`.
- Some components use `window.riskDataFetchPromise` patterns (seen in `RiskInstances.vue`).

### 2.4 API call patterns

- Heavy component-level API orchestration via `apiService` / axios wrappers.
- `RiskKPI.vue` uses many direct KPI endpoint calls and a mix of `fetch` + `apiService`.
- `SystemIdentifiedRisks.vue` contains large workflow/API surface.

### 2.5 Permissions/RBAC

- `AccessUtils` appears in key risk components (`RiskDashboard.vue`, `RiskKPI.vue`, `RiskInstances.vue` etc).
- Permission handling is not fully centralized into Pinia getter/composable patterns.

---

## 3. Current Data Flow

1. Route loads risk page.
2. Page fetches required lists/filters/metrics directly.
3. Some pages first read from `riskDataService`.
4. Mutations update local state and sometimes refresh related lists manually.
5. Dashboard uses `dashboardsStore` cache for risk summary but still fetches many datasets directly.

### Current risks

- Repeated API calls across risk screens
- Multiple state sources (component state, riskDataService, appDataStore, dashboardsStore)
- Possible stale mismatch between register list, instances, scoring, and dashboard after updates

---

## 4. Variable Inventory (Grouped)

| Variable group | Typical examples | Type | Keep local | Move to Pinia |
|---|---|---|---|---|
| Register/instance collections | risks, riskInstances | shared API data | No | Yes |
| Lookup data | frameworks, policies, categories, business impacts, departments | shared API data | No | Yes |
| Analytics payload | dashboard cards, trends, heatmap, KPI charts | shared API data | No | Yes |
| Workflow states | selected risk, workflow status, approver/reviewer selections | shared workflow data | Partial | Yes |
| Form fields | create/edit/scoring input values | local form state | Yes | No (unless draft persistence needed) |
| Modal and UI toggles | open states, local tabs, column chooser | local UI | Yes | No |
| Notification badge count | `pendingRiskCount` in sidebar | shared derived data | No | Yes (getter) |

---

## 5. State Classification

### 5.1 Keep local

- Modal open/close
- Temporary form validation errors
- Local view/tab toggles
- table-only sort and visible column settings

### 5.2 Move to Pinia

- risk register and risk instance shared datasets
- shared lookup dictionaries and filter options
- dashboard/KPI summary data used across analytics screens
- pending system-identified risk count used in sidebar badge

### 5.3 API/server data via Pinia actions

- risks, risk instances, details
- scoring-related datasets
- dashboard and KPI endpoints
- system-identified risks workflow endpoints

---

## 6. API Call Inventory (Major families)

Observed families across risk components:

- Risk register endpoints (`RISKS`, `RISKS_FOR_DROPDOWN`, export)
- Risk instance endpoints (`RISK_INSTANCES`, create/update instance)
- Scoring endpoints (`RISK_INSTANCE(...)`, scoring update flows)
- Dashboard/KPI endpoints (`/api/risk/dashboard-with-filters`, trend, heatmap, analytics, KPI-specific endpoints)
- Lookup endpoints (frameworks/policies/categories/business impacts/departments)
- AI endpoints (`risk_ai.vue`, `risk_ai_instance.vue`)
- System identified risks endpoints (list/detail/scan/schedule/approve/reject/workflow actions)
- Notifications (`PUSH_NOTIFICATION`)

Recommendation: centralize reusable families into `riskStore` actions.

---

## 7. Recommended Pinia Stores

### 7.1 `riskStore` (new, primary)

Suggested file: `src/stores/risk.js`

**Purpose:** single shared risk module source of truth for register, instances, analytics, and system-identified risk workflows.

**Core state fields:**
- `risks`
- `riskInstances`
- `riskDetailsById`
- `lookups` (frameworks, policies, categories, businessImpacts, departments)
- `dashboardMetrics`
- `kpiMetrics`
- `systemIdentifiedRisks`
- `pendingSystemRiskCount`
- `status`, `isLoading`, `isRefreshing`, `error`, `lastFetched`

### 7.2 `dashboardsStore` (existing)

- Continue using `risk` domain cache.
- Let `riskStore` orchestrate fetch and set `dashboardsStore.set('risk', payload)` where appropriate.

### 7.3 `appDataStore` (existing)

- Already has `fetchRisks()` via `riskDataService`.
- Align ownership so `riskStore` and `appDataStore` do not diverge.

### 7.4 `frameworkStore` (existing)

- Use for selected framework synchronization where risk pages currently fetch framework selection independently.

---

## 8. Recommended State Design

```js
state: () => ({
  risks: [],
  riskInstances: [],
  riskDetailsById: {},
  lookups: {
    frameworks: [],
    policies: [],
    categories: [],
    businessImpacts: [],
    departments: []
  },
  dashboard: {
    summary: null,
    trends: null,
    heatmap: null
  },
  kpi: {
    cards: null,
    charts: {}
  },
  systemIdentified: {
    items: [],
    schedules: [],
    stats: null,
    pendingCount: 0
  },
  status: 'idle', // idle | loading | success | error
  isLoading: false,
  isRefreshing: false,
  error: null,
  lastFetched: {
    risks: null,
    instances: null,
    lookups: null,
    dashboard: null,
    kpi: null,
    systemIdentified: null
  }
})
```

---

## 9. Recommended Getters

- `isRisksFresh`
- `riskById(id)`
- `instanceById(id)`
- `openRiskCount`
- `highCriticalRiskCount`
- `pendingSystemRiskCount` (for sidebar badge)
- `dashboardCards`
- `heatmapMatrix`

---

## 10. Recommended Actions

- `prefetchRiskDomain({ force })`
- `fetchRisks({ filters, force })`
- `fetchRiskInstances({ filters, force })`
- `fetchRiskDetails(id, { force })`
- `createRisk(payload)`
- `createRiskInstance(payload)`
- `fetchRiskDashboard({ filters, force })`
- `fetchRiskKpi({ filters, force })`
- `fetchRiskHeatmap({ filters, force })`
- `fetchLookups({ force })`
- `fetchSystemIdentifiedRisks({ filters, force })`
- `runSystemRiskScan(payload)`
- `approveSystemRisk(payload)` / `rejectSystemRisk(payload)`
- `invalidateRiskCache(scope)`
- `resetRiskState()`

---

## 11. Cache-first Implementation Plan

Pinia-first flow:
1. read cache from store,
2. check `lastFetched` + TTL,
3. use cache if fresh,
4. stale with existing data → `isRefreshing`,
5. empty → `isLoading`,
6. update state and timestamps on success,
7. preserve stale data + set `error` on failure,
8. support `force: true`.

Suggested TTL:
- risks/instances: 1–5 min
- dashboard/KPI: 1–5 min
- lookup lists: 15–30 min
- system identified list/stats: 30–90 sec

---

## 12. Repeated API Calls / Patterns to Fix

| Repeated pattern | Current files | Problem | Pinia fix |
|---|---|---|---|
| `riskDataService` plus component fetch fallback | `RiskRegisterList.vue`, `RiskInstances.vue`, `CreateRisk.vue` | mixed cache ownership | `riskStore` unified fetch/cache |
| dashboard analytics endpoint orchestration in view | `RiskDashboard.vue` | duplicated query and error patterns | `fetchRiskDashboard` + `fetchRiskHeatmap` actions |
| KPI endpoint fan-out in component | `RiskKPI.vue` | many independent requests in view | `fetchRiskKpi` action bundle |
| system risk workflow APIs all inside component | `SystemIdentifiedRisks.vue` | oversized smart component | `riskStore.systemIdentified*` actions |
| `window.riskDataFetchPromise` pattern | `RiskInstances.vue` | global mutable promise pattern | store-level in-flight dedupe |

---

## 13. Prop Drilling Analysis

Main issue is not deep prop drilling; primary issue is duplicated orchestration and cache/state scattering.

---

## 14. Forms Analysis

### Create Risk (`CreateRisk.vue`)
- Keep full form model local.
- Move shared lookups and create side-effects to store actions.

### Create Risk Instance (`CreateRiskInstance.vue`) and Scoring (`RiskScoring.vue` / `ScoringDetails.vue`)
- Keep transient form/UI local.
- Move data-fetch and submit/invalidate logic to store actions.

---

## 15. Tables / Filters / Pagination

- Keep table-only state local unless shared across routes.
- Move server filter payload composition to store actions.
- If cross-page filter persistence needed, add a small `uiFilters` slice in `riskStore`.

---

## 16. Dashboard and Chart State Plan

- `RiskDashboard.vue` should read from `riskStore` action outputs (and optional `dashboardsStore` cache) instead of direct endpoint fan-out in component.
- `RiskKPI.vue` should use a bundled KPI action to reduce request duplication and unify loading/error handling.
- Sidebar `pendingRiskCount` should read from `riskStore` getter.

---

## 17. RBAC/Permission Plan

- Keep existing route guards and `AccessUtils` behavior.
- Add centralized permission helper/store (`can(permission)`) to replace scattered checks.
- Avoid hardcoded role logic; align with backend permission semantics.

---

## 18. Async UI Improvement Plan

- Differentiate `isLoading` vs `isRefreshing`.
- Add retry actions for dashboard/KPI/system-risk APIs.
- Add duplicate submit protection for create/approve/reject actions.
- Ensure empty states for no risks/no instances/no system risks.

---

## 19. Optimistic UI Possibilities

Safe:
- local-only UI toggles and preference updates

Avoid optimistic:
- risk create/update
- scoring updates with compliance impact
- system-risk workflow approvals/rejections

---

## 20. Smart vs Presentational Plan

Priority smart/container candidates:
- `SystemIdentifiedRisks.vue`
- `RiskDashboard.vue`
- `RiskKPI.vue`
- `RiskRegisterList.vue`
- `RiskInstances.vue`

Presentational subcomponents should render props and emit events only.

---

## 21. State Normalization Recommendations

When needed:
- `risksById`
- `riskIdsByStatus`
- `instancesById`
- `instanceIdsByRiskId`

Start with simpler arrays + `detailsById` first.

---

## 22. What / Where / Why Plan

### Improvement 1
**What:** Create `riskStore` to centralize risk module shared state and API orchestration.  
**Where:** `src/stores/risk.js`, consumed by risk sidebar pages.  
**Why:** prevent duplicated calls and stale mismatch across register/instances/dashboard/KPI.  
**Priority:** High.

### Improvement 2
**What:** Replace service/global in-flight patterns with store in-flight dedupe.  
**Where:** pages using `riskDataService` and `window.riskDataFetchPromise`.  
**Why:** better reliability, simpler debugging, consistent cache lifecycle.  
**Priority:** High.

### Improvement 3
**What:** Move dashboard/KPI fan-out requests into store action bundles.  
**Where:** `RiskDashboard.vue`, `RiskKPI.vue`.  
**Why:** unified loading/error and reduced repeated requests.  
**Priority:** High.

### Improvement 4
**What:** Keep forms and local UI state local while centralizing lookups and mutation side-effects.  
**Where:** `CreateRisk.vue`, `CreateRiskInstance.vue`, `RiskScoring.vue`, `ScoringDetails.vue`.  
**Why:** practical local UX with centralized consistency for shared data.  
**Priority:** Medium.

---

## 23. File-by-file Migration Plan (sidebar-focused)

| File | Current problem | Change needed | Priority |
|---|---|---|---|
| `RiskRegisterList.vue` | mixed service cache + local API | use `riskStore.fetchRisks` | High |
| `CreateRisk.vue` | local lookup + create orchestration | store lookups + create action + invalidation | High |
| `risk_ai.vue` | local-heavy AI flow | extract shared actions/composable for upload status and results | Medium |
| `RiskInstances.vue` | service + global promise pattern | `riskStore.fetchRiskInstances` + remove global promise | High |
| `CreateRiskInstance.vue` | likely local orchestration | store-backed lookups and submit side-effects | High |
| `RiskScoring.vue` + `ScoringDetails.vue` | mixed fetch/update logic in views | move shared fetch/update to store actions | High |
| `RiskResolution.vue` | workflow state local | store mutation/invalidation actions | Medium |
| `RiskDashboard.vue` | API fan-out in component | store dashboard actions + dashboardsStore cache use | High |
| `RiskKPI.vue` | many KPI endpoint calls in component | bundled KPI action in store | High |
| `baselkpi.vue` | KPI variant branching local | reuse store KPI action with basel mode | Medium |
| `SystemIdentifiedRisks.vue` | very large workflow/API surface | split into store actions + smaller view logic | High |
| `RiskThreshold.vue` | threshold fetch/save local | store actions for consistency | Medium |

---

## 24. Step-by-step Implementation Plan

1. Create `riskStore` with base state/status/TTL fields.
2. Add `fetchRisks`, `fetchRiskInstances`, `fetchLookups`.
3. Migrate `RiskRegisterList.vue` and `RiskInstances.vue` first.
4. Add dashboard/KPI action bundles.
5. Migrate `RiskDashboard.vue` and `RiskKPI.vue`.
6. Migrate create/scoring/resolution forms side-effects.
7. Migrate `SystemIdentifiedRisks.vue` workflow actions.
8. Remove global/inconsistent cache patterns.
9. Add invalidation rules after mutations.
10. Full regression test across all risk routes.

---

## 25. Testing Checklist

- [ ] Risk sidebar routes all load and navigate correctly
- [ ] Register and instances remain consistent after create/update
- [ ] AI upload pages still function with migrated shared state
- [ ] Scoring actions update data consistently
- [ ] Dashboard/KPI cache-first behavior works
- [ ] Force refresh works for key pages
- [ ] Loading/refresh/error/empty states are correct
- [ ] Sidebar `pendingRiskCount` reflects latest store data
- [ ] Permission and access-denied behavior unchanged
- [ ] Pinia DevTools reflects expected risk state transitions

---

## 26. Priority Matrix

- **High:** riskStore creation, register/instances migration, dashboard/KPI centralization, system-risk workflow extraction
- **Medium:** AI/scoring/threshold extraction refinements
- **Low:** UI state persistence optimizations

---

## 27. Final Developer Guidelines

1. Keep component-only UI/form state local.
2. Move shared risk server data to Pinia (`riskStore`).
3. Avoid mixed ownership between views, services, and global promises.
4. Use getters for derived counts/heatmap/pending system risk badge.
5. Use actions for fetch, mutate, invalidate, and refresh logic.
6. Keep permissions centralized and consistent with backend.
7. Start with `RiskRegisterList.vue` + `RiskInstances.vue`, then analytics pages.
8. Validate checklist before moving to next module.

