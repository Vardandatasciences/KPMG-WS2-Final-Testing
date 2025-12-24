"""
RAG (Retrieval Augmented Generation) System for Phase 3
- Stores and retrieves relevant documents for context
- Uses ChromaDB for vector storage
- Integrates with LLM calls to provide domain-specific context
"""

import os
import hashlib
import logging
from typing import List, Dict, Optional, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import ChromaDB
try:
    import chromadb
    try:
        from chromadb.config import Settings as ChromaSettings
    except ImportError:
        # ChromaDB may have different import structure
        pass
    CHROMADB_AVAILABLE = True
except (ImportError, Exception) as e:
    CHROMADB_AVAILABLE = False
    logger.warning(f"⚠️  ChromaDB not available. RAG features will be disabled. Error: {e}")

# Try to import sentence transformers for embeddings (free, local)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠️  sentence-transformers not installed. Will use ChromaDB default embeddings.")

# Global ChromaDB client and collection
_chroma_client = None
_chroma_collection = None
_embedding_model = None

def get_chroma_client():
    """Get or create ChromaDB client."""
    global _chroma_client
    if not CHROMADB_AVAILABLE:
        return None
    
    if _chroma_client is None:
        try:
            # Get storage path from settings or use default
            chroma_db_path = getattr(settings, 'CHROMA_DB_PATH', os.path.join(settings.BASE_DIR, 'chroma_db'))
            os.makedirs(chroma_db_path, exist_ok=True)
            
            # Create persistent client
            _chroma_client = chromadb.PersistentClient(path=chroma_db_path)
            logger.info(f"✅ ChromaDB client initialized at: {chroma_db_path}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            _chroma_client = None
    
    return _chroma_client

def get_chroma_collection(collection_name: str = "grc_risk_documents"):
    """Get or create ChromaDB collection."""
    global _chroma_collection
    if not CHROMADB_AVAILABLE:
        return None
    
    client = get_chroma_client()
    if not client:
        return None
    
    if _chroma_collection is None:
        try:
            # Try to get existing collection first
            try:
                _chroma_collection = client.get_collection(name=collection_name)
                logger.info(f"✅ ChromaDB collection '{collection_name}' retrieved")
            except:
                # Collection doesn't exist, create it
                _chroma_collection = client.create_collection(
                    name=collection_name,
                    metadata={"description": "GRC risk assessment and compliance documents"}
                )
                logger.info(f"✅ ChromaDB collection '{collection_name}' created")
        except Exception as e:
            error_msg = str(e)
            # Handle schema mismatch errors
            if "no such column" in error_msg.lower() or "schema" in error_msg.lower():
                logger.warning(f"⚠️  ChromaDB schema mismatch detected: {e}")
                logger.info("💡 Attempting to delete entire database and recreate...")
                try:
                    # The issue is with the database schema, not just the collection
                    # Delete the entire database folder and recreate
                    chroma_db_path = getattr(settings, 'CHROMA_DB_PATH', os.path.join(settings.BASE_DIR, 'chroma_db'))
                    if os.path.exists(chroma_db_path):
                        import shutil
                        shutil.rmtree(chroma_db_path)
                        logger.info(f"🗑️  Deleted old ChromaDB database at: {chroma_db_path}")
                        os.makedirs(chroma_db_path, exist_ok=True)
                        
                        # Reset client to force recreation
                        global _chroma_client
                        _chroma_client = None
                        
                        # Get fresh client
                        client = get_chroma_client()
                        if client:
                            # Create collection with fresh schema
                            _chroma_collection = client.create_collection(
                                name=collection_name,
                                metadata={"description": "GRC risk assessment and compliance documents"}
                            )
                            logger.info(f"✅ ChromaDB collection '{collection_name}' recreated with correct schema")
                        else:
                            logger.error(f"❌ Failed to recreate ChromaDB client")
                            _chroma_collection = None
                    else:
                        logger.error(f"❌ ChromaDB path not found: {chroma_db_path}")
                        _chroma_collection = None
                except Exception as e2:
                    logger.error(f"❌ Failed to recreate database: {e2}")
                    _chroma_collection = None
            else:
                logger.error(f"❌ Failed to get/create collection: {e}")
                _chroma_collection = None
    
    return _chroma_collection

def get_embedding_model():
    """Get or create embedding model (sentence-transformers)."""
    global _embedding_model
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    
    if _embedding_model is None:
        try:
            # Use a lightweight, fast model for embeddings
            # all-MiniLM-L6-v2 is fast and good quality
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded (all-MiniLM-L6-v2)")
        except Exception as e:
            logger.warning(f"⚠️  Failed to load embedding model: {e}")
            _embedding_model = None
    
    return _embedding_model

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for better retrieval.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
    
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - chunk_overlap  # Overlap for context
    
    return chunks

def add_document_to_rag(
    document_text: str,
    document_id: str,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = 1000
) -> bool:
    """
    Add a document to the RAG system.
    
    Args:
        document_text: Full text of the document
        document_id: Unique identifier for the document
        metadata: Optional metadata (type, framework, year, etc.)
    
    Returns:
        True if successful, False otherwise
    """
    if not CHROMADB_AVAILABLE:
        logger.warning("⚠️  ChromaDB not available, skipping RAG storage")
        return False
    
    collection = get_chroma_collection()
    if not collection:
        logger.warning("⚠️  ChromaDB collection not available, skipping RAG storage")
        return False
    
    try:
        # Chunk the document
        chunks = chunk_text(document_text, chunk_size=chunk_size)
        
        if not chunks:
            logger.warning(f"⚠️  No chunks created for document {document_id}")
            return False
        
        # Prepare data for ChromaDB
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        chunk_metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_meta = metadata.copy() if metadata else {}
            chunk_meta.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "document_id": document_id
            })
            chunk_metadatas.append(chunk_meta)
        
        # Add to ChromaDB
        collection.add(
            documents=chunks,
            ids=chunk_ids,
            metadatas=chunk_metadatas
        )
        
        logger.info(f"✅ Added document {document_id} to RAG ({len(chunks)} chunks)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to add document to RAG: {e}")
        return False

def retrieve_relevant_context(
    query: str,
    n_results: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant document chunks for a query.
    
    Args:
        query: Search query
        n_results: Number of results to return
        filter_metadata: Optional metadata filters (e.g., {"framework": "GDPR"})
    
    Returns:
        List of relevant document chunks with metadata
    """
    if not CHROMADB_AVAILABLE:
        logger.warning("⚠️  ChromaDB not available, returning empty context")
        return []
    
    collection = get_chroma_collection()
    if not collection:
        logger.warning("⚠️  ChromaDB collection not available, returning empty context")
        return []
    
    try:
        # Build query
        query_kwargs = {
            "query_texts": [query],
            "n_results": n_results
        }
        
        # Add metadata filter if provided
        if filter_metadata:
            query_kwargs["where"] = filter_metadata
        
        # Query ChromaDB
        results = collection.query(**query_kwargs)
        
        # Format results
        retrieved_chunks = []
        if results and results.get('documents') and len(results['documents']) > 0:
            documents = results['documents'][0]
            metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []
            distances = results.get('distances', [[]])[0] if results.get('distances') else []
            ids = results.get('ids', [[]])[0] if results.get('ids') else []
            
            for i, doc in enumerate(documents):
                retrieved_chunks.append({
                    "text": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else None,
                    "id": ids[i] if i < len(ids) else None
                })
        
        logger.info(f"✅ Retrieved {len(retrieved_chunks)} relevant chunks for query")
        return retrieved_chunks
        
    except Exception as e:
        logger.error(f"❌ Failed to retrieve context: {e}")
        return []

def build_rag_prompt(
    user_query: str,
    retrieved_context: List[Dict[str, Any]],
    base_prompt: str = None
) -> str:
    """
    Build a prompt with RAG context.
    
    Args:
        user_query: The user's question/query
        retrieved_context: Retrieved document chunks
        base_prompt: Optional base prompt template
    
    Returns:
        Enhanced prompt with context
    """
    if not retrieved_context:
        return user_query
    
    # Build context section
    context_sections = []
    for i, chunk in enumerate(retrieved_context, 1):
        context_text = chunk.get('text', '')
        metadata = chunk.get('metadata', {})
        
        # Add metadata info if available
        source_info = ""
        if metadata.get('document_id'):
            source_info = f" (from document: {metadata.get('document_id')})"
        if metadata.get('framework'):
            source_info += f" [Framework: {metadata.get('framework')}]"
        
        context_sections.append(f"[Context {i}{source_info}]\n{context_text}")
    
    context_block = "\n\n".join(context_sections)
    
    # Build final prompt
    if base_prompt:
        prompt = f"""{base_prompt}

Relevant Context from Your Documents:
{context_block}

User Query: {user_query}

Please answer the user's query using the provided context. If the context doesn't contain enough information, you can use your general knowledge, but prioritize the provided context."""
    else:
        prompt = f"""You are a GRC (Governance, Risk, and Compliance) analyst. Use the following context from your organization's documents to answer the query.

Relevant Context from Your Documents:
{context_block}

User Query: {user_query}

Instructions:
- Answer based on the provided context when possible
- If context is insufficient, use your general knowledge
- Cite which document/chunk you're referencing
- Be specific and accurate"""
    
    return prompt

def is_rag_available() -> bool:
    """Check if RAG system is available."""
    return CHROMADB_AVAILABLE and get_chroma_client() is not None

def get_rag_stats() -> Dict[str, Any]:
    """Get statistics about the RAG system."""
    if not is_rag_available():
        return {
            "status": "unavailable",
            "message": "ChromaDB not available"
        }
    
    try:
        collection = get_chroma_collection()
        if not collection:
            return {"status": "unavailable", "message": "Collection not available"}
        
        count = collection.count()
        return {
            "status": "available",
            "total_chunks": count,
            "collection_name": collection.name if collection else None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

