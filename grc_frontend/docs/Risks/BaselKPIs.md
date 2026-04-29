# Basel KPIs — Pinia & state audit

**Component:** [`src/components/Risk/baselkpi.vue`](../../src/components/Risk/baselkpi.vue)  
**Route:** `/risk/baselkpis`  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | **Basel III** themed dashboard: gauges (`BaselGauge`), charts, tables; **`loading` in `data` remains false** in reviewed `mounted` — KPI values appear **static/demo** from `data()` rather than live APIs. |
| 1.2 | Route | `/risk/baselkpis` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | [`BaselGauge.vue`](../../src/components/Risk/BaselGauge.vue) (`props`: value, max, colors, …) |
| 1.5 | Reusable | `BaselGauge` |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | Regulatory **capital / risk** presentation (read-only demo today) |
| 1.8 | Domain | **Risk** (Basel); no backend integration in current file scan |

---

## 2. Files analysed

- [`src/components/Risk/baselkpi.vue`](../../src/components/Risk/baselkpi.vue)
- [`src/components/Risk/BaselGauge.vue`](../../src/components/Risk/BaselGauge.vue)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | **No `apiService` / `fetch` found** in `baselkpi.vue` |
| 2.13 | Loading | `loading` flag exists but not driven by API in `mounted` (only colorblind observer) |

---

## 4. Current data flow

- **Static:** `kpis` object in `data()` feeds template.  
- **Colorblind:** `MutationObserver` on `documentElement` for `data-colorblind`.

---

## 5. Variable inventory

| Variable | Purpose | Local? | Pinia? |
|----------|---------|--------|--------|
| `kpis` | All metrics | Yes (today) | **Future** when APIs exist |
| `loading` | UI | Yes | N/A until API |

---

## 6–7. Local vs Pinia (today vs future)

- **Today:** all local — no Pinia migration required for **data** until real endpoints exist.  
- **Future:** `risk.fetchBaselKpis` or `dashboardStore` slice with TTL 1–5 min.

---

## 8. API inventory

**None in component** (current). If backend adds Basel endpoints, list them here and map to Pinia.

---

## 9–13. Store (future)

When APIs arrive: `baselKpis`, `baselStatus`, `baselLastFetched`, action `fetchBaselKpis({ force })`.

---

## 14. Repeated API calls

**None** (no live API). When APIs exist, dedupe with a single `fetchBaselKpis` action.

## 15. Prop drilling

`BaselGauge` receives numeric props only — good pattern.

## 16. Forms analysis

**N/A** (no submit forms).

## 17. Tables / filters / pagination

Static ranked tables in template — **N/A** for server pagination until API exists.

## 18. Dashboard / charts

**Entire page** is charts/gauges — data currently **static** in `data().kpis`; `BaselGauge` is presentational.

## 19. RBAC / permissions

Route visible when Basel framework selected (Sidebar `isBaselFramework`); optional `permissionStore` mirror.

## 20. Async UI improvements

Wire `loading` to future fetch; skeleton cards.

## 21. Optimistic UI

**N/A** without mutations.

## 22. Smart vs presentational

`BaselGauge.vue` — **presentational** (keep). `baselkpi.vue` — will become **smart** when APIs added.

## 23. State normalization

When live data arrives, prefer flat `kpis` object in store rather than duplicating nested arrays across widgets.

## 24. What / where / why

| # | What | Where | Why | Pri |
|---|------|-------|-----|-----|
| 1 | Document “demo data” | this file | Avoid false expectation of live metrics | Low |
| 2 | When APIs added | `stores/risk.js` or new `baselStore` | Only if Basel spans beyond risk module | Future |

## 25. File-by-file migration

| File | Change |
|------|--------|
| `baselkpi.vue` | add `fetchBaselKpis` consumption when backend ready |
| `stores/risk.js` | optional `baselKpis` slice |

## 26. Priority matrix

- **Now:** documentation only.  
- **Future P0:** real API + Pinia-backed `kpis`.

## 27. Step-by-step implementation

1. Define API contract.  
2. Add store slice + TTL.  
3. Replace static `kpis` with store refs.  
4. Test with Sidebar Basel gate.

## 28. Testing checklist

Colorblind observer; chart render; future: API error/empty.

## 29. Final developer guidelines

- **Do not** invent Pinia complexity until backend contracts exist.  
- **Keep** `BaselGauge` free of data fetching.
