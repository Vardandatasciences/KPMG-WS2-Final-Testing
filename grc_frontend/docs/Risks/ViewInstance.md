# View Risk Instance — Pinia & state audit

**Component:** [`src/components/Risk/ViewInstance.vue`](../../src/components/Risk/ViewInstance.vue)  
**Route:** `/view-instance/:id`  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | **Read + edit** a single risk instance; `GET`/`PUT` `RISK_INSTANCE`; data subject request; notifications; rich UX text (permissions, ownership) in template copy. |
| 1.2 | Route | `/view-instance/:id` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | — |
| 1.5 | Reusable | — |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk instance** lifecycle view |
| 1.8 | Domain | **Risk** instance + privacy request |

---

## 2. Files analysed

- [`src/components/Risk/ViewInstance.vue`](../../src/components/Risk/ViewInstance.vue)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | `axios` shim |

---

## 4. Current data flow

1. `GET` `RISK_INSTANCE(instanceId)` (multiple code paths / watch).  
2. `PUT` instance with `editInstance`.  
3. `CREATE_DATA_SUBJECT_REQUEST`, `PUSH_NOTIFICATION`.

---

## 5. Variable inventory

| Variable | Purpose | Local? | Pinia? |
|----------|---------|--------|--------|
| `instance`, `editInstance` | Detail/edit | Yes / partial | `risk.instanceDetailsById` optional |

---

## 6–7. Local vs Pinia

- Same pattern as **ViewRisk**: local edit buffer; Pinia for fetch/cache/invalidate instances list.

---

## 8. API inventory

| Endpoint | Method |
|----------|--------|
| `API_ENDPOINTS.RISK_INSTANCE(id)` | GET |
| `API_ENDPOINTS.RISK_INSTANCE(RiskInstanceId)` | PUT |
| `API_ENDPOINTS.CREATE_DATA_SUBJECT_REQUEST` | POST |
| `API_ENDPOINTS.PUSH_NOTIFICATION` | POST |

---

## 9–13. Store

`fetchRiskInstanceDetail(id)`, `updateRiskInstance(id, payload)`, invalidate on success.

---

## 14–29. Summary

- **Repeated:** instance GET also used heavily in `RiskWorkflow` — unify `instanceDetailsById` cache.  
- **Optimistic:** no.  
- **Testing:** id change, save conflicts, data subject errors.

---

## 29. Guidelines

- Align instance detail cache with **RiskWorkflow** migration to prevent divergent copies of same instance.
