import json
from typing import Any

from ..types import AIRequestOptions

# Keys the UI expects for Create Risk AI analysis (flat structure)
FLAT_RISK_ANALYSIS_KEYS = [
    "criticality", "criticalityJustification", "possibleDamage", "possibleDamageJustification",
    "category", "categoryJustification", "riskDescription", "riskDescriptionJustification",
    "riskLikelihood", "riskLikelihoodJustification", "riskImpact", "riskImpactJustification",
    "riskExposureRating", "riskPriority", "riskPriorityJustification", "riskAppetite",
    "riskMitigation", "riskMitigationJustification",
]


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
            # Also try parsing "Analysis: {...}" from inner.text (model often embeds full JSON there)
            text = inner.get("text") if isinstance(inner.get("text"), str) else ""
            if text and ("Analysis:" in text or '"criticality"' in text or '"riskLikelihood"' in text):
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
        # If inner is a string, try to parse as JSON
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
    ]
    for alt, canonical in aliases:
        if (canonical not in out or out.get(canonical) in (None, "")) and alt in out and out[alt] not in (None, ""):
            out[canonical] = out[alt]

    # 3) Ensure numeric types for likelihood/impact
    for key in ("riskLikelihood", "riskImpact"):
        if key in out and out[key] is not None and out[key] != "":
            try:
                out[key] = int(float(out[key]))
            except (TypeError, ValueError):
                pass

    return out


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
    print(f"[AI-TASK] analyze_security_incident: incident_len={len(incident_description)}, rag_context_len={len(rag_context)}")

    prompt = f"""INCIDENT TITLE: {incident_description}
CONTEXT: {rag_context}

Analyze this incident and return EXACTLY this JSON with ALL 16 fields filled. DO NOT SKIP ANY FIELDS:

{{
"criticality": "High",
"criticalityJustification": "High criticality due to potential data exposure from stolen office equipment containing sensitive customer information, violating PCI DSS requirements and creating regulatory compliance risks under banking data protection standards.",
"possibleDamage": "Financial losses: $500K-2M including forensic investigation costs, PCI compliance fines, customer notification expenses. Reputational damage affecting customer trust. Potential regulatory penalties under banking data protection laws. Business disruption from security protocol implementation.",
"possibleDamageJustification": "Damage assessment based on industry breach cost averages for banking sector ($4.45M average), regulatory fine structures for data protection violations, and operational disruption analysis for similar physical security incidents.",
"category": "Physical Security Breach - Equipment Theft",
"categoryJustification": "Categorized as physical security breach per NIST incident taxonomy, involving unauthorized removal of business equipment potentially containing sensitive data, requiring data breach response protocols.",
"riskDescription": "Physical theft of office equipment creates data exposure risk if devices contained unencrypted customer information, payment data, or access credentials. Risk escalates if stolen equipment bypasses endpoint security controls and enables unauthorized system access.",
"riskDescriptionJustification": "Risk scenario constructed using NIST cybersecurity framework physical security controls assessment, considering data-at-rest protection, endpoint security measures, and potential data exposure from unsecured business equipment.",
"riskLikelihood": 6,
"riskLikelihoodJustification": "Moderate likelihood (6/10) based on physical security control gaps, frequency of office equipment theft in business environments, and potential for data recovery from stolen devices lacking full-disk encryption. Historical data shows 40% of stolen business equipment contains recoverable sensitive data.",
"riskImpact": 7,
"riskImpactJustification": "High impact (7/10) considering potential regulatory penalties for data protection violations ($500K-2M fines), customer trust damage (15-25% customer churn typical), incident response costs ($200K-500K), and business disruption from implementing enhanced security protocols.",
"riskExposureRating": "Elevated",
"riskPriority": "P2",
"riskPriorityJustification": "P2 priority assigned due to moderate probability (6/10) but high potential impact (7/10), requiring prompt response within 48 hours per banking incident response protocols and regulatory notification requirements under PCI DSS Section 12.10.1.",
"riskAppetite": "Exceeds Appetite",
"riskMitigation": ["Immediately inventory all office equipment and verify data encryption status", "Implement mandatory full-disk encryption on all business devices within 30 days", "Deploy physical security controls including equipment tracking and secure storage protocols", "Establish data classification program to identify devices containing sensitive information", "Conduct security awareness training on physical security and data handling procedures"],
"riskMitigationJustification": "Mitigation strategy addresses root cause through physical security enhancements (NIST CSF Physical Security controls), data protection improvements (encryption requirements), and process controls (inventory management), with implementation timeline aligned to regulatory compliance requirements."
}}

MANDATORY: Replace ALL example values with your analysis of the actual incident. Ensure ALL 16 fields are present and filled with relevant data. Return ONLY the JSON.
"""
    result = _generate_json(service, "risk.analyze_security_incident", prompt, options)
    print(f"[AI-TASK] analyze_security_incident: DONE - raw result_keys={list(result.keys()) if isinstance(result, dict) else 'n/a'}")
    
    # CRITICAL: Normalize so UI always gets flat structure (model often puts analysis inside context[0])
    if isinstance(result, dict):
        result = _normalize_risk_analysis_response(result)
        print(f"[AI-TASK] analyze_security_incident: after normalize - result_keys={list(result.keys())}")
        missing = [k for k in FLAT_RISK_ANALYSIS_KEYS if k not in result or result.get(k) in (None, "")]
        if missing:
            print(f"[AI-TASK] analyze_security_incident: WARNING - still missing after normalize: {missing}")
    
    return result


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


def _extract_fields_from_document(document_text: str, risk_section: str) -> dict[str, Any]:
    """
    Try to extract fields directly from the document text using pattern matching.
    Returns a dict with extracted fields and their metadata.
    """
    import re
    
    extracted_fields = {}
    text = risk_section.lower()
    
    # Pattern matching for common risk register fields
    patterns = {
        "RiskTitle": [
            r"(?:risk\s*title|title|risk\s*name|name)\s*[:=]\s*([^\n\r]+)",
            r"^([^\n\r]*(?:risk|failure|breach|non-compliance)[^\n\r]*?)(?:\n|$)",
        ],
        "Criticality": [
            r"(?:criticality|severity|priority)\s*[:=]\s*(low|medium|high|critical)",
        ],
        "Category": [
            r"(?:category|type|classification)\s*[:=]\s*([^\n\r]+)",
        ],
        "RiskDescription": [
            r"(?:description|detail|summary)\s*[:=]\s*([^\n\r]+(?:\n[^\n\r]+)*)",
        ],
        "BusinessImpact": [
            r"(?:business\s*impact|impact|consequence)\s*[:=]\s*([^\n\r]+)",
        ],
        "PossibleDamage": [
            r"(?:damage|loss|harm|consequence)\s*[:=]\s*([^\n\r]+)",
        ],
        "RiskLikelihood": [
            r"(?:likelihood|probability|chance)\s*[:=]\s*([0-9]+)",
        ],
        "RiskImpact": [
            r"(?:impact|severity)\s*[:=]\s*([0-9]+)",
        ],
        "RiskMitigation": [
            r"(?:mitigation|control|response|treatment)\s*[:=]\s*([^\n\r]+(?:\n[^\n\r]+)*)",
        ],
    }
    
    for field_name, field_patterns in patterns.items():
        for pattern in field_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                if value and len(value) > 2:  # Valid extraction
                    # Convert to appropriate type
                    if field_name in ("RiskLikelihood", "RiskImpact"):
                        try:
                            value = int(value)
                        except ValueError:
                            continue
                    
                    extracted_fields[field_name] = {
                        "value": value,
                        "source": "EXTRACTED",
                        "confidence": 0.9,
                        "rationale": f"Directly extracted from document using pattern matching."
                    }
                    break
    
    return extracted_fields


def ingest_risk_document_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    document_text = payload.get("document_text", "")
    print(f"[AI-TASK] ingest_risk_document: document_len={len(document_text)}")
    prompt = f"""
You are a GRC risk specialist. Read the following document and extract a list of risks suitable for a risk register.

Return ONLY a JSON array of risk objects with this structure:
[
  {{
    "RiskTitle": "",
    "Criticality": "Low|Medium|High|Critical",
    "PossibleDamage": "",
    "Category": "",
    "RiskType": "Current|Residual|Inherent|Emerging|Accepted",
    "BusinessImpact": "",
    "RiskDescription": "",
    "RiskLikelihood": 1,
    "RiskImpact": 1,
    "RiskExposureRating": 0.0,
    "RiskPriority": "Low|Medium|High|Critical",
    "RiskMitigation": "",
    "CreatedAt": "YYYY-MM-DD",
    "RiskMultiplierX": 0.5,
    "RiskMultiplierY": 0.5
  }}
]

Rules:
- Infer risks directly from the document content.
- Always set RiskTitle and make it concise and descriptive.
- RiskLikelihood and RiskImpact must be integers between 1 and 10.
- RiskExposureRating must be a float between 0 and 100, consistent with likelihood and impact.
- Return ONLY the JSON array, no markdown, no comments, no extra keys.

DOCUMENT:
\"\"\"{document_text}\"\"\"
"""
    result = _generate_json(service, "risk.ingest_risk_document", prompt, options)

    # Normalize LLM output: handle various response formats from the model
    risks = []
    if isinstance(result, list):
        print(f"[AI-RISK] ingest_risk_document_task: model returned list with {len(result)} item(s)")
        risks = [item for item in result if isinstance(item, dict)]
    elif isinstance(result, dict):
        # Check if this is a nested structure with named risks (e.g., {"Risk 1": {...}, "Risk 2": {...}})
        nested_risks = []
        for key, value in result.items():
            if isinstance(value, dict) and any(field in value for field in ["RiskTitle", "Criticality", "RiskDescription"]):
                nested_risks.append(value)
        
        if nested_risks:
            print(f"[AI-RISK] ingest_risk_document_task: extracted {len(nested_risks)} risks from nested structure")
            risks = nested_risks
        elif any(field in result for field in ["RiskTitle", "Criticality", "RiskDescription"]):
            # Single risk object
            print("[AI-RISK] ingest_risk_document_task: model returned single risk dict, wrapping in list")
            risks = [result]
        else:
            print("[AI-RISK] ingest_risk_document_task: unrecognized dict structure, returning empty list")
            return []
    else:
        print(f"[AI-RISK] ingest_risk_document_task: unexpected result type {type(result)}, returning empty list")
        return []

    # Attach simple per-field metadata so frontends can show AI field indicators
    schema_fields = [
        "RiskTitle",
        "Criticality",
        "PossibleDamage",
        "Category",
        "RiskType",
        "BusinessImpact",
        "RiskDescription",
        "RiskLikelihood",
        "RiskImpact",
        "RiskExposureRating",
        "RiskPriority",
        "RiskMitigation",
        "CreatedAt",
        "RiskMultiplierX",
        "RiskMultiplierY",
    ]

    enriched: list[dict[str, Any]] = []
    for idx, item in enumerate(risks, start=1):
        print(f"[AI-RISK] Enriching risk #{idx} with per-field metadata")

        per_field: dict[str, Any] = {}
        for field in schema_fields:
            value = item.get(field)
            if value not in (None, "", [], {}):
                per_field[field] = {
                    "source": "AI_GENERATED",
                    "confidence": 0.8,
                    "rationale": "Generated from document context by centralized risk ingestion task.",
                }
                print(f"[AI-RISK]   Field '{field}' generated with value: {str(value)[:120]}")

        item.setdefault("_meta", {})
        item["_meta"]["per_field"] = per_field

        print(
            f"[AI-RISK]   Metadata summary for risk #{idx}: "
            f"{len(per_field)} fields tagged as AI_GENERATED"
        )

        enriched.append(item)

    print(f"[AI-RISK] ingest_risk_document_task: returning {len(enriched)} enriched risk(s)")
    return enriched


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
        stream_callback('status', {'message': 'Starting AI risk instance analysis...', 'progress': 5})
    
    # Step 1: Extract basic structure first
    structure_prompt = f"""
You are a GRC risk specialist. Analyze this document and identify how many risk instances it contains.

Return ONLY a JSON object with:
{{
  "risk_count": <number of risk instances found>,
  "risk_titles": ["title1", "title2", ...]
}}

DOCUMENT:
\"\"\"{document_text}\"\"\"
"""
    
    structure_result = _generate_json(service, "risk.analyze_structure", structure_prompt, options)
    risk_count = structure_result.get("risk_count", 1)
    risk_titles = structure_result.get("risk_titles", ["Risk Instance 1"])
    
    if stream_callback:
        stream_callback('structure', {
            'risk_count': risk_count,
            'risk_titles': risk_titles,
            'progress': 15
        })
    
    # Step 2: Generate each risk instance progressively
    schema_fields = [
        "RiskTitle", "RiskDescription", "PossibleDamage", "RiskPriority", "Criticality",
        "Category", "Origin", "RiskLikelihood", "RiskImpact", "RiskExposureRating",
        "RiskMultiplierX", "RiskMultiplierY", "Appetite", "RiskResponseType",
        "RiskResponseDescription", "RiskMitigation", "RiskType", "RiskOwner",
        "BusinessImpact", "RiskStatus", "MitigationStatus", "ModifiedMitigations",
        "RiskFormDetails", "Reviewer"
    ]
    
    all_instances = []
    base_progress = 20
    progress_per_instance = 70 / risk_count
    
    for idx in range(risk_count):
        if stream_callback:
            stream_callback('risk_start', {
                'index': idx,
                'title': risk_titles[idx] if idx < len(risk_titles) else f"Risk Instance {idx + 1}",
                'progress': base_progress + (idx * progress_per_instance)
            })
        
        # Generate each field for this risk instance
        risk_instance = {}
        per_field = {}
        fields_per_progress = len(schema_fields)
        field_progress_step = progress_per_instance / fields_per_progress
        
        for field_idx, field_name in enumerate(schema_fields):
            field_prompt = f"""
You are a GRC risk specialist. For risk instance #{idx + 1} "{risk_titles[idx] if idx < len(risk_titles) else f'Risk Instance {idx + 1}'}", 
extract ONLY the field "{field_name}".

Return ONLY a JSON object:
{{
  "value": <your answer>,
  "confidence": 0.0-1.0,
  "rationale": "brief explanation"
}}

Field guidance for "{field_name}":
{RISK_FIELD_GUIDANCE.get("risk_instance", {}).get(field_name, "Return a professional value.")}

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
                        stream_callback('field_generated', {
                            'risk_index': idx,
                            'field_name': field_name,
                            'value': value,
                            'confidence': confidence,
                            'rationale': rationale,
                            'progress': base_progress + (idx * progress_per_instance) + ((field_idx + 1) * field_progress_step)
                        })
                        
            except Exception as e:
                print(f"[AI-TASK] Error generating field {field_name}: {e}")
                if stream_callback:
                    stream_callback('field_error', {
                        'risk_index': idx,
                        'field_name': field_name,
                        'error': str(e)
                    })
        
        risk_instance.setdefault("_meta", {})
        risk_instance["_meta"]["per_field"] = per_field
        all_instances.append(risk_instance)
        
        if stream_callback:
            stream_callback('risk_complete', {
                'index': idx,
                'risk_instance': risk_instance,
                'progress': base_progress + ((idx + 1) * progress_per_instance)
            })
    
    if stream_callback:
        stream_callback('complete', {
            'risk_instances': all_instances,
            'progress': 100
        })
    
    print(f"[AI-TASK] ingest_risk_instance_document_streaming: DONE - {len(all_instances)} instances")
    return all_instances


def ingest_risk_instance_document_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    document_text = payload.get("document_text", "")
    print(f"[AI-TASK] ingest_risk_instance_document: document_len={len(document_text)}")
    prompt = f"""
You are a GRC risk specialist. Read the following document and extract a list of risk instances suitable for a risk instance register.

Return ONLY a JSON array of risk instance objects with this structure:
[
  {{
    "RiskTitle": "",
    "RiskDescription": "",
    "PossibleDamage": "",
    "RiskPriority": "Low|Medium|High|Critical",
    "Criticality": "Low|Medium|High|Critical",
    "Category": "",
    "Origin": "Internal|External|Third-Party|Regulatory|Market|Operational",
    "RiskLikelihood": 1,
    "RiskImpact": 1,
    "RiskExposureRating": 0.0,
    "RiskMultiplierX": 1.0,
    "RiskMultiplierY": 1.0,
    "Appetite": "Low|Medium|High",
    "RiskResponseType": "Avoid|Mitigate|Transfer|Accept",
    "RiskResponseDescription": "",
    "RiskMitigation": [],
    "RiskType": "Current|Residual|Inherent|Emerging|Accepted",
    "RiskOwner": "",
    "BusinessImpact": "",
    "RiskStatus": "Not Assigned|Assigned|Approved|Rejected",
    "MitigationStatus": "Pending|Yet to Start|Work In Progress|Revision Required by Reviewer|Revision Required by User|Completed",
    "ModifiedMitigations": [],
    "RiskFormDetails": {{}},
    "Reviewer": ""
  }}
]

Rules:
- Infer risk instances as concrete occurrences or scenarios described in the document.
- RiskLikelihood and RiskImpact must be integers between 1 and 10.
- RiskExposureRating must be a float between 0 and 100, consistent with likelihood and impact.
- RiskMitigation must be a JSON array (can be empty if not clear).
- Return ONLY the JSON array, no markdown, no comments, no extra keys.

DOCUMENT:
\"\"\"{document_text}\"\"\"
"""
    result = _generate_json(service, "risk.ingest_risk_instance_document", prompt, options)

    # Normalize LLM output: model may return list, single dict, or wrapper like {"Risk Instances": [...]}
    raw_list: list[dict[str, Any]]
    if isinstance(result, list):
        raw_list = [item for item in result if isinstance(item, dict)]
        print(f"[AI-TASK] ingest_risk_instance_document: model returned list with {len(raw_list)} item(s)")
    elif isinstance(result, dict):
        # Extract list from wrapper keys (common LLM response shapes)
        for key in ("Risk Instances", "risk_instances", "riskInstances", "instances"):
            val = result.get(key)
            if isinstance(val, list):
                raw_list = [item for item in val if isinstance(item, dict)]
                print(f"[AI-TASK] ingest_risk_instance_document: extracted list from '{key}' ({len(raw_list)} items)")
                break
        else:
            # Single risk instance dict (has RiskTitle etc)
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
        "RiskTitle",
        "RiskDescription",
        "PossibleDamage",
        "RiskPriority",
        "Criticality",
        "Category",
        "Origin",
        "RiskLikelihood",
        "RiskImpact",
        "RiskExposureRating",
        "RiskMultiplierX",
        "RiskMultiplierY",
        "Appetite",
        "RiskResponseType",
        "RiskResponseDescription",
        "RiskMitigation",
        "RiskType",
        "RiskOwner",
        "BusinessImpact",
        "RiskStatus",
        "MitigationStatus",
        "ModifiedMitigations",
        "RiskFormDetails",
        "Reviewer",
    ]

    enriched_instances: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_list, start=1):
        per_field: dict[str, Any] = {}
        for field in schema_fields:
            value = item.get(field)
            if value not in (None, "", [], {}):
                per_field[field] = {
                    "source": "AI_GENERATED",
                    "confidence": 0.8,
                    "rationale": "Generated from document context by centralized risk instance ingestion task.",
                }
        item.setdefault("_meta", {})
        item["_meta"]["per_field"] = per_field
        enriched_instances.append(item)

    print(f"[AI-TASK] ingest_risk_instance_document: DONE - enriched {len(enriched_instances)} risk instance(s) with _meta.per_field")
    return enriched_instances


RISK_TASKS = {
    "risk.analyze_security_incident": analyze_security_incident_task,
    "risk.infer_field": infer_risk_field_task,
    "risk.ingest_risk_document": ingest_risk_document_task,
    "risk.ingest_risk_instance_document": ingest_risk_instance_document_task,
    "risk.ingest_risk_instance_document_streaming": ingest_risk_instance_document_streaming,
}
