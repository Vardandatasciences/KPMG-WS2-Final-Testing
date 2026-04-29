# Risk Scoring — Pinia & state audit

**Component:** [`src/components/Risk/RiskScoring.vue`](../../src/components/Risk/RiskScoring.vue)  
**Route:** `/risk/scoring`  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | Lists risk instances with names for scoring workflow; integrates `riskDataService` cache; navigates to scoring details; notifications. |
| 1.2 | Route | `/risk/scoring` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | Links to `ScoringDetails` route |
| 1.5 | Reusable | — |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk** scoring intake |
| 1.8 | Domain | **Risk** |

---

## 2. Files analysed

- [`src/components/Risk/RiskScoring.vue`](../../src/components/Risk/RiskScoring.vue)
- [`src/services/riskService.js`](../../src/services/riskService.js)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.4 | `computed` | Yes |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | `GET` `RISK_SCORING_INSTANCES_WITH_NAMES` + cache via `riskDataService` |
| 2.13 | Loading/error | Notifications on events |

---

## 4. Current data flow

1. Try API fetch; on success `riskDataService.setData('riskInstances', ...)`.  
2. Else if cache `hasRiskInstancesCache` use cached instances.  
3. User opens detail route `/risk/scoring-details/:riskId`.

---

## 5. Variable inventory

| Variable | Purpose | Pinia? |
|----------|---------|--------|
| Instance list for scoring | Data | **Yes** — same `riskInstances` with optional `view='scoring'` filter getter |
| Search / UI | Local | No |

---

## 6–7. Local vs Pinia

- **Local:** search, sort, UI.  
- **Pinia:** instances + `fetchScoringInstances` wrapper (could alias `fetchRiskInstances` if same payload).

---

## 8. API inventory

| Endpoint | Method | Note |
|----------|--------|------|
| `API_ENDPOINTS.RISK_SCORING_INSTANCES_WITH_NAMES` | GET | Specialized list — store field `scoringInstances` **or** reuse `riskInstances` if identical shape |
| `PUSH_NOTIFICATION` | POST | helper |

---

## 9–12. Store

- If response shape **equals** `RISK_INSTANCES`, map to single `riskInstances`.  
- If **different**, add `scoringInstanceRows` + TTL to avoid colliding types.

---

## 13. Cache-first

TTL 1–5 min; invalidate on score updates from `ScoringDetails`.

---

## 14. Repeated calls

Same instances domain as list/workflow — avoid three arrays (`riskDataService`, component, Pinia).

---

## 15. Prop drilling

Low; list is internal to page.

## 16. Forms analysis

**N/A** — no primary create/edit form on this route (navigation to `ScoringDetails` for edits).

## 17. Tables / filters / pagination

Search/sort are **client-side** on the loaded list; if server pagination is added later, move query params into `fetchScoringInstances` action arguments.

## 18. Dashboard / charts

**N/A** as primary KPI dashboard (see `RiskKPI.md` / `RiskDashboard.md`).

## 19. RBAC / permissions

API-enforced; optional `permissionStore.can('view_risk_scoring')` on page entry.

## 20. Async UI improvements

Loading row for initial fetch; empty state when list empty; error toast when API fails.

## 21. Optimistic UI

**No** for scoring navigation or list mutations.

## 22. Smart vs presentational

Target: thin container + `ScoringInstancesTable.vue` (props + `@open-details`).

## 23. State normalization

Optional `instancesById` only if workflow joins many ids from this list.

## 24. What / where / why

| # | What | Where | Why | Pri |
|---|------|-------|-----|-----|
| 1 | Single fetch action | `stores/risk.js` + `RiskScoring.vue` | Remove `riskDataService` fork | High |

## 25. File-by-file migration

| File | Change |
|------|--------|
| `RiskScoring.vue` | `useRiskStore` + `fetchScoringInstances` or shared `fetchRiskInstances` |
| `stores/risk.js` | action + optional `scoringInstanceRows` |

## 26. Priority matrix

- **P0:** Align list with Pinia + invalidation from `ScoringDetails` PUT.  
- **P1:** Dedupe shape decision (`riskInstances` vs dedicated scoring rows).

## 27. Step-by-step implementation

1. Add store action.  
2. Replace component fetch/cache branch.  
3. Wire `ScoringDetails` success to `invalidateInstances`.  
4. Test both cache paths removed.

## 28. Testing checklist

- Cache vs API path; navigation to details; stale data after score save (invalidate).

## 29. Final developer guidelines

- **Local:** search, sort keys.  
- **Pinia:** scoring/instance list source of truth.  
- **Do not** duplicate `riskDataService` writes from this page after migration.
