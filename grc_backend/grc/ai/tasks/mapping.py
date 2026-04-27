"""
Centralized AI tasks for Cross-Framework Mapping and Framework Comparison.
Provides AI-powered semantic alignment and gap analysis between different frameworks.
"""

import json
from typing import Any, Dict, List, Optional
from ..types import AIRequestOptions


def _ensure_options(options: AIRequestOptions | None, task_name: str) -> AIRequestOptions:
    """Ensure AIRequestOptions exists with task name."""
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


def cross_framework_mapping_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
) -> dict[str, Any]:
    """
    Perform semantic mapping between two different frameworks.
    
    Payload should contain:
    - source_framework: List of requirements from the primary framework
    - target_framework: List of requirements from the target framework
    - source_name: Name of source framework
    - target_name: Name of target framework
    """
    source_framework = payload.get("source_framework", [])
    target_framework = payload.get("target_framework", [])
    source_name = payload.get("source_name", "Source Framework")
    target_name = payload.get("target_name", "Target Framework")
    
    print(f"[AI-TASK] cross_framework_mapping START: {source_name} -> {target_name}")
    
    prompt = f"""As a senior compliance architect, perform a semantic cross-mapping between the {source_name} and {target_name} frameworks.
    
SOURCE FRAMEWORK REQUIREMENTS:
{json.dumps(source_framework[:50], indent=2)}

TARGET FRAMEWORK REQUIREMENTS:
{json.dumps(target_framework[:50], indent=2)}

Identify semantic equivalencies, overlaps, and gaps. Return a JSON structure:
{{
  "mapping_stats": {{
    "total_source_requirements": {len(source_framework)},
    "mapped_count": 12,
    "partial_match_count": 5,
    "gap_count": 3
  }},
  "mappings": [
    {{
      "source_id": "REQ-01",
      "target_id": "T-REQ-10",
      "similarity_score": 0.95,
      "mapping_type": "equivalent",
      "justification": "Both requirements specify 256-bit encryption for data at rest."
    }}
  ],
  "gaps": [
    {{
      "source_id": "REQ-05",
      "description": "Requirement not found in target framework",
      "impact_level": "high"
    }}
  ]
}}"""

    try:
        return _generate_json(service, "mapping.cross_framework", prompt, options)
    except Exception as e:
        print(f"[AI-TASK] Mapping failed: {e}")
        return {"error": str(e), "success": False}


def analyze_framework_comparison_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
) -> dict[str, Any]:
    """
    Perform strict version comparison and semantic gap analysis between two frameworks.
    """
    f1_data = payload.get("framework1_data", {})
    f2_data = payload.get("framework2_data", {})
    f1_name = f1_data.get("name", "Framework V1")
    f2_name = f2_data.get("name", "Framework V2")
    
    compliances1 = f1_data.get("compliances", [])
    compliances2 = f2_data.get("compliances", [])

    print(f"[AI-TASK] analyze_framework_comparison START: {f1_name} vs {f2_name}")
    print(f"[AI-TASK] Comparing {len(compliances1)} items in V1 to {len(compliances2)} items in V2")
    
    prompt = f"""You are a specialized GRC Auditor performing a Version Comparison Audit between {f1_name} and {f2_name}.

TASK:
Identify exactly what has changed between Version 1 ({f1_name}) and Version 2 ({f2_name}).
Every item in {f2_name} MUST be accounted for.

INPUT DATA:
VERSION 1 ({f1_name}):
{json.dumps(compliances1, indent=1)}

VERSION 2 ({f2_name}):
{json.dumps(compliances2, indent=1)}

STRICT RULES:
1. USE ONLY PROVIDED IDs: You MUST use the 'id' and 'identifier' from the input data. Never invent IDs like 'new-001'.
2. SEMANTIC ANALYSIS: Identify if a requirement in V2 is:
   - 'UNCHANGED': Practically the same text/meaning as V1.
   - 'MODIFIED': Exists in V1 but the wording or obligation changed significantly. Describe the exact delta.
   - 'NEW': Does not have a semantic equivalent in V1.
   - 'REMOVED': Exists in V1 but has no equivalent in V2.
3. OUTPUT FORMAT: Return ONLY a valid JSON object with this structure:

{{
  "summary": {{
    "new_items": count,
    "modified_items": count,
    "removed_items": count,
    "unchanged_items": count,
    "overall_impact": "Low/Medium/High/Substantial"
  }},
  "changes": [
    {{
      "id": "THE_ACTUAL_ID_FROM_INPUT",
      "identifier": "THE_ACTUAL_IDENTIFIER_FROM_INPUT",
      "title": "THE_ACTUAL_TITLE_FROM_INPUT",
      "change_type": "new|modified|removed|unchanged",
      "semantic_diff": "Explanation of what changed semantically compared to V1 (null if new or unchanged)",
      "impact_level": "low|moderate|high"
    }}
  ]
}}

JSON:"""

    return _generate_json(service, "mapping.version_comparison", prompt, options)


def version_comparison_smart_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
) -> dict[str, Any]:
    """
    Focused semantic gap analysis for specific modified controls between two framework versions.
    """
    f1_name = payload.get("framework1_name", "V1")
    f2_name = payload.get("framework2_name", "V2")
    modifications = payload.get("modifications", [])

    if not modifications:
        return {"justifications": []}

    print(f"[AI-TASK] version_comparison_smart START: Analysis for {len(modifications)} controls")

    prompt = f"""You are a GRC Expert auditing the evolution of {f1_name} into {f2_name}.

TASK:
For EVERY compliance control listed below, explain exactly what changed semantically between the old version (V1) and the new version (V2).
You MUST provide a unique justification for each ID provided in the input. Do not skip any items.

CONTROLS TO ANALYZE:
{json.dumps(modifications, indent=1)}

STRICT RULES:
1. COVERAGE: Provide a justification for every single ID in the input list.
2. FOCUS ON DELTA: Identify if obligations are stronger, weaker, clarified, or expanded.
3. BE CONCISE: Maximum 2 sentences per justification.
4. OUTPUT FORMAT: Return ONLY a valid JSON object with this structure:

{{
  "justifications": [
    {{
      "id": "THE_ACTUAL_ID_FROM_INPUT",
      "reason": "Detailed semantic explanation of the change"
    }}
  ]
}}

JSON:"""

    return _generate_json(service, "mapping.version_comparison_smart", prompt, options)


MAPPING_TASKS = {
    "mapping.cross_framework": cross_framework_mapping_task,
    "mapping.version_comparison": analyze_framework_comparison_task,
    "mapping.version_comparison_smart": version_comparison_smart_task,
}
