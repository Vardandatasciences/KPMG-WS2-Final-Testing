# Missed compliance & audit task self-healing — workflow only

Read top to bottom. No separate overview or diagram sections — everything is in this workflow.

```
═══════════════════════════════════════════════════════════════════════════════
  MISSED COMPLIANCE & AUDIT TASK — FULL WORKFLOW (implementation)
  Manual audits (I/E/S) + AI audits (A). Same scheduler as policy_self_healing.py.
═══════════════════════════════════════════════════════════════════════════════

RULES (product) — BOTH manual and AI
  • Reminders to auditor / reviewer       → AUDITOR / REVIEWER (NOT Assignee)
  • Due soon                              → 4 days before DueDate or review due
  • Review due                            → ReviewStartDate + 5 days (ReviewDate = review ENDED)
  • Escalation                            → AFTER 3+ overdue reminder days → Compliance Manager
  • SubPolicy EndDate only                → STOP all reminders after subpolicy end

MANUAL ONLY (TaskView /audit/{id}/tasks)
  • Missing compliance evidence           → audit_findings.Evidence empty
  • Frequency                             → AssignedDate + audit.Frequency
  • Missing audit evidence                → audit.Evidence empty

AI ONLY (AIAuditDocumentUpload /ai-audit/{id}/upload)
  • Missing evidence                      → no documents; EvidenceReminderDays from assign
  • Frequency                             → AIAuditSchedule (upload page), NOT audit.Frequency
  • Run / report                          → remind upload, run check, download report
  • Merge check_ai_audit_evidence         → avoid duplicate alerts

SCHEDULING (how the job runs — use same as policy self-heal)
  Triggers (any one):
    (1) apps.py → _run_compliance_audit_self_heal_loop()
        when ENABLE_COMPLIANCE_AUDIT_SELF_HEAL_SCHEDULER=true
    (2) python manage.py run_compliance_audit_self_heal_reminders
    (3) POST /api/compliance-audit/self-healing/reminders/run/
        header X-Compliance-Audit-Self-Heal-Secret

  Main entry:
    execute_compliance_audit_self_heal_reminders(for_date=today)
      → returns { date, sent, skipped, escalations }

  New module: grc/routes/Compliance/compliance_audit_self_healing.py
  Reuse: NotificationService.send_multi_channel_notification
         notifications.py (_insert_db_notification, _append_memory_notification)
         get_user_email_from_id — same as policy_self_healing.py

───────────────────────────────────────────────────────────────────────────────
PART A — START OF EACH DAILY RUN
───────────────────────────────────────────────────────────────────────────────

    START
      │
      ▼
    Load ALL audits (tenant-aware) — includes AuditType A (AI)
      │
      ▼
    For EACH audit ──────────────────────────────────────────────────────────┐
      ▼                                                                       │
    self_heal_active_for_audit(audit, today) — SubPolicy end cap                │
      ├── today > SubPolicy.EndDate ──► SKIP                                  │
      └── else ACTIVE ────────────────────────────────────────────────────────┘
      │
      ▼
    AuditType == 'A' ?  YES → PARTS AI-B → AI-F    NO → PARTS B → F (manual)
      │
      ▼
    PART G escalation — max 1 notify per TYPE per day
      │
      ▼
    ComplianceAuditReminderSent.get_or_create(audit, type, date=today)  ◄── dedup
      │
      ▼
    END RUN

  Data (migration):
    SubPolicy.EndDate (NEW field on subpolicy only)
    Table compliance_audit_reminder_sent (dedup)
    Table compliance_audit_self_heal_escalation (pending / assigned)

───────────────────────────────────────────────────────────────────────────────
PART B — MANUAL ONLY — MISSING COMPLIANCE EVIDENCE (per audit_finding)
───────────────────────────────────────────────────────────────────────────────

    Audit Status in: Yet to Start, Work In Progress  (NOT Under review / Completed)
      │
      ▼
    For EACH row in audit_findings for this AuditId
      │
      ▼
    audit_findings.Evidence empty or whitespace?
      │
      NO ──────────────────────────────────────────────► next finding
      │
      YES
      ▼
    should_remind_missing_compliance_evidence(audit, finding, today)
      │
      ├── already sent type=missing_compliance_evidence today? ──► SKIP
      │
      NO
      ▼
    _notify_auditor_missing_evidence(audit, finding, audit.Auditor_id)
      • DB notification + in-app (Notifications.vue)
      • optional email via NotificationService
      • link: /audit/{AuditId}/tasks  (TaskView — Upload Compliance Evidence)
      │
      ▼
    Record ComplianceAuditReminderSent

  Why Auditor: assign_audit sets audit_findings.UserId = audit.Auditor_id;
               get_my_audits filters a.auditor = current user.

───────────────────────────────────────────────────────────────────────────────
PART C — MANUAL ONLY — FREQUENCY (“time to perform audit”)
───────────────────────────────────────────────────────────────────────────────

    audit.Frequency set and Frequency > 0  (skip “Only Once” / 0)
    audit.AssignedDate set
      │
      ▼
    days_since = (today - AssignedDate.date()).days
    days_since > 0 AND (days_since % Frequency == 0)   ◄── same idea as policy_should_remind_today
      │
      NO ──────────────────────────────────────────────► SKIP
      │
      YES
      ▼
    Status NOT Completed; default skip if Under review (auditor handed off)
      │
      ▼
    should_remind_frequency_today → dedup type=audit_frequency
      │
      ▼
    _notify_auditor_frequency(audit, audit.Auditor_id)
      • message: perform audit per schedule
      • link: /audit/{AuditId}/tasks

───────────────────────────────────────────────────────────────────────────────
PART D — MANUAL + AI — AUDIT DUE DATE (Auditor) — 4 days before, due day, overdue
───────────────────────────────────────────────────────────────────────────────

    audit.DueDate set
      │
      ▼
    audit_work_complete(audit) ?   ◄── all findings Check in 1,2,3 + evidence where needed
      │
      YES ─────────────────────────────────────────────► SKIP due/overdue (Part D done)
      │
      NO
      ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ DueDate - today == 4                                            │
    │   → should_remind type=audit_due_soon → _notify_auditor_due     │
    │ today == DueDate                                                │
    │   → type=audit_due_today → _notify_auditor_due                  │
    │ today > DueDate                                                 │
    │   → type=audit_overdue → _notify_auditor_overdue                │
    └─────────────────────────────────────────────────────────────────┘
      │
      ▼
    overdue_reminder_days(audit)  ◄── count days type=audit_overdue sent since DueDate
      │
      ├── count < 3 ───────────────────────────────────► stay in Part D only
      │
      └── count >= 3 ──────────────────────────────────► go to PART G (auditor escalation)

───────────────────────────────────────────────────────────────────────────────
PART E — MANUAL + AI — REVIEW (Reviewer) — after auditor sends for review
───────────────────────────────────────────────────────────────────────────────

  USER STEP (auditor, TaskView):
    Auditor saves work → Send for Review
      │
      ▼
    PATCH send_audit_for_review in auditing.py:
      Status = 'Under review'
      ReviewStartDate = COALESCE(ReviewStartDate, NOW())   ◄── REQUIRED fix today missing
      │
      ▼
    review_due_date(audit) = ReviewStartDate.date() + 5   ◄── COMPLIANCE_AUDIT_REVIEW_SLA_DAYS

  DAILY JOB (only if Status = 'Under review'):
      │
      ▼
    review_complete(audit) ?
      • ReviewStatus Accept(2) or Reject(3), OR ReviewDate set (review ENDED)
      │
      YES ─────────────────────────────────────────────► SKIP Part E
      │
      NO
      ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │ review_due_date - today == 4                                    │
    │   → type=review_due_soon → _notify_reviewer(audit.reviewer)     │
    │ today == review_due_date                                        │
    │   → type=review_due_today                                       │
    │ today > review_due_date                                         │
    │   → type=review_overdue                                         │
    │ link: /reviewer/task/{AuditId}  (ReviewTaskView)                │
    └─────────────────────────────────────────────────────────────────┘
      │
      ▼
    overdue review reminder days >= 3 ?
      │
      YES ─────────────────────────────────────────────► PART G (reviewer escalation)

  Fields meaning:
    ReviewStartDate = review START (use for SLA)
    ReviewDate      = review FINISHED — do NOT use as due date
    ReviewStatus    = 0 Yet to Start, 1 In Review, 2 Accept, 3 Reject

───────────────────────────────────────────────────────────────────────────────
PART F — MANUAL ONLY — AUDIT EVIDENCE (optional same run as Part B)
───────────────────────────────────────────────────────────────────────────────

    audit.Evidence empty at audit level (Upload Audit Evidence on TaskView)
      │
      ▼
    Same gates as Part B (active audit, auditor, dedup type=missing_audit_evidence)
      │
      ▼
    _notify_auditor_missing_audit_evidence → /audit/{AuditId}/tasks

───────────────────────────────────────────────────────────────────────────────
PART AI-B — AI ONLY — MISSING EVIDENCE (upload page + EvidenceReminderDays)
───────────────────────────────────────────────────────────────────────────────

    ai_audit_has_documents == false AND days since AssignedDate >= EvidenceReminderDays
      → _notify_auditor_ai_evidence → /ai-audit/{AuditId}/upload
      → merge check_ai_audit_evidence (no duplicate alert)

───────────────────────────────────────────────────────────────────────────────
PART AI-C — AI ONLY — SCHEDULE FREQUENCY (AIAuditSchedule on upload page)
───────────────────────────────────────────────────────────────────────────────

    Frequency Daily/Monthly/… in ai_audit_schedule — NOT audit.Frequency
      → should_remind_ai_schedule_today → _notify_auditor_ai_schedule

───────────────────────────────────────────────────────────────────────────────
PART AI-D — AI ONLY — RUN CHECK / REPORT (optional)
───────────────────────────────────────────────────────────────────────────────

    Docs uploaded but no results → ai_run_pending
    Results but no report action → ai_report_pending (optional)

───────────────────────────────────────────────────────────────────────────────
PART G — ESCALATION (manual + AI) → COMPLIANCE MANAGER (after overdue reminders)
───────────────────────────────────────────────────────────────────────────────

    should_escalate(audit, role='auditor' OR 'reviewer', today)
      │
      ▼
    _compliance_manager_user_ids(tenant_id)   ◄── RBAC role "Compliance Manager"
      │
      ▼
    _ensure_pending_escalation(audit, escalation_type)
      → ComplianceAuditSelfHealEscalation status=pending_assignment
      │
      ▼
    _notify_compliance_managers_escalation(audit, type)
      • in-app metadata → dashboard ?auditEscalations=1
      • dedup managers same day

  MANAGER (UI — mirror Policy Dashboard renewal escalations):
    GET  /api/compliance-audit/self-healing/escalations/pending/
         → list_pending_compliance_audit_escalations()
         → _is_compliance_manager(user)
      │
      ▼
    Manager picks new user
      │
      ▼
    POST /api/compliance-audit/{audit_id}/self-healing/assign/
         body: { role: "auditor"|"reviewer", assigned_user_id }
         → assign_compliance_audit_escalation()
      │
      ├── role=auditor  → UPDATE audit SET auditor = assigned_user_id
      └── role=reviewer → UPDATE audit SET reviewer = assigned_user_id
      │
      ▼
    escalation status = assigned
    _notify_escalation_assignee()  ◄── new person gets first reminder
      │
      ▼
    NEXT daily runs: reminders go to NEW auditor/reviewer (not manager again)

───────────────────────────────────────────────────────────────────────────────
FRONTEND / UI TOUCH
───────────────────────────────────────────────────────────────────────────────

  SubPolicy create/edit     → capture SubPolicy.EndDate (no field on Compliance)
  Compliance Manager panel  → list pending escalations, assign auditor/reviewer
  Notifications.vue         → TaskView, ReviewTaskView, /ai-audit/{id}/upload, escalation panel
  api.js                    → COMPLIANCE_AUDIT_SELF_HEAL_* endpoints

═══════════════════════════════════════════════════════════════════════════════
                              END OF WORKFLOW
     (Functions and why — tables below)
═══════════════════════════════════════════════════════════════════════════════
```

Regenerate Word: `python docs/build_compliance_audit_self_heal_word.py`

---

## Functions and why we use them

### Scheduling

| Function | Why we use it |
|----------|----------------|
| `execute_compliance_audit_self_heal_reminders` | Main daily job: loops audits, runs Parts B–G, returns sent/skipped/escalation counts. Same role as `execute_policy_self_heal_reminders`. |
| `run_compliance_audit_self_heal_reminders` | Webhook/cron entry for Scheduler microservice; validates `COMPLIANCE_AUDIT_SELF_HEAL_CRON_SECRET`. |
| `run_compliance_audit_self_heal_reminders` (management command) | Manual/ops run: `python manage.py run_compliance_audit_self_heal_reminders`. |
| `_run_compliance_audit_self_heal_loop` (`apps.py`) | Optional inline thread on runserver when `ENABLE_COMPLIANCE_AUDIT_SELF_HEAL_SCHEDULER=true`. |

### SubPolicy end

| Function | Why we use it |
|----------|----------------|
| `SubPolicy.EndDate` (new field) | Only place for lifecycle end; Compliance has no EndDate. UI on subpolicy create/edit. |
| `effective_subpolicy_end_date(audit)` | Reads end date from `audit.SubPolicyId`; caps reminders even if `audit.DueDate` is later. |
| `self_heal_active_for_audit(audit, today)` | Master gate: subpolicy end + not fully complete — manual and AI. |
| `is_manual_audit` / `is_ai_audit` | Routes to Part B–F vs AI-B–F. |
| `audit_self_heal_action_url(audit)` | Manual → TaskView; AI → `/ai-audit/{id}/upload`. |

### Evidence

| Function | Why we use it |
|----------|----------------|
| `should_remind_missing_compliance_evidence` | True when `audit_findings.Evidence` empty, audit in progress, dedup not sent today. |
| `_notify_auditor_missing_evidence` | Sends reminder to `audit.Auditor`; link `/audit/{id}/tasks` (TaskView upload compliance evidence). |
| `_notify_auditor_missing_audit_evidence` | Same for `audit.Evidence` empty (Upload Audit Evidence section). |

### Frequency (manual)

| Function | Why we use it |
|----------|----------------|
| `should_remind_frequency_today` | `(today - AssignedDate) % audit.Frequency == 0`; manual only. |
| `_notify_auditor_frequency` | Perform audit per assign frequency; TaskView link. |

### AI evidence & schedule

| Function | Why we use it |
|----------|----------------|
| `ai_audit_has_documents` | True if uploaded docs / `ai_audit_data` exist. |
| `should_remind_ai_missing_evidence` | Uses `EvidenceReminderDays` from Assign Audit (AI). |
| `_notify_auditor_ai_evidence` | Upload page link; absorbs `check_ai_audit_evidence`. |
| `should_remind_ai_schedule_today` | `AIAuditSchedule` next_run / cron from upload page. |
| `_notify_auditor_ai_schedule` | Remind before scheduled AI run. |
| `ai_audit_work_complete` | Docs processed + results; stops due reminders for AI. |
| `should_remind_ai_run_or_report` | Optional: run check or download report. |

### Audit due

| Function | Why we use it |
|----------|----------------|
| `audit_work_complete` | Stops due/overdue when all findings done + evidence present or Status Completed. |
| `should_remind_audit_due_today` | Picks type `audit_due_soon` (4d before), `audit_due_today`, or `audit_overdue`. |
| `_notify_auditor_due` / `_notify_auditor_overdue` | Notifies auditor around `audit.DueDate`. |
| `overdue_reminder_days` | Counts calendar days `audit_overdue` sent after DueDate; triggers Part G when >= 3. |

### Review

| Function | Why we use it |
|----------|----------------|
| `send_audit_for_review` (PATCH) | Must set `ReviewStartDate=NOW` when Status→Under review; today only sets Status. |
| `review_due_date` | `ReviewStartDate.date() + 5` days (`COMPLIANCE_AUDIT_REVIEW_SLA_DAYS`); not `ReviewDate`. |
| `review_complete` | Stops review reminders when ReviewStatus Accept/Reject or `ReviewDate` set. |
| `should_remind_review_today` | `review_due_soon` / `review_due_today` / `review_overdue` for reviewer. |
| `_notify_reviewer_due` / `_notify_reviewer_overdue` | Notifies `audit.reviewer`; link `/reviewer/task/{id}`. |

### Escalation

| Function | Why we use it |
|----------|----------------|
| `should_escalate` | True after 3+ overdue reminder days (auditor or reviewer path) per product rule. |
| `_compliance_manager_user_ids` | Lists active RBAC Compliance Manager users (tenant); mirrors `_policy_manager_user_ids`. |
| `_is_compliance_manager` | Guards manager-only list/assign APIs. |
| `_ensure_pending_escalation` | Creates `ComplianceAuditSelfHealEscalation` `pending_assignment` if missing. |
| `_notify_compliance_managers_escalation` | Email + in-app to managers; dashboard link `?auditEscalations=1`. |
| `list_pending_compliance_audit_escalations` | GET API: manager dashboard list. |
| `assign_compliance_audit_escalation` | POST API: updates `audit.auditor` or `audit.reviewer`; notifies assignee. |
| `_notify_escalation_assignee` | First reminder to newly assigned auditor/reviewer after manager assign. |

### Dedup / data

| Function | Why we use it |
|----------|----------------|
| `ComplianceAuditReminderSent` | One row per audit + `reminder_type` + calendar day; prevents duplicate spam. |
| `ComplianceAuditSelfHealEscalation` | Tracks pending vs assigned escalation and who manager picked. |

### Reuse (existing code)

| Function | Why we use it |
|----------|----------------|
| `NotificationService.send_multi_channel_notification` | Same email/channel pipeline as policy self-heal and rest of GRC. |
| `_insert_db_notification` / `_append_memory_notification` | Copy pattern from `policy_self_healing.py` for DB + in-app list. |
| `get_user_email_from_id` | Resolve recipient email for auditor/reviewer/manager. |
| `RBACUtils.get_user_id_from_request` | JWT user on manager assign APIs. |
| `get_tenant_id_from_request` / `tenant_filter` | Multi-tenancy on all queries. |
| `policy_should_remind_today` (pattern only) | Frequency uses same modulo-day logic from policy self-heal. |

### AI merge / patch

| Function | Why we use it |
|----------|----------------|
| `check_ai_audit_evidence` (deprecate) | Logic moves into `should_remind_ai_missing_evidence`. |
| `ai_audit_api.py` `ReviewStartDate` | Set when AI audit → Under review after docs processed. |

### API routes

| Function | Why we use it |
|----------|----------------|
| `POST /api/compliance-audit/self-healing/reminders/run/` | External scheduler trigger. |
| `GET /api/compliance-audit/self-healing/escalations/pending/` | Manager escalation queue. |
| `POST /api/compliance-audit/{audit_id}/self-healing/assign/` | Manager reassign auditor or reviewer. |

### Frontend

| Function | Why we use it |
|----------|----------------|
| SubPolicy UI (`VV.vue` / framework flows) | Capture `SubPolicy.EndDate` only. |
| Compliance Manager escalation panel | List pending + assign user (mirror PolicyDashboard renewal). |
| `Notifications.vue` | Deep links to TaskView, ReviewTaskView, escalation dashboard. |
| `api.js` `COMPLIANCE_AUDIT_SELF_HEAL_*` | Frontend endpoints for panel and actions. |
