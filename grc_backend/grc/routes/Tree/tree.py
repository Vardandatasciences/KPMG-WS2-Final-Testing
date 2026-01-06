from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from grc.models import Framework, Policy, SubPolicy, Compliance, Risk, RiskInstance
from django.db.models import Q
import json

# MULTI-TENANCY: Import tenant utilities for data isolation
from ...tenant_utils import (
    require_tenant, tenant_filter, get_tenant_id_from_request,
    validate_tenant_access
)

@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_all_frameworks(request):
    """
    Get all frameworks for the tree view
    MULTI-TENANCY: Only returns frameworks for user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        frameworks = Framework.objects.filter(
            tenant_id=tenant_id,
            Status='Approved',
            ActiveInactive='Active'
        ).values(
            'FrameworkId',
            'FrameworkName',
            'FrameworkDescription',
            'Category',
            'Status',
            'ActiveInactive'
        ).order_by('FrameworkName')
        
        return JsonResponse({
            'status': 'success',
            'data': list(frameworks)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_policies_by_framework(request, framework_id):
    """
    Get all policies for a specific framework
    MULTI-TENANCY: Only returns policies for user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # MULTI-TENANCY: Validate framework belongs to tenant
        framework = Framework.objects.filter(FrameworkId=framework_id, tenant_id=tenant_id).first()
        if not framework:
            return JsonResponse({
                'status': 'error',
                'message': 'Framework not found in your organization'
            }, status=404)
        
        policies = Policy.objects.filter(
            FrameworkId=framework_id,
            tenant_id=tenant_id,
            Status='Approved',
            ActiveInactive='Active'
        ).values(
            'PolicyId',
            'PolicyName',
            'PolicyDescription',
            'Status',
            'ActiveInactive',
            'CurrentVersion'
        ).order_by('PolicyName')
        
        return JsonResponse({
            'status': 'success',
            'data': list(policies)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_subpolicies_by_policy(request, policy_id):
    """
    Get all subpolicies for a specific policy
    MULTI-TENANCY: Only returns subpolicies for user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # MULTI-TENANCY: Validate policy belongs to tenant
        policy = Policy.objects.filter(PolicyId=policy_id, tenant_id=tenant_id).first()
        if not policy:
            return JsonResponse({
                'status': 'error',
                'message': 'Policy not found in your organization'
            }, status=404)
        
        subpolicies = SubPolicy.objects.filter(
            PolicyId=policy_id,
            tenant_id=tenant_id,
            Status='Approved'
        ).values(
            'SubPolicyId',
            'SubPolicyName',
            'Description',
            'Status',
            'Identifier'
        ).order_by('SubPolicyName')
        
        return JsonResponse({
            'status': 'success',
            'data': list(subpolicies)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_compliances_by_subpolicy(request, subpolicy_id):
    """
    Get all compliances for a specific subpolicy
    MULTI-TENANCY: Only returns compliances for user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # MULTI-TENANCY: Validate subpolicy belongs to tenant
        subpolicy = SubPolicy.objects.filter(SubPolicyId=subpolicy_id, tenant_id=tenant_id).first()
        if not subpolicy:
            return JsonResponse({
                'status': 'error',
                'message': 'SubPolicy not found in your organization'
            }, status=404)
        
        compliances = Compliance.objects.filter(
            SubPolicy_id=subpolicy_id,
            tenant_id=tenant_id,
            Status='Approved',
            ActiveInactive='Active'
        ).values(
            'ComplianceId',
            'ComplianceTitle',
            'ComplianceItemDescription',
            'Criticality',
            'Status',
            'ActiveInactive',
            'ComplianceVersion',
            'MaturityLevel'
        ).order_by('ComplianceTitle')
        
        return JsonResponse({
            'status': 'success',
            'data': list(compliances)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_risks_by_compliance(request, compliance_id):
    """
    Get all risks associated with a specific compliance
    MULTI-TENANCY: Only returns risks for user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        # MULTI-TENANCY: Validate compliance belongs to tenant
        compliance = Compliance.objects.filter(ComplianceId=compliance_id, tenant_id=tenant_id).first()
        if not compliance:
            return JsonResponse({
                'status': 'error',
                'message': 'Compliance not found in your organization'
            }, status=404)
        
        # Get risks from Risk table
        risks = Risk.objects.filter(
            ComplianceId=compliance_id,
            tenant_id=tenant_id
        ).values(
            'RiskId',
            'RiskTitle',
            'RiskDescription',
            'Criticality',
            'Category',
            'RiskType',
            'PossibleDamage',
            'RiskPriority'
        )
        
        # Get risk instances for each risk to get the status
        risk_list = []
        for risk in risks:
            risk_instances = RiskInstance.objects.filter(
                RiskId=risk['RiskId'],
                tenant_id=tenant_id
            ).values(
                'RiskInstanceId',
                'RiskStatus',
                'MitigationStatus',
                'RiskPriority',
                'Origin'
            )
            
            risk_data = dict(risk)
            risk_data['instances'] = list(risk_instances)
            risk_data['has_instances'] = len(risk_instances) > 0
            
            # Get the latest status if instances exist
            if risk_instances:
                latest_instance = risk_instances.first()
                risk_data['current_status'] = latest_instance['RiskStatus']
                risk_data['mitigation_status'] = latest_instance['MitigationStatus']
            else:
                risk_data['current_status'] = 'Not Assigned'
                risk_data['mitigation_status'] = 'Pending'
            
            risk_list.append(risk_data)
        
        return JsonResponse({
            'status': 'success',
            'data': risk_list
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_tree_hierarchy(request):
    """
    Get complete tree hierarchy (optional - for loading all at once)
    MULTI-TENANCY: Only returns data for user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        frameworks = Framework.objects.filter(
            tenant_id=tenant_id,
            Status='Approved',
            ActiveInactive='Active'
        ).order_by('FrameworkName')
        
        tree_data = []
        
        for framework in frameworks:
            framework_node = {
                'id': f'framework-{framework.FrameworkId}',
                'type': 'framework',
                'data': {
                    'FrameworkId': framework.FrameworkId,
                    'FrameworkName': framework.FrameworkName,
                    'FrameworkDescription': framework.FrameworkDescription,
                    'Category': framework.Category,
                    'Status': framework.Status
                },
                'children': []
            }
            
            policies = Policy.objects.filter(
                FrameworkId=framework.FrameworkId,
                tenant_id=tenant_id,
                Status='Approved',
                ActiveInactive='Active'
            ).order_by('PolicyName')
            
            for policy in policies:
                policy_node = {
                    'id': f'policy-{policy.PolicyId}',
                    'type': 'policy',
                    'data': {
                        'PolicyId': policy.PolicyId,
                        'PolicyName': policy.PolicyName,
                        'PolicyDescription': policy.PolicyDescription,
                        'Status': policy.Status
                    },
                    'children': []
                }
                
                subpolicies = SubPolicy.objects.filter(
                    PolicyId=policy.PolicyId,
                    tenant_id=tenant_id,
                    Status='Approved'
                ).order_by('SubPolicyName')
                
                for subpolicy in subpolicies:
                    subpolicy_node = {
                        'id': f'subpolicy-{subpolicy.SubPolicyId}',
                        'type': 'subpolicy',
                        'data': {
                            'SubPolicyId': subpolicy.SubPolicyId,
                            'SubPolicyName': subpolicy.SubPolicyName,
                            'Description': subpolicy.Description,
                            'Status': subpolicy.Status
                        },
                        'children': []
                    }
                    
                    compliances = Compliance.objects.filter(
                        SubPolicy_id=subpolicy.SubPolicyId,
                        tenant_id=tenant_id,
                        Status='Approved',
                        ActiveInactive='Active'
                    ).order_by('ComplianceTitle')
                    
                    for compliance in compliances:
                        compliance_node = {
                            'id': f'compliance-{compliance.ComplianceId}',
                            'type': 'compliance',
                            'data': {
                                'ComplianceId': compliance.ComplianceId,
                                'ComplianceTitle': compliance.ComplianceTitle or 'Untitled Compliance',
                                'ComplianceItemDescription': compliance.ComplianceItemDescription,
                                'Criticality': compliance.Criticality,
                                'Status': compliance.Status
                            },
                            'children': []
                        }
                        
                        subpolicy_node['children'].append(compliance_node)
                    
                    policy_node['children'].append(subpolicy_node)
                
                framework_node['children'].append(policy_node)
            
            tree_data.append(framework_node)
        
        return JsonResponse({
            'status': 'success',
            'data': tree_data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_framework_metadata(request, framework_id):
    """
    Get detailed metadata for a framework (for hover tooltip)
    MULTI-TENANCY: Only returns metadata for frameworks in user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        framework = Framework.objects.get(FrameworkId=framework_id, tenant_id=tenant_id)
        
        metadata = {
            'FrameworkId': framework.FrameworkId,
            'FrameworkName': framework.FrameworkName,
            'FrameworkDescription': framework.FrameworkDescription or 'No description available',
            'Category': framework.Category or 'N/A',
            'Status': framework.Status or 'N/A',
            'ActiveInactive': framework.ActiveInactive or 'N/A',
            'EffectiveDate': framework.EffectiveDate.strftime('%Y-%m-%d') if framework.EffectiveDate else 'N/A',
            'StartDate': framework.StartDate.strftime('%Y-%m-%d') if framework.StartDate else 'N/A',
            'EndDate': framework.EndDate.strftime('%Y-%m-%d') if framework.EndDate else 'N/A',
            'CurrentVersion': framework.CurrentVersion or 'N/A',
            'CreatedByName': framework.CreatedByName or 'N/A',
            'CreatedByDate': framework.CreatedByDate.strftime('%Y-%m-%d') if framework.CreatedByDate else 'N/A',
            'Identifier': framework.Identifier or 'N/A',
            'InternalExternal': framework.InternalExternal or 'N/A',
        }
        
        return JsonResponse({
            'status': 'success',
            'data': metadata
        })
    except Framework.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Framework not found in your organization'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_policy_metadata(request, policy_id):
    """
    Get detailed metadata for a policy (for hover tooltip)
    MULTI-TENANCY: Only returns metadata for policies in user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        policy = Policy.objects.get(PolicyId=policy_id, tenant_id=tenant_id)
        
        metadata = {
            'PolicyId': policy.PolicyId,
            'PolicyName': policy.PolicyName,
            'PolicyDescription': policy.PolicyDescription or 'No description available',
            'Status': policy.Status or 'N/A',
            'ActiveInactive': policy.ActiveInactive or 'N/A',
            'CurrentVersion': policy.CurrentVersion or 'N/A',
            'StartDate': policy.StartDate.strftime('%Y-%m-%d') if policy.StartDate else 'N/A',
            'EndDate': policy.EndDate.strftime('%Y-%m-%d') if policy.EndDate else 'N/A',
            'Department': policy.Department or 'N/A',
            'CreatedByName': policy.CreatedByName or 'N/A',
            'CreatedByDate': policy.CreatedByDate.strftime('%Y-%m-%d') if policy.CreatedByDate else 'N/A',
            'Applicability': policy.Applicability or 'N/A',
            'Scope': policy.Scope or 'N/A',
            'Objective': policy.Objective or 'N/A',
            'Identifier': policy.Identifier or 'N/A',
            'PermanentTemporary': policy.PermanentTemporary or 'N/A',
            'PolicyType': policy.PolicyType or 'N/A',
            'PolicyCategory': policy.PolicyCategory or 'N/A',
            'PolicySubCategory': policy.PolicySubCategory or 'N/A',
        }
        
        return JsonResponse({
            'status': 'success',
            'data': metadata
        })
    except Policy.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Policy not found in your organization'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_subpolicy_metadata(request, subpolicy_id):
    """
    Get detailed metadata for a subpolicy (for hover tooltip)
    MULTI-TENANCY: Only returns metadata for subpolicies in user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        subpolicy = SubPolicy.objects.get(SubPolicyId=subpolicy_id, tenant_id=tenant_id)
        
        metadata = {
            'SubPolicyId': subpolicy.SubPolicyId,
            'SubPolicyName': subpolicy.SubPolicyName,
            'Description': subpolicy.Description or 'No description available',
            'Status': subpolicy.Status or 'N/A',
            'Identifier': subpolicy.Identifier or 'N/A',
            'CreatedByName': subpolicy.CreatedByName or 'N/A',
            'CreatedByDate': subpolicy.CreatedByDate.strftime('%Y-%m-%d') if subpolicy.CreatedByDate else 'N/A',
            'PermanentTemporary': subpolicy.PermanentTemporary or 'N/A',
            'Control': subpolicy.Control or 'N/A',
        }
        
        return JsonResponse({
            'status': 'success',
            'data': metadata
        })
    except SubPolicy.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'SubPolicy not found in your organization'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_compliance_metadata(request, compliance_id):
    """
    Get detailed metadata for a compliance (for hover tooltip)
    MULTI-TENANCY: Only returns metadata for compliances in user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        compliance = Compliance.objects.get(ComplianceId=compliance_id, tenant_id=tenant_id)
        
        metadata = {
            'ComplianceId': compliance.ComplianceId,
            'ComplianceTitle': compliance.ComplianceTitle or 'Untitled Compliance',
            'ComplianceItemDescription': compliance.ComplianceItemDescription or 'No description available',
            'Status': compliance.Status or 'N/A',
            'ActiveInactive': compliance.ActiveInactive or 'N/A',
            'ComplianceVersion': compliance.ComplianceVersion or 'N/A',
            'Criticality': compliance.Criticality or 'N/A',
            'MaturityLevel': compliance.MaturityLevel or 'N/A',
            'MandatoryOptional': compliance.MandatoryOptional or 'N/A',
            'ManualAutomatic': compliance.ManualAutomatic or 'N/A',
            'Impact': compliance.Impact or 'N/A',
            'Probability': compliance.Probability or 'N/A',
            'RiskType': compliance.RiskType or 'N/A',
            'RiskCategory': compliance.RiskCategory or 'N/A',
            'RiskBusinessImpact': compliance.RiskBusinessImpact or 'N/A',
            'Scope': compliance.Scope or 'N/A',
            'Objective': compliance.Objective or 'N/A',
            'BusinessUnitsCovered': compliance.BusinessUnitsCovered or 'N/A',
            'Applicability': compliance.Applicability or 'N/A',
            'PermanentTemporary': compliance.PermanentTemporary or 'N/A',
            'CreatedByName': compliance.CreatedByName or 'N/A',
            'CreatedByDate': compliance.CreatedByDate.strftime('%Y-%m-%d') if compliance.CreatedByDate else 'N/A',
            'Identifier': compliance.Identifier or 'N/A',
        }
        
        return JsonResponse({
            'status': 'success',
            'data': metadata
        })
    except Compliance.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Compliance not found in your organization'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_risk_metadata(request, risk_id):
    """
    Get detailed metadata for a risk (for hover tooltip)
    MULTI-TENANCY: Only returns metadata for risks in user's tenant
    """
    # MULTI-TENANCY: Extract tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    
    try:
        risk = Risk.objects.get(RiskId=risk_id, tenant_id=tenant_id)
        
        # Get latest risk instance if available
        latest_instance = RiskInstance.objects.filter(
            RiskId=risk_id,
            tenant_id=tenant_id
        ).order_by('-CreatedAt').first()
        
        metadata = {
            'RiskId': risk.RiskId,
            'RiskTitle': risk.RiskTitle or 'Untitled Risk',
            'RiskDescription': risk.RiskDescription or 'No description available',
            'Criticality': risk.Criticality or 'N/A',
            'Category': risk.Category or 'N/A',
            'RiskType': risk.RiskType or 'N/A',
            'BusinessImpact': risk.BusinessImpact or 'N/A',
            'PossibleDamage': risk.PossibleDamage or 'N/A',
            'RiskLikelihood': risk.RiskLikelihood or 'N/A',
            'RiskImpact': risk.RiskImpact or 'N/A',
            'RiskExposureRating': risk.RiskExposureRating or 'N/A',
            'RiskPriority': risk.RiskPriority or 'N/A',
            'RiskMitigation': risk.RiskMitigation or 'N/A',
            'CreatedAt': risk.CreatedAt.strftime('%Y-%m-%d') if risk.CreatedAt else 'N/A',
        }
        
        # Add instance data if available
        if latest_instance:
            metadata['RiskStatus'] = latest_instance.RiskStatus or 'N/A'
            metadata['MitigationStatus'] = latest_instance.MitigationStatus or 'N/A'
            metadata['RiskOwner'] = latest_instance.RiskOwner or 'N/A'
            metadata['MitigationDueDate'] = latest_instance.MitigationDueDate.strftime('%Y-%m-%d') if latest_instance.MitigationDueDate else 'N/A'
            metadata['Origin'] = latest_instance.Origin or 'N/A'
        
        return JsonResponse({
            'status': 'success',
            'data': metadata
        })
    except Risk.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Risk not found in your organization'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
