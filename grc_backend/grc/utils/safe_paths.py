"""
Safe filesystem path utilities to mitigate path traversal.

These helpers ensure that when user-controlled path segments are used,
the resolved path always stays within an intended base directory.
"""

from __future__ import annotations

import os
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


def safe_component(value: PathLike) -> str:
    """
    Reduce a user-controlled value to a single path component.

    Example: '../etc/passwd' -> 'passwd'
    """
    p = _to_path(value)
    # Path(...).name strips directories while keeping the final component.
    return p.name

