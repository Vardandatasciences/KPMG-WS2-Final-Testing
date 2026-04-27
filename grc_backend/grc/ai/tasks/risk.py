import json
from typing import Any

from ..types import AIRequestOptions

# ─────────────────────────────────────────────────────────────────────────────
# SCHEMA KEYS
# ─────────────────────────────────────────────────────────────────────────────

# Core flat keys the UI expects for Create Risk AI analysis
FLAT_RISK_ANALYSIS_KEYS = [
    "criticality", "criticalityJustification", "possibleDamage", "possibleDamageJustification",
    "category", "categoryJustification", "riskDescription", "riskDescriptionJustification",
    "riskLikelihood", "riskLikelihoodJustification", "riskImpact", "riskImpactJustification",
    "riskExposureRating", "riskPriority", "riskPriorityJustification", "riskAppetite",
    "riskMitigation", "riskMitigationJustification", "functionalArea", "functionalAreaJustification",
    # Enhanced fields aligned with PDF specification
    "velocityScore", "velocityJustification",
    "confidenceScore", "confidenceJustification",
    "frameworkReference", "aiReasoning", "perFieldRationale",
]

# ─────────────────────────────────────────────────────────────────────────────
# CONFIDENCE SCORE GUIDELINES  (from PDF specification)
# ─────────────────────────────────────────────────────────────────────────────
#
# External article + matching internal data (audit finding, incident) → 72-80%
# External article + partially matching internal profile              → 65-72%
# External article + no internal data but relevant industry           → 55-65%
# Internal incident / audit finding (direct observation)             → 80-92%
# Internal compliance breach (confirmed)                              → 85-95%
# Inferred from document with clear evidence                          → 75-88%
# Inferred from document with limited evidence                        → 60-75%

SOURCE_CONFIDENCE_GUIDELINES = {
    "INCIDENT":   {"range": "80-92%", "note": "Direct internal observation — high confidence."},
    "AUDIT":      {"range": "82-92%", "note": "Confirmed audit finding — high confidence."},
    "COMPLIANCE": {"range": "85-95%", "note": "Confirmed compliance breach — highest confidence."},
    "DOCUMENT":   {"range": "70-88%", "note": "Inferred from document; use higher end if evidence is explicit."},
    "TPRM":       {"range": "72-85%", "note": "Third-party risk assessment data."},
    "EXTERNAL":   {"range": "60-80%", "note": "Use 72-80% if matching internal data exists; 65-72% partial match; 55-65% industry relevance only."},
    "MANUAL":     {"range": "75-90%", "note": "User-entered data — treat as high confidence if detailed."},
    "GENERAL":    {"range": "70-85%", "note": "Mixed source — calibrate to evidence quality."},
}

# ─────────────────────────────────────────────────────────────────────────────
# FIELD-LEVEL GUIDANCE
# ─────────────────────────────────────────────────────────────────────────────

RISK_FIELD_GUIDANCE = {
    "risk": {
        "Criticality": "Return one of: Low, Medium, High, Critical.",
        "PossibleDamage": (
            "Describe concrete damages: data loss volume, downtime duration, financial penalties, "
            "regulatory fines, reputation impact. 2 sentences. Be specific — avoid generic language."
        ),
        "Category": (
            "Return best fit from: Operational, Financial, Strategic, Compliance, Technical, "
            "Reputational, Information Security, Process Risk, Third-Party, Regulatory, Governance."
        ),
        "RiskType": "Return one of: Current, Residual, Inherent, Emerging, Accepted.",
        "BusinessImpact": (
            "Explain business impact in measurable terms: SLA breach %, revenue effect (INR/USD), "
            "regulatory penalty amount, operational downtime. 2 sentences."
        ),
        "RiskDescription": (
            "Write a precise 2-3 sentence description following the pattern: "
            "[Cause] → [Risk Event] → [Consequence]. Include who is affected and the mechanism of harm."
        ),
        "RiskLikelihood": "Return an integer 1-10. 1=Rare (>5 years). 5=Possible (1-2 years). 8=Likely (months). 10=Almost certain (imminent).",
        "RiskImpact": "Return an integer 1-10. 1=Negligible. 5=Significant operational disruption. 8=Major financial/regulatory impact. 10=Catastrophic/existential.",
        "VelocityScore": (
            "Return an integer 1-10 indicating how quickly this risk could materialise if it became active. "
            "1=Slow (years of build-up). 5=Moderate (weeks to months). 8=Fast (days). 10=Instant (hours or less). "
            "External regulatory deadlines, active exploitation trends, and seasonal patterns increase velocity."
        ),
        "RiskExposureRating": "Return a float 0-100. Align with Likelihood × Impact / 10 as a baseline, then adjust for velocity and control effectiveness.",
        "RiskPriority": "Return one of: Low, Medium, High, Critical — based on exposure, criticality, and velocity combined.",
        "RiskMitigation": "Return 3-5 actionable mitigation steps. Each step should name a specific action, not generic advice.",
        "ConfidenceScore": (
            "Return an integer 0-100 reflecting certainty. "
            "Internal direct observations: 80-92%. External news + matching internal data: 72-80%. "
            "External news + partial match: 65-72%. External news only: 55-65%."
        ),
        "FrameworkReference": (
            "Return the most relevant compliance framework reference code, e.g. 'ME 4', 'HRM 2', "
            "'NIST PR.AC-1', 'ISO 27001 A.12.6', 'DPDP-S8.6', 'KYC-AML'. "
            "If the active framework is known from context, use it. Otherwise infer from risk category."
        ),
        "CreatedAt": "Return a plausible assessment date in YYYY-MM-DD format; if unknown, use today.",
        "RiskMultiplierX": "Return a float 0.1-1.5 reflecting weighting factor X, defaulting near 0.5 if unknown.",
        "RiskMultiplierY": "Return a float 0.1-1.5 reflecting weighting factor Y, defaulting near 0.5 if unknown.",
    },
    "risk_instance": {
        "RiskDescription": (
            "Write a precise 3-4 sentence description: what happened, how it happened, who was affected, "
            "and what the immediate consequence was. Follow pattern: [Cause] → [Event] → [Consequence]."
        ),
        "PossibleDamage": (
            "Describe specific damages with quantities where possible: e.g. '8,400 records exposed', "
            "'INR 15L potential fine', '4-hour downtime'. 2-3 sentences."
        ),
        "RiskPriority": "Return one of: Low, Medium, High, Critical — based on severity, exposure, and urgency.",
        "Criticality": "Return one of: Low, Medium, High, Critical — considering operational, financial, compliance, and reputational impact together.",
        "Category": (
            "Return best fit from: Operational, Financial, Strategic, Compliance, Technical, "
            "Reputational, Information Security, Process Risk, Third-Party, Regulatory, Governance."
        ),
        "Origin": "Return one of: Internal, External, Third-Party, Regulatory, Market, Operational.",
        "RiskLikelihood": "Return an integer 1-10 based on frequency of occurrence, control effectiveness, and environmental factors.",
        "RiskImpact": "Return an integer 1-10 based on financial, operational, reputational, and compliance impact combined.",
        "VelocityScore": (
            "Return an integer 1-10 for how quickly this risk instance could escalate or recur. "
            "1=Slow (years). 5=Moderate (weeks). 8=Fast (days). 10=Instant. "
            "Active incidents, regulatory deadlines, and repeated occurrences increase velocity."
        ),
        "RiskExposureRating": "Return a float 0-100. Align with likelihood × impact / 10 as baseline, adjusted for velocity.",
        "RiskMultiplierX": "Return a float 0.1-2.0, defaulting near 1.0.",
        "RiskMultiplierY": "Return a float 0.1-2.0, defaulting near 1.0.",
        "Appetite": "Return one of: Low, Medium, High — based on organisational tolerance for this risk type.",
        "RiskResponseType": "Return one of: Avoid, Mitigate, Transfer, Accept.",
        "RiskResponseDescription": (
            "Provide a 2-3 sentence response strategy with: the specific action to take, "
            "the rationale for choosing this response type, and the expected outcome."
        ),
        "RiskMitigation": "Return a JSON array of 3-5 objects with 'step' and 'description' fields. Steps must be specific and actionable.",
        "RiskType": "Return one of: Current, Residual, Inherent, Emerging, Accepted.",
        "RiskOwner": "Return a specific owner name, role, or department responsible for this risk instance.",
        "BusinessImpact": (
            "Provide a 3-4 sentence business impact covering revenue, SLA, operations, "
            "reputation, or regulatory exposure. Use measurable terms where possible."
        ),
        "ConfidenceScore": (
            "Return an integer 0-100. Direct internal observation: 80-92%. "
            "External news + matching internal data: 72-80%. External news + partial: 65-72%."
        ),
        "FrameworkReference": (
            "Return the specific framework control reference most relevant to this instance, "
            "e.g. 'ME 4', 'NIST PR.AC-1', 'DPDP-S8.6', 'ISO 27001 A.12.6'."
        ),
        "RiskStatus": "Return one of: Not Assigned, Assigned, Approved, Rejected.",
        "MitigationStatus": (
            "Return one of: Pending, Yet to Start, Work In Progress, "
            "Revision Required by Reviewer, Revision Required by User, Completed."
        ),
        "ModifiedMitigations": "Return a JSON array documenting mitigation changes, or [] if none.",
        "RiskFormDetails": "Return a JSON object with structured assessment details: method, sources, assessment_date, notes.",
        "Reviewer": "Return the reviewer name or role, or 'Pending Review' if not known.",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# SHARED REASONING PATTERN INSTRUCTIONS (injected into prompts)
# ─────────────────────────────────────────────────────────────────────────────
_AI_REASONING_INSTRUCTIONS = """
AI REASONING FORMAT — CRITICAL:
Your ai_reasoning field must follow this exact cross-referencing pattern used by expert GRC analysts:

  "[External/source-specific fact with numbers]. Cross-referencing [with internal data / with 
   the organisation's profile]: [specific internal metric or gap that matches]. 
   [Why this creates elevated risk or urgency — the connection between source and risk]."

Examples of GOOD reasoning:
  "NABH suspended 3 hospitals for hand hygiene compliance below 60%. Cross-referencing internal 
   data: our own hand hygiene compliance is 76% — above 60% but below the 85% NABH standard. 
   Audit findings AF-2041 and AF-2063 indicate active infection control gaps, creating real risk 
   of similar enforcement action before next unannounced inspection."

  "RBI penalised 4 PSU banks for KYC overdue >30% and PEP completion <70%. Cross-referencing: 
   our KYC update backlog is 34% overdue and PEP completion is at 68% — our profile closely 
   matches the penalised banks. With 14 banks penalised this FY, enforcement is accelerating."

Examples of BAD reasoning (DO NOT DO THIS):
  "This is a compliance risk because non-compliance can lead to penalties."  ← too generic
  "The organisation should improve its processes."  ← no cross-referencing, no data

ALWAYS cite specific numbers, incident IDs, audit finding references, or percentages when available.
ALWAYS explain WHY the source data is specifically relevant to this organisation's situation.
"""

_RISK_TITLE_INSTRUCTIONS = """
RISK TITLE FORMAT:
Titles must follow this pattern: "[Core Issue] — [What It Means for This Organisation]"

Examples of GOOD titles:
  "KYC/AML Regulatory Penalty Risk — Enforcement Trend Matching Our Profile"
  "Cloud Storage Misconfiguration — KYC Document Exposure Risk"
  "ICU Staffing Ratio Non-Compliance — Industry-Wide Trend Affecting Our Operations"
  "Fire Safety Compliance Risk — Industry Incident Highlights Our Own Gaps"

Examples of BAD titles:
  "Compliance Risk"           ← too vague
  "Data Breach Risk"          ← too generic
  "KYC Non-Compliance"        ← missing the organisational relevance half
"""

_VELOCITY_INSTRUCTIONS = """
VELOCITY SCORE (1-10) — how fast this risk can materialise:
  1-2  = Slow build-up, years before impact (e.g. long-term strategic drift)
  3-4  = Gradual, months to years (e.g. regulatory review cycles)
  5-6  = Moderate, weeks to months (e.g. audit cycle, scheduled inspections)
  7-8  = Fast, days to weeks (e.g. active regulatory enforcement, known deadlines)
  9-10 = Near-instant, hours to days (e.g. active cyber exploitation, imminent deadline)

Factors that INCREASE velocity: hard regulatory deadlines, active exploitation trends,
ongoing enforcement waves, repeated internal incidents, public disclosure already happened.
"""

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_risk_analysis_response(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten AI response so UI gets expected keys. The model often returns data inside
    context[0] or as alternate key names; we extract and normalize to a single flat dict.
    """
    out = dict(raw)
    if not isinstance(out, dict):
        return out

    # 1) Extract from context[0] if the real analysis is nested there
    context = out.get("context")
    if isinstance(context, list) and len(context) > 0:
        inner = context[0]
        if isinstance(inner, dict):
            for key in FLAT_RISK_ANALYSIS_KEYS:
                if key not in out or out.get(key) in (None, ""):
                    if key in inner and inner[key] not in (None, ""):
                        out[key] = inner[key]
            # Also try parsing "Analysis: {...}" from inner.text
            text = inner.get("text") if isinstance(inner.get("text"), str) else ""
            if text and any(k in text for k in ('"criticality"', '"riskLikelihood"', '"velocityScore"')):
                try:
                    start = text.find("Analysis:")
                    if start < 0:
                        start = text.find("{")
                    else:
                        start = text.find("{", start)
                    if start >= 0:
                        depth = 0
                        end = -1
                        for i in range(start, len(text)):
                            if text[i] == "{":
                                depth += 1
                            elif text[i] == "}":
                                depth -= 1
                                if depth == 0:
                                    end = i + 1
                                    break
                        if end > start:
                            parsed = json.loads(text[start:end])
                            if isinstance(parsed, dict):
                                for key in FLAT_RISK_ANALYSIS_KEYS:
                                    if key not in out or out.get(key) in (None, ""):
                                        if key in parsed and parsed[key] not in (None, ""):
                                            out[key] = parsed[key]
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass
        elif isinstance(inner, str):
            try:
                parsed = json.loads(inner)
                if isinstance(parsed, dict):
                    for key in FLAT_RISK_ANALYSIS_KEYS:
                        if key not in out or out.get(key) in (None, ""):
                            if key in parsed and parsed[key] not in (None, ""):
                                out[key] = parsed[key]
            except json.JSONDecodeError:
                pass

    # 2) Map common alternate keys to expected keys
    aliases = [
        ("riskCategory", "category"),
        ("likelihood", "riskLikelihood"),
        ("impact", "riskImpact"),
        ("exposureRating", "riskExposureRating"),
        ("velocity", "velocityScore"),
        ("velocity_score", "velocityScore"),
        ("confidence", "confidenceScore"),
        ("confidence_score", "confidenceScore"),
        ("framework_reference", "frameworkReference"),
        ("framework_ref", "frameworkReference"),
        ("ai_reasoning", "aiReasoning"),
        ("per_field_rationale", "perFieldRationale"),
    ]
    for alt, canonical in aliases:
        if (
            (canonical not in out or out.get(canonical) in (None, ""))
            and alt in out
            and out[alt] not in (None, "")
        ):
            out[canonical] = out[alt]

    # 3) Ensure numeric types for likelihood/impact/velocity/confidence
    for key in ("riskLikelihood", "riskImpact", "velocityScore", "confidenceScore"):
        if key in out and out[key] is not None and out[key] != "":
            try:
                out[key] = int(float(out[key]))
            except (TypeError, ValueError):
                pass

    return out


def _ensure_options(options: AIRequestOptions | None, task_name: str) -> AIRequestOptions:
    if options is None:
        return AIRequestOptions(task_name=task_name)
    options.task_name = task_name
    return options


def _generate_json(service, task_name: str, prompt: str, options: AIRequestOptions | None = None):
    return service.generate_json(
        task_name=task_name,
        prompt=prompt,
        options=_ensure_options(options, task_name),
    )


def _serialize_current_record(current_record: dict[str, Any], allowed_fields: list[str]) -> str:
    filtered = {
        key: current_record.get(key)
        for key in allowed_fields
        if current_record.get(key) not in (None, "", [], {})
    }
    return json.dumps(filtered, indent=2, default=str)


def _build_risk_field_prompt(payload: dict[str, Any]) -> str:
    subject_type = payload.get("subject_type", "risk")
    field_name = payload.get("field_name", "")
    document_context = payload.get("document_context", "")
    current_record = payload.get("current_record", {})
    current_record_fields = payload.get("current_record_fields", [])

    subject_label = "risk instance" if subject_type == "risk_instance" else "risk"
    full_object_label = "risk instance object" if subject_type == "risk_instance" else "risk object"
    guidance = RISK_FIELD_GUIDANCE.get(subject_type, {}).get(field_name, "Return a concise, professional value.")
    current_record_json = _serialize_current_record(current_record, current_record_fields)

    # Add specialised instructions for new fields
    extra_instructions = ""
    if field_name == "VelocityScore":
        extra_instructions = _VELOCITY_INSTRUCTIONS
    elif field_name in ("FrameworkReference", "frameworkReference"):
        extra_instructions = (
            "\nFRAMEWORK REFERENCE EXAMPLES by category:\n"
            "  Compliance / Healthcare: ME 4, HRM 2, COP 3, COP 5, COP 8, FMS 3\n"
            "  Compliance / Banking: KYC-AML, CREDIT-1, FRAUD-1, OUTSRC\n"
            "  Compliance / Data Protection: DPDP-S8.6, DPDP-S9, DPDP-S16, DPDP-S6, DPDP-S8.7\n"
            "  IT Security: NIST PR.AC-1, ISO 27001 A.12.6, CIS Control 7\n"
            "  General: ISO 31000, COSO ERM\n"
        )

    return f"""
You are a GRC analyst. Infer ONLY the field "{field_name}" for this {subject_label}.

CRITICAL: Return ONLY a JSON object with this EXACT structure:
{{"value": <your answer here>, "confidence": 0.0-1.0, "rationale": "brief explanation"}}

DO NOT return:
- A full {full_object_label}
- Multiple fields
- Markdown code blocks
- Explanations outside the JSON

Context (document):
\"\"\"{document_context}\"\"\"

Current {subject_label} (partial):
{current_record_json}

Rules:
- {guidance}
{extra_instructions}
- Return ONLY the JSON object: {{"value": ..., "confidence": ..., "rationale": ...}}
- If you cannot infer, return {{"value": null, "confidence": 0.0, "rationale": "Not enough information"}}.
- Always include a brief rationale explaining your specific decision, citing evidence from context.
- Return ONLY valid JSON, no markdown, no code blocks, no other text.
- The "value" field should contain ONLY the value for {field_name}, nothing else.
"""


# ─────────────────────────────────────────────────────────────────────────────
# TASK: ANALYZE SECURITY INCIDENT
# ─────────────────────────────────────────────────────────────────────────────

def analyze_security_incident_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    incident_description = payload.get("incident_description", "")
    rag_context = payload.get("rag_context", "")
    print(f"[AI-TASK] analyze_security_incident: incident_len={len(incident_description)}, rag_context_len={len(rag_context)}")

    prompt = f"""You are a senior GRC and Enterprise Risk Management expert.

INCIDENT TO ANALYZE:
{incident_description}

ADDITIONAL CONTEXT (internal data, audit findings, related incidents):
{rag_context}

{_AI_REASONING_INSTRUCTIONS}

{_RISK_TITLE_INSTRUCTIONS}

{_VELOCITY_INSTRUCTIONS}

CRITICAL INSTRUCTIONS — READ CAREFULLY:
Return a JSON object with EXACTLY these 24 fields. DO NOT SKIP ANY FIELD.

REQUIRED JSON STRUCTURE (fill ALL fields):
{{
  "criticality": "High|Medium|Low|Critical",
  "criticalityJustification": "2-3 sentences. Reference specific incident characteristics that drive this level.",

  "possibleDamage": "2-3 sentences. Quantify where possible — record counts, downtime hours, penalty amounts, INR/USD values.",
  "possibleDamageJustification": "1-2 sentences explaining your damage estimate methodology.",

  "category": "Information Security|Operational|Compliance|Financial|Strategic|Third-Party|Reputational",
  "categoryJustification": "1-2 sentences citing which aspect of the incident determines the category.",

  "riskDescription": "2-3 sentences. Pattern: [Cause] → [Risk Event] → [Consequence]. Name the specific system, process, or control that failed.",
  "riskDescriptionJustification": "1-2 sentences explaining the cause-event-consequence logic.",

  "riskLikelihood": 6,
  "riskLikelihoodJustification": "2-3 sentences. Reference: frequency of similar incidents, control gaps, environment. 1=Rare, 10=Near-certain.",

  "riskImpact": 7,
  "riskImpactJustification": "2-3 sentences. Reference: affected records/systems, regulatory implications, financial exposure. 1=Negligible, 10=Catastrophic.",

  "velocityScore": 5,
  "velocityJustification": "1-2 sentences. Explain how quickly this risk could recur or escalate. Reference any deadlines, active trends, or ongoing gaps.",

  "riskExposureRating": "High|Medium|Low|Elevated|Critical",
  "riskPriority": "P1|P2|P3|High|Medium|Low",
  "riskPriorityJustification": "1-2 sentences combining likelihood, impact, velocity, and any regulatory urgency.",

  "riskAppetite": "Exceeds Appetite|Within Appetite|Below Appetite",

  "riskMitigation": ["specific action 1", "specific action 2", "specific action 3", "specific action 4"],
  "riskMitigationJustification": "2-3 sentences explaining how this mitigation set addresses both root cause and consequence.",

  "functionalArea": "HR|Finance|IT|Engineering|Legal|Sales|Marketing|Operations|Security|Compliance",
  "functionalAreaJustification": "1-2 sentences explaining primary ownership and secondary impact areas.",

  "confidenceScore": 85,
  "confidenceJustification": "1 sentence. For direct internal incidents: 80-92%. Explain what evidence drives this score.",

  "frameworkReference": "e.g. NIST PR.AC-1 or ISO 27001 A.12.6 or DPDP-S8.6 — most relevant control reference",

  "aiReasoning": "Follow the cross-referencing format: [Incident facts with numbers]. Cross-referencing [with internal context]: [specific internal metric/gap]. [Why this is elevated risk/urgency].",

  "perFieldRationale": {{
    "criticality": "What in the incident data drove this criticality rating?",
    "riskLikelihood": "What frequency or control-gap evidence set this score?",
    "riskImpact": "What specific impact factors determined this score?",
    "velocityScore": "What makes this risk fast or slow to materialise?",
    "category": "Which incident characteristic determines the category?",
    "riskDescription": "How does the cause→event→consequence chain apply here?",
    "riskMitigation": "Why were these specific mitigations chosen over alternatives?",
    "frameworkReference": "Why is this the most relevant framework control?"
  }}
}}

VALIDATION CHECKLIST — VERIFY BEFORE RESPONDING:
✓ All 24 fields present and non-empty
✓ riskLikelihood, riskImpact, velocityScore are integers 1-10
✓ confidenceScore is an integer 0-100 (internal incidents: 80-92%)
✓ riskMitigation is an array with 3-5 SPECIFIC actionable items (not generic advice)
✓ aiReasoning uses the cross-referencing format with specific numbers
✓ All justification fields cite specific evidence from the incident
✓ Risk title (in riskDescription) follows: [Issue] — [Org-specific implication]
✓ JSON is valid (no trailing commas, proper quotes)

Return ONLY the JSON object. NO text outside the JSON.
"""
    result = _generate_json(service, "risk.analyze_security_incident", prompt, options)
    print(f"[AI-TASK] analyze_security_incident: DONE - raw result_keys={list(result.keys()) if isinstance(result, dict) else 'n/a'}")

    if isinstance(result, dict):
        result = _normalize_risk_analysis_response(result)
        print(f"[AI-TASK] analyze_security_incident: after normalize - result_keys={list(result.keys())}")
        missing = [k for k in FLAT_RISK_ANALYSIS_KEYS if k not in result or result.get(k) in (None, "")]
        if missing:
            print(f"[AI-TASK] analyze_security_incident: WARNING - still missing after normalize: {missing}")
            _fill_missing_risk_fields(result, incident_description)
            print(f"[AI-TASK] analyze_security_incident: filled missing fields, final_keys={list(result.keys())}")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# TASK: INFER SINGLE RISK FIELD
# ─────────────────────────────────────────────────────────────────────────────

def infer_risk_field_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    field_name = payload.get("field_name", "")
    print(f"[AI-TASK] infer_risk_field: field={field_name}")
    prompt = _build_risk_field_prompt(payload)
    result = _generate_json(service, "risk.infer_field", prompt, options)
    print(f"[AI-TASK] infer_risk_field: DONE - field={field_name}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# TASK: INGEST RISK DOCUMENT
# ─────────────────────────────────────────────────────────────────────────────

def ingest_risk_document_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    document_text = payload.get("document_text", "")
    print(f"[AI-TASK] ingest_risk_document: document_len={len(document_text)}")

    prompt = f"""
You are a senior GRC risk specialist. Read the following document and extract a comprehensive list
of risks suitable for a risk register.

{_RISK_TITLE_INSTRUCTIONS}

{_AI_REASONING_INSTRUCTIONS}

{_VELOCITY_INSTRUCTIONS}

CONFIDENCE SCORE GUIDANCE FOR DOCUMENT INGESTION:
- Explicit statement in document → 82-90%
- Clearly implied by document content → 72-82%
- Inferred from partial evidence → 62-72%

Return ONLY a JSON array of risk objects with this complete structure:
[
  {{
    "RiskTitle": "Follow pattern: [Core Issue] — [Org-specific implication]",
    "Criticality": "Low|Medium|High|Critical",
    "PossibleDamage": "Specific damages with quantities where possible. 2 sentences.",
    "Category": "Operational|Financial|Strategic|Compliance|Technical|Reputational|Information Security|Process Risk|Third-Party|Regulatory|Governance",
    "RiskType": "Current|Residual|Inherent|Emerging|Accepted",
    "BusinessImpact": "Measurable business impact: revenue, SLA, regulatory penalties. 2 sentences.",
    "RiskDescription": "Cause → Event → Consequence pattern. Name specific systems, processes, controls. 2-3 sentences.",
    "RiskLikelihood": 1,
    "RiskImpact": 1,
    "VelocityScore": 5,
    "RiskExposureRating": 0.0,
    "RiskPriority": "Low|Medium|High|Critical",
    "RiskMitigation": "3-5 specific, actionable mitigation steps — not generic advice.",
    "FrameworkReference": "Most relevant control reference, e.g. ME 4, NIST PR.AC-1, DPDP-S8.6",
    "ConfidenceScore": 75,
    "AiReasoning": "Cross-referencing format: [Document fact with numbers]. [Why this creates risk]. [Specific gap or exposure].",
    "FunctionalArea": "IT|Finance|HR|Operations|Legal|Compliance|Security|etc",
    "CreatedAt": "YYYY-MM-DD",
    "RiskMultiplierX": 0.5,
    "RiskMultiplierY": 0.5,
    "PerFieldRationale": {{
      "RiskTitle": "Why this title was chosen",
      "Criticality": "What document evidence drove criticality",
      "RiskLikelihood": "What frequency/control evidence set this",
      "RiskImpact": "What impact factors determined this score",
      "VelocityScore": "What makes this risk fast/slow to materialise",
      "FrameworkReference": "Why this framework control is most relevant",
      "RiskMitigation": "Why these specific mitigations address the root cause"
    }}
  }}
]

Rules:
- Infer risks DIRECTLY from document content — do not add generic industry risks not supported by the text.
- RiskTitle must be specific and descriptive — follow the naming pattern above.
- RiskLikelihood and RiskImpact must be integers 1-10.
- VelocityScore must be an integer 1-10.
- ConfidenceScore must be an integer 0-100.
- RiskExposureRating must be a float 0-100, consistent with likelihood × impact / 10.
- AiReasoning must cite specific evidence from the document.
- Return ONLY the JSON array — no markdown, no comments, no extra keys.

DOCUMENT:
\"\"\"{document_text}\"\"\"
"""
    result = _generate_json(service, "risk.ingest_risk_document", prompt, options)

    # Normalize LLM output
    risks = []
    if isinstance(result, list):
        print(f"[AI-RISK] ingest_risk_document_task: model returned list with {len(result)} item(s)")
        risks = [item for item in result if isinstance(item, dict)]
    elif isinstance(result, dict):
        nested_risks = []
        for key, value in result.items():
            if isinstance(value, dict) and any(
                field in value for field in ["RiskTitle", "Criticality", "RiskDescription"]
            ):
                nested_risks.append(value)

        if nested_risks:
            print(f"[AI-RISK] ingest_risk_document_task: extracted {len(nested_risks)} risks from nested structure")
            risks = nested_risks
        elif any(field in result for field in ["RiskTitle", "Criticality", "RiskDescription"]):
            print("[AI-RISK] ingest_risk_document_task: model returned single risk dict, wrapping in list")
            risks = [result]
        else:
            print("[AI-RISK] ingest_risk_document_task: unrecognised dict structure, returning empty list")
            return []
    else:
        print(f"[AI-RISK] ingest_risk_document_task: unexpected result type {type(result)}, returning empty list")
        return []

    schema_fields = [
        "RiskTitle", "Criticality", "PossibleDamage", "Category", "RiskType",
        "BusinessImpact", "RiskDescription", "RiskLikelihood", "RiskImpact",
        "VelocityScore", "RiskExposureRating", "RiskPriority", "RiskMitigation",
        "FrameworkReference", "ConfidenceScore", "AiReasoning", "FunctionalArea",
        "CreatedAt", "RiskMultiplierX", "RiskMultiplierY", "PerFieldRationale",
    ]

    enriched: list[dict[str, Any]] = []
    for idx, item in enumerate(risks, start=1):
        print(f"[AI-RISK] Enriching risk #{idx} with per-field metadata")
        per_field: dict[str, Any] = {}
        confidence = item.get("ConfidenceScore", 80)
        try:
            confidence_float = float(confidence) / 100.0
        except (TypeError, ValueError):
            confidence_float = 0.80

        for field in schema_fields:
            value = item.get(field)
            if value not in (None, "", [], {}):
                # Use per-field rationale from the model if available
                field_rationale = ""
                per_field_rationale = item.get("PerFieldRationale", {})
                if isinstance(per_field_rationale, dict):
                    field_rationale = per_field_rationale.get(field, "")

                per_field[field] = {
                    "source": "AI_GENERATED",
                    "confidence": confidence_float,
                    "rationale": field_rationale or "Generated from document context by risk ingestion task.",
                }
                print(f"[AI-RISK]   Field '{field}' generated: {str(value)[:120]}")

        item.setdefault("_meta", {})
        item["_meta"]["per_field"] = per_field
        print(
            f"[AI-RISK]   Metadata summary for risk #{idx}: "
            f"{len(per_field)} fields tagged as AI_GENERATED"
        )
        enriched.append(item)

    print(f"[AI-RISK] ingest_risk_document_task: returning {len(enriched)} enriched risk(s)")
    return enriched


# ─────────────────────────────────────────────────────────────────────────────
# TASK: INGEST RISK INSTANCE DOCUMENT
# ─────────────────────────────────────────────────────────────────────────────

def ingest_risk_instance_document_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    document_text = payload.get("document_text", "")
    print(f"[AI-TASK] ingest_risk_instance_document: document_len={len(document_text)}")

    prompt = f"""
You are a senior GRC risk specialist. Read the following document and extract a list of risk
instances suitable for a risk instance register. Risk instances are specific, concrete occurrences
or near-misses, not generic risk categories.

{_RISK_TITLE_INSTRUCTIONS}

{_AI_REASONING_INSTRUCTIONS}

{_VELOCITY_INSTRUCTIONS}

CONFIDENCE SCORE GUIDANCE:
- Explicit incident description → 82-92%
- Clearly implied by document → 72-82%
- Inferred from partial evidence → 62-72%

Return ONLY a JSON array of risk instance objects with this structure:
[
  {{
    "RiskTitle": "Follow pattern: [Specific Incident/Issue] — [Consequence or Gap Revealed]",
    "RiskDescription": "Cause → Event → Consequence. Name specific systems/processes. What happened, who affected, immediate consequence. 3-4 sentences.",
    "PossibleDamage": "Specific quantified damages: record counts, downtime hours, financial penalties. 2-3 sentences.",
    "RiskPriority": "Low|Medium|High|Critical",
    "Criticality": "Low|Medium|High|Critical",
    "Category": "Operational|Financial|Strategic|Compliance|Technical|Reputational|Information Security|Process Risk|Third-Party|Regulatory|Governance",
    "Origin": "Internal|External|Third-Party|Regulatory|Market|Operational",
    "RiskLikelihood": 1,
    "RiskImpact": 1,
    "VelocityScore": 5,
    "RiskExposureRating": 0.0,
    "RiskMultiplierX": 1.0,
    "RiskMultiplierY": 1.0,
    "Appetite": "Low|Medium|High",
    "RiskResponseType": "Avoid|Mitigate|Transfer|Accept",
    "RiskResponseDescription": "Specific response strategy with action, rationale, expected outcome. 2-3 sentences.",
    "RiskMitigation": [
      {{"step": "Step title", "description": "Specific actionable description"}},
      {{"step": "Step title", "description": "Specific actionable description"}},
      {{"step": "Step title", "description": "Specific actionable description"}}
    ],
    "RiskType": "Current|Residual|Inherent|Emerging|Accepted",
    "RiskOwner": "Specific role or department",
    "BusinessImpact": "Revenue, SLA, operations, reputation, regulatory exposure in measurable terms. 3-4 sentences.",
    "FrameworkReference": "Most relevant control reference, e.g. NIST PR.AC-1, ISO 27001 A.12.6, DPDP-S8.6",
    "ConfidenceScore": 80,
    "AiReasoning": "Cross-referencing format: [Document facts with numbers]. [Internal profile match if present]. [Why this creates elevated risk].",
    "RiskStatus": "Not Assigned|Assigned|Approved|Rejected",
    "MitigationStatus": "Pending|Yet to Start|Work In Progress|Revision Required by Reviewer|Revision Required by User|Completed",
    "ModifiedMitigations": [],
    "RiskFormDetails": {{"method": "", "sources": "", "assessment_date": "", "notes": ""}},
    "Reviewer": "Pending Review",
    "PerFieldRationale": {{
      "RiskTitle": "Why this title",
      "RiskDescription": "How cause→event→consequence applies",
      "Criticality": "What evidence drove this",
      "RiskLikelihood": "What frequency/control evidence set this",
      "RiskImpact": "What impact factors determined this",
      "VelocityScore": "What makes this fast/slow",
      "FrameworkReference": "Why this framework control",
      "RiskMitigation": "Why these specific mitigations"
    }}
  }}
]

Rules:
- Extract CONCRETE instances — specific events, incidents, near-misses, or identified control failures.
- RiskLikelihood and RiskImpact must be integers 1-10.
- VelocityScore must be an integer 1-10.
- ConfidenceScore must be an integer 0-100.
- RiskExposureRating must be a float 0-100.
- RiskMitigation must be a JSON array of objects with 'step' and 'description' keys (min 3 items).
- AiReasoning must cite specific data points or incident details from the document.
- Return ONLY the JSON array — no markdown, no comments, no extra keys.

DOCUMENT:
\"\"\"{document_text}\"\"\"
"""
    result = _generate_json(service, "risk.ingest_risk_instance_document", prompt, options)

    # Normalize LLM output
    raw_list: list[dict[str, Any]]
    if isinstance(result, list):
        raw_list = [item for item in result if isinstance(item, dict)]
        print(f"[AI-TASK] ingest_risk_instance_document: model returned list with {len(raw_list)} item(s)")
    elif isinstance(result, dict):
        for key in ("Risk Instances", "risk_instances", "riskInstances", "instances"):
            val = result.get(key)
            if isinstance(val, list):
                raw_list = [item for item in val if isinstance(item, dict)]
                print(f"[AI-TASK] ingest_risk_instance_document: extracted list from '{key}' ({len(raw_list)} items)")
                break
        else:
            if any(k in result for k in ("RiskTitle", "RiskDescription", "Category")):
                raw_list = [result]
                print("[AI-TASK] ingest_risk_instance_document: model returned single dict, wrapping in list")
            else:
                raw_list = []
                print("[AI-TASK] ingest_risk_instance_document: unknown dict shape, returning empty list")
    else:
        raw_list = []
        print(f"[AI-TASK] ingest_risk_instance_document: unexpected type {type(result)}, returning empty list")

    schema_fields = [
        "RiskTitle", "RiskDescription", "PossibleDamage", "RiskPriority", "Criticality",
        "Category", "Origin", "RiskLikelihood", "RiskImpact", "VelocityScore",
        "RiskExposureRating", "RiskMultiplierX", "RiskMultiplierY", "Appetite",
        "RiskResponseType", "RiskResponseDescription", "RiskMitigation", "RiskType",
        "RiskOwner", "BusinessImpact", "FrameworkReference", "ConfidenceScore",
        "AiReasoning", "RiskStatus", "MitigationStatus", "ModifiedMitigations",
        "RiskFormDetails", "Reviewer", "PerFieldRationale",
    ]

    enriched_instances: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_list, start=1):
        per_field: dict[str, Any] = {}
        confidence = item.get("ConfidenceScore", 80)
        try:
            confidence_float = float(confidence) / 100.0
        except (TypeError, ValueError):
            confidence_float = 0.80

        per_field_rationale = item.get("PerFieldRationale", {})

        for field in schema_fields:
            value = item.get(field)
            if value not in (None, "", [], {}):
                field_rationale = ""
                if isinstance(per_field_rationale, dict):
                    field_rationale = per_field_rationale.get(field, "")
                per_field[field] = {
                    "source": "AI_GENERATED",
                    "confidence": confidence_float,
                    "rationale": field_rationale or "Generated from document context by risk instance ingestion task.",
                }
        item.setdefault("_meta", {})
        item["_meta"]["per_field"] = per_field
        enriched_instances.append(item)

    print(f"[AI-TASK] ingest_risk_instance_document: DONE - enriched {len(enriched_instances)} risk instance(s)")
    return enriched_instances


# ─────────────────────────────────────────────────────────────────────────────
# TASK: IDENTIFY RISKS (universal — all source types)
# ─────────────────────────────────────────────────────────────────────────────

def identify_risks_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    """
    Universal task for identifying risks from various data sources.
    Supported source_types: INCIDENT, AUDIT, COMPLIANCE, DOCUMENT, TPRM, MANUAL, EXTERNAL, GENERAL.

    For EXTERNAL source type, the AI applies cross-referencing logic:
    - External article signals + internal data match → new risk (confidence 72-80%)
    - External article + partial internal match       → new risk (confidence 65-72%)
    - External article validates existing risk        → add evidence (do not duplicate)
    - External article shows outcome matching existing risk → boost severity
    """
    source_type = payload.get("source_type", "GENERAL")
    data_summary = payload.get("data_summary", "")
    internal_context = payload.get("internal_context", "")  # Internal data for cross-referencing
    existing_risks_summary = payload.get("existing_risks_summary", "")  # Existing register summary

    print(f"[AI-TASK] identify_risks_task START: source={source_type}")

    confidence_guidance = SOURCE_CONFIDENCE_GUIDELINES.get(
        source_type, SOURCE_CONFIDENCE_GUIDELINES["GENERAL"]
    )

    # Source-type-specific preamble for the prompt
    source_instructions = _build_source_type_instructions(
        source_type, internal_context, existing_risks_summary
    )

    prompt = f"""You are a senior GRC (Governance, Risk, Compliance) and Enterprise Risk Management expert.

Analyze the following data from the {source_type} module and identify potential risks for the Risk Register.

SOURCE DATA:
\"\"\"{data_summary}\"\"\"

{source_instructions}

{_RISK_TITLE_INSTRUCTIONS}

{_AI_REASONING_INSTRUCTIONS}

{_VELOCITY_INSTRUCTIONS}

CONFIDENCE SCORE FOR THIS SOURCE TYPE ({source_type}):
Range: {confidence_guidance['range']}
Guidance: {confidence_guidance['note']}

REQUIREMENTS — Identify 1-5 distinct risks. For each risk provide ALL fields below:

OUTPUT FORMAT — Return ONLY a JSON array:
[
  {{
    "risk_title": "Follow the [Issue] — [Org-specific implication] pattern",
    "risk_description": "Cause → Event → Consequence. Name specific systems/controls/processes. 2-3 sentences.",
    "category": "Operational|Financial|Strategic|Compliance|Technical|Reputational|Information Security|Third-Party|Regulatory|Governance",
    "risk_type": "Current|Emerging|Residual|Inherent|Accepted",
    "criticality": "Low|Medium|High|Critical",
    "business_impact": "Measurable: revenue effect, SLA breach %, penalty amount, downtime. 2-3 sentences.",
    "possible_damage": "Quantified where possible: record count, downtime hours, penalty INR/USD. 2 sentences.",
    "likelihood": 5,
    "impact": 5,
    "velocity_score": 5,
    "risk_exposure_rating": 25.0,
    "ai_reasoning": "Use exact cross-referencing format: [Source-specific fact with numbers]. Cross-referencing [with internal data/profile]: [specific internal metric or gap]. [Why this creates elevated risk]. Always cite specific evidence.",
    "confidence_score": 80,
    "control_effectiveness": "Low|Medium|High",
    "framework_reference": "Specific code: ME 4, HRM 2, NIST PR.AC-1, DPDP-S8.6, KYC-AML, etc.",
    "functional_area": "IT|Finance|HR|Operations|Legal|Compliance|Security|Credit Risk|Fraud Management|etc",
    "mitigation_steps": [
      "Specific step 1 — name the action and target system/process",
      "Specific step 2 — name the action and target system/process",
      "Specific step 3 — name the action and target system/process"
    ],
    "per_field_rationale": {{
      "risk_title": "What makes this title specific and accurate?",
      "risk_description": "How does the cause→event→consequence chain apply to source data?",
      "category": "Which characteristic of the source data determines category?",
      "risk_type": "Is this current/active or emerging — what evidence?",
      "criticality": "What specific source data point drove this criticality?",
      "likelihood": "What frequency or trend data set this score? (1=rare, 10=near-certain)",
      "impact": "What financial/operational/regulatory factors determined this? (1=negligible, 10=catastrophic)",
      "velocity_score": "What makes this materialise quickly or slowly? Any deadlines or active trends?",
      "control_effectiveness": "What do we know about existing controls for this risk?",
      "mitigation_steps": "Why these specific steps over generic alternatives?",
      "possible_damage": "How were damage estimates derived from source data?",
      "business_impact": "How does this translate to business terms for leadership?",
      "functional_area": "Why is this area primarily responsible/impacted?",
      "framework_reference": "Why is this the most relevant control reference?"
    }},
    "action_type": "CREATE_NEW|ADD_EVIDENCE|BOOST_SEVERITY",
    "action_reasoning": "If ADD_EVIDENCE or BOOST_SEVERITY: which existing risk ID or title does this affect, and what specifically changes?"
  }}
]

ACTION TYPE RULES:
- "CREATE_NEW": This source data reveals a new risk not yet in the register.
- "ADD_EVIDENCE": External source validates or corroborates an EXISTING risk — do NOT create a duplicate.
  Set this when: external article describes the same issue as an existing internal risk.
  Include: which existing risk it supports and what evidence to add.
- "BOOST_SEVERITY": External source shows an ACTUAL OUTCOME (fatality, penalty, breach) that demonstrates
  real consequences matching an existing risk's scenario. Increases impact score on existing risk.
  Include: which existing risk, what the new impact score should be, and why.

CRITICAL RULES:
- Return ONLY the JSON array. No markdown, no extra text.
- If no risks are found, return an empty array [].
- likelihood, impact, velocity_score must be integers 1-10.
- confidence_score must be an integer in the range for this source type.
- risk_exposure_rating = (likelihood × impact) / 10 as baseline, then adjust for velocity.
- ai_reasoning MUST use the cross-referencing format — generic explanations are NOT acceptable.
- mitigation_steps must be SPECIFIC — reference the actual system, process, or control to change.
- Risk titles must follow the naming pattern above — vague titles like "Compliance Risk" are NOT acceptable.
"""

    result = _generate_json(service, "risk.identify_risks", prompt, options)

    # Normalize result to ensure it's a list
    if isinstance(result, list):
        risks = result
    elif isinstance(result, dict):
        for key in ["risks", "identified_risks", "data"]:
            if isinstance(result.get(key), list):
                risks = result[key]
                break
        else:
            risks = [result]
    else:
        risks = []

    print(f"[AI-TASK] identify_risks_task DONE: source={source_type}, found={len(risks)} risks")
    return risks


def _build_source_type_instructions(
    source_type: str,
    internal_context: str,
    existing_risks_summary: str,
) -> str:
    """Build source-type-specific instructions to inject into the identify_risks prompt."""

    base = ""

    if internal_context:
        base += f"""
INTERNAL ORGANISATION DATA (for cross-referencing):
\"\"\"{internal_context}\"\"\"

"""

    if existing_risks_summary:
        base += f"""
EXISTING RISK REGISTER SUMMARY (to avoid duplicates and identify evidence-add/severity-boost opportunities):
\"\"\"{existing_risks_summary}\"\"\"

"""

    if source_type == "EXTERNAL":
        base += """
EXTERNAL SOURCE PROCESSING RULES:
This data comes from external news, regulatory bulletins, or industry reports.
Your primary task is to determine the RELEVANCE to this organisation's specific profile.

Decision logic:
1. Does the external article describe a regulatory enforcement action or industry incident?
   → Check if the organisation has a matching internal gap/profile.
   → If YES and no existing risk covers this: CREATE_NEW (confidence 72-80% if internal data matches)
   → If YES and existing risk covers this: ADD_EVIDENCE (do not duplicate)

2. Does the article show an actual OUTCOME (penalty imposed, fatality, breach published)?
   → If we have an existing risk with a matching scenario: BOOST_SEVERITY
   → Demonstrated outcomes increase the Impact score (typically +1 to +2)

3. Is the article purely informational with no actionable risk signal?
   → Return empty array []

4. Is the article about an industry the organisation has NO exposure to?
   → Return empty array []

CONFIDENCE CALIBRATION FOR EXTERNAL SOURCES:
- External article + matching internal data (audit finding, incident ID): 72-80%
- External article + partially matching internal profile: 65-72%
- External article + relevant industry but no internal data: 55-65%
- External article + no organisational relevance: Do NOT create risk

IMPORTANT: External risks should have LOWER confidence than internal sources because
the AI is inferring relevance rather than directly observing internal data.
"""

    elif source_type == "INCIDENT":
        base += """
INCIDENT SOURCE PROCESSING RULES:
This data comes from an internal security or operational incident.
- You have DIRECT EVIDENCE of the risk materialising — confidence should be 80-92%.
- Velocity should reflect how quickly the same incident pattern could recur.
- Identify both the immediate risk (from this incident) and any systemic risks it reveals.
- Cross-reference with any provided internal context to identify root-cause risks.
"""

    elif source_type == "AUDIT":
        base += """
AUDIT SOURCE PROCESSING RULES:
This data comes from internal or external audit findings.
- Audit findings confirm control failures — confidence should be 82-92%.
- Classify each finding as a distinct risk only if the underlying risk is different.
- Reference specific audit finding IDs where available (e.g. AF-2041).
- Velocity reflects how close the next inspection or remediation deadline is.
"""

    elif source_type == "COMPLIANCE":
        base += """
COMPLIANCE SOURCE PROCESSING RULES:
This data comes from compliance monitoring (control testing, regulatory returns, breaches).
- Confirmed compliance breaches → confidence 85-95%.
- Reference specific regulation sections (e.g. DPDP S.8.6, KYC-AML Rule 7).
- Include regulatory penalty amounts where known from provided context.
- Velocity is high if a reporting deadline or enforcement window is approaching.
"""

    elif source_type == "TPRM":
        base += """
THIRD-PARTY RISK SOURCE PROCESSING RULES:
This data comes from third-party/vendor risk assessments.
- Identify concentration risk, single-vendor dependency, and contractual gaps.
- Reference specific vendor names where available.
- Confidence 72-85% depending on assessment quality.
- Category should typically be Third-Party, though secondary categories may apply.
"""

    return base


# ─────────────────────────────────────────────────────────────────────────────
# TASK: INGEST RISK INSTANCE DOCUMENT (STREAMING)
# ─────────────────────────────────────────────────────────────────────────────

def ingest_risk_instance_document_streaming(
    service,
    payload: dict[str, Any],
    stream_callback=None,
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    """
    Streaming version that generates risk instance fields progressively.
    Calls stream_callback(event_type, data) for each field generated.
    """
    document_text = payload.get("document_text", "")
    print(f"[AI-TASK] ingest_risk_instance_document_streaming: document_len={len(document_text)}")

    if stream_callback:
        stream_callback("status", {"message": "Starting AI risk instance analysis...", "progress": 5})

    # Step 1: Extract basic structure first
    structure_prompt = f"""
You are a GRC risk specialist. Analyze this document and identify how many risk instances it contains.

Return ONLY a JSON object with:
{{
  "risk_count": <number of risk instances found>,
  "risk_titles": ["[Issue] — [Consequence]", ...]
}}

Note: Risk titles should follow pattern: [Issue] — [Consequence or Gap Revealed]

DOCUMENT:
\"\"\"{document_text}\"\"\"
"""
    structure_result = _generate_json(service, "risk.analyze_structure", structure_prompt, options)
    risk_count = structure_result.get("risk_count", 1)
    risk_titles = structure_result.get("risk_titles", ["Risk Instance 1"])

    if stream_callback:
        stream_callback("structure", {
            "risk_count": risk_count,
            "risk_titles": risk_titles,
            "progress": 15,
        })

    # Step 2: Generate each risk instance progressively with enhanced field guidance
    schema_fields = [
        "RiskTitle", "RiskDescription", "PossibleDamage", "RiskPriority", "Criticality",
        "Category", "Origin", "RiskLikelihood", "RiskImpact", "VelocityScore",
        "RiskExposureRating", "RiskMultiplierX", "RiskMultiplierY", "Appetite",
        "RiskResponseType", "RiskResponseDescription", "RiskMitigation", "RiskType",
        "RiskOwner", "BusinessImpact", "FrameworkReference", "ConfidenceScore",
        "AiReasoning", "RiskStatus", "MitigationStatus", "ModifiedMitigations",
        "RiskFormDetails", "Reviewer",
    ]

    all_instances = []
    base_progress = 20
    progress_per_instance = 70 / max(risk_count, 1)

    for idx in range(risk_count):
        risk_title = risk_titles[idx] if idx < len(risk_titles) else f"Risk Instance {idx + 1}"

        if stream_callback:
            stream_callback("risk_start", {
                "index": idx,
                "title": risk_title,
                "progress": base_progress + (idx * progress_per_instance),
            })

        risk_instance: dict[str, Any] = {}
        per_field: dict[str, Any] = {}
        fields_per_progress = len(schema_fields)
        field_progress_step = progress_per_instance / fields_per_progress

        for field_idx, field_name in enumerate(schema_fields):
            guidance = RISK_FIELD_GUIDANCE.get("risk_instance", {}).get(
                field_name, "Return a professional, specific value."
            )

            # Inject velocity and framework instructions for relevant fields
            extra = ""
            if field_name == "VelocityScore":
                extra = _VELOCITY_INSTRUCTIONS
            elif field_name == "AiReasoning":
                extra = _AI_REASONING_INSTRUCTIONS

            field_prompt = f"""
You are a GRC risk specialist. For risk instance #{idx + 1} "{risk_title}",
extract ONLY the field "{field_name}".

Return ONLY a JSON object:
{{
  "value": <your answer>,
  "confidence": 0.0-1.0,
  "rationale": "cite specific evidence from the document"
}}

Field guidance for "{field_name}":
{guidance}
{extra}

DOCUMENT:
\"\"\"{document_text}\"\"\"
"""
            try:
                field_result = _generate_json(service, f"risk.field.{field_name}", field_prompt, options)
                value = field_result.get("value")
                confidence = field_result.get("confidence", 0.8)
                rationale = field_result.get("rationale", "Generated from document context")

                if value not in (None, "", [], {}):
                    risk_instance[field_name] = value
                    per_field[field_name] = {
                        "source": "AI_GENERATED",
                        "confidence": confidence,
                        "rationale": rationale,
                    }

                    if stream_callback:
                        stream_callback("field_generated", {
                            "risk_index": idx,
                            "field_name": field_name,
                            "value": value,
                            "confidence": confidence,
                            "rationale": rationale,
                            "progress": (
                                base_progress
                                + (idx * progress_per_instance)
                                + ((field_idx + 1) * field_progress_step)
                            ),
                        })

            except Exception as e:
                print(f"[AI-TASK] Error generating field {field_name}: {e}")
                if stream_callback:
                    stream_callback("field_error", {
                        "risk_index": idx,
                        "field_name": field_name,
                        "error": str(e),
                    })

        risk_instance.setdefault("_meta", {})
        risk_instance["_meta"]["per_field"] = per_field
        all_instances.append(risk_instance)

        if stream_callback:
            stream_callback("risk_complete", {
                "index": idx,
                "risk_instance": risk_instance,
                "progress": base_progress + ((idx + 1) * progress_per_instance),
            })

    if stream_callback:
        stream_callback("complete", {
            "risk_instances": all_instances,
            "progress": 100,
        })

    print(f"[AI-TASK] ingest_risk_instance_document_streaming: DONE - {len(all_instances)} instances")
    return all_instances


# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK: FILL MISSING RISK FIELDS
# ─────────────────────────────────────────────────────────────────────────────

def _fill_missing_risk_fields(result: dict, incident_description: str):
    """Fill any missing required fields with sensible defaults based on what we have."""

    criticality = result.get("criticality", "Medium")
    category = result.get("category", "Information Security")

    criticality_defaults = {
        "Critical": {"likelihood": 8, "impact": 9, "velocity": 7, "priority": "P1", "exposure": "Critical", "confidence": 85},
        "High":     {"likelihood": 7, "impact": 7, "velocity": 6, "priority": "P2", "exposure": "High",     "confidence": 80},
        "Medium":   {"likelihood": 5, "impact": 5, "velocity": 5, "priority": "P3", "exposure": "Medium",   "confidence": 75},
        "Low":      {"likelihood": 3, "impact": 3, "velocity": 3, "priority": "P4", "exposure": "Low",      "confidence": 70},
    }
    defaults = criticality_defaults.get(criticality, criticality_defaults["Medium"])

    if not result.get("criticalityJustification"):
        result["criticalityJustification"] = (
            f"{criticality} criticality assigned based on potential business and regulatory impact of this incident type."
        )

    if not result.get("possibleDamage"):
        result["possibleDamage"] = (
            "Potential operational disruption, regulatory scrutiny, customer trust impact, and remediation costs. "
            "Financial impact may include investigation expenses and compliance-related costs."
        )

    if not result.get("possibleDamageJustification"):
        result["possibleDamageJustification"] = (
            "Damage assessment based on typical incident response costs and business impact patterns for similar events."
        )

    if not result.get("category"):
        result["category"] = "Information Security"

    if not result.get("categoryJustification"):
        result["categoryJustification"] = (
            f"Categorised as {result['category']} based on the nature of the incident and primary risk exposure areas."
        )

    if not result.get("riskDescription"):
        incident_lower = incident_description.lower()
        if "breach" in incident_lower or "data" in incident_lower:
            result["riskDescription"] = (
                "Data security incident could lead to unauthorised access to sensitive information, "
                "resulting in regulatory violations and business disruption."
            )
        elif "system" in incident_lower or "server" in incident_lower:
            result["riskDescription"] = (
                "System security incident may compromise data integrity and availability, "
                "potentially affecting business operations and compliance posture."
            )
        else:
            result["riskDescription"] = (
                "Security incident poses risk to organisational assets and operations, "
                "potentially leading to data exposure and business impact."
            )

    if not result.get("riskDescriptionJustification"):
        result["riskDescriptionJustification"] = (
            "Risk description formulated based on incident characteristics and typical consequence patterns for this event type."
        )

    if not result.get("riskLikelihood"):
        result["riskLikelihood"] = defaults["likelihood"]

    if not result.get("riskLikelihoodJustification"):
        result["riskLikelihoodJustification"] = (
            f"Likelihood score of {result['riskLikelihood']} reflects typical frequency patterns "
            "for this incident type and current control environment."
        )

    if not result.get("riskImpact"):
        result["riskImpact"] = defaults["impact"]

    if not result.get("riskImpactJustification"):
        result["riskImpactJustification"] = (
            f"Impact score of {result['riskImpact']} considers potential business disruption, "
            "regulatory exposure, and remediation requirements."
        )

    if not result.get("velocityScore"):
        result["velocityScore"] = defaults["velocity"]

    if not result.get("velocityJustification"):
        result["velocityJustification"] = (
            f"Velocity score of {result['velocityScore']} reflects typical materialisation speed "
            "for this incident type based on known control gaps and environmental factors."
        )

    if not result.get("riskExposureRating"):
        result["riskExposureRating"] = defaults["exposure"]

    if not result.get("riskPriority"):
        result["riskPriority"] = defaults["priority"]

    if not result.get("riskPriorityJustification"):
        result["riskPriorityJustification"] = (
            f"Priority {result['riskPriority']} assigned based on risk exposure level, "
            "velocity, and business impact potential."
        )

    if not result.get("riskAppetite"):
        appetite_map = {
            "Critical": "Exceeds Appetite",
            "High":     "Exceeds Appetite",
            "Medium":   "At Appetite Limit",
            "Low":      "Within Appetite",
        }
        result["riskAppetite"] = appetite_map.get(criticality, "At Appetite Limit")

    if not result.get("riskMitigation") or not isinstance(result.get("riskMitigation"), list):
        result["riskMitigation"] = [
            "Conduct immediate scope assessment of affected systems and data exposure.",
            "Implement enhanced monitoring and access controls for related systems.",
            "Review and update incident response procedures based on lessons learned.",
            "Strengthen preventive controls to reduce likelihood of recurrence.",
        ]

    if not result.get("riskMitigationJustification"):
        result["riskMitigationJustification"] = (
            "Mitigation strategy addresses immediate containment, enhanced monitoring, "
            "process improvements, and preventive controls to reduce both likelihood and impact."
        )

    if not result.get("confidenceScore"):
        result["confidenceScore"] = defaults["confidence"]

    if not result.get("confidenceJustification"):
        result["confidenceJustification"] = (
            f"Confidence score of {result['confidenceScore']}% based on internal incident data "
            "(direct observation — high confidence source)."
        )

    if not result.get("frameworkReference"):
        framework_map = {
            "Information Security": "ISO 27001 A.12.6",
            "IT Security":          "NIST PR.AC-1",
            "Technical":            "CIS Control 7",
            "Financial":            "COSO ERM Financial",
            "Compliance":           "ISO 31000",
            "Operational":          "ISO 31000 Operational",
            "Process Risk":         "ISO 31000",
            "Third-Party":          "ISO 27001 A.15",
        }
        result["frameworkReference"] = framework_map.get(category, "ISO 31000")

    if not result.get("aiReasoning"):
        result["aiReasoning"] = (
            f"Incident data indicates {criticality.lower()} criticality risk in the {category} category. "
            "Cross-referencing with internal context: incident characteristics match known control gaps. "
            "Elevated risk of recurrence if root cause is not addressed promptly."
        )

    if not result.get("functionalArea"):
        cat_map = {
            "Information Security": "IT",
            "IT Security":          "IT",
            "Technical":            "Engineering",
            "Financial":            "Finance",
            "Compliance":           "Legal",
            "Operational":          "Operations",
            "Process Risk":         "Operations",
            "Third-Party":          "Procurement",
        }
        result["functionalArea"] = cat_map.get(category, "Operations")

    if not result.get("functionalAreaJustification"):
        result["functionalAreaJustification"] = (
            f"Assigned to {result.get('functionalArea')} based on the risk category "
            "and primary operational impact area."
        )


# ─────────────────────────────────────────────────────────────────────────────
# TASK REGISTRY
# ─────────────────────────────────────────────────────────────────────────────

RISK_TASKS = {
    "risk.analyze_security_incident":              analyze_security_incident_task,
    "risk.infer_field":                            infer_risk_field_task,
    "risk.ingest_risk_document":                   ingest_risk_document_task,
    "risk.ingest_risk_instance_document":          ingest_risk_instance_document_task,
    "risk.ingest_risk_instance_document_streaming": ingest_risk_instance_document_streaming,
    "risk.identify_risks":                         identify_risks_task,
}