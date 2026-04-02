"""
Centralized input sanitization helpers for RFP/RFI invitation flows.
"""

import re


MAX_INVITATION_MESSAGE_LENGTH = 2000

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_UNSAFE_URL_PROTOCOL_RE = re.compile(r"(javascript:|data:|vbscript:)", re.IGNORECASE)


def sanitize_invitation_custom_message(value, field_name="customMessage"):
    """
    Enforce plain-text custom invitation message.

    - Rejects HTML tags and unsafe URL protocols.
    - Normalizes surrounding whitespace.
    - Enforces a max length to limit abuse and oversized payloads.
    """
    if value is None:
        return ""

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a text value.")

    sanitized_value = value.strip()

    if len(sanitized_value) > MAX_INVITATION_MESSAGE_LENGTH:
        raise ValueError(
            f"{field_name} must be {MAX_INVITATION_MESSAGE_LENGTH} characters or fewer."
        )

    if _HTML_TAG_RE.search(sanitized_value):
        raise ValueError(f"{field_name} cannot contain HTML tags.")

    if _UNSAFE_URL_PROTOCOL_RE.search(sanitized_value):
        raise ValueError(f"{field_name} contains an unsafe URL or protocol.")

    return sanitized_value
