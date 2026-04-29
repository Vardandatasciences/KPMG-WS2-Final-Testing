# System Identified Risks — Pinia & state audit

**Component:** [`src/components/Risk/SystemIdentifiedRisks.vue`](../../src/components/Risk/SystemIdentifiedRisks.vue)  
**Related:** [`src/components/Risk/SystemRiskWorkflowModal.vue`](../../src/components/Risk/SystemRiskWorkflowModal.vue)  
**Route:** `/risk/system-identified-risks`  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | End-to-end **AI/system-identified risk** lifecycle: schedules (CRUD), stats, paginated list, detail/review modals, manual scan (long timeout), external sources, company folder/subfolder browse, document picker, test analysis job polling/cancel, accept/reject/review/send-for-approval, workflow approve/reject on converted instance, user/department pickers. |
| 1.2 | Route | `/risk/system-identified-risks` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | `SystemRiskWorkflowModal` (props + emits `workflow-created`, `close`) |
| 1.5 | Reusable | Modal pattern, tables |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | Intake → review → accept/reject → optional approval → instance workflow |
| 1.8 | Domain | **Risk** (system), **documents**, **users**, **departments**, **notifications** |

**Cross-module:** [`Sidebar.vue`](../../src/components/Policy/Sidebar.vue) also calls `API_ENDPOINTS.SYSTEM_RISKS_STATS` for `pendingRiskCount` — should consume Pinia after this slice exists.

---

## 2. Files analysed

- [`src/components/Risk/SystemIdentifiedRisks.vue`](../../src/components/Risk/SystemIdentifiedRisks.vue)
- [`src/components/Risk/SystemRiskWorkflowModal.vue`](../../src/components/Risk/SystemRiskWorkflowModal.vue)
- [`src/config/api.js`](../../src/config/api.js) (`SYSTEM_RISKS_*`, `COMPANY_*`, `DOCUMENTS_LIST`)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.4 | `computed` | Yes (filters, derived lists) |
| 2.5 | `watch` | Likely on route/filters/job |
| 2.6–2.7 | props/emits | Modal uses **props** + **emits** |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | **`apiService` only** (consistent) |
| 2.13 | Loading/error | Long-running scan (`timeout: 600000`); background fetch for stats |
| 2.14 | RBAC | Server-side on APIs; UI assumes success/failure |

---

## 4. Current data flow

1. **Stats:** `GET` `SYSTEM_RISKS_STATS` (background option).  
2. **List:** `GET` `SYSTEM_RISKS_LIST?${params}` (pagination/filter query string from component state).  
3. **Schedules:** `GET`/`POST`/`DELETE` schedule endpoints.  
4. **Detail:** `GET` `SYSTEM_RISKS_DETAIL(id)` (multiple flows).  
5. **Scan:** `POST` `SYSTEM_RISKS_RUN_SCAN_MANUAL` with large timeout.  
6. **Test job:** poll `SYSTEM_RISKS_RUN_TEST_ANALYSIS_STATUS`, cancel via `...CANCEL`.  
7. **Folders/docs:** `COMPANY_FOLDERS`, `COMPANY_SUBFOLDERS`, `DOCUMENTS_LIST`.  
8. **Decisions:** `ACCEPT`, `PUT REVIEW`, `POST REJECT`, `POST SEND_FOR_APPROVAL`, workflow `APPROVE`/`REJECT` on `riskInstanceId`.  
9. **Users/depts:** `USERS_FOR_DROPDOWN`, `CURRENT_USER`, `DEPARTMENTS`.

**Modal (`SystemRiskWorkflowModal.vue`):**

- `GET` users (`USERS_FOR_REVIEWER_SELECTION` || `USERS_FOR_DROPDOWN` || `USERS`).  
- `POST` `SYSTEM_RISKS_SEND_FOR_APPROVAL(riskData.id)`.

---

## 5. Variable inventory (representative)

| Variable / area | Purpose | Local? | Pinia? |
|-----------------|---------|--------|--------|
| `scheduleForm`, schedule list | Schedules UI | Partial | `systemRisks.schedules` |
| List filters, page, pageSize | Table | Yes* | *Pinia if URL sync across modules |
| `selectedRisk`, modals | UI | Yes | Store **`selectedSystemRiskId`** if Sidebar needs |
| `testAnalysis.jobId` | Poll | Yes | Could be `systemRisks.testJob` |
| Stats object | KPI strip | No | **`systemRisksStats`** |

\*Default: keep local; move only if product demands.

---

## 6. Local state to keep

- Modal open/close (unless global), wizard steps for folder navigation, table row expansion, inline search for documents, per-field validation for review forms.

---

## 7. State to move to Pinia

- **`systemRisksStats`** + TTL **30–60 s** (feeds Sidebar badge).  
- **`systemRisksList` + pagination meta** + `listStatus`.  
- **`schedules`**.  
- **`selectedSystemRiskDetail`** keyed by id (optional).  
- **Actions** for every mutation (accept/reject/…) with **invalidation** rules.

---

## 8. API call inventory (complete from grep)

| Purpose | Endpoint | Method | Component |
|---------|----------|--------|-----------|
| List schedules | `SYSTEM_RISKS_SCHEDULES` | GET | main |
| Create schedule | `SYSTEM_RISKS_SCHEDULE_CREATE` | POST | main |
| Delete schedule | `SYSTEM_RISKS_SCHEDULE_DETAIL(id)` | DELETE | main |
| Stats | `SYSTEM_RISKS_STATS` | GET | main (+ Sidebar duplicate) |
| List risks | `SYSTEM_RISKS_LIST` + query | GET | main |
| Detail | `SYSTEM_RISKS_DETAIL(id)` | GET | main |
| Manual scan | `SYSTEM_RISKS_RUN_SCAN_MANUAL` | POST | main |
| External sources | `SYSTEM_RISKS_EXTERNAL_SOURCES` | GET | main |
| Company folders | `COMPANY_FOLDERS` | GET | main |
| Subfolders | `COMPANY_SUBFOLDERS(folderId)` | GET | main |
| Documents | `DOCUMENTS_LIST` + query | GET | main |
| Test job status | `SYSTEM_RISKS_RUN_TEST_ANALYSIS_STATUS(jobId)` | GET | main |
| Cancel test | `SYSTEM_RISKS_RUN_TEST_ANALYSIS_CANCEL(jobId)` | POST | main |
| Accept | `SYSTEM_RISKS_ACCEPT(id)` | POST | main |
| Review | `SYSTEM_RISKS_REVIEW(id)` | PUT | main |
| Reject (selected) | `SYSTEM_RISKS_REJECT(id)` | POST | main |
| Reject (by id) | `SYSTEM_RISKS_REJECT(id)` | POST | main |
| Send approval | `SYSTEM_RISKS_SEND_FOR_APPROVAL(id)` | POST | main + modal |
| Workflow approve | `SYSTEM_RISKS_WORKFLOW_APPROVE(riskInstanceId)` | POST | main |
| Workflow reject | `SYSTEM_RISKS_WORKFLOW_REJECT(riskInstanceId)` | POST | main |
| Users dropdown | `USERS_FOR_DROPDOWN` | GET | main |
| Current user | `CURRENT_USER` | GET | main |
| Departments | `DEPARTMENTS` | GET | main |

---

## 9–12. Recommended Pinia slice (`risk` store)

**State:**

```js
systemRisks: {
  stats: null,
  statsLastFetched: null,
  list: [],
  listPagination: { page: 1, pageSize: 20, total: 0 },
  listFilters: {},
  schedules: [],
  selectedId: null,
  detailById: {},
  testAnalysis: { jobId: null, status: null },
  status: 'idle',
  error: null
}
```

**Actions (examples):** `fetchSystemRisksStats`, `fetchSystemRisksList`, `fetchSystemRiskDetail`, `createSchedule`, `deleteSchedule`, `runManualScan`, `pollTestAnalysis`, `cancelTestAnalysis`, `acceptSystemRisk`, `reviewSystemRisk`, `rejectSystemRisk`, `sendForApproval`, `workflowApprove`, `workflowReject`.

**Getters:** `pendingSystemRiskCount` (from `stats`), `isStatsStale`.

---

## 13. Cache-first

| Data | TTL | Invalidate |
|------|-----|--------------|
| Stats | 30–60 s | After any accept/reject/approval |
| List | 1–5 min | After mutations |
| Detail | 60 s | After review on that id |

---

## 14. Repeated API calls

- **`SYSTEM_RISKS_STATS`** with Sidebar — **must** dedupe via store.  
- **Detail** `GET` appears twice in grep paths — consolidate `fetchSystemRiskDetail`.

---

## 15. Prop drilling

`SystemRiskWorkflowModal` receives **`riskData`** etc. — acceptable; could pass only `id` once detail is always in store.

---

## 16. Forms

Multiple forms (schedule, review, reject reason, approval payload): **keep field values local**; on submit call **Pinia actions**.

---

## 17. Tables / filters / pagination

Server-driven list — **query params** should be built in action `fetchSystemRisksList({ filters, page })` to keep component thin.

---

## 18. Dashboard / charts

Stats strip acts like mini-dashboard — store-backed.

---

## 19. RBAC

Fine-grained button disable using future `permissionStore` (`system_risk_review`, etc.) — align with backend permission names.

---

## 20. Async UI

- Progress for long scan; disable double submit on accept/reject.  
- Polling backoff for test job.  
- Clear **empty** / **error** / **timeout** states.

---

## 21. Optimistic UI

**Not recommended** for accept/reject/approval (audit).

---

## 22. Smart vs presentational

- **Target:** `SystemIdentifiedRisks` becomes orchestrator; extract `SystemRisksTable.vue`, `SystemRiskReviewModal.vue` as dumb components.

---

## 23. Normalization

`detailById: { [id]: {...} }` helps when list row + modal share same entity.

---

## 24. What / where / why (priority)

| What | Where | Why | Pri |
|------|-------|-----|-----|
| `systemRisks` slice | `stores/risk.js` | Largest API surface; dedupe stats | High |
| Sidebar reads getter | `Sidebar.vue` (follow-up) | One stats call | High |

---

## 25. File-by-file migration

| File | Change |
|------|--------|
| `SystemIdentifiedRisks.vue` | Replace methods with store actions; `storeToRefs` |
| `SystemRiskWorkflowModal.vue` | Call `sendForApproval` action or emit to parent that calls action |
| `stores/risk.js` | add slice + actions |
| `Sidebar.vue` | `pendingRiskCount` from `useRiskStore` getter (outside this folder) |

---

## 26–27. Priority & steps

**P0:** stats + list + detail fetch.  
**P1:** mutations with invalidation.  
**P2:** Sidebar integration.

---

## 28. Testing checklist

- Pagination + filters; schedule CRUD; scan timeout; test job poll/cancel; all decision endpoints; stats badge sync; permission denied.

---

## 29. Guidelines

- **Never** cache half-applied review state in Pinia — only server-confirmed detail.  
- **Centralize** `SYSTEM_RISKS_STATS` — highest ROI for the whole app shell.
