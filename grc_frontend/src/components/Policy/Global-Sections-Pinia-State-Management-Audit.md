# Global Sidebar Sections — Pinia State Management Audit & Migration Plan

**Scope requested:** `Sidebar.vue` block lines 409–440  
Includes these sections/routes:

1. `Document Handling` → `/document-handling`
2. `Data Retention` → `/retention/dashboard`
3. `KPIs` → `/kpis`
4. `Data Analysis` → `/data-analysis`
5. `AI Privacy Analysis` → `/ai-privacy-analysis`

---

## 1. Page/Module Summary

### 1.1 What these pages do

- **Document Handling:** company folder/subfolder/document listing, counts, file preview/download/delete, folder CRUD.
- **Data Retention:** lifecycle dashboard overview with expiring/archived/paused/audit-trail widgets.
- **Global KPIs (`/kpis`):** all-module KPI view and framework filter.
- **Data Analysis:** framework-based data inventory analytics + export.
- **AI Privacy Analysis:** framework-based privacy analysis and report export/download.

### 1.2 Routes and components

| Route | Component |
|---|---|
| `/document-handling` | `components/DocumentHandling/DocumentHandling.vue` |
| `/retention/dashboard` | `components/Retention/RetentionLifecycleDashboard.vue` |
| `/kpis` | `components/AiKpis/kpi.vue` |
| `/data-analysis` | `components/DataAnalysis/dataAnalysis.vue` |
| `/ai-privacy-analysis` | `components/DataAnalysis/aiPrivacyAnalysis.vue` |

### 1.3 Parent/layout

- All are route-level pages loaded in app shell (`App.vue` + `Sidebar.vue` + `router-view`).

### 1.4 Workflow mapping

- Document lifecycle and storage navigation
- Retention and governance dashboarding
- Cross-module KPI aggregation
- Data inventory and privacy analytics

---

## 2. Current Vue Implementation Summary

### 2.1 API usage

- `DocumentHandling.vue`: uses `axiosInstance` + `API_ENDPOINTS` from config.
- `RetentionLifecycleDashboard.vue`: uses raw `axios` with explicit API base URL and auth headers.
- `kpi.vue`: raw `axios` and API endpoints for KPI retrieval.
- `dataAnalysis.vue`: `axiosInstance` + API endpoints.
- `aiPrivacyAnalysis.vue`: raw `axios` + API base URL.

### 2.2 Pinia usage

- No direct dedicated Pinia store usage in these pages today.
- Existing global stores (`dashboards`, `appData`) are not primary orchestrators for these sections.

### 2.3 State primitives

- Mostly local component state (`data`/`ref`/computed) and component-level request orchestration.

### 2.4 RBAC/access

- Route-level `requiresAuth` exists.
- Component-level permission centralization appears limited/inconsistent across these pages.

---

## 3. Current Data Flow

1. Page route loads.
2. Page fetches framework/options and then page-specific datasets.
3. Results stay in local state.
4. Each page performs own refresh/error handling.

### Current risk areas

- repeated framework fetches (`/api/frameworks/`) in multiple pages
- mixed HTTP clients (`axios`, `axiosInstance`) across pages
- no shared cache invalidation strategy for cross-page shared data (frameworks, KPI summary slices)

---

## 4. Variable Inventory (Grouped)

| Variable group | Typical examples | Type | Keep local | Move to Pinia |
|---|---|---|---|---|
| Framework selectors | selected framework id/name | shared context | Partial | Yes |
| Core datasets | documents, retention cards, kpi rows, analysis results | shared API data (if reused) | No | Yes (where reused) |
| Export/download state | isExporting, fileUrl, download progress | local async UI | Yes | Optional |
| Folder tree UI states | selected folder, expanded nodes, dialogs | local UI | Yes | No |
| Table/search/filter | query, sort, page, selected row | local UI | Yes | No unless persisted/shared |

---

## 5. State Classification

### 5.1 Keep local

- Dialog/modals open state
- Selected row for immediate action
- Local search input and transient filter controls
- Temporary download spinner/button states

### 5.2 Move to Pinia

- Shared framework options and selected framework context
- reusable KPI/analytics payloads used across multiple global pages
- document counts/summary if displayed outside document page in future

### 5.3 API/server data via Pinia actions

- frameworks list
- global KPI summary
- retention overview datasets
- data-analysis and ai-privacy result sets when reused/cached across navigation

---

## 6. API Call Inventory (Observed families)

- `DocumentHandling.vue`:
  - `FRAMEWORKS`, folder/subfolder list/create/delete, document list/count/download/delete
- `RetentionLifecycleDashboard.vue`:
  - retention dashboard overview/expiring/archived/paused/audit-trail endpoints
- `kpi.vue`:
  - `KPIS_ALL`, `KPIS_FRAMEWORKS`
- `dataAnalysis.vue`:
  - frameworks + `DATA_ANALYSIS(frameworkId)` + export endpoint
- `aiPrivacyAnalysis.vue`:
  - frameworks + AI privacy analysis endpoint + report download

Recommendation: centralize shared API families into a store action layer.

---

## 7. Recommended Pinia Store Design

For these global sidebar pages, avoid creating too many stores. Recommended:

### 7.1 `frameworkStore` (existing)

- Use as shared selected-framework source for data analysis, AI privacy, KPIs where applicable.

### 7.2 `globalAnalyticsStore` (new, focused)

Suggested file: `src/stores/globalAnalytics.js`

**Purpose:**
- global KPI datasets
- data analysis datasets
- ai privacy analysis datasets
- shared framework option list for these pages

**State (high-level):**
- `frameworks`
- `kpis`
- `dataInventory`
- `privacyAnalysis`
- `status`, `isLoading`, `isRefreshing`, `error`, `lastFetched`

### 7.3 `documentStore` (optional new, only if module expands)

If Document Handling grows (already sizeable), a dedicated store is justified:
- folder/subfolder tree
- document list/counts
- document action status

### 7.4 `retentionStore` (optional minimal)

Use only if retention dashboard gets multi-page expansion; otherwise keep in `globalAnalyticsStore` as retention slice.

---

## 8. Recommended State Structure (starter)

```js
state: () => ({
  frameworks: [],
  kpis: null,
  dataInventory: null,
  privacyAnalysis: null,
  retention: {
    overview: null,
    expiring: [],
    archived: [],
    paused: [],
    auditTrail: []
  },
  documentHandling: {
    folders: [],
    subfoldersByFolderId: {},
    documents: [],
    counts: null
  },
  status: 'idle', // idle | loading | success | error
  isLoading: false,
  isRefreshing: false,
  error: null,
  lastFetched: {
    frameworks: null,
    kpis: null,
    dataInventory: null,
    privacyAnalysis: null,
    retention: null,
    documents: null
  }
})
```

---

## 9. Recommended Getters

- `isFrameworksFresh`
- `kpiCards`
- `retentionSummary`
- `documentCounts`
- `documentsBySelectedFolder`
- `privacyRiskBreakdown`

---

## 10. Recommended Actions

- `fetchFrameworks({ force })`
- `fetchGlobalKpis({ frameworkId, force })`
- `fetchDataInventory({ frameworkId, force })`
- `fetchAIPrivacyAnalysis({ frameworkId, force })`
- `fetchRetentionDashboard({ force })`
- `fetchDocumentFolders({ force })`
- `fetchSubfolders(folderId, { force })`
- `fetchDocuments(params, { force })`
- `createFolder(payload)` / `createSubfolder(payload)`
- `deleteFolder(id)` / `deleteSubfolder(id)` / `deleteDocument(id)`
- `downloadDocument(id)`
- `invalidateGlobalSections(scope)`

---

## 11. Cache-first Plan

Recommended TTL:
- frameworks: 15–30 min
- global KPIs: 1–5 min
- data analysis/privacy analysis: 5–15 min (unless force refresh)
- retention dashboard: 1–5 min
- document lists/counts: 30–120 sec

Pattern:
1. serve fresh cache
2. stale + existing → background refresh
3. empty → loading
4. force refresh supported
5. invalidate on create/delete/export actions where needed

---

## 12. Repeated API Calls / Gaps

| Issue | Current impact | Recommendation |
|---|---|---|
| frameworks fetched independently in multiple pages | duplicate calls | central `fetchFrameworks` action |
| mixed HTTP clients (`axios` vs `axiosInstance`) | inconsistent interceptors/error handling | standardize on one client via shared store action layer |
| local-only cache strategy | no cross-page cache consistency | store-level TTL + invalidation |
| export/download logic spread per page | duplicate logic | shared helper in store/composable |

---

## 13. Prop Drilling Analysis

No major prop-drilling issue; primary issue is duplicated API orchestration and missing shared state layer.

---

## 14. Forms Analysis

Minimal heavy forms in these sections except folder/subfolder create in Document Handling:
- keep input fields local
- move mutation API and cache invalidation into store actions

---

## 15. Tables / Filters / Pagination

- Keep local for page-only behaviors.
- If cross-navigation persistence needed (e.g., remember document filters), add a small persisted filter slice in store.

---

## 16. Dashboard/Chart Plan

- KPI + retention + analysis pages should use store-backed cache-first actions.
- Keep visualization-only controls local (chart type, expanded card).

---

## 17. RBAC/Permission Plan

- Keep route auth guard.
- Add centralized permission helper if module-specific capability restrictions are needed at button level (delete folder/document, export actions).

---

## 18. Async UI Improvements

- Standardize `isLoading` vs `isRefreshing`
- Provide retry CTA for data analysis/privacy/retention failures
- Add duplicate-submit prevention for folder/subfolder creation
- Add clear empty states for no documents/no analysis results

---

## 19. Optimistic UI Possibilities

Safe:
- local UI toggles (expand/collapse, tab switches)

Avoid optimistic:
- destructive document delete
- retention governance actions
- privacy analysis result replacement

---

## 20. Smart vs Presentational Plan

Priority smart/container pages:
- `DocumentHandling.vue`
- `RetentionLifecycleDashboard.vue`
- `dataAnalysis.vue`
- `aiPrivacyAnalysis.vue`
- `AiKpis/kpi.vue`

Move reusable data logic into store/composables; keep rendering components dumb where possible.

---

## 21. State Normalization Recommendations

Only where useful:
- `documentsById`
- `documentIdsByFolderId`
- `subfolderIdsByFolderId`

Do not over-engineer first iteration.

---

## 22. What / Where / Why Plan

### Improvement 1
**What:** Centralize framework + analytics fetches in `globalAnalyticsStore`.  
**Where:** `/kpis`, `/data-analysis`, `/ai-privacy-analysis`, `/retention/dashboard`.  
**Why:** reduce duplicate framework/API calls and ensure consistent cache behavior.  
**Priority:** High.

### Improvement 2
**What:** Introduce store-backed document handling state/actions.  
**Where:** `DocumentHandling.vue`.  
**Why:** folder/document CRUD flows need predictable invalidation and less component complexity.  
**Priority:** High.

### Improvement 3
**What:** Keep UI-only interaction state local.  
**Where:** all five pages.  
**Why:** avoids unnecessary global store bloat.  
**Priority:** Medium.

---

## 23. File-by-file Migration Plan

| File | Current issue | Change needed | Priority |
|---|---|---|---|
| `components/DocumentHandling/DocumentHandling.vue` | large component with CRUD + fetch + download logic | move data/actions to store; keep UI interactions local | High |
| `components/Retention/RetentionLifecycleDashboard.vue` | direct axios endpoints and auth logic local | store action wrappers + unified error/loading handling | High |
| `components/AiKpis/kpi.vue` | direct KPI fetches without shared cache | use `globalAnalyticsStore.fetchGlobalKpis` | High |
| `components/DataAnalysis/dataAnalysis.vue` | direct framework + analysis + export orchestration | use store actions + cache-first | High |
| `components/DataAnalysis/aiPrivacyAnalysis.vue` | similar direct orchestration | use store actions + shared framework cache | High |

---

## 24. Step-by-step Implementation Plan

1. Add `globalAnalyticsStore` with shared framework + analytics state.
2. Add cache-first actions for `/kpis`, `/data-analysis`, `/ai-privacy-analysis`, retention.
3. Migrate `kpi.vue`, `dataAnalysis.vue`, `aiPrivacyAnalysis.vue` to store actions.
4. Introduce document-handling store slice (or `documentStore`).
5. Migrate `DocumentHandling.vue` CRUD and list actions.
6. Migrate retention dashboard fetches.
7. Add invalidation and refresh rules.
8. Remove duplicated direct API calls.
9. Validate end-to-end and clean dead code.

---

## 25. Testing Checklist

- [ ] `/document-handling` loads and CRUD actions work
- [ ] `/retention/dashboard` cards/lists load and refresh correctly
- [ ] `/kpis` loads with cache-first behavior
- [ ] `/data-analysis` and `/ai-privacy-analysis` framework filtering works
- [ ] shared framework list is reused (no duplicate bursts)
- [ ] loading/refresh/error/empty states handled properly
- [ ] destructive actions (delete) show confirmations and update state
- [ ] export/download links work post-migration
- [ ] state visible and correct in Pinia DevTools

---

## 26. Priority Matrix

- **High:** shared analytics store, framework-fetch dedupe, document handling store-backed CRUD
- **Medium:** retention/store refinement, permission helper standardization
- **Low:** UI state persistence enhancements

---

## 27. Final Developer Guidelines

1. Keep local UI state local.
2. Move shared framework + analytics + document datasets to Pinia.
3. Use one HTTP client strategy through store actions.
4. Add TTL + invalidation for all reusable data.
5. Use getters for derived dashboard/cards/counts.
6. Keep destructive operations server-authoritative (no risky optimistic updates).
7. Migrate analytics pages first, then document handling, then retention refinements.

