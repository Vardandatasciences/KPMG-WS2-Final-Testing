from pathlib import Path
from typing import Any

from ...utils.document_preprocessor import calculate_document_hash, preprocess_document
from ...utils.file_compression import decompress_if_needed


class DocumentPreparationService:
    def prepare_text(self, text: str, max_length: int = 8000, preserve_sections: bool = True) -> dict[str, Any]:
        processed_text, metadata = preprocess_document(text, max_length=max_length)
        metadata["preserve_sections"] = preserve_sections
        metadata["document_hash"] = calculate_document_hash(processed_text)
        return {
            "text": processed_text,
            "metadata": metadata,
        }

    def prepare_uploaded_file(self, file_path: str | Path) -> dict[str, Any]:
        normalized_path = Path(file_path)
        actual_path, compression_stats = decompress_if_needed(str(normalized_path))
        actual_path_obj = Path(actual_path)
        content = actual_path_obj.read_text(encoding="utf-8", errors="ignore")
        prepared = self.prepare_text(content)
        prepared["metadata"]["file_path"] = str(actual_path_obj)
        prepared["metadata"]["file_name"] = actual_path_obj.name
        prepared["metadata"]["compression"] = compression_stats
        return prepared

    def calculate_hash(self, text_or_bytes: str | bytes) -> str:
        if isinstance(text_or_bytes, bytes):
            return calculate_document_hash(text_or_bytes.decode("utf-8", errors="ignore"))
        return calculate_document_hash(text_or_bytes)
