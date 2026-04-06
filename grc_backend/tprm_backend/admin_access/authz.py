"""
Object-level authorization for admin_access APIs (BOLA / IDOR hardening).

Only privileged callers may list all users or change arbitrary users' RBAC rows.
Others may only read their own permission payload.
"""
from __future__ import annotations

import logging
from typing import Optional

from rest_framework import status
from rest_framework.response import Response

from .models import RBACTPRM

logger = logging.getLogger(__name__)

# Role names in rbac_tprm.Role that imply full user-administration (lowercased).
_ADMIN_ROLE_NAMES = frozenset(
    {
        "admin",
        "administrator",
        "super admin",
        "superadmin",
        "system admin",
        "system administrator",
    }
)


def resolve_authenticated_tprm_user_id(request) -> Optional[int]:
    """Map request.user to an integer user id (matches users.UserId / rbac_tprm.UserId)."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None
    for attr in ("id", "pk", "user_id", "UserId"):
        raw = getattr(user, attr, None)
        if raw is None:
            continue
        try:
            return int(raw)
        except (TypeError, ValueError):
            continue
    return None


def user_can_manage_tprm_permissions(request) -> bool:
    """
    True if the caller may administer other users' TPRM RBAC (list users, bulk update, etc.).
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    if getattr(user, "user_type", None) == "admin":
        return True

    uid = resolve_authenticated_tprm_user_id(request)
    if uid is None:
        return False

    rbac = RBACTPRM.objects.filter(user_id=uid, is_active="Y").first()
    if not rbac:
        return False
    if getattr(rbac, "create_update_user_roles", False) is True:
        return True
    role = (rbac.role or "").strip().lower()
    return role in _ADMIN_ROLE_NAMES


def forbid_manage_permissions(request) -> Optional[Response]:
    """403 unless caller may manage user permissions."""
    if user_can_manage_tprm_permissions(request):
        return None
    uid = resolve_authenticated_tprm_user_id(request)
    logger.warning(
        "admin_access: denied privileged operation path=%s actor_user_id=%s",
        getattr(request, "path", ""),
        uid,
    )
    return Response(
        {
            "error": "User administration rights are required for this action.",
            "code": "admin_access_forbidden",
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def forbid_view_user_permissions(request, target_user_id: int) -> Optional[Response]:
    """
    Allow viewing own permissions, or any user if caller has manage rights.
    """
    if user_can_manage_tprm_permissions(request):
        return None
    actor_id = resolve_authenticated_tprm_user_id(request)
    if actor_id is not None and int(target_user_id) == int(actor_id):
        return None
    logger.warning(
        "admin_access: denied view permissions for user_id=%s path=%s actor_user_id=%s",
        target_user_id,
        getattr(request, "path", ""),
        actor_id,
    )
    return Response(
        {
            "error": "You may only view your own permissions unless you have user administration rights.",
            "code": "admin_access_forbidden",
        },
        status=status.HTTP_403_FORBIDDEN,
    )
