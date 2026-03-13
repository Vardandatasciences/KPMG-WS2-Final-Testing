import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from django.conf import settings


class AIJobService:
    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self.base_dir = Path(settings.MEDIA_ROOT) / "ai_jobs" / namespace
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _job_path(self, task_id: str) -> Path:
        return self.base_dir / f"{task_id}.json"

    def create_job(self, task_id: str | None = None, status: str = "queued", message: str = "Queued") -> str:
        actual_id = task_id or f"{self.namespace}_{uuid.uuid4().hex}"
        self.update_job_status(actual_id, status=status, progress=0, message=message, data={})
        return actual_id

    def update_job_status(
        self,
        task_id: str,
        *,
        status: str,
        progress: int,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "task_id": task_id,
            "status": status,
            "progress": progress,
            "message": message,
            "data": data or {},
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._job_path(task_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    def get_job_status(self, task_id: str) -> dict[str, Any] | None:
        job_path = self._job_path(task_id)
        if not job_path.exists():
            return None
        return json.loads(job_path.read_text(encoding="utf-8"))

    def cancel_job(self, task_id: str) -> dict[str, Any]:
        return self.update_job_status(task_id, status="cancelled", progress=-1, message="Cancelled", data={})

    def submit_job(self, target: Callable[..., Any], *args, task_id: str | None = None, **kwargs) -> str:
        actual_id = self.create_job(task_id=task_id, status="queued", message="Queued")

        def _runner():
            try:
                self.update_job_status(actual_id, status="processing", progress=5, message="Started", data={})
                target(actual_id, *args, **kwargs)
            except Exception as exc:  # pragma: no cover
                self.update_job_status(
                    actual_id,
                    status="error",
                    progress=-1,
                    message=str(exc),
                    data={},
                )

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        return actual_id
