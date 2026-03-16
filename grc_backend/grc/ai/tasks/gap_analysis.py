"""
Centralized AI tasks for Gap Analysis Between Framework Versions.
Provides AI-powered semantic gap analysis and impact assessment for framework comparison.
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


def analyze_framework_gaps_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
) -> dict[str, Any]:
    """
    Centralized task for AI-powered gap analysis between framework versions.
    
    Payload should contain:
    - original_framework: Dict with original framework structure
    - amended_framework: Dict with amended framework structure  
    - framework_name: Name of the framework being analyzed
    - comparison_context: Optional context about the comparison
    """
    original_framework = payload.get("original_framework", {})
    amended_framework = payload.get("amended_framework", {})
    framework_name = payload.get("framework_name", "Unknown Framework")
    comparison_context = payload.get("comparison_context", "")
    
    if not original_framework or not amended_framework:
        raise ValueError("Both original_framework and amended_framework are required")
    
    print(f"[AI-TASK] analyze_framework_gaps START: {framework_name}")
    
    # Create comprehensive gap analysis prompt
    prompt = f"""As a senior GRC compliance expert, conduct a comprehensive gap analysis between the original and amended versions of the {framework_name} framework.

COMPARISON CONTEXT: {comparison_context}

ORIGINAL FRAMEWORK STRUCTURE:
{json.dumps(original_framework, indent=2)[:8000]}

AMENDED FRAMEWORK STRUCTURE: 
{json.dumps(amended_framework, indent=2)[:8000]}

Provide a comprehensive gap analysis in JSON format:

{{
  "framework_info": {{
    "framework_name": "{framework_name}",
    "analysis_timestamp": "2026-03-16T03:30:00Z",
    "comparison_scope": "full_framework_analysis"
  }},
  "executive_summary": {{
    "total_changes_detected": 15,
    "critical_gaps": 3,
    "moderate_gaps": 8,
    "minor_gaps": 4,
    "overall_impact_level": "moderate",
    "compliance_risk_rating": "medium"
  }},
  "detailed_gap_analysis": {{
    "added_requirements": [
      {{
        "requirement_id": "NEW-REQ-001", 
        "title": "New Security Requirement",
        "description": "Description of new requirement",
        "impact_level": "high",
        "affected_areas": ["security", "access_control"],
        "implementation_priority": "immediate"
      }}
    ],
    "removed_requirements": [
      {{
        "requirement_id": "OLD-REQ-005",
        "title": "Deprecated Legacy Requirement", 
        "description": "Description of removed requirement",
        "impact_level": "low",
        "affected_areas": ["documentation"],
        "migration_needed": false
      }}
    ],
    "modified_requirements": [
      {{
        "requirement_id": "MOD-REQ-012",
        "title": "Updated Data Protection Requirement",
        "original_text": "Original requirement text...",
        "amended_text": "Updated requirement text...",
        "change_type": "enhancement",
        "impact_level": "moderate",
        "affected_areas": ["data_protection", "privacy"],
        "compliance_implications": "Requires policy updates"
      }}
    ]
  }},
  "impact_assessment": {{
    "policy_impact": {{
      "policies_requiring_updates": 5,
      "new_policies_needed": 2, 
      "obsolete_policies": 1,
      "estimated_update_effort": "moderate"
    }},
    "compliance_impact": {{
      "regulatory_alignment_risk": "low",
      "audit_findings_potential": "medium",
      "certification_impact": "minimal",
      "training_requirements": "standard_update_training"
    }},
    "operational_impact": {{
      "process_changes_required": 8,
      "system_updates_needed": 3,
      "staff_training_scope": "department_wide",
      "implementation_timeline": "3-6_months"
    }}
  }},
  "recommendations": {{
    "immediate_actions": [
      "Review and update critical security policies",
      "Assess current compliance posture against new requirements",
      "Notify affected departments of upcoming changes"
    ],
    "short_term_actions": [
      "Develop implementation roadmap for new requirements",
      "Update training materials and procedures",
      "Conduct gap assessment across all business units"
    ],
    "long_term_actions": [
      "Monitor regulatory developments for additional changes",
      "Implement continuous compliance monitoring",
      "Review framework update processes for efficiency"
    ]
  }},
  "risk_analysis": {{
    "compliance_risks": [
      {{
        "risk_description": "Non-compliance with new security requirements",
        "likelihood": "medium",
        "impact": "high", 
        "mitigation_strategy": "Immediate policy updates and training"
      }}
    ],
    "operational_risks": [
      {{
        "risk_description": "Process disruption during transition",
        "likelihood": "low",
        "impact": "medium",
        "mitigation_strategy": "Phased implementation approach"
      }}
    ],
    "financial_risks": [
      {{
        "risk_description": "Potential regulatory penalties",
        "likelihood": "low",
        "impact": "high",
        "estimated_cost_range": "$10,000-$100,000"
      }}
    ]
  }},
  "confidence_metrics": {{
    "analysis_completeness": 0.95,
    "change_detection_confidence": 0.92,
    "impact_assessment_confidence": 0.88,
    "recommendation_confidence": 0.90
  }},
  "methodology": {{
    "analysis_approach": "AI-powered semantic comparison with regulatory context",
    "frameworks_referenced": ["NIST", "ISO27001", "SOX", "GDPR"],
    "quality_assurance": "Automated consistency checks and expert validation rules"
  }}
}}

ANALYSIS CRITERIA:
- Focus on compliance and regulatory implications
- Assess business impact and implementation complexity
- Provide actionable recommendations with priority levels
- Consider risk mitigation strategies
- Include confidence scoring for all assessments"""

    try:
        result = _generate_json(service, "gap_analysis.framework_comparison", prompt, options)
        print(f"[AI-TASK] Framework gap analysis completed for {framework_name}")
        return result
    except Exception as e:
        print(f"[AI-TASK] Failed to analyze framework gaps: {e}")
        # Return fallback result
        return {
            "framework_info": {
                "framework_name": framework_name,
                "analysis_timestamp": "2026-03-16T03:30:00Z",
                "comparison_scope": "error_fallback"
            },
            "executive_summary": {
                "total_changes_detected": 0,
                "critical_gaps": 0,
                "moderate_gaps": 0,
                "minor_gaps": 0,
                "overall_impact_level": "unknown",
                "compliance_risk_rating": "requires_manual_review"
            },
            "error_details": {
                "error_message": str(e),
                "fallback_reason": "AI analysis failed, manual review required",
                "recommended_action": "Conduct manual gap analysis"
            },
            "confidence_metrics": {
                "analysis_completeness": 0.0,
                "change_detection_confidence": 0.0,
                "impact_assessment_confidence": 0.0,
                "recommendation_confidence": 0.0
            }
        }


def assess_compliance_impact_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
) -> dict[str, Any]:
    """
    Centralized task for assessing compliance impact of framework changes.
    
    Payload should contain:
    - changes_list: List of identified changes between frameworks
    - current_policies: Current organizational policies
    - regulatory_context: Relevant regulatory requirements
    - framework_name: Name of framework being assessed
    """
    changes_list = payload.get("changes_list", [])
    current_policies = payload.get("current_policies", [])
    regulatory_context = payload.get("regulatory_context", "")
    framework_name = payload.get("framework_name", "Unknown Framework")
    
    if not changes_list:
        raise ValueError("changes_list is required in payload")
    
    print(f"[AI-TASK] assess_compliance_impact START: {len(changes_list)} changes")
    
    # Create compliance impact assessment prompt
    prompt = f"""As a compliance risk expert, assess the compliance impact of framework changes for {framework_name}.

REGULATORY CONTEXT: {regulatory_context}

IDENTIFIED CHANGES:
{json.dumps(changes_list, indent=2)[:6000]}

CURRENT ORGANIZATIONAL POLICIES:
{json.dumps(current_policies, indent=2)[:4000]}

Provide detailed compliance impact assessment in JSON format:

{{
  "overall_compliance_assessment": {{
    "risk_level": "medium",
    "compliance_score": 0.85,
    "regulatory_alignment": "high", 
    "immediate_action_required": true
  }},
  "change_impact_analysis": [
    {{
      "change_id": "CHG-001",
      "change_description": "Updated data retention requirements",
      "compliance_impact_level": "high",
      "affected_regulations": ["GDPR Article 5", "SOX Section 409"],
      "policy_gaps_identified": ["Data Retention Policy needs update", "Backup procedures require review"],
      "remediation_priority": "immediate",
      "estimated_effort": "2-4 weeks",
      "compliance_risk_if_ignored": "Potential regulatory penalty up to €20M under GDPR"
    }}
  ],
  "regulatory_mapping": {{
    "affected_regulations": [
      {{
        "regulation_name": "GDPR",
        "articles_impacted": ["Article 5", "Article 17"],
        "compliance_status": "requires_updates",
        "risk_level": "high"
      }}
    ]
  }},
  "policy_update_requirements": {{
    "policies_needing_immediate_update": [
      {{
        "policy_name": "Data Retention Policy",
        "current_version": "v2.1",
        "update_priority": "critical",
        "expected_completion": "within_30_days",
        "owner": "Data Protection Officer"
      }}
    ],
    "new_policies_required": [
      {{
        "policy_name": "AI Ethics and Governance Policy",
        "justification": "New AI governance requirements in framework",
        "development_priority": "high",
        "expected_completion": "within_60_days"
      }}
    ]
  }},
  "compliance_recommendations": {{
    "immediate_actions": [
      "Conduct compliance gap assessment",
      "Update critical policies within 30 days",
      "Notify regulatory bodies if required"
    ],
    "medium_term_actions": [
      "Implement updated controls and procedures",
      "Train staff on new requirements",
      "Update compliance monitoring systems"
    ],
    "ongoing_monitoring": [
      "Regular compliance status reviews",
      "Automated compliance reporting",
      "Continuous framework update monitoring"
    ]
  }},
  "confidence_metrics": {{
    "impact_assessment_confidence": 0.91,
    "regulatory_mapping_confidence": 0.87,
    "recommendation_confidence": 0.89
  }}
}}

Focus on specific regulatory implications and actionable compliance steps."""

    try:
        result = _generate_json(service, "gap_analysis.compliance_impact", prompt, options)
        print(f"[AI-TASK] Compliance impact assessment completed")
        return result
    except Exception as e:
        print(f"[AI-TASK] Failed to assess compliance impact: {e}")
        return {
            "overall_compliance_assessment": {
                "risk_level": "unknown",
                "compliance_score": 0.0,
                "regulatory_alignment": "requires_review",
                "immediate_action_required": True
            },
            "error_details": {
                "error_message": str(e),
                "recommended_action": "Manual compliance review required"
            },
            "confidence_metrics": {
                "impact_assessment_confidence": 0.0,
                "regulatory_mapping_confidence": 0.0,
                "recommendation_confidence": 0.0
            }
        }


def generate_migration_roadmap_task(
    service,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    options: AIRequestOptions | None = None,
) -> dict[str, Any]:
    """
    Centralized task for generating implementation roadmap for framework changes.
    
    Payload should contain:
    - gap_analysis_results: Results from gap analysis
    - organizational_context: Information about organization size, complexity, etc.
    - resource_constraints: Available resources and timeline constraints
    - framework_name: Name of framework
    """
    gap_analysis_results = payload.get("gap_analysis_results", {})
    organizational_context = payload.get("organizational_context", {})
    resource_constraints = payload.get("resource_constraints", {})
    framework_name = payload.get("framework_name", "Unknown Framework")
    
    if not gap_analysis_results:
        raise ValueError("gap_analysis_results is required in payload")
    
    print(f"[AI-TASK] generate_migration_roadmap START: {framework_name}")
    
    # Create migration roadmap prompt
    prompt = f"""As a GRC implementation specialist, create a detailed migration roadmap for implementing {framework_name} framework changes.

GAP ANALYSIS RESULTS:
{json.dumps(gap_analysis_results, indent=2)[:6000]}

ORGANIZATIONAL CONTEXT:
{json.dumps(organizational_context, indent=2)[:2000]}

RESOURCE CONSTRAINTS:
{json.dumps(resource_constraints, indent=2)[:2000]}

Create a comprehensive implementation roadmap in JSON format:

{{
  "roadmap_overview": {{
    "framework_name": "{framework_name}",
    "total_implementation_phases": 4,
    "estimated_total_duration": "6-9 months", 
    "resource_requirements": "medium",
    "complexity_rating": "moderate"
  }},
  "implementation_phases": [
    {{
      "phase_number": 1,
      "phase_name": "Assessment and Planning",
      "duration": "4-6 weeks",
      "objectives": ["Complete detailed gap assessment", "Develop detailed project plan", "Secure stakeholder buy-in"],
      "deliverables": ["Gap assessment report", "Implementation project plan", "Resource allocation plan"],
      "key_activities": [
        {{
          "activity": "Conduct comprehensive policy gap analysis",
          "duration": "2 weeks",
          "resources_required": ["Compliance team", "Legal review"],
          "dependencies": [],
          "critical_path": true
        }}
      ],
      "success_criteria": ["All gaps identified and documented", "Project plan approved by leadership"],
      "risks_and_mitigations": [
        {{
          "risk": "Incomplete gap identification",
          "likelihood": "medium",
          "impact": "high",
          "mitigation": "Engage external consultants for validation"
        }}
      ]
    }}
  ],
  "resource_planning": {{
    "team_composition": [
      {{
        "role": "Project Manager",
        "allocation": "100%",
        "duration": "full project",
        "skills_required": ["GRC project management", "Stakeholder management"]
      }},
      {{
        "role": "Compliance Specialist", 
        "allocation": "75%",
        "duration": "phases 1-3",
        "skills_required": ["Framework expertise", "Policy development"]
      }}
    ],
    "budget_estimates": {{
      "internal_resources": "$150,000",
      "external_consultants": "$75,000",
      "training_costs": "$25,000",
      "technology_costs": "$50,000",
      "total_estimated_cost": "$300,000"
    }}
  }},
  "risk_management": {{
    "project_risks": [
      {{
        "risk_category": "timeline",
        "risk_description": "Implementation delays due to complexity",
        "probability": "medium", 
        "impact": "medium",
        "mitigation_strategy": "Phased approach with buffer time",
        "contingency_plan": "Prioritize critical requirements first"
      }}
    ]
  }},
  "success_metrics": {{
    "completion_criteria": [
      "100% of critical gaps addressed",
      "All updated policies approved and deployed", 
      "Staff training completion rate >95%",
      "Successful compliance audit"
    ],
    "performance_indicators": [
      {{
        "metric": "Policy update completion rate",
        "target": "95%",
        "measurement_frequency": "weekly"
      }}
    ]
  }},
  "change_management": {{
    "stakeholder_engagement": [
      {{
        "stakeholder_group": "Executive Leadership",
        "engagement_strategy": "Regular steering committee meetings",
        "communication_frequency": "bi-weekly"
      }}
    ],
    "training_plan": {{
      "training_modules": [
        {{
          "module_name": "Framework Updates Overview",
          "target_audience": "All staff",
          "delivery_method": "online_course",
          "duration": "2 hours"
        }}
      ]
    }}
  }},
  "quality_assurance": {{
    "review_checkpoints": [
      "Phase completion reviews",
      "Policy quality audits", 
      "Compliance validation tests"
    ],
    "validation_methods": [
      "Expert review panels",
      "Automated compliance checks",
      "Stakeholder acceptance testing"
    ]
  }}
}}

Focus on practical implementation steps with realistic timelines and resource requirements."""

    try:
        result = _generate_json(service, "gap_analysis.migration_roadmap", prompt, options)
        print(f"[AI-TASK] Migration roadmap generated for {framework_name}")
        return result
    except Exception as e:
        print(f"[AI-TASK] Failed to generate migration roadmap: {e}")
        return {
            "roadmap_overview": {
                "framework_name": framework_name,
                "total_implementation_phases": 0,
                "estimated_total_duration": "unknown",
                "resource_requirements": "unknown", 
                "complexity_rating": "requires_assessment"
            },
            "error_details": {
                "error_message": str(e),
                "recommended_action": "Manual roadmap development required"
            }
        }


# Registry of gap analysis AI tasks  
GAP_ANALYSIS_TASKS = {
    "gap_analysis.framework_comparison": analyze_framework_gaps_task,
    "gap_analysis.compliance_impact": assess_compliance_impact_task, 
    "gap_analysis.migration_roadmap": generate_migration_roadmap_task,
}