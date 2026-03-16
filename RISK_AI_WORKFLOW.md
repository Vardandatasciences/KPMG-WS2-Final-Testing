## Risk AI Workflow – Create Risk (AI Mode)

**Example input**

- **Title**: `data breach`
- **Description**: `data stolen from server`

The diagram below shows the full end‑to‑end flow from this input to the final AI JSON response that fills the Risk form, including preprocessing, optimisations, and prompts.

---

### 1. Frontend – User Input & API Call

- **Step 1.1 – User types incident details**
  - **Where**: `CreateRisk.vue` (AI mode).
  - **What**: User enters:
    - `aiInput.title = "data breach"`
    - `aiInput.description = "data stolen from server"`.
  - **Why (theory)**: Keep the UI simple – only title and description; all advanced risk logic is delegated to the backend AI.

- **Step 1.2 – Frontend sends request**
  - **Where**: `generateAiSuggestion()` → `POST /api/analyze-incident/`.
  - **Payload**:
    - `{"title": "data breach", "description": "data stolen from server"}`
  - **Why (theory)**: A single, stable API hides AI details from the UI so you can evolve the backend AI without breaking the frontend.

Tree view:

- **User (browser)**
  - **CreateRisk.vue**
    - `generateAiSuggestion()`
      - `POST /api/analyze-incident/` → backend

---

### 2. Risk View – Normalisation & Routing into AI

- **Step 2.1 – Build canonical incident text**
  - **Where**: `risk_views.analyze_incident` (Django/DRF view).
  - **What**:
    - Constructs:
      - `full_incident = "Title: data breach\n\nDescription: data stolen from server"`
  - **Why (theory)**: Forces a **consistent structure** for all incidents, which stabilises prompts and makes AI optimisation easier.

- **Step 2.2 – Call Risk SLM service**
  - **Where**: `analysis_result = analyze_security_incident(full_incident)`.
  - **Why (theory)**: All deep risk logic lives in a dedicated service (`slm_service.py`), not in the API view; this makes it reusable and testable.

Tree view:

- **Risk API (`/api/analyze-incident/`)**
  - Build `full_incident` string
  - Call `analyze_security_incident(full_incident)`

---

### 3. Risk SLM Service – Preprocessing, RAG, Queueing

#### 3.1 Document hashing & logging

- **Step 3.1.1 – Compute document hash**
  - **Where**: `slm_service.analyze_security_incident`.
  - **What**:
    - `document_hash = calculate_document_hash(incident_description)`
  - **Why (theory)**:
    - Hash is used as a **stable identifier** for:
      - AI caching (same input → reuse result).
      - RAG document IDs.
      - Auditable logs of which text produced which analysis.

#### 3.2 RAG (optional retrieval)

- **Step 3.2.1 – Try to retrieve context**
  - **Where**: `retrieve_relevant_context(incident_description, n_results=3)` (if enabled).
  - **What**:
    - Searches your knowledge base for similar incidents or analyses.
  - **Why (theory)**:
    - Implements **Retrieval‑Augmented Generation (RAG)**: the LLM gets extra grounding from your historical data, improving consistency and domain alignment.

#### 3.3 Queueing for very large incidents

- **Step 3.3.1 – Check size and queue if necessary**
  - **Where**: `if len(incident_description) > 5000: process_with_queue(...)`.
  - **Why (theory)**:
    - Protects the system under load; long incidents can be queued without blocking short requests.

Tree view:

- **Risk SLM service (`analyze_security_incident`)**
  - Compute `document_hash`
  - (Optional) **RAG**: `retrieve_relevant_context(...)`
  - (Optional) **Queue**: `process_with_queue(...)`
  - Call centralized AI service:
    - `AIService.run_task("risk.analyze_security_incident", payload={...})`

---

### 4. Centralized AI Layer – Task, Prompt, and Model Routing

#### 4.1 Task entrypoint

- **Step 4.1.1 – Task dispatch**
  - **Where**: `AIService.run_task("risk.analyze_security_incident", ...)` in `ai/service.py`.
  - **What**:
    - Looks up `RISK_TASKS["risk.analyze_security_incident"]` and calls it.
  - **Why (theory)**:
    - All AI logic is defined as **named tasks**, not ad‑hoc prompts. This gives you an internal “API” for AI features across modules.

#### 4.2 Risk‑specific JSON prompt

- **Step 4.2.1 – Build structured risk prompt**
  - **Where**: `analyze_security_incident_task` in `ai/tasks/risk.py`.
  - **What**:
    - Embeds:
      - `INCIDENT DETAILS:` → `"Title: data breach\n\nDescription: data stolen from server"`
      - `OPTIONAL RETRIEVED CONTEXT:` → RAG chunks (if any).
    - Specifies required JSON keys:
      - `criticality`, `possibleDamage`, `category`, `riskDescription`,
      - `riskLikelihood`, `riskImpact`, justifications, `riskExposureRating`,
      - `riskPriority`, `riskAppetite`, `riskMitigation`.
  - **Why (theory)**:
    - Strong **schema‑driven prompting** reduces parse errors and keeps every output aligned to your risk data model.

#### 4.3 Context window & system prompt

- **Step 4.3.1 – Context and optimisation**
  - **Where**: `AIService._prepare_prompt` in `ai/service.py`.
  - **What**:
    - Uses:
      - `build_context_window(...)` to size text for the model’s context.
      - `optimize_prompt_for_speed(...)` to trim noise.
      - `get_system_prompt("risk.*")` to apply the **risk‑specialist** system role.
  - **Why (theory)**:
    - Implements **context optimisation** (you don’t waste tokens on unimportant text) and a **task‑specific system role** so the model behaves like a GRC risk analyst.

#### 4.4 Model routing & quantization

- **Step 4.4.1 – Choose provider/model**
  - **Where**: `ModelRoutingService.select_model(...)` in `ai/service.py`.
  - **What**:
    - Examines:
      - Task name (`risk.analyze_security_incident`)
      - Prompt length
      - Provider availability
      - Default model profile (quantized Ollama)
    - Selects e.g.:
      - `provider = "ollama"`
      - `model = "llama3.2:3b-instruct-q4_K_M"`
  - **Why (theory)**:
    - Encodes **O1 Model selection** and **O4 Quantization**: the router chooses a performant, size‑appropriate model rather than hardcoding one per route.

#### 4.5 Caching & metrics

- **Step 4.5.1 – Invoke cached JSON generation**
  - **Where**: `AIService.generate_json(...)`.
  - **What**:
    - Wraps the provider call in a cache lookup:
      - Key includes task name, provider, model, prompt, `document_hash`, and `schema_version`.
  - **Why (theory)**:
    - Implements **O2 Caching** and **O14 Monitoring**:
      - Avoid repeated work for identical incidents.
      - Record timing and usage metrics for capacity planning.

Tree view:

- **AIService.run_task("risk.analyze_security_incident")**
  - **Task**: `analyze_security_incident_task`
    - Build risk JSON prompt
  - **Pre‑prompt**: `_prepare_prompt(...)`
    - Context sizing, risk system prompt, (few‑shot support)
  - **Routing**: `select_model(...)`
    - Decide provider + model
  - **Execution**: `generate_json(...)`
    - Cache, metrics, provider call

---

### 5. Model Execution – LLM Inference

- **Step 5.1 – Provider call**
  - **Where**: `OllamaProvider.generate_json(...)` (behind `AIService`).
  - **What**:
    - Sends the final enriched prompt to the Ollama server with:
      - `model = llama3.2:3b-instruct-q4_K_M`
      - low `temperature` for stability.
  - **Why (theory)**:
    - Centralizes **all network I/O** to providers and lets you swap providers/models via config, not code changes in routes.

- **Step 5.2 – Raw JSON risk analysis**
  - **Where**: Provider returns JSON to `AIService`.
  - **What**:
    - Example keys:
      - `criticality: "Severe"`
      - `category: "Data Breach"`
      - `riskLikelihood: 8`
      - `riskImpact: 9`
      - `riskExposureRating: "High Exposure"`
      - `riskPriority: "P0"`
      - `riskMitigation: ["Isolate affected systems", "Notify regulators", ...]`
  - **Why (theory)**:
    - The LLM applies risk rules from the prompt to your specific “data breach / data stolen from server” scenario and returns a **complete structured view** of that risk.

---

### 6. Post‑Processing, RAG Write‑Back, and Response

#### 6.1 RAG write‑back (optional)

- **Step 6.1.1 – Store incident + analysis**
  - **Where**: `add_document_to_rag(...)` in `slm_service`.
  - **What**:
    - Saves:
      - `Incident: Title: data breach ...`
      - `Analysis: {criticality: ..., riskPriority: ..., ...}`
    - Under ID like `risk_slm_<hash prefix>`.
  - **Why (theory)**:
    - Builds a **searchable memory** of past incidents and AI analyses to improve future answers (RAG).

#### 6.2 Guarantee required fields & justifications

- **Step 6.2.1 – Normalize in view**
  - **Where**: `risk_views.analyze_incident`.
  - **What**:
    - Ensures required keys exist:
      - `criticality`, `possibleDamage`, `category`, `riskDescription`,
      - `riskLikelihood`, `riskImpact`, `riskExposureRating`, `riskPriority`, `riskMitigation`.
    - Synthesizes justifications if missing:
      - Example:
        - `"Likelihood score 8 was suggested based on the incident details provided and overall criticality rated as Severe."`
  - **Why (theory)**:
    - Guarantees a **fully populated, user‑friendly object** for the UI, even if the model under‑performs on some fields.

#### 6.3 Final JSON back to frontend

- **Step 6.3.1 – Response to client**
  - **What**:
    - Returns `analysis_result` JSON to the frontend.
  - **UI usage**:
    - Maps fields to the Risk create form:
      - Sets dropdowns (criticality, priority).
      - Fills numeric sliders (likelihood, impact).
      - Populates mitigation steps and tooltips with justifications.

Tree view:

- **SLM service**
  - (Optional) Add to RAG
  - Return `incident_analysis` dict
- **Risk view**
  - Normalize fields and justifications
  - `return Response(analysis_result)`
- **Frontend**
  - Map JSON → Risk form fields

---

### Summary (Data Breach Example)

For the incident:

- **Title**: `data breach`
- **Description**: `data stolen from server`

The centralized AI layer:

1. Normalizes and hashes the text.
2. Optionally enriches it with past knowledge (RAG) and queues long jobs.
3. Runs a named **Risk AI task** with a strictly defined JSON schema.
4. Optimizes prompts and context, selects an appropriate quantized model, and uses caching + metrics.
5. Returns a complete structured risk assessment (criticality, likelihood, impact, exposure, priority, mitigations, justifications).
6. Post‑processes the output so the UI always receives a stable, user‑ready JSON object that can directly fill the Risk creation form.

