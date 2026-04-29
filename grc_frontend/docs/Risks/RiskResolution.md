# Risk Resolution — Pinia & state audit

**Component:** [`src/components/Risk/RiskResolution.vue`](../../src/components/Risk/RiskResolution.vue)  
**Route:** `/risk/resolution`  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | **Risk handling / resolution:** load instances, assign owners/reviewers, resolve/mitigate actions, notifications; uses reviewer selection API with RBAC note in code. |
| 1.2 | Route | `/risk/resolution` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | Internal panels / lists |
| 1.5 | Reusable | Popup / toggle patterns |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | Assignment → reviewer → mitigation handoff (overlaps conceptually with `RiskWorkflow` but simpler surface) |
| 1.8 | Domain | **Risk** instances; **users**; **notifications** |

---

## 2. Files analysed

- [`src/components/Risk/RiskResolution.vue`](../../src/components/Risk/RiskResolution.vue)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.4 | `computed` | Yes |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | `apiService` via local `axios` shim |
| 2.13 | Loading/error | Notification + try/catch patterns |
| 2.14 | RBAC | `USERS_FOR_REVIEWER_SELECTION` — reviewer list server-filtered |

---

## 4. Current data flow

1. `GET` `RISK_INSTANCES` for list.  
2. Per-row `GET` `RISK_INSTANCE(id)` when drilling into detail.  
3. `GET` `USERS_FOR_REVIEWER_SELECTION` with params for picker.  
4. `POST` `RISK_ASSIGN` and `POST` `ASSIGN_REVIEWER` for assignment flows.  
5. `PUSH_NOTIFICATION` on milestones.

---

## 5. Variable inventory (key)

| Variable | Purpose | Local? | Pinia? |
|----------|---------|--------|--------|
| Instance list | Table | No | `risk.riskInstances` (shared) |
| Selected instance / panels | UI | Yes | No |
| Reviewer search | UI | Yes | No |

---

## 6–7. Local vs Pinia

- **Local:** selection, modals, inline forms.  
- **Pinia:** shared **`riskInstances`** + `fetchInstanceDetail` if same detail used on `RiskWorkflow`.

---

## 8. API inventory

| Endpoint | Method | Move to Pinia? |
|----------|--------|----------------|
| `RISK_INSTANCES` | GET | Yes — reuse `fetchRiskInstances` |
| `RISK_INSTANCE(id)` | GET | `risk.fetchRiskInstanceDetail` |
| `USERS_FOR_REVIEWER_SELECTION` | GET | Optional `usersStore` / keep in action |
| `RISK_ASSIGN` | POST | `risk.assignRisk` |
| `ASSIGN_REVIEWER` | POST | `risk.assignReviewer` |
| `PUSH_NOTIFICATION` | POST | helper |

---

## 9–12. Store

Extend `risk` with assignment actions that **invalidate** instance list and optionally selected detail.

---

## 13. Cache-first

Instance list: same TTL as list page. Detail: short TTL or fetch-on-open always if highly volatile.

---

## 14. Repeated calls

`RISK_INSTANCES` overlaps `RiskInstances`, `riskService`, workflow — unify.

---

## 15. Prop drilling

None material; avoid passing large instance objects to deep children—prefer instance id + store getter.

## 16. Forms analysis

Assignment / reviewer forms: **keep field state local**; submit via Pinia actions `assignRisk` / `assignReviewer` that return updated instance or trigger `invalidateInstances`.

## 17. Tables / filters / pagination

Primary table of instances: data from **`risk.riskInstances`** after migration; filter/sort can stay client-side unless API supports server filters.

## 18. Dashboard / charts

**N/A** on this page.

## 19. RBAC / permissions

Prefer `permissionStore.can('assign_risk_reviewer')` wrapping buttons; keep server checks on `USERS_FOR_REVIEWER_SELECTION` and assignment POSTs.

## 20. Async UI improvements

Per-row spinners on assign; global toast on failure; disable double-submit on POST.

## 21. Optimistic UI

**No** optimistic assignment (audit trail).

## 22. Smart vs presentational

Optional extraction of `AssignmentPanel` presentational (props: instance summary; emits: `assign`).

## 23. State normalization

Optional `instancesById` when the same instance is opened in side panel and list row highlights depend on shared fields.

## 24. What / where / why

| # | What | Where | Why | Pri |
|---|------|-------|-----|-----|
| 1 | `fetchRiskInstances` | `RiskResolution.vue` | Remove duplicate list fetch | High |
| 2 | `assignRisk` / `assignReviewer` | `stores/risk.js` | Shared error + invalidation | Medium |

## 25. File-by-file migration

| File | Change |
|------|--------|
| `RiskResolution.vue` | `storeToRefs` for instances; call actions |
| `stores/risk.js` | assignment actions + invalidation |

## 26. Priority matrix

- **P0:** Shared instances list.  
- **P1:** Assignment actions.  
- **P2:** Permission composable.

## 27. Step-by-step implementation

1. Expose instances on store.  
2. Point resolution page at store.  
3. Add mutation actions.  
4. Regression test with `RiskWorkflow` same user ids.

## 28. Testing checklist

- Assign + verify list/detail; permission denied; concurrent updates; notifications not duplicated.

## 29. Final developer guidelines

- **Local:** form drafts, selected row highlight.  
- **Pinia:** instance list + mutations.  
- **Do not** store reviewer comment drafts globally unless multi-step across routes is required.
