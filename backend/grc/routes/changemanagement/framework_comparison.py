"""
Framework Comparison API
Provides endpoints for comparing framework versions with amendments
"""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from grc.models import Framework, Policy, SubPolicy, Compliance
from .similarity_matcher import get_similarity_matcher
import logging
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


@api_view(['GET'])
def get_frameworks_with_amendments(request):
    """
    Get all frameworks that have amendments
    Returns frameworks with non-empty Amendment column
    """
    try:
        # Get frameworks where Amendment field is not null/empty
        frameworks = Framework.objects.exclude(
            Q(Amendment__isnull=True) | Q(Amendment=[])
        ).values(
            'FrameworkId',
            'FrameworkName',
            'FrameworkDescription',
            'CurrentVersion',
            'Category',
            'Status',
            'Amendment'
        )
        
        # Add amendment count to each framework
        frameworks_list = []
        for fw in frameworks:
            fw_data = dict(fw)
            amendments = fw_data.get('Amendment', [])
            fw_data['amendment_count'] = len(amendments) if isinstance(amendments, list) else 0
            fw_data['latest_amendment'] = amendments[-1] if amendments else None
            frameworks_list.append(fw_data)
        
        return Response({
            'success': True,
            'data': frameworks_list,
            'count': len(frameworks_list)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching frameworks with amendments: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_framework_amendments(request, framework_id):
    """
    Get all amendments for a specific framework
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        return Response({
            'success': True,
            'framework_id': framework.FrameworkId,
            'framework_name': framework.FrameworkName,
            'amendments': amendments,
            'count': len(amendments)
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching amendments for framework {framework_id}: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_framework_origin_data(request, framework_id):
    """
    Get origin (current) framework data with full hierarchy:
    Framework -> Policies -> SubPolicies -> Compliances
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Get all policies for this framework
        policies = Policy.objects.filter(FrameworkId=framework_id).values(
            'PolicyId',
            'PolicyName',
            'PolicyDescription',
            'Identifier',
            'Status',
            'CurrentVersion'
        )
        
        policies_data = []
        for policy in policies:
            # Get subpolicies for each policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy['PolicyId']).values(
                'SubPolicyId',
                'SubPolicyName',
                'Description',
                'Identifier',
                'Status'
            )
            
            subpolicies_data = []
            for subpolicy in subpolicies:
                # Get compliances for each subpolicy
                compliances = Compliance.objects.filter(SubPolicy=subpolicy['SubPolicyId']).values(
                    'ComplianceId',
                    'ComplianceTitle',
                    'ComplianceItemDescription',
                    'ComplianceType',
                    'Status',
                    'Criticality',
                    'MaturityLevel',
                    'ManualAutomatic',
                    'MandatoryOptional'
                )
                
                subpolicies_data.append({
                    **subpolicy,
                    'compliances': list(compliances)
                })
            
            policies_data.append({
                **policy,
                'subpolicies': subpolicies_data
            })
        
        return Response({
            'success': True,
            'framework': {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName,
                'FrameworkDescription': framework.FrameworkDescription,
                'CurrentVersion': framework.CurrentVersion,
                'Status': framework.Status
            },
            'policies': policies_data,
            'total_policies': len(policies_data)
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching origin data for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_framework_target_data(request, framework_id, amendment_id=None):
    """
    Get target (amended) framework data from Amendment JSON
    If amendment_id is provided, get specific amendment
    Otherwise, get the latest amendment
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        if not amendments:
            return Response({
                'success': False,
                'error': 'No amendments found for this framework'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get specific amendment or latest
        if amendment_id is not None:
            try:
                amendment_idx = int(amendment_id) - 1
                if amendment_idx < 0 or amendment_idx >= len(amendments):
                    return Response({
                        'success': False,
                        'error': f'Amendment ID {amendment_id} not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                target_amendment = amendments[amendment_idx]
            except (ValueError, IndexError):
                return Response({
                    'success': False,
                    'error': f'Invalid amendment ID {amendment_id}'
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_amendment = amendments[-1]  # Latest amendment
        
        # Extract amendment data
        modified_controls = target_amendment.get('ai_analysis', {}).get('modified_controls', [])
        new_additions = target_amendment.get('ai_analysis', {}).get('new_additions', [])
        framework_references = target_amendment.get('ai_analysis', {}).get('framework_references', [])
        modified_sections = target_amendment.get('modified_sections', [])
        
        return Response({
            'success': True,
            'framework': {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName,
            },
            'amendment': {
                'amendment_id': target_amendment.get('amendment_id'),
                'amendment_name': target_amendment.get('amendment_name'),
                'uploaded_date': target_amendment.get('uploaded_date'),
                's3_url': target_amendment.get('s3_url'),
                'content_summary': target_amendment.get('content_summary'),
            },
            'modified_controls': modified_controls,
            'new_additions': new_additions,
            'framework_references': framework_references,
            'modified_sections': modified_sections,
            'stats': {
                'total_modified': len(modified_controls),
                'total_new': len(new_additions),
                'total_references': len(framework_references)
            }
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching target data for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_framework_comparison_summary(request, framework_id):
    """
    Get summary statistics for framework comparison
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        if not amendments:
            return Response({
                'success': False,
                'error': 'No amendments found for this framework'
            }, status=status.HTTP_404_NOT_FOUND)
        
        latest_amendment = amendments[-1]
        ai_analysis = latest_amendment.get('ai_analysis', {})
        
        # Count statistics
        modified_controls = ai_analysis.get('modified_controls', [])
        new_additions = ai_analysis.get('new_additions', [])
        
        # Count by change type
        modified_count = sum(1 for c in modified_controls if c.get('change_type') in ['modified', 'enhanced'])
        new_count = len(new_additions)
        deprecated_count = sum(1 for c in modified_controls if c.get('change_type') == 'deprecated')
        
        # Count sub-policies affected
        sub_policies_count = sum(
            len(c.get('sub_policies', [])) 
            for c in modified_controls
        )
        
        return Response({
            'success': True,
            'framework_id': framework.FrameworkId,
            'framework_name': framework.FrameworkName,
            'summary': {
                'new_controls': new_count,
                'modified_controls': modified_count,
                'deprecated_controls': deprecated_count,
                'sub_policies_affected': sub_policies_count,
                'total_amendments': len(amendments),
                'latest_amendment_date': latest_amendment.get('uploaded_date'),
                'latest_amendment_name': latest_amendment.get('amendment_name')
            }
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching comparison summary for framework {framework_id}: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def find_control_matches(request, framework_id):
    """
    Find best matching origin items for a target control
    
    POST body:
    {
        "control": {
            "control_id": "...",
            "control_name": "...",
            "change_description": "..."
        },
        "use_ai": true/false,  # Optional, default false
        "top_n": 5  # Optional, default 5
    }
    """
    try:
        logger.info("find_control_matches called")
        logger.info("Request user: %s", getattr(request.user, "UserName", None))
        logger.info("Request data: %s", request.data)

        # Get request data
        control = request.data.get('control')
        use_ai = request.data.get('use_ai', False)
        top_n = request.data.get('top_n', 5)
        
        if not control:
            return Response({
                'success': False,
                'error': 'Control data is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get origin data
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Get all policies for this framework
        policies = Policy.objects.filter(FrameworkId=framework_id).values(
            'PolicyId',
            'PolicyName',
            'PolicyDescription',
            'Identifier',
            'Status',
            'CurrentVersion'
        )
        
        policies_data = []
        for policy in policies:
            # Get subpolicies for each policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy['PolicyId']).values(
                'SubPolicyId',
                'SubPolicyName',
                'Description',
                'Identifier',
                'Status'
            )
            
            subpolicies_data = []
            for subpolicy in subpolicies:
                # Get compliances for each subpolicy
                compliances = Compliance.objects.filter(SubPolicy=subpolicy['SubPolicyId']).values(
                    'ComplianceId',
                    'ComplianceTitle',
                    'ComplianceItemDescription',
                    'ComplianceType',
                    'Status'
                )
                
                subpolicies_data.append({
                    **subpolicy,
                    'compliances': list(compliances)
                })
            
            policies_data.append({
                **policy,
                'subpolicies': subpolicies_data
            })
        
        origin_data = {
            'framework': {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName
            },
            'policies': policies_data
        }
        
        # Get similarity matcher
        matcher = get_similarity_matcher()
        
        # Find matches
        matches = matcher.find_best_matches(
            control,
            origin_data,
            top_n=top_n,
            use_ai=use_ai
        )
        
        return Response({
            'success': True,
            'control': control,
            'matches': matches,
            'total_matches': len(matches),
            'use_ai': use_ai
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error finding control matches for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def batch_match_controls(request, framework_id):
    """
    Match multiple controls at once
    
    POST body:
    {
        "controls": [...],  # Array of controls
        "use_ai": true/false  # Optional, default false
    }
    """
    try:
        # Get request data
        controls = request.data.get('controls', [])
        use_ai = request.data.get('use_ai', False)
        
        if not controls:
            return Response({
                'success': False,
                'error': 'Controls array is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get origin data
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Get all policies for this framework
        policies = Policy.objects.filter(FrameworkId=framework_id).values(
            'PolicyId',
            'PolicyName',
            'PolicyDescription',
            'Identifier',
            'Status',
            'CurrentVersion'
        )
        
        policies_data = []
        for policy in policies:
            # Get subpolicies for each policy
            subpolicies = SubPolicy.objects.filter(PolicyId=policy['PolicyId']).values(
                'SubPolicyId',
                'SubPolicyName',
                'Description',
                'Identifier',
                'Status'
            )
            
            subpolicies_data = []
            for subpolicy in subpolicies:
                # Get compliances for each subpolicy
                compliances = Compliance.objects.filter(SubPolicy=subpolicy['SubPolicyId']).values(
                    'ComplianceId',
                    'ComplianceTitle',
                    'ComplianceItemDescription',
                    'ComplianceType',
                    'Status'
                )
                
                subpolicies_data.append({
                    **subpolicy,
                    'compliances': list(compliances)
                })
            
            policies_data.append({
                **policy,
                'subpolicies': subpolicies_data
            })
        
        origin_data = {
            'framework': {
                'FrameworkId': framework.FrameworkId,
                'FrameworkName': framework.FrameworkName
            },
            'policies': policies_data
        }
        
        # Get similarity matcher
        matcher = get_similarity_matcher()
        
        # Batch match controls
        results = matcher.batch_match_controls(controls, origin_data, use_ai=use_ai)
        
        return Response({
            'success': True,
            'total_controls': len(controls),
            'matches': results,
            'use_ai': use_ai
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error batch matching controls for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_migration_overview(request, framework_id):
    """
    Get migration overview for a framework
    Returns high-level statistics and recent activity
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        if not amendments:
            return Response({
                'success': False,
                'error': 'No amendments found for this framework'
            }, status=status.HTTP_404_NOT_FOUND)
        
        latest_amendment = amendments[-1]
        ai_analysis = latest_amendment.get('ai_analysis', {})
        
        # Count statistics
        modified_controls = ai_analysis.get('modified_controls', [])
        new_additions = ai_analysis.get('new_additions', [])
        
        # Count by change type
        new_count = len(new_additions)
        modified_count = sum(1 for c in modified_controls if c.get('change_type') in ['modified', 'enhanced'])
        removed_count = sum(1 for c in modified_controls if c.get('change_type') == 'deprecated')
        
        # Calculate progress (this is a simple calculation, can be made more sophisticated)
        total_changes = new_count + modified_count + removed_count
        # Assume if we have processed the latest amendment, we're 80% complete (example)
        progress_percentage = 80 if total_changes > 0 else 0
        
        # Get migration status based on framework status
        migration_status = "IN PROGRESS"
        if framework.Status == "Approved":
            migration_status = "COMPLETED"
        elif framework.Status == "Draft":
            migration_status = "NOT STARTED"
        
        # Generate recent activities from modified controls (latest 5)
        recent_activities = []
        activity_count = 0
        for control in modified_controls[:5]:
            activity_count += 1
            activity = {
                'id': activity_count,
                'action': f"{control.get('control_id', 'N/A')} {control.get('control_name', 'Control')} - {control.get('change_type', 'modified').title()}",
                'status': 'completed' if control.get('change_type') == 'deprecated' else 'info',
                'time': 'Recently updated',
                'control_id': control.get('control_id'),
                'change_type': control.get('change_type')
            }
            recent_activities.append(activity)
        
        return Response({
            'success': True,
            'framework': {
                'id': framework.FrameworkId,
                'name': framework.FrameworkName,
                'version': framework.CurrentVersion,
                'status': framework.Status
            },
            'migration_status': migration_status,
            'progress_percentage': progress_percentage,
            'statistics': {
                'new_controls': new_count,
                'modified_controls': modified_count,
                'removed_controls': removed_count,
                'total_changes': total_changes
            },
            'recent_activities': recent_activities,
            'latest_amendment': {
                'name': latest_amendment.get('amendment_name'),
                'date': latest_amendment.get('uploaded_date'),
                's3_url': latest_amendment.get('s3_url')
            }
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching migration overview for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_migration_gap_analysis(request, framework_id):
    """
    Get gap analysis data for migration
    Returns detailed breakdown of changes needed
    """
    try:
        framework = Framework.objects.get(FrameworkId=framework_id)
        amendments = framework.Amendment if framework.Amendment else []
        
        if not amendments:
            return Response({
                'success': False,
                'error': 'No amendments found for this framework'
            }, status=status.HTTP_404_NOT_FOUND)
        
        latest_amendment = amendments[-1]
        ai_analysis = latest_amendment.get('ai_analysis', {})
        
        # Get modified controls and new additions
        modified_controls = ai_analysis.get('modified_controls', [])
        new_additions = ai_analysis.get('new_additions', [])
        
        # Format gap items
        gap_items = []
        for control in modified_controls:
            gap_item = {
                'control_id': control.get('control_id'),
                'control_name': control.get('control_name'),
                'change_type': control.get('change_type'),
                'change_description': control.get('change_description'),
                'enhancements': control.get('enhancements', []),
                'related_controls': control.get('related_controls', []),
                'sub_policies': control.get('sub_policies', []),
                'priority': _determine_priority(control.get('change_type')),
                'action_required': _get_action_required(control.get('change_type')),
                'status': 'pending'
            }
            gap_items.append(gap_item)
        
        # Add new additions as gap items
        for addition in new_additions:
            gap_item = {
                'control_id': addition.get('control_id'),
                'control_name': addition.get('control_name'),
                'change_type': 'new',
                'change_description': addition.get('purpose', ''),
                'scope': addition.get('scope'),
                'purpose': addition.get('purpose'),
                'requirements': addition.get('requirements', []),
                'priority': 'High',
                'action_required': 'Implement new control',
                'status': 'new'
            }
            gap_items.append(gap_item)
        
        return Response({
            'success': True,
            'framework': {
                'id': framework.FrameworkId,
                'name': framework.FrameworkName,
                'version': framework.CurrentVersion
            },
            'amendment': {
                'name': latest_amendment.get('amendment_name'),
                'date': latest_amendment.get('uploaded_date')
            },
            'gap_items': gap_items,
            'total_gaps': len(gap_items),
            'summary': {
                'high_priority': sum(1 for item in gap_items if item['priority'] == 'High'),
                'medium_priority': sum(1 for item in gap_items if item['priority'] == 'Medium'),
                'low_priority': sum(1 for item in gap_items if item['priority'] == 'Low'),
                'new_controls': sum(1 for item in gap_items if item['change_type'] == 'new'),
                'modified_controls': sum(1 for item in gap_items if item['change_type'] in ['modified', 'enhanced']),
                'deprecated_controls': sum(1 for item in gap_items if item['change_type'] == 'deprecated')
            }
        }, status=status.HTTP_200_OK)
        
    except Framework.DoesNotExist:
        return Response({
            'success': False,
            'error': f'Framework with ID {framework_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching gap analysis for framework {framework_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _determine_priority(change_type):
    """Helper function to determine priority based on change type"""
    priority_map = {
        'new': 'High',
        'modified': 'High',
        'enhanced': 'Medium',
        'deprecated': 'Low',
        'unchanged': 'Low'
    }
    return priority_map.get(change_type, 'Medium')


def _get_action_required(change_type):
    """Helper function to get action required based on change type"""
    action_map = {
        'new': 'Implement new control and procedures',
        'modified': 'Review and update existing control',
        'enhanced': 'Enhance existing control implementation',
        'deprecated': 'Plan phaseout and update documentation',
        'unchanged': 'No action required'
    }
    return action_map.get(change_type, 'Review changes')



