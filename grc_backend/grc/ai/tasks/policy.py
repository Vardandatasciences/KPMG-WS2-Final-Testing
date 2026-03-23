from typing import Any

from ..types import AIRequestOptions


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


def extract_framework_structure(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    document_text = payload.get("document_text", "")
    prompt = f"""
Return only JSON with this structure:
{{
  "framework_name": "",
  "framework_description": "",
  "category": "",
  "identifier_prefix": "",
  "sections": [{{"section_title": "", "section_summary": ""}}]
}}

Extract a concise framework structure from this source document:
{document_text}
"""
    return _generate_json(service, "policy.extract_framework_structure", prompt, options)


def extract_policy_hierarchy(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    """
    Centralized AI task: extract policy hierarchy from section text.
    Returns policies and subpolicies with justification analysis (what/where/how selected).
    Caller: policy_extractor_enhanced (upload framework) or any payload-based client.
    """
    section_title = payload.get("section_title", "")
    section_text = payload.get("section_text", "") or "(no text)"
    print(f"[AI-TASK] extract_policy_hierarchy: section_title={section_title[:60]}..., section_text_len={len(section_text)}")
    prompt = f"""
Extract the FULL policy hierarchy from this section. You MUST extract ALL policies and ALL subpolicies/controls you find. Do NOT skip any. If the text has multiple requirements or controls, create a separate subpolicy for each.

RULES (VERY IMPORTANT):
- Return ONLY a valid JSON object. No markdown, no ```json, no extra text before or after.
- Use double quotes for all keys and string values.
- ALWAYS populate "policies" array with at least one policy.
- NEVER use a top-level key called "controls". ALL individual requirements MUST be represented as items in the "subpolicies" array for each policy.
- If the source text contains a list of controls/requirements, create ONE subpolicy per control/requirement.
- For subpolicy_title: use the control identifier, requirement ID, or a short descriptive title that is meaningful in UI.
- For control: include the full requirement text. If long, summarize the key points but keep the most important regulatory phrases.
- If section_text is sparse or unclear, infer structure from headers, numbering, bullets or strong phrases.
- For each policy and each subpolicy you MUST include "ai_analysis" with:
  - "extraction_rationale": one clear sentence explaining WHY this policy/subpolicy was created (the reason).
  - "source_excerpt": a short quote from the section text that led to this selection (HOW/source), or "" only if there is absolutely no quote that makes sense.
  
QUALITY RULES:
- Prefer SPECIFIC, regulatory-style titles (e.g. "PCI DSS - Protect Stored Cardholder Data") instead of generic ones.
- Group logically related controls under the same policy when they belong to the same standard or topic.
- Avoid duplicating identical subpolicies; merge closely similar sentences into a single, richer subpolicy.

REQUIRED JSON STRUCTURE (FOLLOW EXACTLY THESE KEYS):
{{
  "section_title": "{section_title}",
  "policies": [
    {{
      "policy_title": "Short, specific, business-friendly policy name (e.g. 'PCI DSS - Secure Storage of Cardholder Data')",
      "policy_description": "2-4 sentences summarising the main intent of the policy in plain language.",
      "scope": "Which entities / systems / data this policy applies to.",
      "objective": "What this policy is trying to achieve (risk reduction / compliance outcomes).",
      "policy_type": "One of: 'Regulatory', 'Internal', 'Industry Standard', 'Contractual'.",
      "policy_category": "High-level category (e.g. 'Information Security', 'Compliance', 'Privacy', 'Operational Risk').",
      "policy_subcategory": "More specific grouping under the category (e.g. 'Payment Card Security', 'Access Control').",
      "ai_analysis": {{
        "extraction_rationale": "ONE short sentence explaining WHY this policy exists and what problem it addresses.",
        "source_excerpt": "Short quote from the section text that best represents this policy, or \"\" if nothing is suitable."
      }},
      "subpolicies": [
        {{
          "subpolicy_title": "Short requirement/controls name (e.g. 'Secure Storage of Cardholder Data').",
          "subpolicy_description": "1-3 sentences describing what this specific requirement/ control enforces.",
          "control": "The full requirement text or a faithful summary of the key sentences from the source.",
          "ai_analysis": {{
            "extraction_rationale": "ONE short sentence explaining WHY this subpolicy/control is important.",
            "source_excerpt": "Short quote from the section text that led to this subpolicy, or \"\" if nothing is suitable."
          }}
        }}
      ]
    }}
  ]
}}

SECTION CONTENT:
{section_text}

Return the JSON object now."""
    result = _generate_json(service, "policy.extract_policy_hierarchy", prompt, options)
    policies_count = len(result.get("policies", [])) if isinstance(result, dict) else 0
    subpolicies_count = sum(len(p.get("subpolicies", [])) for p in (result.get("policies", []) or [])) if isinstance(result, dict) else 0
    print(f"[AI-TASK] extract_policy_hierarchy: DONE - policies={policies_count}, subpolicies={subpolicies_count}")
    return result


def generate_subpolicy_compliances(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    subpolicy_title = payload.get("subpolicy_title", "") or "Policy requirement"
    subpolicy_description = payload.get("subpolicy_description", "") or "(no description)"
    control = payload.get("control", "") or subpolicy_description or subpolicy_title
    prompt = f"""
You are a GRC compliance expert. Generate compliance records for the following policy control. You MUST return at least ONE compliance record. Never return an empty compliances array.

RULES:
- Return ONLY a valid JSON object. No markdown, no ```json, no extra text.
- Use double quotes for keys and strings. No trailing commas.
- ALWAYS include "compliances" as an array with at least 1 item.
- Populate ComplianceItemDescription and ComplianceTitle from the control. Never leave them empty.
- Use Criticality: High/Medium/Low based on the control's regulatory importance.

INPUT:
Subpolicy title: {subpolicy_title}
Subpolicy description: {subpolicy_description}
Control text: {control}

REQUIRED JSON STRUCTURE:
{{
  "compliances": [
    {{
      "ComplianceTitle": "",
      "ComplianceItemDescription": "",
      "ComplianceType": "Automated",
      "Scope": "",
      "Objective": "",
      "BusinessUnitsCovered": "",
      "Criticality": "Medium",
      "MandatoryOptional": "Mandatory",
      "ManualAutomatic": "Manual",
      "Impact": 5,
      "Probability": 5,
      "MaturityLevel": "Developing",
      "Applicability": "Global",
      "PotentialRiskScenarios": "",
      "RiskType": "Current",
      "RiskCategory": "Operational",
      "RiskBusinessImpact": "",
      "PossibleDamage": "",
      "risk_details": {{
        "risk_summary": "",
        "source_logic": "",
        "evidence_source": ""
      }}
    }}
  ]
}}

Return the JSON object now."""
    print(f"[AI-TASK] generate_subpolicy_compliances: subpolicy={subpolicy_title[:50]}..., control_len={len(control)}")
    result = _generate_json(service, "policy.generate_subpolicy_compliances", prompt, options)
    compliances = result.get("compliances", []) if isinstance(result, dict) else (result if isinstance(result, list) else [])
    print(f"[AI-TASK] generate_subpolicy_compliances: DONE - compliances_count={len(compliances)}")
    return compliances


def generate_compliance_risk_details(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    prompt = f"""
Return only JSON:
{{
  "risk_summary": "",
  "business_impact": "",
  "possible_damage": "",
  "recommended_mitigation": ""
}}

Generate risk details for this compliance item:
{payload}
"""
    return _generate_json(service, "policy.generate_compliance_risk_details", prompt, options)


def suggest_policy_metadata(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    prompt = f"""
Return only JSON:
{{
  "policy_type": "",
  "policy_category": "",
  "policy_subcategory": "",
  "applicability": "",
  "department": ""
}}

Suggest policy metadata for:
{payload}
"""
    return _generate_json(service, "policy.suggest_policy_metadata", prompt, options)


def suggest_scope_and_objective(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    prompt = f"""
Return only JSON:
{{
  "scope": "",
  "objective": ""
}}

Write a concise scope and objective for this policy payload:
{payload}
"""
    return _generate_json(service, "policy.suggest_scope_and_objective", prompt, options)


def summarize_framework_changes(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    prompt = f"""
Return only JSON:
{{
  "summary": "",
  "new_requirements": [],
  "modified_requirements": [],
  "review_focus_areas": []
}}

Summarize the framework changes:
{payload}
"""
    return _generate_json(service, "policy.summarize_framework_changes", prompt, options)


def generate_policy_gap_analysis(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    prompt = f"""
Return only JSON:
{{
  "coverage_summary": "",
  "covered_areas": [],
  "partial_gaps": [],
  "missing_controls": [],
  "recommended_actions": []
}}

Compare the following framework controls against existing policies and provide a gap analysis:
{payload}
"""
    return _generate_json(service, "policy.generate_policy_gap_analysis", prompt, options)


def draft_policy_from_framework_control(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    prompt = f"""
Return only JSON:
{{
  "policy_title": "",
  "policy_description": "",
  "scope": "",
  "objective": "",
  "subpolicies": [
    {{
      "subpolicy_title": "",
      "subpolicy_description": "",
      "control": ""
    }}
  ],
  "evidence_source": "",
  "drafting_logic": ""
}}

Draft a policy from these framework controls:
{payload}
"""
    return _generate_json(service, "policy.draft_policy_from_framework_control", prompt, options)


def review_policy_quality(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    prompt = f"""
Return only JSON:
{{
  "quality_score": 0,
  "strengths": [],
  "issues": [],
  "recommended_improvements": []
}}

Review this policy draft for quality, completeness, and governance readiness:
{payload}
"""
    return _generate_json(service, "policy.review_policy_quality", prompt, options)


def suggest_policy_version_delta(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    prompt = f"""
Return only JSON:
{{
  "change_summary": "",
  "major_deltas": [],
  "minor_deltas": [],
  "review_notes": []
}}

Summarize the version delta between these policy versions:
{payload}
"""
    return _generate_json(service, "policy.suggest_policy_version_delta", prompt, options)


def explain_generated_output_with_evidence(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    prompt = f"""
Return only JSON:
{{
  "explanation": "",
  "evidence_points": [],
  "assumptions": [],
  "human_review_needed": []
}}

Explain the generated policy output and cite the evidence used:
{payload}
"""
    return _generate_json(service, "policy.explain_generated_output_with_evidence", prompt, options)


def generate_policy_with_compliances(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    """
    High-level helper used across the product:
    - Drafts a policy and subpolicies from the given input (usually framework controls or regulatory text)
    - Generates AI compliances for each subpolicy

    Returns a single JSON object with:
    {
      "policy": { ... },
      "subpolicies": [
        {
          "subpolicy_title": "",
          "subpolicy_description": "",
          "control": "",
          "compliances": [ ... ]
        }
      ]
    }
    """
    # Step 1: Draft policy and subpolicies from the input payload
    draft = draft_policy_from_framework_control(service, payload, metadata=metadata, options=options) or {}

    policy_data = {
      "policy_title": draft.get("policy_title", ""),
      "policy_description": draft.get("policy_description", ""),
      "scope": draft.get("scope", ""),
      "objective": draft.get("objective", ""),
      # Preserve any extra keys from the draft in case callers rely on them
      **{k: v for k, v in draft.items() if k not in {"policy_title", "policy_description", "scope", "objective", "subpolicies"}},
    }

    subpolicies_with_compliances: list[dict[str, Any]] = []
    for sub in draft.get("subpolicies", []) or []:
        subpolicy_title = sub.get("subpolicy_title", "")
        subpolicy_description = sub.get("subpolicy_description", "")
        control = sub.get("control", "")

        if not subpolicy_title and not subpolicy_description and not control:
            continue

        try:
            compliances = generate_subpolicy_compliances(
                service,
                {
                    "subpolicy_title": subpolicy_title,
                    "subpolicy_description": subpolicy_description,
                    "control": control,
                },
                metadata=metadata,
                options=options,
            )
        except Exception:
            compliances = []

        enriched_subpolicy = dict(sub)
        enriched_subpolicy["compliances"] = compliances or []
        subpolicies_with_compliances.append(enriched_subpolicy)

    return {
        "policy": policy_data,
        "subpolicies": subpolicies_with_compliances,
    }


POLICY_TASKS = {
    "policy.extract_framework_structure": extract_framework_structure,
    "policy.extract_policy_hierarchy": extract_policy_hierarchy,
    "policy.generate_subpolicy_compliances": generate_subpolicy_compliances,
    "policy.generate_compliance_risk_details": generate_compliance_risk_details,
    "policy.suggest_policy_metadata": suggest_policy_metadata,
    "policy.suggest_scope_and_objective": suggest_scope_and_objective,
    "policy.summarize_framework_changes": summarize_framework_changes,
    "policy.generate_policy_gap_analysis": generate_policy_gap_analysis,
    "policy.draft_policy_from_framework_control": draft_policy_from_framework_control,
    "policy.review_policy_quality": review_policy_quality,
    "policy.suggest_policy_version_delta": suggest_policy_version_delta,
    "policy.explain_generated_output_with_evidence": explain_generated_output_with_evidence,
    "policy.generate_policy_with_compliances": generate_policy_with_compliances,
}
