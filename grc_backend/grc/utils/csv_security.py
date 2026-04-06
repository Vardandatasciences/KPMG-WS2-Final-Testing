"""
CSV security helpers to prevent formula injection in spreadsheet clients.
"""

import re
from typing import Any

# Spreadsheet apps can evaluate cells beginning with these characters.
_DANGEROUS_CSV_PREFIXES = ("=", "+", "-", "@")
# Excel / Sheets: fullwidth variants sometimes used to bypass naive filters.
_DANGEROUS_FULLWIDTH = ("\uff1d", "\uff0b", "\uff0d", "\uff20")  # ＝＋－＠

_MAX_EXPORT_FILENAME_LEN = 200
_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_csv_cell(value: Any) -> Any:
    """
    Neutralize CSV formula injection by prefixing dangerous string cells.

    - Non-string values are returned as-is.
    - Newlines / NUL are removed (row-break and embedding tricks).
    - Strings whose first non-whitespace character is =, +, -, @ (ASCII or
      common fullwidth equivalents) are prefixed with a single quote.
    """
    if not isinstance(value, str):
        return value

    s = value.replace("\x00", "")
    s = s.replace("\r", " ").replace("\n", " ").replace("\x0b", " ").replace("\x0c", " ")

    stripped = s.lstrip()
    if not stripped:
        return s

    first = stripped[0]
    if first in _DANGEROUS_CSV_PREFIXES or first in _DANGEROUS_FULLWIDTH:
        return f"'{s}"

    return s


def sanitize_csv_dataset(data: Any) -> Any:
    """
    Recursively sanitize export payloads before CSV / JSON / XML serialization.
    """
    if isinstance(data, list):
        return [sanitize_csv_dataset(item) for item in data]

    if isinstance(data, dict):
        out: dict[Any, Any] = {}
        for key, value in data.items():
            safe_key = sanitize_csv_cell(str(key)) if isinstance(key, str) else key
            out[safe_key] = sanitize_csv_dataset(value)
        return out

    return sanitize_csv_cell(data)


def sanitize_export_filename(name: Any, default: str = "export") -> str:
    """
    Safe basename for downloaded export files: alphanumerics, dot, underscore, hyphen only.
    Strips path segments, control characters, and length-limits.
    """
    raw = "" if name is None else str(name)
    raw = raw.replace("\x00", "").replace("\r", "").replace("\n", "")
    base = raw.replace("\\", "/").split("/")[-1] if raw else ""
    base = _SAFE_FILENAME_RE.sub("_", base).strip("._-")
    if not base:
        base = default
    if len(base) > _MAX_EXPORT_FILENAME_LEN:
        base = base[:_MAX_EXPORT_FILENAME_LEN].rstrip("._-") or default
    return base
