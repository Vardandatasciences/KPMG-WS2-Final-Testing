import hashlib
import json
from typing import Any, Callable

from ...utils.ai_cache import get_cached_response, set_cached_response


def build_cache_key(
    task_name: str,
    provider: str,
    model: str,
    prompt: str,
    document_hash: str | None = None,
    schema_version: str = "v1",
) -> str:
    cache_material = json.dumps(
        {
            "task_name": task_name,
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "document_hash": document_hash,
            "schema_version": schema_version,
        },
        sort_keys=True,
    )
    return f"ai_cache:{hashlib.sha256(cache_material.encode('utf-8')).hexdigest()}"


class AIResponseCache:
    def get_or_set(
        self,
        *,
        task_name: str,
        provider: str,
        model: str,
        prompt: str,
        callback: Callable[[], Any],
        document_hash: str | None = None,
        schema_version: str = "v1",
        ttl: int = 3600,
        use_cache: bool = True,
    ) -> Any:
        if not use_cache:
            return callback()

        key = build_cache_key(
            task_name=task_name,
            provider=provider,
            model=model,
            prompt=prompt,
            document_hash=document_hash,
            schema_version=schema_version,
        )
        cached = get_cached_response(key)
        if cached is not None:
            return cached

        value = callback()
        set_cached_response(key, value, ttl=ttl)
        return value
