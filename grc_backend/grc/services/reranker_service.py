"""
Step 5: Cross-Encoder Reranker Service
Deeply compares candidates from Step 4 for better ranking.
Uses BAAI/bge-reranker-v2-m3 for accurate similarity scoring.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Module-level singleton — reranker loads once per process
_RERANKER_CACHE: dict = {}


class RerankerService:
    """
    Service for reranking similar candidates using BGE cross-encoder.
    
    Takes candidates from ChromaDB (Step 4) and provides more accurate
    similarity scores by comparing text pairs directly.
    """
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        """
        Initialize the reranker with specified model.
        
        Args:
            model_name: HuggingFace model name for reranker
                       Options: BAAI/bge-reranker-v2-m3 (best), BAAI/bge-reranker-base (lighter)
        """
        self.model_name = model_name
        self.reranker = None
        self._load_model()
    
    def _load_model(self):
        """Lazy load the reranker model, cached at module level."""
        global _RERANKER_CACHE
        if self.model_name in _RERANKER_CACHE:
            self.reranker = _RERANKER_CACHE[self.model_name]
            logger.info(f"[Reranker] Model reused from cache: {self.model_name}")
            return
        try:
            from FlagEmbedding import FlagReranker
            
            logger.info(f"[Reranker] Loading model: {self.model_name}")
            self.reranker = FlagReranker(
                self.model_name,
                use_fp16=True  # Faster inference with half precision
            )
            _RERANKER_CACHE[self.model_name] = self.reranker
            logger.info("[Reranker] Model loaded and cached successfully")
            
        except ImportError:
            logger.warning("[Reranker] FlagEmbedding not installed. Step 5 will be skipped.")
            self.reranker = None
        except Exception as e:
            logger.warning(f"[Reranker] Failed to load model: {e}. Step 5 will be skipped.")
            self.reranker = None
    
    def rerank_candidates(
        self,
        query_text: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates using cross-encoder for more accurate similarity.
        
        Args:
            query_text: The new record text to compare against
            candidates: List of candidates from Step 4 (ChromaDB search)
                         Each candidate should have 'embedding_text' or 'name' field
            top_k: Number of top candidates to return after reranking
        
        Returns:
            Reranked list of top_k candidates with reranker_score added
            Sorted by reranker_score (highest first)
            
        Example:
            candidates = [
                {"id": "framework_101", "name": "Food Safety", "chroma_score": 0.82},
                {"id": "framework_102", "name": "Food Cleanliness", "chroma_score": 0.73}
            ]
            
            result = reranker.rerank_candidates(
                "Food Hygiene Framework",
                candidates,
                top_k=3
            )
            
            # Result: Food Cleanliness (0.94), Food Safety (0.80)
        """
        if not candidates:
            logger.warning("[Reranker] No candidates to rerank")
            return []
        
        if not self.reranker:
            logger.error("[Reranker] Model not loaded")
            return candidates  # Return original order if model fails
        
        try:
            logger.info(f"[Reranker] Reranking {len(candidates)} candidates")
            
            # Build pairs: [query, candidate_text] for each candidate
            pairs = []
            for candidate in candidates:
                # Get candidate text - prefer full embedding_text, fallback to name
                candidate_text = candidate.get('embedding_text') or candidate.get('name', '')
                if not candidate_text:
                    candidate_text = candidate.get('metadata', {}).get('name', '')
                
                pairs.append([query_text, candidate_text])
            
            # Compute reranker scores for all pairs
            scores = self.reranker.compute_score(pairs)
            
            # Normalize scores to 0-1 range (FlagReranker may return raw logits)
            # Apply sigmoid if scores are not already in 0-1 range
            import torch
            if isinstance(scores, list):
                scores = torch.tensor(scores)
            
            # Convert to probability-like scores using sigmoid if needed
            if scores.max() > 1.0 or scores.min() < 0:
                scores = torch.sigmoid(scores)
            
            scores = scores.tolist()
            
            # Attach reranker scores to candidates
            reranked_candidates = []
            for candidate, score in zip(candidates, scores):
                candidate_copy = candidate.copy()
                candidate_copy['reranker_score'] = float(score)
                # Keep original ChromaDB score for comparison
                candidate_copy['chroma_score'] = candidate.get('score', 0)
                reranked_candidates.append(candidate_copy)
            
            # Sort by reranker score (descending)
            reranked_candidates.sort(
                key=lambda x: x['reranker_score'],
                reverse=True
            )
            
            # Return top_k
            top_candidates = reranked_candidates[:top_k]
            
            logger.info(f"[Reranker] Top {len(top_candidates)} after reranking:")
            for i, c in enumerate(top_candidates, 1):
                logger.info(f"  {i}. {c.get('name', 'Unknown')}: "
                          f"chroma={c['chroma_score']:.3f}, "
                          f"reranker={c['reranker_score']:.3f}")
            
            return top_candidates
            
        except Exception as e:
            logger.exception(f"[Reranker] Reranking failed: {e}")
            # Return original candidates sorted by ChromaDB score as fallback
            return sorted(
                candidates,
                key=lambda x: x.get('score', 0),
                reverse=True
            )[:top_k]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            'model_name': self.model_name,
            'loaded': self.reranker is not None,
            'type': 'cross_encoder'
        }


# Simple test function
def test_reranker():
    """Test the reranker service."""
    service = RerankerService()
    
    query = "Food Hygiene and Sanitation Framework. Covers hygiene, sanitation, cleaning, and contamination prevention."
    
    candidates = [
        {
            'id': 'framework_101',
            'name': 'Food Safety Framework',
            'score': 0.82,
            'embedding_text': 'Food Safety Framework. General food safety guidelines covering handling, storage, and preparation.'
        },
        {
            'id': 'framework_102', 
            'name': 'Food Cleanliness Framework',
            'score': 0.73,
            'embedding_text': 'Food Cleanliness Framework. Covers cleaning, hygiene checks, sanitation controls, and contamination prevention.'
        },
        {
            'id': 'framework_103',
            'name': 'Food Packaging Framework',
            'score': 0.75,
            'embedding_text': 'Food Packaging Framework. Guidelines for food packaging materials, labeling, and storage containers.'
        }
    ]
    
    result = service.rerank_candidates(query, candidates, top_k=3)
    
    print("\nReranking Results:")
    for i, c in enumerate(result, 1):
        print(f"{i}. {c['name']}")
        print(f"   ChromaDB: {c['chroma_score']:.3f} → Reranker: {c['reranker_score']:.3f}")
    
    return result


if __name__ == "__main__":
    test_reranker()
