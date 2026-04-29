# View Risk — Pinia & state audit

**Component:** [`src/components/Risk/ViewRisk.vue`](../../src/components/Risk/ViewRisk.vue)  
**Route:** `/view-risk/:id`  
**Parent:** `App.vue` → `router-view` (`props: true` if configured — verify router; route uses `:id`).

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | **Read + edit** a single risk by id: `GET` risk, `PUT` updates, optional data-subject request flows, notifications. |
| 1.2 | Route | `/view-risk/:id` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | — |
| 1.5 | Reusable | — |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk** maintenance / privacy request |
| 1.8 | Domain | **Risk** + **data subject** APIs |

---

## 2. Files analysed

- [`src/components/Risk/ViewRisk.vue`](../../src/components/Risk/ViewRisk.vue)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | `axios` shim on `apiService` |

---

## 4. Current data flow

1. `GET` `API_ENDPOINTS.RISK(riskId)` on load.  
2. Edit buffer in `data`; `PUT` `API_ENDPOINTS.RISK(id)`.  
3. `POST` `API_ENDPOINTS.CREATE_DATA_SUBJECT_REQUEST` (paths in file).  
4. `PUSH_NOTIFICATION`.

---

## 5. Variable inventory

| Variable | Purpose | Local? | Pinia? |
|----------|---------|--------|--------|
| `risk` / `edit` buffers | UI | **Yes** | No |
| Server risk snapshot | detail | Optional | `risk.riskDetailsById[id]` |

---

## 6–7. Local vs Pinia

- **Local:** edit mode toggles, unsaved changes.  
- **Pinia:** `fetchRiskById`, `updateRisk` actions; **invalidate** `risks` list on successful save.

---

## 8. API inventory

| Endpoint | Method |
|----------|--------|
| `API_ENDPOINTS.RISK(riskId)` | GET |
| `API_ENDPOINTS.RISK(RiskId)` | PUT |
| `API_ENDPOINTS.CREATE_DATA_SUBJECT_REQUEST` | POST |
| `API_ENDPOINTS.PUSH_NOTIFICATION` | POST |

---

## 9–13. Store

- `fetchRiskDetail(id, { force })`  
- `updateRisk(id, payload)`  
- TTL short (60s) or always refetch on route param change.

---

## 14. Repeated calls

Same risk may be opened from register — cache by id avoids duplicate GET when navigating back/forth if TTL warm.

---

## 15–29. Summary

- **Forms:** edit buffer local.  
- **Optimistic:** **No** for PUT risk.  
- **Testing:** concurrent edit, 404 risk, data subject flow errors.

---

## 29. Guidelines

- Route param drives `fetchRiskDetail`; clear detail cache on logout (`risk.resetDetails`).
