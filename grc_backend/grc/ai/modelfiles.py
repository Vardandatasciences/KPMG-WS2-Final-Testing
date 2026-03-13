from pathlib import Path


MODELFILE_REGISTRY = {
    "policy.analyst": {
        "model_name": "grc-policy-analyst:latest",
        "file_name": "grc-policy-analyst.Modelfile",
        "base_model": "llama3.2:3b-instruct-q4_K_M",
        "use_cases": [
            "policy.extract_policy_hierarchy",
            "policy.generate_subpolicy_compliances",
            "policy.draft_policy_from_framework_control",
        ],
    },
    "policy.reviewer": {
        "model_name": "grc-policy-reviewer:latest",
        "file_name": "grc-policy-reviewer.Modelfile",
        "base_model": "llama3:8b-instruct-q4_K_M",
        "use_cases": [
            "policy.generate_policy_gap_analysis",
            "policy.review_policy_quality",
            "policy.explain_generated_output_with_evidence",
        ],
    },
}


def get_modelfiles_directory() -> Path:
    return Path(__file__).resolve().parent / "modelfiles"


def get_modelfile_registry() -> dict:
    return MODELFILE_REGISTRY.copy()


def get_modelfile_definition(profile_name: str) -> dict:
    profile = MODELFILE_REGISTRY[profile_name].copy()
    profile["path"] = str(get_modelfiles_directory() / profile["file_name"])
    return profile


def get_modelfile_build_command(profile_name: str) -> str:
    profile = get_modelfile_definition(profile_name)
    return f'ollama create {profile["model_name"]} -f "{profile["path"]}"'


def resolve_custom_ollama_model(task_name: str) -> str | None:
    if task_name in MODELFILE_REGISTRY["policy.reviewer"]["use_cases"]:
        return MODELFILE_REGISTRY["policy.reviewer"]["model_name"]
    if task_name in MODELFILE_REGISTRY["policy.analyst"]["use_cases"]:
        return MODELFILE_REGISTRY["policy.analyst"]["model_name"]
    return None
