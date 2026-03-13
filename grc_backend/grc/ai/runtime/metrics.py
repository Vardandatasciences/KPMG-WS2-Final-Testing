from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Any


_METRICS = defaultdict(list)


def _record(metric_name: str, payload: dict[str, Any]):
    payload = dict(payload)
    payload["recorded_at"] = datetime.utcnow().isoformat()
    _METRICS[metric_name].append(payload)
    if len(_METRICS[metric_name]) > 500:
        _METRICS[metric_name] = _METRICS[metric_name][-500:]


def record_ai_call(task_name: str, provider: str, model: str, latency_ms: float, success: bool):
    _record(
        "ai_calls",
        {
            "task_name": task_name,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "success": success,
        },
    )


def record_cache_hit(task_name: str, model: str):
    _record("cache_hits", {"task_name": task_name, "model": model})


def record_queue_wait(task_name: str, wait_ms: float):
    _record("queue_waits", {"task_name": task_name, "wait_ms": wait_ms})


def record_rag_usage(task_name: str, chunks_used: int):
    _record("rag_usage", {"task_name": task_name, "chunks_used": chunks_used})


def record_fallback(provider_from: str, provider_to: str):
    _record("fallbacks", {"provider_from": provider_from, "provider_to": provider_to})


def get_ai_metrics_summary() -> dict[str, Any]:
    calls = _METRICS["ai_calls"]
    return {
        "total_calls": len(calls),
        "success_rate": round((sum(1 for item in calls if item["success"]) / len(calls)) * 100, 2) if calls else 0,
        "average_latency_ms": round(mean(item["latency_ms"] for item in calls), 2) if calls else 0,
        "cache_hits": len(_METRICS["cache_hits"]),
        "queue_events": len(_METRICS["queue_waits"]),
        "rag_events": len(_METRICS["rag_usage"]),
        "fallbacks": len(_METRICS["fallbacks"]),
    }


def list_metric_events(metric_name: str) -> list[dict[str, Any]]:
    return list(_METRICS.get(metric_name, []))
