"""
Safe filesystem path utilities to mitigate path traversal.

These helpers ensure that when user-controlled path segments are used,
the resolved path always stays within an intended base directory.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Union


class UnsafePathError(ValueError):
    """Raised when a resolved path escapes the intended base directory."""


PathLike = Union[str, os.PathLike]


def _to_path(path: PathLike) -> Path:
    return Path(path).expanduser()


def safe_join(base_dir: PathLike, *parts: PathLike) -> str:
    """
    Join path parts under base_dir and ensure the result stays within base_dir.

    This is defensive against inputs like '../' or absolute paths.
    """
    base_path = _to_path(base_dir).resolve(strict=False)

    # Convert user parts to strings and join as relative paths under base.
    joined = base_path
    for part in parts:
        if part is None:
            continue
        part_str = str(part)
        if "\x00" in part_str:
            raise UnsafePathError("Null byte in path segment")
        joined = joined.joinpath(part_str)

    candidate = joined.resolve(strict=False)

    base_str = str(base_path)
    cand_str = str(candidate)

    # Normalize case for Windows.
    if os.name == "nt":
        base_str = base_str.lower()
        cand_str = cand_str.lower()

    base_sep = base_str + os.sep
    if cand_str == base_str or cand_str.startswith(base_sep):
        return str(candidate)

    raise UnsafePathError("Resolved path escapes base directory")


def resolved_path_under_base(candidate: PathLike, base_dir: PathLike) -> bool:
    """True if candidate resolves inside base_dir (use after glob, etc.)."""
    try:
        c = Path(candidate).resolve(strict=False)
        b = Path(base_dir).resolve(strict=False)
        c_str, b_str = str(c), str(b)
        if os.name == "nt":
            c_str, b_str = c_str.lower(), b_str.lower()
        return c_str == b_str or c_str.startswith(b_str + os.sep)
    except Exception:
        return False


# User / tenant keys used in upload_* folder names (no path separators or "..").
_SAFE_USER_KEY_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}$")

# Task / export job folder names (e.g. extracted_policies/<task_id>).
_SAFE_TASK_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,240}$")

# Single directory or file name component from JSON / user input (section folder, control id).
_SAFE_REL_SEGMENT_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_. -]{0,240}$")


def require_safe_user_key(user_id: PathLike) -> str:
    """Allow-list user id for paths like upload_<id> (alphanumeric, underscore, hyphen)."""
    s = str(user_id).strip()
    if not s or "\x00" in s or ".." in s:
        raise UnsafePathError("Invalid user_id")
    if not _SAFE_USER_KEY_RE.match(s):
        raise UnsafePathError("user_id must match [a-zA-Z0-9][a-zA-Z0-9_-]*")
    return s


def require_safe_task_id(task_id: PathLike) -> str:
    """Allow-list task / job folder identifiers under MEDIA_ROOT."""
    s = str(task_id).strip()
    if not s or "\x00" in s or ".." in s:
        raise UnsafePathError("Invalid task_id")
    if not _SAFE_TASK_ID_RE.match(s):
        raise UnsafePathError("task_id contains disallowed characters")
    return s


def require_safe_rel_segment(value: PathLike, *, label: str = "path segment") -> str:
    """
    One filesystem component derived from external data (section folder, control folder name).
    Allows space for titles slugified to folder names.
    """
    s = str(value).strip()
    if not s or "\x00" in s or ".." in s:
        raise UnsafePathError(f"Invalid {label}")
    if any(c in s for c in "/\\:"):
        raise UnsafePathError(f"Invalid {label}: path separators not allowed")
    if not _SAFE_REL_SEGMENT_RE.match(s):
        raise UnsafePathError(f"Invalid {label}: disallowed characters")
    return s


def safe_upload_filename(name: PathLike) -> str:
    """Safe stored file name for uploads (final path component only)."""
    try:
        from werkzeug.utils import secure_filename
    except ImportError:
        secure_filename = None
    raw = str(name).strip()
    if not raw or "\x00" in raw:
        raise UnsafePathError("Invalid filename")
    base = secure_filename(raw) if secure_filename else Path(raw).name
    if not base or base in (".", ".."):
        raise UnsafePathError("Invalid filename after sanitization")
    if any(c in base for c in "/\\"):
        raise UnsafePathError("Invalid filename")
    return base


def safe_component(value: PathLike) -> str:
    """
    Reduce a user-controlled value to a single path component.

    Example: '../etc/passwd' -> 'passwd'
    """
    p = _to_path(value)
    # Path(...).name strips directories while keeping the final component.
    return p.name

