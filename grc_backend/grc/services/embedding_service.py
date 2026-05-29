"""
Step 3: Embedding Creation Service
Converts text to vector embeddings using BGE-M3
"""

import os
import hashlib
import logging
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Module-level singleton — model loads once per process, shared across all requests
_MODEL_CACHE: dict = {}


class EmbeddingService:
    """Service to generate embeddings using BGE-M3"""
    
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        self.model_name = model_name
        self.dimension = 768  # MPNet output dimension
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load BGE-M3 model once and cache at module level."""
        global _MODEL_CACHE
        if self.model_name in _MODEL_CACHE:
            self.model = _MODEL_CACHE[self.model_name]
            logger.info(f"✓ Embedding model reused from cache: {self.model_name}")
            return
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            _MODEL_CACHE[self.model_name] = self.model
            logger.info(f"✓ Model loaded and cached. Dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Convert text to embedding vector
        
        Args:
            text: Input text to embed
            
        Returns:
            List of 1024 float numbers
        """
        if not text or not text.strip():
            logger.warning("Empty text provided, returning zero vector")
            return [0.0] * self.dimension
        
        try:
            # Generate embedding with normalization
            vector = self.model.encode(text, normalize_embeddings=True)
            return vector.tolist()
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def build_embedding_text(self, item_type: str, audit_record) -> str:
        """
        Build rich embedding text from audit record
        Combines Step 1 cleaned data + Step 2 classification
        
        Args:
            item_type: Framework/Policy/SubPolicy/Compliance
            audit_record: SimilarityCheckAudit instance
            
        Returns:
            Rich text for embedding
        """
        structured = audit_record.proposed_structured_json or {}
        
        # Common fields for all types
        common_parts = [
            f"Record Type: {item_type}",
            f"Name: {audit_record.proposed_name}",
            f"Description: {audit_record.proposed_description}",
            f"Domain: {audit_record.classified_primary_domain or 'Unknown'}",
            f"Industry: {audit_record.classified_industry_vertical or 'N/A'}",
        ]
        
        # Type-specific fields
        if item_type == 'Framework':
            specific_parts = [
                f"Category: {structured.get('category', 'N/A')}",
                f"Type: {structured.get('type', 'N/A')}",
                f"Identifier: {structured.get('identifier', 'N/A')}",
                f"Business Function: {audit_record.classified_business_function or 'N/A'}",
                f"Compliance Area: {audit_record.classified_compliance_area or 'N/A'}",
            ]
            
        elif item_type == 'Policy':
            specific_parts = [
                f"Category: {structured.get('category', 'N/A')}",
                f"Policy Type: {structured.get('policy_type', 'N/A')}",
                f"Sub-Category: {structured.get('sub_category', 'N/A')}",
                f"Business Function: {audit_record.classified_business_function or 'N/A'}",
                f"Compliance Area: {audit_record.classified_compliance_area or 'N/A'}",
                f"Scope: {structured.get('scope', 'N/A')[:200]}",
                f"Objective: {structured.get('objective', 'N/A')[:200]}",
            ]
            
        elif item_type == 'SubPolicy':
            specific_parts = [
                f"Control: {structured.get('control', 'N/A')[:300]}",
                f"Business Function: {audit_record.classified_business_function or 'N/A'}",
                f"Control Type: {audit_record.classified_control_type or 'N/A'}",
                f"Compliance Area: {audit_record.classified_compliance_area or 'N/A'}",
            ]
            
        elif item_type == 'Compliance':
            specific_parts = [
                f"Compliance Type: {structured.get('compliance_type', 'N/A')}",
                f"Criticality: {structured.get('criticality', 'N/A')}",
                f"Business Function: {audit_record.classified_business_function or 'N/A'}",
                f"Compliance Area: {audit_record.classified_compliance_area or 'N/A'}",
                f"Risk Category: {audit_record.classified_risk_category or 'N/A'}",
            ]
        else:
            specific_parts = []
        
        # Add classification reasoning (truncated for context)
        reasoning = audit_record.classification_reasoning or ''
        if reasoning:
            specific_parts.append(f"Context: {reasoning[:250]}")
        
        # Combine all parts
        all_parts = common_parts + specific_parts
        
        # Join with newlines and clean up
        embedding_text = '\n'.join(all_parts)
        
        # Remove extra whitespace
        embedding_text = '\n'.join(line.strip() for line in embedding_text.split('\n') if line.strip())
        
        return embedding_text
    
    def compute_text_hash(self, text: str) -> str:
        """Compute SHA256 hash of text for change detection"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
