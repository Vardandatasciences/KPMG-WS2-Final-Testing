"""
Dynamic Homepage API
Provides aggregated, framework-aware data for the home page dashboard
"""
import threading
from django.http import JsonResponse
from django.db.models import Q, Count, Avg, F, Sum, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from grc.models import (
    Framework, Policy, SubPolicy, Compliance, Risk, RiskInstance,
    Incident, Audit, AuditFinding, PolicyApproval, ComplianceApproval,
    PolicyCategory, Users
)
from ..changemanagement.login_framework_checking import auto_check_all_frameworks
from rest_framework.request import Request
from ...debug_utils import debug_print


def get_homepage_data(request):
    """
    GET /api/homepage?frameworkId=<id>
    Returns comprehensive homepage payload with:
    - Framework info
    - Hero stats and preview metrics
    - Policy donut data with counts/percentages
    - Domain compliance metrics
    - Module-specific KPIs (Policy, Compliance, Risk, Incident, Audit)
    """
    # NOTE: Auto framework check on login/homepage load has been disabled.
    # If you want to re-enable it, restore the background thread that calls
    # auto_check_all_frameworks here.
    # debug_print("🚀 [Homepage] Auto framework check is currently DISABLED")
    
    debug_print("=" * 80)
    debug_print("🏠 BACKEND: get_homepage_data() CALLED")
    debug_print("=" * 80)
    debug_print(f"📥 Request Method: {request.method}")
    debug_print(f"📥 Request Path: {request.path}")
    debug_print(f"📥 Full Query String: {request.GET.urlencode()}")
    
    try:
        # Get framework from query params or session
        framework_id = request.GET.get('frameworkId')
        debug_print(f"📥 Request GET params - frameworkId: {framework_id}")
        debug_print(f"📥 Request session keys: {list(request.session.keys())}")
        
        if not framework_id:
            # Try to get from session
            framework_id = request.session.get('selected_framework_id')
            debug_print(f"📥 Framework ID from session: {framework_id}")
        
        # Build framework filter
        framework_filter = Q()
        selected_framework = None
        
        if framework_id:
            try:
                framework_id = int(framework_id)
                selected_framework = Framework.objects.filter(FrameworkId=framework_id).first()
                framework_filter = Q(FrameworkId=framework_id)
                debug_print(f"✅ Framework found: ID={framework_id}, Name={selected_framework.FrameworkName if selected_framework else 'None'}")
            except (ValueError, TypeError):
                debug_print(f"⚠️ Invalid framework_id format: {framework_id}")
                pass
        
        # If no framework selected, use first active framework or all data
        if not selected_framework:
            selected_framework = Framework.objects.filter(
                Status='Approved',
                ActiveInactive='Active'
            ).first()
            if selected_framework:
                framework_id = selected_framework.FrameworkId
                framework_filter = Q(FrameworkId=framework_id)
                debug_print(f"🔄 Using default framework: ID={framework_id}, Name={selected_framework.FrameworkName}")
            else:
                debug_print("⚠️ No framework selected and no default framework found - using all data")
        
        # ====================================================================
        # FRAMEWORK INFO
        # ====================================================================
        framework_info = {
            'id': selected_framework.FrameworkId if selected_framework else None,
            'name': selected_framework.FrameworkName if selected_framework else 'All Frameworks',
            'description': selected_framework.FrameworkDescription if selected_framework else 'Unified GRC Platform',
            'category': selected_framework.Category if selected_framework else 'Compliance',
        }
        
        # ====================================================================
        # POLICY DONUT DATA CALCULATION
        # ====================================================================
        # 
        # CALCULATION LOGIC:
        # 1. Filter policies by selected framework (if any)
        # 2. Filter to only ACTIVE policies (ActiveInactive='Active')
        # 3. Count total active policies (denominator for percentages)
        # 4. Categorize by status:
        #    - APPLIED: Status='Approved' AND ActiveInactive='Active'
        #    - IN PROGRESS: Status='Under Review' AND ActiveInactive='Active'
        #    - PENDING: Status IN ('Draft', 'Pending') AND ActiveInactive='Active'
        # 5. Calculate percentage: (Category Count / Total Active) × 100
        #
        # ====================================================================
        debug_print("")
        debug_print("📊 ========================================")
        debug_print("📊 FETCHING POLICY DONUT DATA")
        debug_print("📊 ========================================")
        
        # Step 1: Get policies filtered by framework
        debug_print("")
        debug_print("🔍 ========================================")
        debug_print("🔍 FILTERING POLICIES BY FRAMEWORK")
        debug_print("🔍 ========================================")
        debug_print(f"📊 Framework ID: {framework_id}")
        debug_print(f"📊 Framework Filter Applied: {bool(framework_filter)}")
        if selected_framework:
            debug_print(f"📊 Selected Framework Name: {selected_framework.FrameworkName}")
        
        policies_qs = Policy.objects.filter(framework_filter) if framework_filter else Policy.objects.all()
        
        # Step 2: Count total policies (all statuses)
        total_policies_all = policies_qs.count()
        debug_print(f"📊 Total Policies (before active filter): {total_policies_all}")
        
        # Step 3: Filter to only active policies for accurate counting
        # IMPORTANT: Only policies with ActiveInactive='Active' are counted
        # Inactive/Deleted policies are excluded from all calculations
        active_policies_qs = policies_qs.filter(ActiveInactive='Active')
        
        # Step 4: Count total active policies (this is the denominator for percentages)
        total_policies = active_policies_qs.count()
        
        # Step 5: Count inactive policies
        inactive_policies = total_policies_all - total_policies
        debug_print(f"📊 Total policies (all): {total_policies_all}")
        debug_print(f"📊 Total ACTIVE policies queried: {total_policies}")
        debug_print(f"📊 Total INACTIVE policies: {inactive_policies}")
        
        # Step 6: Count policies by status (only active policies)
        # APPLIED: Policies with Status='Approved' (approved and implemented)
        applied = active_policies_qs.filter(Status='Approved').count()
        
        # IN PROGRESS: Policies with Status='Under Review' (currently being reviewed)
        in_progress = active_policies_qs.filter(Status='Under Review').count()
        
        # PENDING: Policies with Status='Draft' or 'Pending' (not yet submitted for review)
        pending = active_policies_qs.filter(Status__in=['Draft', 'Pending']).count()
        
        # REJECTED: Policies with Status='Rejected' (rejected during review)
        rejected = active_policies_qs.filter(Status='Rejected').count()
        
        debug_print(f"📊 Applied (Status='Approved' + Active): {applied}")
        debug_print(f"📊 In Progress (Status='Under Review' + Active): {in_progress}")
        debug_print(f"📊 Pending (Status IN ['Draft','Pending'] + Active): {pending}")
        debug_print(f"📊 Rejected (Status='Rejected' + Active): {rejected}")
        
        # Step 7: Calculate percentages
        # Formula: (Category Count / Total Active Policies) × 100
        applied_pct = round((applied / total_policies * 100), 1) if total_policies > 0 else 0
        in_progress_pct = round((in_progress / total_policies * 100), 1) if total_policies > 0 else 0
        pending_pct = round((pending / total_policies * 100), 1) if total_policies > 0 else 0
        rejected_pct = round((rejected / total_policies * 100), 1) if total_policies > 0 else 0
        
        debug_print(f"📊 Calculated Percentages:")
        debug_print(f"   Applied: {applied_pct}% = ({applied}/{total_policies}) × 100")
        debug_print(f"   In Progress: {in_progress_pct}% = ({in_progress}/{total_policies}) × 100")
        debug_print(f"   Pending: {pending_pct}% = ({pending}/{total_policies}) × 100")
        debug_print(f"   Rejected: {rejected_pct}% = ({rejected}/{total_policies}) × 100")
        
        debug_print(f"📊 Percentages - Applied: {applied_pct}%, In Progress: {in_progress_pct}%, Pending: {pending_pct}%, Rejected: {rejected_pct}%")
        
        # Get policy lists for popup - Return ALL policies (not limited)
        # This ensures all policies from database are shown in the popup
        debug_print("")
        debug_print("📋 Fetching policy details for popup...")
        debug_print(f"📋 Will return ALL policies matching each status (no limit)")
        
        # Helper function to add compliance counts to policy list
        def add_compliance_counts_to_policies(policy_list, framework_id=None):
            """Add compliance counts (total and compliant) to each policy"""
            for policy in policy_list:
                policy_id = policy['PolicyId']
                
                # Get all compliances for this policy through SubPolicies
                # Compliance -> SubPolicy -> Policy
                # Use SubPolicy to filter Compliances by PolicyId
                compliance_filter = Q(SubPolicy__PolicyId=policy_id)
                if framework_id:
                    compliance_filter &= Q(FrameworkId=framework_id)
                
                total_compliances = Compliance.objects.filter(
                    compliance_filter
                ).count()
                
                # Compliant compliances: Those with AuditFinding Check='2' (Fully Compliant)
                # Query AuditFinding directly for better accuracy
                # Filter by PolicyId through Compliance -> SubPolicy -> Policy
                # And filter by FrameworkId to ensure correct framework
                compliant_filter = Q(
                    ComplianceId__SubPolicy__PolicyId=policy_id,
                    Check='2'  # Fully Compliant/Completed
                )
                if framework_id:
                    compliant_filter &= Q(FrameworkId=framework_id)
                
                # Count distinct compliances that have audit findings with Check='2'
                compliant_compliances = AuditFinding.objects.filter(
                    compliant_filter
                ).values('ComplianceId').distinct().count()
                
                policy['totalCompliances'] = total_compliances
                policy['implementedCompliances'] = compliant_compliances
            
            return policy_list
        
        applied_policies_qs = active_policies_qs.filter(
            Status='Approved'
        ).values('PolicyId', 'PolicyName', 'Status').order_by('PolicyName')
        
        applied_policies = list(applied_policies_qs)
        applied_policies = add_compliance_counts_to_policies(applied_policies, framework_id)
        debug_print(f"📋 Applied policies fetched from DB: {len(applied_policies)}")
        debug_print(f"📋 Applied policies expected count: {applied}")
        if applied_policies:
            debug_print(f"📋 Sample applied policy: {applied_policies[0]}")
            debug_print(f"📋 All applied policy IDs: {[p['PolicyId'] for p in applied_policies]}")
            # Print compliance data for first few policies
            debug_print("")
            debug_print("📊 COMPLIANCE DATA FOR APPLIED POLICIES:")
            for i, policy in enumerate(applied_policies[:5]):  # Show first 5
                debug_print(f"   Policy {i+1}: {policy.get('PolicyName', 'N/A')}")
                debug_print(f"      - Total Compliances (Controls): {policy.get('totalCompliances', 0)}")
                debug_print(f"      - Compliant Compliances (Implemented): {policy.get('implementedCompliances', 0)}")
            if len(applied_policies) > 5:
                debug_print(f"   ... and {len(applied_policies) - 5} more policies")
            debug_print("")
        
        in_progress_policies_qs = active_policies_qs.filter(
            Status='Under Review'
        ).values('PolicyId', 'PolicyName', 'Status').order_by('PolicyName')
        
        in_progress_policies = list(in_progress_policies_qs)
        in_progress_policies = add_compliance_counts_to_policies(in_progress_policies, framework_id)
        debug_print(f"📋 In Progress policies fetched from DB: {len(in_progress_policies)}")
        debug_print(f"📋 In Progress policies expected count: {in_progress}")
        if in_progress_policies:
            debug_print(f"📋 Sample in_progress policy: {in_progress_policies[0]}")
            debug_print(f"📋 All in_progress policy IDs: {[p['PolicyId'] for p in in_progress_policies]}")
        
        pending_policies_qs = active_policies_qs.filter(
            Status__in=['Draft', 'Pending']
        ).values('PolicyId', 'PolicyName', 'Status').order_by('PolicyName')
        
        pending_policies = list(pending_policies_qs)
        pending_policies = add_compliance_counts_to_policies(pending_policies, framework_id)
        debug_print(f"📋 Pending policies fetched from DB: {len(pending_policies)}")
        debug_print(f"📋 Pending policies expected count: {pending}")
        if pending_policies:
            debug_print(f"📋 Sample pending policy: {pending_policies[0]}")
            debug_print(f"📋 All pending policy IDs: {[p['PolicyId'] for p in pending_policies]}")
        
        rejected_policies_qs = active_policies_qs.filter(
            Status='Rejected'
        ).values('PolicyId', 'PolicyName', 'Status').order_by('PolicyName')
        
        rejected_policies = list(rejected_policies_qs)
        rejected_policies = add_compliance_counts_to_policies(rejected_policies, framework_id)
        debug_print(f"📋 Rejected policies fetched from DB: {len(rejected_policies)}")
        debug_print(f"📋 Rejected policies expected count: {rejected}")
        if rejected_policies:
            debug_print(f"📋 Sample rejected policy: {rejected_policies[0]}")
            debug_print(f"📋 All rejected policy IDs: {[p['PolicyId'] for p in rejected_policies]}")
        
        # Verify counts match
        if len(applied_policies) != applied:
            debug_print(f"⚠️ WARNING: Applied policies count mismatch! DB count: {applied}, Returned: {len(applied_policies)}")
        if len(in_progress_policies) != in_progress:
            debug_print(f"⚠️ WARNING: In Progress policies count mismatch! DB count: {in_progress}, Returned: {len(in_progress_policies)}")
        if len(pending_policies) != pending:
            debug_print(f"⚠️ WARNING: Pending policies count mismatch! DB count: {pending}, Returned: {len(pending_policies)}")
        if len(rejected_policies) != rejected:
            debug_print(f"⚠️ WARNING: Rejected policies count mismatch! DB count: {rejected}, Returned: {len(rejected_policies)}")
        
        policies_data = {
            'total': total_policies,
            'totalAll': total_policies_all,  # Include all policies (active + inactive)
            'active': total_policies,
            'inactive': inactive_policies,
            'applied': {
                'count': applied,
                'percentage': applied_pct,
                'policies': applied_policies
            },
            'in_progress': {
                'count': in_progress,
                'percentage': in_progress_pct,
                'policies': in_progress_policies
            },
            'pending': {
                'count': pending,
                'percentage': pending_pct,
                'policies': pending_policies
            },
            'rejected': {
                'count': rejected,
                'percentage': rejected_pct,
                'policies': rejected_policies
            }
        }
        
        debug_print("")
        debug_print("✅ POLICY DATA STRUCTURE:")
        debug_print(f"   Total: {policies_data['total']}")
        debug_print(f"   Applied - Count: {policies_data['applied']['count']}, Percentage: {policies_data['applied']['percentage']}%, Policies: {len(policies_data['applied']['policies'])}")
        debug_print(f"   In Progress - Count: {policies_data['in_progress']['count']}, Percentage: {policies_data['in_progress']['percentage']}%, Policies: {len(policies_data['in_progress']['policies'])}")
        debug_print(f"   Pending - Count: {policies_data['pending']['count']}, Percentage: {policies_data['pending']['percentage']}%, Policies: {len(policies_data['pending']['policies'])}")
        debug_print(f"   Rejected - Count: {policies_data['rejected']['count']}, Percentage: {policies_data['rejected']['percentage']}%, Policies: {len(policies_data['rejected']['policies'])}")
        debug_print("")
        debug_print("📊 COMPLIANCE DATA SUMMARY:")
        total_compliances_all_policies = sum(p.get('totalCompliances', 0) for p in policies_data['applied']['policies'])
        compliant_compliances_all_policies = sum(p.get('implementedCompliances', 0) for p in policies_data['applied']['policies'])
        debug_print(f"   Total Compliances (Controls) across all Applied Policies: {total_compliances_all_policies}")
        debug_print(f"   Compliant Compliances (Implemented) across all Applied Policies: {compliant_compliances_all_policies}")
        if total_compliances_all_policies > 0:
            overall_compliant_pct = round((compliant_compliances_all_policies / total_compliances_all_policies) * 100, 1)
            debug_print(f"   Overall Compliance Percentage: {overall_compliant_pct}%")
        debug_print("📊 ========================================")
        debug_print("")
        
        # ====================================================================
        # MODULE METRICS - POLICY
        # ====================================================================
        active_policies = active_policies_qs.filter(Status='Approved').count()
        
        # Approval rate from PolicyApproval
        policy_approvals = PolicyApproval.objects.filter(
            PolicyId__FrameworkId=framework_id
        ) if framework_id else PolicyApproval.objects.all()
        
        total_approvals = policy_approvals.count()
        approved_count = policy_approvals.filter(ApprovedNot=True).count()
        approval_rate = round((approved_count / total_approvals * 100), 1) if total_approvals > 0 else 0
        
        # Average approval time (in days)
        recent_approvals = policy_approvals.filter(
            ApprovedNot=True,
            ApprovedDate__isnull=False
        ).order_by('-ApprovedDate')[:50]
        
        avg_approval_time = 0
        if recent_approvals.exists():
            # This is a simplified calculation - in real scenario you'd track submission date
            avg_approval_time = 7  # Placeholder - would calculate from actual submission dates
        
        policy_metrics = {
            'activePolicies': active_policies,
            'approvalRate': approval_rate,
            'totalPolicies': total_policies,
            'avgApprovalTime': avg_approval_time
        }
        
        # ====================================================================
        # MODULE METRICS - COMPLIANCE
        # ====================================================================
        compliances_qs = Compliance.objects.filter(framework_filter) if framework_filter else Compliance.objects.all()
        
        # Count total compliances (all statuses)
        total_compliances_all = compliances_qs.count()
        
        # Count active compliances
        active_compliances = compliances_qs.filter(
            Status='Approved',
            ActiveInactive='Active'
        ).count()
        
        # Count inactive compliances
        inactive_compliances = compliances_qs.filter(ActiveInactive='Inactive').count()
        
        # Compliance approval rate
        compliance_approvals = ComplianceApproval.objects.filter(
            FrameworkId=framework_id
        ) if framework_id else ComplianceApproval.objects.all()
        
        total_comp_approvals = compliance_approvals.count()
        approved_comp_count = compliance_approvals.filter(ApprovedNot=True).count()
        compliance_approval_rate = round((approved_comp_count / total_comp_approvals * 100), 1) if total_comp_approvals > 0 else 0
        
        total_findings = compliances_qs.count()
        under_review = compliances_qs.filter(Status='Under Review').count()
        
        compliance_metrics = {
            'activeCompliances': active_compliances,
            'inactiveCompliances': inactive_compliances,
            'totalCompliances': total_compliances_all,
            'approvalRate': compliance_approval_rate,
            'totalFindings': total_findings,
            'underReview': under_review
        }
        
        # ====================================================================
        # MODULE METRICS - RISK
        # ====================================================================
        risk_instances_qs = RiskInstance.objects.filter(framework_filter) if framework_filter else RiskInstance.objects.all()
        
        total_risks = risk_instances_qs.count()
        accepted_risks = risk_instances_qs.filter(
            RiskStatus='Approved'
        ).count()
        
        mitigated_risks = risk_instances_qs.filter(
            MitigationStatus='Completed'
        ).count()
        
        in_progress_risks = risk_instances_qs.filter(
            MitigationStatus='Work In Progress'
        ).count()
        
        # Count active vs inactive risks (if ActiveInactive field exists)
        active_risks = risk_instances_qs.filter(ActiveInactive='Active').count() if hasattr(RiskInstance, 'ActiveInactive') else total_risks
        inactive_risks = total_risks - active_risks if hasattr(RiskInstance, 'ActiveInactive') else 0
        
        risk_metrics = {
            'totalRisks': total_risks,
            'total': total_risks,  # Keep for backward compatibility
            'active': active_risks,
            'inactive': inactive_risks,
            'acceptedRisks': accepted_risks,
            'accepted': accepted_risks,  # Keep for backward compatibility
            'mitigatedRisks': mitigated_risks,
            'mitigated': mitigated_risks,  # Keep for backward compatibility
            'inProgressRisks': in_progress_risks,
            'inProgress': in_progress_risks  # Keep for backward compatibility
        }
        
        # ====================================================================
        # MODULE METRICS - INCIDENT
        # ====================================================================
        incidents_qs = Incident.objects.filter(framework_filter) if framework_filter else Incident.objects.all()
        
        total_incidents = incidents_qs.count()
        
        # Count active vs inactive incidents (if ActiveInactive field exists)
        active_incidents = incidents_qs.filter(ActiveInactive='Active').count() if hasattr(Incident, 'ActiveInactive') else total_incidents
        inactive_incidents = total_incidents - active_incidents if hasattr(Incident, 'ActiveInactive') else 0
        
        # Calculate MTTD (Mean Time To Detect) - simplified
        mttd = 0
        incidents_with_detection = incidents_qs.filter(
            IdentifiedAt__isnull=False,
            Date__isnull=False
        )
        if incidents_with_detection.exists():
            # In real scenario, you'd have a reported_at field
            mttd = 24  # Placeholder hours
        
        # Calculate MTTR (Mean Time To Resolve)
        mttr = 0
        resolved_incidents = incidents_qs.filter(
            Status='Completed',
            MitigationCompletedDate__isnull=False
        )
        if resolved_incidents.exists():
            # Calculate average resolution time
            mttr = 72  # Placeholder hours
        
        # Closure rate
        completed_incidents = incidents_qs.filter(Status='Completed').count()
        closure_rate = round((completed_incidents / total_incidents * 100), 1) if total_incidents > 0 else 0
        
        incident_metrics = {
            'totalIncidents': total_incidents,
            'total': total_incidents,  # Keep for backward compatibility
            'active': active_incidents,
            'inactive': inactive_incidents,
            'resolved': completed_incidents,
            'mttd': mttd,
            'mttr': mttr,
            'closureRate': closure_rate
        }
        
        # ====================================================================
        # MODULE METRICS - AUDIT
        # ====================================================================
        audits_qs = Audit.objects.filter(framework_filter) if framework_filter else Audit.objects.all()
        
        total_audits = audits_qs.count()
        completed_audits = audits_qs.filter(Status='Completed').count()
        open_audits = audits_qs.exclude(Status__in=['Completed', 'Cancelled']).count()
        
        # Count active vs inactive audits (if ActiveInactive field exists)
        active_audits = audits_qs.filter(ActiveInactive='Active').count() if hasattr(Audit, 'ActiveInactive') else total_audits
        inactive_audits = total_audits - active_audits if hasattr(Audit, 'ActiveInactive') else 0
        
        completion_rate = round((completed_audits / total_audits * 100), 1) if total_audits > 0 else 0
        
        audit_metrics = {
            'completionRate': completion_rate,
            'totalAudits': total_audits,
            'active': active_audits,
            'inactive': inactive_audits,
            'openAudits': open_audits,
            'completedAudits': completed_audits
        }
        
        # ====================================================================
        # HERO STATS
        # ====================================================================
        # Calculate compliant compliances (based on audit findings with Check='2')
        compliant_compliances = AuditFinding.objects.filter(
            framework_filter,
            Check='2'  # Completed = Compliant
        ).values('ComplianceId').distinct().count()
        
        hero_stats = {
            'totalPolicies': total_policies,
            'totalPoliciesAll': total_policies_all,  # All policies (active + inactive)
            'activePolicies': active_policies,
            'inactivePolicies': inactive_policies,
            'totalCompliances': total_findings,
            'totalCompliancesAll': total_compliances_all,  # All compliances (active + inactive)
            'activeCompliances': active_compliances,
            'inactiveCompliances': inactive_compliances,
            'compliantCompliances': compliant_compliances,  # NEW: Compliant controls count (based on audit findings)
            'totalRisks': total_risks,
            'activeRisks': active_risks,
            'inactiveRisks': inactive_risks,
            'mitigatedRisks': mitigated_risks,
            'totalIncidents': total_incidents,
            'activeIncidents': active_incidents,
            'inactiveIncidents': inactive_incidents,
            'resolvedIncidents': completed_incidents,
            'totalAudits': total_audits,
            'activeAudits': active_audits,
            'inactiveAudits': inactive_audits,
            'completedAudits': completed_audits
        }
        
        # ====================================================================
        # PREVIEW METRICS (for hero card)
        # ====================================================================
        # Calculate compliance percentage
        total_controls = compliances_qs.count()
        implemented_controls = compliances_qs.filter(
            Status='Approved',
            ActiveInactive='Active'
        ).count()
        compliance_percentage = round((implemented_controls / total_controls * 100), 1) if total_controls > 0 else 0
        
        # Remaining controls to implement
        remaining_controls = total_controls - implemented_controls
        
        # Next audit due
        next_audit = audits_qs.filter(
            DueDate__gte=timezone.now().date(),
            Status__in=['Assigned', 'In Progress']
        ).order_by('DueDate').first()
        
        next_audit_date = next_audit.DueDate.strftime('%Y-%m-%d') if next_audit else None
        
        preview_metrics = {
            'compliancePercentage': compliance_percentage,
            'remainingControls': remaining_controls,
            'nextAudit': next_audit_date,
            'policiesLabel': 'Active Policies',
            'policiesValue': active_policies
        }
        
        # ====================================================================
        # BUILD RESPONSE
        # ====================================================================
        debug_print("")
        debug_print("📦 ========================================")
        debug_print("📦 BUILDING RESPONSE")
        debug_print("📦 ========================================")
        
        response_data = {
            'success': True,
            'framework': framework_info,
            'hero': {
                'stats': hero_stats,
                'previewMetrics': preview_metrics
            },
            'policies': policies_data,
            'moduleMetrics': {
                'policy': policy_metrics,
                'compliance': compliance_metrics,
                'risk': risk_metrics,
                'incident': incident_metrics,
                'audit': audit_metrics
            },
            'timestamp': timezone.now().isoformat()
        }
        
        debug_print(f"✅ Response structure - Success: {response_data['success']}")
        debug_print(f"✅ Framework: {response_data['framework']['name']} (ID: {response_data['framework']['id']})")
        debug_print("")
        debug_print("📊 ========================================")
        debug_print("📊 FRAMEWORK STATUS BREAKDOWN")
        debug_print("📊 ========================================")
        debug_print(f"📋 POLICIES:")
        debug_print(f"   Total (All): {response_data['hero']['stats']['totalPoliciesAll']}")
        debug_print(f"   Active: {response_data['hero']['stats']['activePolicies']}")
        debug_print(f"   Inactive: {response_data['hero']['stats']['inactivePolicies']}")
        debug_print(f"   Applied: {len(response_data['policies']['applied']['policies'])} policies")
        debug_print(f"   In Progress: {len(response_data['policies']['in_progress']['policies'])} policies")
        debug_print(f"   Pending: {len(response_data['policies']['pending']['policies'])} policies")
        debug_print(f"   Rejected: {len(response_data['policies']['rejected']['policies'])} policies")
        debug_print("")
        debug_print(f"✅ COMPLIANCES:")
        debug_print(f"   Total (All): {response_data['hero']['stats']['totalCompliancesAll']}")
        debug_print(f"   Active: {response_data['hero']['stats']['activeCompliances']}")
        debug_print(f"   Inactive: {response_data['hero']['stats']['inactiveCompliances']}")
        debug_print("")
        debug_print("📊 ========================================")
        debug_print("📊 COMPLIANCE DATA IN FULL RESPONSE")
        debug_print("📊 ========================================")
        debug_print("📋 Applied Policies with Compliance Data:")
        applied_with_compliance = response_data['policies']['applied']['policies']
        for i, policy in enumerate(applied_with_compliance[:10]):  # Show first 10
            debug_print(f"   {i+1}. {policy.get('PolicyName', 'N/A')} (ID: {policy.get('PolicyId', 'N/A')})")
            debug_print(f"      - Total Compliances (Controls): {policy.get('totalCompliances', 0)}")
            debug_print(f"      - Compliant Compliances (Implemented): {policy.get('implementedCompliances', 0)}")
            if policy.get('totalCompliances', 0) > 0:
                compliant_pct = round((policy.get('implementedCompliances', 0) / policy.get('totalCompliances', 0)) * 100, 1)
                debug_print(f"      - Compliance %: {compliant_pct}%")
        if len(applied_with_compliance) > 10:
            debug_print(f"   ... and {len(applied_with_compliance) - 10} more policies with compliance data")
        debug_print("")
        debug_print("📊 Full Response includes compliance data in:")
        debug_print("   - response.policies.applied.policies[*].totalCompliances")
        debug_print("   - response.policies.applied.policies[*].implementedCompliances")
        debug_print("   - response.policies.in_progress.policies[*].totalCompliances")
        debug_print("   - response.policies.in_progress.policies[*].implementedCompliances")
        debug_print("   - response.policies.pending.policies[*].totalCompliances")
        debug_print("   - response.policies.pending.policies[*].implementedCompliances")
        debug_print("   - response.policies.rejected.policies[*].totalCompliances")
        debug_print("   - response.policies.rejected.policies[*].implementedCompliances")
        debug_print("")
        debug_print("📊 ========================================")
        debug_print("📊 MODULE METRICS DATA IN FULL RESPONSE")
        debug_print("📊 ========================================")
        debug_print("📋 Policy Metrics:")
        debug_print(f"   - Active Policies: {response_data['moduleMetrics']['policy']['activePolicies']}")
        debug_print(f"   - Total Policies: {response_data['moduleMetrics']['policy']['totalPolicies']}")
        debug_print(f"   - Approval Rate: {response_data['moduleMetrics']['policy']['approvalRate']}%")
        debug_print(f"   - Avg. Approval Time: {response_data['moduleMetrics']['policy']['avgApprovalTime']} days")
        debug_print("")
        debug_print("📋 Compliance Metrics:")
        debug_print(f"   - Active Compliances: {response_data['moduleMetrics']['compliance']['activeCompliances']}")
        debug_print(f"   - Total Compliances: {response_data['moduleMetrics']['compliance']['totalCompliances']}")
        debug_print(f"   - Total Findings: {response_data['moduleMetrics']['compliance']['totalFindings']}")
        debug_print(f"   - Approval Rate: {response_data['moduleMetrics']['compliance']['approvalRate']}%")
        debug_print(f"   - Under Review: {response_data['moduleMetrics']['compliance']['underReview']}")
        debug_print("")
        debug_print("📋 Risk Metrics:")
        debug_print(f"   - Total Risks: {response_data['moduleMetrics']['risk']['totalRisks']}")
        debug_print(f"   - Accepted Risks: {response_data['moduleMetrics']['risk']['acceptedRisks']}")
        debug_print(f"   - Mitigated Risks: {response_data['moduleMetrics']['risk']['mitigatedRisks']}")
        debug_print(f"   - In Progress: {response_data['moduleMetrics']['risk']['inProgressRisks']}")
        debug_print("")
        debug_print("📋 Incident Metrics:")
        debug_print(f"   - Total Incidents: {response_data['moduleMetrics']['incident']['totalIncidents']}")
        debug_print(f"   - Resolved: {response_data['moduleMetrics']['incident']['resolved']}")
        debug_print(f"   - MTTD: {response_data['moduleMetrics']['incident']['mttd']}h")
        debug_print(f"   - MTTR: {response_data['moduleMetrics']['incident']['mttr']}h")
        debug_print(f"   - Closure Rate: {response_data['moduleMetrics']['incident']['closureRate']}%")
        debug_print("")
        debug_print("📋 Audit Metrics:")
        debug_print(f"   - Total Audits: {response_data['moduleMetrics']['audit']['totalAudits']}")
        debug_print(f"   - Completed Audits: {response_data['moduleMetrics']['audit']['completedAudits']}")
        debug_print(f"   - Open Audits: {response_data['moduleMetrics']['audit']['openAudits']}")
        debug_print(f"   - Completion Rate: {response_data['moduleMetrics']['audit']['completionRate']}%")
        debug_print("📊 ========================================")
        debug_print("")
        debug_print(f"⚠️ RISKS:")
        debug_print(f"   Total: {response_data['hero']['stats']['totalRisks']}")
        debug_print(f"   Active: {response_data['hero']['stats']['activeRisks']}")
        debug_print(f"   Inactive: {response_data['hero']['stats']['inactiveRisks']}")
        debug_print(f"   Mitigated: {response_data['hero']['stats']['mitigatedRisks']}")
        debug_print("")
        debug_print(f"🚨 INCIDENTS:")
        debug_print(f"   Total: {response_data['hero']['stats']['totalIncidents']}")
        debug_print(f"   Active: {response_data['hero']['stats']['activeIncidents']}")
        debug_print(f"   Inactive: {response_data['hero']['stats']['inactiveIncidents']}")
        debug_print(f"   Resolved: {response_data['hero']['stats']['resolvedIncidents']}")
        debug_print("")
        debug_print(f"🔍 AUDITS:")
        debug_print(f"   Total: {response_data['hero']['stats']['totalAudits']}")
        debug_print(f"   Active: {response_data['hero']['stats']['activeAudits']}")
        debug_print(f"   Inactive: {response_data['hero']['stats']['inactiveAudits']}")
        debug_print(f"   Completed: {response_data['hero']['stats']['completedAudits']}")
        debug_print("📊 ========================================")
        debug_print("")
        debug_print("📦 ========================================")
        debug_print("")
        debug_print("✅ ========================================")
        debug_print("✅ SENDING RESPONSE TO FRONTEND")
        debug_print("✅ ========================================")
        debug_print(f"✅ Success: {response_data['success']}")
        debug_print(f"✅ Framework ID in Response: {response_data['framework']['id']}")
        debug_print(f"✅ Framework Name in Response: {response_data['framework']['name']}")
        debug_print(f"✅ Applied Policies Count: {len(response_data['policies']['applied']['policies'])}")
        debug_print("✅ ========================================")
        debug_print("")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        debug_print("")
        debug_print("❌ ========================================")
        debug_print("❌ ERROR IN get_homepage_data()")
        debug_print("❌ ========================================")
        debug_print(f"❌ Error type: {type(e).__name__}")
        debug_print(f"❌ Error message: {str(e)}")
        import traceback
        debug_print(f"❌ Traceback: {traceback.format_exc()}")
        debug_print("❌ ========================================")
        debug_print("")
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_all_frameworks_data(request):
    """
    GET /api/homepage/all-frameworks
    Returns aggregated data for ALL frameworks
    Shows combined statistics across all frameworks
    """
    # NOTE: Auto framework check on "all frameworks" view has been disabled.
    # To re-enable, restore the background thread that calls auto_check_all_frameworks.
    # debug_print("🚀 [All Frameworks] Auto framework check is currently DISABLED")
    
    debug_print("=" * 80)
    debug_print("🌐 BACKEND: get_all_frameworks_data() CALLED")
    debug_print("=" * 80)
    
    try:
        # Get all active frameworks
        all_frameworks = Framework.objects.filter(
            Status='Approved',
            ActiveInactive='Active'
        )
        
        debug_print(f"📋 Found {all_frameworks.count()} active frameworks")
        
        # Aggregate data across all frameworks
        all_frameworks_list = []
        total_stats = {
            'totalPolicies': 0,
            'totalPoliciesAll': 0,
            'activePolicies': 0,
            'inactivePolicies': 0,
            'totalCompliances': 0,
            'totalCompliancesAll': 0,
            'activeCompliances': 0,
            'inactiveCompliances': 0,
            'compliantCompliances': 0,  # New: Count of compliances with Check='2' in audit findings
            'totalRisks': 0,
            'activeRisks': 0,
            'inactiveRisks': 0,
            'mitigatedRisks': 0,
            'totalIncidents': 0,
            'activeIncidents': 0,
            'inactiveIncidents': 0,
            'resolvedIncidents': 0,
            'totalAudits': 0,
            'activeAudits': 0,
            'inactiveAudits': 0,
            'completedAudits': 0
        }
        
        # Get data for each framework
        for framework in all_frameworks:
            framework_id = framework.FrameworkId
            framework_filter = Q(FrameworkId=framework_id)
            
            # Policies
            policies_qs = Policy.objects.filter(framework_filter)
            total_policies_all = policies_qs.count()
            active_policies = policies_qs.filter(ActiveInactive='Active').count()
            inactive_policies = total_policies_all - active_policies
            
            # Compliances - Get all compliances for the framework
            compliances_qs = Compliance.objects.filter(framework_filter)
            total_compliances_all = compliances_qs.count()
            active_compliances = compliances_qs.filter(
                Status='Approved',
                ActiveInactive='Active'
            ).count()
            inactive_compliances = compliances_qs.filter(ActiveInactive='Inactive').count()
            
            # NEW: Calculate compliant compliances based on audit findings
            # Count compliances that have audit findings with Check='2' (Completed/Compliant)
            from grc.models import AuditFinding
            compliant_compliances = AuditFinding.objects.filter(
                framework_filter,
                Check='2'  # Completed = Compliant
            ).values('ComplianceId').distinct().count()
            
            # Risks
            risks_qs = RiskInstance.objects.filter(framework_filter)
            total_risks = risks_qs.count()
            active_risks = risks_qs.filter(ActiveInactive='Active').count() if hasattr(RiskInstance, 'ActiveInactive') else total_risks
            inactive_risks = total_risks - active_risks if hasattr(RiskInstance, 'ActiveInactive') else 0
            mitigated_risks = risks_qs.filter(MitigationStatus='Completed').count()
            
            # Incidents
            incidents_qs = Incident.objects.filter(framework_filter)
            total_incidents = incidents_qs.count()
            active_incidents = incidents_qs.filter(ActiveInactive='Active').count() if hasattr(Incident, 'ActiveInactive') else total_incidents
            inactive_incidents = total_incidents - active_incidents if hasattr(Incident, 'ActiveInactive') else 0
            resolved_incidents = incidents_qs.filter(Status='Completed').count()
            
            # Audits
            audits_qs = Audit.objects.filter(framework_filter)
            total_audits = audits_qs.count()
            active_audits = audits_qs.filter(ActiveInactive='Active').count() if hasattr(Audit, 'ActiveInactive') else total_audits
            inactive_audits = total_audits - active_audits if hasattr(Audit, 'ActiveInactive') else 0
            completed_audits = audits_qs.filter(Status='Completed').count()
            
            framework_data = {
                'id': framework_id,
                'name': framework.FrameworkName,
                'description': framework.FrameworkDescription,
                'category': framework.Category,
                'stats': {
                    'totalPolicies': active_policies,
                    'totalPoliciesAll': total_policies_all,
                    'activePolicies': active_policies,
                    'inactivePolicies': inactive_policies,
                    'totalCompliances': active_compliances,
                    'totalCompliancesAll': total_compliances_all,
                    'activeCompliances': active_compliances,
                    'inactiveCompliances': inactive_compliances,
                    'compliantCompliances': compliant_compliances,  # NEW: Compliant controls count
                    'totalRisks': total_risks,
                    'activeRisks': active_risks,
                    'inactiveRisks': inactive_risks,
                    'mitigatedRisks': mitigated_risks,
                    'totalIncidents': total_incidents,
                    'activeIncidents': active_incidents,
                    'inactiveIncidents': inactive_incidents,
                    'resolvedIncidents': resolved_incidents,
                    'totalAudits': total_audits,
                    'activeAudits': active_audits,
                    'inactiveAudits': inactive_audits,
                    'completedAudits': completed_audits
                }
            }
            
            all_frameworks_list.append(framework_data)
            
            # Aggregate totals
            total_stats['totalPolicies'] += active_policies
            total_stats['totalPoliciesAll'] += total_policies_all
            total_stats['activePolicies'] += active_policies
            total_stats['inactivePolicies'] += inactive_policies
            total_stats['totalCompliances'] += active_compliances
            total_stats['totalCompliancesAll'] += total_compliances_all
            total_stats['activeCompliances'] += active_compliances
            total_stats['inactiveCompliances'] += inactive_compliances
            total_stats['compliantCompliances'] += compliant_compliances  # NEW: Add to total
            total_stats['totalRisks'] += total_risks
            total_stats['activeRisks'] += active_risks
            total_stats['inactiveRisks'] += inactive_risks
            total_stats['mitigatedRisks'] += mitigated_risks
            total_stats['totalIncidents'] += total_incidents
            total_stats['activeIncidents'] += active_incidents
            total_stats['inactiveIncidents'] += inactive_incidents
            total_stats['resolvedIncidents'] += resolved_incidents
            total_stats['totalAudits'] += total_audits
            total_stats['activeAudits'] += active_audits
            total_stats['inactiveAudits'] += inactive_audits
            total_stats['completedAudits'] += completed_audits
        
        # Get aggregated policy data for donut chart
        all_policies_qs = Policy.objects.all()
        active_policies_qs = all_policies_qs.filter(ActiveInactive='Active')
        total_active_policies = active_policies_qs.count()
        
        # Categorize policies by status for donut chart
        applied_policies_qs = active_policies_qs.filter(Status='Approved')
        in_progress_policies_qs = active_policies_qs.filter(Status='Under Review')
        pending_policies_qs = active_policies_qs.filter(Status__in=['Draft', 'Pending'])
        rejected_policies_qs = active_policies_qs.filter(Status='Rejected')
        
        applied_count = applied_policies_qs.count()
        in_progress_count = in_progress_policies_qs.count()
        pending_count = pending_policies_qs.count()
        rejected_count = rejected_policies_qs.count()
        
        # Calculate percentages
        applied_pct = round((applied_count / total_active_policies * 100), 1) if total_active_policies > 0 else 0
        in_progress_pct = round((in_progress_count / total_active_policies * 100), 1) if total_active_policies > 0 else 0
        pending_pct = round((pending_count / total_active_policies * 100), 1) if total_active_policies > 0 else 0
        rejected_pct = round((rejected_count / total_active_policies * 100), 1) if total_active_policies > 0 else 0
        
        debug_print("")
        debug_print("📊 ========================================")
        debug_print("📊 ALL FRAMEWORKS AGGREGATED DATA")
        debug_print("📊 ========================================")
        debug_print(f"📋 Total Frameworks: {len(all_frameworks_list)}")
        debug_print(f"📋 POLICIES:")
        debug_print(f"   Total (All): {total_stats['totalPoliciesAll']}")
        debug_print(f"   Active: {total_stats['activePolicies']}")
        debug_print(f"   Inactive: {total_stats['inactivePolicies']}")
        debug_print(f"   Applied: {applied_count} ({applied_pct}%)")
        debug_print(f"   In Progress: {in_progress_count} ({in_progress_pct}%)")
        debug_print(f"   Pending: {pending_count} ({pending_pct}%)")
        debug_print(f"   Rejected: {rejected_count} ({rejected_pct}%)")
        debug_print(f"✅ COMPLIANCES:")
        debug_print(f"   Total (All): {total_stats['totalCompliancesAll']}")
        debug_print(f"   Active: {total_stats['activeCompliances']}")
        debug_print(f"   Inactive: {total_stats['inactiveCompliances']}")
        debug_print(f"   Compliant (Audited): {total_stats['compliantCompliances']}")
        debug_print(f"⚠️ RISKS:")
        debug_print(f"   Total: {total_stats['totalRisks']}")
        debug_print(f"   Active: {total_stats['activeRisks']}")
        debug_print(f"   Inactive: {total_stats['inactiveRisks']}")
        debug_print(f"   Mitigated: {total_stats['mitigatedRisks']}")
        debug_print(f"🚨 INCIDENTS:")
        debug_print(f"   Total: {total_stats['totalIncidents']}")
        debug_print(f"   Active: {total_stats['activeIncidents']}")
        debug_print(f"   Inactive: {total_stats['inactiveIncidents']}")
        debug_print(f"   Resolved: {total_stats['resolvedIncidents']}")
        debug_print(f"🔍 AUDITS:")
        debug_print(f"   Total: {total_stats['totalAudits']}")
        debug_print(f"   Active: {total_stats['activeAudits']}")
        debug_print(f"   Inactive: {total_stats['inactiveAudits']}")
        debug_print(f"   Completed: {total_stats['completedAudits']}")
        debug_print("📊 ========================================")
        debug_print("")
        
        # Build policy data for donut chart
        policy_data = {
            'applied': {
                'policies': list(applied_policies_qs.values('PolicyId', 'PolicyName', 'Status', 'FrameworkId')),
                'count': applied_count,
                'percentage': applied_pct
            },
            'in_progress': {
                'policies': list(in_progress_policies_qs.values('PolicyId', 'PolicyName', 'Status', 'FrameworkId')),
                'count': in_progress_count,
                'percentage': in_progress_pct
            },
            'pending': {
                'policies': list(pending_policies_qs.values('PolicyId', 'PolicyName', 'Status', 'FrameworkId')),
                'count': pending_count,
                'percentage': pending_pct
            },
            'rejected': {
                'policies': list(rejected_policies_qs.values('PolicyId', 'PolicyName', 'Status', 'FrameworkId')),
                'count': rejected_count,
                'percentage': rejected_pct
            }
        }
        
        response_data = {
            'success': True,
            'framework': {
                'id': None,
                'name': 'All Frameworks',
                'description': 'Aggregated data across all frameworks',
                'category': 'All'
            },
            'hero': {
                'stats': total_stats,
                'previewMetrics': {
                    'compliancePercentage': round((total_stats['compliantCompliances'] / total_stats['totalCompliancesAll'] * 100), 1) if total_stats['totalCompliancesAll'] > 0 else 0,
                    'remainingControls': total_stats['totalCompliancesAll'] - total_stats['compliantCompliances'],
                    'nextAudit': None,
                    'policiesLabel': 'Active Policies',
                    'policiesValue': total_stats['activePolicies']
                }
            },
            'policies': policy_data,  # NEW: Add policy data for donut chart
            'frameworks': all_frameworks_list,
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        debug_print("")
        debug_print("❌ ========================================")
        debug_print("❌ ERROR IN get_all_frameworks_data()")
        debug_print("❌ ========================================")
        debug_print(f"❌ Error type: {type(e).__name__}")
        debug_print(f"❌ Error message: {str(e)}")
        import traceback
        debug_print(f"❌ Traceback: {traceback.format_exc()}")
        debug_print("❌ ========================================")
        debug_print("")
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

