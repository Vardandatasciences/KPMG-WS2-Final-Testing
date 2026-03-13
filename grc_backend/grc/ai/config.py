import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from .modelfiles import get_modelfile_registry, resolve_custom_ollama_model


def _clean_model_name(value: str, default: str) -> str:
    raw = value or default
    return str(raw).strip().strip('"').strip("'")


@dataclass(frozen=True)
class AISettings:
    provider: str
    openai_api_key: str | None
    openai_model: str
    openai_api_url: str
    ollama_base_url: str
    ollama_timeout: int
    ollama_temperature: float
    ollama_seed: int
    ollama_model_default: str
    ollama_model_fast: str
    ollama_model_complex: str
    embed_model: str
    use_openai_primary: bool
    task_sampling_profiles: dict
    model_profiles: dict
    use_custom_ollama_models: bool
    modelfile_registry: dict


def _resolve_provider(openai_api_key: str | None, ollama_base_url: str) -> str:
    configured = getattr(
        settings,
        "RISK_AI_PROVIDER",
        os.environ.get("RISK_AI_PROVIDER", "ollama"),
    )
    provider = str(configured or "").strip().lower()
    if provider in {"openai", "ollama"}:
        return provider
    if ollama_base_url:
        return "ollama"
    if openai_api_key:
        return "openai"
    return "openai"


@lru_cache(maxsize=1)
def get_ai_settings() -> AISettings:
    openai_api_key = getattr(settings, "OPENAI_API_KEY", None) or os.environ.get("OPENAI_API_KEY")
    ollama_base_url = (
        getattr(settings, "OLLAMA_BASE_URL", os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
        or "http://127.0.0.1:11434"
    ).rstrip("/")

    openai_model = _clean_model_name(getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"), "gpt-4o-mini")
    ollama_model_default = _clean_model_name(
        getattr(settings, "OLLAMA_MODEL", "llama3.2:3b-instruct-q4_K_M"),
        "llama3.2:3b-instruct-q4_K_M",
    )

    provider = _resolve_provider(openai_api_key, ollama_base_url)
    custom_models_value = getattr(settings, "USE_CUSTOM_OLLAMA_MODELS", os.environ.get("USE_CUSTOM_OLLAMA_MODELS", "false"))
    use_custom_ollama_models = str(custom_models_value).strip().lower() == "true"
    modelfile_registry = get_modelfile_registry()
    custom_policy_analyst_model = _clean_model_name(
        getattr(settings, "OLLAMA_CUSTOM_POLICY_ANALYST_MODEL", os.environ.get("OLLAMA_CUSTOM_POLICY_ANALYST_MODEL", modelfile_registry["policy.analyst"]["model_name"])),
        modelfile_registry["policy.analyst"]["model_name"],
    )
    custom_policy_reviewer_model = _clean_model_name(
        getattr(settings, "OLLAMA_CUSTOM_POLICY_REVIEWER_MODEL", os.environ.get("OLLAMA_CUSTOM_POLICY_REVIEWER_MODEL", modelfile_registry["policy.reviewer"]["model_name"])),
        modelfile_registry["policy.reviewer"]["model_name"],
    )

    return AISettings(
        provider=provider,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        openai_api_url="https://api.openai.com/v1/chat/completions",
        ollama_base_url=ollama_base_url,
        ollama_timeout=int(getattr(settings, "OLLAMA_TIMEOUT", 600)),
        ollama_temperature=float(getattr(settings, "OLLAMA_TEMPERATURE", 0.1)),
        ollama_seed=int(getattr(settings, "OLLAMA_SEED", 42)),
        ollama_model_default=ollama_model_default,
        ollama_model_fast=_clean_model_name(
            getattr(settings, "OLLAMA_MODEL_FAST", "llama3.2:1b-instruct-q4_K_M"),
            "llama3.2:1b-instruct-q4_K_M",
        ),
        ollama_model_complex=_clean_model_name(
            getattr(settings, "OLLAMA_MODEL_COMPLEX", "llama3:8b-instruct-q4_K_M"),
            "llama3:8b-instruct-q4_K_M",
        ),
        embed_model=_clean_model_name(
            getattr(settings, "OPENAI_EMBEDDING_MODEL", getattr(settings, "OLLAMA_EMBED_MODEL", "text-embedding-3-small")),
            "text-embedding-3-small",
        ),
        use_openai_primary=bool(getattr(settings, "USE_OPENAI", provider == "openai")),
        task_sampling_profiles={
            "default": {"temperature": 0.1, "top_p": 0.9, "top_k": 40, "repeat_penalty": 1.1},
            "policy.extract_policy_hierarchy": {"temperature": 0.2, "top_p": 0.85, "top_k": 30, "repeat_penalty": 1.05},
            "policy.generate_subpolicy_compliances": {"temperature": 0.15, "top_p": 0.9, "top_k": 35, "repeat_penalty": 1.1},
            "policy.draft_policy_from_framework_control": {"temperature": 0.25, "top_p": 0.92, "top_k": 45, "repeat_penalty": 1.05},
            "policy.generate_policy_gap_analysis": {"temperature": 0.1, "top_p": 0.8, "top_k": 25, "repeat_penalty": 1.15},
            "policy.review_policy_quality": {"temperature": 0.05, "top_p": 0.8, "top_k": 20, "repeat_penalty": 1.2},
        },
        model_profiles={
            "ollama_fast_quantized": {
                "provider": "ollama",
                "model": _clean_model_name(getattr(settings, "OLLAMA_MODEL_FAST", "llama3.2:1b-instruct-q4_K_M"), "llama3.2:1b-instruct-q4_K_M"),
                "quantized": True,
                "tier": "fast",
            },
            "ollama_default_quantized": {
                "provider": "ollama",
                "model": ollama_model_default,
                "quantized": "q" in ollama_model_default.lower(),
                "tier": "default",
            },
            "ollama_complex_quantized": {
                "provider": "ollama",
                "model": _clean_model_name(getattr(settings, "OLLAMA_MODEL_COMPLEX", "llama3:8b-instruct-q4_K_M"), "llama3:8b-instruct-q4_K_M"),
                "quantized": True,
                "tier": "complex",
            },
            "openai_default": {
                "provider": "openai",
                "model": openai_model,
                "quantized": False,
                "tier": "default",
            },
            "ollama_custom_policy_analyst": {
                "provider": "ollama",
                "model": custom_policy_analyst_model,
                "quantized": True,
                "tier": "custom",
                "enabled": use_custom_ollama_models,
                "modelfile": str(Path(__file__).resolve().parent / "modelfiles" / modelfile_registry["policy.analyst"]["file_name"]),
            },
            "ollama_custom_policy_reviewer": {
                "provider": "ollama",
                "model": custom_policy_reviewer_model,
                "quantized": True,
                "tier": "custom",
                "enabled": use_custom_ollama_models,
                "modelfile": str(Path(__file__).resolve().parent / "modelfiles" / modelfile_registry["policy.reviewer"]["file_name"]),
            },
        },
        use_custom_ollama_models=use_custom_ollama_models,
        modelfile_registry=modelfile_registry,
    )


AI_SETTINGS = get_ai_settings()
AI_PROVIDER = AI_SETTINGS.provider
OPENAI_API_KEY = AI_SETTINGS.openai_api_key
OPENAI_MODEL = AI_SETTINGS.openai_model
OPENAI_API_URL = AI_SETTINGS.openai_api_url
OLLAMA_BASE_URL = AI_SETTINGS.ollama_base_url
OLLAMA_TIMEOUT = AI_SETTINGS.ollama_timeout
OLLAMA_TEMPERATURE = AI_SETTINGS.ollama_temperature
OLLAMA_SEED = AI_SETTINGS.ollama_seed
OLLAMA_MODEL_DEFAULT = AI_SETTINGS.ollama_model_default
OLLAMA_MODEL_FAST = AI_SETTINGS.ollama_model_fast
OLLAMA_MODEL_COMPLEX = AI_SETTINGS.ollama_model_complex
USE_CUSTOM_OLLAMA_MODELS = AI_SETTINGS.use_custom_ollama_models


def get_model_profiles() -> dict:
    return AI_SETTINGS.model_profiles


def get_sampling_profile(task_name: str) -> dict:
    return AI_SETTINGS.task_sampling_profiles.get(task_name, AI_SETTINGS.task_sampling_profiles["default"]).copy()


def get_task_model_hints(task_name: str) -> dict:
    if USE_CUSTOM_OLLAMA_MODELS:
        custom_model = resolve_custom_ollama_model(task_name)
        if custom_model and ("gap" in task_name or "review" in task_name):
            return {"preferred_profile": "ollama_custom_policy_reviewer", "accuracy": "high"}
        if custom_model:
            return {"preferred_profile": "ollama_custom_policy_analyst", "accuracy": "high"}
    if "gap" in task_name or "review" in task_name:
        return {"preferred_profile": "ollama_complex_quantized", "accuracy": "high"}
    if "draft" in task_name:
        return {"preferred_profile": "ollama_default_quantized", "accuracy": "medium"}
    return {"preferred_profile": "ollama_fast_quantized", "accuracy": "medium"}


def get_quantized_model(task_name: str = "default") -> str:
    preferred_profile = get_task_model_hints(task_name)["preferred_profile"]
    return get_model_profiles()[preferred_profile]["model"]


def is_quantized_model(model_name: str) -> bool:
    return "q" in (model_name or "").lower()


def build_generation_options(task_name: str, override_temperature: float | None = None) -> dict:
    profile = get_sampling_profile(task_name)
    if override_temperature is not None:
        profile["temperature"] = override_temperature
    return profile


def get_modelfile_registry_info() -> dict:
    return AI_SETTINGS.modelfile_registry.copy()
