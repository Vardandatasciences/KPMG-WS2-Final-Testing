"""
OpenAI API client for KPI generation
"""
import json
import re
import time
from typing import Dict, Any, List, Optional

from .config import (
    OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS,
    TEMPERATURE, OPENAI_AVAILABLE, OPENAI_CLIENT
)

if OPENAI_AVAILABLE:
    from openai import OpenAI


def _escape_newlines_in_json_strings(raw_text: str) -> str:
    """Ensure any literal newlines inside JSON string values are escaped as \\n."""
    result_chars = []
    in_string = False
    escape_next = False

    for ch in raw_text:
        if in_string:
            if escape_next:
                result_chars.append(ch)
                escape_next = False
                continue

            if ch == '\\':
                result_chars.append(ch)
                escape_next = True
                continue

            if ch == '"':
                result_chars.append(ch)
                in_string = False
                continue

            if ch in ('\r', '\n'):
                result_chars.append('\\n')
                continue

            result_chars.append(ch)
            continue

        if ch == '"':
            in_string = True
            result_chars.append(ch)
        else:
            result_chars.append(ch)

    return ''.join(result_chars)


def extract_json_from_text(text):
    """Enhanced JSON extraction with auto-repair for truncated responses."""
    print(f"[INFO] [JSON_EXTRACT] Starting JSON extraction from response...")
    if not text:
        print(f"[INFO] [JSON_EXTRACT] No text provided")
        return None

    original_length = len(text)
    print(f"[INFO] [JSON_EXTRACT] Response length: {original_length} characters")

    # Save original for debugging
    original_text = text
    text = _escape_newlines_in_json_strings(text.strip())

    # Try direct parsing first
    try:
        parsed = json.loads(text)
        print(f"[INFO] [JSON_EXTRACT] Successfully parsed JSON")
        return json.dumps(parsed)
    except json.JSONDecodeError as e:
        print(f"[INFO] [JSON_EXTRACT] Direct parsing failed: {e}")

    # Find JSON structure
    start_idx = text.find('{')
    if start_idx == -1:
        print(f"[ERROR] [JSON_EXTRACT] No JSON object found")
        return None

    # Extract from first { to end
    json_str = _escape_newlines_in_json_strings(text[start_idx:])

    # Try to auto-repair truncated JSON
    try:
        # Count brackets
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')

        # Check if we have an unclosed string
        quote_count = 0
        in_string = False
        for i, char in enumerate(json_str):
            if char == '"' and (i == 0 or json_str[i - 1] != '\\'):
                quote_count += 1
                in_string = not in_string

        # Fix unclosed strings
        if quote_count % 2 != 0:
            json_str += '"'
            print(f"[INFO] [JSON_EXTRACT] Added missing closing quote")

        # Add missing brackets/braces
        missing_braces = open_braces - close_braces
        missing_brackets = open_brackets - close_brackets

        if missing_brackets > 0:
            json_str += ']' * missing_brackets
            print(f"[INFO] [JSON_EXTRACT] Added {missing_brackets} missing closing brackets")

        if missing_braces > 0:
            json_str += '}' * missing_braces
            print(f"[INFO] [JSON_EXTRACT] Added {missing_braces} missing closing braces")

        # Try parsing the repaired JSON
        parsed = json.loads(json_str)
        print(f"[INFO] [JSON_EXTRACT] Successfully repaired and parsed truncated JSON")
        return json.dumps(parsed)

    except Exception as e:
        print(f"[ERROR] [JSON_EXTRACT] Failed to repair JSON: {e}")
        print(f"[DEBUG] [JSON_EXTRACT] Attempted JSON (first 500 chars): {json_str[:500]}")

        # Last resort: return minimal valid JSON
        print(f"[INFO] [JSON_EXTRACT] Returning empty KPI array as fallback")
        return '{"kpis":[]}'


def generate_kpis_with_ollama(
    data_summary,
    category_name="",
    schema_info=None,
    existing_kpi_names=None,
    framework_id=None,
    framework_info=None,
    framework_only=False,
    s3_evidence=None,
):
    """Generate KPIs using OpenAI API."""
    
    if not OPENAI_AVAILABLE:
        print("[ERROR] OpenAI SDK not available. Install with: pip install openai")
        return []
    
    if not OPENAI_API_KEY:
        print("[ERROR] OPENAI_API_KEY not configured")
        return []

    global OPENAI_CLIENT
    if OPENAI_CLIENT is None:
        OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

    category_context = f"Focus on {category_name} " if category_name else ""

    # Minimal framework metadata
    framework_name = "Unknown Framework"
    if framework_info and isinstance(framework_info, dict):
        framework_name = framework_info.get('FrameworkName') or framework_name

    existing_names_text = ""
    if existing_kpi_names:
        existing_names_text = f"""Avoid duplicate names: {', '.join(existing_kpi_names)}"""

    empty_response_literal = '{"kpis":[]}'

    if not framework_only:
        print("[INFO] [PROMPT] framework_only flag disabled; using framework-native prompt anyway.")

    s3_evidence_section = ""
    if s3_evidence:
        ranked_evidence = []
        for evidence in s3_evidence[:15]:
            ranked_evidence.append(
                {
                    "key": evidence.get("key"),
                    "bucket": evidence.get("bucket"),
                    "content_type": evidence.get("content_type"),
                    "excerpt": (evidence.get("excerpt") or "")[:600],
                }
            )
        if ranked_evidence:
            evidence_lines = "\n".join(
                f"- {json.dumps(ev, ensure_ascii=False)}" for ev in ranked_evidence
            )
            s3_evidence_section = (
                "═══════════════════════════════════════════════════════════════════════\n"
                "S3 EVIDENCE SNAPSHOTS (TOP 15)\n"
                "═══════════════════════════════════════════════════════════════════════\n"
                f"{evidence_lines}\n\n"
            )

    prompt = f"""You are a senior GRC strategist and regulatory SME. Design the definitive KPI portfolio for the "{framework_name}" framework (FrameworkId {framework_id}).

{s3_evidence_section}═══════════════════════════════════════════════════════════════════════
PHASE 1 – DOMAIN SENSE-MAKING (do NOT output)
═══════════════════════════════════════════════════════════════════════
- Deduce the industry vertical, operating environment, and regulatory intent implied by "{framework_name}" (e.g., payment security, prudential capital, medical device quality).
- Identify mandated authorities, requirement families / clauses, validation artifacts, and audit/testing cadences referenced by this framework.
- List the archetypal control owners, assurance teams, external assessors, and executive stakeholders who consume these KPIs.

- If the framework name is ambiguous, expand it into its fully qualified regulatory title before proceeding.

═══════════════════════════════════════════════════════════════════════
PHASE 2 – PORTFOLIO ARCHITECTURE
═══════════════════════════════════════════════════════════════════════
- Produce exactly 12 KPIs that collectively evidence compliance status, control design & operating effectiveness, incident/remediation responsiveness, governance oversight, and continuous improvement for "{framework_name}".
- Every KPI name should read like an executive-friendly title anchored to the framework (e.g., "Basel III Framework: Liquidity Risk Exposure"). Avoid raw control codes (e.g., "BIS.239.SL.LAG") unless the code is part of a longer descriptive title.
- Ensure the 12 KPIs span different personas: regulator-facing reporting, CISO/Chief Compliance dashboards, control operator views, audit committees, and frontline remediation leads.
- Balance leading vs lagging indicators and include at least one trend or maturity index when the framework expects ongoing attestation.

═══════════════════════════════════════════════════════════════════════
PHASE 3 – DATA & EVIDENCE BLUEPRINT
═══════════════════════════════════════════════════════════════════════
- For every KPI, define a precise calculation using pandas-friendly expressions (e.g., "(ResolvedWithinSLA == 'Yes').mean()", "(NonComplianceCount.sum() / ControlsTested.sum())", "(LiquidityRiskExposure - Threshold).clip(lower=0).sum()"). Do NOT emit SQL, and do not default to simple ".mean()"—select the aggregation or transformation that best represents the KPI (ratios, weighted scores, sums, boolean rates, rolling stats, thresholds, etc.).
- When existing evidence datasets are sufficient, reference the relevant column names exactly as they appear in the data and cite the supporting S3 document (bucket/key). Keep formulas limited to Series operations a data engineer can execute directly.
- If no dataset yet exists, emit a schema plan: describe the target structure and still express the intended calculation in human-readable terms (no placeholder math).
- Review the 's3_evidence' array to understand what artefacts are already available and reuse their column names and context in both the formula and FromWhereToAccessData.
- When data is missing, design the schema plan with the three labelled sections:
  "Schema plan ->" describe table purpose, accountable owner, refresh cadence, and enumerate each column with data type, nullability, keys, lineage, and data-quality rules.
  "Data acquisition ->" outline upstream systems, ingestion method (ETL/API/manual upload), integration cadence, validation checkpoints, and reconciliation or attestation controls.
  "S3 evidence plan ->" prescribe document types, producing team, filename pattern, and the specific artefact contents or data extractions reviewers must upload (e.g., FDA 483 response packages detailing CAPA milestones).
- Recommend S3 evidence uploads aligned to the framework, highlighting the exact data points or attestations auditors should extract (cross-reference existing excerpts when possible).
- Treat any raw rows inside FRAMEWORK DATA REPOSITORY or S3 excerpts as read-only evidence to confirm availability; do NOT let row-level content influence KPI naming or descriptions—anchor those purely in regulatory vocabulary.

═══════════════════════════════════════════════════════════════════════
PHASE 4 – OUTPUT SPECIFICATION
═══════════════════════════════════════════════════════════════════════
- Output JSON with exactly 12 entries in "kpis".
- Keep each field concise (≤400 characters). Use short clauses separated by ';' instead of paragraphs.
- Each KPI must contain:
  * Name – fully anchored in framework vocabulary (include clause/control IDs where applicable).
  * Description – articulate strategic purpose, success/failure interpretation, and primary stakeholder for "{framework_name}".
  * Formula – explicit pandas-friendly expression (no SQL). Reference column names exactly as they appear in the dataset, choosing an operation that matches the KPI semantics (percentages, ratios, sums, weighted metrics, threshold breaches, rolling trends, etc.) rather than automatically falling back to simple ".mean()".
  * DisplayType – one of: Gauge, Bar Chart, Line Chart, Metric Card, Table.
  * FromWhereToAccessData – single STRING value. Either list concrete evidence datasets (e.g., "s3://bucket/key -> columns: ColumnA, ColumnB") with short usage notes, or, if data is missing, concatenate the three sections exactly as: "Schema plan -> ... ; Data acquisition -> ... ; S3 evidence plan -> ...". When referencing existing S3 artefacts, cite the bucket/key (or filename) along with the data points pulled from the excerpt. Escape every newline inside string values as \\n. Do not omit any section.
- All JSON object keys and string values MUST be wrapped in double quotes.
- Formula and FromWhereToAccessData must reference identical column names and dataset identifiers when data exists. Keep Formula free of SQL keywords.
- If any KPI cannot be grounded in the framework's lexicon, discard it and create another that can.
═══════════════════════════════════════════════════════════════════════
NON-NEGOTIABLE NAME RULES
═══════════════════════════════════════════════════════════════════════
- Every KPI Name must be non-empty, unique, and ≤120 characters.
- If you would otherwise emit an empty name or "Unnamed", craft a descriptive title that anchors to the framework (e.g., "{framework_name}: Evidence Readiness Index").
{existing_names_text}

Return ONLY raw JSON (no markdown, no prose) starting with '{{' and ending with '}}'.
"""

    try:
        start_time = time.time()
        print(f"[INFO] [API_CALL] Calling OpenAI API")
        print(f"[INFO] [API_CALL] Model: {OPENAI_MODEL}")
        print(f"[INFO] [API_CALL] Category: {category_name if category_name else 'Framework-Standard KPIs'}")
        print(f"[INFO] [API_CALL] Payload size: ~{len(prompt)} characters")
        print(f"[INFO] [API_CALL] Sending request...")

        response = OPENAI_CLIENT.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a JSON-only response generator. You MUST output ONLY valid JSON with no exceptions. "
                        "CRITICAL: Your response must start with the character '{' as the very first character. Do NOT include any text, "
                        "explanations, markdown, code blocks, or comments before or after the JSON. Do NOT use ```json or ``` markers. "
                        "Return ONLY the raw JSON object starting with '{' and ending with '}'. Every KPI must include all 5 fields: "
                        "Name, Description, Formula, DisplayType, FromWhereToAccessData. Formulas must be executable pandas-style expressions (no SQL) "
                        "and should reference column names exactly as they appear in the supporting dataset or schema plan. If any KPI would require "
                        "a column that is absent from available evidence, describe the required additions in FromWhereToAccessData instead of inventing names. "
                        "All JSON object keys MUST be wrapped in double quotes, and all newline characters inside any string MUST be escaped as \\n. "
                        f"If you cannot comply, respond exactly with {empty_response_literal}."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"}
        )

        elapsed = time.time() - start_time
        print(f"[INFO] [API_CALL] Request completed in {elapsed:.2f} seconds")

        content = response.choices[0].message.content
        if not content:
            print("[ERROR] [PARSE] No content in OpenAI response")
            return []
        
        print(f"[INFO] [PARSE] Response content length: {len(content)} characters")

        print("[INFO] [PARSE] Attempting to extract JSON from response...")
        json_content = extract_json_from_text(content)

        if not json_content:
            print(f"[ERROR] [PARSE] Could not extract JSON from OpenAI response")
            print(f"[DEBUG] [PARSE] Response content preview (first 500 chars): {content[:500]}")
            return []

        print("[INFO] [PARSE] JSON extracted, loading into Python...")
        parsed_result = json.loads(json_content)
        kpis = parsed_result.get('kpis', [])

        print(f"[INFO] [SUCCESS] Successfully parsed {len(kpis)} KPIs from OpenAI response")
        if kpis:
            print(f"[INFO] [SUCCESS] KPI names: {', '.join([k.get('Name', 'Unnamed')[:40] for k in kpis[:5]])}")
            if len(kpis) > 5:
                print(f"[INFO] [SUCCESS] ... and {len(kpis) - 5} more")

            missing_fields = []
            for idx, kpi in enumerate(kpis, 1):
                if not kpi.get('FromWhereToAccessData'):
                    missing_fields.append(f"KPI {idx}: {kpi.get('Name', 'Unnamed')}")

            if missing_fields:
                print(f"[WARNING] [VALIDATION] {len(missing_fields)} KPIs missing FromWhereToAccessData field")
                for missing in missing_fields[:5]:
                    print(f"[WARNING] [VALIDATION]   - {missing}")
            else:
                print(f"[INFO] [VALIDATION] All {len(kpis)} KPIs have FromWhereToAccessData field")

        return kpis

    except json.JSONDecodeError as e:
        print(f"[ERROR] Error parsing JSON from OpenAI response: {e}")
        print(f"[DEBUG] Response content: {content[:500] if 'content' in locals() else 'N/A'}")
        return []
    except Exception as e:
        print(f"[ERROR] Unexpected error generating KPIs with OpenAI: {e}")
        import traceback
        traceback.print_exc()
        return []
