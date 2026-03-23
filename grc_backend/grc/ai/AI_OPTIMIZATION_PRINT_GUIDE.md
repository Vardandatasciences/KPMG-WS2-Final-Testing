# AI Preprocessing & Optimization – Print Statement Guide

This document describes all `print()` statements added for **cross-verification** of preprocessing and optimization flows. When you upload a document or run AI tasks, the terminal will show the full pipeline.

---

## 1. Document Preprocessing (`grc/utils/document_preprocessor.py`)

| Tag | Step | What it logs |
|-----|------|--------------|
| `[PREPROCESS] Step 1` | remove_control_characters | Control chars removed, result length |
| `[PREPROCESS] Step 2` | normalize_whitespace | Char counts before/after |
| `[PREPROCESS] Step 3` | lemmatize_text | spaCy or rule-based, char counts |
| `[PREPROCESS] Step 4` | truncate_intelligently | Truncation (or none), char counts |
| `[PREPROCESS] DONE` | preprocess_document | Final: original, processed, truncated, reduction % |
| `[PREPROCESS] calculate_document_hash` | Hash | SHA256 hash (first 16 chars) for cache key |

---

## 2. AI Document Preparation (`grc/ai/processing/preprocessor.py`)

| Tag | What it logs |
|-----|--------------|
| `[AI-PREP] DocumentPreparationService.prepare_text` | Input length, max_length |
| `[AI-PREP] DocumentPreparationService.prepare_text` | Output length, document hash |
| `[AI-PREP] DocumentPreparationService.prepare_uploaded_file` | File path being prepared |

---

## 3. Context Optimization (`grc/ai/processing/context.py`)

| Tag | What it logs |
|-----|--------------|
| `[AI-CONTEXT] calculate_optimal_context_size` | Text length, complexity, max_context |
| `[AI-CONTEXT] truncate_for_context_budget` | Length before/after, max_context (when truncated) |
| `[AI-CONTEXT] build_context_window` | Strategy (head/tail/balanced), chars kept, truncated flag |

---

## 4. Model Routing (`grc/ai/routing/model_router.py` + `grc/utils/model_router.py`)

| Tag | What it logs |
|-----|--------------|
| `[AI-ROUTER] select_model` | Provider, model, reason (OpenAI or Ollama) |
| `[AI-ROUTER] route_model` | Task type, doc_size, complexity, system_load, selected model |

---

## 5. Response Cache (`grc/ai/runtime/cache.py`)

| Tag | What it logs |
|-----|--------------|
| `[AI-CACHE] HIT` | Task, provider, model, cache key (skipped LLM call) |
| `[AI-CACHE] MISS` | Task, provider, model – calling callback |
| `[AI-CACHE] SET` | Task, TTL – result cached |

---

## 6. Prompt Optimization (`grc/ai/prompts/__init__.py`)

| Tag | What it logs |
|-----|--------------|
| `[AI-PROMPT] optimize_prompt_for_speed` | Task, char counts before/after |
| `[AI-PROMPT] attach_few_shot_examples` | Task, number of examples (if any) |

---

## 7. AI Service (`grc/ai/service.py`)

| Tag | What it logs |
|-----|--------------|
| `[AI-SERVICE] _prepare_prompt` | Task, raw prompt length |
| `[AI-SERVICE] _prepare_prompt` | Task, final prompt length, truncated flag |
| `[AI-POLICY]` | Centralized AI calls for policy tasks (existing) |
| `[AI-RISK]` | Centralized AI calls for risk tasks (existing) |
| `[AI-INCIDENT]` | Centralized AI calls for incident tasks (existing) |

---

## 8. Provider – Ollama (`grc/ai/providers/ollama_provider.py`)

| Tag | What it logs |
|-----|--------------|
| `[AI-PROVIDER] Ollama.generate_json` | Model, prompt length, temperature |
| `[AI-PROVIDER] Ollama.generate_json: SUCCESS` | Response length, parsed type |

---

## 9. JSON Parser (`grc/ai/processing/parser.py`)

| Tag | What it logs |
|-----|--------------|
| `[AI-PARSER] parse_json_block` | First parse failed, retrying with comments stripped |

---

## 10. Metrics (`grc/ai/runtime/metrics.py`)

| Tag | What it logs |
|-----|--------------|
| `[AI-METRICS] record_ai_call` | Task, provider, model, latency_ms, success |

---

## 11. Policy Tasks (`grc/ai/tasks/policy.py`)

| Tag | What it logs |
|-----|--------------|
| `[AI-TASK] extract_policy_hierarchy` | Section title, section text length |
| `[AI-TASK] extract_policy_hierarchy: DONE` | Policies count, subpolicies count |
| `[AI-TASK] generate_subpolicy_compliances` | Subpolicy title, control length |
| `[AI-TASK] generate_subpolicy_compliances: DONE` | Compliances count |

---

## Example Flow (Document Upload → Policy Extraction → Compliance Generation)

```
[AI-PREP] DocumentPreparationService.prepare_uploaded_file: file=...
[AI-PREP] DocumentPreparationService.prepare_text: input=... chars, max_length=8000
[PREPROCESS] Step 1 - remove_control_characters: removed X control chars, result=... chars
[PREPROCESS] Step 2 - normalize_whitespace: before=... chars, after=... chars
[PREPROCESS] Step 3 - lemmatize_text: spaCy/rule-based applied, ... -> ... chars
[PREPROCESS] Step 4 - truncate_intelligently: ... (if truncated)
[PREPROCESS] DONE - preprocess_document: original=..., processed=..., truncated=..., reduction=...%
[PREPROCESS] calculate_document_hash: SHA256 hash=...
[AI-PREP] DocumentPreparationService.prepare_text: output=... chars, hash=...

[AI-TASK] extract_policy_hierarchy: section_title=..., section_text_len=...
[AI-SERVICE] _prepare_prompt: task=policy.extract_policy_hierarchy, raw_prompt_len=...
[AI-CONTEXT] calculate_optimal_context_size: text_len=..., complexity=... -> max_context=...
[AI-PROMPT] optimize_prompt_for_speed: task=..., before=... chars, after=... chars
[AI-ROUTER] select_model: Ollama heuristic, model=..., task=..., doc_size=...
[AI-ROUTER] route_model: task=..., doc_size=..., complexity=..., load=... -> model=...
[AI-CACHE] MISS: task=... - calling callback
[AI-PROVIDER] Ollama.generate_json: model=..., prompt_len=..., temperature=...
[AI-METRICS] record_ai_call: task=..., provider=ollama, model=..., latency=...ms, success=True
[AI-PROVIDER] Ollama.generate_json: SUCCESS, response_len=..., parsed_type=dict
[AI-CACHE] SET: task=..., ttl=...s, cached result
[AI-TASK] extract_policy_hierarchy: DONE - policies=X, subpolicies=Y

[AI-TASK] generate_subpolicy_compliances: subpolicy=..., control_len=...
[AI-CACHE] HIT or MISS ...
[AI-TASK] generate_subpolicy_compliances: DONE - compliances_count=...
```

---

## Enabling / Disabling Prints

These are standard Python `print()` calls. To reduce noise:

- Redirect stdout: `python manage.py runserver 2>&1 | grep '\[AI-'`
- Use `ENABLE_DEBUG_LOGGING` only where `debug_print` is used (separate from these prints)
- Or wrap in an environment check if you add a debug flag later
