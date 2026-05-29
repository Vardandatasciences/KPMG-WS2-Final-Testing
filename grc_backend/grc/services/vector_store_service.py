"""
Step 4: Vector Search Service using ChromaDB
Stores and searches embeddings with metadata filtering.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Service for storing and searching vectors using ChromaDB.
    
    Features:
    - Store embeddings with rich metadata
    - Search with metadata filters (tenant, domain, entity_type, etc.)
    - Support for all 4 entity types (Framework, Policy, SubPolicy, Compliance)
    """
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize ChromaDB client.
        
        Args:
            persist_directory: Where to store ChromaDB files
                               (None = in-memory, good for testing)
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not installed. Run: pip install chromadb")
        
        self.persist_directory = persist_directory or os.path.join(
            os.path.dirname(__file__), '..', '..', 'chroma_db'
        )
        
        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection for GRC embeddings
        # Using cosine distance for similarity search (matches BGE-M3)
        self.collection = self.client.get_or_create_collection(
            name="grc_similarity_index",
            metadata={
                "hnsw:space": "cosine",  # Use cosine similarity
                "description": "GRC entity embeddings for similarity search"
            }
        )
        
        logger.info(f"✓ VectorStoreService initialized. Collection: grc_similarity_index")
        logger.info(f"  Storage: {self.persist_directory}")
    
    def store_embedding(
        self,
        embedding_id: str,
        embedding_vector: List[float],
        entity_type: str,
        entity_id: int,
        tenant_id: Optional[int],
        domain: Optional[str],
        category: Optional[str],
        name: str,
        status: str = "Active",
        parent_framework_id: Optional[int] = None,
        parent_policy_id: Optional[int] = None,
        parent_subpolicy_id: Optional[int] = None,
        additional_metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Store an embedding with metadata in ChromaDB.
        
        Args:
            embedding_id: Unique ID (e.g., "framework_101")
            embedding_vector: The 1024-dimension vector
            entity_type: Framework/Policy/SubPolicy/Compliance
            entity_id: Database ID of the entity
            tenant_id: Multi-tenancy filter
            domain: Domain filter (from Step 2 classification)
            category: Category filter
            name: Entity name for reference
            status: Active/Inactive
            parent_*_id: Hierarchy references
            additional_metadata: Any extra fields
            
        Returns:
            True if stored successfully
        """
        try:
            # Build metadata payload
            metadata = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "tenant_id": tenant_id or 0,  # 0 = global/no tenant
                "domain": domain or "Unknown",
                "category": category or "",
                "name": name,
                "status": status,
                "parent_framework_id": parent_framework_id or 0,
                "parent_policy_id": parent_policy_id or 0,
                "parent_subpolicy_id": parent_subpolicy_id or 0,
                "created_at": datetime.utcnow().isoformat(),
            }
            
            # Add any additional metadata
            if additional_metadata:
                # Filter out None values and convert to strings for ChromaDB
                for key, value in additional_metadata.items():
                    if value is not None:
                        metadata[key] = str(value)
            
            # Store in ChromaDB
            self.collection.upsert(
                ids=[embedding_id],
                embeddings=[embedding_vector],
                metadatas=[metadata]
            )
            
            logger.info(f"✓ Stored embedding: {embedding_id} ({entity_type} - {name})")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to store embedding {embedding_id}: {e}")
            return False
    
    def search_similar(
        self,
        query_vector: List[float],
        entity_type: str,
        tenant_id: Optional[int],
        domain: Optional[str] = None,
        category: Optional[str] = None,
        parent_framework_id: Optional[int] = None,
        parent_policy_id: Optional[int] = None,
        parent_subpolicy_id: Optional[int] = None,
        status: str = "Active",
        top_k: int = 20,
        min_score: float = 0.70
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings with metadata filters.
        
        Args:
            query_vector: The 1024-dimension vector to search
            entity_type: Filter by record type (Framework/Policy/SubPolicy/Compliance)
            tenant_id: Filter by tenant
            domain: Optional domain filter
            category: Optional category filter
            parent_*_id: Optional hierarchy filters
            status: Filter by status (default: Active)
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1, cosine similarity)
            
        Returns:
            List of candidates with scores and metadata
            [
                {
                    "id": "framework_101",
                    "score": 0.91,
                    "entity_type": "Framework",
                    "entity_id": 101,
                    "name": "Food Hygiene Framework",
                    "domain": "Food",
                    "category": "Food Safety",
                    ...
                }
            ]
        """
        try:
            # Build where clause for metadata filtering
            where_clause = {
                "entity_type": {"$eq": entity_type}
            }
            
            # Add optional filters if provided
            extra_filters = []
            if domain:
                extra_filters.append({"domain": {"$eq": domain}})
            if category:
                extra_filters.append({"category": {"$eq": category}})
            if parent_framework_id:
                extra_filters.append({"parent_framework_id": {"$eq": parent_framework_id}})
            if parent_policy_id:
                extra_filters.append({"parent_policy_id": {"$eq": parent_policy_id}})
            if parent_subpolicy_id:
                extra_filters.append({"parent_subpolicy_id": {"$eq": parent_subpolicy_id}})
            if tenant_id is not None:
                extra_filters.append({"tenant_id": {"$eq": int(tenant_id)}})

            if extra_filters:
                where_clause = {"$and": [where_clause] + extra_filters}
            
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_clause,
                include=["metadatas", "distances"]
            )
            
            # Process results
            candidates = []
            
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    # ChromaDB returns distance, convert to similarity score
                    # Cosine distance: 0 = identical, 2 = opposite
                    # Convert to similarity: 1 - (distance / 2)
                    distance = results["distances"][0][i]
                    similarity_score = 1 - (distance / 2)
                    
                    metadata = results["metadatas"][0][i]
                    
                    # Filter by minimum score
                    if similarity_score < min_score:
                        continue
                    
                    candidates.append({
                        "id": doc_id,
                        "score": round(similarity_score, 4),
                        "entity_type": metadata.get("entity_type"),
                        "entity_id": metadata.get("entity_id"),
                        "name": metadata.get("name"),
                        "domain": metadata.get("domain"),
                        "category": metadata.get("category"),
                        "status": metadata.get("status"),
                        "tenant_id": metadata.get("tenant_id"),
                        "parent_framework_id": metadata.get("parent_framework_id"),
                        "parent_policy_id": metadata.get("parent_policy_id"),
                        "parent_subpolicy_id": metadata.get("parent_subpolicy_id"),
                    })
            
            logger.info(
                f"✓ Search complete: {len(candidates)} candidates found "
                f"(entity_type={entity_type}, tenant={tenant_id}, domain={domain})"
            )
            
            return candidates
            
        except Exception as e:
            logger.error(f"✗ Search failed: {e}")
            return []
    
    def get_embedding_ids_for_entity_type(self, entity_type: str) -> set:
        """Return all Chroma embedding ids for an entity type (single query)."""
        try:
            result = self.collection.get(
                where={"entity_type": {"$eq": entity_type}},
                include=[],
            )
            return set(result.get('ids') or [])
        except Exception as e:
            logger.error(f"✗ Failed to list embeddings for {entity_type}: {e}")
            return set()

    def update_metadata(self, embedding_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """Update metadata fields on an existing embedding (no re-embedding)."""
        try:
            existing = self.collection.get(ids=[embedding_id], include=['metadatas'])
            if not existing['ids']:
                return False
            merged = dict(existing['metadatas'][0])
            for key, value in metadata_updates.items():
                if value is not None:
                    merged[key] = value
            self.collection.update(ids=[embedding_id], metadatas=[merged])
            logger.debug(f"Updated metadata: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to update metadata {embedding_id}: {e}")
            return False

    def batch_update_metadata(
        self,
        updates: Dict[str, Dict[str, Any]],
        batch_size: int = 200,
    ) -> int:
        """
        Update metadata for many embeddings in batches (much faster than per-record updates).
        Returns number of embeddings successfully updated.
        """
        if not updates:
            return 0
        updated = 0
        ids = list(updates.keys())
        for i in range(0, len(ids), batch_size):
            chunk_ids = ids[i:i + batch_size]
            try:
                existing = self.collection.get(ids=chunk_ids, include=['metadatas'])
                if not existing['ids']:
                    continue
                valid_ids = []
                merged_metas = []
                for eid, meta in zip(existing['ids'], existing['metadatas']):
                    merged = dict(meta)
                    for key, value in updates[eid].items():
                        if value is not None:
                            merged[key] = value
                    valid_ids.append(eid)
                    merged_metas.append(merged)
                if valid_ids:
                    self.collection.update(ids=valid_ids, metadatas=merged_metas)
                    updated += len(valid_ids)
            except Exception as e:
                logger.error(f"✗ Batch metadata update failed (offset {i}): {e}")
        return updated

    def embedding_exists(self, embedding_id: str) -> bool:
        """Check if an embedding already exists in ChromaDB."""
        try:
            result = self.collection.get(ids=[embedding_id])
            return len(result['ids']) > 0
        except Exception:
            return False

    def delete_embedding(self, embedding_id: str) -> bool:
        """Delete an embedding from ChromaDB."""
        try:
            self.collection.delete(ids=[embedding_id])
            logger.info(f"✓ Deleted embedding: {embedding_id}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to delete embedding {embedding_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            count = self.collection.count()
            return {
                "total_embeddings": count,
                "collection_name": "grc_similarity_index",
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"✗ Failed to get stats: {e}")
            return {}
