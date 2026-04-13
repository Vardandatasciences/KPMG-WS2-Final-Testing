"""
Custom DRF throttle classes for GRC application.

These throttles use the scope names defined in settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
and key on the authenticated user's session user_id so each account gets its own bucket.
"""

from rest_framework.throttling import UserRateThrottle


class AuditWriteThrottle(UserRateThrottle):
    """
    Limits audit creation (and other write operations on audits) to the
    'audit_write' rate defined in DEFAULT_THROTTLE_RATES.

    Default: 10 requests per minute per authenticated user.
    Adjust via settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['audit_write'].

    Returns HTTP 429 with a Retry-After header when the limit is exceeded.
    """

    scope = "audit_write"

    def get_cache_key(self, request, view):
        # Key on the session user_id (GRC custom field) when present,
        # falling back to DRF's default Django user identity.
        session_user_id = request.session.get("user_id") if hasattr(request, "session") else None
        if session_user_id:
            ident = str(session_user_id)
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }


class NotificationWriteThrottle(UserRateThrottle):
    """
    Limits notification push requests to reduce alert spam.

    Rate is configured via REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['notification_write'].
    """

    scope = "notification_write"

    def get_cache_key(self, request, view):
        session_user_id = request.session.get("user_id") if hasattr(request, "session") else None
        if session_user_id:
            ident = str(session_user_id)
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }
