"""
Centralized Gap Analysis Service
Provides AI-powered semantic gap analysis for framework version comparison using centralized AI service.
"""

import logging
from typing import Dict, List, Optional, Any
from ..service import get_ai_service

logger = logging.getLogger(__name__)


class CentralizedGapAnalysisService:
    """
    Centralized service for AI-powered gap analysis between framework versions
    """
    
    def __init__(self):
        self.ai_service = get_ai_service()
        logger.info("CentralizedGapAnalysisService initialized with centralized AI service")
    
    def analyze_framework_gaps(
        self,
        original_framework: Dict[str, Any],
        amended_framework: Dict[str, Any],
        framework_name: str,
        comparison_context: str = ""
    ) -> Dict[str, Any]:
        """
        Perform comprehensive AI-powered gap analysis between framework versions
        
        Args:
            original_framework: Original framework structure
            amended_framework: Amended framework structure
            framework_name: Name of the framework
            comparison_context: Additional context about the comparison
        
        Returns:
            Comprehensive gap analysis results with AI insights
        """
        try:
            print(f"[GAP-ANALYSIS] Starting AI-powered gap analysis for {framework_name}")
            
            # Prepare payload for centralized AI service
            payload = {
                "original_framework": original_framework,
                "amended_framework": amended_framework,
                "framework_name": framework_name,
                "comparison_context": comparison_context
            }
            
            # Call centralized AI service for gap analysis
            result = self.ai_service.run_task("gap_analysis.framework_comparison", payload)
            
            print(f"[GAP-ANALYSIS] AI gap analysis completed for {framework_name}")
            
            # Enhance result with additional metadata
            result["analysis_metadata"] = {
                "service_version": "centralized_ai_v1",
                "analysis_type": "ai_powered_semantic_gap_analysis",
                "framework_analyzed": framework_name,
                "original_framework_size": len(str(original_framework)),
                "amended_framework_size": len(str(amended_framework))
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to perform AI gap analysis for {framework_name}: {e}")
            
            # Return fallback structural analysis
            return self._fallback_structural_analysis(
                original_framework, amended_framework, framework_name, str(e)
            )
    
    def assess_compliance_impact(
        self,
        changes_list: List[Dict[str, Any]],
        current_policies: List[Dict[str, Any]],
        framework_name: str,
        regulatory_context: str = ""
    ) -> Dict[str, Any]:
        """
        Assess compliance impact of framework changes using AI analysis
        
        Args:
            changes_list: List of identified changes between frameworks
            current_policies: Current organizational policies
            framework_name: Name of framework being assessed
            regulatory_context: Relevant regulatory requirements
        
        Returns:
            Detailed compliance impact assessment
        """
        try:
            print(f"[GAP-ANALYSIS] Assessing compliance impact for {len(changes_list)} changes")
            
            # Prepare payload for AI service
            payload = {
                "changes_list": changes_list,
                "current_policies": current_policies,
                "regulatory_context": regulatory_context,
                "framework_name": framework_name
            }
            
            # Call centralized AI service for compliance impact analysis
            result = self.ai_service.run_task("gap_analysis.compliance_impact", payload)
            
            print(f"[GAP-ANALYSIS] Compliance impact assessment completed")
            
            # Add metadata
            result["assessment_metadata"] = {
                "service_version": "centralized_ai_v1",
                "changes_analyzed": len(changes_list),
                "policies_reviewed": len(current_policies),
                "framework_name": framework_name
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to assess compliance impact: {e}")
            
            # Return basic fallback assessment
            return {
                "overall_compliance_assessment": {
                    "risk_level": "requires_manual_review",
                    "compliance_score": 0.0,
                    "regulatory_alignment": "unknown",
                    "immediate_action_required": True
                },
                "error_details": {
                    "error_message": str(e),
                    "fallback_reason": "AI compliance analysis failed",
                    "recommended_action": "Conduct manual compliance review with legal and compliance teams"
                },
                "confidence_metrics": {
                    "impact_assessment_confidence": 0.0,
                    "regulatory_mapping_confidence": 0.0,
                    "recommendation_confidence": 0.0
                }
            }
    
    def generate_implementation_roadmap(
        self,
        gap_analysis_results: Dict[str, Any],
        organizational_context: Dict[str, Any],
        resource_constraints: Dict[str, Any],
        framework_name: str
    ) -> Dict[str, Any]:
        """
        Generate AI-powered implementation roadmap for framework changes
        
        Args:
            gap_analysis_results: Results from gap analysis
            organizational_context: Information about organization
            resource_constraints: Available resources and constraints
            framework_name: Name of framework
        
        Returns:
            Detailed implementation roadmap with AI recommendations
        """
        try:
            print(f"[GAP-ANALYSIS] Generating implementation roadmap for {framework_name}")
            
            # Prepare payload for AI service
            payload = {
                "gap_analysis_results": gap_analysis_results,
                "organizational_context": organizational_context,
                "resource_constraints": resource_constraints,
                "framework_name": framework_name
            }
            
            # Call centralized AI service for roadmap generation
            result = self.ai_service.run_task("gap_analysis.migration_roadmap", payload)
            
            print(f"[GAP-ANALYSIS] Implementation roadmap generated successfully")
            
            # Add roadmap metadata
            result["roadmap_metadata"] = {
                "service_version": "centralized_ai_v1",
                "generation_method": "ai_powered_roadmap",
                "framework_name": framework_name,
                "organization_profile": organizational_context.get("organization_size", "unknown")
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate implementation roadmap: {e}")
            
            # Return basic fallback roadmap
            return {
                "roadmap_overview": {
                    "framework_name": framework_name,
                    "total_implementation_phases": 0,
                    "estimated_total_duration": "requires_assessment",
                    "resource_requirements": "unknown",
                    "complexity_rating": "requires_analysis"
                },
                "error_details": {
                    "error_message": str(e),
                    "fallback_reason": "AI roadmap generation failed",
                    "recommended_action": "Develop implementation roadmap manually with project management team"
                }
            }
    
    def perform_comprehensive_analysis(
        self,
        original_framework: Dict[str, Any],
        amended_framework: Dict[str, Any],
        current_policies: List[Dict[str, Any]],
        framework_name: str,
        organizational_context: Dict[str, Any] = None,
        resource_constraints: Dict[str, Any] = None,
        regulatory_context: str = ""
    ) -> Dict[str, Any]:
        """
        Perform comprehensive gap analysis including framework comparison, 
        compliance impact, and implementation roadmap
        
        Args:
            original_framework: Original framework structure
            amended_framework: Amended framework structure  
            current_policies: Current organizational policies
            framework_name: Name of framework
            organizational_context: Organization information
            resource_constraints: Resource and timeline constraints
            regulatory_context: Regulatory requirements context
        
        Returns:
            Complete comprehensive analysis results
        """
        print(f"[GAP-ANALYSIS] Starting comprehensive analysis for {framework_name}")
        
        comprehensive_results = {
            "framework_name": framework_name,
            "analysis_timestamp": "2026-03-16T03:30:00Z",
            "analysis_type": "comprehensive_ai_powered_gap_analysis"
        }
        
        # 1. Framework Gap Analysis
        try:
            gap_analysis = self.analyze_framework_gaps(
                original_framework, amended_framework, framework_name
            )
            comprehensive_results["gap_analysis"] = gap_analysis
        except Exception as e:
            logger.error(f"Gap analysis failed: {e}")
            comprehensive_results["gap_analysis"] = {"error": str(e)}
        
        # 2. Compliance Impact Assessment (if gap analysis has changes)
        if comprehensive_results.get("gap_analysis", {}).get("detailed_gap_analysis"):
            try:
                changes_list = []
                
                # Extract changes from gap analysis results
                gap_details = comprehensive_results["gap_analysis"]["detailed_gap_analysis"]
                
                for added in gap_details.get("added_requirements", []):
                    changes_list.append({
                        "change_type": "addition",
                        "change_id": added.get("requirement_id", ""),
                        "change_description": added.get("description", ""),
                        "impact_level": added.get("impact_level", "medium")
                    })
                
                for modified in gap_details.get("modified_requirements", []):
                    changes_list.append({
                        "change_type": "modification",
                        "change_id": modified.get("requirement_id", ""),
                        "change_description": modified.get("description", ""),
                        "impact_level": modified.get("impact_level", "medium")
                    })
                
                if changes_list:
                    compliance_impact = self.assess_compliance_impact(
                        changes_list, current_policies, framework_name, regulatory_context
                    )
                    comprehensive_results["compliance_impact"] = compliance_impact
            except Exception as e:
                logger.error(f"Compliance impact assessment failed: {e}")
                comprehensive_results["compliance_impact"] = {"error": str(e)}
        
        # 3. Implementation Roadmap (if gap analysis and compliance impact are available)
        if (comprehensive_results.get("gap_analysis") and 
            comprehensive_results.get("compliance_impact") and
            organizational_context and resource_constraints):
            try:
                roadmap = self.generate_implementation_roadmap(
                    comprehensive_results["gap_analysis"],
                    organizational_context or {},
                    resource_constraints or {},
                    framework_name
                )
                comprehensive_results["implementation_roadmap"] = roadmap
            except Exception as e:
                logger.error(f"Implementation roadmap generation failed: {e}")
                comprehensive_results["implementation_roadmap"] = {"error": str(e)}
        
        # Summary metrics
        comprehensive_results["analysis_summary"] = {
            "components_completed": sum([
                1 if "error" not in comprehensive_results.get("gap_analysis", {}) else 0,
                1 if "error" not in comprehensive_results.get("compliance_impact", {}) else 0,
                1 if "error" not in comprehensive_results.get("implementation_roadmap", {}) else 0
            ]),
            "total_components": 3,
            "analysis_quality": "ai_powered" if all(
                "error" not in comp for comp in [
                    comprehensive_results.get("gap_analysis", {}),
                    comprehensive_results.get("compliance_impact", {}),
                    comprehensive_results.get("implementation_roadmap", {})
                ] if comp
            ) else "partial_ai_analysis"
        }
        
        print(f"[GAP-ANALYSIS] Comprehensive analysis completed for {framework_name}")
        
        return comprehensive_results
    
    def _fallback_structural_analysis(
        self, 
        original_framework: Dict[str, Any], 
        amended_framework: Dict[str, Any], 
        framework_name: str,
        error_message: str
    ) -> Dict[str, Any]:
        """
        Fallback structural comparison when AI analysis fails
        """
        return {
            "framework_info": {
                "framework_name": framework_name,
                "analysis_timestamp": "2026-03-16T03:30:00Z",
                "comparison_scope": "fallback_structural_analysis"
            },
            "executive_summary": {
                "total_changes_detected": 0,
                "critical_gaps": 0,
                "moderate_gaps": 0,
                "minor_gaps": 0,
                "overall_impact_level": "requires_manual_analysis",
                "compliance_risk_rating": "unknown"
            },
            "error_details": {
                "ai_analysis_failed": True,
                "error_message": error_message,
                "fallback_reason": "Using structural comparison only",
                "recommended_action": "Manual gap analysis required by subject matter experts"
            },
            "structural_comparison": {
                "original_policies_count": len(original_framework.get("policies", [])),
                "amended_policies_count": len(amended_framework.get("policies", [])),
                "structure_changed": len(original_framework.get("policies", [])) != len(amended_framework.get("policies", []))
            },
            "confidence_metrics": {
                "analysis_completeness": 0.3,  # Low due to fallback
                "change_detection_confidence": 0.1,
                "impact_assessment_confidence": 0.0,
                "recommendation_confidence": 0.0
            }
        }


# Singleton instance
_centralized_gap_analysis_service = None

def get_centralized_gap_analysis_service() -> CentralizedGapAnalysisService:
    """Get or create singleton instance of CentralizedGapAnalysisService"""
    global _centralized_gap_analysis_service
    if _centralized_gap_analysis_service is None:
        _centralized_gap_analysis_service = CentralizedGapAnalysisService()
    return _centralized_gap_analysis_service