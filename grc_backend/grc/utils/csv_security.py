"""
CSV security helpers to prevent formula injection in spreadsheet clients.
"""

from typing import Any

# Spreadsheet apps can evaluate cells beginning with these characters.
_DANGEROUS_CSV_PREFIXES = ("=", "+", "-", "@")


def sanitize_csv_cell(value: Any) -> Any:
    """
    Neutralize CSV formula injection by prefixing dangerous string cells.

    - Non-string values are returned as-is.
    - Strings whose first non-whitespace character is =, +, -, or @
      are prefixed with a single quote.
    """
    if not isinstance(value, str):
        return value

    stripped_value = value.lstrip()
    if stripped_value and stripped_value[0] in _DANGEROUS_CSV_PREFIXES:
        return f"'{value}"

    return value


def sanitize_csv_dataset(data: Any) -> Any:
    """
    Recursively sanitize export payloads before CSV serialization.
    """
    if isinstance(data, list):
        return [sanitize_csv_dataset(item) for item in data]

    if isinstance(data, dict):
        return {key: sanitize_csv_dataset(value) for key, value in data.items()}

    return sanitize_csv_cell(data)
