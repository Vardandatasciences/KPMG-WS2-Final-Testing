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

    prompt = f"""Analyze the following security incident for a banking GRC system and provide a comprehensive JSON response with detailed justifications for each assessment.

**INCIDENT DETAILS:**
{incident_details}

**REGULATORY CONTEXT:** {rag_context}

**REQUIRED JSON STRUCTURE WITH JUSTIFICATIONS:**
{{
  "riskPriority": "P2",
  "riskPriorityJustification": "P2 assigned due to limited customer impact (<1K affected), moderate financial exposure ($50K-100K), and containable operational disruption. Response required within 48 hours per banking incident protocols.",
  
  "criticality": "High", 
  "criticalityJustification": "High criticality due to potential regulatory compliance implications under PCI DSS, customer data exposure risks, and operational impact on core banking services. Meets criteria for priority escalation to senior management.",
  
  "costOfIncident": 75000,
  "costJustification": "Cost estimate based on: incident response team hours ($15K), forensic investigation ($25K), customer notification costs ($10K), regulatory reporting ($5K), system remediation ($15K), and potential fine provisions ($5K). Based on industry benchmarks for similar banking incidents.",
  
  "possibleDamage": "Financial losses including regulatory fines ($10K-50K), customer trust erosion affecting retention rates, potential reputational damage requiring PR response, operational disruption to banking services, compliance violations requiring audit response, and system remediation costs.",
  "possibleDamageJustification": "Damage assessment considers banking sector regulatory requirements (PCI DSS, SOX, FFIEC), historical incident cost data from financial services industry, customer impact analysis, and operational resilience requirements. Regulatory penalties estimated based on violation severity and compliance history.",
  
  "systemsInvolved": ["Core Banking System", "Customer Authentication Service", "Payment Processing Gateway"],
  "systemsInvolvedJustification": "Systems identified based on incident description analysis, typical banking infrastructure dependencies, and regulatory compliance requirements. Assessment considers data flow analysis and system interdependencies critical to banking operations.",
  
  "initialImpactAssessment": "Immediate operational impact includes service degradation affecting customer transactions, potential data exposure requiring breach notification protocols, and regulatory reporting obligations. Estimated 2-hour response window for containment per banking crisis management procedures.",
  "initialImpactAssessmentJustification": "Impact assessment follows banking industry standard incident response framework (NIST Cybersecurity Framework), considering operational resilience requirements, customer impact thresholds, and regulatory notification timelines under banking regulations.",
  
  "mitigationSteps": ["Immediate system isolation and forensic preservation", "Customer impact assessment and notification preparation", "Regulatory body notification within required timeframes", "Enhanced monitoring implementation", "Third-party security audit scheduling"],
  "mitigationStepsJustification": "Mitigation strategy addresses immediate containment (NIST Respond function), regulatory compliance obligations (PCI DSS breach notification), operational recovery (business continuity), and long-term security enhancement. Timeline aligned with banking incident response best practices and regulatory requirements.",
  
  "comments": "Incident requires immediate escalation due to potential regulatory implications and customer data exposure. Recommend engaging external forensic specialists and legal counsel for compliance guidance. Enhanced monitoring should continue for 90 days post-resolution.",
  "commentsJustification": "Expert analysis considers banking sector risk tolerance, regulatory scrutiny levels, and industry best practices for incident response. Recommendations based on FFIEC guidance for cybersecurity incident response and lessons learned from similar banking sector incidents.",
  
  "violatedPolicies": ["Information Security Policy Section 4.2", "Data Classification and Handling Standard", "Incident Response Procedure IRP-001"],
  "violatedPoliciesJustification": "Policy violations identified through gap analysis against incident timeline, comparing actual response to documented procedures. Assessment considers policy compliance monitoring and training effectiveness in incident prevention.",
  
  "procedureControlFailures": ["Multi-factor authentication bypass", "Inadequate access logging", "Delayed incident detection"],
  "procedureControlFailuresJustification": "Control failures identified through root cause analysis methodology, examining both technical controls (authentication, monitoring) and operational controls (detection, response). Analysis follows banking regulatory guidance for control effectiveness assessment.",
  
  "lessonsLearned": ["Implement real-time anomaly detection", "Enhance staff incident recognition training", "Review third-party access controls", "Update incident escalation criteria"],
  "lessonsLearnedJustification": "Lessons derived from incident timeline analysis, control failure assessment, and industry best practices for similar incidents. Focus on preventive measures and detection improvements aligned with banking cybersecurity frameworks."
}}

**CLASSIFICATION GUIDELINES:**
- P0: Critical banking operations down, >10K customers affected, >$1M regulatory penalty
- P1: Significant impact, 1K-10K customers affected, $100K-$1M penalty  
- P2: Limited impact, <1K customers affected, $10K-100K exposure
- P3: Minor impact, internal only, <$10K exposure

**QUALITY REQUIREMENTS:**
- ALL justification fields are MANDATORY - you MUST provide detailed reasoning for every field
- Each justification must be 3-4 sentences explaining methodology, sources, and specific rationale  
- Reference banking regulations (PCI DSS, SOX, FFIEC, BASEL III) and frameworks (NIST, ISO27001)
- Include quantitative estimates: dollar amounts, timeframes, affected user counts, system counts
- costOfIncident MUST be a pure numeric value without currency symbols
- Use specific technical terms and regulatory language appropriate for banking GRC professionals

**ANALYSIS METHODOLOGY:**
For each assessment, explain: (1) What criteria you used, (2) Which regulatory requirements apply, (3) What industry benchmarks you referenced, (4) How you calculated estimates, (5) What risk factors you considered.

**CRITICAL INSTRUCTIONS:**
1. Return ONLY the JSON object - no additional text before or after
2. Replace ALL example values with your actual analysis of the incident  
3. Every justification field MUST contain specific, detailed reasoning - never leave empty
4. Use the exact field names shown - do not modify or omit any fields
5. Ensure valid JSON syntax with proper commas and quotes
"""
    print(f"[AI-TASK] analyze_for_creation: incident_len={len(incident_details)}")
    raw_result = _generate_json(service, "incident.analyze_for_creation", prompt, options)
    
    # Log raw AI response for debugging
    print(f"[AI-TASK] RAW AI RESPONSE: {raw_result}")
    
    # Normalize the AI response to ensure consistent structure (similar to risk analysis)
    normalized_result = _normalize_incident_analysis_response(raw_result)
    
    print(f"[AI-TASK] analyze_for_creation: raw_keys={list(raw_result.keys() if isinstance(raw_result, dict) else [])}")
    print(f"[AI-TASK] analyze_for_creation: normalized_keys={list(normalized_result.keys() if isinstance(normalized_result, dict) else [])}")
    
    # Check specifically for justification fields
    justification_fields = [key for key in normalized_result.keys() if 'Justification' in key]
    print(f"[AI-TASK] JUSTIFICATION FIELDS FOUND: {justification_fields}")
    for field in justification_fields:
        value = normalized_result.get(field, "")
        print(f"[AI-TASK] {field}: {value[:100]}..." if len(str(value)) > 100 else f"[AI-TASK] {field}: {value}")
    
    print(f"[AI-TASK] analyze_for_creation: DONE")
    
    return normalized_result


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