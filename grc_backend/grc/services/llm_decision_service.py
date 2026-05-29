"""
Step 6: LLM Final Decision and Explanation Service
Provides human-level analysis and final classification of similar candidates.
Uses NVIDIA LLM to analyze reranked candidates and make recommendations.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..services.domain_classifier import DomainClassificationResult

logger = logging.getLogger(__name__)


@dataclass
class LLMDecisionResult:
    """Result from LLM decision analysis."""
    can_create: bool
    duplicate_risk: str  # "low", "medium", "high"
    overall_recommendation: str
    suggestions: List[Dict[str, Any]]
    raw_response: str = ""


class LLMDecisionService:
    """
    Service for LLM-based final similarity decision.
    
    Analyzes top reranked candidates and provides:
    - Final status classification (duplicate, highly_similar, related_but_different, different)
    - Detailed reasoning
    - Recommendations for user action
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM decision service.
        
        Args:
            api_key: NVIDIA API key (uses settings if not provided)
        """
        self.api_key = api_key
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model = "meta/llama-3.1-70b-instruct"
    
    def analyze_candidates(
        self,
        new_record: Dict[str, Any],
        classification_result: DomainClassificationResult,
        candidates: List[Dict[str, Any]]
    ) -> LLMDecisionResult:
        """
        Analyze reranked candidates and provide final decision.
        
        Args:
            new_record: Cleaned new record data
            classification_result: Step 2 classification result
            candidates: Top 3-5 reranked candidates from Step 5
        
        Returns:
            LLMDecisionResult with final classification and recommendations
        """
        try:
            logger.info(f"[Step 6] Analyzing {len(candidates)} candidates with LLM")
            
            # Build prompt
            prompt = self._build_decision_prompt(new_record, classification_result, candidates)
            
            # Call LLM
            response = self._call_llm(prompt)
            
            # Parse response
            decision = self._parse_llm_response(response)
            
            logger.info(f"[Step 6] LLM decision: can_create={decision.can_create}, risk={decision.duplicate_risk}")
            
            return decision
            
        except Exception as e:
            logger.exception(f"[Step 6] LLM analysis failed: {e}")
            # Return safe default
            return LLMDecisionResult(
                can_create=True,
                duplicate_risk="unknown",
                overall_recommendation="Unable to analyze similarity. Please review manually.",
                suggestions=[],
                raw_response=""
            )
    
    def _build_decision_prompt(
        self,
        new_record: Dict[str, Any],
        classification_result: DomainClassificationResult,
        candidates: List[Dict[str, Any]]
    ) -> str:
        """Build the LLM prompt for decision analysis."""
        
        # Format new record
        new_record_json = json.dumps({
            "name": new_record.get('name', ''),
            "description": new_record.get('description', ''),
            "domain": classification_result.primary_domain,
            "industry": classification_result.industry_vertical,
            "category": classification_result.compliance_area or classification_result.business_function,
            "sub_category": new_record.get('sub_category', ''),
            "purpose": new_record.get('purpose', ''),
            "scope": new_record.get('scope', ''),
            "control_objective": new_record.get('control_objective', ''),
            "evidence_requirement": new_record.get('evidence_requirement', '')
        }, indent=2)
        
        # Format candidates
        candidates_list = []
        for c in candidates:
            candidates_list.append({
                "id": c.get('entity_id') or c.get('id'),
                "record_type": c.get('entity_type', 'unknown'),
                "name": c.get('name', ''),
                "chroma_score": round(c.get('chroma_score', c.get('score', 0)), 3),
                "reranker_score": round(c.get('reranker_score', 0), 3),
                "domain": c.get('domain', ''),
                "category": c.get('category', ''),
                "description": c.get('embedding_text', c.get('description', ''))[:500]  # Truncate for token limit
            })
        
        candidates_json = json.dumps(candidates_list, indent=2)
        
        prompt = f"""You are an expert GRC (Governance, Risk, Compliance) similarity decision assistant.

Your task is to compare the new record with the candidate records returned by semantic search and reranking.

Decide whether each candidate is:
- duplicate (same meaning, different wording - should not create new)
- highly_similar (very close in scope and purpose - warn user)
- related_but_different (same domain but different focus - allow creation)
- different (no meaningful overlap - allow creation)

IMPORTANT RULES:
1. Do NOT mark something as duplicate only because it has the same domain or category.
2. Two records can belong to the same category but still have different purpose, scope, and control intent.
3. Compare: name/title, description, domain, category, context, purpose, scope, control objective.
4. Provide specific same_points and different_points for each candidate.

NEW RECORD:
{new_record_json}

CANDIDATE RECORDS (ranked by accuracy):
{candidates_json}

Return ONLY valid JSON in this exact format:
{{
  "can_create": true,
  "duplicate_risk": "low | medium | high",
  "overall_recommendation": "Brief overall advice for the user",
  "suggestions": [
    {{
      "id": "record id",
      "record_type": "framework|policy|subpolicy|compliance",
      "name": "record name",
      "chroma_score": 0.0,
      "reranker_score": 0.0,
      "final_status": "duplicate|highly_similar|related_but_different|different",
      "reason": "Detailed explanation of why this status was chosen",
      "same_points": ["point 1", "point 2"],
      "different_points": ["point 1", "point 2"],
      "recommendation": "use_existing|create_anyway|review_manually|merge"
    }}
  ]
}}

Respond with ONLY the JSON. No markdown, no explanation outside JSON."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call NVIDIA LLM API."""
        import requests
        from django.conf import settings
        
        api_key = self.api_key or getattr(settings, 'NVIDIA_API_KEY', None)
        if not api_key:
            raise ValueError("NVIDIA API key not configured")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,  # Low temperature for consistent decisions
            "max_tokens": 2000
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"LLM API error: {response.status_code} - {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _parse_llm_response(self, response: str) -> LLMDecisionResult:
        """Parse LLM JSON response into LLMDecisionResult."""
        try:
            # Clean response - remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Parse JSON
            data = json.loads(cleaned)
            
            return LLMDecisionResult(
                can_create=data.get("can_create", True),
                duplicate_risk=data.get("duplicate_risk", "unknown"),
                overall_recommendation=data.get("overall_recommendation", ""),
                suggestions=data.get("suggestions", []),
                raw_response=response
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"[Step 6] Failed to parse LLM response: {e}")
            logger.error(f"[Step 6] Raw response: {response[:500]}")
            
            # Return default with error info
            return LLMDecisionResult(
                can_create=True,
                duplicate_risk="unknown",
                overall_recommendation="Unable to parse LLM response. Please review manually.",
                suggestions=[],
                raw_response=response
            )


# Test function
def test_llm_decision():
    """Test the LLM decision service."""
    service = LLMDecisionService()
    
    new_record = {
        "name": "Food Hygiene and Sanitation Framework",
        "description": "Covers hygiene, sanitation, cleaning, and contamination prevention in food handling.",
        "purpose": "Ensure hygienic food handling",
        "scope": "All food handling areas"
    }
    
    # Mock classification result
    from ..services.domain_classifier import DomainClassificationResult
    classification = DomainClassificationResult(
        primary_domain="Food Safety",
        industry_vertical="Food Service",
        compliance_area="Food Safety",
        business_function="Operations",
        classification_method="llm",
        raw_response=""
    )
    
    candidates = [
        {
            "entity_id": 101,
            "entity_type": "Framework",
            "name": "Food Cleanliness Framework",
            "chroma_score": 0.82,
            "reranker_score": 0.94,
            "domain": "Food Safety",
            "embedding_text": "Covers cleaning, hygiene checks, sanitation controls."
        }
    ]
    
    result = service.analyze_candidates(new_record, classification, candidates)
    
    print(f"\nCan create: {result.can_create}")
    print(f"Risk: {result.duplicate_risk}")
    print(f"Recommendation: {result.overall_recommendation}")
    print(f"\nSuggestions:")
    for s in result.suggestions:
        print(f"  - {s['name']}: {s['final_status']} → {s['recommendation']}")
    
    return result


if __name__ == "__main__":
    test_llm_decision()
