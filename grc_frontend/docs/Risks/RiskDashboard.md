# Risk Dashboard — Pinia & state audit

**Component:** [`src/components/Risk/RiskDashboard.vue`](../../src/components/Risk/RiskDashboard.vue)  
**Route:** `/risk/riskdashboard`  
**Parent:** `App.vue` → `router-view` (keep-alive).

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | Executive-style risk dashboard: filters (framework, policy, time, category, priority), KPI cards, charts (doughnut/bar/line), heatmap, category/mitigation analytics, export, color-blind support. |
| 1.2 | Route | `/risk/riskdashboard` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | `CustomDropdown`, `DashboardChartCard`, Chart.js wrappers |
| 1.5 | Reusable | `CustomDropdown`, shared chart card CSS component |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk** analytics; **framework/policy** context |
| 1.8 | Domain | **Risk** dashboard; reads **framework** selection (today mixed **Vuex** + Pinia) |

---

## 2. Files analysed

- [`src/components/Risk/RiskDashboard.vue`](../../src/components/Risk/RiskDashboard.vue)
- [`src/stores/risk.js`](../../src/stores/risk.js)
- [`src/stores/framework.js`](../../src/stores/framework.js)
- [`src/stores/appData.js`](../../src/stores/appData.js) (referenced)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Hybrid:** `export default` + **`setup()`** using `ref`, `reactive`, `computed`, `watch` |
| 2.2–2.5 | Composition | Heavy `watch` on filters, charts, colorblind mode |
| 2.6–2.8 | props/emits/inject | Minimal |
| 2.9 | Pinia | **`useRiskStore`**, **`useAppDataStore`** |
| 2.9b | Vuex | **`useStore` (Vuex)** still used for framework id sync — **technical debt** |
| 2.10–2.11 | API | Local `axios` shim → `apiService`; multiple `GET`/`POST` under `/api/risk/...` and `API_ENDPOINTS.*` |
| 2.13 | Loading/error | Partial; `AccessUtils.handleApiError`; `showSkeleton` computed vs metrics |
| 2.14 | RBAC | `AccessUtils` around fetches |

---

## 4. Current data flow

1. **Framework/policy:** Fetches `/api/risk/frameworks-for-filter/`, `FRAMEWORK_GET_SELECTED`, `/api/risk/policies-for-filter/`. Vuex store updated in some paths (see file logs).  
2. **Categories:** `API_ENDPOINTS.RISK_CATEGORIES_DROPDOWN`.  
3. **Metrics:** `riskStore.fetchDashboardMetrics` / `fetchTrendData` (store) + component fetches for identification rate, mitigation completion, mitigation cost, heatmap, analytics POST.  
4. **Filters:** `reactive` `filters` object watched → refetch charts.  
5. **Charts:** Mix of demo/static category blocks and API-driven series.

**Risk:** Duplicate source of truth for **selected framework** (Vuex vs `useFrameworkStore`).

---

## 5. Variable inventory (key)

| Variable / area | Declared | Purpose | Local? | Pinia? |
|-----------------|----------|---------|--------|--------|
| `filters` (framework, policy, timeRange, category, priority) | `reactive` | API query params | Partial | Sync **framework** with `frameworkStore`; rest local OR `risk.filters` if URL sync |
| `riskStore.metrics` | Pinia | Summary KPIs | No | Already store |
| Chart refs (`donutChartData`, …) | `reactive`/`ref` | Chart.js | Yes | No |
| Popups (`showCategoryPopup`, `heatmapRisks`, …) | `ref` | UI | Yes | No |
| `store` (Vuex) | `useStore()` | Framework | **Migrate** | `useFrameworkStore` |

---

## 6. Local state to keep

- Chart axis selections, popups, export UI, colorblind toggle consumption (attribute on `document`).  
- Transient chart animation keys (`categoryChartKey`).

---

## 7. State to move to Pinia

- **All dashboard API payloads** tied to filters: metrics, trend, heatmap, analytics response — extend `risk` store slices (`dashboardHeatmap`, `dashboardAnalytics`, etc.) OR single `fetchDashboardBundle(filters, force)`.  
- **Remove Vuex** dependency; use **`useFrameworkStore` + `storeToRefs`**.

---

## 8. API call inventory (component + store)

| Purpose | Endpoint | Method | Location | Pinia? |
|---------|----------|--------|----------|--------|
| Frameworks filter | `/api/risk/frameworks-for-filter/` | GET | component | `risk` or `framework` |
| Selected framework | `API_ENDPOINTS.FRAMEWORK_GET_SELECTED` | GET | component | align with `frameworkStore` |
| Policies filter | `/api/risk/policies-for-filter/` | GET | component | `risk` action |
| Categories dropdown | `API_ENDPOINTS.RISK_CATEGORIES_DROPDOWN` | GET | component | `risk.fetchRiskCategories` |
| Identification rate | `/api/risk/identification-rate/` | GET | component | merge into bundle |
| Mitigation completion | `/api/risk/mitigation-completion-rate/` | GET | component | merge |
| Mitigation cost | `/api/risk/mitigation-cost/` | GET | component | merge |
| Heatmap | `API_ENDPOINTS.RISK_HEATMAP` | GET | component | `risk.fetchHeatmap` |
| Analytics | `/api/risk/analytics-with-filters/` | POST | component | `risk.postAnalyticsWithFilters` |
| Dynamic risk-by-category URLs | built `url` | GET | component | same |
| Dashboard metrics | `/api/risk/dashboard-with-filters/` | GET | **`stores/risk.js`** | extend status/TTL |
| Trend | `/api/risk/trend-over-time/` | GET | **`stores/risk.js`** | keep in action |

---

## 9–12. Store design

**Extend** `useRiskStore`:

- `dashboardStatus`, `dashboardLastFetched`, `heatmapData`, `analyticsResult`, `filterOptions` (frameworks/policies/categories) as needed.  
**Getters:** `isDashboardStale`, `activeRiskFilters` (non-`all`).  
**Actions:** `fetchDashboardPageData({ filters, force })` (internally parallel `Promise.all`).

**`useFrameworkStore`:** selected framework id/name — **single source** for filter default.

---

## 13. Cache-first

| Data | TTL | Invalidate |
|------|-----|------------|
| Metrics + charts bundle | 1–5 min | On any filter change |
| Framework/policy lists | 5–15 min | Framework org switch |

Use `isRefreshing` when charts visible.

---

## 14. Repeated API calls

- Framework list may also load elsewhere — centralize in `frameworkStore` / `risk.fetchFrameworksForRiskDashboard` once.

---

## 15. Prop drilling

None; issue is **dual global state** (Vuex + Pinia).

---

## 16–17. Forms / tables

Filter bar is **not** a classic form — treat filter `reactive` object as UI bound to store action params.

---

## 18. Dashboard / charts

**Core of page** — all series data should flow from Pinia actions; components only map to Chart.js structures.

---

## 19. RBAC

`AccessUtils` per fetch — later map to `permissionStore` for `view_risk_dashboard`.

---

## 20. Async UI

Align skeleton with `dashboardStatus`; per-widget error chips; retry on analytics POST failure.

---

## 21. Optimistic UI

Not for analytics POST.

---

## 22. Smart vs presentational

Split into `RiskDashboardContainer` (setup + store) and small presentational chart cards (props only).

---

## 23. Normalization

Optional `risksInHeatmapCell` keyed by `impact-likelihood` if data grows.

---

## 24. What / where / why

| What | Where | Why | Pri |
|------|-------|-----|-----|
| Remove Vuex `useStore` | `RiskDashboard.vue` setup | Pinia-only direction; fewer bugs | High |
| Bundle fetches | `stores/risk.js` | Fewer waterfalls; single loading state | High |

---

## 25. Migration files

- `RiskDashboard.vue` — consume store; delete Vuex.  
- `stores/risk.js` — dashboard bundle + statuses.  
- `stores/framework.js` — ensure selected framework usable here.

---

## 26–27. Priority & steps

**P0:** Vuex → `frameworkStore`.  
**P1:** Move API cluster to store actions.  
**Steps:** framework swap → bundle action → simplify watches → test filter changes.

---

## 28. Testing checklist

- Each filter change updates charts once (no duplicate network).  
- Colorblind mode redraw.  
- Access denied paths.  
- Export if present.  
- Cold vs warm navigation (`keep-alive`).

---

## 29. Guidelines

- **Never** store Chart.js instances in Pinia.  
- **Do** store serializable metrics and heatmap arrays.  
- **First change:** framework source of truth.
