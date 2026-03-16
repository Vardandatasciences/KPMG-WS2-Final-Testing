1. AI Policy Creation
Converts uploaded regulatory/framework PDFs into structured policies, subpolicies, and compliance records.
This reduces manual framework setup effort and speeds up onboarding of new standards into the product.
2. AI Audit Assignment Recommendations
Suggests suitable auditors or reviewers based on audit scope, objective, and compliance context.
This helps teams assign audits faster and improves match quality with better consistency.
3. AI Audit Document Upload and Compliance Check
Analyzes uploaded audit evidence against mapped compliance requirements and returns structured findings.
This reduces manual evidence review and helps auditors identify gaps, strengths, and recommendations quickly.
4. Combined Evidence Audit Analysis
Evaluates both document evidence and database/system evidence together for audit assessment.
This gives a more realistic and defensible view of control effectiveness than document-only checking.
5. AI Audit Report Generation
Creates downloadable audit reports from AI-based evidence analysis and compliance results.
This shortens the reporting cycle and makes audit outputs easier to share with management.
6. Incident Form AI Analysis
Generates structured incident insights from a title and description, such as priority, impact, and mitigation.
This improves incident triage speed and helps users fill complex fields more consistently.
7. Incident AI Import
Extracts structured incident records from uploaded files such as reports, spreadsheets, or memos.
This reduces manual data entry and helps organizations convert external incident documents into system records.
8. AI Suggested Risk Creation
Converts incident or narrative input into a draft risk assessment with scoring and mitigation suggestions.
This helps teams move faster from incident identification to formal risk creation.
9. Risk Instance AI Ingestion
Extracts workflow-ready risk instance records from uploaded documents with editable AI-generated fields.
This supports quicker operational risk registration while keeping human review in the loop.
10. Backend Risk Document Import
Processes uploaded risk-related files and extracts normalized risk records with provenance tracking.
This is useful for importing legacy risk registers and improving trust in AI-generated outputs.
11. Organizational Controls Mapping
Maps internal organizational controls against compliance requirements and explains what is satisfied or missing.
This helps compliance teams assess control coverage and identify gaps more clearly.
12. Framework Amendment Analysis
Detects and structures changes in updated framework documents, such as modified or newly added controls.
This reduces manual comparison effort and helps teams understand regulatory changes faster.
13. Similarity-Based Change Matching
Matches changed framework controls to existing policies, subpolicies, and compliances using similarity logic.
This helps teams trace which internal governance items are likely impacted by new amendments.
14. Gap Analysis Between Framework Versions
Compares old and new framework versions to identify new, modified, removed, and unchanged controls.
This supports structured framework migration and helps compliance teams plan updates systematically.

---

## Centralized vs local AI – feature mapping

**Centralized** = uses `grc/ai` service (`get_ai_service()`, tasks in `grc/ai/tasks/`, prompts, context budgeting, cache, model router).  
**Local** = uses route-level AI only (`call_ai_api` in `ai_audit_api.py`, direct Ollama/OpenAI in route files, or OpenAI client for embeddings).

| # | Feature | Where used | Centralized API + optimizations | Local / existing code |
|---|--------|------------|---------------------------------|------------------------|
| 1 | **AI Policy Creation** | Upload framework → policy/subpolicy/compliance extraction | ✅ Yes. `policy_extractor_enhanced` → `get_ai_service().generate_json("policy.extract_policy_hierarchy")`. Compliances via `policy_ai_service` → `get_ai_service()` + `compliance_generator` → `policy.generate_subpolicy_compliances`. | Prompt built in route; normalization in `policy_extractor_enhanced` (nested format, fallback subpolicy). |
| 2 | **AI Audit Assignment Recommendations** | Assign audit flow | ❌ No centralized AI. | Logic in `assign_audit.py`; no `get_ai_service` or `call_ai_api` for recommendations (rule-based or no AI). |
| 3 | **AI Audit Document Upload and Compliance Check** | Audit evidence vs compliance | ❌ No. | ✅ Local. `ai_audit_api.py` uses `call_ai_api(prompt, …)` (direct Ollama/OpenAI in same module). No `grc/ai` service, cache, or model router. |
| 4 | **Combined Evidence Audit Analysis** | Document + DB evidence | ❌ No. | ✅ Local. Same `call_ai_api` in `ai_audit_api.py`. |
| 5 | **AI Audit Report Generation** | Report from AI evidence analysis | ❌ No. | ✅ Local. Report built from results of `call_ai_api`; no centralized report task. |
| 6 | **Incident Form AI Analysis** | Create incident (title/description → fields) | ✅ Yes. `incident_slm.py` → `get_ai_service()` with centralized incident task. | — |
| 7 | **Incident AI Import** | Extract incidents from uploaded files | ✅ Yes. `incident_ai_import.py` → `get_ai_service()`, centralized preprocessor + extract task. | — |
| 8 | **AI Suggested Risk Creation** | Incident/narrative → risk draft | ✅ Yes. `slm_service.py` (Create Risk) → `get_ai_service()`. | — |
| 9 | **Risk Instance AI Ingestion** | Ingest risk from documents | ✅ Yes. `risk_instance_ai.py` → `get_ai_service()` (infer fields + ingest), centralized document prep. | Some paths may still use legacy Ollama/OpenAI wrappers in same file. |
| 10 | **Backend Risk Document Import** | Risk doc import (normalized records) | ✅ Yes. `risk_ai_doc.py` → `get_ai_service()` for `risk.ingest_risk_document`, centralized preprocessor. | Same file also has `legacy_call_ollama_json` / `legacy_call_openai_json` for some field-inference paths. |
| 11 | **Organizational Controls Mapping** | Org control vs framework requirement | ✅ Yes. `organizational_controls.py` → `get_ai_service().generate_json("compliance.control_mapping_audit", prompt)`. Uses grc/ai prompts, config, cache, model router. | Prompt built in route (5000-char cap); response normalized if string. |
| 12 | **Framework Amendment Analysis** | Amendment PDF → structure/changes | ✅ Yes (for extraction). Amendment pipeline uses `policy_extractor_enhanced.extract_policies` and `compliance_generator`, which use `get_ai_service()`. | Section extraction and orchestration in `amendment_processor`; PDF/index flow is existing upload pipeline. |
| 13 | **Similarity-Based Change Matching** | Match changed controls to policies/subpolicies/compliances | ❌ No. | ✅ Local. `similarity_matcher.py` uses **OpenAI client directly** for embeddings (`get_embedding`); hybrid similarity uses local text/ID logic. No `grc/ai` service. |
| 14 | **Gap Analysis Between Framework Versions** | Old vs new version gaps | ❌ No centralized AI. | Gap list built in `framework_comparison.py` from amendment/comparison data (structural); no AI call in gap endpoint. |

### Summary

- **Using centralized APIs and optimizations:** 1, 6, 7, 8, 9, 10, 11, 12 (policy/amendment extraction and compliance generation; incident form + import; risk creation + risk/instance doc ingest; **organizational controls mapping**).
- **Still using local/existing code only:** 2, 3, 4, 5, 13, 14 (audit assignment, audit document/evidence/report, similarity matching, gap analysis).