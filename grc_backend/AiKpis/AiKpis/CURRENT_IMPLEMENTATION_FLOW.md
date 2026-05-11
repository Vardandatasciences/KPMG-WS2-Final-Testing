# AiKpis Current Implementation and End-to-End Flow

This document explains the **current implementation** of `grc_backend/AiKpis/AiKpis`, including:

- what each file does,
- how KPI generation works step-by-step at runtime,
- and the theoretical architecture behind the flow.

---

## 1) High-Level Purpose

The `AiKpis` package generates framework-specific KPIs by combining:

1. relational database context (framework + related operational tables),
2. optional S3 evidence/documents,
3. LLM-generated KPI definitions,
4. validation and formula hardening,
5. runtime KPI value calculation,
6. persistence into the `kpis` database table.

The implementation is designed as a pipeline with explicit logging and retry behavior.

---

## 2) File-by-File Responsibility Map

### `generateFrameworkKpi.py`
- CLI entrypoint.
- Parses command-line arguments:
  - `--framework-id`
  - `--modules`
  - `--max-s3-docs`
- Calls `generate_kpis_for_framework(...)` from `kpi_generator.py`.
- Handles top-level process exit codes and terminal summary output.

### `config.py`
- Centralized runtime configuration.
- Loads environment (`.env`) via `load_dotenv()`.
- Provides:
  - DB config (`DB_CONFIG`) (currently env-first, then fallback),
  - OpenAI config (`OPENAI_API_KEY`, `OPENAI_MODEL`) (env-first, then fallback),
  - output directory and cache paths,
  - feature flags for optional dependencies,
  - shared in-memory globals (`CURRENT_SCHEMA_INFO`, `EVIDENCE_DATAFRAMES`).

### `kpi_generator.py`
- Main orchestration layer.
- Contains:
  - `generate_kpis_for_framework(...)`: full pipeline controller.
  - `generate_kpis_from_module_summaries(...)`: module-level LLM generation loop with chunk/retry support.
  - upload-trigger refresh helpers for full or targeted refresh.

### `database.py`
- Database IO and schema introspection.
- Handles:
  - DB connection,
  - framework metadata retrieval,
  - schema and row-count extraction,
  - retrieval of core module tables and additional tables,
  - ensuring `kpis.Module` column exists,
  - upsert behavior for generated KPIs,
  - schema metadata persistence.

### `module_summaries.py`
- Converts database data into per-module JSON summaries for prompting.
- Produces module artifacts like:
  - `module_summary_<framework>_<module>_<timestamp>.json`
- Includes chunking helpers for large prompt contexts.

### `evidence.py`
- Evidence preparation and linking.
- Adds S3 evidence snippets to module summaries.
- Builds lookup/index structures used later for source alignment.

### `s3_handler.py`
- S3 document discovery and extraction helpers.
- Cache read/write utilities for S3 document metadata and extracted content.
- DataFrame storage for S3-backed evidence datasets.

### `ollama_client.py`
- LLM interaction layer (OpenAI chat completions in current implementation).
- Sends prompt payloads and parses model output into KPI objects.
- Includes JSON extraction/repair handling and retry-compatible behavior.

### `kpi_validation.py`
- KPI post-generation quality gate.
- Performs:
  - formula sanitization,
  - source (`FromWhereToAccessData`) correction/normalization,
  - evidence/schema alignment,
  - deduplication and consistency checks.

### `formula_evaluator.py`
- Computes runtime KPI values from available in-memory evidence/dataframes.
- Applies formula-safe evaluation rules to populate KPI `Value`.

### `synthetic_data.py`
- Fallback path when a KPI lacks executable/compatible source data.
- Generates synthetic datasets with LLM guidance.
- Attempts to upload synthetic artifacts (CSV/PDF) and bind them to KPI sources.

### `__init__.py`
- Package exports.
- Publicly exposes core generation/refresh functions.

### `test_moduleimport.py`
- Diagnostic utility for import-path troubleshooting.

---

## 3) Runtime Flow (Practical Step-by-Step)

Below is the actual runtime flow when invoking:

`python generateFrameworkKpi.py --framework-id <id>`

### Step 0: Startup and argument parsing
1. `generateFrameworkKpi.py` starts.
2. CLI args are parsed.
3. `kpi_generator.generate_kpis_for_framework(...)` is called.

### Step 1: Database connection
1. `database.connect_to_database()` is called with `DB_CONFIG`.
2. On success, pipeline continues.
3. On failure, process exits with runtime error.

### Step 2: Framework metadata fetch
1. `database.get_framework_info(...)` validates that framework exists.
2. If framework is missing, pipeline stops.

### Step 3: S3 evidence fetch
1. `s3_handler.get_s3_documents(...)` fetches and filters S3 docs.
2. Cache may be used to avoid repeated heavy extraction.

### Step 4: Framework core data retrieval
1. `database.get_framework_data(...)` loads major module tables:
   - policies, subpolicies, compliance, risk, incidents, audit.

### Step 5: Schema retrieval and metadata save
1. `database.get_database_schema(...)` introspects all tables/columns.
2. Framework row counts are applied where `FrameworkId` exists.
3. Schema snapshot is persisted via `save_schema_metadata(...)`.
4. Shared schema cache (`CURRENT_SCHEMA_INFO`) is updated.

### Step 6: Other table data retrieval
1. `database.get_other_tables_data(...)` reads non-core tables.
2. Excludes known core tables and target `kpis` table.
3. Adds broad contextual information for prompts.

### Step 7: Module summary generation
1. `module_summaries.create_module_summaries(...)` builds per-module JSON summaries.
2. Writes one file per module in output directory.

### Step 8: OpenAI configuration verification
1. Checks SDK availability and API key presence.
2. Reads active model from config.

### Step 9: KPI generation from summaries
1. `generate_kpis_from_module_summaries(...)` scans module summaries.
2. Keeps latest file per module and optionally applies module filter.
3. Injects S3 evidence into each summary (`evidence.attach_s3_evidence_to_summary`).
4. Chunks oversized module payloads.
5. For each chunk, calls `ollama_client.generate_kpis_with_ollama(...)` with retries.
6. Aligns output with evidence and schema.
7. Validates/sanitizes formulas and removes duplicates.
8. Aggregates all modules' KPI objects.

### Step 10: Post-processing and persistence
1. Global deduplication.
2. Formula validation pass.
3. `FromWhereToAccessData` enforcement pass.
4. Synthetic source injection for schema-plan gaps:
   - `synthetic_data.ensure_synthetic_sources_for_schema_plan_kpis(...)`
5. KPI value computation:
   - `formula_evaluator.populate_kpi_values_from_memory(...)`
6. Database upsert:
   - `database.write_kpis_to_database(...)`
7. Returns structured result with KPI list and upsert count.

---

## 4) Theoretical Architecture (Why Each Layer Exists)

### A) Separation of concerns
The package is split into layers so each concern can evolve independently:

- **Input/config layer** (`config.py`, CLI)
- **Data acquisition layer** (`database.py`, `s3_handler.py`)
- **Context shaping layer** (`module_summaries.py`, `evidence.py`)
- **Generation layer** (`ollama_client.py`)
- **Quality/safety layer** (`kpi_validation.py`)
- **Execution/value layer** (`formula_evaluator.py`, `synthetic_data.py`)
- **Persistence layer** (`database.write_kpis_to_database`)

This minimizes coupling and improves testability and debugging.

### B) Retrieval-Augmented KPI Generation pattern
Conceptually this is a RAG-style KPI system:

1. Retrieve relevant structured + unstructured context.
2. Compress/shape context into module summaries.
3. Ask LLM for KPI candidates.
4. Ground and constrain outputs against schema/evidence.
5. Evaluate formulas against available data.

### C) Deterministic hardening after probabilistic generation
LLM output is probabilistic, so deterministic post-steps are critical:

- schema conformance,
- source-path normalization,
- formula sanitization,
- duplicate elimination,
- DB-safe upsert.

### D) Fallback strategy for missing data
If a KPI formula cannot be satisfied with live sources, synthetic fallback attempts to keep KPI execution feasible by generating structured surrogate datasets.

---

## 5) Inputs and Outputs

## Inputs
- Framework ID (`--framework-id`)
- Optional module filter (`--modules`)
- Optional S3 document limit (`--max-s3-docs`)
- `.env` / settings configuration for DB and OpenAI

## Intermediate outputs
- Module summary JSON files
- Schema metadata JSON
- S3 caches

## Final outputs
- Upserted rows in DB `kpis` table
- Runtime result object:
  - generated KPI list,
  - upsert count,
  - framework info metadata.

---

## 6) Common Failure Points in Current Flow

1. **Config parse problems** (`.env` malformed)  
   - causes key/model/DB values to be misread.

2. **Model mismatch**  
   - invalid `OPENAI_MODEL` causes API 400 invalid model.

3. **Credentials/auth issues**  
   - invalid `OPENAI_API_KEY` causes API 401.

4. **Import/environment mismatch**  
   - direct-script execution without correct package context causes import failures.

5. **Synthetic upload unavailable**  
   - if upload helper is unavailable, synthetic dataset cannot be persisted to S3.

---

## 7) Current Behavioral Notes

- Pipeline is verbose by design (detailed terminal progress logs).
- Large module contexts are chunked before LLM calls.
- Retry loops are used for unstable/empty model responses.
- Deduplication happens both per-module and globally.
- DB upsert updates existing KPI by `(FrameworkId, Name)` and inserts otherwise.

---

## 8) Minimal Execution Examples

```bash
# Default run
python generateFrameworkKpi.py

# Framework-specific run
python generateFrameworkKpi.py --framework-id 970

# Module-limited run
python generateFrameworkKpi.py --framework-id 970 --modules audit,policies

# Limit S3 scope
python generateFrameworkKpi.py --framework-id 970 --max-s3-docs 5
```

