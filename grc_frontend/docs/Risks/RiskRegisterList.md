# Risk Register List — Pinia & state audit

**Component:** [`src/components/Risk/RiskRegisterList.vue`](../../src/components/Risk/RiskRegisterList.vue)  
**Route:** `/risk/riskregister-list` (`RiskRegisterList`)  
**Parent:** `App.vue` → `router-view` (keep-alive included).

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | Tabular view of the risk register with client-side search, column visibility, retention-aware export, and optional cache via `riskDataService`. |
| 1.2 | Route | `/risk/riskregister-list` |
| 1.3 | Parent | `App.vue` layout; no dedicated Risk layout. |
| 1.4 | Child components | `DynamicTable`, `PopupModal` |
| 1.5 | Reusable | `DynamicTable`, shared popup module |
| 1.6 | Layout | Global sidebar + navbar only |
| 1.7 | Workflow | Browse/search register; export; navigate to create/view/tailoring via actions in table/links |
| 1.8 | Domain | **Risk** register; touches **retention** config, **notifications** on export |

---

## 2. Files analysed

- [`src/components/Risk/RiskRegisterList.vue`](../../src/components/Risk/RiskRegisterList.vue)
- [`src/services/riskService.js`](../../src/services/riskService.js)
- [`src/router/index.js`](../../src/router/index.js)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API style | **Options API** (`export default`) |
| 2.2 | `ref` | No (Options `data`) |
| 2.3 | `reactive` | No |
| 2.4 | `computed` | Yes — `exportFormatLabel`, `filteredColumnDefinitions`, `columnSelection`, `tableColumns`, `filteredRisks`, `tableData` |
| 2.5 | `watch` | Yes — `watch` option (e.g. lifecycle sync) |
| 2.6 | `props` | No |
| 2.7 | `emits` | No |
| 2.8 | `provide`/`inject` | No |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | **Direct** via `apiService` + local `axiosInstance` shim; **`riskDataService`** for cache |
| 2.12 | Prop drilling | Minimal |
| 2.13 | Loading/error | `loading` flag; errors mostly console / user messaging varies |
| 2.14 | RBAC | Not explicit; relies on API / global interceptor |

---

## 4. Current data flow

1. **Start:** `mounted` / `activated` → `loadRisks` (or equivalent) checks `riskDataService.hasValidCache()`.  
2. **If cache hit:** `this.risks = riskDataService.getData('risks')`.  
3. **If miss:** `GET` `API_ENDPOINTS.RISKS_FOR_DROPDOWN` → assign `this.risks`; optionally populate `riskDataService`.  
4. **Retention:** `GET` `/api/retention/page-configs/` for export gating.  
5. **Export:** `POST` `API_ENDPOINTS.EXPORT_RISK_REGISTER` → may `fetch` file URLs.  
6. **Notify:** `POST` `API_ENDPOINTS.PUSH_NOTIFICATION` after export.  
7. **Child table:** `filteredRisks` / `tableData` computed from `this.risks` (client filter/sort).

**Stale data risk:** Register can disagree with Pinia (`stores/risk.js`) and `riskDataService` until all writers invalidate the same cache.

---

## 5. Variable inventory (key fields)

| Variable | Declared | Purpose | Type | Local? | Pinia? | Store / action | Priority |
|----------|----------|---------|------|--------|--------|----------------|----------|
| `risks` | `data` | Rows | API | No | Yes | `risk.state.risks` + `fetchRisks` | High |
| `searchQuery` | `data` | Search box | UI | Yes | No | — | — |
| `loading` | `data` | Page load | UI | Yes | No* | *or derive from `risk.risksStatus` | Medium |
| `visibleColumnKeys`, `showColumnEditor`, `columnSearchQuery` | `data` | Column UI | UI | Yes | No | — | — |
| `selectedExportFormat`, `isExportDropdownOpen` | `data` | Export UI | UI | Yes | No | — | — |
| `riskRetentionEnabled`, `riskRetentionWarningShown` | `data` | Retention UX | Mixed | Yes | No | — | Low |
| `filteredRisks` | `computed` | Client filter | Derived | Yes | Optional getter if reused | Low |

---

## 6. Local state to keep (5.1)

- Search query, column picker, export dropdown, modal toggles, column search.  
**Reason:** Single-screen UI; no cross-route requirement.

---

## 7. State to move to Pinia (5.2 / 5.3)

- **Canonical `risks` array** + fetch status + `lastFetched` + TTL + `error`.  
- Optional: **retention flag** if other risk pages need the same export gate without re-fetch.

---

## 8. API call inventory

| Purpose | Endpoint / constant | Method | Where | Move to Pinia? | Recommended |
|---------|---------------------|--------|-------|----------------|-------------|
| List risks | `API_ENDPOINTS.RISKS_FOR_DROPDOWN` | GET | `loadRisks` path | Yes | `risk.fetchRisks({ force })` |
| Page retention config | `/api/retention/page-configs/` | GET | export flow | Optional | `risk.fetchRetentionPageConfig('risk_register')` or shared `ui/compliance` slice |
| Export register | `API_ENDPOINTS.EXPORT_RISK_REGISTER` | POST | export | Yes (or service) | `risk.exportRegister(payload)` |
| Download export file | `result.file_url` / `safeFileUrl` | `fetch` | export | No (blob handling local) | Component keeps blob; store returns URL |
| Push notification | `API_ENDPOINTS.PUSH_NOTIFICATION` | POST | after export | Optional | Shared notification helper |

**Repeated calls:** Same list endpoint as `riskService.fetchRisks`, `TailoringRisk`, Pinia `fetchAllRisks` — consolidate.

---

## 9–12. Store design, getters, actions (this page)

**Store:** [`src/stores/risk.js`](../../src/stores/risk.js) (`useRiskStore`).

**State fields:** `risks`, `risksStatus`, `risksLastFetched`, `risksError`, `isLoading`, `isRefreshing`.

**Getters:** `filteredRisksLocal` stays component-side unless server-side search is added; store getter `riskCount`, `isRisksStale`.

**Actions:** `fetchRisks({ force })`, `invalidateRisks()` (called from CreateRisk/Tailoring after POST).

---

## 13. Cache-first (Pinia)

| Data | TTL | When use cache | Invalidate |
|------|-----|----------------|------------|
| `risks` | 1–5 min | Enter list; cache warm | After create/update/delete risk |

Use `isRefreshing` when `risks.length > 0` and `force` refetch.

---

## 14. Repeated API calls

- `RISKS_FOR_DROPDOWN` via `riskDataService` + this component + others → **one Pinia action**.

---

## 15. Prop drilling

None significant.

---

## 16. Forms

No full-page create form; export is a **pseudo-form** (format selection). Keep `selectedExportFormat` local.

---

## 17. Tables / filters / pagination

| Item | Detail |
|------|--------|
| Table | `DynamicTable` fed by `tableData` |
| Data source | `risks` (API/cache) |
| Search | `searchQuery` → `filteredRisks` (client-side) |
| Sort | Client sort on `CreatedAt` in computed |
| Pagination | Not server paginated in current pattern — if added, pass params to `fetchRisks` action |

---

## 18. Dashboard / charts

N/A on this page.

---

## 19. RBAC

Defer to API + interceptor; optional `permissionStore.can('view_risk_register')` for button visibility.

---

## 20. Async UI

Improve: tie skeleton to `risksStatus === 'loading'`; retry on export failure; empty state when `risks.length === 0`.

---

## 21. Optimistic UI

Not recommended for export (file generation) or list deletion without confirmation.

---

## 22. Smart vs presentational

- **Today:** `RiskRegisterList` mixes fetch, retention, export, table config → **smart**.  
- **Target:** thin container calling Pinia; optional dumb wrapper around `DynamicTable` with props + events.

---

## 23. Normalization

Not required at current list sizes; optional `risksById` if workflow joins by id frequently.

---

## 24. What / where / why (samples)

1. **What:** Move `risks` load to `risk.fetchRisks`. **Where:** `RiskRegisterList.vue` `loadRisks`. **Why:** Single cache with TTL; removes divergence from `riskService`. **Priority:** High.  
2. **What:** Keep `visibleColumnKeys` local. **Where:** same file `data`. **Why:** User preference could later sync to backend via retention API — still not global store. **Priority:** Low.

---

## 25. File-by-file migration

| File | Change |
|------|--------|
| `RiskRegisterList.vue` | Replace `riskDataService` branch with `useRiskStore` + `storeToRefs`; call `fetchRisks` on `activated` with staleness check |
| `stores/risk.js` | Implement `fetchRisks`/`invalidateRisks` per §8 |

---

## 26. Priority matrix

- **High:** List fetch + invalidation.  
- **Medium:** Export action wrapper + consistent error UI.  
- **Low:** Column prefs persistence.

---

## 27. Implementation steps

1. Implement `fetchRisks` + `invalidateRisks` in `risk` store.  
2. Switch component to store.  
3. Remove duplicate cache write if store owns data.  
4. Test activate/deactivate with `keep-alive`.  
5. Test after creating risk from another route.

---

## 28. Testing checklist

- Load with empty cache / warm cache.  
- Search + column hide/show.  
- Export each format (if enabled).  
- Error path when API fails.  
- After `CreateRisk`, list shows new row without stale cache.  
- Pinia DevTools shows single `risks` source.

---

## 29. Developer guidelines (this page)

- **Local:** search, columns, export UI.  
- **Pinia:** `risks`, fetch/error/stale metadata.  
- **Do not store:** export blob in Pinia.  
- **First refactor:** align this page with store before refactoring `RiskInstances` in parallel if possible — or do both together since same endpoints pattern.
