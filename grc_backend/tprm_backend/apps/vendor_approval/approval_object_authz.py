"""
Object-level authorization for vendor approval APIs (BOLA / IDOR).

Restricts access to approval details and requester-scoped lists so callers cannot
enumerate or open arbitrary approvals by id or user_id within a tenant.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from rest_framework import status
from rest_framework.response import Response

from tprm_backend.admin_access.authz import user_can_manage_tprm_permissions

logger = logging.getLogger(__name__)


def resolve_vendor_approval_actor_user_id(request) -> Optional[int]:
    """Map JWT / session user to integer UserId (matches approval requester / stage assignee)."""
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return None
    for attr in ("userid", "id", "pk", "user_id", "UserId"):
        raw = getattr(user, attr, None)
        if raw is None:
            continue
        try:
            return int(raw)
        except (TypeError, ValueError):
            continue
    return None


def _as_int_id(val: Any) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def forbid_cross_user_requester_list(request, requester_id_int: int) -> Optional[Response]:
    """Only the requester (or a user administrator) may list approvals by requester_id."""
    if user_can_manage_tprm_permissions(request):
        return None
    actor = resolve_vendor_approval_actor_user_id(request)
    if actor is None:
        return Response(
            {
                "error": "Unable to resolve user from authentication.",
                "code": "approval_authn_required",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if int(requester_id_int) != int(actor):
        logger.warning(
            "vendor_approval: denied requester list path=%s actor=%s requested_requester=%s",
            getattr(request, "path", ""),
            actor,
            requester_id_int,
        )
        return Response(
            {
                "error": "You may only list approvals for your own user id.",
                "code": "approval_idor_forbidden",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def forbid_vendor_approval_detail_access(
    request,
    approval_row: Dict[str, Any],
    stages: List[Dict[str, Any]],
) -> Optional[Response]:
    """
    Caller must be the approval requester, assigned on at least one stage, or a user administrator.
    """
    if user_can_manage_tprm_permissions(request):
        return None
    actor = resolve_vendor_approval_actor_user_id(request)
    if actor is None:
        return Response(
            {
                "error": "Unable to resolve user from authentication.",
                "code": "approval_authn_required",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    rid = _as_int_id(approval_row.get("requester_id"))
    if rid is not None and rid == actor:
        return None
    for stage in stages:
        aid = _as_int_id(stage.get("assigned_user_id"))
        if aid is not None and aid == actor:
            return None
    logger.warning(
        "vendor_approval: denied approval detail approval_id=%s path=%s actor=%s",
        approval_row.get("approval_id"),
        getattr(request, "path", ""),
        actor,
    )
    return Response(
        {
            "error": "You are not authorized to access this approval request.",
            "code": "approval_idor_forbidden",
        },
        status=status.HTTP_403_FORBIDDEN,
    )
