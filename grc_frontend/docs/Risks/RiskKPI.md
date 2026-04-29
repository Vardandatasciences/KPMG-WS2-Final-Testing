# Risk KPI Dashboard — Pinia & state audit

**Component:** [`src/components/Risk/RiskKPI.vue`](../../src/components/Risk/RiskKPI.vue)  
**Route:** `/risk/riskkpi`  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | Large **KPI dashboard** for risk: many independent metrics (active risks, exposure, mitigation, recurrence, remediation, cost, identification rate, etc.); mixes **`apiService.get`**, raw **`fetch`**, and **`axios.get`**; period selectors per widget. |
| 1.2 | Route | `/risk/riskkpi` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | Many chart/gauge widgets (inline template) |
| 1.5 | Reusable | Chart fragments inline |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk** performance read-only analytics |
| 1.8 | Domain | **Risk** KPI; regulatory-style metrics |

---

## 2. Files analysed

- [`src/components/Risk/RiskKPI.vue`](../../src/components/Risk/RiskKPI.vue)
- [`src/config/api.js`](../../src/config/api.js) (`RISK_*` KPI constants)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** (large) |
| 2.4 | `computed` | Extensive |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | **Inconsistent HTTP clients:** `apiService`, `fetch`, `axios` |
| 2.13 | Loading/error | Per-widget loading often local; inconsistent global error |
| 2.14 | RBAC | Implicit |

---

## 4. Current data flow

- **Mounted / methods:** each KPI widget triggers its own fetch (many sequential or parallel uncontrolled).  
- **Period state:** `data` fields like `mitigationCostPeriod`, `identificationPeriod`, `dueMitigationPeriod` change query strings for some `fetch` calls.  
- **Responses:** stored across many `data` keys backing charts.

**Problem:** Network waterfall, duplicate base URLs, hard to cache-coordinate.

---

## 5. Variable inventory (pattern)

| Class | Examples | Local? | Pinia? |
|-------|----------|--------|--------|
| Period selectors | `mitigationCostPeriod`, … | Yes | Optional `risk.kpiFilters` if shared with RiskDashboard |
| Widget series data | many keys in `data` | No | **`risk.kpiPayload` slices** or normalized `kpiByWidgetId` |
| Loading flags | per-widget | Yes | Or `kpiStatusByKey` in store |

---

## 6. Local state to keep

- UI-only: expanded sections, tab index, chart hover state, **period dropdown selections** unless shared globally.

---

## 7. State to move to Pinia

- **All KPI API results** + **single coordinated load** (`fetchRiskKpiDashboard({ periods, force })`).  
- **Unified error** object per widget key for retry UI.

---

## 8. API call inventory (from codebase grep — consolidate in store)

| Purpose | Endpoint / pattern | Client | Suggested action |
|---------|-------------------|--------|------------------|
| KPI bundle | `API_ENDPOINTS.RISK_KPI_DATA` | `apiService.get` | include in batch |
| Active risks KPI | `API_ENDPOINTS.RISK_ACTIVE_RISKS_KPI` | `fetch` | batch |
| Exposure trend | `API_ENDPOINTS.RISK_EXPOSURE_TREND` | `fetch` | batch |
| Reduction trend | `API_ENDPOINTS.RISK_REDUCTION_TREND` | `apiService.get` | batch |
| High criticality | `API_ENDPOINTS.RISK_HIGH_CRITICALITY` | `fetch` | batch |
| Mitigation completion KPI | `API_ENDPOINTS.RISK_MITIGATION_COMPLETION_RATE_KPI` | `fetch` | batch |
| Avg remediation | `API_ENDPOINTS.RISK_AVG_REMEDIATION_TIME` | `fetch` | batch |
| Recurrence | `API_ENDPOINTS.RISK_RECURRENCE_RATE` | `fetch` | batch |
| Avg incident response | `API_ENDPOINTS.RISK_AVG_INCIDENT_RESPONSE_TIME` | `fetch` | batch |
| Mitigation cost | `/api/risk/mitigation-cost/?timeRange=` | `fetch` | batch |
| Identification rate | `/api/risk/identification-rate/?timeRange=` | `fetch` | batch |
| Due mitigation | `/api/risk/due-mitigation/?timeRange=` | `fetch` | batch |
| Classification accuracy | `API_ENDPOINTS.RISK_CLASSIFICATION_ACCURACY` | `fetch` | batch |
| Improvement initiatives | `${baseUrl}/api/risk/improvement-initiatives/` | `fetch` | batch |
| Impact | `${baseUrl}/api/risk/impact/` | `fetch` | batch |
| Severity | `API_ENDPOINTS.RISK_SEVERITY` | `fetch` | batch |
| Exposure score | `API_ENDPOINTS.RISK_EXPOSURE_SCORE` | `fetch` | batch |
| Resilience | `${baseUrl}/api/risk/resilience/` | `fetch` | batch |
| Assessment frequency | `API_ENDPOINTS.RISK_ASSESSMENT_FREQUENCY` | `fetch` | batch |
| Assessment consensus | `API_ENDPOINTS.RISK_ASSESSMENT_CONSENSUS` | `fetch` | batch |
| Approval rate cycle | `${baseUrl}/api/risk/approval-rate-cycle/` | `apiService.get` | batch |
| Register update frequency | `${baseUrl}/api/risk/register-update-frequency/` | `fetch` | batch |
| Recurrence probability | `${baseUrl}/api/risk/recurrence-probability/` | `apiService.get` | batch |
| Tolerance thresholds | `${baseUrl}/api/risk/tolerance-thresholds/` | `fetch` | batch |
| Appetite | `${baseUrl}/api/risk/appetite/` | `fetch` | batch |
| Severity (axios duplicate path) | `${baseUrl}/api/risk/severity/` | `axios.get` | dedupe with above |
| Identification rate KPI fn | `API_ENDPOINTS.RISK_IDENTIFICATION_RATE_KPI()` | `axios.get` | dedupe |

**Standardize on `apiService`** (or one wrapper) inside Pinia actions for auth/credentials consistency.

---

## 9–12. Store design

**State (example):**

```js
kpi: {
  byKey: {},       // e.g. { exposureTrend: {...}, ... }
  statusByKey: {},
  lastFetchedByKey: {},
  globalStatus: 'idle',
  globalError: null
}
```

**Action:** `fetchRiskKpiPage({ periods, force })` using `Promise.allSettled` to avoid one failure blanking all.

**Getters:** `kpisReady`, `failedKpiKeys`.

---

## 13. Cache-first

- Per-widget TTL **1–5 min** (metrics).  
- On period change: invalidate only affected keys.

---

## 14. Repeated API calls

- Risk identification / severity may appear twice (`fetch` vs `axios`) — **dedupe** in store.  
- Navigating away and back may refetch all — **cache** with TTL.

---

## 15–18. Drilling / forms / tables / charts

**Charts are the page** — store holds **data**; components map to chart props locally.

---

## 19. RBAC

`view_risk_kpi` style permission when `permissionStore` exists.

---

## 20. Async UI

- Global skeleton until `globalStatus === 'success'` OR partial render with per-card spinners.  
- Retry per failed key.

---

## 21. Optimistic UI

No.

---

## 22. Smart vs presentational

Split each KPI card into dumb component: `props: { series, loading, error }` + emit `retry`.

---

## 23. Normalization

`byKey` map is sufficient; avoid huge nested duplication.

---

## 24–27. Migration / priority

**Priority:** Medium–High (large refactor surface).  
**Steps:** introduce store batch → replace `fetch`/`axios` gradually per widget group (financial, operational, …).

---

## 28. Testing checklist

- Each period change triggers only affected APIs.  
- One endpoint failure leaves others visible.  
- Auth headers consistent (no raw `fetch` missing credentials).  
- Performance: parallel cap (e.g. max 6 concurrent).

---

## 29. Guidelines

- **Do not** leave three HTTP clients long-term.  
- **Do** centralize in Pinia actions for cache + retry + security.
