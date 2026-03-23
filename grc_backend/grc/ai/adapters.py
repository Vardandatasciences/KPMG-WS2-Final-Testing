from .config import (
    AI_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL_COMPLEX,
    OLLAMA_MODEL_DEFAULT,
    OLLAMA_MODEL_FAST,
    OLLAMA_TIMEOUT,
    OLLAMA_TEMPERATURE,
)
from .processing.parser import JSONResponseParser
from .service import get_ai_service, legacy_call_ollama_json, legacy_call_openai_json


def legacy_json_parser(text: str):
    return JSONResponseParser.parse_json_block(text)


def get_legacy_ai_config() -> dict[str, str | int | float | None]:
    return {
        "provider": AI_PROVIDER,
        "openai_model": OPENAI_MODEL,
        "openai_api_key": OPENAI_API_KEY,
        "ollama_base_url": OLLAMA_BASE_URL,
        "ollama_model_default": OLLAMA_MODEL_DEFAULT,
        "ollama_model_fast": OLLAMA_MODEL_FAST,
        "ollama_model_complex": OLLAMA_MODEL_COMPLEX,
        "ollama_timeout": OLLAMA_TIMEOUT,
        "ollama_temperature": OLLAMA_TEMPERATURE,
    }


__all__ = [
    "AI_PROVIDER",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL_DEFAULT",
    "OLLAMA_MODEL_FAST",
    "OLLAMA_MODEL_COMPLEX",
    "OLLAMA_TIMEOUT",
    "OLLAMA_TEMPERATURE",
    "legacy_call_openai_json",
    "legacy_call_ollama_json",
    "legacy_json_parser",
    "get_ai_service",
    "get_legacy_ai_config",
]
