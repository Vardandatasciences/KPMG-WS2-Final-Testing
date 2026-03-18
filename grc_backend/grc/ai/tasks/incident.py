"""
Centralized AI tasks for Incident module.
Defines incident-specific AI tasks with prompts, field guidance, and document processing.
"""

import json
from typing import Any, Dict
from ..types import AIRequestOptions


# Incident field-specific guidance and validation rules
INCIDENT_FIELD_GUIDANCE = {
    "IncidentTitle": {
        "instruction": "Extract or generate a clear, concise incident title (max 255 characters). Format: '[Incident Type] - [Key Impact] - [Timeframe if available]'. Example: 'Data Breach - 10,000 Customer Records Exposed - Q3 2024'. Be specific and professional.",
        "validation": "string",
        "max_length": 255,
        "required": True
    },
    "Description": {
        "instruction": "Extract or generate a comprehensive incident description covering: (1) What happened, (2) When it was detected, (3) How it was discovered, (4) Affected systems/processes, (5) Immediate consequences. Write 3-5 factual sentences with specific details like timestamps and system names.",
        "validation": "string",
        "required": True
    },
    "IncidentCategory": {
        "instruction": "Choose the incident category from the available options. This reflects the TYPE of incident event (e.g., 'Cyber Attack' for phishing, even if it creates operational risk).",
        "validation": "choice",
        "choices": ["Security Breach", "Data Loss", "System Outage", "Compliance Violation", "Operational Failure", "Third-Party Issue", "Human Error", "Natural Disaster", "Cyber Attack", "Privacy Incident", "Safety Incident", "Financial Loss"],
        "required": True
    },
    "Status": {
        "instruction": "Determine current incident status based on the document context.",
        "validation": "choice",
        "choices": ["New", "In Progress", "Under Investigation", "Resolved", "Closed", "Escalated", "Risk Mitigated"],
        "required": True
    },
    "Criticality": {
        "instruction": "Assess criticality level. Criteria: Critical (threatens core business/safety), High (significant operational/financial/reputational impact), Medium (moderate impact with workarounds), Low (minimal impact).",
        "validation": "choice",
        "choices": ["Low", "Medium", "High", "Critical"],
        "required": True
    },
    "RiskPriority": {
        "instruction": "Assess priority level. Criteria: Critical (immediate threat to operations/safety), High (significant impact, prompt action needed), Medium (notable impact, manageable timeline), Low (minor impact, minimal urgency).",
        "validation": "choice",
        "choices": ["Low", "Medium", "High", "Critical"],
        "required": True
    },
    "Origin": {
        "instruction": "Classify the incident origin. Guidelines: AUDIT_FINDING (discovered during audit), MANUAL (person reported), AUTOMATED (system detected), EXTERNAL_REPORT (outside party), INTERNAL_DETECTION (internal monitoring).",
        "validation": "choice",
        "choices": ["MANUAL", "AUDIT_FINDING", "AUTOMATED", "EXTERNAL_REPORT", "INTERNAL_DETECTION"],
        "required": True
    },
    "RiskCategory": {
        "instruction": "Select the PRIMARY risk category based on the core nature of the incident. Choose the most significant risk domain.",
        "validation": "choice",
        "choices": ["Operational", "Financial", "Strategic", "Compliance", "Technical", "Reputational", "Information Security", "Process Risk", "Third-Party", "Regulatory", "Governance"],
        "required": False
    },
    "AffectedBusinessUnit": {
        "instruction": "Extract specific business units/departments impacted. Be precise with actual names: 'Customer Service - EMEA Region', 'IT Infrastructure', 'Finance - Accounts Payable'. Multiple units: comma-separated. Organization-wide: 'Enterprise-Wide'. Unknown: 'To be determined'.",
        "validation": "string",
        "required": False
    },
    "SystemsAssetsInvolved": {
        "instruction": "List specific systems, applications, or infrastructure affected. Include technical details: version numbers, hostnames, identifiers. Example: 'SAP ERP Production (sap-prod-01), Customer DB v3.2, Payment Gateway API'. Comma-separated. Unknown: 'To be determined'.",
        "validation": "string",
        "required": False
    },
    "GeographicLocation": {
        "instruction": "Specify physical/logical location of incident. Include: country, region, city, data center, or office. Examples: 'London Office - UK', 'AWS US-East-1', 'Global - Multiple Regions'. Be as specific as possible.",
        "validation": "string",
        "required": False
    },
    "InitialImpactAssessment": {
        "instruction": "Provide structured initial assessment (3-4 sentences) covering: (1) immediate operational impact, (2) affected stakeholders/customers with numbers, (3) data/system integrity concerns, (4) preliminary scope. Be factual and quantitative where possible.",
        "validation": "string",
        "required": False
    },
    "PossibleDamage": {
        "instruction": "Describe all potential damages (2-3 sentences): operational, financial, reputational, legal, compliance impacts. Include realized and avoided consequences with quantitative estimates. Example: 'Service outage 50K users 4hrs, revenue loss $200K, potential fines $500K, brand damage'.",
        "validation": "string",
        "required": False
    },
    "InternalContacts": {
        "instruction": "List key internal personnel involved/notified. Format: 'John Smith (IT Manager), Jane Doe (CISO), Security Operations Team'. If names unavailable, list roles/departments. Comma-separated.",
        "validation": "string",
        "required": False
    },
    "ExternalPartiesInvolved": {
        "instruction": "Identify external organizations/vendors/partners involved in incident or response. Examples: 'Microsoft Support', 'Acme Cloud Services', 'External Auditors', 'Law Enforcement'. Include their role if mentioned. Empty string if purely internal.",
        "validation": "string",
        "required": False
    },
    "RegulatoryBodies": {
        "instruction": "List regulatory authorities/compliance bodies/government agencies requiring notification or involvement. Examples: 'SEC', 'GDPR DPA', 'FDA', 'PCI DSS Council'. Include notification requirements if mentioned. Empty string if none required.",
        "validation": "string",
        "required": False
    },
    "RelevantPoliciesProceduresViolated": {
        "instruction": "Identify specific policies/procedures/standards violated. Include policy names/numbers: 'Password Policy v2.3 (Section 4.2)', 'Change Management Procedure violation'. Be specific to identify systemic issues.",
        "validation": "string",
        "required": False
    },
    "ControlFailures": {
        "instruction": "Describe failed security controls/safeguards (2-3 sentences). Be technical and specific: 'Multi-factor authentication bypass', 'Firewall rule misconfiguration', 'Failed backup verification'. Explain why controls didn't prevent the incident.",
        "validation": "string",
        "required": False
    },
    "LessonsLearned": {
        "instruction": "Summarize key insights and learnings (2-4 sentences). What could be done differently? What worked well? What process improvements needed? Focus on actionable takeaways for future prevention.",
        "validation": "string",
        "required": False
    },
    "IncidentClassification": {
        "instruction": "Extract classification code or generate severity-based classification. Examples: 'CAT-1: Critical Security Incident', 'P1: Production Outage', 'Type A: Data Breach'. Format: 'Category: Description'. If not mentioned, infer appropriate classification.",
        "validation": "string",
        "required": False
    },
    "CostOfIncident": {
        "instruction": "Extract or estimate financial cost/impact. Format: '$50,000', '€25K', or 'Estimated $100K-$150K'. If specific cost mentioned, use it. If impact described but no cost, provide reasonable estimate. If no financial info, return 'Not assessed'.",
        "validation": "string",
        "required": False
    },
    "Comments": {
        "instruction": "Extract or provide 2-3 sentences of additional context: unusual circumstances, related incidents, influencing factors, or observations that add value beyond the main description. Be concise and informative.",
        "validation": "string",
        "required": False
    },
    "Attachments": {
        "instruction": "Extract file names or document references mentioned in the incident. Return as semicolon-separated list (e.g., 'report.pdf;evidence.xlsx;screenshot.png'). If none mentioned, return empty string ''.",
        "validation": "string",
        "required": False
    },
    "RepeatedNot": {
        "instruction": "Determine if this is a recurring incident. Return boolean true if document mentions: 'recurring', 'happened before', 'previous occurrence', 'similar to incident X'. Return false if first-time or no indication of recurrence.",
        "validation": "boolean",
        "required": False
    },
    "ReopenedNot": {
        "instruction": "Determine if incident was reopened. Return boolean true ONLY if document explicitly states it was previously closed then reopened. Keywords: 'reopened', 'recurred after closure'. Return false for new incidents or ongoing ones.",
        "validation": "boolean",
        "required": False
    },
    "RejectionSource": {
        "instruction": "Identify rejection/escalation source. Return 'INCIDENT' if rejected from incident workflow, 'RISK' if escalated from risk assessment. Return null if not applicable.",
        "validation": "choice",
        "choices": ["INCIDENT", "RISK"],
        "required": False
    },
    "Mitigation": {
        "instruction": "Extract or generate a JSON array of mitigation steps. Each step must have: 'step' (action description), 'status' (Completed/Planned/In Progress), 'responsible' (team/person), 'deadline' (YYYY-MM-DD format). Return array with at least 2-3 concrete actions.",
        "validation": "json_array",
        "required": False
    },
    "IncidentFormDetails": {
        "instruction": "Generate JSON object with incident details. Required keys: 'reported_by' (name/role), 'detection_method' (how discovered), 'response_time_minutes' (number), 'escalation_level' (L1/L2/L3), 'containment_status' (Contained/Not Contained), 'root_cause_category', 'affected_records_count' (number), 'recovery_time_objective' (duration). Fill based on context.",
        "validation": "json_object",
        "required": False
    }
}


def _serialize_current_record(record: dict) -> str:
    """Helper to format current record data for prompts."""
    filled_fields = {k: v for k, v in record.items() if v not in (None, "", [])}
    if filled_fields:
        return f"\nALREADY EXTRACTED FIELDS:\n{json.dumps(filled_fields, indent=2)}"
    return ""


def _build_incident_field_prompt(field_name: str, payload: dict) -> str:
    """Build dynamic prompt for incident field inference using centralized guidance."""
    document_text = payload.get("document_text", "")
    current_record = payload.get("current_record", {})
    
    guidance = INCIDENT_FIELD_GUIDANCE.get(field_name, {})
    instruction = guidance.get("instruction", "Return a concise, professional value.")
    validation = guidance.get("validation", "string")
    choices = guidance.get("choices", [])
    
    # Build prompt based on field type
    prompt = f"""Analyze the incident document and extract ONLY the "{field_name}" field.

DOCUMENT CONTEXT:
\"\"\"{document_text[:3000]}\"\"\"
{_serialize_current_record(current_record)}

INSTRUCTIONS FOR "{field_name}":
{instruction}"""

    if choices:
        prompt += f"\n\nVALID OPTIONS: {', '.join(choices)}"
    
    if validation == "boolean":
        prompt += f"""

REQUIRED OUTPUT FORMAT:
Return ONLY a JSON object in this exact format:
{{
  "value": true or false,
  "confidence": <number between 0.0 and 1.0>
}}"""
    elif validation == "json_array":
        prompt += f"""

REQUIRED OUTPUT FORMAT:
Return ONLY a JSON object in this exact format:
{{
  "value": [array of objects],
  "confidence": <number between 0.0 and 1.0>
}}"""
    elif validation == "json_object":
        prompt += f"""

REQUIRED OUTPUT FORMAT:
Return ONLY a JSON object in this exact format:
{{
  "value": {{object with required keys}},
  "confidence": <number between 0.0 and 1.0>
}}"""
    else:
        prompt += f"""

REQUIRED OUTPUT FORMAT:
Return ONLY a JSON object in this exact format:
{{
  "value": "<extracted or inferred value>",
  "confidence": <number between 0.0 and 1.0>
}}"""
    
    prompt += """

Rules:
1. If the field is explicitly mentioned in the document, extract it (confidence 0.8-1.0)
2. If you must infer based on context, do so (confidence 0.5-0.7)
3. If you cannot determine, return {"value": null, "confidence": 0.0}
4. Return ONLY the JSON object, no other text"""
    
    return prompt


def _ensure_options(options: AIRequestOptions | None, task_name: str) -> AIRequestOptions:
    if options is None:
        return AIRequestOptions(task_name=task_name)
    options.task_name = task_name
    return options


def _generate_json(service, task_name: str, prompt: str, options: AIRequestOptions | None = None):
    """Helper to generate JSON response using AI service."""
    return service.generate_json(
        task_name=task_name,
        prompt=prompt,
        options=_ensure_options(options, task_name),
    )


def infer_incident_field_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    """
    Centralized task for inferring a single incident field using AI.
    
    Payload should contain:
    - field_name: The field to infer
    - document_text: Document context
    - current_record: Already extracted fields
    """
    field_name = payload.get("field_name")
    if not field_name:
        raise ValueError("field_name is required in payload")
    print(f"[AI-TASK] infer_incident_field START: field={field_name}")
    prompt = _build_incident_field_prompt(field_name, payload)
    result = _generate_json(service, "incident.infer_field", prompt, options)
    
    # Extract value from AI response format
    if isinstance(result, dict) and "value" in result:
        val = result.get("value")
        print(f"[AI-TASK] infer_incident_field DONE: field={field_name} -> value={repr(val)[:80]}")
        return val
    elif isinstance(result, dict) and field_name in result:
        val = result.get(field_name)
        print(f"[AI-TASK] infer_incident_field DONE (fallback): field={field_name} -> value={repr(val)[:80]}")
        return val
    
    print(f"[AI-TASK] infer_incident_field DONE (raw): field={field_name} -> result={repr(result)[:80]}")
    return result


def ingest_incident_document_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    """
    Centralized task for extracting incidents from a full document.
    
    Payload should contain:
    - document_text: Preprocessed document content
    """
    document_text = payload.get("document_text", "")
    single_block = payload.get("single_incident_block", False)
    print(f"[AI-TASK] ingest_incident_document: document_len={len(document_text)}, single_incident_block={single_block}")

    # Build comprehensive incident extraction prompt
    choices_str = {
        "Criticality": ["Low", "Medium", "High", "Critical"],
        "RiskPriority": ["Low", "Medium", "High", "Critical"],
        "Status": ["New", "In Progress", "Under Investigation", "Resolved", "Closed", "Escalated", "Risk Mitigated"],
        "Origin": ["MANUAL", "AUDIT_FINDING", "AUTOMATED", "EXTERNAL_REPORT", "INTERNAL_DETECTION"],
        "IncidentCategory": ["Security Breach", "Data Loss", "System Outage", "Compliance Violation", "Operational Failure", "Third-Party Issue", "Human Error", "Natural Disaster", "Cyber Attack", "Privacy Incident", "Safety Incident", "Financial Loss"],
        "RiskCategory": ["Operational", "Financial", "Strategic", "Compliance", "Technical", "Reputational", "Information Security", "Process Risk", "Third-Party", "Regulatory", "Governance"]
    }
    
    if single_block:
        intro = "The following text is a SINGLE incident block (one incident only). Extract this ONE incident and return a JSON array with exactly one object."
    else:
        intro = "Analyze the following document and extract ALL incidents mentioned. Return EVERY distinct incident; if the document describes 3 incidents, return an array of 3 objects. Do NOT merge multiple incidents into one."

    prompt = f"""You are a GRC (Governance, Risk, Compliance) incident analyst. {intro}

DOCUMENT TO ANALYZE:
\"\"\"{document_text}\"\"\"

EXTRACTION REQUIREMENTS:

1. {"This block contains exactly ONE incident. Return a JSON array with one object." if single_block else "IDENTIFY ALL INCIDENTS - Return EVERY distinct incident. Each incident must be a separate object in the array."}

2. FOR EACH INCIDENT, extract ALL of these fields (use empty string or default if not found):
   - IncidentTitle: Clear title (max 255 chars, REQUIRED)
   - Description: Comprehensive description (3-5 sentences, REQUIRED)
   - IncidentCategory: EXACTLY ONE OF: {', '.join(choices_str["IncidentCategory"])}
   - Status: EXACTLY ONE OF: {', '.join(choices_str["Status"])}
   - Criticality: EXACTLY ONE OF: {', '.join(choices_str["Criticality"])}
   - RiskPriority: EXACTLY ONE OF: {', '.join(choices_str["RiskPriority"])}
   - Origin: EXACTLY ONE OF: {', '.join(choices_str["Origin"])}
   - RiskCategory: ONE OF: {', '.join(choices_str["RiskCategory"])} (or empty string)
   - AffectedBusinessUnit, SystemsAssetsInvolved, GeographicLocation: Specific text values
   - InitialImpactAssessment, PossibleDamage: Detailed descriptions (2-4 sentences)
   - InternalContacts, ExternalPartiesInvolved, RegulatoryBodies: Lists or empty strings
   - RelevantPoliciesProceduresViolated, ControlFailures, LessonsLearned: Text descriptions
   - IncidentClassification, CostOfIncident, Comments, Attachments: Text values
   - RepeatedNot, ReopenedNot: boolean (true/false)
   - RejectionSource: "INCIDENT", "RISK", or null
   - Mitigation: JSON array with step objects
   - IncidentFormDetails: JSON object with incident metadata

3. ADD METADATA for each field in _meta.per_field:
   - source: "EXTRACTED" if the value was explicitly stated or found verbatim in the document
   - source: "AI_GENERATED" only if you had to infer, guess, or generate the value (not in document)
   - confidence: 0.0-1.0 (higher for EXTRACTED, lower for inferred)
   - rationale: Brief explanation (e.g. "Found in document header" vs "Inferred from context")

4. OUTPUT FORMAT:
Return ONLY a JSON array of incident objects. Start with [ and end with ].
Do NOT wrap the array in an object (e.g. do NOT return {{"Incident": [...]}}).
Use field name "IncidentTitle" (not "Title") for the incident title.

Example - return this structure:
[
  {{
    "IncidentTitle": "...",
    "Description": "...",
    "IncidentCategory": "...",
    "Status": "...",
    "Criticality": "...",
    "RiskPriority": "...",
    "Origin": "...",
    "RiskCategory": "...",
    "AffectedBusinessUnit": "...",
    "SystemsAssetsInvolved": "...",
    "GeographicLocation": "...",
    "InitialImpactAssessment": "...",
    "PossibleDamage": "...",
    "InternalContacts": "...",
    "ExternalPartiesInvolved": "...",
    "RegulatoryBodies": "...",
    "RelevantPoliciesProceduresViolated": "...",
    "ControlFailures": "...",
    "LessonsLearned": "...",
    "IncidentClassification": "...",
    "CostOfIncident": "...",
    "Comments": "...",
    "Attachments": "...",
    "RepeatedNot": false,
    "ReopenedNot": false,
    "RejectionSource": null,
    "Mitigation": [],
    "IncidentFormDetails": {{}},
    "_meta": {{
      "per_field": {{
        "IncidentTitle": {{"source": "EXTRACTED", "confidence": 0.9, "rationale": "Found in document header"}},
        "Description": {{"source": "AI_GENERATED", "confidence": 0.7, "rationale": "Inferred from context"}}
      }}
    }}
  }}
]

CRITICAL RULES:
- Return ONLY a raw JSON array [ {...}, {...} ] - no outer object, no "Incident" or "incidents" wrapper
- Use "IncidentTitle" for the title field (not "Title")
- Return ONLY valid JSON, no markdown, no code blocks, no explanations
- Use double quotes for all strings
- Boolean values must be true/false (lowercase)
- No trailing commas
- Ensure all choice fields match EXACTLY the allowed values
- If a field cannot be determined, use reasonable defaults or empty strings
- For JSON fields (Mitigation, IncidentFormDetails), ensure proper nested structure
- Each incident object MUST include all fields above (IncidentTitle through IncidentFormDetails)
- Return one object per distinct incident - never merge multiple incidents into one

Begin analysis now and return the JSON array:"""

    result = _generate_json(service, "incident.ingest_document", prompt, options)

    # Normalize: LLM may return array, {Incident: [...]}, {incidents: [...]}, or single dict
    if isinstance(result, list):
        incidents = [item for item in result if isinstance(item, dict)]
    elif isinstance(result, dict):
        # Handle common LLM wrappers: {"Incident": [...]} or {"incidents": [...]}
        if "Incident" in result and isinstance(result["Incident"], list):
            incidents = [item for item in result["Incident"] if isinstance(item, dict)]
            print(f"[AI-INCIDENT] Unwrapped result[\"Incident\"] -> {len(incidents)} incident(s)")
        elif "incidents" in result and isinstance(result["incidents"], list):
            raw = result["incidents"]
            incidents = [item for item in raw if isinstance(item, dict)] if raw else []
        else:
            incidents = [result]
    else:
        incidents = []
    print(f"[AI-TASK] ingest_incident_document: DONE - incidents={len(incidents)}")
    for i, inc in enumerate(incidents, 1):
        filled = [k for k, v in inc.items() if k not in ("_meta", "_trace") and v not in (None, "", [], {})]
        print(f"[AI-TASK]   Incident {i} fields from LLM: {', '.join(filled)}")

    RESERVED_KEYS = {"_meta", "_trace"}
    schema_fields = list(INCIDENT_FIELD_GUIDANCE.keys())
    # Map common LLM key variants to canonical names (route expects PascalCase)
    KEY_ALIASES = {
        "id": "IncidentTitle",  # LLM often returns id (e.g. CAR-145) as incident identifier
        "incident_title": "IncidentTitle",
        "incidentTitle": "IncidentTitle",
        "title": "IncidentTitle",
        "Title": "IncidentTitle",  # LLM often returns "Title" when wrapped in {"Incident": [...]}
        "description": "Description",
        "incident_category": "IncidentCategory",
        "incidentCategory": "IncidentCategory",
        "status": "Status",
        "criticality": "Criticality",
        "risk_priority": "RiskPriority",
        "riskPriority": "RiskPriority",
        "Risk Priority": "RiskPriority",
        "possible_damage": "PossibleDamage",
        "Possible Damage": "PossibleDamage",
        "origin": "Origin",
        "risk_category": "RiskCategory",
        "riskCategory": "RiskCategory",
        "affected_business_unit": "AffectedBusinessUnit",
        "systems_assets_involved": "SystemsAssetsInvolved",
        "geographic_location": "GeographicLocation",
        "initial_impact_assessment": "InitialImpactAssessment",
        "internal_contacts": "InternalContacts",
        "external_parties_involved": "ExternalPartiesInvolved",
        "regulatory_bodies": "RegulatoryBodies",
        "mitigation": "Mitigation",
        "comments": "Comments",
        "attachments": "Attachments",
        "repeated_not": "RepeatedNot",
        "reopened_not": "ReopenedNot",
        "rejection_source": "RejectionSource",
        "cost_of_incident": "CostOfIncident",
        "incident_form_details": "IncidentFormDetails",
    }

    enriched: list = []
    for idx, item in enumerate(incidents, start=1):
        if not isinstance(item, dict):
            continue
        if idx == 1:
            print(f"[AI-INCIDENT] First incident keys from LLM: {list(k for k in item.keys() if k not in RESERVED_KEYS)}")
        # Normalize keys: copy alias -> canonical so route finds values
        for alias, canonical in KEY_ALIASES.items():
            if alias in item and canonical not in item and item.get(alias) not in (None, "", [], {}):
                item[canonical] = item[alias]
        print(f"[AI-INCIDENT] Enriching incident #{idx} with per-field metadata")
        existing = item.get("_meta", {}).get("per_field", {})
        per_field: dict = {}
        default_ai_meta = {
            "source": "AI_GENERATED",
            "confidence": 0.8,
            "rationale": "Generated from document context by centralized incident ingestion task.",
        }

        def _meta_for(key: str, value) -> dict:
            """Use EXTRACTED from LLM if present and plausible, else AI_GENERATED."""
            if key in existing and isinstance(existing[key], dict):
                src = existing[key].get("source", "").upper()
                if src == "EXTRACTED":
                    return existing[key]
            return default_ai_meta.copy()

        # Use actual keys from item (prefer LLM's EXTRACTED when provided)
        for key, value in item.items():
            if key in RESERVED_KEYS:
                continue
            if value not in (None, "", [], {}):
                per_field[key] = _meta_for(key, value)
                src = per_field[key].get("source", "")
                print(f"[AI-INCIDENT]   Field '{key}' {src} value: {str(value)[:100]}")
        # Also check schema_fields for canonical names
        for field in schema_fields:
            if field in per_field:
                continue
            value = item.get(field)
            if value not in (None, "", [], {}):
                per_field[field] = _meta_for(field, value)
                src = per_field[field].get("source", "")
                print(f"[AI-INCIDENT]   Field '{field}' {src} value: {str(value)[:100]}")
        # Include any LLM metadata for keys we didn't process
        for k, v in existing.items():
            if k not in per_field:
                per_field[k] = v
        item.setdefault("_meta", {})
        item["_meta"]["per_field"] = per_field
        print(
            f"[AI-INCIDENT]   Metadata summary for incident #{idx}: "
            f"{len(per_field)} fields tagged as AI_GENERATED"
        )
        enriched.append(item)

    print(f"[AI-INCIDENT] ingest_incident_document_task: returning {len(enriched)} enriched incident(s)")
    return enriched


def analyze_incident_for_creation_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
):
    """
    Centralized task for inline incident analysis (title + description).
    Used by Create Incident when user enters title/description and clicks "Generate Analysis".
    Returns comprehensive incident analysis for mapping to form fields.
    Same schema as incident_slm.analyze_incident_comprehensive for Create Incident UI compatibility.
    """
    incident_title = payload.get("incident_title", "")
    incident_description = payload.get("incident_description", "")
    rag_context = payload.get("rag_context", "")

    incident_details = f"""Title: {incident_title}

Description: {incident_description}"""

    prompt = f"""You are a senior GRC and incident response expert with:
- 15+ years of hands-on experience in banking cybersecurity, operational risk, and regulatory compliance
- Deep expertise in incident response frameworks (NIST, ISO 27035, SANS), banking regulations (PCI DSS, SOX, FFIEC, BASEL III), and crisis management
- Proven track record in incident cost analysis, impact assessment, and regulatory reporting for financial institutions

Your job is to analyze the incident below and produce a high-quality, realistic, and business-ready incident analysis for a banking organization.

INCIDENT TO ANALYZE:
{incident_details}

RETRIEVED CONTEXT (USE ONLY IF RELEVANT):
{rag_context}

CRITICAL INSTRUCTIONS - READ CAREFULLY:
You MUST return a JSON object with EXACTLY these 12 fields. DO NOT SKIP ANY FIELD. Missing even one field will cause system failure.

REQUIRED JSON STRUCTURE (fill ALL fields):
{{
  "riskPriority": "P0|P1|P2|P3",
  "riskPriorityJustification": "3-4 sentences explaining priority classification with specific criteria and timeline requirements",
  "criticality": "Critical|High|Medium|Low",
  "criticalityJustification": "3-4 sentences explaining criticality assessment with business and regulatory impact analysis",
  "costOfIncident": 75000,
  "costJustification": "3-4 sentences breaking down cost components with industry benchmarks and calculation methodology",
  "possibleDamage": "3-4 sentences describing operational, financial, regulatory, and reputational damages with quantitative estimates",
  "possibleDamageJustification": "2-3 sentences explaining damage assessment methodology and regulatory considerations",
  "systemsInvolved": ["System 1", "System 2", "System 3"],
  "systemsInvolvedJustification": "2-3 sentences explaining system identification and interdependency analysis",
  "initialImpactAssessment": "3-4 sentences covering immediate operational impact, stakeholder effects, and response requirements",
  "initialImpactAssessmentJustification": "2-3 sentences explaining assessment framework and regulatory compliance considerations",
  "mitigationSteps": ["Step 1", "Step 2", "Step 3", "Step 4"],
  "mitigationStepsJustification": "3-4 sentences explaining mitigation strategy, timeline, and regulatory alignment",
  "comments": "2-3 sentences with additional context, recommendations, or observations",
  "commentsJustification": "2-3 sentences explaining expert recommendations and industry best practices",
  "violatedPolicies": ["Policy 1", "Policy 2", "Policy 3"],
  "violatedPoliciesJustification": "2-3 sentences explaining policy gap analysis and compliance implications",
  "procedureControlFailures": ["Failure 1", "Failure 2", "Failure 3"],
  "procedureControlFailuresJustification": "3-4 sentences explaining root cause analysis and control effectiveness assessment",
  "lessonsLearned": ["Lesson 1", "Lesson 2", "Lesson 3"],
  "lessonsLearnedJustification": "3-4 sentences explaining improvement opportunities and preventive measures"
}}

PRIORITY CLASSIFICATION GUIDELINES:
- P0: Critical banking operations down, >10K customers affected, >$1M regulatory exposure, immediate threat to business continuity
- P1: Significant operational impact, 1K-10K customers affected, $100K-$1M exposure, major system compromise
- P2: Limited operational impact, <1K customers affected, $10K-100K exposure, contained security incident
- P3: Minor impact, internal only, <$10K exposure, policy violation or minor system issue

QUALITY AND RELEVANCE REQUIREMENTS:
1. WRITE LIKE A SENIOR PROFESSIONAL: Use clear, business-appropriate language suitable for C-suite and regulators
2. BE SPECIFIC BUT REALISTIC: Base estimates on the incident details provided; avoid invented precise numbers when evidence is weak
3. NO HALLUCINATIONS: Do not invent specific systems, regulations, or consequences not reasonably implied by the incident
4. QUANTITATIVE WHEN POSSIBLE: Include dollar amounts, timeframes, user counts, but acknowledge uncertainty when appropriate
5. REGULATORY AWARENESS: Reference appropriate banking regulations and frameworks when relevant to the incident type
6. INDUSTRY CONTEXT: Use typical banking incident patterns and cost benchmarks, but keep them generic if specific details are missing

FIELD-SPECIFIC EXPECTATIONS:
- costOfIncident: Pure numeric value (no currency symbols), realistic for incident type and scope
- systemsInvolved: 3-6 specific systems based on incident type, avoid generic names unless incident lacks detail
- mitigationSteps: 4-6 actionable steps in logical sequence, specific to incident type and banking environment
- violatedPolicies: 2-5 relevant policies, use generic banking policy names if specific ones not mentioned
- procedureControlFailures: 2-4 specific control failures that enabled the incident
- lessonsLearned: 3-5 actionable improvements focused on prevention and detection

VALIDATION CHECKLIST - VERIFY BEFORE RESPONDING:
✓ All 12 fields are present and filled
✓ No field contains null, empty string, or placeholder text
✓ costOfIncident is a pure number
✓ All array fields contain 2-6 relevant items
✓ All justification fields have meaningful 2-4 sentence explanations
✓ JSON syntax is valid (proper quotes, commas, brackets)
✓ Content is realistic and based on incident details provided

Return ONLY the JSON object with all fields filled. NO explanations outside the JSON.
"""
    print(f"[AI-TASK] analyze_for_creation: incident_len={len(incident_details)}")
    raw_result = _generate_json(service, "incident.analyze_for_creation", prompt, options)
    
    # Log raw AI response for debugging
    print(f"[AI-TASK] RAW AI RESPONSE: {raw_result}")
    
    # Normalize the AI response to ensure consistent structure (similar to risk analysis)
    normalized_result = _normalize_incident_analysis_response(raw_result)
    
    print(f"[AI-TASK] analyze_for_creation: raw_keys={list(raw_result.keys() if isinstance(raw_result, dict) else [])}")
    print(f"[AI-TASK] analyze_for_creation: normalized_keys={list(normalized_result.keys() if isinstance(normalized_result, dict) else [])}")
    
    # Check for missing required fields and fill them
    required_fields = [
        "riskPriority", "riskPriorityJustification", "criticality", "criticalityJustification", 
        "costOfIncident", "costJustification", "possibleDamage", "possibleDamageJustification",
        "systemsInvolved", "systemsInvolvedJustification", "initialImpactAssessment", "initialImpactAssessmentJustification",
        "mitigationSteps", "mitigationStepsJustification", "comments", "commentsJustification",
        "violatedPolicies", "violatedPoliciesJustification", "procedureControlFailures", "procedureControlFailuresJustification",
        "lessonsLearned", "lessonsLearnedJustification"
    ]
    
    missing = [f for f in required_fields if f not in normalized_result or normalized_result.get(f) in (None, "", [])]
    if missing:
        print(f"[AI-TASK] analyze_for_creation: WARNING - missing fields: {missing}")
        _fill_missing_incident_fields(normalized_result, incident_title, incident_description)
        print(f"[AI-TASK] analyze_for_creation: filled missing fields, final_keys={list(normalized_result.keys())}")
    
    # Check specifically for justification fields
    justification_fields = [key for key in normalized_result.keys() if 'Justification' in key]
    print(f"[AI-TASK] JUSTIFICATION FIELDS FOUND: {justification_fields}")
    for field in justification_fields:
        value = normalized_result.get(field, "")
        print(f"[AI-TASK] {field}: {value[:100]}..." if len(str(value)) > 100 else f"[AI-TASK] {field}: {value}")
    
    print(f"[AI-TASK] analyze_for_creation: DONE")
    
    return normalized_result


def _fill_missing_incident_fields(result: dict, incident_title: str, incident_description: str):
    """Fill any missing required incident fields with sensible defaults based on what we have"""
    
    # Get existing values for context
    criticality = result.get("criticality", "Medium")
    risk_priority = result.get("riskPriority", "P2")
    
    # Analyze incident content for context
    incident_text = (incident_title + " " + incident_description).lower()
    
    # Determine incident type and severity
    is_security_breach = any(word in incident_text for word in ["breach", "hack", "attack", "malware", "phishing", "unauthorized"])
    is_data_incident = any(word in incident_text for word in ["data", "leak", "exposure", "privacy", "customer"])
    is_system_outage = any(word in incident_text for word in ["outage", "down", "failure", "unavailable", "crash"])
    is_compliance = any(word in incident_text for word in ["compliance", "violation", "audit", "regulatory"])
    
    # Set defaults based on criticality and incident type
    if criticality in ["Critical", "High"] or is_security_breach:
        default_cost = 500000 if is_data_incident else 250000
        default_priority = "P1" if criticality == "Critical" else "P2"
        default_systems = ["Core Banking System", "Security Infrastructure", "Customer Database", "Monitoring Systems"]
        default_damage = "Significant operational disruption, potential regulatory penalties, customer impact, and reputational damage requiring immediate executive attention and comprehensive response."
    elif criticality == "Medium":
        default_cost = 100000
        default_priority = "P2"
        default_systems = ["Affected Business System", "Network Infrastructure", "User Access Systems"]
        default_damage = "Moderate operational impact with contained scope, manageable customer effects, and standard incident response procedures."
    else:  # Low
        default_cost = 25000
        default_priority = "P3"
        default_systems = ["Local System", "User Workstation", "Application Service"]
        default_damage = "Limited operational impact with minimal customer effect and routine remediation procedures."
    
    # Fill missing fields with intelligent defaults
    if not result.get("riskPriority"):
        result["riskPriority"] = default_priority
    
    if not result.get("riskPriorityJustification"):
        result["riskPriorityJustification"] = f"Priority {result['riskPriority']} assigned based on incident scope, customer impact assessment, and regulatory requirements. Classification follows banking incident response protocols and business continuity procedures."
    
    if not result.get("criticality"):
        result["criticality"] = criticality
    
    if not result.get("criticalityJustification"):
        result["criticalityJustification"] = f"{result['criticality']} criticality determined through impact analysis considering operational disruption, regulatory implications, customer exposure, and business continuity requirements per banking risk assessment standards."
    
    if not result.get("costOfIncident"):
        result["costOfIncident"] = default_cost
    
    if not result.get("costJustification"):
        result["costJustification"] = f"Cost estimate of ${default_cost:,} based on typical incident response expenses including investigation, remediation, regulatory reporting, customer communication, and system recovery. Estimate follows banking industry benchmarks for similar incident types."
    
    if not result.get("possibleDamage"):
        result["possibleDamage"] = default_damage
    
    if not result.get("possibleDamageJustification"):
        result["possibleDamageJustification"] = "Damage assessment considers operational impact, regulatory exposure, customer trust implications, and financial consequences based on banking industry incident analysis frameworks and regulatory guidance."
    
    if not result.get("systemsInvolved") or not isinstance(result.get("systemsInvolved"), list):
        result["systemsInvolved"] = default_systems[:4]  # Limit to 4 systems
    
    if not result.get("systemsInvolvedJustification"):
        result["systemsInvolvedJustification"] = "Systems identified based on incident description analysis, typical banking infrastructure dependencies, and operational impact assessment. Analysis considers system interdependencies and regulatory compliance requirements."
    
    if not result.get("initialImpactAssessment"):
        result["initialImpactAssessment"] = f"Initial assessment indicates {criticality.lower()} impact incident affecting banking operations with potential customer service disruption. Immediate response activated per incident management procedures with estimated containment timeline of 2-4 hours."
    
    if not result.get("initialImpactAssessmentJustification"):
        result["initialImpactAssessmentJustification"] = "Impact assessment follows banking incident response framework considering operational resilience, customer service levels, regulatory notification requirements, and business continuity protocols."
    
    if not result.get("mitigationSteps") or not isinstance(result.get("mitigationSteps"), list):
        result["mitigationSteps"] = [
            "Activate incident response team and establish command center",
            "Implement immediate containment measures to prevent escalation",
            "Conduct impact assessment and stakeholder notification",
            "Execute recovery procedures and restore normal operations",
            "Document incident details and conduct post-incident review"
        ]
    
    if not result.get("mitigationStepsJustification"):
        result["mitigationStepsJustification"] = "Mitigation strategy follows NIST incident response framework with banking-specific considerations for regulatory compliance, customer communication, and operational recovery. Timeline aligned with business continuity requirements and regulatory notification obligations."
    
    if not result.get("comments"):
        result["comments"] = "Incident requires standard banking incident response procedures with appropriate escalation based on impact assessment. Recommend following established protocols for customer communication and regulatory reporting as applicable."
    
    if not result.get("commentsJustification"):
        result["commentsJustification"] = "Expert recommendations based on banking industry best practices, regulatory requirements, and incident response experience. Guidance considers operational resilience and regulatory compliance obligations."
    
    if not result.get("violatedPolicies") or not isinstance(result.get("violatedPolicies"), list):
        if is_security_breach:
            result["violatedPolicies"] = ["Information Security Policy", "Access Control Policy", "Incident Response Policy"]
        elif is_compliance:
            result["violatedPolicies"] = ["Regulatory Compliance Policy", "Risk Management Policy", "Audit Policy"]
        else:
            result["violatedPolicies"] = ["Operational Risk Policy", "Business Continuity Policy", "Incident Management Policy"]
    
    if not result.get("violatedPoliciesJustification"):
        result["violatedPoliciesJustification"] = "Policy violations identified through gap analysis comparing incident circumstances to established procedures and controls. Assessment considers policy compliance monitoring and effectiveness of existing safeguards."
    
    if not result.get("procedureControlFailures") or not isinstance(result.get("procedureControlFailures"), list):
        if is_security_breach:
            result["procedureControlFailures"] = ["Access control mechanisms", "Security monitoring systems", "Threat detection controls"]
        elif is_system_outage:
            result["procedureControlFailures"] = ["System monitoring controls", "Backup and recovery procedures", "Change management controls"]
        else:
            result["procedureControlFailures"] = ["Operational controls", "Monitoring procedures", "Risk assessment processes"]
    
    if not result.get("procedureControlFailuresJustification"):
        result["procedureControlFailuresJustification"] = "Control failures identified through root cause analysis examining both technical and operational controls. Analysis follows banking regulatory guidance for control effectiveness assessment and considers prevention, detection, and response capabilities."
    
    if not result.get("lessonsLearned") or not isinstance(result.get("lessonsLearned"), list):
        result["lessonsLearned"] = [
            "Enhance monitoring and detection capabilities for early incident identification",
            "Review and update incident response procedures based on response effectiveness",
            "Strengthen preventive controls to reduce likelihood of similar incidents",
            "Improve staff training and awareness for better incident recognition and response"
        ]
    
    if not result.get("lessonsLearnedJustification"):
        result["lessonsLearnedJustification"] = "Lessons derived from incident analysis, response effectiveness review, and industry best practices for similar incidents. Focus on preventive measures, detection improvements, and response optimization aligned with banking operational resilience requirements."


def _normalize_incident_analysis_response(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize incident AI analysis response to ensure consistent flat structure.
    Handles cases where AI returns nested objects, arrays, or embedded JSON strings.
    Similar to risk analysis normalization.
    """
    FLAT_INCIDENT_ANALYSIS_KEYS = [
        "riskPriority", "riskPriorityJustification", "criticality", "criticalityJustification", 
        "costOfIncident", "costJustification", "possibleDamage", "possibleDamageJustification",
        "systemsInvolved", "systemsInvolvedJustification", "initialImpactAssessment", "initialImpactAssessmentJustification",
        "mitigationSteps", "mitigationStepsJustification", "comments", "commentsJustification",
        "violatedPolicies", "violatedPoliciesJustification", "procedureControlFailures", "procedureControlFailuresJustification",
        "lessonsLearned", "lessonsLearnedJustification"
    ]
    
    if not isinstance(raw, dict):
        return raw
        
    out = dict(raw)
    print(f"[NORMALIZE] Raw incident response keys: {list(raw.keys())}")

    # 1) Extract from context[0] if the real analysis is nested there
    context = out.get("context")
    if isinstance(context, list) and len(context) > 0:
        inner = context[0]
        if isinstance(inner, dict):
            print(f"[NORMALIZE] Found context[0] dict with keys: {list(inner.keys())}")
            for key in FLAT_INCIDENT_ANALYSIS_KEYS:
                if key not in out or out.get(key) in (None, ""):
                    if key in inner and inner[key] not in (None, ""):
                        out[key] = inner[key]
                        
            # Parse embedded JSON in text field
            text = inner.get("text") if isinstance(inner.get("text"), str) else ""
            if text and ("Analysis:" in text or '"riskPriority"' in text or '"criticality"' in text):
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
                                print(f"[NORMALIZE] Parsed JSON from text with keys: {list(parsed.keys())}")
                                for key in FLAT_INCIDENT_ANALYSIS_KEYS:
                                    if key not in out or out.get(key) in (None, ""):
                                        if key in parsed and parsed[key] not in (None, ""):
                                            out[key] = parsed[key]
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"[NORMALIZE] Failed to parse JSON from text: {e}")
                    
        elif isinstance(inner, str):  # If inner is a string, try to parse as JSON
            try:
                parsed = json.loads(inner)
                if isinstance(parsed, dict):
                    print(f"[NORMALIZE] Parsed context[0] string as JSON with keys: {list(parsed.keys())}")
                    for key in FLAT_INCIDENT_ANALYSIS_KEYS:
                        if key not in out or out.get(key) in (None, ""):
                            if key in parsed and parsed[key] not in (None, ""):
                                out[key] = parsed[key]
            except json.JSONDecodeError:
                print(f"[NORMALIZE] Failed to parse context[0] string as JSON")

    # 2) Map common alternate keys to expected keys (incident-specific)
    aliases = [
        ("riskCategory", "category"),
        ("incidentAnalysis", "analysis"),
        ("systemsAffected", "systemsInvolved"),
        ("impactAssessment", "initialImpactAssessment"),
        ("recommendedActions", "mitigationSteps"),
        ("policyViolations", "violatedPolicies"),
        ("controlFailures", "procedureControlFailures"),
        ("lessons", "lessonsLearned"),
        # Justification field aliases
        ("riskPriorityReason", "riskPriorityJustification"),
        ("criticalityReason", "criticalityJustification"),
        ("costReason", "costJustification"),
        ("damageReason", "possibleDamageJustification"),
        ("systemsReason", "systemsInvolvedJustification"),
        ("impactReason", "initialImpactAssessmentJustification"),
        ("mitigationReason", "mitigationStepsJustification"),
        ("commentsReason", "commentsJustification"),
        ("policiesReason", "violatedPoliciesJustification"),
        ("controlsReason", "procedureControlFailuresJustification"),
        ("lessonsReason", "lessonsLearnedJustification")
    ]
    for alt, canonical in aliases:
        if (canonical not in out or out.get(canonical) in (None, "")) and alt in out and out[alt] not in (None, ""):
            out[canonical] = out[alt]
            print(f"[NORMALIZE] Mapped {alt} -> {canonical}")
            
    # 3) Try to extract justifications from any field that might contain them (case-insensitive search)
    all_keys = list(out.keys())
    for key in all_keys:
        lower_key = key.lower()
        value = out[key]
        if isinstance(value, str) and value.strip():
            # Map justification-like fields to proper justification keys
            for target_field in FLAT_INCIDENT_ANALYSIS_KEYS:
                if target_field.endswith('Justification'):
                    base_field = target_field.replace('Justification', '').lower()
                    if (base_field in lower_key and 
                        ('justif' in lower_key or 'reason' in lower_key or 'rational' in lower_key or 'explain' in lower_key) and
                        (target_field not in out or out.get(target_field) in (None, ""))):
                        out[target_field] = value
                        print(f"[NORMALIZE] Extracted justification: {key} -> {target_field}")
                        break

    # 4) Ensure numeric types for cost
    for key in ("costOfIncident",):
        if key in out and out[key] is not None and out[key] != "":
            try: 
                out[key] = int(float(out[key]))
                print(f"[NORMALIZE] Converted {key} to integer: {out[key]}")
            except (TypeError, ValueError): 
                print(f"[NORMALIZE] Failed to convert {key} to integer: {out[key]}")
                
    # 5) Log results
    missing_keys = [key for key in FLAT_INCIDENT_ANALYSIS_KEYS if key not in out or out.get(key) in (None, "")]
    justification_keys = [key for key in FLAT_INCIDENT_ANALYSIS_KEYS if key.endswith('Justification')]
    missing_justifications = [key for key in justification_keys if key not in out or out.get(key) in (None, "")]
    
    if missing_keys:
        print(f"[NORMALIZE] WARNING: Still missing keys after normalization: {missing_keys}")
    if missing_justifications:
        print(f"[NORMALIZE] WARNING: Missing justification fields: {missing_justifications}")
    else:
        print(f"[NORMALIZE] SUCCESS: All incident justification keys present")
        
    print(f"[NORMALIZE] Final normalized keys: {list(out.keys())}")
    return out


# Registry of all incident AI tasks (keys must match run_task usage)
INCIDENT_TASKS = {
    "incident.infer_field": infer_incident_field_task,
    "incident.ingest_document": ingest_incident_document_task,
    "incident.analyze_for_creation": analyze_incident_for_creation_task,
}