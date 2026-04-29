# Risk Workflow — Pinia & state audit

**Component:** [`src/components/Risk/RiskWorkflow.vue`](../../src/components/Risk/RiskWorkflow.vue)  
**Route:** `/risk/workflow`  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | **Primary operational hub** for risk **instances**: user selection, reviewer tasks, mitigation updates, latest reviews, assigned reviewers, evidence upload/delete, reviewer comments, version history, linked incidents/evidence/file operations, notifications. Very large single-file component. |
| 1.2 | Route | `/risk/workflow` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | Inline sections (potential split targets) |
| 1.5 | Reusable | — |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | Full **mitigation → review → evidence → versioning** loop |
| 1.8 | Domain | **Risk** instances, **incidents**, **files/evidence**, **users** |

---

## 2. Files analysed

- [`src/components/Risk/RiskWorkflow.vue`](../../src/components/Risk/RiskWorkflow.vue)
- [`src/services/riskService.js`](../../src/services/riskService.js) (`hasRiskInstancesCache`, `getData`, `setData`)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.4 | `computed` | Very large (user task sections, filters) |
| 2.5 | `watch` | Yes |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | `axios` shim; **many** `API_ENDPOINTS` usages |
| 2.12 | Data passing | Heavy **internal state**; some N+1 patterns (`LATEST_REVIEW` per risk) |
| 2.13 | Loading/error | Mixed; console logging for debugging |
| 2.14 | RBAC | Relies on APIs + user roles from `CURRENT_USER` / `CUSTOM_USERS` |

---

## 4. Current data flow (high level)

1. **User context:** `GET` `CURRENT_USER`, `CUSTOM_USERS`, `USERS_FOR_DROPDOWN`.  
2. **Queues:** `USER_RISKS(userId)`, `REVIEWER_TASKS(userId)` in parallel.  
3. **Per risk row:** `LATEST_REVIEW`, `GET_ASSIGNED_REVIEWER`, `RISK_MITIGATIONS`, `RISK_FORM_DETAILS` in various branches.  
4. **Mutations:** `UPDATE_MITIGATION_STATUS`, `ASSIGN_REVIEWER`, `COMPLETE_REVIEW`, `UPLOAD_RISK_EVIDENCE`, `DELETE_RISK_EVIDENCE`.  
5. **Detail pane:** `RISK_INSTANCE(selectedRiskId)` multiple times; `/api/file-operations/`; incident linked evidence `/api/incidents/:id/linked-evidence/`.  
6. **Versioning:** `RISK_VERSION`, `RISK_VERSIONS`.  
7. **Cache:** `riskDataService` for instances prefetch path.  
8. **Notify:** `PUSH_NOTIFICATION`.

---

## 5. Variable inventory (clusters)

| Cluster | Examples | Local? | Pinia? |
|---------|----------|--------|--------|
| User selection | `selectedUserId` | Yes | Optional `risk.workflowSelectedUserId` if shared |
| Task lists | `userRisks`, `reviewerTasks` | No | `risk.workflowUserRisks`, `risk.workflowReviewerTasks` |
| Selected risk | `selectedRiskId`, detail objects | Partial | `risk.selectedWorkflowInstanceId` + `instanceDetailsById` |
| Version UI | `globalSelectedVersion` | Yes | No |
| Evidence / file ops | upload progress | Yes | No |
| Comments / mitigations | arrays | No | Cached slices per instance id |

---

## 6. Local state to keep

- Tab/accordion UI, upload progress bars, modal visibility, unsaved text fields, version dropdown **UI index**.

---

## 7. State to move to Pinia (phased)

**Phase A — lists & selection**

- `riskInstances` (shared with list pages)  
- `fetchUserRisks`, `fetchReviewerTasks`

**Phase B — detail**

- `fetchRiskInstanceBundle(instanceId)` internal `Promise.all` for mitigations + form + latest review + assigned reviewer (reduce N+1 from template-driven calls)

**Phase C — mutations**

- Each POST/DELETE as action with **invalidation** of affected keys

---

## 8. API call inventory (grouped)

**Users / session**

- `PUSH_NOTIFICATION` — POST  
- `CURRENT_USER` — GET  
- `CUSTOM_USERS` — GET  
- `USERS_FOR_DROPDOWN` — GET  

**Queues**

- `USER_RISKS(selectedUserId)` — GET  
- `REVIEWER_TASKS(selectedUserId)` — GET  

**Per-instance reads**

- `LATEST_REVIEW(riskInstanceId)` — GET (watch N+1)  
- `GET_ASSIGNED_REVIEWER(riskId)` — GET  
- `RISK_MITIGATIONS(riskId)` — GET  
- `RISK_FORM_DETAILS(riskId)` — GET  
- `REVIEWER_COMMENTS(riskId)` — GET  
- `RISK_INSTANCE(riskInstanceId)` — GET (multiple)  

**Mutations**

- `UPDATE_MITIGATION_STATUS` — POST  
- `ASSIGN_REVIEWER` — POST  
- `COMPLETE_REVIEW` — POST  
- `UPLOAD_RISK_EVIDENCE` — POST (multipart)  
- `DELETE_RISK_EVIDENCE(fileId)` — DELETE  

**Files / incidents**

- `/api/file-operations/` — GET  
- `/api/incidents/:id/linked-evidence/` — GET  
- Download URL pattern for linked evidence documents  

**Versioning**

- `RISK_VERSION(riskId, version)` — GET  
- `RISK_VERSIONS(riskId)` — GET  

*(Exact parameter names vary — align with [`api.js`](../../src/config/api.js).)*

---

## 9–12. Store design notes

- Prefer **`fetchWorkflowBundle(instanceId)`** action returning `{ instance, mitigations, form, latestReview, assignedReviewer, comments }` to collapse round-trips.  
- **Getters:** `workflowTasksFlattened`, `isInstanceStale(id)`.  
- **State machine:** `workflowStatus: 'idle'|'loading'|'error'` per section if needed.

---

## 13. Cache-first

- **Instance list:** TTL as other pages.  
- **Detail bundle:** short TTL or invalidate on any mutation touching that id.  
- **Reviewer tasks:** 30–60 s TTL (frequently changing).

---

## 14. Repeated API calls

- `RISK_INSTANCE(selectedRiskId)` appears **many times** — consolidate.  
- `/api/file-operations/` repeated — memoize in store with short TTL or single fetch per session.

---

## 15. Prop drilling

Internal only; refactor will **split** into children with explicit props.

---

## 16–17. Forms / tables

- Many inline forms (mitigation, review, assign) — **keep draft text local**; submit via actions.

---

## 18. Dashboard

Embedded metrics per sections — optional small charts; treat like local derived data from store bundles.

---

## 19. RBAC

Centralize permission checks for “Assign reviewer”, “Upload evidence”, “Complete review” using future `permissionStore`.

---

## 20. Async UI

- Per-section spinners; global error banner; retry for bundle fetch.  
- Evidence upload: progress + cancel.

---

## 21. Optimistic UI

**Avoid** for `COMPLETE_REVIEW`, `UPDATE_MITIGATION_STATUS`, deletes.  
Possible: **non-regulatory** UI flags only (collapsed section).

---

## 22. Smart vs presentational

**Strong recommendation:** break into:

- `RiskWorkflowPage.vue` (container: Pinia)  
- `RiskTaskList.vue`, `RiskInstanceDetail.vue`, `RiskEvidencePanel.vue`, `RiskVersionHistory.vue` (presentational)

---

## 23. Normalization

Highly beneficial here:

- `instancesById`  
- `reviewsByInstanceId`  
- `mitigationsByRiskId`  

Avoid storing same nested instance object on every task row.

---

## 24–27. Migration / priority / steps

**Priority:** High (complexity + data volume).  
**Approach:** **Phase A → C** above; add tests after each phase.  
**Risk:** regressions in evidence/incident linking — test heavily.

---

## 28. Testing checklist

- User switch clears stale tasks.  
- Selecting instance loads **one** bundle request (after refactor).  
- Mitigation update refreshes correct cards.  
- Evidence upload/delete lists consistent.  
- Version switch loads correct snapshot.  
- Incident-linked evidence download path.

---

## 29. Guidelines

- **Do not** move File blobs to Pinia.  
- **Do** collapse N+1 review fetches into bundle actions.  
- **First refactor step:** extract **read** paths before **write** paths to reduce regression blast radius.
