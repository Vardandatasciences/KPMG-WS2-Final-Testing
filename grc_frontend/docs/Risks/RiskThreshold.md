# Risk Threshold — Pinia & state audit

**Component:** [`src/components/Risk/RiskThreshold.vue`](../../src/components/Risk/RiskThreshold.vue)  
**Route:** `/risk/threshold`  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | Surfaces **system-identified risks that exceed threshold** via API; presentation + alerts (read-heavy). |
| 1.2 | Route | `/risk/threshold` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | — |
| 1.5 | Reusable | — |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | Monitoring / escalation awareness tied to **system risks** |
| 1.8 | Domain | **Risk** (system-identified subset) |

---

## 2. Files analysed

- [`src/components/Risk/RiskThreshold.vue`](../../src/components/Risk/RiskThreshold.vue)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.4 | `computed` | Yes |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | `apiService.get('/api/system-risks/threshold-exceeded/')` |

---

## 4. Current data flow

1. On mount / refresh method → GET threshold-exceeded list.  
2. Component maps response to local `data` for display.

---

## 5. Variable inventory

| Variable | Purpose | Local? | Pinia? |
|----------|---------|--------|--------|
| API result rows | list | No | **`risk.thresholdExceededRisks`** or reuse `systemRisks` filtered view |
| UI toggles | filters | Yes | No |

---

## 6–7. Local vs Pinia

- **Local:** expand/collapse, sorting UI.  
- **Pinia:** share dataset with **System Identified Risks** if same source — avoid second fetch.

---

## 8. API inventory

| Endpoint | Method | Move to Pinia? |
|----------|--------|----------------|
| `/api/system-risks/threshold-exceeded/` | GET | Yes — `risk.fetchThresholdExceeded({ force })` |

**Note:** Consider using `API_ENDPOINTS` constant instead of string path for consistency.

---

## 9–13. Store

- Add to `risk` store alongside system risks slice; TTL **30–60 s** (operational alert data).  
- Invalidate when system risk status changes (accept/reject) — event from system risks page or websocket (if any).

---

## 14. Repeated API calls

If user toggles between `/risk/threshold` and `/risk/system-identified-risks`, may refetch overlapping domain — coordinate via store.

---

## 15–29. Summary

- Small page — **high value / low effort** to align with `systemRisks` Pinia slice.  
- **Testing:** empty result, API error, large list performance.

---

## 29. Guidelines

- Prefer **one** system-risk data subsystem in Pinia over many one-off fetches.
