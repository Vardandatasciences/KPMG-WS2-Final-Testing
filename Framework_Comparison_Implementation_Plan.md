# Framework Comparison — Implementation Plan

## Document Information
- **Date:** 28 May 2026
- **Prepared for:** Change Management / Regulatory Compliance Team
- **Status:** Gap Analysis & Implementation Roadmap

---

## 1. Executive Summary

The Framework Comparison feature currently handles:
- Finding amendment documents online
- Extracting rules using AI
- Identifying brand-new rules and adding them via approval

**Critical Gap:** It does **not** handle updating existing rules that have changed in the amendment. It also lacks integration with Risk and Audit modules, automatic periodic checking, and high-level impact summaries.

---

## 2. Current State (What Already Exists)

### 2.1 Backend — Existing Functions

| Function | File | What It Does | Status |
|----------|------|-------------|--------|
| `check_framework_updates()` | `framework_comparison.py` | Searches the internet for latest amendment PDF and downloads it | ✅ Existing |
| `query_perplexity_api()` | `framework_update_checker.py` | Calls Perplexity AI to find official amendment PDF links | ✅ Existing |
| `start_amendment_analysis()` | `framework_comparison.py` | Triggers AI to read downloaded PDF and extract rules in background | ✅ Existing |
| `process_downloaded_amendment()` | `amendment_processor.py` | Main pipeline: extract sections → policies → sub-policies → compliances | ✅ Existing |
| `get_framework_origin_data()` | `framework_comparison.py` | Fetches current framework data (policies, sub-policies, compliances) from database | ✅ Existing |
| `get_framework_target_data()` | `framework_comparison.py` | Fetches amendment-extracted rules from JSON storage | ✅ Existing |
| `match_amendments_compliances()` | `framework_comparison.py` | Matches all amendment compliances against database compliances using AI | ✅ Existing |
| `find_control_matches()` | `framework_comparison.py` | Finds best matching origin items for a single target control | ✅ Existing |
| `batch_match_controls()` | `framework_comparison.py` | Matches multiple controls at once | ✅ Existing |
| `add_compliance_from_amendment()` | `framework_comparison.py` | Creates new compliance + policy + sub-policy and sends for approval | ✅ Existing |
| `get_framework_comparison_summary()` | `framework_comparison.py` | Returns summary counts (new, modified, deprecated) | ✅ Existing |
| `get_migration_gap_analysis()` | `framework_comparison.py` | Returns gap items with priorities | ✅ Existing |
| `get_amendment_document_info()` | `framework_comparison.py` | Returns document processing status for polling | ✅ Existing |
| `calculate_hybrid_similarity()` | `similarity_matcher.py` | Calculates similarity score using text + keyword + AI embedding | ✅ Existing |
| `match_all_amendments_compliances()` | `similarity_matcher.py` | Bulk matching with AI fallback | ✅ Existing |
| `_perform_ai_gap_analysis()` | `framework_comparison.py` | AI-powered gap analysis between original and amended versions | ✅ Existing |
| `_assess_ai_compliance_impact()` | `framework_comparison.py` | Assesses compliance impact using AI | ✅ Existing |
| `cancel_amendment_analysis()` | `framework_comparison.py` | Cancels running background analysis | ✅ Existing |

### 2.2 Frontend — Existing Functions

| Function | File | What It Does | Status |
|----------|------|-------------|--------|
| `onFrameworkChange()` | `FrameworkComparisonUpdated.vue` | Loads framework data, document info, target data, summary | ✅ Existing |
| `checkForUpdates()` | `FrameworkComparisonUpdated.vue` | Calls backend to search and download amendment | ✅ Existing |
| `startAnalysis()` | `FrameworkComparisonUpdated.vue` | Triggers background analysis, starts polling | ✅ Existing |
| `startAnalysisPolling()` | `FrameworkComparisonUpdated.vue` | Polls every 3 seconds for completion status | ✅ Existing |
| `checkAndCompleteAnalysis()` | `FrameworkComparisonUpdated.vue` | Checks if analysis finished, refreshes data | ✅ Existing |
| `matchCompliances()` | `FrameworkComparisonUpdated.vue` | Calls compliance matching API | ✅ Existing |
| `findMatches(control)` | `FrameworkComparisonUpdated.vue` | Finds matches for a single control | ✅ Existing |
| `openComplianceModal()` | `FrameworkComparisonUpdated.vue` | Opens modal to add missing compliance | ✅ Existing |
| `submitComplianceForm()` | `FrameworkComparisonUpdated.vue` | Submits new compliance for approval | ✅ Existing |
| `saveAnalysisState()` / `loadAnalysisState()` | `FrameworkComparisonUpdated.vue` | Persists analysis progress in sessionStorage | ✅ Existing |
| `getFrameworksWithAmendments()` | `frameworkComparisonService.js` | Fetches frameworks list with amendment counts | ✅ Existing |
| `startAmendmentAnalysis()` | `frameworkComparisonService.js` | API call to start analysis | ✅ Existing |
| `matchAmendmentsCompliances()` | `frameworkComparisonService.js` | API call for compliance matching | ✅ Existing |
| `createComplianceFromAmendment()` | `frameworkComparisonService.js` | API call to create new compliance | ✅ Existing |

---

## 3. Gap Analysis (What Is Missing)

### 3.1 Critical Gaps

| # | Gap | Impact | Priority |
|---|-----|--------|----------|
| 1 | **No mechanism to update existing compliances that changed in amendment** | Database rules become outdated. Compliance drift. Regulatory risk. | 🔴 Critical |
| 2 | **No connection to Risk module** | Cannot see which risk entries are affected by a framework change. | 🟠 High |
| 3 | **No connection to Audit module** | Cannot see which audits are impacted and need re-auditing. | 🟠 High |
| 4 | **No automatic periodic checking** | Requires manual human intervention every time. Amendments may be missed. | 🟡 Medium |
| 5 | **No policy-level impact summary dashboard** | Only rule-by-rule view exists. No high-level "3 policies, 7 sub-policies affected" summary. | 🟡 Medium |

---

## 4. Implementation Plan

### Phase 1: Update Existing Rules That Changed (MOST CRITICAL)

**Objective:** When an amendment modifies an existing rule, the system must flag it, show the difference, and let the user update it through an approval workflow.

#### 4.1.1 New Backend Functions

| Function | Purpose | Input | Output | File To Add |
|----------|---------|-------|--------|-------------|
| `detect_control_changes()` | Compares amendment compliance against matched database compliance and detects if wording/requirements changed | `target_compliance`, `origin_compliance` | `change_detected` (bool), `diff_fields` (list), `old_text`, `new_text` | `framework_comparison.py` |
| `get_compliance_change_detail()` | Returns side-by-side diff of what changed | `framework_id`, `compliance_id`, `amendment_id` | JSON with old vs new values for each field | `framework_comparison.py` |
| `create_compliance_update_request()` | Creates an update request record (similar to ComplianceApproval but for updates) | `framework_id`, `compliance_id`, `proposed_changes`, `reviewer_id` | `update_request_id`, `status: pending` | `framework_comparison.py` |
| `apply_compliance_update()` | Applies approved changes to the existing compliance record | `update_request_id` | `success` (bool), `updated_compliance` | `framework_comparison.py` |
| `get_pending_compliance_updates()` | Lists all compliance update requests pending approval | `framework_id` (optional) | List of update requests with status | `framework_comparison.py` |
| `reject_compliance_update()` | Rejects an update request with reason | `update_request_id`, `rejection_reason` | `success` (bool) | `framework_comparison.py` |

#### 4.1.2 New Frontend Functions

| Function | Purpose | File To Add |
|----------|---------|-------------|
| `showComplianceDiff(control)` | Opens a modal showing side-by-side old vs new text for a changed compliance | `FrameworkComparisonUpdated.vue` |
| `openUpdateComplianceModal(match)` | Opens a pre-filled form with the proposed changes for an existing compliance | `FrameworkComparisonUpdated.vue` |
| `submitComplianceUpdate()` | Submits the update request to backend for reviewer approval | `FrameworkComparisonUpdated.vue` |
| `loadPendingUpdates()` | Fetches and displays pending compliance update requests | `FrameworkComparisonUpdated.vue` |
| `updateComplianceService.updateCompliance()` | API service call to backend | `frameworkComparisonService.js` |
| `updateComplianceService.getChangeDetail()` | API service call to get diff | `frameworkComparisonService.js` |

#### 4.1.3 Database Changes

| Table / Column | Purpose |
|----------------|---------|
| `ComplianceUpdateRequest` (new table) | Stores requests to update existing compliances. Columns: `id`, `framework_id`, `compliance_id`, `old_values` (JSON), `proposed_values` (JSON), `reviewer_id`, `status` (pending/approved/rejected), `created_at`, `updated_at`, `rejection_reason` |
| `Compliance.ComplianceHistory` (new JSON column) | Tracks version history of compliance changes |
| `Compliance.AmendmentSource` (new column) | Links compliance to the amendment that introduced/updated it |

---

### Phase 2: Risk Module Integration

**Objective:** When a compliance changes, show which Risk entries are linked to it.

#### 4.2.1 New Backend Functions

| Function | Purpose | Input | Output | File To Add |
|----------|---------|-------|--------|-------------|
| `get_affected_risks()` | Finds all risk entries linked to a given compliance or policy | `framework_id`, `compliance_id` | List of risks with `RiskId`, `RiskName`, `ImpactLevel` | `framework_comparison.py` or new `risk_integration.py` |
| `get_risk_impact_summary()` | Returns count of risks affected by the amendment | `framework_id`, `amendment_id` | `total_risks_affected`, `high_impact`, `medium_impact`, `low_impact` | `framework_comparison.py` |
| `notify_risk_owners()` | Sends notification to risk owners when linked compliance changes | `framework_id`, `compliance_id`, `change_type` | `success` (bool) | `framework_comparison.py` |

#### 4.2.2 New Frontend Functions

| Function | Purpose | File To Add |
|----------|---------|-------------|
| `showAffectedRisks(control)` | Expands a section showing linked risk entries for a compliance | `FrameworkComparisonUpdated.vue` |
| `loadRiskSummary()` | Fetches and displays risk impact summary at top of page | `FrameworkComparisonUpdated.vue` |

---

### Phase 3: Audit Module Integration

**Objective:** When a policy or compliance changes, flag which audits cover that area and may need re-auditing.

#### 4.3.1 New Backend Functions

| Function | Purpose | Input | Output | File To Add |
|----------|---------|-------|--------|-------------|
| `get_affected_audits()` | Finds all audits linked to a given policy/sub-policy/compliance | `framework_id`, `compliance_id` | List of audits with `AuditId`, `AuditName`, `Status`, `LastAuditDate` | `framework_comparison.py` or new `audit_integration.py` |
| `get_audit_impact_summary()` | Returns count of audits affected | `framework_id`, `amendment_id` | `total_audits_affected`, `requiring_reaudit`, `completed` | `framework_comparison.py` |
| `flag_audit_for_reaudit()` | Marks an audit as needing re-audit due to framework change | `audit_id`, `compliance_id`, `reason` | `success` (bool) | `framework_comparison.py` |

#### 4.3.2 New Frontend Functions

| Function | Purpose | File To Add |
|----------|---------|-------------|
| `showAffectedAudits(control)` | Shows linked audits for a compliance | `FrameworkComparisonUpdated.vue` |
| `loadAuditSummary()` | Displays audit impact summary | `FrameworkComparisonUpdated.vue` |

---

### Phase 4: Automatic Periodic Checking

**Objective:** The system automatically checks for new amendments on a schedule without human intervention.

#### 4.4.1 New Backend Functions

| Function | Purpose | Input | Output | File To Add |
|----------|---------|-------|--------|-------------|
| `schedule_framework_update_check()` | Cron-scheduled task that runs weekly for all active frameworks | None (reads all active frameworks from DB) | Logs results, sends email/notification if amendment found | New `tasks.py` or `cron.py` |
| `should_check_framework()` | Determines if enough time has passed since last check (7-day cooldown logic) | `framework_id` | `should_check` (bool) | `framework_comparison.py` |
| `send_update_notification()` | Sends email/notification to admins when new amendment is found | `framework_id`, `amendment_name`, `document_url` | `success` (bool) | `framework_comparison.py` |

#### 4.4.2 Configuration Changes

| Setting | Purpose |
|---------|---------|
| `AUTO_CHECK_ENABLED` | Toggle automatic checking on/off |
| `AUTO_CHECK_INTERVAL_DAYS` | How often to check (default: 7) |
| `AUTO_CHECK_NOTIFICATION_EMAILS` | List of emails to notify when amendment found |

---

### Phase 5: Policy-Level Impact Summary Dashboard

**Objective:** Show a high-level summary of what the amendment impacts, not just individual rules.

#### 4.5.1 New Backend Functions

| Function | Purpose | Input | Output | File To Add |
|----------|---------|-------|--------|-------------|
| `get_policy_impact_summary()` | Returns aggregate stats: policies affected, sub-policies affected, compliances affected, risks affected, audits affected | `framework_id`, `amendment_id` | JSON summary with counts and lists | `framework_comparison.py` |
| `get_affected_policies_list()` | Returns list of all policies impacted by the amendment | `framework_id`, `amendment_id` | List of policies with change types | `framework_comparison.py` |
| `get_affected_subpolicies_list()` | Returns list of all sub-policies impacted | `framework_id`, `amendment_id` | List of sub-policies with parent policy | `framework_comparison.py` |

#### 4.5.2 New Frontend Functions

| Function | Purpose | File To Add |
|----------|---------|-------------|
| `showImpactSummary()` | Renders a dashboard card showing "3 Policies, 7 Sub-Policies, 12 Compliances, 4 Risks, 2 Audits affected" | `FrameworkComparisonUpdated.vue` |
| `expandPolicyTree()` | Interactive tree view showing affected policies → sub-policies → compliances | `FrameworkComparisonUpdated.vue` |

---

## 5. Workflow (read top to bottom)

No separate diagram images — full flow is inline text (same style as `docs/COMPLIANCE_AUDIT_SELF_HEAL.docx`).

```
═══════════════════════════════════════════════════════════════════════════════
  FRAMEWORK COMPARISON — CURRENT WORKFLOW (AS-IS)
  UI: FrameworkComparisonUpdated.vue  |  Backend: framework_comparison.py
═══════════════════════════════════════════════════════════════════════════════

RULES (today)
  • User must manually click “Check the updates” per framework
  • Amendment PDF → AI extract → match → add NEW rules only via approval
  • Matched controls show “You already have this” — NO update path for changed text

───────────────────────────────────────────────────────────────────────────────
PART A — SELECT FRAMEWORK & FIND AMENDMENT
───────────────────────────────────────────────────────────────────────────────

    START (user opens Framework Comparison page)
      │
      ▼
    User selects framework from dropdown
      │  onFrameworkChange() → load origin data, summary, document info
      │
      ▼
    User clicks “Check the updates”
      │  checkForUpdates() → check_framework_updates() / query_perplexity_api()
      │
      ▼
    Amendment PDF found on internet?
      │
      ├── NO ──► Show “No document found” ──► END (wait for user retry)
      │
      YES
      ▼
    Download PDF → MEDIA_ROOT/change_management/
      │
      ▼
    Show document card — status: Awaiting Analysis

───────────────────────────────────────────────────────────────────────────────
PART B — EXTRACT RULES FROM AMENDMENT (BACKGROUND)
───────────────────────────────────────────────────────────────────────────────

    User clicks “Start Analysis”
      │  startAnalysis() → start_amendment_analysis() → process_downloaded_amendment()
      │
      ▼
    Poll every 3s (startAnalysisPolling / get_amendment_document_info)
      │
      ▼
    Analysis complete?
      │
      ├── NO / ERROR / TIMEOUT ──► Show error; user may cancel (cancel_amendment_analysis)
      │
      YES
      ▼
    LEFT panel: extracted policies / sub-policies / compliances (target JSON)

───────────────────────────────────────────────────────────────────────────────
PART C — MATCH & ACT ON RESULTS (AS-IS GAP: UPDATE NOT SUPPORTED)
───────────────────────────────────────────────────────────────────────────────

    User clicks “Match Compliances”
      │  matchCompliances() → match_amendments_compliances() / similarity_matcher
      │
      ▼
    RIGHT panel: Matched vs Not Following / New / Modified counts (summary API)
      │
      ▼
    For EACH amendment control ─────────────────────────────────────────────┐
      │                                                                       │
      ▼                                                                       │
    Result type?                                                              │
      │                                                                       │
      ├── NEW / MISSING ──► User clicks “+” (openComplianceModal)             │
      │       │                                                               │
      │       ▼                                                               │
      │     Fill form + select reviewer → submitComplianceForm()              │
      │       │  add_compliance_from_amendment() → approval queue             │
      │       ▼                                                               │
      │     Reviewer approves → new Compliance active in DB                   │
      │                                                                       │
      ├── MATCHED ──► Show “You already have this”                          │
      │       │                                                               │
      │       └── NO diff / update UI ──► END for this control  ◄── GAP     │
      │                                                                       │
      └── (other summary types from get_framework_comparison_summary)         │
            └─────────────────────────────────────────────────────────────────┘
      │
      ▼
    END (user may save session state: saveAnalysisState / loadAnalysisState)

═══════════════════════════════════════════════════════════════════════════════
                              END OF AS-IS WORKFLOW
═══════════════════════════════════════════════════════════════════════════════
```

```
═══════════════════════════════════════════════════════════════════════════════
  FRAMEWORK COMPARISON — PROPOSED WORKFLOW (TO-BE)
  Adds: update existing compliances + risk/audit hooks (Phases 1–3)
═══════════════════════════════════════════════════════════════════════════════

    (PARTS A–B same as AS-IS: select framework → check updates → download →
     start analysis → poll → LEFT panel shows extracted rules)

───────────────────────────────────────────────────────────────────────────────
PART C — MATCH WITH CHANGE DETECTION (Phase 1)
───────────────────────────────────────────────────────────────────────────────

    User clicks “Match Compliances”
      │  match returns origin match + detect_control_changes() per pair
      │
      ▼
    RIGHT panel + optional Impact Summary card (Phase 5)
      │
      ▼
    For EACH amendment control ─────────────────────────────────────────────┐
      │                                                                       │
      ▼                                                                       │
    Result type?                                                              │
      │                                                                       │
      ├── NEW / MISSING ──► Same as AS-IS: + → approval → active in DB        │
      │                                                                       │
      ├── MATCHED ──► detect_control_changes(target, origin)                  │
      │       │                                                               │
      │       ├── similarity >= 0.85 AND no critical field change             │
      │       │       └── Show “You already have this” ──► END                │
      │       │                                                               │
      │       └── CHANGE DETECTED (wording / criticality / mandatory / type)    │
      │               │                                                       │
      │               ▼                                                       │
      │             Show UPDATE badge + side-by-side diff (showComplianceDiff) │
      │               │  get_compliance_change_detail()                       │
      │               ▼                                                       │
      │             User clicks “Update Compliance”                             │
      │               │  openUpdateComplianceModal → submitComplianceUpdate() │
      │               ▼                                                       │
      │             create_compliance_update_request() → status=pending       │
      │               │                                                       │
      │               ▼                                                       │
      │             Reviewer approves → apply_compliance_update()             │
      │               │  writes ComplianceHistory; sets AmendmentSource       │
      │               ▼                                                       │
      │             Existing Compliance row UPDATED in DB                     │
      │               │                                                       │
      │               ├── Phase 2: get_affected_risks() → notify_risk_owners()│
      │               └── Phase 3: get_affected_audits() → flag_audit_for_reaudit()
      │                                                                       │
      └───────────────────────────────────────────────────────────────────────┘
      │
      ▼
    END

═══════════════════════════════════════════════════════════════════════════════
                              END OF TO-BE WORKFLOW
═══════════════════════════════════════════════════════════════════════════════
```

```
═══════════════════════════════════════════════════════════════════════════════
  FRAMEWORK COMPARISON — AUTOMATIC PERIODIC CHECK (Phase 4)
  No user click required to discover new amendments
═══════════════════════════════════════════════════════════════════════════════

SCHEDULING
  Triggers (any one — mirror policy / compliance-audit self-heal pattern):
    (1) Celery/cron: schedule_framework_update_check() weekly
    (2) Management command (optional): run_framework_update_checks
    (3) POST /api/frameworks/auto-check-trigger/  (admin / scheduler secret)

CONFIG
  AUTO_CHECK_ENABLED, AUTO_CHECK_INTERVAL_DAYS (default 7), AUTO_CHECK_NOTIFICATION_EMAILS

───────────────────────────────────────────────────────────────────────────────
PART D — WEEKLY JOB
───────────────────────────────────────────────────────────────────────────────

    START (scheduled for_date = today)
      │
      ▼
    Query frameworks: Status=Approved, ActiveInactive=Active
      │
      ▼
    For EACH framework ─────────────────────────────────────────────────────┐
      │                                                                       │
      ▼                                                                       │
    should_check_framework(framework_id) ?                                    │
      │ last check older than AUTO_CHECK_INTERVAL_DAYS                        │
      │                                                                       │
      ├── NO ──► SKIP (too soon) ─────────────────────────────────────────────┤
      │                                                                       │
      YES                                                                     │
      ▼                                                                       │
    run_framework_update_check() → query_perplexity_api() / download          │
      │                                                                       │
      ▼                                                                       │
    New amendment found?                                                      │
      │                                                                       │
      ├── NO ──► Log “no update” ─────────────────────────────────────────────┤
      │                                                                       │
      YES                                                                     │
      ▼                                                                       │
    Save to Framework.Amendment + send_update_notification()                  │
      │  email + in-app bell badge for admins                                 │
      │                                                                       │
      └── User opens Framework Comparison later → PARTS A–C (manual analysis) ┘
      │
      ▼
    END RUN

═══════════════════════════════════════════════════════════════════════════════
                         END OF AUTOMATIC CHECK WORKFLOW
═══════════════════════════════════════════════════════════════════════════════
```

---

## 6. Detailed Function Specifications

### 6.1 Phase 1 Functions (Update Existing Rules)

#### `detect_control_changes()`
```
Purpose:    Detects if a matched compliance has material changes vs the amendment version
Input:      target_compliance (from amendment), origin_compliance (from database)
Output:     {
              "change_detected": true/false,
              "diff_fields": ["ComplianceItemDescription", "Criticality"],
              "old_values": { "ComplianceItemDescription": "old text...", "Criticality": "Medium" },
              "new_values": { "ComplianceItemDescription": "new text...", "Criticality": "High" },
              "similarity_score": 0.72
            }
Logic:      Compare text fields using SequenceMatcher + keyword overlap.
            If similarity < 0.85 OR criticality/mandatory/type changed, flag as changed.
```

#### `create_compliance_update_request()`
```
Purpose:    Creates an approval workflow record for updating an existing compliance
Input:      framework_id, compliance_id, proposed_changes (JSON), reviewer_id, requested_by_user_id
Output:     { "success": true, "update_request_id": 123 }
Database:   Inserts into ComplianceUpdateRequest table with status = "pending"
```

#### `apply_compliance_update()`
```
Purpose:    Applies approved changes to the actual Compliance record
Input:      update_request_id
Output:     { "success": true, "updated_compliance": { ... } }
Logic:      1. Validate request status = "approved"
            2. Update Compliance record with proposed_values
            3. Save old_values to ComplianceHistory
            4. Set request status = "applied"
            5. Trigger risk/audit notifications
```

### 6.2 Phase 2 Functions (Risk Integration)

#### `get_affected_risks()`
```
Purpose:    Finds risks in the Risk module linked to a specific compliance
Input:      framework_id, compliance_id
Output:     [
              { "RiskId": 1, "RiskName": "Data Breach", "Probability": "High", "Impact": "Critical" },
              { "RiskId": 5, "RiskName": "Unauthorized Access", "Probability": "Medium", "Impact": "High" }
            ]
Logic:      Query Risk table where ComplianceId = compliance_id OR linked_controls contains compliance_id
```

### 6.3 Phase 3 Functions (Audit Integration)

#### `get_affected_audits()`
```
Purpose:    Finds audits linked to a policy/sub-policy/compliance
Input:      framework_id, compliance_id (optional), policy_id (optional)
Output:     [
              { "AuditId": 10, "AuditName": "Q1 Access Control Audit", "Status": "Completed", "LastAuditDate": "2026-01-15" },
              { "AuditId": 12, "AuditName": "Q2 Compliance Review", "Status": "Scheduled", "LastAuditDate": null }
            ]
Logic:      Query Audit table where linked_framework_id/framework elements match
```

### 6.4 Phase 4 Functions (Automatic Checking)

#### `schedule_framework_update_check()`
```
Purpose:    Scheduled background task to check all frameworks for updates
Frequency:  Weekly (configurable via AUTO_CHECK_INTERVAL_DAYS)
Logic:      1. Query all frameworks where Status = 'Approved' AND ActiveInactive = 'Active'
            2. For each framework, call should_check_framework()
            3. If true, call run_framework_update_check()
            4. If new amendment found, call send_update_notification()
            5. Log all results
```

---

## 7. API Endpoints Needed

### New Endpoints to Add

| Method | Endpoint | Handler Function | Purpose |
|--------|----------|------------------|---------|
| POST | `/api/frameworks/{id}/compliances/{comp_id}/detect-changes/` | `detect_control_changes` | Compare old vs new compliance |
| POST | `/api/frameworks/{id}/compliances/{comp_id}/update-request/` | `create_compliance_update_request` | Create update approval request |
| POST | `/api/compliance-update-requests/{id}/approve/` | `apply_compliance_update` | Approve and apply update |
| POST | `/api/compliance-update-requests/{id}/reject/` | `reject_compliance_update` | Reject update request |
| GET | `/api/frameworks/{id}/compliance-update-requests/` | `get_pending_compliance_updates` | List pending update requests |
| GET | `/api/frameworks/{id}/compliances/{comp_id}/affected-risks/` | `get_affected_risks` | Get linked risks |
| GET | `/api/frameworks/{id}/compliances/{comp_id}/affected-audits/` | `get_affected_audits` | Get linked audits |
| GET | `/api/frameworks/{id}/impact-summary/` | `get_policy_impact_summary` | High-level impact summary |
| POST | `/api/frameworks/auto-check-trigger/` | `schedule_framework_update_check` | Manual trigger of auto-check |

---

## 8. Frontend UI Changes Needed

### 8.1 Matched Compliance Cards — Add "Update" State

Currently matched compliances show:
```
✅ Matched (You already have this)
```

Should show:
```
⚠️ MATCHED BUT CHANGED (Update Required)
   Old: Passwords must be 8 characters
   New: Passwords must be 12 characters with special symbols
   [View Diff] [Update Compliance]
```

### 8.2 New Modal: Compliance Update Modal

Similar to the existing "Add Compliance" modal, but pre-filled with:
- Current values (read-only)
- Proposed values (editable)
- Diff highlights showing what changed
- Reviewer dropdown
- Submit for Approval button

### 8.3 New Section: Impact Summary Card

Add a card at the top of the page showing:
```
┌─ Amendment Impact Summary ─────────────────┐
│ 3 Policies Affected                          │
│ 7 Sub-Policies Affected                      │
│ 12 Compliances: 4 New | 6 Changed | 2 Removed│
│ 4 Risk Entries Linked                        │
│ 2 Audits Require Re-audit                    │
└────────────────────────────────────────────┘
```

### 8.4 New Expandable Sections

When expanding a matched/changed compliance:
- Show linked Risks (if any)
- Show linked Audits (if any)
- Show change history (if previously updated)

---

## 9. Database Schema Changes

### New Table: `ComplianceUpdateRequest`

| Column | Type | Description |
|--------|------|-------------|
| `id` | AutoField (PK) | Unique ID |
| `framework_id` | ForeignKey → Framework | Which framework |
| `compliance_id` | ForeignKey → Compliance | Which compliance to update |
| `old_values` | JSONField | Snapshot of current values before change |
| `proposed_values` | JSONField | New values from amendment |
| `reviewer_id` | ForeignKey → Users | Who must approve |
| `requested_by_id` | ForeignKey → Users | Who initiated the update |
| `status` | CharField | `pending` / `approved` / `rejected` / `applied` |
| `rejection_reason` | TextField | Why rejected (if applicable) |
| `created_at` | DateTimeField | When request created |
| `updated_at` | DateTimeField | When last updated |
| `applied_at` | DateTimeField | When changes were applied |

### Modified Table: `Compliance`

| Column | Type | Description |
|--------|------|-------------|
| `ComplianceHistory` | JSONField (new) | Array of previous versions |
| `AmendmentSource` | CharField (new) | Which amendment introduced/last updated this |
| `LastAmendmentDate` | DateField (new) | Date of last amendment update |

---

## 10. Implementation Priority & Timeline Estimate

| Phase | Feature | Complexity | Estimated Effort | Priority |
|-------|---------|-----------|------------------|----------|
| 1 | Update existing compliances (backend) | Medium | 5–7 days | 🔴 Critical |
| 1 | Update existing compliances (frontend) | Medium | 4–5 days | 🔴 Critical |
| 1 | ComplianceUpdateRequest table | Low | 1–2 days | 🔴 Critical |
| 2 | Risk module integration | Medium | 3–4 days | 🟠 High |
| 3 | Audit module integration | Medium | 3–4 days | 🟠 High |
| 4 | Automatic periodic checking | Medium | 3–4 days | 🟡 Medium |
| 5 | Policy-level impact summary | Low | 2–3 days | 🟡 Medium |
| — | Testing & QA | — | 5–7 days | Required |

**Total Estimated Effort: 4–6 weeks** (with 1–2 developers)

---

## 11. Testing Checklist

| Test Case | Expected Result |
|-----------|----------------|
| Amendment changes an existing compliance wording | System shows "Changed" badge with diff |
| User clicks Update on changed compliance | Update modal opens with old vs new |
| User submits update with reviewer | Record created in ComplianceUpdateRequest, status = pending |
| Reviewer approves update | Compliance record updated, history saved, status = applied |
| Reviewer rejects update | Status = rejected, compliance unchanged, user notified |
| Compliance is linked to 2 risks | Both risks shown in expanded view |
| Compliance is linked to 1 audit | Audit shown, flag for re-audit available |
| Cron runs on Monday 9 AM | All frameworks checked, notifications sent if amendments found |
| Amendment has 3 policies | Impact summary shows "3 Policies Affected" |

---

## 12. Files to Modify

| File | Changes |
|------|---------|
| `grc/routes/changemanagement/framework_comparison.py` | Add new API endpoints and functions for Phases 1–5 |
| `grc/routes/changemanagement/similarity_matcher.py` | Add change detection logic to matching results |
| `grc_frontend/vue/FrameworkComparisonUpdated.vue` | Add new UI components, modals, and sections |
| `grc_frontend/src/services/frameworkComparisonService.js` | Add new API service methods |
| `grc/models.py` (or models folder) | Add ComplianceUpdateRequest model, modify Compliance model |
| `grc/routes/Risk/risk_views.py` (or similar) | Add helper endpoints for risk lookups |
| `grc/routes/Audit/audit_views.py` (or similar) | Add helper endpoints for audit lookups |
| New: `grc/routes/changemanagement/tasks.py` | Add Celery/scheduled task for automatic checking |
| New: `grc/routes/changemanagement/risk_integration.py` | Risk integration logic |
| New: `grc/routes/changemanagement/audit_integration.py` | Audit integration logic |

---

*End of Document*
