"""
RFP Versioning and Editing API Views
Handles RFP editing with versioning support and change request tracking
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import json
import uuid
from datetime import datetime

from .models import RFP, RFPEvaluationCriteria, RFPVersions
from .serializers import RFPSerializer

# RBAC imports
from rfp.rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission
from rbac.tprm_decorators import rbac_rfp_required


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def edit_rfp_with_versioning(request):
    """
    Edit RFP with automatic versioning and change tracking
    """
    try:
        rfp_id = request.data.get('rfp_id')
        rfp_data = request.data.get('rfp_data')
        change_reason = request.data.get('change_reason')
        change_request_id = request.data.get('change_request_id')
        fields_changed = request.data.get('fields_changed', [])
        
        if not rfp_id or not rfp_data:
            return Response({
                'success': False,
                'error': 'RFP ID and data are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the current RFP
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id)
        except RFP.DoesNotExist:
            return Response({
                'success': False,
                'error': 'RFP not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        with transaction.atomic():
            # Create version record before making changes
            version_id = f"VR_{uuid.uuid4().hex[:8].upper()}"
            
            # Get the next version number
            latest_version = RFPVersions.objects.filter(rfp_id=rfp_id).order_by('-version_number').first()
            version_number = (latest_version.version_number + 1) if latest_version else 1
            
            # Create comprehensive JSON payload of current state
            current_payload = {
                'rfp_id': rfp.rfp_id,
                'rfp_number': rfp.rfp_number,
                'rfp_title': rfp.rfp_title,
                'description': rfp.description,
                'rfp_type': rfp.rfp_type,
                'category': rfp.category,
                'status': rfp.status,
                'version_number': rfp.version_number,
                'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
                'currency': rfp.currency,
                'budget_range_min': float(rfp.budget_range_min) if rfp.budget_range_min else None,
                'budget_range_max': float(rfp.budget_range_max) if rfp.budget_range_max else None,
                'issue_date': rfp.issue_date.isoformat() if rfp.issue_date else None,
                'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
                'evaluation_period_end': rfp.evaluation_period_end.isoformat() if rfp.evaluation_period_end else None,
                'award_date': rfp.award_date.isoformat() if rfp.award_date else None,
                'evaluation_method': rfp.evaluation_method,
                'criticality_level': rfp.criticality_level,
                'geographical_scope': rfp.geographical_scope,
                'approval_workflow_id': rfp.approval_workflow_id,
                'auto_approved': rfp.auto_approved,
                'allow_late_submissions': rfp.allow_late_submissions,
                'compliance_requirements': rfp.compliance_requirements,
                'custom_fields': rfp.custom_fields,
                'documents': rfp.documents,
                'final_evaluation_score': float(rfp.final_evaluation_score) if rfp.final_evaluation_score else None,
                'award_decision_date': rfp.award_decision_date.isoformat() if rfp.award_decision_date else None,
                'award_justification': rfp.award_justification,
                'created_at': rfp.created_at.isoformat(),
                'updated_at': rfp.updated_at.isoformat(),
                'created_by': rfp.created_by,
                'approved_by': rfp.approved_by,
                'primary_reviewer_id': rfp.primary_reviewer_id,
                'executive_reviewer_id': rfp.executive_reviewer_id
            }
            
            # Create version record
            version_record = RFPVersions.objects.create(
                version_id=version_id,
                rfp_id=rfp_id,
                version_number=version_number,
                version_label=f"Version {version_number} - {rfp.rfp_title}",
                json_payload=current_payload,
                changes_summary=f"Changes made to: {', '.join(fields_changed)}" if fields_changed else "RFP updated",
                created_by=request.data.get('user_id', 1),
                created_by_name=request.data.get('user_name', 'System'),
                created_by_role=request.data.get('user_role', 'Administrator'),
                version_type='REVISION',
                parent_version_id=latest_version.version_id if latest_version else None,
                is_current=True,
                change_reason=change_reason
            )
            
            # Update the RFP with new data
            rfp.rfp_title = rfp_data.get('rfp_title', rfp.rfp_title)
            rfp.description = rfp_data.get('description', rfp.description)
            rfp.rfp_type = rfp_data.get('rfp_type', rfp.rfp_type)
            rfp.category = rfp_data.get('category', rfp.category)
            rfp.estimated_value = rfp_data.get('estimated_value')
            rfp.currency = rfp_data.get('currency', rfp.currency)
            rfp.budget_range_min = rfp_data.get('budget_range_min')
            rfp.budget_range_max = rfp_data.get('budget_range_max')
            rfp.issue_date = rfp_data.get('issue_date')
            rfp.submission_deadline = rfp_data.get('submission_deadline')
            rfp.evaluation_period_end = rfp_data.get('evaluation_period_end')
            rfp.award_date = rfp_data.get('award_date')
            rfp.evaluation_method = rfp_data.get('evaluation_method', rfp.evaluation_method)
            rfp.criticality_level = rfp_data.get('criticality_level', rfp.criticality_level)
            rfp.geographical_scope = rfp_data.get('geographical_scope', rfp.geographical_scope)
            rfp.auto_approved = rfp_data.get('auto_approved', rfp.auto_approved)
            rfp.allow_late_submissions = rfp_data.get('allow_late_submissions', rfp.allow_late_submissions)
            rfp.compliance_requirements = rfp_data.get('compliance_requirements', rfp.compliance_requirements)
            rfp.custom_fields = rfp_data.get('custom_fields', rfp.custom_fields)
            rfp.version_number = version_number
            rfp.updated_at = timezone.now()
            
            rfp.save()
            
            # Mark previous versions as not current
            RFPVersions.objects.filter(rfp_id=rfp_id, is_current=True).exclude(version_id=version_id).update(is_current=False)
            
            # Update change request status if provided
            if change_request_id:
                try:
                    # This would update the change request status in the approval system
                    # For now, we'll just log it
                    print(f"Change request {change_request_id} addressed for RFP {rfp_id}")
                except Exception as e:
                    print(f"Error updating change request status: {e}")
            
            return Response({
                'success': True,
                'message': 'RFP updated successfully with versioning',
                'rfp': {
                    'rfp_id': rfp.rfp_id,
                    'version_number': rfp.version_number,
                    'updated_at': rfp.updated_at.isoformat()
                },
                'version': {
                    'version_id': version_record.version_id,
                    'version_number': version_record.version_number,
                    'changes_summary': version_record.changes_summary
                }
            })
            
    except Exception as e:
        print(f"Error editing RFP with versioning: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Failed to edit RFP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_rfp_version_history(request, rfp_id):
    """
    Get version history for an RFP
    """
    try:
        versions = RFPVersions.objects.filter(rfp_id=rfp_id).order_by('-version_number')
        
        version_list = []
        for version in versions:
            version_list.append({
                'version_id': version.version_id,
                'version_number': version.version_number,
                'version_label': version.version_label,
                'version_type': version.version_type,
                'changes_summary': version.changes_summary,
                'created_by_name': version.created_by_name,
                'created_by_role': version.created_by_role,
                'created_at': version.created_at.isoformat(),
                'is_current': version.is_current,
                'change_reason': version.change_reason,
                'parent_version_id': version.parent_version_id
            })
        
        return Response({
            'success': True,
            'versions': version_list
        })
        
    except Exception as e:
        print(f"Error getting RFP version history: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to get version history: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_rfp_version(request, version_id):
    """
    Get specific version of an RFP
    """
    try:
        version = RFPVersions.objects.get(version_id=version_id)
        
        return Response({
            'success': True,
            'rfp': version.json_payload,
            'version_info': {
                'version_id': version.version_id,
                'version_number': version.version_number,
                'version_label': version.version_label,
                'version_type': version.version_type,
                'changes_summary': version.changes_summary,
                'created_by_name': version.created_by_name,
                'created_by_role': version.created_by_role,
                'created_at': version.created_at.isoformat(),
                'is_current': version.is_current,
                'change_reason': version.change_reason
            }
        })
        
    except RFPVersions.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Version not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error getting RFP version: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to get version: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def rollback_rfp_version(request):
    """
    Rollback RFP to a specific version
    """
    try:
        rfp_id = request.data.get('rfp_id')
        version_id = request.data.get('version_id')
        rollback_reason = request.data.get('rollback_reason', 'Rollback to previous version')
        
        if not rfp_id or not version_id:
            return Response({
                'success': False,
                'error': 'RFP ID and version ID are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Get the version to rollback to
            try:
                version = RFPVersions.objects.get(version_id=version_id, rfp_id=rfp_id)
            except RFPVersions.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Version not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get current RFP
            rfp = RFP.objects.get(rfp_id=rfp_id)
            
            # Create a new version record for the rollback
            rollback_version_id = f"VR_{uuid.uuid4().hex[:8].upper()}"
            latest_version = RFPVersions.objects.filter(rfp_id=rfp_id).order_by('-version_number').first()
            version_number = (latest_version.version_number + 1) if latest_version else 1
            
            # Create version record for current state before rollback
            current_payload = {
                'rfp_id': rfp.rfp_id,
                'rfp_number': rfp.rfp_number,
                'rfp_title': rfp.rfp_title,
                'description': rfp.description,
                'rfp_type': rfp.rfp_type,
                'category': rfp.category,
                'status': rfp.status,
                'version_number': rfp.version_number,
                'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
                'currency': rfp.currency,
                'budget_range_min': float(rfp.budget_range_min) if rfp.budget_range_min else None,
                'budget_range_max': float(rfp.budget_range_max) if rfp.budget_range_max else None,
                'issue_date': rfp.issue_date.isoformat() if rfp.issue_date else None,
                'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
                'evaluation_period_end': rfp.evaluation_period_end.isoformat() if rfp.evaluation_period_end else None,
                'award_date': rfp.award_date.isoformat() if rfp.award_date else None,
                'evaluation_method': rfp.evaluation_method,
                'criticality_level': rfp.criticality_level,
                'geographical_scope': rfp.geographical_scope,
                'approval_workflow_id': rfp.approval_workflow_id,
                'auto_approved': rfp.auto_approved,
                'allow_late_submissions': rfp.allow_late_submissions,
                'compliance_requirements': rfp.compliance_requirements,
                'custom_fields': rfp.custom_fields,
                'documents': rfp.documents,
                'final_evaluation_score': float(rfp.final_evaluation_score) if rfp.final_evaluation_score else None,
                'award_decision_date': rfp.award_decision_date.isoformat() if rfp.award_decision_date else None,
                'award_justification': rfp.award_justification,
                'created_at': rfp.created_at.isoformat(),
                'updated_at': rfp.updated_at.isoformat(),
                'created_by': rfp.created_by,
                'approved_by': rfp.approved_by,
                'primary_reviewer_id': rfp.primary_reviewer_id,
                'executive_reviewer_id': rfp.executive_reviewer_id
            }
            
            # Create rollback version record
            rollback_version = RFPVersions.objects.create(
                version_id=rollback_version_id,
                rfp_id=rfp_id,
                version_number=version_number,
                version_label=f"Rollback to Version {version.version_number}",
                json_payload=current_payload,
                changes_summary=f"Rollback to version {version.version_number}",
                created_by=request.data.get('user_id', 1),
                created_by_name=request.data.get('user_name', 'System'),
                created_by_role=request.data.get('user_role', 'Administrator'),
                version_type='REVISION',
                parent_version_id=latest_version.version_id if latest_version else None,
                is_current=False,
                change_reason=rollback_reason
            )
            
            # Restore RFP from the target version
            version_data = version.json_payload
            rfp.rfp_title = version_data.get('rfp_title', rfp.rfp_title)
            rfp.description = version_data.get('description', rfp.description)
            rfp.rfp_type = version_data.get('rfp_type', rfp.rfp_type)
            rfp.category = version_data.get('category', rfp.category)
            rfp.estimated_value = version_data.get('estimated_value')
            rfp.currency = version_data.get('currency', rfp.currency)
            rfp.budget_range_min = version_data.get('budget_range_min')
            rfp.budget_range_max = version_data.get('budget_range_max')
            rfp.issue_date = version_data.get('issue_date')
            rfp.submission_deadline = version_data.get('submission_deadline')
            rfp.evaluation_period_end = version_data.get('evaluation_period_end')
            rfp.award_date = version_data.get('award_date')
            rfp.evaluation_method = version_data.get('evaluation_method', rfp.evaluation_method)
            rfp.criticality_level = version_data.get('criticality_level', rfp.criticality_level)
            rfp.geographical_scope = version_data.get('geographical_scope', rfp.geographical_scope)
            rfp.auto_approved = version_data.get('auto_approved', rfp.auto_approved)
            rfp.allow_late_submissions = version_data.get('allow_late_submissions', rfp.allow_late_submissions)
            rfp.compliance_requirements = version_data.get('compliance_requirements', rfp.compliance_requirements)
            rfp.custom_fields = version_data.get('custom_fields', rfp.custom_fields)
            rfp.version_number = version_number
            rfp.updated_at = timezone.now()
            
            rfp.save()
            
            # Mark the target version as current
            RFPVersions.objects.filter(rfp_id=rfp_id).update(is_current=False)
            version.is_current = True
            version.save()
            
            return Response({
                'success': True,
                'message': f'RFP rolled back to version {version.version_number}',
                'rfp': {
                    'rfp_id': rfp.rfp_id,
                    'version_number': rfp.version_number,
                    'updated_at': rfp.updated_at.isoformat()
                },
                'rollback_version': {
                    'version_id': rollback_version.version_id,
                    'version_number': rollback_version.version_number
                }
            })
            
    except Exception as e:
        print(f"Error rolling back RFP version: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': f'Failed to rollback RFP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_rfp_change_requests(request, rfp_id):
    """
    Get change requests for an RFP
    """
    try:
        # This would typically come from the approval workflow system
        # For now, we'll return a mock response
        change_requests = [
            {
                'id': f'CR_{rfp_id}_001',
                'requested_by': 'John Doe',
                'request_date': timezone.now().isoformat(),
                'description': 'Please update the budget range and add more specific requirements',
                'status': 'pending',
                'stage_id': 'STG_001',
                'approval_id': 'APP_001'
            }
        ]
        
        return Response({
            'success': True,
            'change_requests': change_requests
        })
        
    except Exception as e:
        print(f"Error getting RFP change requests: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to get change requests: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

