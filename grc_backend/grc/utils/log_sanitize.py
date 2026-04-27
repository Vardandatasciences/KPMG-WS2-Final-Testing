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


def _sanitize_log_arg(value: Any, max_len: int = 500) -> Any:
    """
    Sanitize only text-like log args and preserve numeric/bool types.

    Preserving ints/floats avoids breaking logging format strings such as
    "%d" used by third-party libraries (e.g., urllib3).
    """
    if isinstance(value, str):
        return sanitize_for_log(value, max_len=max_len)
    if isinstance(value, (bytes, bytearray)):
        return sanitize_for_log(value, max_len=max_len)
    if isinstance(value, dict):
        return {k: _sanitize_log_arg(v, max_len=max_len) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        ctor = tuple if isinstance(value, tuple) else list
        return ctor(_sanitize_log_arg(v, max_len=max_len) for v in value)
    return value


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
def mask_sensitive_data(data: Any) -> Any:
    """
    Recursively mask common sensitive fields in dicts or lists.
    """
    sensitive_keys = {
        "password", "token", "access_token", "refresh_token", 
        "secret", "key", "authorization", "cookie", "otp"
    }
    
    if isinstance(data, dict):
        masked_dict = {}
        for k, v in data.items():
            k_lower = k.lower()
            if any(sk in k_lower for sk in sensitive_keys):
                masked_dict[k] = "********"
            else:
                masked_dict[k] = mask_sensitive_data(v)
        return masked_dict
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    
    return data


class LogForgingFilter(logging.Filter):
    """
    Logging filter that sanitizes message and args before formatting.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = sanitize_for_log(record.msg, max_len=2000)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {k: _sanitize_log_arg(v, max_len=500) for k, v in record.args.items()}
                elif isinstance(record.args, tuple):
                    record.args = tuple(_sanitize_log_arg(v, max_len=500) for v in record.args)
                else:
                    record.args = _sanitize_log_arg(record.args, max_len=500)
        except Exception:
            # Never block logging due to sanitization errors.
            return True
        return True

