# Risk Instances List — Pinia & state audit

**Component:** [`src/components/Risk/RiskInstances.vue`](../../src/components/Risk/RiskInstances.vue)  
**Route:** `/risk/riskinstances-list` (redirect from `/risk/riskinstances`)  
**Parent:** `App.vue` → `router-view` (keep-alive).

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | Lists risk instances (incidents), supports retention-aware export, bulk/card views, notifications on actions, uses `riskDataService` cache when warm. |
| 1.2 | Route | `/risk/riskinstances-list` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | Table/card UI (internal template blocks) |
| 1.5 | Reusable | Patterns shared with register styling |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | Instance visibility; create instance (navigate); export |
| 1.8 | Domain | **Risk** instances; **retention**; **notifications** |

---

## 2. Files analysed

- [`src/components/Risk/RiskInstances.vue`](../../src/components/Risk/RiskInstances.vue)
- [`src/services/riskService.js`](../../src/services/riskService.js)
- [`src/utils/accessUtils.js`](../../src/utils/accessUtils.js) (403 handling)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.4 | `computed` | Filtering / view mode |
| 2.5 | `watch` | As needed |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | `apiService` + **`riskDataService`** cache read/write |
| 2.13 | Loading/error | `AccessUtils.handleApiError` on fetch/create |
| 2.14 | RBAC | Via API errors + AccessUtils |

---

## 4. Current data flow

1. Load instances: if `riskDataService.hasRiskInstancesCache()` use cache else `GET` `API_ENDPOINTS.RISK_INSTANCES`.  
2. On refresh path: `GET` again + `riskDataService.setData('riskInstances', ...)`.  
3. Retention: `GET` `/api/retention/page-configs/`.  
4. Create: `POST` `API_ENDPOINTS.CREATE_RISK_INSTANCE` (multipart) from embedded flow.  
5. Export: `POST` `API_ENDPOINTS.EXPORT_RISK_REGISTER` (same as register — verify backend semantics for instances).  
6. Notify: `PUSH_NOTIFICATION`.

---

## 5. Variable inventory (key)

| Variable | Declared | Purpose | Local? | Pinia? |
|----------|----------|---------|--------|--------|
| `instances` | `data` | Rows | No | **Yes** — `risk.riskInstances` |
| View/filter UI | `data` / `computed` | Cards/table | Yes | No |
| `loading` | `data` | UI | Yes | Or bind `risk.instancesStatus` |

---

## 6. Local state to keep

- View toggle, search, sort keys, card expansion, export dropdown, column visibility if any.

---

## 7. State to move to Pinia

- **`riskInstances` list** + fetch TTL + errors + `invalidateInstances()` after create/update elsewhere.

---

## 8. API inventory

| Purpose | Endpoint | Method | Pinia action (recommended) |
|---------|----------|--------|-----------------------------|
| List | `API_ENDPOINTS.RISK_INSTANCES` | GET | `fetchRiskInstances({ force })` |
| Retention | `/api/retention/page-configs/` | GET | optional shared |
| Create instance | `API_ENDPOINTS.CREATE_RISK_INSTANCE` | POST | `createRiskInstance` + invalidate |
| Export | `API_ENDPOINTS.EXPORT_RISK_REGISTER` | POST | `exportRiskData` or keep local |
| Notify | `API_ENDPOINTS.PUSH_NOTIFICATION` | POST | helper |

---

## 9–12. Store / getters / actions

- **State:** `riskInstances`, `instancesStatus`, `instancesLastFetched`, `instancesError`.  
- **Getters:** `instanceById` (optional).  
- **Actions:** `fetchRiskInstances`, `invalidateInstances`.

---

## 13. Cache-first

Same pattern as register: TTL 1–5 min; `force` on user refresh; invalidate on mutations.

---

## 14. Repeated calls

`RISK_INSTANCES` used here, `riskService`, `RiskResolution`, `RiskWorkflow`, `CreateRiskInstance` cache updates — unify.

---

## 15–18. Prop drilling / forms / tables / charts

- **Tables:** primary; client filters in `computed`.  
- **Charts:** N/A.

---

## 19. RBAC

403 → AccessUtils; optional permission keys for export/create.

---

## 20–21. Async / optimistic

- Disable double submit on create.  
- No optimistic list append without server confirmation.

---

## 22. Smart vs presentational

Today monolithic smart component → optional split table presentation.

---

## 23. Normalization

Optional `instancesById` for workflow joins.

---

## 24. What / where / why

| What | Where | Why | Pri |
|------|-------|-----|-----|
| Pinia instances list | store + component | Remove `riskDataService` duplication | High |

---

## 25–27. Files / priority / steps

| File | Change |
|------|--------|
| `RiskInstances.vue` | `useRiskStore` + `storeToRefs` |
| `stores/risk.js` | instances actions |

**Steps:** store → component → test create from `CreateRiskInstance` invalidates list.

---

## 28. Testing checklist

- Cache hit/miss; force refresh; access denied; empty list; export; create flow error.

---

## 29. Guidelines

- **Local:** view + search.  
- **Pinia:** `riskInstances` + status.  
- Align export endpoint naming with backend meaning (register vs instances).
