# Organizational Controls Mapping – What It Does, Purpose, and Code Map

## 1. What It Does

**Organizational Controls Mapping** lets compliance teams:

1. **Pick a framework** (e.g. PCI DSS, NIST) and see its structure: **Policies → Sub-Policies → Compliances** (framework requirements/controls).
2. **For each compliance (control)**, attach what the organization actually does:
   - **Manual:** Type “control text” (how you meet the requirement).
   - **Documents:** Upload PDF/DOCX/TXT; text is extracted and stored as “organizational control” content.
3. **Run an AI audit** that compares:
   - **Framework requirement:** title, description, identifier, criticality.
   - **Organizational control:** your text (manual + extracted from docs).
   - AI returns: **mapping status** (fully_mapped / partially_mapped / not_mapped), **confidence**, and **what is satisfying / what is left / why not mapped**.
4. **View results** in the UI: status dots, confidence, and AI analysis text per control. You can upload at **compliance**, **sub-policy**, **policy**, or **whole-framework** level (including bulk).

So: **map your real controls to framework requirements and get AI-backed coverage/gap analysis.**

---

## 2. Purpose

- **Assess coverage:** See which framework requirements are fully, partially, or not met by your controls.
- **Reduce manual review:** AI summarizes “what satisfies,” “what’s missing,” “why not mapped.”
- **Evidence in one place:** Attach policy/procedure docs to controls; text is extracted and used for the audit.
- **Bulk and scope:** Upload one document to many compliances (e.g. one policy doc for a whole policy or framework) and run audit at compliance / sub-policy / policy / framework level.

---

## 3. Backend Code – File and Functions

**File:** `grc_backend/grc/routes/Compliance/organizational_controls.py`

### Helper (no HTTP)

| Function | Purpose |
|----------|--------|
| `extract_text_from_document(file_path, file_extension)` | Extracts text from `.txt`, `.pdf` (PyPDF2), `.docx` (python-docx). Used when uploading documents so AI can analyze content. |
| `table_exists(cursor, table_name)` | Checks if `organizational_controls` table exists (used to decide whether to join org-control data in queries). |

### API View Functions (how they are called)

| Function | HTTP | URL (pattern) | Purpose |
|----------|------|----------------|--------|
| `get_framework_controls` | GET | `/api/organizational-controls/framework/<framework_id>/` | Returns full hierarchy for one framework: policies → subpolicies → compliances, with org-control fields (MappingStatus, ControlText, DocumentName, AIAnalysis, ConfidenceScore, etc.) when the table exists. |
| `get_organizational_control` | GET | `/api/organizational-controls/compliance/<compliance_id>/` | Returns one org control for a compliance (ControlText, ExtractedText, MappingStatus, AIAnalysis, Documents list, etc.). |
| `save_organizational_control` | POST | `/api/organizational-controls/save/` | Creates or updates org control for a compliance. Body: `compliance_id`, `control_text`, optional `framework_id`. Sets MappingStatus to `not_audited`. |
| `upload_organizational_document` | POST | `/api/organizational-controls/upload/` | Uploads one or more files; links them to compliance(s). Form: `files`, `framework_id`, `compliance_id` or `compliance_ids`, `upload_type` (single/policy/subpolicy/bulk), optional `policy_id`, `subpolicy_id`. Extracts text, creates/updates OrganizationalControl and OrganizationalControlDocument, concatenates ExtractedText. |
| `run_control_mapping_audit` | POST | `/api/organizational-controls/run-audit/` | Runs AI mapping audit. Body: one of `compliance_id`, `policy_id`, `subpolicy_id`, `org_control_ids`, or `framework_id` + `audit_all=true`. For each org control with content, builds prompt (framework requirement + org content truncated to 5000 chars), calls `call_ai_api`, parses JSON, saves MappingStatus, ConfidenceScore, AIAnalysis, LastAuditedAt. Returns summary and per-control results. |
| `delete_organizational_control` | DELETE | `/api/organizational-controls/delete/<org_control_id>/` | Deletes one org control and its document records (and files on disk). |
| `get_mapping_statistics` | GET | `/api/organizational-controls/statistics/<framework_id>/` | Returns counts for one framework: total compliances, with/without org controls, fully_mapped, partially_mapped, not_mapped, not_audited, coverage_percentage. |
| `get_frameworks_with_org_stats` | GET | `/api/organizational-controls/frameworks-with-stats/` | Returns list of frameworks with aggregate org-control stats (total compliances, with_org_controls, fully_mapped, etc., coverage). |

**Authentication:** All use `CsrfExemptSessionAuthentication`, `BasicAuthentication`; multi-tenant via `@require_tenant` and `@tenant_filter`.

**AI:** Only `run_control_mapping_audit` calls AI. It uses the **centralized AI service** `get_ai_service().generate_json(task_name="compliance.control_mapping_audit", prompt=prompt)` from `grc/ai/service.py`, so it gets context budgeting, cache, model router, and compliance system prompt. No dependency on `grc/routes/Audit/ai_audit_api.py`.

---

## 4. Frontend Code – File and How It Calls the Backend

**File:** `grc_frontend/src/components/Compliance/OrganizationalControls.vue`  
**Route:** `/compliance/organizational-controls` (name: `OrganizationalControls`).

### UI Layout (three panels)

- **Left:** Framework selector → tree (Framework → Policies → Sub-Policies → Compliances). Search, expand/collapse, upload buttons per node.
- **Middle:** Selected compliance details; manual control text; “Save,” “Save & Run AI Audit”; document list and upload.
- **Right:** AI analysis result (what is satisfying, what is left, why not mapped) and confidence.

### Main methods that call the backend

| Frontend method | Backend API called | When |
|-----------------|--------------------|------|
| `loadFrameworks()` | `GET /api/all-policies/frameworks/` (not org-controls) | `mounted()` – populates framework dropdown. |
| `loadFrameworkControls()` | `GET .../organizational-controls/framework/<id>/` and `GET .../organizational-controls/statistics/<id>/` (parallel) | User selects a framework. |
| `selectControl(compliance, subpolicy, policy)` | — | User clicks a compliance in the tree; loads its documents from already-fetched data. |
| `saveControl()` | `POST .../organizational-controls/upload/` (if file) then `POST .../organizational-controls/save/` | User saves manual text (and optional file) for selected compliance. |
| `saveAndAudit()` | Same upload/save, then `POST .../organizational-controls/run-audit/` with `compliance_id` | Save then run AI audit for that compliance. |
| `runSingleAudit(compliance)` | `POST .../organizational-controls/run-audit/` with `compliance_id` | Run AI audit for one compliance. |
| `runAIAudit()` | `POST .../organizational-controls/save/` then `POST .../organizational-controls/run-audit/` with `compliance_id` | Save text then audit (middle panel). |
| `runAIAuditAfterUpload()` | `POST .../organizational-controls/run-audit/` with `policy_id` or `subpolicy_id` or `compliance_id` (from upload target) | After upload modal; runs audit for the scope that was uploaded. |
| `runBulkAudit()` | `POST .../organizational-controls/run-audit/` with `audit_all: true` and `framework_id` (or policy/subpolicy) | Bulk audit from modal. |
| `uploadBulkDocument()` | `POST .../organizational-controls/upload/` with bulk/policy/subpolicy and selected IDs | Bulk upload modal submit. |
| `processUpload()` | `POST .../organizational-controls/upload/` with `upload_type`, `upload_mode`, target (policy/subpolicy/compliance/framework) and files | Upload-interface modal (single/multiple/bulk). |

Other methods are UI/state only (toggle, search, clear, format, toast, etc.) and do not call the org-controls API.

---

## 5. Data Models (Backend)

- **OrganizationalControl** (table `organizational_controls`): Links Framework, Policy, SubPolicy, Compliance; stores `ControlText`, `ExtractedText`, `MappingStatus`, `AIAnalysis` (JSON), `ConfidenceScore`, `LastAuditedAt`, `BulkUploadId`, etc.
- **OrganizationalControlDocument** (table `organizational_documents`): Per-file record for an org control; `DocumentPath`, `ExtractedText`, `IsPrimary`, etc.

Framework/Policy/SubPolicy/Compliance come from existing GRC models.

---

## 6. Call Flow Summary

1. User opens **Organizational Controls** → `mounted()` → `loadFrameworks()`.
2. User selects framework → `loadFrameworkControls()` → **get_framework_controls** + **get_mapping_statistics**.
3. User selects a compliance in tree → `selectControl()` (no API; uses loaded tree data).
4. User enters text and/or uploads file and clicks Save → `saveControl()` → **upload_organizational_document** (if file) + **save_organizational_control**.
5. User clicks “Run AI Audit” (single or bulk) → `runSingleAudit` / `runAIAudit` / `runAIAuditAfterUpload` / `runBulkAudit` → **run_control_mapping_audit**.
6. Backend in **run_control_mapping_audit**: for each org control with content, build prompt, call **call_ai_api**, parse JSON, save MappingStatus/AIAnalysis/ConfidenceScore; return summary + results.
7. Frontend refreshes or reselects so the right panel shows AI analysis from the updated control data (from tree/selection state or a refetch of framework controls).

This is the full picture of what the feature does, why it exists, and which functions are used and how they are called.

---

## 7. AI Functions Used and Which Requirement They Serve

In **Organizational Controls Mapping** only **one** AI entry point is used. There is no centralized `grc/ai` service here—only the local audit AI.

| AI function (as used) | Where it lives | Requirement it serves | Input | Output |
|------------------------|----------------|------------------------|--------|--------|
| **get_ai_service().generate_json**(task_name="compliance.control_mapping_audit", prompt=prompt) | `grc/ai/service.py` (centralized) | **Control mapping audit:** Decide whether the organization’s control (your text or text from uploaded docs) **fully maps**, **partially maps**, or **does not map** to the framework compliance requirement, and explain what satisfies, what’s missing, and why not mapped. | **Prompt:** (1) Framework requirement: title, description, identifier, criticality, mandatory/optional. (2) Organizational control content (capped at 5000 chars in route). Centralized service applies context budgeting and optimization. | **Expected JSON:** `mapping_status`, `confidence_score`, `what_is_satisfying`, `what_is_left`, `why_not_mapped`, `detailed_analysis`. |

**Where it’s called:**  
`run_control_mapping_audit()` in `organizational_controls.py` builds the prompt, calls `get_ai_service().generate_json(task_name=CONTROL_MAPPING_AUDIT_TASK, prompt=prompt)`, then saves `MappingStatus`, `ConfidenceScore`, and `AIAnalysis` on the `OrganizationalControl` record.

**Centralized AI behaviour:**  
- **Prompts:** `grc/ai/prompts/__init__.py` defines system prompt for `compliance.*` tasks.  
- **Config:** `grc/ai/config.py` has `compliance.control_mapping_audit` in `task_sampling_profiles` (temperature, etc.).  
- **Service:** Context window, prompt optimization, model router, cache (TTL), and provider (Ollama/OpenAI) selection are all in `grc/ai/service.py`.  

So: **one AI function, one requirement**—control mapping audit, now via centralized AI. Text extraction from PDF/DOCX remains non-AI (PyPDF2 / python-docx).
