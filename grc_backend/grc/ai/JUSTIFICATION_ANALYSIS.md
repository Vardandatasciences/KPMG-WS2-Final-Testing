# Justification Analysis in Centralized AI

This document describes **what** justification analysis is, **where** it lives in the centralized AI, and **how** it flows from the model to the UI.

---

## What

**Justification analysis** is the AI-produced explanation for *why* and *how* a policy or subpolicy was selected from source text during framework upload:

| Field | Meaning |
|-------|--------|
| **extraction_rationale** | **Why selected** – One sentence explaining the reason this policy/subpolicy was identified (e.g. "This control represents the requirement for installing and maintaining a firewall to protect cardholder data."). |
| **source_excerpt** | **How selected / source** – A short quote from the section text that led to this selection, or empty string. |

It is returned per **policy** and per **subpolicy** so the UI can show "How & why this policy/subpolicy was selected" in the Upload Framework (Content Selection and Edit Policy Details).

---

## Where

| Layer | Location | Role |
|-------|----------|------|
| **Task (canonical prompt)** | `grc/ai/tasks/policy.py` → `extract_policy_hierarchy()` | Defines the required JSON shape including `ai_analysis` for policies and subpolicies. Used when callers use payload-based API. |
| **Caller (upload flow)** | `grc/routes/uploadNist/policy_extractor_enhanced.py` | Builds its own prompt (with same ai_analysis structure), calls `get_ai_service().generate_json(task_name="policy.extract_policy_hierarchy", prompt=...)`. Uses centralized routing, config, cache, metrics. |
| **Config** | `grc/ai/config.py` | `policy.extract_policy_hierarchy` in `task_sampling_profiles` (temperature, etc.). |
| **System prompt** | `grc/ai/prompts/__init__.py` | `task_name.startswith("policy.")` → system prompt "You are a policy and compliance expert...". |
| **Service** | `grc/ai/service.py` | `generate_json()` applies context budgeting, optimization, cache, model router for this task. |
| **Normalizer** | `grc/routes/uploadNist/policy_extractor_enhanced.py` → `_normalize_policy_response()` | Preserves `ai_analysis` from raw response (including nested/array formats). |
| **Data pipeline** | `consolidate_data.py`, `upload_framework.py`, `uploaded_data_loader.py` | Pass `ai_analysis` through to API response. |
| **UI** | `grc_frontend/.../UploadFramework.vue` | Shows "How & why this policy/subpolicy was selected" with **Why selected:** and **How selected / source:**. |

---

## How

1. **Request**  
   Upload framework processing (or any caller) calls the centralized AI with task `policy.extract_policy_hierarchy` and a prompt that asks for policies/subpolicies and, for each, `ai_analysis: { extraction_rationale, source_excerpt }`.

2. **Centralized AI**  
   - System prompt: policy/compliance expert.  
   - Context budgeting and prompt optimization applied.  
   - Model router selects provider/model.  
   - Cache key includes task + prompt (optional).  
   - Response is parsed as JSON.

3. **Normalizer**  
   `_normalize_policy_response()` ensures various response shapes (flat policies, nested by framework/section, section → list of controls) are converted to a single shape and **keeps** `ai_analysis` on each policy and subpolicy.

4. **Persistence**  
   Enhanced policies/subpolicies (with `ai_analysis`) are written to `all_policies.json` and then to consolidated/framework data used by the sections API.

5. **API**  
   `get_sections_by_user` (and consolidate_data / uploaded_data_loader) include `ai_analysis` in each policy and subpolicy in the JSON response.

6. **UI**  
   Upload Framework shows an "AI" toggle per policy and subpolicy; when expanded, it displays **Why selected:** (extraction_rationale) and **How selected / source:** (source_excerpt).

---

## Summary

- **What:** extraction_rationale (why) + source_excerpt (how/source).  
- **Where:** Centralized in `grc/ai` (task, config, prompts, service); caller in `policy_extractor_enhanced`; normalizer and data pipeline pass it through; UI in UploadFramework.vue.  
- **How:** Call → centralized `generate_json` → normalizer preserves ai_analysis → all_policies → consolidated/API → frontend displays "How & why this policy/subpolicy was selected".
