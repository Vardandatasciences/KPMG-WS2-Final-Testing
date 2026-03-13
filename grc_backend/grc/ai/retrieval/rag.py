from typing import Any

from ...utils.rag_system import (
    add_document_to_rag,
    build_rag_prompt,
    get_rag_stats,
    is_rag_available,
    retrieve_relevant_context,
)


class RAGService:
    def ingest_document(self, document_text: str, document_id: str, metadata: dict[str, Any] | None = None):
        return add_document_to_rag(document_text, document_id, metadata=metadata or {})

    def retrieve_context(self, query: str, limit: int = 3):
        return retrieve_relevant_context(query, n_results=limit)

    def build_augmented_prompt(self, prompt: str, context_chunks):
        return build_rag_prompt(prompt, context_chunks)

    def get_stats(self):
        return get_rag_stats()

    def available(self) -> bool:
        return is_rag_available()
