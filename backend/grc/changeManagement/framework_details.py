#!/usr/bin/env python3
"""
Framework Comparison and Export Module

This module provides functionality to export complete framework data
including policies, subpolicies, compliances, audits, incidents, risks, and events
in a hierarchical JSON format.

Usage:
    from framework_comparision import export_framework_data
    
    result = export_framework_data(framework_id=1, output_file="framework_export.json")
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder

# Django setup (must happen BEFORE importing models)
import django
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Import Django models AFTER setup
from grc.models import (
    Framework, Policy, SubPolicy, Compliance, Audit, Incident, Risk, Event,
    PolicyVersion, FrameworkVersion, AuditFinding, AuditVersion, RiskInstance, 
    PolicyApproval, ComplianceApproval, FrameworkApproval
)


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
    """CLI entry point for framework export"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Export Framework Data to JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Export a single framework:
    python framework_comparision.py --framework-id 1
  
  Export with custom output file:
    python framework_comparision.py --framework-id 1 --output custom_export.json
  
  Compare two frameworks:
    python framework_comparision.py --compare 1 2
  
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

