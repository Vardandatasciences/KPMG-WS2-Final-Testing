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
    section_title = payload.get("section_title", "")
    section_text = payload.get("section_text", "")
    prompt = f"""
Return only JSON with this structure:
{{
  "section_title": "{section_title}",
  "policies": [
    {{
      "policy_title": "",
      "policy_description": "",
      "scope": "",
      "objective": "",
      "policy_type": "",
      "policy_category": "",
      "policy_subcategory": "",
      "subpolicies": [
        {{
          "subpolicy_title": "",
          "subpolicy_description": "",
          "control": ""
        }}
      ]
    }}
  ]
}}

Extract the policy hierarchy from this section content:
{section_text}
"""
    return _generate_json(service, "policy.extract_policy_hierarchy", prompt, options)


def generate_subpolicy_compliances(service, payload: dict[str, Any], metadata: dict[str, Any] | None = None, options: AIRequestOptions | None = None):
    subpolicy_title = payload.get("subpolicy_title", "")
    subpolicy_description = payload.get("subpolicy_description", "")
    control = payload.get("control", "")
    prompt = f"""
Return only JSON with this structure:
{{
  "compliances": [
    {{
      "ComplianceTitle": "",
      "ComplianceItemDescription": "",
      "ComplianceType": "",
      "Scope": "",
      "Objective": "",
      "BusinessUnitsCovered": "",
      "Criticality": "Low",
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

Generate compliance records for this policy control.
Subpolicy title: {subpolicy_title}
Subpolicy description: {subpolicy_description}
Control text: {control}
"""
    result = _generate_json(service, "policy.generate_subpolicy_compliances", prompt, options)
    if isinstance(result, dict):
        return result.get("compliances", [])
    return result if isinstance(result, list) else []


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
}
