# Create Risk Instance — Pinia & state audit

**Component:** [`src/components/Risk/CreateRiskInstance.vue`](../../src/components/Risk/CreateRiskInstance.vue)  
**Route:** `/risk/create-instance`  
**Parent:** `App.vue` (excluded from `keep-alive`).

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | Form to create a risk **instance** linked to register risks, compliances, users, business impacts, categories; file/evidence hooks; notifications. |
| 1.2 | Route | `/risk/create-instance` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | `props`-based subcomponents if any (check file for dynamic imports) |
| 1.5 | Reusable | Popup / form patterns |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk** instance creation; **notification** |
| 1.8 | Domain | **Risk**; touches **compliance**, **users**, **business impact** |

---

## 2. Files analysed

- [`src/components/Risk/CreateRiskInstance.vue`](../../src/components/Risk/CreateRiskInstance.vue)
- [`src/services/riskService.js`](../../src/services/riskService.js) (post-create cache prepend)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.4 | `computed` | Yes |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | `apiService` direct; updates **`riskDataService`** after create |
| 2.13 | Loading/error | Submit guards; extensive debug logging around auth |
| 2.14 | RBAC | API-driven |

---

## 4. Current data flow

1. **Load risks:** `GET` `API_ENDPOINTS.RISKS_FOR_DROPDOWN`.  
2. **Related fetches:** `RISK_INSTANCES`, `USERS_FOR_DROPDOWN`, `ALL_COMPLIANCES_FOR_DROPDOWN`, `BUSINESS_IMPACTS`, `RISK_CATEGORIES`, optional `test-connection`.  
3. **Submit:** `POST` `API_ENDPOINTS.CREATE_RISK_INSTANCE`.  
4. **Post-success:** mutates `riskDataService` cache (`setData` / `clearCache`); `PUSH_NOTIFICATION`.

---

## 5. Variable inventory (key)

| Area | Local? | Pinia? |
|------|--------|--------|
| Full form model | Yes | No |
| Dropdown source arrays | Optional share | `risk` / `compliance` master actions |
| Created instance handle | N/A | `invalidateInstances` |

---

## 6–7. Local vs Pinia

- **Local:** all form fields, step state, file selection UI.  
- **Pinia:** `createRiskInstance` action + **invalidate** `riskInstances`; optionally `fetchRisks` if counts change.

---

## 8. API inventory

| Endpoint | Method | Notes |
|----------|--------|-------|
| `RISKS_FOR_DROPDOWN` | GET | Dedupe with store |
| `RISK_INSTANCES` | GET | Prefill / validation |
| Dynamic `endpoint` (headers) | GET | Review in code for purpose |
| `CREATE_RISK_INSTANCE` | POST | **Pinia `createRiskInstance`** |
| `USERS_FOR_DROPDOWN` | GET | Could be org store later |
| `ALL_COMPLIANCES_FOR_DROPDOWN` | GET | Compliance store candidate (out of scope) |
| `BUSINESS_IMPACTS` / `ADD_BUSINESS_IMPACT` | GET/POST | Same as CreateRisk |
| `RISK_CATEGORIES` / `ADD_RISK_CATEGORY` | GET/POST | Same |
| `PUSH_NOTIFICATION` | POST | helper |
| `/api/test-connection/` | GET | Dev-only? consider removal in prod |

---

## 9–12. Store

**Actions:** `createRiskInstance(formData)`, `invalidateInstances()`, optional `fetchCreateInstanceMasters()`.

---

## 13. Cache-first

Masters: TTL; create: no cache of result beyond invalidation.

---

## 14. Repeated API calls

Same masters as `CreateRisk`, `TailoringRisk`, `ScoringDetails`.

---

## 15. Prop drilling

Low; `props` used for embedded sub-flows if any—prefer route params + store for shared ids.

## 16. Forms analysis

| Form | Path | Fields | Validation | Submit | Local fields? | Pinia? |
|------|------|--------|------------|--------|---------------|--------|
| Create instance | `CreateRiskInstance.vue` | Large model + attachments | Inline | `POST CREATE_RISK_INSTANCE` | **Yes** | Actions only |

## 17. Tables / filters / pagination

**N/A** as primary grid page; dropdown result lists are secondary UI.

## 18. Dashboard / charts

**N/A**.

## 19. RBAC / permissions

API + interceptor; optional `permissionStore.can('create_risk_instance')` on submit.

## 20. Async UI improvements

Double-submit guard on POST; clear progress for long uploads; inline field errors.

## 21. Optimistic UI

**No** optimistic instance append; use invalidate + refetch or insert server-returned instance inside store action only after success.

## 22. Smart vs presentational

Split large field groups into presentational sections receiving `modelValue` + emits.

## 23. State normalization

Not required unless instance payload embeds duplicate nested user/compliance objects at scale.

## 24. What / where / why

| # | What | Where | Why | Pri |
|---|------|-------|-----|-----|
| 1 | Remove `riskDataService.setData` | after create | Single invalidation path | High |

## 25. File-by-file migration

| File | Change |
|------|--------|
| `CreateRiskInstance.vue` | call `risk.createRiskInstance` |
| `stores/risk.js` | implement action + invalidate |

## 26. Priority matrix

- **P0:** create action + invalidate instances.  
- **P1:** dedupe master fetches.  
- **P2:** remove `/api/test-connection/` in production builds if unused.

## 27. Step-by-step implementation

1. Add `createRiskInstance` action.  
2. Swap component submit handler.  
3. Remove cache mutation; call `invalidateInstances`.  
4. Test navigate to `RiskInstances` list.

## 28. Testing checklist

- Multipart payload; validation errors; success → instances list correct; Pinia DevTools shows updated instances after navigate.

## 29. Final developer guidelines

- **Local:** entire form model.  
- **Pinia:** mutations affecting lists only.  
- **Do not** persist half-filled forms in Pinia unless product mandates draft across navigation.
