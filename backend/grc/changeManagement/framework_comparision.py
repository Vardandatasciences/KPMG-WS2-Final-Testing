#!/usr/bin/env python3
"""
Framework Comparison and Export Module

This module provides functionality to export complete framework data
including policies, subpolicies, compliances, audits, incidents, risks, and events
in a hierarchical JSON format.

It also provides AI-powered policy name similarity comparison between frameworks.

Usage:
    from framework_comparision import export_framework_data, compare_policy_names
    
    # Export framework
    result = export_framework_data(framework_id=1, output_file="framework_export.json")
    
    # Compare policy names between two framework JSONs
    comparison = compare_policy_names("framework1.json", "framework2.json")
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
from django.core.serializers.json import DjangoJSONEncoder

# Django setup (must happen BEFORE importing models)
import django
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Import Django models and settings AFTER setup
from django.conf import settings
from grc.models import (
    Framework, Policy, SubPolicy, Compliance, Audit, Incident, Risk, Event,
    PolicyVersion, FrameworkVersion, AuditFinding, AuditVersion, RiskInstance, 
    PolicyApproval, ComplianceApproval, FrameworkApproval
)


def calculate_text_similarity(text1, text2):
    """
    Calculate similarity between two text strings using SequenceMatcher.
    
    Args:
        text1 (str): First text
        text2 (str): Second text
    
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize: lowercase and strip whitespace
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    
    # Calculate similarity using SequenceMatcher
    similarity = SequenceMatcher(None, text1, text2).ratio()
    return similarity


def calculate_ai_similarity(text1, text2, use_ai=True):
    """
    Calculate similarity using AI model (Grok/OpenAI).
    Falls back to text similarity if AI is not available.
    
    Args:
        text1 (str): First text
        text2 (str): Second text
        use_ai (bool): Whether to use AI model
    
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    if not use_ai:
        return calculate_text_similarity(text1, text2)
    
    try:
        from openai import OpenAI
        
        # Use Grok if available, else OpenAI
        api_key = getattr(settings, 'GROK_API_KEY', None) or getattr(settings, 'OPENAI_API_KEY', None)
        model = getattr(settings, 'GROK_MODEL', None) or getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        base_url = getattr(settings, 'GROK_BASE_URL', None) if getattr(settings, 'GROK_API_KEY', None) else None
        
        if not api_key:
            print("[WARNING] No AI API key found, using text similarity")
            return calculate_text_similarity(text1, text2)
        
        # Initialize OpenAI client
        if base_url:
            client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            client = OpenAI(api_key=api_key)
        
        # Create prompt for AI similarity assessment
        prompt = f"""Compare these two policy names and rate their similarity on a scale of 0.0 to 1.0, where:
- 1.0 = identical or essentially the same policy
- 0.8-0.9 = very similar policies with minor differences
- 0.6-0.7 = similar policies with some differences
- 0.4-0.5 = related but different policies
- 0.0-0.3 = completely different policies

Policy 1: "{text1}"
Policy 2: "{text2}"

Respond with ONLY a number between 0.0 and 1.0, nothing else."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a policy analysis expert. Compare policy names and provide similarity scores."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        # Extract similarity score from response
        score_text = response.choices[0].message.content.strip()
        try:
            score = float(score_text)
            return max(0.0, min(1.0, score))  # Clamp between 0 and 1
        except ValueError:
            print(f"[WARNING] Could not parse AI score: {score_text}, using text similarity")
            return calculate_text_similarity(text1, text2)
            
    except Exception as e:
        print(f"[WARNING] AI similarity failed: {str(e)}, using text similarity")
        return calculate_text_similarity(text1, text2)


def compare_policy_names(json_file_1, json_file_2, output_file=None, use_ai=True, min_similarity=0.0):
    """
    Compare policy names between two framework JSON files using similarity scoring.
    
    Args:
        json_file_1 (str): Path to first framework JSON
        json_file_2 (str): Path to second framework JSON
        output_file (str, optional): Path to save comparison results
        use_ai (bool): Whether to use AI for similarity (default: True)
        min_similarity (float): Minimum similarity threshold to consider a match (default: 0.0)
    
    Returns:
        dict: Comparison results with matched and unmatched policies
    
    Example:
        >>> result = compare_policy_names("framework1.json", "framework2.json")
        >>> print(f"Found {len(result['matched_policies'])} similar policies")
    """
    try:
        print(f"[INFO] Comparing policy names between:")
        print(f"  - Framework 1: {json_file_1}")
        print(f"  - Framework 2: {json_file_2}")
        print(f"  - Using AI: {use_ai}")
        
        # Load JSON files
        with open(json_file_1, 'r', encoding='utf-8') as f:
            framework_1 = json.load(f)
        
        with open(json_file_2, 'r', encoding='utf-8') as f:
            framework_2 = json.load(f)
        
        # Extract policy names from both frameworks
        policies_1 = []
        policies_2 = []
        
        # Handle different JSON structures
        if "policies" in framework_1:
            policies_1 = [
                {
                    "id": p.get("PolicyId", idx),
                    "name": p.get("PolicyName", "Unknown Policy"),
                    "identifier": p.get("Identifier", ""),
                    "description": p.get("PolicyDescription", "")
                }
                for idx, p in enumerate(framework_1["policies"], 1)
            ]
        elif "framework" in framework_1:
            # Handle nested structure
            for section in framework_1.get("framework", {}).get("sections", []):
                for policy in section.get("policies", []):
                    policies_1.append({
                        "id": policy.get("policy_id", len(policies_1) + 1),
                        "name": policy.get("policy_name", "Unknown Policy"),
                        "identifier": policy.get("policy_identifier", ""),
                        "description": policy.get("policy_description", "")
                    })
        
        if "policies" in framework_2:
            policies_2 = [
                {
                    "id": p.get("PolicyId", idx),
                    "name": p.get("PolicyName", "Unknown Policy"),
                    "identifier": p.get("Identifier", ""),
                    "description": p.get("PolicyDescription", "")
                }
                for idx, p in enumerate(framework_2["policies"], 1)
            ]
        elif "framework" in framework_2:
            for section in framework_2.get("framework", {}).get("sections", []):
                for policy in section.get("policies", []):
                    policies_2.append({
                        "id": policy.get("policy_id", len(policies_2) + 1),
                        "name": policy.get("policy_name", "Unknown Policy"),
                        "identifier": policy.get("policy_identifier", ""),
                        "description": policy.get("policy_description", "")
                    })
        
        print(f"[INFO] Found {len(policies_1)} policies in framework 1")
        print(f"[INFO] Found {len(policies_2)} policies in framework 2")
        
        # Calculate similarity matrix
        print("[INFO] Calculating similarity scores...")
        matched_policies = []
        unmatched_policies_1 = []
        unmatched_policies_2 = set(range(len(policies_2)))  # Track unmatched indices
        
        for idx1, policy1 in enumerate(policies_1):
            best_match = None
            best_score = 0.0
            best_idx2 = -1
            
            for idx2, policy2 in enumerate(policies_2):
                # Calculate similarity score
                if use_ai:
                    score = calculate_ai_similarity(policy1["name"], policy2["name"], use_ai=True)
                else:
                    score = calculate_text_similarity(policy1["name"], policy2["name"])
                
                if score > best_score:
                    best_score = score
                    best_match = policy2
                    best_idx2 = idx2
            
            # Check if best match meets minimum similarity threshold
            if best_match and best_score >= min_similarity:
                matched_policies.append({
                    "framework_1_policy": policy1,
                    "framework_2_policy": best_match,
                    "similarity_score": round(best_score, 4),
                    "similarity_percentage": round(best_score * 100, 2)
                })
                # Mark this policy from framework 2 as matched
                if best_idx2 in unmatched_policies_2:
                    unmatched_policies_2.remove(best_idx2)
            else:
                unmatched_policies_1.append({
                    "policy": policy1,
                    "reason": f"No match found with similarity >= {min_similarity}"
                })
        
        # Add remaining unmatched policies from framework 2
        unmatched_policies_2_list = [
            {
                "policy": policies_2[idx],
                "reason": "No matching policy found in framework 1"
            }
            for idx in sorted(unmatched_policies_2)
        ]
        
        # Sort matched policies by similarity score (descending)
        matched_policies.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Create comparison result
        comparison_result = {
            "metadata": {
                "comparison_timestamp": datetime.now().isoformat(),
                "framework_1_file": json_file_1,
                "framework_2_file": json_file_2,
                "framework_1_name": framework_1.get("metadata", {}).get("framework_name", "Unknown"),
                "framework_2_name": framework_2.get("metadata", {}).get("framework_name", "Unknown"),
                "total_policies_framework_1": len(policies_1),
                "total_policies_framework_2": len(policies_2),
                "total_matched": len(matched_policies),
                "total_unmatched_framework_1": len(unmatched_policies_1),
                "total_unmatched_framework_2": len(unmatched_policies_2_list),
                "ai_enabled": use_ai,
                "min_similarity_threshold": min_similarity
            },
            "matched_policies": matched_policies,
            "unmatched_policies_framework_1": unmatched_policies_1,
            "unmatched_policies_framework_2": unmatched_policies_2_list,
            "summary": {
                "match_rate_framework_1": round(len(matched_policies) / len(policies_1) * 100, 2) if policies_1 else 0,
                "match_rate_framework_2": round(len(matched_policies) / len(policies_2) * 100, 2) if policies_2 else 0,
                "average_similarity": round(sum(m["similarity_score"] for m in matched_policies) / len(matched_policies), 4) if matched_policies else 0,
                "high_similarity_matches": len([m for m in matched_policies if m["similarity_score"] >= 0.8]),
                "medium_similarity_matches": len([m for m in matched_policies if 0.6 <= m["similarity_score"] < 0.8]),
                "low_similarity_matches": len([m for m in matched_policies if m["similarity_score"] < 0.6])
            }
        }
        
        # Save to JSON if output file specified
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"changeManagement/output/policy_comparison_{timestamp}.json"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comparison_result, f, ensure_ascii=False, indent=2)
        
        # Print summary
        print(f"\n[SUCCESS] Policy comparison complete!")
        print(f"[SUMMARY]")
        print(f"  - Matched policies: {len(matched_policies)}")
        print(f"  - Unmatched from framework 1: {len(unmatched_policies_1)}")
        print(f"  - Unmatched from framework 2: {len(unmatched_policies_2_list)}")
        print(f"  - Average similarity: {comparison_result['summary']['average_similarity']}")
        print(f"  - High similarity (≥80%): {comparison_result['summary']['high_similarity_matches']}")
        print(f"  - Medium similarity (60-79%): {comparison_result['summary']['medium_similarity_matches']}")
        print(f"  - Low similarity (<60%): {comparison_result['summary']['low_similarity_matches']}")
        print(f"  - Output saved to: {output_path}")
        
        return {
            "success": True,
            "output_file": str(output_path.resolve()),
            "comparison_result": comparison_result
        }
        
    except FileNotFoundError as e:
        error_msg = f"JSON file not found: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON format: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Error comparing policy names: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        print(traceback.format_exc())
        return {
            "success": False,
            "error": error_msg
        }


def serialize_model_instance(instance):
    """
    Convert a Django model instance to a dictionary.
    Handles ForeignKey relationships and special field types.
    """
    if instance is None:
        return None
    
    data = {}
    for field in instance._meta.get_fields():
        field_name = field.name
        
        # Skip reverse relations for now (we'll handle them explicitly)
        if field.one_to_many or field.many_to_many:
            continue
        
        try:
            value = getattr(instance, field_name, None)
            
            # Handle ForeignKey fields
            if field.many_to_one and value is not None:
                # Get the related object's primary key
                if hasattr(value, 'pk'):
                    data[field_name] = value.pk
                else:
                    data[field_name] = value
            # Handle date/datetime fields
            elif isinstance(value, (datetime,)):
                data[field_name] = value.isoformat() if value else None
            # Handle JSON fields
            elif isinstance(value, (dict, list)):
                data[field_name] = value
            # Handle other fields
            else:
                data[field_name] = value
        except Exception as e:
            # Skip fields that can't be accessed
            continue
    
    return data


def export_framework_data(framework_id, output_file=None, include_versions=True):
    """
    Export all data for a specific framework in hierarchical JSON format.
    
    Args:
        framework_id (int): The FrameworkId to export
        output_file (str, optional): Path to save JSON file. If None, auto-generates filename
        include_versions (bool): Whether to include version history (default: True)
    
    Returns:
        dict: The complete framework data structure
    
    Example:
        >>> result = export_framework_data(framework_id=1)
        >>> print(f"Exported {result['metadata']['total_policies']} policies")
    """
    try:
        # Fetch framework
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        print(f"[INFO] Exporting framework: {framework.FrameworkName} (ID: {framework_id})")
        
        # Initialize the hierarchical structure
        framework_data = {
            "metadata": {
                "framework_id": framework_id,
                "export_timestamp": datetime.now().isoformat(),
                "framework_name": framework.FrameworkName,
                "framework_version": framework.CurrentVersion,
            },
            "framework": serialize_model_instance(framework),
            "policies": [],
            "audits": [],
            "incidents": [],
            "risks": [],
            "events": []
        }
        
        # ========== POLICIES AND SUBPOLICIES ==========
        print("[INFO] Fetching policies and subpolicies...")
        policies = Policy.objects.filter(FrameworkId=framework_id)
        
        for policy in policies:
            policy_data = serialize_model_instance(policy)
            policy_data["subpolicies"] = []
            
            # Fetch subpolicies for this policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy.PolicyId)
            
            for subpolicy in subpolicies:
                subpolicy_data = serialize_model_instance(subpolicy)
                subpolicy_data["compliances"] = []
                
                # Fetch compliances for this subpolicy
                compliances = Compliance.objects.filter(SubPolicy=subpolicy.SubPolicyId)
                
                for compliance in compliances:
                    compliance_data = serialize_model_instance(compliance)
                    subpolicy_data["compliances"].append(compliance_data)
                
                policy_data["subpolicies"].append(subpolicy_data)
            
            # Add policy versions if requested
            if include_versions:
                policy_versions = PolicyVersion.objects.filter(PolicyId=policy.PolicyId)
                policy_data["versions"] = [
                    serialize_model_instance(version) for version in policy_versions
                ]
            
            framework_data["policies"].append(policy_data)
        
        framework_data["metadata"]["total_policies"] = len(framework_data["policies"])
        framework_data["metadata"]["total_subpolicies"] = sum(
            len(p["subpolicies"]) for p in framework_data["policies"]
        )
        framework_data["metadata"]["total_compliances"] = sum(
            len(sp["compliances"]) 
            for p in framework_data["policies"] 
            for sp in p["subpolicies"]
        )
        
        # ========== AUDITS ==========
        print("[INFO] Fetching audits...")
        audits = Audit.objects.filter(FrameworkId=framework_id)
        
        for audit in audits:
            audit_data = serialize_model_instance(audit)
            audit_data["findings"] = []
            
            # Fetch audit findings
            findings = AuditFinding.objects.filter(AuditId=audit.AuditId)
            for finding in findings:
                finding_data = serialize_model_instance(finding)
                audit_data["findings"].append(finding_data)
            
            # Add audit versions if requested
            if include_versions:
                try:
                    audit_versions = AuditVersion.objects.filter(AuditId=audit.AuditId)
                    audit_data["versions"] = [
                        serialize_model_instance(version) for version in audit_versions
                    ]
                except Exception:
                    # Some deployments have no primary key column on audit_version;
                    # skip versions gracefully if querying fails
                    audit_data["versions"] = []
            
            framework_data["audits"].append(audit_data)
        
        framework_data["metadata"]["total_audits"] = len(framework_data["audits"])
        framework_data["metadata"]["total_audit_findings"] = sum(
            len(a["findings"]) for a in framework_data["audits"]
        )
        
        # ========== INCIDENTS ==========
        print("[INFO] Fetching incidents...")
        incidents = Incident.objects.filter(FrameworkId=framework_id)
        
        for incident in incidents:
            incident_data = serialize_model_instance(incident)
            framework_data["incidents"].append(incident_data)
        
        framework_data["metadata"]["total_incidents"] = len(framework_data["incidents"])
        
        # ========== RISKS ==========
        print("[INFO] Fetching risks...")
        risks = Risk.objects.filter(FrameworkId=framework_id)
        
        for risk in risks:
            risk_data = serialize_model_instance(risk)
            
            # Fetch risk instances if any
            risk_instances = RiskInstance.objects.filter(
                RiskId=risk.RiskId,
                FrameworkId=framework_id
            )
            risk_data["instances"] = [
                serialize_model_instance(instance) for instance in risk_instances
            ]
            
            framework_data["risks"].append(risk_data)
        
        framework_data["metadata"]["total_risks"] = len(framework_data["risks"])
        framework_data["metadata"]["total_risk_instances"] = sum(
            len(r["instances"]) for r in framework_data["risks"]
        )
        
        # ========== EVENTS ==========
        print("[INFO] Fetching events...")
        events = Event.objects.filter(FrameworkId=framework_id)
        
        for event in events:
            event_data = serialize_model_instance(event)
            framework_data["events"].append(event_data)
        
        framework_data["metadata"]["total_events"] = len(framework_data["events"])
        
        # ========== APPROVALS ==========
        print("[INFO] Fetching approvals...")
        
        # Policy Approvals
        policy_approvals = PolicyApproval.objects.filter(FrameworkId=framework_id)
        framework_data["approvals"] = {
            "policy_approvals": [
                serialize_model_instance(approval) for approval in policy_approvals
            ],
            "compliance_approvals": [],
            "framework_approvals": []
        }
        
        # Compliance Approvals
        compliance_approvals = ComplianceApproval.objects.filter(FrameworkId=framework_id)
        framework_data["approvals"]["compliance_approvals"] = [
            serialize_model_instance(approval) for approval in compliance_approvals
        ]
        
        # Framework Approvals
        framework_approvals = FrameworkApproval.objects.filter(FrameworkId=framework_id)
        framework_data["approvals"]["framework_approvals"] = [
            serialize_model_instance(approval) for approval in framework_approvals
        ]
        
        framework_data["metadata"]["total_policy_approvals"] = len(
            framework_data["approvals"]["policy_approvals"]
        )
        framework_data["metadata"]["total_compliance_approvals"] = len(
            framework_data["approvals"]["compliance_approvals"]
        )
        framework_data["metadata"]["total_framework_approvals"] = len(
            framework_data["approvals"]["framework_approvals"]
        )
        
        # ========== SAVE TO JSON ==========
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(c for c in framework.FrameworkName if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')[:50]
            output_file = f"changeManagement/output/framework_{framework_id}_{safe_name}_{timestamp}.json"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(framework_data, f, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)
        
        print(f"[SUCCESS] Framework data exported to: {output_path}")
        print(f"[SUMMARY]")
        print(f"  - Policies: {framework_data['metadata']['total_policies']}")
        print(f"  - Subpolicies: {framework_data['metadata']['total_subpolicies']}")
        print(f"  - Compliances: {framework_data['metadata']['total_compliances']}")
        print(f"  - Audits: {framework_data['metadata']['total_audits']}")
        print(f"  - Incidents: {framework_data['metadata']['total_incidents']}")
        print(f"  - Risks: {framework_data['metadata']['total_risks']}")
        print(f"  - Events: {framework_data['metadata']['total_events']}")
        
        return {
            "success": True,
            "output_file": str(output_path.resolve()),
            "framework_data": framework_data,
            "metadata": framework_data["metadata"]
        }
        
    except Framework.DoesNotExist:
        error_msg = f"Framework with ID {framework_id} not found"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Error exporting framework data: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        print(traceback.format_exc())
        return {
            "success": False,
            "error": error_msg
        }


def compare_frameworks(framework_id_1, framework_id_2, output_file=None):
    """
    Compare two frameworks and generate a comparison report.
    
    Args:
        framework_id_1 (int): First framework ID
        framework_id_2 (int): Second framework ID
        output_file (str, optional): Path to save comparison JSON
    
    Returns:
        dict: Comparison data with differences and similarities
    """
    try:
        print(f"[INFO] Comparing frameworks {framework_id_1} and {framework_id_2}...")
        
        # Export both frameworks
        framework_1_data = export_framework_data(framework_id_1, include_versions=False)
        framework_2_data = export_framework_data(framework_id_2, include_versions=False)
        
        if not framework_1_data["success"] or not framework_2_data["success"]:
            return {
                "success": False,
                "error": "Failed to export one or both frameworks"
            }
        
        # Create comparison structure
        comparison = {
            "metadata": {
                "comparison_timestamp": datetime.now().isoformat(),
                "framework_1": {
                    "id": framework_id_1,
                    "name": framework_1_data["framework_data"]["framework"]["FrameworkName"],
                    "version": framework_1_data["framework_data"]["framework"]["CurrentVersion"]
                },
                "framework_2": {
                    "id": framework_id_2,
                    "name": framework_2_data["framework_data"]["framework"]["FrameworkName"],
                    "version": framework_2_data["framework_data"]["framework"]["CurrentVersion"]
                }
            },
            "statistics": {
                "framework_1": framework_1_data["metadata"],
                "framework_2": framework_2_data["metadata"],
                "differences": {
                    "policies": framework_1_data["metadata"]["total_policies"] - framework_2_data["metadata"]["total_policies"],
                    "subpolicies": framework_1_data["metadata"]["total_subpolicies"] - framework_2_data["metadata"]["total_subpolicies"],
                    "compliances": framework_1_data["metadata"]["total_compliances"] - framework_2_data["metadata"]["total_compliances"],
                    "audits": framework_1_data["metadata"]["total_audits"] - framework_2_data["metadata"]["total_audits"],
                    "incidents": framework_1_data["metadata"]["total_incidents"] - framework_2_data["metadata"]["total_incidents"],
                    "risks": framework_1_data["metadata"]["total_risks"] - framework_2_data["metadata"]["total_risks"],
                    "events": framework_1_data["metadata"]["total_events"] - framework_2_data["metadata"]["total_events"]
                }
            },
            "framework_1_data": framework_1_data["framework_data"],
            "framework_2_data": framework_2_data["framework_data"]
        }
        
        # Save comparison
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"changeManagement/output/framework_comparison_{framework_id_1}_vs_{framework_id_2}_{timestamp}.json"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder)
        
        print(f"[SUCCESS] Comparison saved to: {output_path}")
        
        return {
            "success": True,
            "output_file": str(output_path.resolve()),
            "comparison": comparison
        }
        
    except Exception as e:
        error_msg = f"Error comparing frameworks: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        print(traceback.format_exc())
        return {
            "success": False,
            "error": error_msg
        }


def list_all_frameworks():
    """
    List all available frameworks in the database.
    
    Returns:
        list: List of framework dictionaries with basic info
    """
    try:
        frameworks = Framework.objects.all().order_by('FrameworkName')
        
        framework_list = []
        for framework in frameworks:
            framework_list.append({
                "framework_id": framework.FrameworkId,
                "framework_name": framework.FrameworkName,
                "current_version": framework.CurrentVersion,
                "category": framework.Category,
                "status": framework.Status,
                "active_inactive": framework.ActiveInactive
            })
        
        return {
            "success": True,
            "total_frameworks": len(framework_list),
            "frameworks": framework_list
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "frameworks": []
        }


def main():
    """CLI entry point for framework export and comparison"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Export Framework Data and Compare Policy Names",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Export a single framework:
    python framework_comparision.py --framework-id 1
  
  Export with custom output file:
    python framework_comparision.py --framework-id 1 --output custom_export.json
  
  Compare two frameworks:
    python framework_comparision.py --compare 1 2
  
  Compare policy names in two JSON files:
    python framework_comparision.py --compare-policies framework1.json framework2.json
  
  Compare with AI similarity:
    python framework_comparision.py --compare-policies framework1.json framework2.json --use-ai
  
  List all frameworks:
    python framework_comparision.py --list
        """
    )
    
    parser.add_argument(
        '--framework-id',
        type=int,
        help='Framework ID to export'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file path (optional)'
    )
    parser.add_argument(
        '--compare',
        nargs=2,
        type=int,
        metavar=('ID1', 'ID2'),
        help='Compare two frameworks by their IDs'
    )
    parser.add_argument(
        '--compare-policies',
        nargs=2,
        type=str,
        metavar=('JSON1', 'JSON2'),
        help='Compare policy names between two JSON files'
    )
    parser.add_argument(
        '--use-ai',
        action='store_true',
        help='Use AI for policy name similarity (requires API key)'
    )
    parser.add_argument(
        '--min-similarity',
        type=float,
        default=0.0,
        help='Minimum similarity threshold (0.0-1.0) for matching policies'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available frameworks'
    )
    parser.add_argument(
        '--no-versions',
        action='store_true',
        help='Exclude version history from export'
    )
    
    args = parser.parse_args()
    
    if args.list:
        result = list_all_frameworks()
        if result["success"]:
            print(f"\nFound {result['total_frameworks']} frameworks:\n")
            for fw in result["frameworks"]:
                print(f"  ID: {fw['framework_id']:3d} | {fw['framework_name']:50s} | v{fw['current_version']}")
        else:
            print(f"Error: {result.get('error')}")
        return 0
    
    if args.compare_policies:
        result = compare_policy_names(
            args.compare_policies[0],
            args.compare_policies[1],
            output_file=args.output,
            use_ai=args.use_ai,
            min_similarity=args.min_similarity
        )
        if result["success"]:
            print(f"\n✓ Policy comparison complete! Output: {result['output_file']}")
            return 0
        else:
            print(f"\n✗ Failed: {result.get('error')}")
            return 1
    
    if args.compare:
        result = compare_frameworks(args.compare[0], args.compare[1], args.output)
        if result["success"]:
            print(f"\n✓ Comparison complete! Output: {result['output_file']}")
            return 0
        else:
            print(f"\n✗ Failed: {result.get('error')}")
            return 1
    
    if args.framework_id:
        result = export_framework_data(
            framework_id=args.framework_id,
            output_file=args.output,
            include_versions=not args.no_versions
        )
        if result["success"]:
            print(f"\n✓ Export complete! Output: {result['output_file']}")
            return 0
        else:
            print(f"\n✗ Failed: {result.get('error')}")
            return 1
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
