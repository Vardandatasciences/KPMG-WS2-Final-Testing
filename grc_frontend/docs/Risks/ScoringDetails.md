# Scoring Details — Pinia & state audit

**Component:** [`src/components/Risk/ScoringDetails.vue`](../../src/components/Risk/ScoringDetails.vue)  
**Route:** `/risk/scoring-details/:riskId` (`props: true`)  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | Detail/edit scoring for a **risk instance** identified by `riskId` route param; loads instance, register risks dropdown, business impacts/categories; saves via `PUT` instance; notifications. |
| 1.2 | Route | `/risk/scoring-details/:riskId` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | — |
| 1.5 | Reusable | — |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk** scoring update |
| 1.8 | Domain | **Risk** |

---

## 2. Files analysed

- [`src/components/Risk/ScoringDetails.vue`](../../src/components/Risk/ScoringDetails.vue)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.6 | `props` | **`riskId`** from router |
| 2.4 / 2.5 | `computed` / `watch` | Yes |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | `axios` shim over `apiService` |

---

## 4. Current data flow

1. `GET` `RISK_INSTANCE(safeRiskId)` on load / watch param.  
2. `GET` `RISKS_FOR_DROPDOWN` for linkage UI.  
3. `GET/POST` business impact & category endpoints (same as create flows).  
4. `PUT` `RISK_INSTANCE` with `submissionData`.  
5. `PUSH_NOTIFICATION`.

---

## 5. Variable inventory

| Variable | Purpose | Local? | Pinia? |
|----------|---------|--------|--------|
| `riskId` | Route prop | N/A | — |
| Editable instance model | `data` | **Yes** | No |
| Loaded instance snapshot | `data` | Optional | `risk.instanceDetailsById[riskId]` |

---

## 6–7. Local vs Pinia

- **Local:** unsaved edits, UI toggles.  
- **Pinia:** optional cached **read-only** detail; **invalidate** `riskInstances` + scoring list on successful `PUT`.

---

## 8. API inventory

| Endpoint | Method |
|----------|--------|
| `RISK_INSTANCE(id)` | GET |
| `RISKS_FOR_DROPDOWN` | GET |
| `BUSINESS_IMPACTS` / `ADD_BUSINESS_IMPACT` | GET / POST |
| `RISK_CATEGORIES` / `ADD_RISK_CATEGORY` | GET / POST |
| `RISK_INSTANCE(id)` | PUT |
| `PUSH_NOTIFICATION` | POST |

---

## 9–12. Store

**Actions:** `fetchRiskInstanceForScoring(id)`, `updateRiskInstanceScoring(id, payload)` → on success `invalidateInstances()` (+ scoring slice if separate).

---

## 13. Cache-first

Detail: fetch on route param change; cache optional 30–60s; **always refetch** after save.

---

## 14. Repeated calls

Master data same as CreateRisk/CreateRiskInstance — dedupe.

---

## 15–29. Short summary

- **Prop drilling:** `riskId` only — good.  
- **Forms:** large — keep local.  
- **Optimistic:** **No** for scoring PUT.  
- **Testing:** param change, invalid id, save, back to list reflects new values.
