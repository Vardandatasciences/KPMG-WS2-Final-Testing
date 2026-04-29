# Create Risk — Pinia & state audit

**Component:** [`src/components/Risk/CreateRisk.vue`](../../src/components/Risk/CreateRisk.vue)  
**Routes:** `/risk/create`, `/risk/create-risk`  
**Parent:** `App.vue` → `router-view` (**excluded from `keep-alive`**).

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | Multi-section form to define a new risk (or pre-fill from incident / source instance), including compliance linkage, business impact, categories, departments, optional AI/incident flows. |
| 1.2 | Routes | `/risk/create`, `/risk/create-risk` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | `TailoringRisk` imported for related UX (path `/risk/tailoring` is separate route) |
| 1.5 | Reusable | Shared form/popup patterns |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk** creation; optional **incident** read/analyze; **compliance** dropdown; **notification** on success |
| 1.8 | Domain | **Risk**, **Compliance**, **Incident**, **Notification** |

---

## 2. Files analysed

- [`src/components/Risk/CreateRisk.vue`](../../src/components/Risk/CreateRisk.vue)
- [`src/config/api.js`](../../src/config/api.js) (endpoint constants)
- [`src/services/riskService.js`](../../src/services/riskService.js) (comments/cache sync on submit)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.2–2.3 | `ref`/`reactive` | No in script (large `data()` model) |
| 2.4 | `computed` | Yes |
| 2.5 | `watch` | As needed for dependencies |
| 2.6–2.8 | props/emits/inject | No / minimal |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | **Direct `apiService`** for master data + submit |
| 2.12 | Prop drilling | Low |
| 2.13 | Loading/error | Submit loading flags; access errors via interceptor / comments |
| 2.14 | RBAC | Implicit via API |

---

## 4. Current data flow

1. **Mount:** Loads dropdowns — `BUSINESS_IMPACTS`, `RISK_CATEGORIES`, `DEPARTMENTS`, compliance search `COMPLIANCES_FOR_DROPDOWN(query)`.  
2. **Optional context:** `RISK_INSTANCE(sourceRiskId)`, `INCIDENT`, `ANALYZE_INCIDENT` when query params present.  
3. **Submit:** `POST` `API_ENDPOINTS.RISKS` with sanitized payload.  
4. **After success:** `PUSH_NOTIFICATION`; code paths mention syncing **RiskRegisterList** cache (`riskDataService`).  
5. **Child:** `TailoringRisk` is separate route component — not prop-driven state.

---

## 5. Variable inventory (representative)

| Variable | Declared | Purpose | Local? | Pinia? | Priority |
|----------|----------|---------|--------|--------|----------|
| Entire risk form model (`risk`, nested fields) | `data` | Create payload | **Yes** | No* | — |
| `complianceSearchQuery`, debounced search | `data` | Dropdown | Yes | No | — |
| `sourceRiskId`, `incidentId` | `data`/`$route` | Context | Yes | No | — |
| Master lists (`businessImpacts`, `categories`, …) | `data` | Dropdowns | Optional | Yes** | Medium |

\*Unless multi-step wizard across routes — not current.  
\**If reused by TailoringRisk/CreateRiskInstance — `risk.fetchMasterData()` in store.

---

## 6. Local state to keep

- All **field-level** form values, validation messages, step toggles, modals for add category/business impact.  
**Reason:** Standard Vue form pattern; no global sharing.

---

## 7. State to move to Pinia

- **Post-success invalidation:** `risk.invalidateRisks()` (not the form).  
- **Shared master data** (if deduping): departments, categories, business impacts — or keep fetching per page if payloads differ.

---

## 8. API call inventory

| Purpose | Endpoint | Method | Move to Pinia? |
|---------|----------|--------|----------------|
| Compliance dropdown | `API_ENDPOINTS.COMPLIANCES_FOR_DROPDOWN` | GET | Optional shared action |
| Source instance | `API_ENDPOINTS.RISK_INSTANCE(id)` | GET | Optional `risk.fetchInstance` |
| Incident | `API_ENDPOINTS.INCIDENT` | GET | No (incident domain) |
| Analyze incident | `API_ENDPOINTS.ANALYZE_INCIDENT` | POST | No |
| Business impacts | `API_ENDPOINTS.BUSINESS_IMPACTS` | GET | Optional master |
| Add business impact | `API_ENDPOINTS.ADD_BUSINESS_IMPACT` | POST | Keep in component or `risk` action |
| Risk categories | `API_ENDPOINTS.RISK_CATEGORIES` | GET | Optional master |
| Departments | `API_ENDPOINTS.DEPARTMENTS` | GET | Optional org slice |
| Add category | `API_ENDPOINTS.ADD_RISK_CATEGORY` | POST | Component OK |
| Create risk | `API_ENDPOINTS.RISKS` | POST | **`risk.createRisk(payload)`** recommended |
| Notification | `API_ENDPOINTS.PUSH_NOTIFICATION` | POST | Shared helper |

---

## 9–12. Store / getters / actions

- **Action:** `createRisk(payload)` → POST → on success `invalidateRisks()` + optional toast.  
- **Getter:** none required for this page.  
- **Do not** store unsaved draft in Pinia unless product requires draft across navigation.

---

## 13. Cache-first

- Master dropdowns: TTL 15–30 min if moved to store.  
- No cache for **submit** — always server authoritative.

---

## 14. Repeated API calls

- `BUSINESS_IMPACTS`, `RISK_CATEGORIES`, `DEPARTMENTS` duplicated with `TailoringRisk`, `CreateRiskInstance`, `ScoringDetails` → centralize if churn is high.

---

## 15. Prop drilling

Low.

---

## 16. Forms

| Form | Fields | Validation | Submit | Local? |
|------|--------|------------|--------|--------|
| Create risk | Large model (title, compliance, criticality, mitigation, …) | Inline / custom | `apiService.post(RISKS)` | **Yes** |

**Pinia for form:** No, unless draft persistence is a product requirement.

---

## 17. Tables / filters

Secondary lists (e.g. compliance results) — keep local.

---

## 18. Dashboard / charts

N/A.

---

## 19. RBAC

Use future `permissionStore.can('create_risk')` for submit button; keep server enforcement.

---

## 20. Async UI

- Disable double submit on `POST RISKS`.  
- Clear success redirect + toast.  
- Inline errors for validation.

---

## 21. Optimistic UI

**No** for create risk (regulatory record).

---

## 22. Smart vs presentational

Large **smart** component; optional split: `CreateRiskFormFields.vue` presentational + container with Pinia actions.

---

## 23. Normalization

N/A for create form.

---

## 24. What / where / why

| What | Where | Why | Pri |
|------|-------|-----|-----|
| `createRisk` Pinia action | `stores/risk.js` + call from component | Central invalidation + consistent error handling | High |
| Keep form `data` local | `CreateRisk.vue` | Avoid global mutable form | High |

---

## 25. File-by-file migration

| File | Change |
|------|--------|
| `CreateRisk.vue` | Call `risk.createRisk`; remove direct `riskDataService` cache mutation in favor of `invalidateRisks` |
| `stores/risk.js` | Add `createRisk` |

---

## 26–27. Priority & steps

**High:** create action + invalidate register.  
**Medium:** shared master-data actions.  
**Steps:** store action → component swap → test create → verify register list.

---

## 28. Testing checklist

- Happy path create.  
- Validation errors.  
- Compliance search debounce.  
- Incident/source instance prefill when query present.  
- Register list refresh / no stale cache.

---

## 29. Guidelines

- **Local:** entire form.  
- **Pinia:** mutations affecting lists (`invalidateRisks`).  
- **First:** wire `createRisk` + invalidation before deduplicating master fetches.
