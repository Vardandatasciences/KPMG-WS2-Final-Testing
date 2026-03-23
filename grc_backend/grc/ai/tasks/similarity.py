"""
Centralized AI tasks for Similarity-Based Change Matching.
Provides AI-powered similarity analysis for framework comparison using centralized AI service.
"""

import json
from typing import Any, Dict, List, Optional
from ..types import AIRequestOptions


def _ensure_options(options: AIRequestOptions | None, task_name: str) -> AIRequestOptions:
    """Ensure AIRequestOptions exists with task name."""
    if options is None:
        return AIRequestOptions(task_name=task_name)
    options.task_name = task_name
    return options


def _generate_json(service, task_name: str, prompt: str, options: AIRequestOptions | None = None):
    """Helper to generate JSON response using AI service."""
    return service.generate_json(
        task_name=task_name,
        prompt=prompt,
        options=_ensure_options(options, task_name),
    )


def generate_embeddings_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
) -> dict[str, Any]:
    """
    Centralized task for generating text embeddings for similarity analysis.
    
    Payload should contain:
    - texts: List of texts to generate embeddings for
    - max_length: Optional maximum text length (default: 8000)
    """
    texts = payload.get("texts", [])
    max_length = payload.get("max_length", 8000)
    
    if not texts:
        raise ValueError("texts list is required in payload")
    
    print(f"[AI-TASK] generate_embeddings START: {len(texts)} texts")
    
    embeddings = []
    for i, text in enumerate(texts):
        # Truncate text to max length
        truncated_text = text[:max_length] if text else ""
        
        # Create embedding request prompt (for models that don't have direct embedding support)
        prompt = f"""Generate a semantic representation vector for the following text for similarity comparison:

TEXT: {truncated_text}

Return a JSON object with:
- text_summary: Brief summary of the key concepts (max 100 chars)
- semantic_features: List of 5-10 key semantic features/concepts
- domain_category: Classification (e.g., "compliance", "security", "operational", "financial")
- complexity_score: Complexity rating 1-10

Format:
{{
  "text_summary": "Brief summary of content",
  "semantic_features": ["concept1", "concept2", "concept3"],
  "domain_category": "compliance",
  "complexity_score": 5
}}"""

        try:
            result = _generate_json(service, f"similarity.embedding.{i}", prompt, options)
            embeddings.append({
                "text": truncated_text,
                "embedding": result,
                "index": i
            })
            print(f"[AI-TASK] Generated embedding {i+1}/{len(texts)}")
        except Exception as e:
            print(f"[AI-TASK] Failed to generate embedding for text {i}: {e}")
            # Fallback embedding
            embeddings.append({
                "text": truncated_text,
                "embedding": {
                    "text_summary": "Error generating embedding",
                    "semantic_features": [],
                    "domain_category": "unknown",
                    "complexity_score": 1
                },
                "index": i
            })
    
    print(f"[AI-TASK] generate_embeddings DONE: {len(embeddings)} embeddings generated")
    
    return {
        "embeddings": embeddings,
        "total_processed": len(embeddings),
        "success_count": sum(1 for e in embeddings if e["embedding"].get("complexity_score", 0) > 1)
    }


def calculate_semantic_similarity_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
) -> dict[str, Any]:
    """
    Centralized task for calculating semantic similarity between two texts using AI analysis.
    
    Payload should contain:
    - text1: First text for comparison
    - text2: Second text for comparison  
    - comparison_type: Type of comparison ("policy", "subpolicy", "compliance")
    - context: Optional context information
    """
    text1 = payload.get("text1", "")
    text2 = payload.get("text2", "")
    comparison_type = payload.get("comparison_type", "general")
    context = payload.get("context", "")
    
    if not text1 or not text2:
        raise ValueError("Both text1 and text2 are required in payload")
    
    print(f"[AI-TASK] calculate_semantic_similarity START: {comparison_type} comparison")
    
    # Create comprehensive similarity analysis prompt
    prompt = f"""As a GRC compliance expert, analyze the semantic similarity between these two {comparison_type} texts for framework comparison purposes.

CONTEXT: {context}

TEXT 1:
{text1[:4000]}

TEXT 2:
{text2[:4000]}

Provide a comprehensive similarity analysis in JSON format:

{{
  "overall_similarity_score": 0.85,
  "similarity_analysis": {{
    "conceptual_overlap": 0.90,
    "terminology_alignment": 0.80,
    "structural_similarity": 0.85,
    "intent_matching": 0.90
  }},
  "detailed_comparison": {{
    "common_concepts": ["concept1", "concept2", "concept3"],
    "unique_to_text1": ["unique1", "unique2"],
    "unique_to_text2": ["unique3", "unique4"],
    "terminology_differences": ["term1->term2", "oldterm->newterm"]
  }},
  "compliance_assessment": {{
    "maintains_compliance_intent": true,
    "regulatory_alignment": "high",
    "risk_of_gaps": "low",
    "recommended_action": "accept_as_equivalent"
  }},
  "confidence_metrics": {{
    "analysis_confidence": 0.92,
    "recommendation_confidence": 0.88,
    "data_quality_score": 0.95
  }},
  "justification": "Detailed explanation of similarity assessment methodology and reasoning"
}}

SCORING CRITERIA:
- 0.9-1.0: Nearly identical or equivalent meaning
- 0.7-0.89: High similarity, minor differences
- 0.5-0.69: Moderate similarity, notable differences  
- 0.3-0.49: Low similarity, major differences
- 0.0-0.29: Very different or unrelated content

Focus on compliance and regulatory context for GRC framework analysis."""

    try:
        result = _generate_json(service, "similarity.semantic_analysis", prompt, options)
        print(f"[AI-TASK] Semantic similarity analysis completed")
        return result
    except Exception as e:
        print(f"[AI-TASK] Failed to calculate semantic similarity: {e}")
        # Return fallback result
        return {
            "overall_similarity_score": 0.0,
            "similarity_analysis": {
                "conceptual_overlap": 0.0,
                "terminology_alignment": 0.0,
                "structural_similarity": 0.0,
                "intent_matching": 0.0
            },
            "detailed_comparison": {
                "common_concepts": [],
                "unique_to_text1": [],
                "unique_to_text2": [],
                "terminology_differences": []
            },
            "compliance_assessment": {
                "maintains_compliance_intent": False,
                "regulatory_alignment": "unknown",
                "risk_of_gaps": "high",
                "recommended_action": "manual_review_required"
            },
            "confidence_metrics": {
                "analysis_confidence": 0.0,
                "recommendation_confidence": 0.0,
                "data_quality_score": 0.0
            },
            "justification": f"Error in AI analysis: {str(e)}"
        }


def batch_similarity_analysis_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
) -> dict[str, Any]:
    """
    Centralized task for batch similarity analysis of multiple text pairs.
    
    Payload should contain:
    - text_pairs: List of {"text1": str, "text2": str, "id": str} objects
    - comparison_type: Type of comparison
    - context: Optional context information
    """
    text_pairs = payload.get("text_pairs", [])
    comparison_type = payload.get("comparison_type", "general")
    context = payload.get("context", "")
    
    if not text_pairs:
        raise ValueError("text_pairs list is required in payload")
    
    print(f"[AI-TASK] batch_similarity_analysis START: {len(text_pairs)} pairs")
    
    results = []
    for i, pair in enumerate(text_pairs):
        try:
            # Create payload for individual comparison
            individual_payload = {
                "text1": pair.get("text1", ""),
                "text2": pair.get("text2", ""),
                "comparison_type": comparison_type,
                "context": context
            }
            
            # Calculate similarity for this pair
            similarity_result = calculate_semantic_similarity_task(
                service, individual_payload, metadata, options
            )
            
            results.append({
                "pair_id": pair.get("id", f"pair_{i}"),
                "similarity_result": similarity_result,
                "success": True
            })
            
            print(f"[AI-TASK] Completed analysis {i+1}/{len(text_pairs)}")
            
        except Exception as e:
            print(f"[AI-TASK] Failed analysis for pair {i}: {e}")
            results.append({
                "pair_id": pair.get("id", f"pair_{i}"),
                "similarity_result": None,
                "success": False,
                "error": str(e)
            })
    
    success_count = sum(1 for r in results if r["success"])
    print(f"[AI-TASK] batch_similarity_analysis DONE: {success_count}/{len(text_pairs)} successful")
    
    return {
        "results": results,
        "total_pairs": len(text_pairs),
        "success_count": success_count,
        "failure_count": len(text_pairs) - success_count
    }


# Registry of similarity AI tasks
SIMILARITY_TASKS = {
    "similarity.generate_embeddings": generate_embeddings_task,
    "similarity.semantic_analysis": calculate_semantic_similarity_task,
    "similarity.batch_analysis": batch_similarity_analysis_task,
}