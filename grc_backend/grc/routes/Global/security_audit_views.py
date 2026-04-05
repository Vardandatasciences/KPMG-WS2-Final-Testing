"""
Security audit helpers: verify hash-chain log integrity (admin-only API).
"""

from __future__ import annotations

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from grc.rbac.utils import RBACUtils
from grc.utils.integrity_log_handler import verify_hash_chain_file


@api_view(["GET"])
@permission_classes([AllowAny])
def verify_audit_log_chain(request):
    """
    Verify the append-only hash-chain security audit log.
    Requires an authenticated GRC user with GRC Administrator role.
    """
    user_id = RBACUtils.get_user_id_from_request(request)
    if user_id is None:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    if not RBACUtils.is_system_admin(user_id):
        return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    path = getattr(settings, "SECURITY_AUDIT_LOG_PATH", "")
    if not path:
        return Response(
            {"chain_valid": False, "message": "SECURITY_AUDIT_LOG_PATH not configured"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not getattr(settings, "SECURITY_AUDIT_LOG_ENABLED", True):
        return Response(
            {
                "chain_valid": True,
                "lines_verified": 0,
                "message": "security_audit_log_disabled",
            }
        )

    result = verify_hash_chain_file(path)
    http_status = status.HTTP_200_OK if result.get("chain_valid") else status.HTTP_409_CONFLICT
    return Response(result, status=http_status)
