## Centralized AI Preprocessing & Optimisation Flows

This document explains the two main AI input flows in your backend, focusing on:

- **What preprocessing steps are involved**
- **What optimisations are applied**
- **A short theory (1–2 lines) for what each step actually does**

---

## Flow 1 – Document‑Based AI (Uploads / Large Documents)

**Used by**: `risk_ai_doc.py`, `risk_instance_ai.py`, policy/framework upload routes, and any code that calls `DocumentPreparationService.prepare_text()` or `preprocess_document()`.

**Core pipeline**

- Raw document → `preprocess_document()` → `DocumentPreparationService` → centralized AI tasks (policy / risk / incident, etc.)

### 1.1 Preprocessing Steps

- **Step 1 – Remove control characters**
  - **Code**: `remove_control_characters(text)` in `document_preprocessor.py`.
  - **What it does**: Strips non‑printable bytes (keeps normal characters plus `\n`, `\r`, `\t`).
  - **Theory (2 lines)**:  
    Removes hidden control symbols that can corrupt JSON or break tokenization.  
    Keeps the semantic content unchanged while making the text safe for downstream parsers and LLMs.

- **Step 2 – Normalize whitespace**
  - **Code**: `normalize_whitespace(text)`.
  - **What it does**:
    - Collapses repeated spaces into a single space.
    - Collapses 3+ newlines into double newlines.
    - Converts tabs to spaces and trims each line.
  - **Theory (2 lines)**:  
    Converts messy PDFs/Word exports into a clean, compact layout without losing paragraph structure.  
    This improves prompt readability and reduces unnecessary tokens, which saves context and cost.

- **Step 3 – Lemmatization (centralized, mandatory in this flow)**
  - **Code**: `lemmatize_text(text)`.
  - **What it does**:
    - If available, uses `spaCy` (`en_core_web_sm`) to turn words into lemmas (e.g., “breaches” → “breach”, “running” → “run”).  
    - Otherwise uses a lightweight rule‑based lemmatizer for common English endings (`s`, `ies`, `ing`, `ed`).
  - **Theory (2 lines)**:  
    Normalizes word forms so searches, retrieval, and AI prompts see a more consistent vocabulary.  
    This modestly improves recall in RAG and makes the model less sensitive to inflectional noise.

- **Step 4 – Intelligent truncation**
  - **Code**: `truncate_intelligently(text, max_length=8000)`.
  - **What it does**:
    - If length exceeds `max_length`, keeps ~40% from the start, ~20% around the middle, ~40% from the end.  
    - Tries to align cuts to sentence boundaries and inserts “[... content truncated for performance ...]” markers.
  - **Theory (2 lines)**:  
    Preserves introductions, core content, and conclusions even when you must fit into a tight context window.  
    Prevents giant documents from overwhelming the model while still keeping enough structure to reason about.

- **Step 5 – Metadata capture**
  - **Code**: return `(processed_text, metadata)` where `metadata` includes `original_length`, `processed_length`, `was_truncated`, `reduction_percent`, `lemmatization_applied`.
  - **Theory (2 lines)**:  
    Gives you introspection into how aggressively each document was cleaned and shortened.  
    This is useful for debugging odd model behaviour and tuning `max_length` or preprocessing rules over time.

### 1.2 Optimisations in the Document Flow

- **Context window optimisation**:  
  - Truncation ensures docs respect a global `max_length`, reducing token load and latency.  
  - Combined with RAG, this lets you handle long sources by slicing + retrieval instead of brute‑forcing everything into one prompt.

- **Token normalisation via lemmatization**:  
  - Reduces sparse variants (“breach”, “breaches”, “breached”) down to a canonical form for the retrieval/indexing layer.  
  - This improves hit rates when you later query similar documents or annotate per‑token stats.

- **Prompt stability**:  
  - Since uploads are always pre‑cleaned, downstream prompts see consistent structure regardless of source format (PDF, DOCX, TXT, etc.).  
  - This reduces prompt engineering overhead per module because all consumers share the same clean text contract.

---

## Flow 2 – Inline Text AI (Risk Create – Analyze Incident)

**Used by**: `/api/analyze-incident/` → `risk_views.analyze_incident` → `slm_service.analyze_security_incident` → `AIService.run_task("risk.analyze_security_incident", ...)`.

**Core pipeline**

- Title + description from UI → build `"Title: ... / Description: ..."` string → centralized AI task → model routing, caching, metrics → risk JSON → UI.

> Note: This flow currently does **not** call `preprocess_document`, so it does **not** involve the lemmatization/truncation pipeline. It relies on lighter, task‑level optimisations inside the centralized AI service.

### 2.1 Preprocessing Steps

- **Step 1 – Canonical incident string**
  - **Where**: `risk_views.analyze_incident`.
  - **What it does**:
    - Builds `full_incident = "Title: <title>\n\nDescription: <description>"` from raw request JSON.
  - **Theory (2 lines)**:  
    Forces all incident inputs into a consistent, minimal schema independent of UI layout.  
    This makes downstream prompts simpler and avoids per‑client variations in how incidents are described.

- **Step 2 – Document hash for the incident**
  - **Where**: `slm_service.analyze_security_incident` → `calculate_document_hash(incident_description)`.
  - **What it does**:
    - Computes a SHA‑256 hash of the incident text for use as a cache/RAG key.
  - **Theory (2 lines)**:  
    Provides a stable fingerprint for a given incident description across requests and services.  
    This is the backbone for fast cache lookups and also cleanly associates RAG entries with specific incidents.

### 2.2 Optimisations in the Inline Flow

- **O9 – Optional RAG for incidents**
  - **Where**: `retrieve_relevant_context(incident_description, n_results=3)` in `slm_service`.
  - **What it does**:
    - When enabled, fetches up to three relevant past analyses or documents and injects them into the prompt context.
  - **Theory (2 lines)**:  
    Enriches one‑off incident analyses with your historical understanding of similar events.  
    This nudges the model toward decisions and patterns that have already proven useful in your environment.

- **O6 – Queueing for very large incidents**
  - **Where**: `if len(incident_description) > 5000: process_with_queue(...)`.
  - **What it does**:
    - Routes very large descriptions through a background queue rather than handling them inline.
  - **Theory (2 lines)**:  
    Protects your API latency for typical users by isolating heavy requests.  
    This ensures that a single large incident doesn’t degrade the overall system responsiveness.

- **Task‑level prompt optimisation**
  - **Where**: `ai/tasks/risk.py` and `AIService._prepare_prompt`.
  - **What it does**:
    - Uses a standardized risk JSON schema prompt plus centralized context handling and a risk‑specialist system prompt.  
    - `AIService` further optimizes whitespace, context budget, and (optionally) few‑shot examples.
  - **Theory (2 lines)**:  
    Keeps per‑route logic thin—most intelligence (schema, risk rules, system instruction) lives in one central place.  
    This makes it easier to upgrade the risk analysis behaviour globally without editing multiple endpoints.

- **Model routing & quantization (O1, O4)**
  - **Where**: `ModelRoutingService.select_model`, `get_quantized_model` in `AIService.generate_json`.
  - **What it does**:
    - Chooses between providers/models (e.g. quantized Ollama vs. OpenAI) based on task name and content size.  
    - Prefers quantized models like `llama3.2:3b-instruct-q4_K_M` for speed and cost.
  - **Theory (2 lines)**:  
    Encodes best‑practice model choices in configuration and routing rules, not in UI or route code.  
    This allows you to adjust performance/price trade‑offs centrally per task.

- **Response caching (O2)**
  - **Where**: `AIService.generate_json` via `AIResponseCache.get_or_set`.
  - **What it does**:
    - Caches AI responses keyed by task, provider, model, prompt, and `document_hash`.
  - **Theory (2 lines)**:  
    Avoids paying twice for identical or near‑identical analyses when users resubmit the same incident.  
    Reduces latency and provider cost while preserving deterministic results for repeated inputs.

- **Metrics & health monitoring (O14, O15)**
  - **Where**: `record_ai_call`, `record_cache_hit`, `record_rag_usage`, `get_ai_runtime_health`.
  - **What it does**:
    - Tracks latency, cache hits, RAG usage, and provider health across all risk tasks.
  - **Theory (2 lines)**:  
    Gives you operational insight into how often and how well the AI layer runs.  
    Supports capacity planning, model tuning, and debugging when production behaviour changes.

---

## Summary Comparison

- **Flow 1 – Document‑based**:
  - Heavy on **text preprocessing** (control‑chars, whitespace, **lemmatization**, intelligent truncation).
  - Designed for **large, uploaded documents** where normalization and context management are critical.

- **Flow 2 – Inline risk incident**:
  - Light normalization (canonical incident string) plus hash‑based caching and RAG/queueing optimisations.  
  - Designed for **short UI text inputs** with strong task‑level schema prompts and centralized model routing.

Together, these two flows let you handle both **big, messy documents** and **fast inline risk analyses** through the same centralized AI layer, while tailoring preprocessing and optimisations to the nature of the input. 


---

## Centralized AI Components in `grc_backend/grc/ai` and Where They Are Used

This section lists the main centralized AI components under `grc_backend/grc/ai`, what optimisations they provide, and **which product features** currently use them.

### 3.1 `ai/config.py` – Central Provider/Model Configuration

- **What it does**
  - Normalizes AI settings (`AI_PROVIDER`, `OPENAI_MODEL`, `OLLAMA_MODEL_*`, `USE_CUSTOM_OLLAMA_MODELS`).
  - Defines **model profiles** (fast/default/complex/custom) and sampling profiles per task.
  - Exposes `AI_SETTINGS` so all modules read configuration from a single place.
- **Key optimisations**
  - **O1 – Model selection baseline** (profiles for fast vs. complex vs. custom).
  - **O4 – Quantization awareness** (defaults to quantized Ollama models where appropriate).
- **Where it is used**
  - **Risk document ingestion**: `routes/Risk/risk_ai_doc.py` (`AI_PROVIDER`, `OLLAMA_*`, `OPENAI_*`).
  - **Risk instance ingestion**: `routes/Risk/risk_instance_ai.py` (via `risk_ai_doc` exports).
  - **Incident AI import**: `routes/Incident/incident_ai_import.py` (reuses same provider config).
  - **Incident SLM**: `routes/Incident/incident_slm.py` (reads `AI_PROVIDER`, `OPENAI_MODEL`, `OLLAMA_MODEL_*`).
  - **Change Management AI**: `routes/changemanagement/framework_comparison.py` (reads `AI_PROVIDER` / `OPENAI_MODEL`).
  - **Policy upload & compliance generator**: `routes/uploadNist/policy_extractor_enhanced.py`, `routes/uploadNist/compliance_generator.py`.

### 3.2 `ai/service.py` – `AIService` (Core Orchestrator)

- **What it does**
  - Provides unified APIs: `generate_text`, `generate_json`, `embed`, `ingest_knowledge`, `retrieve_knowledge`, `run_task`, `get_job_status`, `health`.
  - Wires together routing, context optimisation, caching, metrics, RAG, and provider calls.
- **Key optimisations**
  - **O1/O4** – Model routing and quantized model selection (`ModelRoutingService`, `get_quantized_model`).
  - **O2** – Response caching (`AIResponseCache.get_or_set`).
  - **O3/O10/O13** – Context sizing + prompt optimisation + few‑shot (via `prompts` and `processing/context.py`).
  - **O9** – RAG integration via `RAGService` for tasks that pass `rag_chunks_used` metadata.
  - **O14/O15** – Metrics and health (records latency, cache hits, RAG usage; exposes `health()`).
- **Where it is used (features)**
  - **Risk Create (AI mode)**:
    - `routes/Risk/slm_service.py` → `get_ai_service().run_task("risk.analyze_security_incident", ...)`.
  - **Risk document ingestion**:
    - `routes/Risk/risk_ai_doc.py` → uses `JSONResponseParser` and `legacy_call_*` wrappers now backed by `AIService`.
  - **Risk instance ingestion**:
    - `routes/Risk/risk_instance_ai.py` → `get_ai_service().run_task("risk.infer_field", ...)` for missing fields.
  - **Policy upload/extraction & compliance generation**:
    - `routes/uploadNist/policy_extractor_enhanced.py` → `get_ai_service().generate_json(...)`.
    - `routes/uploadNist/compliance_generator.py` → `get_ai_service().generate_json(...)`.
  - **Policy AI features (centralized policy AI)**:
    - `routes/Policy/policy_ai_service.py` → `get_ai_service()` for:
      - Draft policy from controls.
      - Gap analysis.
      - Policy review quality.
      - Explain generated output with evidence.

### 3.3 `ai/runtime/*` – Cache, Queue, Jobs, Metrics, Health

- **`runtime/cache.py` – `AIResponseCache`**
  - **Optimisation**: Implements **O2 – AI response caching** with composite keys (`task`, `provider`, `model`, `prompt`, `document_hash`, `schema_version`).
  - **Used by**:
    - All centralized `AIService.generate_json` calls (Policy tasks, Risk tasks, Risk doc parsing, etc.).

- **`runtime/queue.py` – `AIRequestQueue`**
  - **Optimisation**: Central interface for queuing long AI jobs (used indirectly via older `request_queue` in Risk/Incident/Upload flows).
  - **Used by**:
    - **Risk incident SLM**: `slm_service.analyze_security_incident` (for large incidents).
    - Document ingestion flows that still depend on `process_with_queue`.

- **`runtime/jobs.py` – `AIJobService`**
  - **Optimisation**: Centralized tracking of long‑running AI jobs (file‑backed store).
  - **Used by**:
    - **Framework upload AI processing**: `routes/uploadNist/ai_upload_api.py`.
    - **Policy AI workflow orchestration**: `routes/Policy/policy_ai_service.py` (import job tracking).

- **`runtime/metrics.py` and `runtime/health.py`**
  - **Optimisation**: Implements **O14/O15** (monitoring + health).
  - **Used by**:
    - `AIService.generate_*` (records every AI call).
    - `AIService.health()` endpoint (consumed by system/ops health checks).

### 3.4 `ai/processing/*` – Preprocessor, Parser, Context, Upload I/O

- **`processing/preprocessor.py` – `DocumentPreparationService`**
  - Wraps `preprocess_document` + `calculate_document_hash` + decompression (via `upload_io`).
  - **Used by**:
    - Policy framework ingestion and compliance generation (UploadNist flows).
    - Risk and risk‑instance document ingestion (`risk_ai_doc.py`, `risk_instance_ai.py`).

- **`processing/parser.py` – `JSONResponseParser`**
  - Robust parsing for AI JSON responses (handles code blocks, slight malformations).
  - **Used by**:
    - **Risk document ingestion**: `routes/Risk/risk_ai_doc.py` (`_json_from_llm_text`).
    - Compliance/Policy routes that previously had brittle JSON parsing.

- **`processing/context.py` – context sizing & window building**
  - Calculates optimal context sizes and builds windows according to strategy and task complexity.
  - **Used by**:
    - `AIService._prepare_prompt` for all tasks (Policy & Risk), including `risk.analyze_security_incident`.

- **`processing/upload_io.py` – file decompression**
  - Handles decompressing uploaded files and capturing compression metadata.
  - **Used by**:
    - `DocumentPreparationService.prepare_uploaded_file()` (framework, risk, and risk‑instance document uploads).

### 3.5 `ai/retrieval/rag.py` – RAG Service

- **What it does**
  - Provides a centralized interface for ingesting documents into a vector store and retrieving relevant context.
- **Used by**
  - `AIService.ingest_knowledge` and `AIService.retrieve_knowledge`.
  - **Risk incident SLM**:
    - `slm_service.analyze_security_incident` adds completed incident + analysis to RAG.
  - Potentially by Policy/Compliance routes as you extend RAG coverage.

### 3.6 `ai/prompts/__init__.py` – System Prompts, Templates, Few‑Shot

- **What it does**
  - Stores **system prompts** (e.g. `risk` specialist, `policy` expert).
  - Stores **prompt templates** for some policy tasks.
  - Supports attaching **few‑shot examples** and rendering prompts in a standardized way.
- **Used by**
  - `AIService._prepare_prompt` for:
    - All **Policy tasks** (gap analysis, drafting, review).
    - All **Risk tasks** (`risk.analyze_security_incident`, `risk.infer_field`).

### 3.7 `ai/tasks/*` – Policy and Risk Task Definitions

- **`tasks/policy.py`**
  - **Features using it**:
    - Policy framework extraction & hierarchy building (`UploadFramework` / `uploadNist` flows).
    - Subpolicy compliance generation and risk detail generation.
    - Policy gap analysis, policy drafting, policy quality review, explain‑with‑evidence.
  - These are wired into:
    - `routes/Policy/policy_ai_service.py`.
    - `routes/uploadNist/policy_extractor_enhanced.py`.
    - `routes/uploadNist/compliance_generator.py`.

- **`tasks/risk.py`**
  - **Features using it**:
    - **Risk Create AI**: `risk.analyze_security_incident` for inline incident analysis.
    - **Risk & Risk‑Instance document flows**: `risk.infer_field` for filling missing risk or risk‑instance fields during ingestion.
  - These are wired into:
    - `routes/Risk/slm_service.py` (incident string → `risk.analyze_security_incident`).
    - `routes/Risk/risk_ai_doc.py` and `routes/Risk/risk_instance_ai.py` (per‑field inference).

### 3.8 `ai/adapters.py` – Legacy Compatibility Layer

- **What it does**
  - Exposes `legacy_call_openai_json` / `legacy_call_ollama_json` and config constants in a way that old modules can use **without** knowing about `AIService`.
- **Used by**
  - **Incident SLM**: `routes/Incident/incident_slm.py`.
  - **Risk SLM (older code)**: portions of `risk_ai_doc.py`, `risk_instance_ai.py` and incident import still relying on legacy call patterns.

---

### 3.9 High‑Level Map: Centralized AI vs Product Features

- **Policy Module**
  - Framework upload & AI extraction (`UploadFramework`, `uploadNist`):
    - Uses document preprocessing (with lemmatization), AIService, Policy tasks, and RAG support.
  - Policy drafting, gap analysis, quality review, and explain‑with‑evidence:
    - Uses centralized Policy tasks, prompts, routing, caching, and metrics.

- **Risk Module**
  - Risk document ingestion:
    - Uses document preprocessing (with lemmatization), JSONResponseParser, centralized Risk field inference.
  - Risk instance ingestion:
    - Same as above but with a richer risk‑instance schema and JSON normalization.
  - Risk Create AI (inline):
    - Uses the **inline flow** plus centralized Risk incident task, routing, caching, metrics, and optional RAG.

- **Incident Module**
  - Incident SLM (impact/response analysis):
    - Uses centralized provider config, adapters, and parts of the optimization layer (routing, metrics).
  - Incident document AI import:
    - Uses central config and older wrappers; can be gradually migrated to full `AIService` usage.

- **Change Management & Compliance Matching**
  - `changemanagement/framework_comparison.py`:
    - Reuses centralized AI provider/model configuration for similarity analysis and gap checks.

In short, **all new and refactored AI features in your product now depend on the centralized `grc_backend/grc/ai` layer**, with:

- Document‑style features using **Flow 1** (full preprocessing + lemmatization).  
- Inline risk analysis using **Flow 2** (light preprocessing + strong centralized routing/caching).  
- Common config, routing, metrics, and health shared across Policy, Risk, Incident, and Change Management modules.

