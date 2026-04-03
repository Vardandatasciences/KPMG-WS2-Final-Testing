"""
Utilities to sanitize log content and prevent log-forging via newline/control chars.
"""

from __future__ import annotations

import logging
import re
from typing import Any

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_for_log(value: Any, max_len: int = 500) -> str:
    """
    Convert arbitrary input to a safe single-line string for logging.
    """
    if value is None:
        return ""

    text = str(value)
    # Prevent line-breaking / log-injection payloads.
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    # Remove remaining control chars.
    text = _CONTROL_CHARS_RE.sub("", text)

    if max_len > 0 and len(text) > max_len:
        return text[:max_len] + "...(truncated)"
    return text


def mask_email_for_log(email: Any) -> str:
    """
    Mask email to avoid leaking full identifiers in logs.
    """
    email_text = sanitize_for_log(email, max_len=320)
    if "@" not in email_text:
        return email_text

    local, domain = email_text.split("@", 1)
    if len(local) <= 2:
        local_masked = local[:1] + "*"
    else:
        local_masked = local[:2] + "*" * max(1, len(local) - 2)
    return f"{local_masked}@{domain}"


class LogForgingFilter(logging.Filter):
    """
    Logging filter that sanitizes message and args before formatting.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = sanitize_for_log(record.msg, max_len=2000)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {k: sanitize_for_log(v, max_len=500) for k, v in record.args.items()}
                elif isinstance(record.args, tuple):
                    record.args = tuple(sanitize_for_log(v, max_len=500) for v in record.args)
                else:
                    record.args = sanitize_for_log(record.args, max_len=500)
        except Exception:
            # Never block logging due to sanitization errors.
            return True
        return True

