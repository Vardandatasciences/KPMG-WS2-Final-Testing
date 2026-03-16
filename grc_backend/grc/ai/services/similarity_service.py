"""
Centralized Similarity Matching Service
Provides AI-powered similarity analysis using centralized AI service instead of direct OpenAI calls.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher
import re
from ..service import get_ai_service

logger = logging.getLogger(__name__)


class CentralizedSimilarityMatcher:
    """
    Centralized service for matching target controls with origin policies using centralized AI service
    """
    
    def __init__(self):
        self.ai_service = get_ai_service()
        logger.info("CentralizedSimilarityMatcher initialized with centralized AI service")
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity using SequenceMatcher (0.0 - 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize text
        text1_normalized = text1.lower().strip()
        text2_normalized = text2.lower().strip()
        
        # Calculate similarity ratio
        return SequenceMatcher(None, text1_normalized, text2_normalized).ratio()
    
    def calculate_keyword_overlap(self, text1: str, text2: str) -> float:
        """
        Calculate keyword overlap score (0.0 - 1.0)
        """
        if not text1 or not text2:
            return 0.0
        
        # Extract keywords (words with 4+ characters, excluding common words)
        stop_words = {
            'that', 'this', 'with', 'from', 'have', 'been', 'were', 'will',
            'shall', 'must', 'should', 'would', 'could', 'their', 'there',
            'which', 'where', 'when', 'what', 'about', 'such', 'into', 'only'
        }
        
        def extract_keywords(text):
            words = re.findall(r'\b[a-z]{4,}\b', text.lower())
            return set(w for w in words if w not in stop_words)
        
        keywords1 = extract_keywords(text1)
        keywords2 = extract_keywords(text2)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_id_similarity(self, target_id: str, origin_id: str) -> float:
        """
        Calculate similarity between control/policy IDs
        Returns higher score for matching patterns (e.g., "1.2.3" vs "Requirement 1.2.3")
        """
        if not target_id or not origin_id:
            return 0.0
        
        # Extract numeric patterns
        target_nums = re.findall(r'\d+\.?\d*', target_id)
        origin_nums = re.findall(r'\d+\.?\d*', origin_id)
        
        if target_nums and origin_nums:
            # Check if any numbers match
            for t_num in target_nums:
                for o_num in origin_nums:
                    if t_num == o_num or t_num in o_num or o_num in t_num:
                        return 0.9  # High score for ID match
        
        # Fallback to text similarity
        return self.calculate_text_similarity(target_id, origin_id) * 0.7
    
    def calculate_ai_similarity(
        self,
        target_control: Dict[str, Any],
        origin_item: Dict[str, Any],
        item_type: str
    ) -> dict[str, Any]:
        """
        Calculate AI-based similarity using centralized AI service
        Returns comprehensive similarity analysis instead of just cosine similarity
        """
        try:
            # Prepare text for AI analysis
            target_text = f"{target_control.get('control_id', '')} {target_control.get('control_name', '')} {target_control.get('change_description', '')}"
            
            if item_type == 'policy':
                origin_text = f"{origin_item.get('Identifier', '')} {origin_item.get('PolicyName', '')} {origin_item.get('PolicyDescription', '')}"
            elif item_type == 'subpolicy':
                origin_text = f"{origin_item.get('Identifier', '')} {origin_item.get('SubPolicyName', '')} {origin_item.get('Description', '')}"
            else:
                origin_text = f"{origin_item.get('ComplianceTitle', '')} {origin_item.get('ComplianceItemDescription', '')}"
            
            # Call centralized AI service for semantic similarity analysis
            payload = {
                "text1": target_text.strip(),
                "text2": origin_text.strip(),
                "comparison_type": item_type,
                "context": f"Comparing {item_type} for framework change matching analysis"
            }
            
            result = self.ai_service.run_task("similarity.semantic_analysis", payload)
            
            print(f"[SIMILARITY] AI analysis completed for {item_type} comparison")
            return result
            
        except Exception as e:
            logger.warning(f"Failed to get AI similarity analysis: {e}")
            return {
                "overall_similarity_score": 0.0,
                "similarity_analysis": {
                    "conceptual_overlap": 0.0,
                    "terminology_alignment": 0.0,
                    "structural_similarity": 0.0,
                    "intent_matching": 0.0
                },
                "confidence_metrics": {
                    "analysis_confidence": 0.0,
                    "recommendation_confidence": 0.0,
                    "data_quality_score": 0.0
                },
                "justification": f"AI analysis failed: {str(e)}"
            }
    
    def calculate_hybrid_similarity(
        self,
        target_control: Dict[str, Any],
        origin_item: Dict[str, Any],
        item_type: str
    ) -> float:
        """
        Calculate hybrid similarity score combining multiple methods
        
        Args:
            target_control: Modified control from target
            origin_item: Policy/SubPolicy/Compliance from origin
            item_type: 'policy', 'subpolicy', or 'compliance'
        
        Returns:
            Similarity score (0.0 - 1.0)
        """
        scores = []
        weights = []
        
        # 1. ID similarity (high weight)
        target_id = target_control.get('control_id', '')
        if item_type == 'policy':
            origin_id = origin_item.get('Identifier', '')
        elif item_type == 'subpolicy':
            origin_id = origin_item.get('Identifier', '')
        else:  # compliance
            origin_id = origin_item.get('ComplianceTitle', '')
        
        if target_id and origin_id:
            id_score = self.calculate_id_similarity(target_id, origin_id)
            scores.append(id_score)
            weights.append(3.0)  # High weight for ID match
        
        # 2. Name/Title similarity
        target_name = target_control.get('control_name', '')
        if item_type == 'policy':
            origin_name = origin_item.get('PolicyName', '')
        elif item_type == 'subpolicy':
            origin_name = origin_item.get('SubPolicyName', '')
        else:
            origin_name = origin_item.get('ComplianceTitle', '')
        
        if target_name and origin_name:
            name_score = self.calculate_text_similarity(target_name, origin_name)
            scores.append(name_score)
            weights.append(2.0)  # Medium-high weight
        
        # 3. Description similarity
        target_desc = target_control.get('change_description', '')
        if item_type == 'policy':
            origin_desc = origin_item.get('PolicyDescription', '')
        elif item_type == 'subpolicy':
            origin_desc = origin_item.get('Description', '')
        else:
            origin_desc = origin_item.get('ComplianceItemDescription', '')
        
        if target_desc and origin_desc:
            desc_score = self.calculate_text_similarity(target_desc, origin_desc)
            scores.append(desc_score)
            weights.append(1.5)  # Medium weight
        
        # 4. Keyword overlap
        combined_target = f"{target_name} {target_desc}"
        combined_origin = f"{origin_name} {origin_desc}"
        
        if combined_target.strip() and combined_origin.strip():
            keyword_score = self.calculate_keyword_overlap(combined_target, combined_origin)
            scores.append(keyword_score)
            weights.append(1.0)  # Lower weight
        
        # Calculate weighted average
        if not scores:
            return 0.0
        
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight
    
    def find_best_matches(
        self,
        target_control: Dict[str, Any],
        origin_data: Dict[str, Any],
        top_n: int = 5,
        use_ai: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find best matching items in origin for a target control using centralized AI
        
        Args:
            target_control: Modified control from target
            origin_data: Complete origin framework data with policies
            top_n: Number of top matches to return
            use_ai: Whether to use centralized AI (recommended for better accuracy)
        
        Returns:
            List of matches with scores and detailed analysis
        """
        matches = []
        
        # Extract policies from origin data
        policies = origin_data.get('policies', [])
        
        print(f"[SIMILARITY] Finding matches for control: {target_control.get('control_id', 'unknown')} (AI enabled: {use_ai})")
        
        for policy in policies:
            # Check policy level
            hybrid_score = self.calculate_hybrid_similarity(target_control, policy, 'policy')
            ai_analysis = {}
            
            if use_ai:
                ai_analysis = self.calculate_ai_similarity(target_control, policy, 'policy')
            
            # Use AI overall score if available, otherwise hybrid score
            if use_ai and ai_analysis.get('overall_similarity_score', 0) > 0:
                final_score = ai_analysis['overall_similarity_score']
                # Combine with hybrid score for robustness (60% AI, 40% hybrid)
                final_score = (final_score * 0.6) + (hybrid_score * 0.4)
            else:
                final_score = hybrid_score
            
            matches.append({
                'type': 'policy',
                'item': policy,
                'policy_id': policy.get('PolicyId'),
                'policy_name': policy.get('PolicyName'),
                'identifier': policy.get('Identifier'),
                'score': final_score,
                'hybrid_score': hybrid_score,
                'ai_analysis': ai_analysis if use_ai else None,
                'path': f"Policy: {policy.get('PolicyName')}",
                'confidence_metrics': ai_analysis.get('confidence_metrics', {}) if use_ai else {}
            })
            
            # Check sub-policy level
            for subpolicy in policy.get('subpolicies', []):
                hybrid_score = self.calculate_hybrid_similarity(target_control, subpolicy, 'subpolicy')
                ai_analysis = {}
                
                if use_ai:
                    ai_analysis = self.calculate_ai_similarity(target_control, subpolicy, 'subpolicy')
                
                if use_ai and ai_analysis.get('overall_similarity_score', 0) > 0:
                    final_score = ai_analysis['overall_similarity_score']
                    final_score = (final_score * 0.6) + (hybrid_score * 0.4)
                else:
                    final_score = hybrid_score
                
                matches.append({
                    'type': 'subpolicy',
                    'item': subpolicy,
                    'policy_id': policy.get('PolicyId'),
                    'policy_name': policy.get('PolicyName'),
                    'subpolicy_id': subpolicy.get('SubPolicyId'),
                    'subpolicy_name': subpolicy.get('SubPolicyName'),
                    'identifier': subpolicy.get('Identifier'),
                    'score': final_score,
                    'hybrid_score': hybrid_score,
                    'ai_analysis': ai_analysis if use_ai else None,
                    'path': f"Policy: {policy.get('PolicyName')} > Sub-Policy: {subpolicy.get('SubPolicyName')}",
                    'confidence_metrics': ai_analysis.get('confidence_metrics', {}) if use_ai else {}
                })
                
                # Check compliance level
                for compliance in subpolicy.get('compliances', []):
                    hybrid_score = self.calculate_hybrid_similarity(target_control, compliance, 'compliance')
                    ai_analysis = {}
                    
                    if use_ai:
                        ai_analysis = self.calculate_ai_similarity(target_control, compliance, 'compliance')
                    
                    if use_ai and ai_analysis.get('overall_similarity_score', 0) > 0:
                        final_score = ai_analysis['overall_similarity_score']
                        final_score = (final_score * 0.6) + (hybrid_score * 0.4)
                    else:
                        final_score = hybrid_score
                    
                    matches.append({
                        'type': 'compliance',
                        'item': compliance,
                        'policy_id': policy.get('PolicyId'),
                        'policy_name': policy.get('PolicyName'),
                        'subpolicy_id': subpolicy.get('SubPolicyId'),
                        'subpolicy_name': subpolicy.get('SubPolicyName'),
                        'compliance_id': compliance.get('ComplianceId'),
                        'compliance_title': compliance.get('ComplianceTitle'),
                        'score': final_score,
                        'hybrid_score': hybrid_score,
                        'ai_analysis': ai_analysis if use_ai else None,
                        'path': f"Policy: {policy.get('PolicyName')} > Sub-Policy: {subpolicy.get('SubPolicyName')} > Compliance: {compliance.get('ComplianceTitle')}",
                        'confidence_metrics': ai_analysis.get('confidence_metrics', {}) if use_ai else {}
                    })
        
        # Sort by score (descending) and return top N
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"[SIMILARITY] Found {len(matches)} total matches, returning top {top_n}")
        
        return matches[:top_n]
    
    def batch_match_controls(
        self,
        target_controls: List[Dict[str, Any]],
        origin_data: Dict[str, Any],
        use_ai: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Match multiple target controls to origin items using centralized AI service
        
        Args:
            target_controls: List of modified controls
            origin_data: Complete origin framework data
            use_ai: Whether to use centralized AI (recommended for better results)
        
        Returns:
            Dictionary mapping control_id to list of matches with detailed AI analysis
        """
        results = {}
        
        print(f"[SIMILARITY] Batch matching {len(target_controls)} controls (AI enabled: {use_ai})")
        
        for i, control in enumerate(target_controls):
            control_id = control.get('control_id', '')
            if not control_id:
                continue
            
            print(f"[SIMILARITY] Processing control {i+1}/{len(target_controls)}: {control_id}")
            
            matches = self.find_best_matches(control, origin_data, top_n=3, use_ai=use_ai)
            results[control_id] = matches
        
        print(f"[SIMILARITY] Batch matching completed: {len(results)} controls processed")
        
        return results


# Singleton instance
_centralized_similarity_matcher = None

def get_centralized_similarity_matcher() -> CentralizedSimilarityMatcher:
    """Get or create singleton instance of CentralizedSimilarityMatcher"""
    global _centralized_similarity_matcher
    if _centralized_similarity_matcher is None:
        _centralized_similarity_matcher = CentralizedSimilarityMatcher()
    return _centralized_similarity_matcher