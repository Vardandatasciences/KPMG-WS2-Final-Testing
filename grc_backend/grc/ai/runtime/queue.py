from typing import Any, Callable

from ...utils.request_queue import get_queue_status, process_with_queue, rate_limit_decorator


class AIRequestQueue:
    def run(self, request_id: str, func: Callable[..., Any], *args, **kwargs) -> Any:
        return process_with_queue(request_id, func, *args, **kwargs)

    def status(self) -> dict[str, Any]:
        return get_queue_status()


__all__ = ["AIRequestQueue", "get_queue_status", "process_with_queue", "rate_limit_decorator"]
