# Compliance Module — Pinia State Management Audit & Migration Plan

**Scope:** `grc_frontend/src/components/Compliance/`, `grc_backend/grc/routes/Compliance/`, Compliance section in `grc_frontend/src/components/Policy/Sidebar.vue` (lines ~113–198).  
**Stack:** Vue 3 + Pinia only (no Vuex / React patterns).  
**Status:** Analysis and plan only — no implementation in this document.

---

## Document map (original template coverage)

| # | Section | Coverage in this file |
|---|---------|------------------------|
| 1 | Page/module summary | §1 |
| 2 | Current Vue implementation | §2 |
| 3 | Current data flow | §3 |
| 4 | Variable inventory | §4 (grouped + per-page in §12) |
| 5 | State classification | §5 |
| 6 | API call inventory | §6 + §12 matrix |
| 7 | Pinia store recommendation | §7 |
| 8 | Recommended Pinia state design | §8 |
| 9 | Recommended getters | §9 |
| 10 | Recommended actions | §10 |
| 11 | Cache-first plan | §11 |
| 12 | Repeated API calls | §12 |
| 13 | Prop drilling | §13 |
| 14 | Forms | §14 |
| 15 | Tables / filters / pagination | §15 |
| 16 | Dashboard / charts | §16 |
| 17 | RBAC / permissions | §17 |
| 18 | Async UI | §18 |
| 19 | Optimistic UI | §19 |
| 20 | Smart vs presentational | §20 |
| 21 | State normalization | §21 |
| 22 | What / Where / Why | §22 |
| 23 | File-by-file migration | §23 |
| 24 | Implementation steps | §24 |
| 25 | Testing checklist | §25 |
| 26 | Priority matrix | §26 |
| 27–29 | Guidelines & summary | §27 |

---

## 1. Page / module summary

### 1.1 What this module does

- **Control register:** Framework → policy → sub-policy → controls (compliances), list/detail/export.
- **Organizational controls:** Framework-scoped controls, uploads, saves, audit runs (`OrganizationalControls.vue`).
- **Compliance / audit management:** Register-style lists, exports (`AuditManagementView.vue`, related views).
- **Approval workflow:** Reviewer and final approval queues, detail view, resubmission/rejection (`ComplianceApprover.vue`, `ComplianceDetails.vue`).
- **Lifecycle:** Create, edit, copy, tailoring, versioning (toggle/deactivate flows as implemented), baseline configuration.
- **Analytics:** User compliance dashboard, KPI dashboard (`ComplianceDashboard.vue`, `ComplianceKPINew.vue`).
- **Other:** Cross-framework mapping, tree “view” and “audit” routes, internal demo/debug.

### 1.2 Routes → components (shell router: `grc_frontend/src/router/index.js`)

| Route | Name (if set) | Component |
|-------|-----------------|-----------|
| `/compliance/list` (alias `/control-management`) | `AllCompliance` | `AllCompliance.vue` |
| `/compliance/organizational-controls` | `OrganizationalControls` | `OrganizationalControls.vue` |
| `/compliance/audit-management` | `AuditManagement` | `AuditManagementView.vue` |
| `/compliance/approver` | `ComplianceApprover` | `ComplianceApprover.vue` |
| `/compliance/create` | `CreateCompliance` | `CreateCompliance.vue` |
| `/compliance/tailoring` | `ComplianceTailoring` | `ComplianceTailoring.vue` |
| `/compliance/versioning` | `ComplianceVersioning` | `ComplianceVersioning.vue` |
| `/compliance/baseline-configuration` | `BaselineConfiguration` | `BaselineConfiguration.vue` |
| `/compliance/user-dashboard` | `ComplianceDashboard` | `ComplianceDashboard.vue` |
| `/compliance/kpi-dashboard` | `ComplianceKPI` | `ComplianceKPINew.vue` |
| `/compliance/audit-status` | `Compliances` | `Compliances.vue` |
| `/compliance/audit-status/all` | `AllComplianceAudit` | `ComplianceAuditView.vue` (lazy) |
| `/compliance/cross-framework-mapping` | `CrossFrameworkMapping` | `CrossFrameworkMapping.vue` |
| `/compliance/view/:type/:id/:name` | `ComplianceView` | `ComplianceView.vue` |
| `/compliance/audit/:type/:id/:name` | `ComplianceAuditView` | `ComplianceAuditView.vue` |
| `/compliance/details/:complianceId` | `ComplianceDetails` | `ComplianceDetails.vue` |
| `/compliance-details/:complianceId` | `ComplianceDetails` | `ComplianceDetails.vue` (lazy) |
| `/compliance/edit/:id` | `EditCompliance` | `EditCompliance.vue` |
| `/compliance/copy/:id` | `CopyCompliance` | `CopyCompliance.vue` |
| `/compliance/popup-demo` | `PopupDemo` | `PopupDemo.vue` |
| `/compliance/debug` | `ComplianceDebug` | `ComplianceDebug.vue` |

### 1.3 Parent / layout

- **`grc_frontend/src/App.vue`:** Renders `Sidebar` + `<router-view>` — compliance pages are **route components**, not nested under a dedicated Compliance layout.

### 1.4 Sidebar (Compliance block) — `Sidebar.vue`

- **Control Management:** `/compliance/list`, `/compliance/organizational-controls`
- **Compliance Management:** `/compliance/audit-management`, `/compliance/approver`
- **Compliance Creation:** `/compliance/create`, `/compliance/tailoring`, `/compliance/versioning`, `/compliance/baseline-configuration`
- **Performance Analysis:** `/compliance/user-dashboard`, `/compliance/kpi-dashboard`

Sidebar submenu UI state: `openMenus.compliances`, `complianceList`, `complianceManagement`, `complianceCreation`, `compliancePerformance` — **local `ref` in Sidebar** (fine to keep local unless you want menu persistence across reloads).

### 1.5 Domain tags

Compliance, control, policy/sub-policy hierarchy, audit, dashboard, evidence (org uploads), RBAC, notifications.

---

## 2. Current Vue implementation summary

| Topic | Finding |
|-------|---------|
| **API style** | Mix of **Options API** and **`<script setup>`** (`AllCompliance.vue`, `AuditManagementView.vue`, `ComplianceAuditView.vue`, `ComplianceView.vue` use setup). |
| **Pinia today** | `ComplianceDashboard.vue`: `useDashboardsStore`, `useAppDataStore`. **`useFrameworkStore`** exists (`stores/framework.js`) but many compliance pages still call **`FRAMEWORK_GET_SELECTED` / `FRAMEWORK_SET_SELECTED`** directly. |
| **Caching** | Singleton **`complianceDataService`** (`services/complianceService.js`) + **`window.complianceDataFetchPromise`** for dedupe — **outside Pinia**. **`useAppDataStore.fetchCompliances`** also uses `complianceDataService` — **two consumers** of the same cache pattern. |
| **HTTP** | Mostly **`apiService`** via local `axios` shim object; **`axiosInstance`** in `OrganizationalControls.vue`; raw **`axios`** in `CrossFrameworkMapping.vue`. |
| **RBAC** | **`AccessUtils`** in several views; **`USER_ROLE`** + string checks (e.g. `GRC Administrator`) in `ComplianceDetails.vue` / `ComplianceApprover.vue`. |

---

## 3. Current data flow

1. **Route activated** → page **mount**.
2. Many pages **fetch session framework** (`API_ENDPOINTS.FRAMEWORK_GET_SELECTED`) then **framework list** / hierarchy endpoints (`COMPLIANCE_ALL_POLICIES_*`, or `complianceService.*`, or public `/api/compliance/frameworks/public/`).
3. Data stored in **component state** (`ref` / `data`) and/or **`complianceDataService.dataStore`** and/or **`appDataStore`** (`complianceFrameworks`, `compliances`).
4. **Mutations** (create, approve, export) trigger **refetch** or navigation; **no single invalidation bus** — risk of stale list vs detail vs cache.

---

## 4. Variable inventory (grouped)

High-impact buckets (not every field in large SFCs):

| Bucket | Typical symbols | Keep local? | Pinia? |
|--------|-----------------|-------------|--------|
| Hierarchy lists | `frameworks`, `policies`, `subpolicies`, `compliances` | No (shared) | **Yes** — `complianceStore` |
| Session / selected framework | `sessionFrameworkId`, `selectedFramework` | Align with store | **`frameworkStore`** |
| Export UI | `exportFormat`, `isExporting`, dropdown open | **Yes** | Job id/result optional |
| Approvals | grouped lists, filters, tabs | Partial UI local | **Yes** — list + cache metadata |
| Modals / choosers | `showRejectModal`, `selectedControl`, column chooser | **Yes** | No |
| Dashboard copy | `dashboardData`, local `frameworks` | No | **`dashboardsStore` + actions** |

---

## 5. State classification

### 5.1 Local UI state (stay in component)

Modal visibility, column chooser, export format dropdown, textarea for rejection reason, transient validation, **Sidebar** `openMenus.*` for compliance submenus.

### 5.2 Shared global / cross-page

Selected framework (backend session), compliance prefetch cache, approval list coherence, dashboard KPI slice — **Pinia**.

### 5.3 API / server data

Lists, details, export task status, KPI payloads — **Pinia actions** + optional normalized state; call **`complianceService`** / `apiService` **inside actions**.

---

## 6. API inventory (families)

Central definitions: `grc_frontend/src/services/api.js` (`complianceService`), `grc_frontend/src/config/api.js` (`API_ENDPOINTS`).

| Family | Examples | Used in (representative) |
|--------|----------|---------------------------|
| Framework session | `FRAMEWORK_GET_SELECTED`, `FRAMEWORK_SET_SELECTED` | Most compliance pages |
| Hierarchy | `COMPLIANCE_ALL_POLICIES_FRAMEWORKS`, policies/subpolicies/compliances by id | `AllCompliance`, `Compliances` |
| Public frameworks | `api/compliance/frameworks/public/` | `ComplianceAuditView`, `complianceService` |
| Audit management | `/api/compliance/all-for-audit-management/`, `public` variant | `AuditManagementView`, `ComplianceAuditView` |
| CRUD / clone | `COMPLIANCE_CREATE`, `COMPLIANCE_UPDATE`, clone | `CreateCompliance`, `EditCompliance`, `CopyCompliance` |
| Detail | `complianceService.getComplianceById`, `COMPLIANCE_GET` | `ComplianceDetails`, copy/edit |
| Approvals | user/reviewer approval APIs, submit/resubmit | `ComplianceApprover`, `complianceService` |
| Dashboard / KPI | `COMPLIANCE_USER_DASHBOARD`, KPI endpoints, analytics POST | `ComplianceDashboard`, `ComplianceKPINew`, `appDataStore` |
| Export | `COMPLIANCE_EXPORT`, `EXPORT_COMPLIANCE_MANAGEMENT`, export status URL | `Compliances`, `AllCompliance`, `AuditManagementView` |
| Versioning | toggle version, deactivate (as wired) | `ComplianceVersioning` |
| Baseline | baseline list/create endpoints | `BaselineConfiguration` |
| Org controls | `/api/organizational-controls/*`, frameworks | `OrganizationalControls` |
| Cross-framework | `/api/cross-framework-mapping/`, compare | `CrossFrameworkMapping` |
| RBAC / users | `USER_ROLE`, `USERS_FOR_DROPDOWN`, `USERS_FOR_REVIEWER_SELECTION` | `ComplianceDetails`, `ComplianceApprover`, forms |
| Notifications | `PUSH_NOTIFICATION` | `ComplianceApprover` |

---

## 7. Recommended Pinia stores (module-scoped)

| Store | Path | Purpose |
|-------|------|---------|
| **frameworkStore** (existing) | `stores/framework.js` | Single source for selected framework + session sync — **use everywhere** instead of per-page `FRAMEWORK_*` calls. |
| **complianceStore** (new) | `stores/compliance.js` | Hierarchy cache, audit-management list, approvals slice, detail-by-id, export jobs, `status` / `lastFetched` / TTL, in-action fetch dedupe (**replace `window.complianceDataFetchPromise`**). |
| **dashboardsStore** (existing) | `stores/dashboards.js` | Compliance dashboard KPI cache — **single writer** from a compliance dashboard action. |
| **appDataStore** (existing) | `stores/appData.js` | Decide: **either** sole prefetch orchestrator **or** delegate to `complianceStore` — avoid two parallel truths. |
| **permissionStore** (new or extend) | e.g. `stores/permission.js` | `can(permission)` aligned with backend RBAC; replace ad-hoc role strings over time. |

---

## 8. Recommended `complianceStore` state (starter)

```js
state: () => ({
  hierarchy: {
    frameworks: [],
    policiesByFrameworkId: {},
    subpoliciesByPolicyId: {},
    compliancesBySubPolicyId: {},
  },
  auditManagementList: [],
  approvals: { asUser: [], asReviewer: [], lastQuery: {} },
  selectedComplianceId: null,
  complianceDetailById: {},
  exportJobs: {},
  status: 'idle', // idle | loading | success | error
  isLoading: false,
  isRefreshing: false,
  error: null,
  lastFetched: {
    hierarchy: null,
    auditList: null,
    approvals: null,
    detail: {},
  },
})
```

Tune normalization only if list sizes require it.

---

## 9. Recommended getters

- `isHierarchyFresh` — TTL vs `lastFetched.hierarchy`
- `compliancesForSubPolicy(subPolicyId)`
- `pendingApprovalCount` / grouped buckets
- `complianceDetail(complianceId)` — from `complianceDetailById`
- **`frameworkStore`:** `selectedFramework`, `isAllFrameworks` (existing)

---

## 10. Recommended actions

- `prefetchComplianceDomain({ force })` — replaces `fetchAllComplianceData` + global promise
- `fetchHierarchy({ frameworkId, force })`
- `fetchAuditManagementList({ force })`
- `fetchApprovals({ userId, mode, filters })`
- `fetchComplianceDetail(complianceId, { force })`
- `invalidateAfterComplianceMutation()` — clears relevant slices + optional `dashboardsStore.clear('compliance')`
- `startComplianceExport` / `pollExportStatus` (if cross-route resume needed)
- `fetchBaselineForFramework`, `fetchCrossFrameworkPair` — or submodule actions in same store initially

---

## 11. Cache-first (Pinia-only pattern)

1. If data present and `lastFetched` within TTL → return (use **`isRefreshing`** if optional background refresh).
2. If empty → **`isLoading` true**; if stale but present → show stale + **`isRefreshing`**.
3. On success → update state + `lastFetched`; on failure → `error`, `status: 'error'`.
4. **`force: true`** on user “Refresh” and after mutations.

**TTL guidance (tune per env):** hierarchy 5–15 min; approvals 30–60 s; dashboard 1–5 min; detail 30–60 s.

---

## 12. Per-page matrix — route, file, APIs, Pinia direction

| Page | File | Main API / service touchpoints | Move to Pinia | Keep local |
|------|------|--------------------------------|---------------|------------|
| Controls (list) | `AllCompliance.vue` | `FRAMEWORK_*`, `COMPLIANCE_ALL_POLICIES_*`, export register, `complianceDataService`, `AccessUtils` | `frameworkStore`, `complianceStore` hierarchy + export job metadata | Column chooser, export dropdown UI, breadcrumbs display |
| Organizational controls | `OrganizationalControls.vue` | `axiosInstance` → frameworks, OC CRUD/upload/audit | `complianceStore` (or slim `organizationalControlsStore` if scope grows) | Wizard steps, file pickers, inline errors |
| Audit management | `AuditManagementView.vue` | `FRAMEWORK_*`, frameworks list, `all-for-audit-management`, export | `complianceStore` | Table UI, column visibility |
| Compliance approval | `ComplianceApprover.vue` | `USER_ROLE`, approval list APIs, `FRAMEWORK_*`, `complianceDataService`, push notification | `complianceStore` + `permissionStore` | Tab UI, inline filters if page-only |
| Create | `CreateCompliance.vue` | `complianceService` create + hierarchy + category BU + `FRAMEWORK_*`, `AccessUtils` | Actions + **invalidate** hierarchy/lists | Entire form model |
| Edit | `EditCompliance.vue` | load/update + reviewers (`USERS_FOR_REVIEWER_SELECTION`) | Same | Form fields |
| Copy | `CopyCompliance.vue` | `getComplianceById`, clone, hierarchy, `complianceDataService` | Same | Form fields |
| Tailoring | `ComplianceTailoring.vue` | `FRAMEWORK_*`, tailoring APIs, reviewers | `frameworkStore`, `complianceStore` | Template UI state |
| Versioning | `ComplianceVersioning.vue` | `FRAMEWORK_*`, version/toggle APIs, `AccessUtils` | `complianceStore` | Modals, selection UI |
| Baseline | `BaselineConfiguration.vue` | frameworks, baseline GET/POST | `complianceStore.baseline*` | Local tree UI |
| User dashboard | `ComplianceDashboard.vue` | `complianceService` / dashboard APIs, `dashboardsStore`, `complianceDataService` | **One** `loadComplianceDashboard` action writing `dashboardsStore` | Chart display options |
| KPI | `ComplianceKPINew.vue` | `FRAMEWORKS`, `FRAMEWORK_*`, many KPI GETs | `fetchKpiBundle` in `complianceStore` | Selected chart/tab UI |
| Audit status | `Compliances.vue` | Same hierarchy family + export + audit-info | `complianceStore` | Filters, pagination UI |
| Audit status (all) | `ComplianceAuditView.vue` | `FRAMEWORK_*`, public frameworks, view/audit endpoints, audit-info | `complianceStore` | Filters |
| Cross-framework | `CrossFrameworkMapping.vue` | raw `axios` frameworks + mapping + compare | Pinia actions using **`apiService`** | Two framework pickers, diff UI |
| View | `ComplianceView.vue` | View-by-type endpoints, filters, export | `complianceStore` or thin composable calling store | `statusFilter`, modal, table columns |
| Audit view | `ComplianceAuditView.vue` | Same family as audit-status all | `complianceStore` | Local filters |
| Details | `ComplianceDetails.vue` | `USER_ROLE`, `complianceService.getComplianceById`, approve/reject | `fetchComplianceDetail`, `permissionStore` | Reject modal, comments |
| Popup demo | `PopupDemo.vue` | Demo + `PopupMixin` | Low priority | All |
| Debug | `ComplianceDebug.vue` | Debug-only | Exclude / last | All |

---

## 13. Prop drilling

Primary issue is **not deep props** but **repeated session/framework fetches** per page. Fix: **`storeToRefs(useFrameworkStore())`** + central **`complianceStore`** for shared lists.

---

## 14. Forms

- **Create / Edit / Copy:** keep **form state local** unless product requires **multi-step drafts across routes** — then Pinia `drafts.createCompliance` with explicit save/clear.
- **Rejection reason:** local only.

---

## 15. Tables / filters / pagination

- Default: **filters, sort, page index local** to the page.
- Move filters to Pinia **only** if shared with another route/widget or URL-persisted product requirement.
- Server-driven filters: pass as **action parameters**; store optional `lastQuery` for restore.

---

## 16. Dashboard / charts

- Unify **`ComplianceDashboard.vue`** so it does not both **`complianceDataService.prefetch`** and **`dashboardsStore`** without a single orchestration rule.
- **`ComplianceKPINew.vue`:** bundle KPI fetches in one action with shared loading/error.

---

## 17. RBAC / permissions

- Today: **`AccessUtils`** + **`API_ENDPOINTS.USER_ROLE`** + string role checks.
- Target: **`permissionStore.can('…')`** aligned with backend (`compliance_views.py` decorators / permission classes).
- Keep **server** as source of truth; UI hides buttons + handles **403** consistently.

---

## 18. Async UI

- Standardize: **skeleton** (initial), **spinner** (button), **retry**, **empty**, **toast** on success/failure (`PopupService` where already used).
- Use **`isLoading`** vs **`isRefreshing`** for cache-first screens.

---

## 19. Optimistic UI

- **Avoid** for approve/reject, delete/deactivate, clone submit.
- **OK** for pure UI (column order, collapsed panels).

---

## 20. Smart vs presentational

- **Containers:** `AllCompliance`, `ComplianceApprover`, `OrganizationalControls`, `AuditManagementView` — thin wrappers calling Pinia; pass minimal props to dumb tables.
- **Presentational:** `DynamicTable` rows, dumb modals.

---

## 21. State normalization

- Start with **lists + `detailById`**. Add **`compliancesById`** + id lists per sub-policy only if profiling shows benefit.

---

## 22. What / Where / Why (samples)

### W1 — Framework session via Pinia

- **What:** Stop duplicating `FRAMEWORK_GET_SELECTED` / `FRAMEWORK_SET_SELECTED` in every compliance page.
- **Where:** All files in §12 matrix that call `FRAMEWORK_*`.
- **Why:** Same framework as `HomeView` / shell; fewer bugs and duplicate requests.

### W2 — Kill `window.complianceDataFetchPromise`

- **What:** Move deduped prefetch into **`complianceStore`** private promise or action mutex.
- **Where:** `AllCompliance.vue`, `ComplianceDashboard.vue`, `ComplianceApprover.vue`, `ComplianceTailoring.vue`, `CopyCompliance.vue`, etc.
- **Why:** Testable, visible in DevTools, no global leaks.

### W3 — Single writer for compliance dashboard cache

- **What:** `loadComplianceDashboard({ force })` updates **`dashboardsStore.set('compliance', …)`** and frameworks slice.
- **Where:** `ComplianceDashboard.vue`.
- **Why:** Matches existing TTL cache pattern in `stores/dashboards.js`.

---

## 23. File-by-file migration (order suggestion)

1. `stores/compliance.js` — create with prefetch + hierarchy + status fields.  
2. `AllCompliance.vue` — pilot consumer; remove direct `complianceDataService` / `window` usage.  
3. `Compliances.vue`, `AuditManagementView.vue` — share actions.  
4. `ComplianceApprover.vue`, `ComplianceDetails.vue` — approvals + detail cache + permission refactor pilot.  
5. `CreateCompliance.vue`, `EditCompliance.vue`, `CopyCompliance.vue` — call actions; **invalidate** on success.  
6. `ComplianceDashboard.vue`, `ComplianceKPINew.vue` — dashboard/KPI bundles.  
7. `OrganizationalControls.vue`, `CrossFrameworkMapping.vue`, `BaselineConfiguration.vue`.  
8. `PopupDemo.vue`, `ComplianceDebug.vue` — last or out of scope for production.

---

## 24. Step-by-step implementation (safe order)

1. Add **`complianceStore`** with `status`, `error`, `lastFetched`, `isLoading`, `isRefreshing`.  
2. Implement **`prefetchComplianceDomain`** (replaces `fetchAllComplianceData` usage from components).  
3. Align **`appDataStore.fetchCompliances`** with the same internal helper or call `complianceStore` (document one pattern).  
4. Migrate **`FRAMEWORK_*`** reads/writes to **`useFrameworkStore`** page by page.  
5. Move hierarchy fetches to **`fetchHierarchy`**.  
6. Wire **mutations** to **`invalidateAfterComplianceMutation`**.  
7. Dashboard: single action + **`dashboardsStore`**.  
8. Introduce **`permissionStore`** incrementally; replace **`USER_ROLE`** string checks on pilot screens.  
9. Regression-test all routes in §1.2.  
10. Remove dead globals and duplicate caches.

---

## 25. Testing checklist

- [ ] Each route in §1.2 loads without console errors.  
- [ ] Framework selected on **Home** matches compliance pages after navigation.  
- [ ] Cache-first: second visit uses cache within TTL; **force** refresh refetches.  
- [ ] **Loading** vs **refreshing** UX distinct where applicable.  
- [ ] Error + retry paths (list, detail, export, KPI).  
- [ ] Empty hierarchy / empty approvals.  
- [ ] Create → list shows new row (invalidation).  
- [ ] Approve/reject → detail + list consistent.  
- [ ] Export: start, poll, complete (and localStorage resume if kept).  
- [ ] RBAC: denied user sees safe UI + **403** handling.  
- [ ] Logout clears **`dashboardsStore`** compliance slice + **`complianceStore.reset()`**.  
- [ ] Pinia DevTools: expected keys after each flow.

---

## 26. Priority matrix

| Priority | Work |
|----------|------|
| **P0** | `frameworkStore` everywhere; `complianceStore` prefetch replacing `window.*`; pilot `AllCompliance` |
| **P1** | Hierarchy + audit list + approvals in store; mutation invalidation |
| **P2** | KPI bundle; export job handling; `CrossFrameworkMapping` use `apiService` |
| **P3** | Component splits; deep normalization; demo/debug |

---

## 27. Developer guidelines (this module)

1. **Local:** modals, choosers, form fields, page-only filters, sidebar submenu toggles.  
2. **Pinia:** shared lists, session-aligned framework (via **`frameworkStore`**), prefetch, approvals, detail cache, dashboard writes to **`dashboardsStore`**.  
3. **API:** only inside **store actions** (or shared functions invoked by actions).  
4. **Getters:** freshness, counts, derived lists.  
5. **Actions:** fetch, mutate, invalidate, export orchestration.  
6. **Do not store:** huge transient form blobs unless multi-step requirement is explicit.  
7. **First store work:** **`complianceStore` prefetch** + **`frameworkStore` adoption**.  
8. **First component:** **`AllCompliance.vue`**.  
9. **Before next module:** P0 + P1 checklist green; no duplicate prefetch; framework sync verified.

---

## 28. Backend reference (read-only)

`grc_backend/grc/routes/Compliance/compliance_views.py` — RBAC decorators and compliance APIs. Frontend **`permissionStore`** should eventually align with these capabilities to reduce string role checks.

---

## 29. Revision history

| Date | Author | Note |
|------|--------|------|
| 2026-04-28 | Engineering audit | Initial Markdown export from compliance Pinia audit |
