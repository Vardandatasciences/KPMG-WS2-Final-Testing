from typing import Any


SYSTEM_PROMPTS = {
    "default": "You are a GRC AI assistant. Follow the requested output format exactly.",
    "policy": "You are a policy and compliance expert. Return concise, structured, reviewable outputs.",
    "analysis": "You are an expert analyst. Focus on evidence, traceability, and operational clarity.",
    "risk": "You are a GRC risk specialist. Produce structured, reviewable risk outputs with precise scoring and rationale.",
}


PROMPT_TEMPLATES = {
    "policy.generate_subpolicy_compliances": """
Generate compliance records for the following subpolicy.

SubPolicy Name: {subpolicy_title}
Description: {subpolicy_description}
Control: {control}
Current Date: {current_date}
""".strip(),
    "policy.draft_policy_from_framework_control": """
Draft a governed policy from the following framework controls and regulatory text:
{payload}
""".strip(),
    "policy.generate_policy_gap_analysis": """
Compare framework requirements against the provided policy library and return a gap analysis:
{payload}
""".strip(),
}


FEW_SHOT_EXAMPLES = {
    "policy.review_policy_quality": [
        {
            "input": "Policy scope is vague and objective is missing.",
            "output": "Identify unclear scope, missing objective, and recommend tighter governance language.",
        }
    ],
    "policy.generate_policy_gap_analysis": [
        {
            "input": "Framework requires MFA; existing policy covers passwords only.",
            "output": "Mark MFA as missing control and recommend a remediation action.",
        }
    ],
}


def get_system_prompt(task_name: str) -> str:
    if task_name.startswith("risk."):
        return SYSTEM_PROMPTS["risk"]
    if task_name.startswith("policy."):
        return SYSTEM_PROMPTS["policy"]
    if "analysis" in task_name:
        return SYSTEM_PROMPTS["analysis"]
    return SYSTEM_PROMPTS["default"]


def get_prompt_template(task_name: str) -> str:
    return PROMPT_TEMPLATES.get(task_name, "{payload}")


def get_few_shot_examples(task_name: str) -> list[dict[str, str]]:
    return FEW_SHOT_EXAMPLES.get(task_name, [])


def attach_few_shot_examples(prompt: str, task_name: str) -> str:
    examples = get_few_shot_examples(task_name)
    if not examples:
        return prompt
    example_text = "\n\n".join(
        f"Example Input: {example['input']}\nExample Output: {example['output']}"
        for example in examples
    )
    return f"{prompt}\n\nFew-shot examples:\n{example_text}"


def optimize_prompt_for_speed(task_name: str, payload: Any) -> str:
    rendered = render_prompt(task_name, payload)
    return "\n".join(line.rstrip() for line in rendered.splitlines() if line.strip())


def render_prompt(task_name: str, payload: Any) -> str:
    template = get_prompt_template(task_name)
    if isinstance(payload, dict):
        try:
            return template.format(**payload, payload=payload)
        except Exception:
            return template.format(payload=payload)
    return template.format(payload=payload)
