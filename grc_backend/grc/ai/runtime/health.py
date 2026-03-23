from typing import Any

from ...utils.ai_cache import get_cache_stats, get_redis_client
from .metrics import get_ai_metrics_summary
from .queue import get_queue_status


def get_provider_health(available_providers: list[str]) -> dict[str, Any]:
    return {
        "available_providers": available_providers,
        "provider_count": len(available_providers),
        "healthy": len(available_providers) > 0,
    }


def get_cache_health() -> dict[str, Any]:
    client = get_redis_client()
    return {
        "backend": "redis" if client else "memory",
        "stats": get_cache_stats(),
        "healthy": True,
    }


def get_queue_health() -> dict[str, Any]:
    status = get_queue_status()
    status["healthy"] = status["processing"] <= status["max_concurrent"]
    return status


def get_ai_runtime_health(available_providers: list[str], rag_available: bool) -> dict[str, Any]:
    return {
        "providers": get_provider_health(available_providers),
        "cache": get_cache_health(),
        "queue": get_queue_health(),
        "rag": {"available": rag_available, "healthy": True},
        "metrics": get_ai_metrics_summary(),
    }
