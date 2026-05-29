"""
Dataclasses for similarity detection pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class SimilarityCheckRequest:
    """Request to initiate similarity check."""
    item_type: str  # 'Framework', 'Policy', 'SubPolicy', 'Compliance'
    item_data: Dict[str, Any]
    tenant_id: Optional[int] = None
    user_id: Optional[int] = None
    parent_framework_id: Optional[int] = None
    parent_policy_id: Optional[int] = None
    parent_subpolicy_id: Optional[int] = None


@dataclass
class SimilarityCheckResponse:
    """Response from similarity check."""
    check_id: int
    status: str  # 'PENDING', 'DOMAIN_CLASSIFIED', 'EMBEDDING_GENERATED', 'COMPLETED', 'FAILED'
    candidates: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    step1_result: Optional[Any] = None
    step2_result: Optional[Any] = None
    step3_result: Optional[Any] = None
