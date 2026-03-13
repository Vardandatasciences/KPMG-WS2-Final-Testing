import json
from typing import Any

from ..types import AIRequestOptions


RISK_FIELD_GUIDANCE = {
    "risk": {
        "Criticality": "Return one of: Low, Medium, High, Critical.",
        "PossibleDamage": "Describe concrete damages such as data loss, downtime, penalties, or reputation impact in 1-2 sentences.",
        "Category": "Return the best fit category from: Operational, Financial, Strategic, Compliance, Technical, Reputational, Information Security, Process Risk, Third-Party, Regulatory, Governance.",
        "RiskType": "Return one of: Current, Residual, Inherent, Emerging, Accepted.",
        "BusinessImpact": "Explain business impact in business terms such as SLA breach, revenue effect, or compliance effect in 1-2 sentences.",
        "RiskDescription": "Write a precise description in 1-3 sentences of how and why the risk arises.",
        "RiskLikelihood": "Return an integer 1-10 where 1 is rare and 10 is almost certain.",
        "RiskImpact": "Return an integer 1-10 where 1 is negligible and 10 is catastrophic.",
        "RiskExposureRating": "Return a float 0-100. If uncertain, align with the combined likelihood and impact.",
        "RiskPriority": "Return one of: Low, Medium, High, Critical, based on exposure and criticality.",
        "RiskMitigation": "Return 2-4 actionable mitigation steps as one concise paragraph or JSON-style list.",
        "CreatedAt": "Return a plausible assessment date in YYYY-MM-DD format; if unknown, use today.",
        "RiskMultiplierX": "Return a float in 0.1-1.5 reflecting weighting factor X, defaulting near 0.5 if unknown.",
        "RiskMultiplierY": "Return a float in 0.1-1.5 reflecting weighting factor Y, defaulting near 0.5 if unknown.",
    },
    "risk_instance": {
        "RiskDescription": "Write a precise 2-4 sentence description of how and why the risk instance occurred, including what happened and who was affected.",
        "PossibleDamage": "Describe concrete specific damages such as data loss volume, downtime, financial penalties, or reputation impact in 2-3 sentences.",
        "RiskPriority": "Return one of: Low, Medium, High, Critical based on severity, exposure, and urgency.",
        "Criticality": "Return one of: Low, Medium, High, Critical considering operational, financial, compliance, and reputational impact.",
        "Category": "Return the best fit category from: Operational, Financial, Strategic, Compliance, Technical, Reputational, Information Security, Process Risk, Third-Party, Regulatory, Governance.",
        "Origin": "Return one of: Internal, External, Third-Party, Regulatory, Market, Operational.",
        "RiskLikelihood": "Return an integer 1-10 based on frequency, controls, and environmental factors.",
        "RiskImpact": "Return an integer 1-10 based on financial, operational, reputational, and compliance impact.",
        "RiskExposureRating": "Return a float 0-100 representing overall exposure. Align it with likelihood, impact, and multipliers.",
        "RiskMultiplierX": "Return a float in 0.1-2.0 reflecting weighting factor X, defaulting near 1.0 if unknown.",
        "RiskMultiplierY": "Return a float in 0.1-2.0 reflecting weighting factor Y, defaulting near 1.0 if unknown.",
        "Appetite": "Return one of: Low, Medium, High based on organizational tolerance for this risk.",
        "RiskResponseType": "Return one of: Avoid, Mitigate, Transfer, Accept.",
        "RiskResponseDescription": "Provide a detailed 2-3 sentence response strategy with concrete actions, rationale, and expected outcome.",
        "RiskMitigation": "Return a JSON array of 3-5 mitigation objects with 'step' and 'description' fields.",
        "RiskType": "Return one of: Current, Residual, Inherent, Emerging, Accepted.",
        "RiskOwner": "Return a specific owner name, role, or department responsible for this risk instance.",
        "BusinessImpact": "Provide a detailed 2-4 sentence business impact covering revenue, SLA, operations, reputation, or regulatory exposure.",
        "RiskStatus": "Return one of: Not Assigned, Assigned, Approved, Rejected.",
        "MitigationStatus": "Return one of: Pending, Yet to Start, Work In Progress, Revision Required by Reviewer, Revision Required by User, Completed.",
        "ModifiedMitigations": "Return a JSON array documenting mitigation changes, or [] if none.",
        "RiskFormDetails": "Return a JSON object with structured assessment details such as method, sources, assessment date, and notes.",
        "Reviewer": "Return the reviewer name or role, or 'Pending Review' if not known.",
    },
}


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
    filtered = {key: current_record.get(key) for key in allowed_fields if current_record.get(key) not in (None, "", [], {})}
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
- Return ONLY the JSON object: {{"value": ..., "confidence": ..., "rationale": ...}}
- If you cannot infer, return {{"value": null, "confidence": 0.0, "rationale": "Not enough information"}}.
- Always include a brief rationale explaining your decision.
- Return ONLY valid JSON, no markdown, no code blocks, no other text.
- The "value" field should contain ONLY the value for {field_name}, nothing else.
"""


def analyze_security_incident_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    incident_description = payload.get("incident_description", "")
    rag_context = payload.get("rag_context", "")

    prompt = f"""
Analyze the following security incident for a banking GRC system and return ONLY valid JSON.

INCIDENT DETAILS:
{incident_description}

OPTIONAL RETRIEVED CONTEXT:
{rag_context}

Return JSON with exactly these keys:
{{
  "criticality": "<Severe/Significant/Moderate/Minor>",
  "possibleDamage": "<detailed potential harm description>",
  "category": "<incident type>",
  "riskDescription": "<cause-effect risk scenario>",
  "riskLikelihood": <integer 1-10>,
  "riskLikelihoodJustification": "<detailed explanation>",
  "riskImpact": <integer 1-10>,
  "riskImpactJustification": "<detailed explanation>",
  "riskExposureRating": "<Critical/High/Elevated/Low Exposure>",
  "riskPriority": "<P0/P1/P2/P3>",
  "riskAppetite": "<Within Appetite/Borderline/Exceeds Appetite>",
  "riskMitigation": ["<step1>", "<step2>", "..."]
}}

Rules:
- Use banking and GRC terminology.
- Every key is mandatory.
- `riskLikelihood` and `riskImpact` must be integers between 1 and 10.
- `riskMitigation` must be a JSON array of specific actions.
- Do not add extra top-level keys.
- Do not return markdown.
"""
    return _generate_json(service, "risk.analyze_security_incident", prompt, options)


def infer_risk_field_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    prompt = _build_risk_field_prompt(payload)
    return _generate_json(service, "risk.infer_field", prompt, options)


RISK_TASKS = {
    "risk.analyze_security_incident": analyze_security_incident_task,
    "risk.infer_field": infer_risk_field_task,
}
