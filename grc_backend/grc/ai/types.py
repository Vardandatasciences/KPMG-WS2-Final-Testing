from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIRequestOptions:
    task_name: str = "generic"
    preferred_provider: str | None = None
    preferred_model: str | None = None
    temperature: float | None = None
    timeout: int | None = None
    retries: int = 2
    use_cache: bool = True
    document_hash: str | None = None
    schema_version: str = "v1"
    stream: bool = False
    include_trace: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelDecision:
    provider: str
    model: str
    reason: str


@dataclass
class AIJobStatus:
    task_id: str
    status: str
    progress: int
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    updated_at: str | None = None


@dataclass
class EvidenceSource:
    source_type: str
    source_id: str
    label: str
    excerpt: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceTrace:
    task_name: str
    provider: str
    model: str
    route_reason: str
    logic: str
    evidence_sources: list[EvidenceSource] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
