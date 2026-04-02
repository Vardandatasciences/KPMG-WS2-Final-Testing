# TPRM vendor risk assessment — implementation plan (from product discussion, 30 Mar 2026)

This document translates the agreed scope from the stakeholder discussion into a **detailed implementation plan** aligned with the existing `grc_backend/tprm_backend` and `grc_frontend/tprm_frontend` codebases.

---

## 1. Business scope (summary)

| Theme | Requirement |
|--------|-------------|
| **Assessment types** | Inherent risk (profile + external signals), residual risk (after controls), continuous / periodic monitoring. |
| **Onboarding** | First-time risk from **external screening** + **questionnaire**; scored risks; traceable to source. |
| **Periodic assessment** | Recurring external checks (e.g. weekly/monthly) and recurring questionnaires (e.g. quarterly). **Each new data batch** should drive **risk identification/scoring**, not only the first run. |
| **Continuous / proactive** | Additional connectors (e.g. news/GIS-style feeds) with **org-defined frequency**, weaker structured signals → need mapping to vendor impact. |
| **Multi-module TPRM** | Over time: BCP/DRP, SLA, contract audits/testing feed the same risk model; **do not double-count** the same underlying evidence across runs. |
| **Risk handling** | Mitigation workflow (assign → act → evidence → review → close); **score adjusts** after remediation and when new observations increase/decrease exposure. |
| **Deduplication** | Same audit/finding must not be consumed twice in generation; **semantic dedupe** when AI emits near-duplicate risk wordings → update existing risk vs create new. |
| **Architecture** | Prefer **TPRM-local** risk handling (or extracted GRC “microservice” patterns) vs forcing full GRC schema; confirm with Susheel for **TPRM-only** packaging for trials. |

---

## 2. Current implementation (as-built)

### 2.1 Backend — vendor risk generation

| Area | Location | Behaviour |
|------|----------|-----------|
| **Service API** | `risk_analysis_vendor/services.py` — `RiskAnalysisService` | `analyze_entity_data_row(entity, table, row_id)` loads row via `EntityDataService`, calls `LlamaService`, returns normalized risk payloads. |
| **Vendor save path** | Same file — `generate_vendor_risks(approval_id)` | Reads `approval_requests.request_data`, resolves `vendor_id`, calls `analyze_entity_data_row('vendor_management', 'temp_vendor', vendor_id)` or `_create_basic_vendor_risks` on LLM failure; **persists** via `Risk.objects.create(...)` → table **`risk_tprm`**. |
| **Async trigger** | `generate_vendor_risks_async` + `risk_analysis_vendor/threading_service.py` | Non-blocking generation after approval. |
| **Model** | `risk_analysis_vendor/models.py` — `Risk` | Maps to `risk_tprm`; fields include `entity`, `data`, `row`, scores, `suggested_mitigations`, `status`, `assigned_to`, etc. **No structured fields today for source type, source record id, ingestion batch, or fingerprint.** |
| **Approval hook** | `apps/vendor_approval/views.py` — `requester_final_decision` | On `response_approval`, imports `RiskAnalysisService` and calls `generate_vendor_risks_async(approval_id)`. |

### 2.2 Backend — periodic external screening

- **Scheduling**: `apps/management/models.py` — `ScreeningSchedule` (referenced from `apps/management/views.py`).
- **CRUD API**: `management/vendors/<vendor_code>/screening-schedules/` (see `apps/management/views.py` — `ScreeningScheduleListCreateView` / `ScreeningScheduleDetailView`).
- **Execution**: `apps/management/apps.py` — daemon thread `_run_due_schedules()` every ~60s; calls `TempVendorManagementViewSet()._perform_automatic_screening(vendor)` then advances `next_run_at`.
- **Gap vs requirement**: Screening refresh **does not** invoke `RiskAnalysisService` or a “delta risk” pipeline. New matches are **not** automatically turned into/merged with `risk_tprm` rows.

### 2.3 Backend — generic module risk (BCP/DRP, etc.)

- **Package**: `risk_analysis/` (separate from `risk_analysis_vendor` but same entity-row pattern).
- **Integration doc**: `risk_analysis/INTEGRATION_GUIDE.md`.
- **Example usage**: `bcpdrp/views.py` imports `tprm_backend.risk_analysis.services.RiskAnalysisService` for plan analysis.
- **Gap**: Vendor periodic flow should **reuse one orchestration pattern** (single “risk ingestion” layer) so BCP/SLA/contract findings and vendor screening/questionnaires all write with **consistent provenance and dedupe rules**.

### 2.4 Frontend

| Area | Location | Behaviour |
|------|----------|-----------|
| **Screening schedules UI** | `tprm_frontend/src/pages/vendor/VendorExternalScreening.vue` | Calls `management/vendors/.../screening-schedules/` APIs. |
| **Cross-module risk dashboard** | `tprm_frontend/src/pages/BCP/RiskAnalytics.vue` | Uses `/risk-analysis/dashboard/`, `/risk-analysis/risks/` (generic **risk_analysis** app URLs). |
| **Vendor risk API helper** | `tprm_frontend/src/services/vendorApi.js` | `risk-analysis-vendor/analyze/`, `history/` endpoints. |
| **Gap** | — | No end-to-end UX for **risk provenance** (which screening run / questionnaire version / audit id), **mitigation workflow** aligned to transcript, or **score history** after periodic reruns. |

---

## 3. Gap analysis (requirements → code)

| Requirement | Current state | Gap |
|-------------|---------------|-----|
| Risk on **first** questionnaire + screening | Hook on questionnaire approval + entity analysis | Verify E2E in target environment (LLM/Ollama, DB routing); harden logging. |
| Risk on **periodic** screening | Screening runs on schedule | **Add post-screening hook**: new/changed escalated matches → ingestion pipeline → create/update `risk_tprm`. |
| Risk on **periodic** questionnaire | Partial (scheduling exists in questionnaire app) | Ensure reassessment completion triggers **same** ingestion as onboarding (with batch id). |
| **Source attribution** | Risks lack explicit source | Extend model/API: source_type, source_id, external_ref, run_id, human-readable summary, optional URL. |
| **No double-counting** | Not implemented | Store **content fingerprints** (hash of audit finding id, screening match id, questionnaire answer snapshot id) and skip if already linked to a risk revision. |
| **Semantic dedupe** | Not implemented | On create: embed/compare titles+descriptions (LLM or embedding API); merge into existing risk + bump observation count / score per policy. |
| **Residual + mitigation** | `suggested_mitigations` text only | Workflow: tasks, owners, evidence attachments, states; recalculate **residual** score when mitigations verified. |
| **Continuous news-like feeds** | Not in codebase | New connector abstraction + cron/beat + prompt/rules to relate broad events to vendor categories/geography (future phase; design hooks now). |
| **TPRM-only product** | GRC+TPRM monorepo | Feature flags / route pruning / Susheel decision — **process**, not only code. |

---

## 4. Detailed implementation plan

Work is sequenced for a **3–4 day sprint** as discussed, then iterative hardening.

### Phase A — Stabilize first-time path (Day 1)

**A1. E2E verification**

- Trace: questionnaire approval → `generate_vendor_risks_async` → `risk_tprm` rows for a real tenant.
- Confirm DB alias (`tprm` vs `default`) matches deployment; fix any connection mismatches.
- Validate Ollama/`OLLAMA_URL` / `LLAMA_MODEL_NAME` in `vendor_guard_hub/settings.py` (and env).

**A2. Observability**

- Structured logs: `approval_id`, `vendor_id`, risk ids created, duration, LLM fallback used or not.
- Optional: persist last run status on vendor or approval (for UI “generation failed” banner).

**Files (primary):**  
`risk_analysis_vendor/services.py`, `risk_analysis_vendor/threading_service.py`, `apps/vendor_approval/views.py`, `risk_analysis_vendor/llama_service.py`

---

### Phase B — Periodic screening → risk ingestion (Day 1–2)

**B1. Hook after automatic screening**

- In `apps/management/apps.py` — after successful `_perform_automatic_screening(vendor)`, call a new **thin orchestrator** (e.g. `risk_analysis_vendor/ingestion.py` — `ingest_vendor_screening_delta(vendor_id, schedule_id, run_timestamp)`).
- Orchestrator responsibilities:
  - Query **new or updated** `screening_matches` / `external_screening_results` since last processed watermark (per vendor or per schedule).
  - Build a compact payload for LLM or rule engine (escalated matches, scores, categories).
  - Call existing `analyze_entity_data_row` **or** a specialized method that takes “screening_delta” JSON to avoid re-analyzing whole vendor profile blindly.

**B2. Watermark / dedupe store**

- New table e.g. `risk_ingestion_checkpoint` (vendor_id, source_type=`screening`, source_cursor or last_match_id, last_processed_at) **or** reuse match ids in a join table `risk_tprm_source_refs` (risk_id, ref_type, ref_id, created_at).

**Files (primary):**  
`apps/management/apps.py`, `apps/management/views.py` (`TempVendorManagementViewSet._perform_automatic_screening` if better to hook there), new `risk_analysis_vendor/ingestion.py`, migrations under `risk_analysis_vendor` or `management`.

---

### Phase C — Periodic questionnaire → risk (Day 2)

**C1. Identify reassessment completion event**

- In `apps/vendor_questionnaire/views.py` (and any approval flow), mirror the `response_approval` branch: on **scheduled** reassessment approval, call the **same** orchestrator with `source_type=questionnaire` and `approval_id` / response ids.

**C2. Unified ingestion entrypoint**

- `ingest_risk_event(event_type, vendor_id, payload, tenant_id)` used by:
  - onboarding approval (existing),
  - periodic screening (B),
  - periodic questionnaire (C),
  - later: SLA/BCP/contract (Phase F).

**Files (primary):**  
`apps/vendor_questionnaire/views.py`, `apps/vendor_approval/views.py`, `risk_analysis_vendor/ingestion.py`

---

### Phase D — Provenance, dedupe, score updates (Day 2–3)

**D1. Schema extension**

- Add to `risk_tprm` (via `Risk` model migration): e.g. `source_type`, `source_ref` (JSON or varchar), `ingestion_run_id`, `duplicate_of_id` (nullable), `observation_count`, `last_source_at`, optional `score_residual`.
- Add `risk_tprm_source_refs` many-to-many style table for **multiple evidence rows per risk**.

**D2. Create vs update logic**

- **New evidence keys**: if fingerprint exists in `risk_tprm_source_refs`, skip **or** attach to existing risk and increment `observation_count`, adjust likelihood per agreed rule (config table or constants).
- **Semantic match**: optional Celery task `dedupe_risks_for_vendor(vendor_id)` using LLM “same risk Y/N” or embeddings; merge if yes.

**D3. Score rules**

- Document formula version in DB or settings; transcript allows approximate formulae but requires **monotonic** behaviour: more repeated incidents → score tendency up; closed mitigations → residual down.

**Files (primary):**  
`risk_analysis_vendor/models.py`, migrations, `risk_analysis_vendor/services.py`, new `risk_analysis_vendor/dedupe.py`

---

### Phase E — Mitigation / handling workflow (Day 3–4)

**E1. Minimum viable workflow (TPRM-local)**

- States: `Open` → `In Progress` → `Pending Review` → `Closed` (reuse/extend `status` on `Risk`).
- APIs: assign user, add mitigation steps, upload evidence (reuse existing file patterns from RFP/contracts if available), reviewer sign-off.
- On `Closed`, apply **residual score** update and write audit log row.

**E2. Frontend**

- Vendor risk detail drawer/page: show **sources**, mitigation timeline, assignee.
- Reuse patterns from GRC if visuals exist in main `grc_frontend`; otherwise new views under `tprm_frontend/src/pages/vendor/`.

**E3. Longer-term**

- If product chooses **deep GRC integration**, map `risk_tprm.id` → GRC risk register id via bridge table; **only after** Susheel confirms schema impact for TPRM-only customers.

**Files (primary):**  
`risk_analysis_vendor/views.py`, serializers, new Vue screens, router entries in `tprm_frontend/src/router/index.js`

---

### Phase F — Other modules (incremental, post-sprint)

- **BCP/DRP**: Already calls `risk_analysis.RiskAnalysisService` — add calls to shared `ingest_risk_event` with `entity` labels and finding ids (from `bcpdrp/views.py`).
- **SLA / contracts**: Use existing triggers (e.g. `contractsApi.js` — `trigger-contract-risk-analysis`) to enqueue ingestion with **contract_audit_finding_id** fingerprints.
- **News / external broad feeds**: New `Connector` config table, Celery beat job, prompt templates; vendor-scope vs tenant-scope flags (deferred detail per transcript).

---

## 5. Testing checklist (acceptance)

1. **Onboarding**: Approve questionnaire → N risks in `risk_tprm` with correct `vendor_id` (`row`) and tenant isolation.
2. **Periodic screening**: Force due schedule (or `run_due_screening_schedules` command) → new match → **new or updated** risk; second run with **same** match → **no duplicate** risk (or merged observation).
3. **Periodic questionnaire**: Second assessment → ingestion fires; score/provenance updates.
4. **Dedupe**: Two AI wordings same meaning → one risk or linked duplicate with score update policy.
5. **Mitigation**: Close mitigation → residual score lower than inherent; audit trail present.
6. **Frontend**: Screening schedule UI still works; vendor risk view shows sources and status.

---

## 6. Open decisions (explicit)

| Decision | Options | Owner |
|----------|---------|--------|
| GRC vs TPRM workflow | TPRM-local MVP vs redirect to GRC risk module vs shared microservice | Susheel + eng |
| LLM provider | Ollama (current) vs centralized API | Infra |
| Semantic dedupe | On-write vs nightly batch | Product + eng |
| TPRM-only build | Feature flags vs separate branch vs route hiding | Susheel |

---

## 7. Key file index (quick navigation)

| Concern | Path |
|---------|------|
| Vendor risk service | `grc_backend/tprm_backend/risk_analysis_vendor/services.py` |
| Risk ORM | `grc_backend/tprm_backend/risk_analysis_vendor/models.py` |
| Questionnaire approval hook | `grc_backend/tprm_backend/apps/vendor_approval/views.py` |
| Screening scheduler | `grc_backend/tprm_backend/apps/management/apps.py` |
| Screening schedule API | `grc_backend/tprm_backend/apps/management/views.py` |
| Generic risk module | `grc_backend/tprm_backend/risk_analysis/` |
| Screening UI | `grc_frontend/tprm_frontend/src/pages/vendor/VendorExternalScreening.vue` |
| Risk dashboard (cross-module) | `grc_frontend/tprm_frontend/src/pages/BCP/RiskAnalytics.vue` |

---

## 8. Suggested task breakdown (for PM tooling)

- **T1**: E2E test + fix first-time vendor risk generation.
- **T2**: Implement `ingest_risk_event` + screening post-hook + watermark.
- **T3**: Questionnaire reassessment hook → same ingestion.
- **T4**: Migrations for provenance + source refs + dedupe fingerprints.
- **T5**: Mitigation APIs + minimal vendor risk UI.
- **T6**: Contract/SLA/BCP adapters (incremental).
- **T7**: TPRM-only packaging / feature flags (with Susheel).

---

*Document version: 1.0 — aligned to repository snapshot and discussion transcript dated 30 March 2026.*
