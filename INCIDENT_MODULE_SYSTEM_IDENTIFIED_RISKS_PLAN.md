# Incident Module: System Identified Risks (Implementation Plan)

## What I understand from your image

The workflow in the image describes a cross-module AI pipeline that continuously monitors multiple sources, identifies likely risks, and routes them through a human review and approval process before adding them to the Risk Register.

## Image analysis (step-by-step)

1. **Step 1 - Data sources (continuous monitoring)**
   - Audit findings
   - Incident module
   - Compliance controls
   - TPRM/vendor data
   - External integrations
   - Events/manual

2. **Step 2 - AI risk identification engine**
   - A centralized engine analyzes patterns and correlations across modules.
   - It predicts emerging risks.

3. **Step 3 - Risk type classification/routing**
   - Routes into categories like:
     - Operational
     - IT/Security
     - Compliance
     - Third-party
     - Emerging

4. **Step 4 - "System Identified Risks" staging queue (new tool)**
   - This is a **pre-risk queue**, not yet in official Risk Register.
   - Queue records include fields like:
     - Title
     - Type
     - Category
     - Likelihood
     - Impact
     - Mitigation
     - Source links
     - Confidence score

5. **Step 5 - Human review decision**
   - **Accept** -> continue to scoring/completion
   - **Modify & Resubmit** -> update details, remain in queue/stateful workflow
   - **Reject** -> log reason and feed back to AI quality loop

6. **Step 6 - Risk scoring and detail completion**
   - AI helps suggest likelihood, impact, exposure, mitigation steps.
   - Reviewer finalizes details.

7. **Step 7 - Approval workflow**
   - Existing reviewer/approver flow:
   - Assign -> review -> approve/reject

8. **Step 8 - Formal add to Risk Register**
   - Final accepted + approved item is logged as official risk.
   - Track origin as `AI Identified` and keep source linkage.

---

## Why this is a good fit for your current system

You already have core building blocks:

- **Frontend**
  - `grc_frontend/src/components/Incident/incident_ai_import.vue`
  - `grc_frontend/src/components/Risk/risk_ai.vue`
  - Existing Risk sidebar/routing already supports AI pages.
- **Backend**
  - `grc_backend/grc/routes/Incident/incident_ai_import.py`
  - Incident AI endpoints in `grc_backend/grc/urls.py`:
    - `/api/ai-incident-upload/`
    - `/api/ai-incident-save/`
    - `/api/ai-incident-test/`
  - Existing centralized AI service integration (`get_ai_service`, AI tasks).

So this feature is mostly an **orchestration + staging queue + review workflow** problem, not a from-scratch AI problem.

---

## Start with Incident module first (recommended scope)

### MVP objective
Use **Incident data as the first source** to generate system-identified risks and send them through a dedicated review queue before creating Risk Register entries.

---

## Proposed architecture (Incident-first)

## 1) Backend components

### A. New staging table
Create a staging model/table (example name):

- `SystemIdentifiedRiskQueue`

Suggested fields:

- `id`
- `tenant_id`
- `source_module` (`INCIDENT`)
- `source_record_id` (incident id)
- `source_ref` (human-readable source, e.g. incident code/title)
- `risk_title`
- `risk_type`
- `category`
- `criticality`
- `risk_description`
- `possible_damage`
- `business_impact` (JSON array)
- `likelihood` (1-10)
- `impact` (1-10)
- `exposure_rating` (computed)
- `priority`
- `mitigation_steps` (JSON array)
- `ai_reasoning`
- `confidence_score` (0-100)
- `status` (`PENDING_REVIEW`, `DRAFT`, `ACCEPTED_PENDING_APPROVAL`, `REJECTED`, `APPROVED_ADDED`)
- `review_notes`
- `rejection_reason`
- `reviewed_by`
- `reviewed_at`
- `approved_by`
- `approved_at`
- `created_at`
- `updated_at`

### B. AI generation service for Incident -> Risk candidates

Create a service function:

- `generate_risk_candidates_from_incident(incident) -> [queue_records]`

Use your centralized AI task mechanism (similar to existing incident/risk tasks):

- Add task like: `incident.identify_risks`

This task should return:

- normalized risk candidate(s)
- per-field confidence
- rationale

### C. API endpoints (new)

Suggested endpoints:

- `POST /api/system-identified-risks/run-scan/incident/`
  - pulls eligible incidents, runs AI candidate generation
  - writes to staging queue (dedupe-safe)
- `GET /api/system-identified-risks/`
  - list queue with filters (status/source/category/confidence)
- `GET /api/system-identified-risks/<id>/`
  - get full details for review modal
- `PUT /api/system-identified-risks/<id>/review/`
  - save edits / draft
- `POST /api/system-identified-risks/<id>/accept/`
  - move to `ACCEPTED_PENDING_APPROVAL`
- `POST /api/system-identified-risks/<id>/reject/`
  - require reason, mark rejected, feedback data for AI quality tracking
- `POST /api/system-identified-risks/<id>/create-risk/`
  - convert queue item to official Risk Register record
  - link to workflow/approval process

### D. Deduplication logic

Prevent spam duplicates by:

- source-based dedupe key:
  - `tenant_id + source_module + source_record_id + normalized_title_hash`
- time window dedupe:
  - do not create same candidate within N days unless severity changed

### E. Audit trail

Log every decision:

- accepted by who
- rejected why
- what fields were changed from AI draft
- when converted to risk register

---

## 2) Frontend components

You already created the first UI shell in Risk. For Incident-first delivery:

### A. Queue page

Use your new page as base:

- `SystemIdentifiedRisks.vue`

Enhance with live backend integration:

- load counts from API
- load queue records from API
- filter by source = `Incident` initially

### B. Review modal

Keep split panel:

- left = AI draft (read-only)
- right = editable review form

Hook buttons to real API actions:

- `Accept & Send for Approval`
- `Save as Draft`
- `Reject` (reason mandatory)

### C. Incident module entry point

Add trigger button in Incident area:

- `"Run AI Risk Scan"`

This should call:

- `POST /api/system-identified-risks/run-scan/incident/`

---

## 3) Workflow mapping for Incident-first rollout

### Phase 1 (MVP)

- Scan Incident records
- Create queue entries
- Review + accept/reject UI
- Manual convert accepted entry -> Risk Register

### Phase 2

- Integrate existing approval workflow
- Automated transition:
  - accepted -> approval -> add to Risk Register

### Phase 3

- Add more sources:
  - Audit findings
  - Compliance controls
  - TPRM
  - Integrations
  - Events/manual

### Phase 4

- AI quality feedback loop:
  - rejected reasons become training/evaluation signal
  - confidence calibration dashboards

---

## Backend implementation checklist

- [ ] Add `SystemIdentifiedRiskQueue` model + migration
- [ ] Add serializer(s)
- [ ] Add service for Incident -> risk candidate generation
- [ ] Add new AI task (`incident.identify_risks`)
- [ ] Add queue APIs (list/detail/review/accept/reject/create-risk)
- [ ] Add permissions + tenant isolation checks
- [ ] Add dedupe rules
- [ ] Add audit logs
- [ ] Add unit/integration tests

## Frontend implementation checklist

- [ ] Connect queue page to real APIs
- [ ] Add API constants in `grc_frontend/src/config/api.js`
- [ ] Implement list filters + pagination
- [ ] Implement review modal save/accept/reject calls
- [ ] Add loading states + error handling
- [ ] Add Run Scan action in Incident module
- [ ] Add toasts + optimistic refresh

---

## Data and security considerations

- Respect tenant isolation in every query and write.
- Sanitize AI output before persistence.
- Validate enum/choice fields server-side.
- Keep source links immutable for traceability.
- Require reject reason for governance quality.

---

## What I think is the best way to do this

1. **Do Incident-only MVP first** (small blast radius, faster validation).
2. Build **staging queue as the core abstraction**.
3. Reuse your current AI framework and existing UI patterns.
4. Add strict state transitions to avoid ambiguous records.
5. Expand source adapters one by one after MVP is stable.

---

## Suggested next immediate task (practical)

Start with backend first:

1. Create queue model + migration.
2. Add `run-scan/incident` endpoint that creates placeholder candidates from existing incidents (even before full AI quality is perfect).
3. Connect current `SystemIdentifiedRisks.vue` list to that endpoint.

This gives you an end-to-end working pipeline quickly, then improve AI quality iteratively.

