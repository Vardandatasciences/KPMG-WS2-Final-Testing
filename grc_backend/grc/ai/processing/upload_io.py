from pathlib import Path
from typing import Any

from ...utils.file_compression import decompress_if_needed


def decompress_uploaded_input(path: str | Path) -> tuple[str, dict[str, Any]]:
    return decompress_if_needed(str(path))


def get_upload_compression_stats(path: str | Path) -> dict[str, Any]:
    _, stats = decompress_uploaded_input(path)
    return stats


def prepare_uploaded_ai_file(path: str | Path) -> dict[str, Any]:
    actual_path, stats = decompress_uploaded_input(path)
    file_path = Path(actual_path)
    return {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "size_bytes": file_path.stat().st_size if file_path.exists() else 0,
        "compression": stats,
    }
