from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
import json

from .models import RFPEvaluatorAssignment, RFP, RFPResponse, CustomUser
from .rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission
from tprm_backend.rbac.tprm_decorators import rbac_rfp_required
from tprm_backend.rbac.tprm_utils import RBACTPRMUtils

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    require_tenant,
    tenant_filter
)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('assign_rfp_evaluators')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def bulk_assign_evaluators(request):
    """
    Bulk assign evaluators to multiple proposals
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        data = request.data
        
        # Validate required fields
        proposal_ids = data.get('proposal_ids', [])
        evaluator_ids = data.get('evaluator_ids', [])
        assignment_type = data.get('assignment_type', 'evaluation')
        assigned_by_id = data.get('assigned_by_id', 1)
        deadline_date = data.get('deadline_date')
        
        if not proposal_ids or not evaluator_ids:
            return Response({
                'error': 'Both proposal_ids and evaluator_ids are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate proposals exist
        # MULTI-TENANCY: Filter by tenant
        existing_proposals = RFPResponse.objects.filter(response_id__in=proposal_ids, tenant_id=tenant_id)
        if len(existing_proposals) != len(proposal_ids):
            return Response({
                'error': 'One or more proposals not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        created_assignments = []
        
        with transaction.atomic():
            for proposal_id in proposal_ids:
                for evaluator_id in evaluator_ids:
                    # Check if assignment already exists
                    # MULTI-TENANCY: Filter by tenant
                    existing_assignment = RFPEvaluatorAssignment.objects.filter(
                        proposal_id=proposal_id,
                        evaluator_id=evaluator_id,
                        assignment_type=assignment_type,
                        tenant_id=tenant_id
                    ).first()
                    
                    if existing_assignment:
                        print(f"Assignment already exists for proposal {proposal_id} and evaluator {evaluator_id}")
                        continue
                    
                    # Create new assignment
                    # MULTI-TENANCY: Set tenant_id on creation
                    assignment = RFPEvaluatorAssignment.objects.create(
                        proposal_id=proposal_id,
                        evaluator_id=evaluator_id,
                        assignment_type=assignment_type,
                        assigned_by_id=assigned_by_id,
                        assigned_date=timezone.now(),
                        deadline_date=deadline_date,
                        status='ASSIGNED',
                        tenant_id=tenant_id  # MULTI-TENANCY: Set tenant_id
                    )
                    
                    created_assignments.append({
                        'assignment_id': assignment.assignment_id,
                        'proposal_id': proposal_id,
                        'evaluator_id': evaluator_id,
                        'status': assignment.status
                    })
        
        return Response({
            'message': f'Successfully assigned {len(created_assignments)} evaluators to {len(proposal_ids)} proposals',
            'created_assignments': created_assignments,
            'total_assignments': len(created_assignments)
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to create bulk assignments: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_evaluator_assignments(request, evaluator_id):
    """
    Get all assignments for a specific evaluator
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # MULTI-TENANCY: Filter by tenant
        assignments = RFPEvaluatorAssignment.objects.filter(evaluator_id=evaluator_id, tenant_id=tenant_id)
        
        assignment_data = []
        for assignment in assignments:
            # MULTI-TENANCY: Filter by tenant
            try:
                proposal = RFPResponse.objects.get(response_id=assignment.proposal_id, tenant_id=tenant_id)
                assignment_data.append({
                    'assignment_id': assignment.assignment_id,
                    'proposal_id': assignment.proposal_id,
                    'proposal_title': proposal.vendor_name,
                    'assignment_type': assignment.assignment_type,
                    'status': assignment.status,
                    'assigned_date': assignment.assigned_date,
                    'deadline_date': assignment.deadline_date,
                    'notes': assignment.notes
                })
            except RFPResponse.DoesNotExist:
                # Skip assignments for proposals that no longer exist
                continue
        
        return Response({
            'evaluator_id': evaluator_id,
            'assignments': assignment_data,
            'total_assignments': len(assignment_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get evaluator assignments: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_proposal_assignments(request, proposal_id):
    """
    Get all evaluators assigned to a specific proposal
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # MULTI-TENANCY: Verify proposal belongs to tenant
        try:
            proposal = RFPResponse.objects.get(response_id=proposal_id, tenant_id=tenant_id)
        except RFPResponse.DoesNotExist:
            return Response({
                'error': f'Proposal not found: {proposal_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # MULTI-TENANCY: Filter by tenant
        assignments = RFPEvaluatorAssignment.objects.filter(proposal_id=proposal_id, tenant_id=tenant_id)
        
        assignment_data = []
        for assignment in assignments:
            assignment_data.append({
                'assignment_id': assignment.assignment_id,
                'evaluator_id': assignment.evaluator_id,
                'assignment_type': assignment.assignment_type,
                'status': assignment.status,
                'assigned_date': assignment.assigned_date,
                'deadline_date': assignment.deadline_date,
                'assigned_by_id': assignment.assigned_by_id,
                'notes': assignment.notes
            })
        
        return Response({
            'proposal_id': proposal_id,
            'assignments': assignment_data,
            'total_assignments': len(assignment_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to get proposal assignments: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('edit_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def update_assignment_status(request, assignment_id):
    """
    Update the status of a specific assignment
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        data = request.data
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if not new_status:
            return Response({
                'error': 'Status is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # MULTI-TENANCY: Filter by tenant
        try:
            assignment = RFPEvaluatorAssignment.objects.get(assignment_id=assignment_id, tenant_id=tenant_id)
        except RFPEvaluatorAssignment.DoesNotExist:
            return Response({
                'error': 'Assignment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update status and related fields
        assignment.status = new_status
        assignment.notes = notes
        assignment.updated_at = timezone.now()
        
        # Set started_date if transitioning to IN_PROGRESS
        if new_status == 'IN_PROGRESS' and not assignment.started_date:
            assignment.started_date = timezone.now()
        
        # Set completed_date if transitioning to COMPLETED
        if new_status == 'COMPLETED' and not assignment.completed_date:
            assignment.completed_date = timezone.now()
        
        assignment.save()
        
        return Response({
            'message': 'Assignment status updated successfully',
            'assignment_id': assignment_id,
            'new_status': new_status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to update assignment status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('delete_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def remove_assignment(request, assignment_id):
    """
    Remove a specific assignment
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # MULTI-TENANCY: Filter by tenant
        try:
            assignment = RFPEvaluatorAssignment.objects.get(assignment_id=assignment_id, tenant_id=tenant_id)
        except RFPEvaluatorAssignment.DoesNotExist:
            return Response({
                'error': 'Assignment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        assignment.delete()
        
        return Response({
            'message': 'Assignment removed successfully',
            'assignment_id': assignment_id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Failed to remove assignment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_available_evaluators(request):
    """
    Get list of available evaluators from the database.
    Returns all active users who can be assigned as evaluators.
    Optionally filters by users who have evaluation permissions via RBAC.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # Get all active users from CustomUser model
        # MULTI-TENANCY: Filter by tenant (if CustomUser has tenant_id field)
        # Note: Assuming CustomUser has tenant_id field, adjust if different
        active_users = CustomUser.objects.filter(is_active='Y').order_by('first_name', 'last_name')
        # If CustomUser has tenant_id: .filter(tenant_id=tenant_id)
        
        evaluators = []
        for user in active_users:
            # Check if user has evaluation permission (optional filter)
            # If RBAC is available, only include users with score_rfp_response permission
            try:
                has_evaluation_permission = RBACTPRMUtils.check_rfp_permission(
                    user.user_id, 
                    'score_rfp_response'
                )
            except Exception:
                # If RBAC check fails, include all active users
                has_evaluation_permission = True
            
            # Include user if they have permission or if RBAC check failed
            if has_evaluation_permission:
                # Get user's role from RBAC if available
                try:
                    rbac_record = RBACTPRMUtils.get_user_rbac_record(user.user_id)
                    role = rbac_record.role if rbac_record else 'User'
                except Exception:
                    role = 'User'
                
                evaluators.append({
                    'user_id': user.user_id,
                    'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'username': user.username,
                    'role': role,
                    'department': f"Department {user.department_id}" if user.department_id else 'N/A',
                    'email': user.email or f"{user.username}@company.com"
                })
        
        # If no evaluators found with permissions, return all active users as fallback
        if not evaluators:
            for user in active_users:
                evaluators.append({
                    'user_id': user.user_id,
                    'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'username': user.username,
                    'role': 'User',
                    'department': f"Department {user.department_id}" if user.department_id else 'N/A',
                    'email': user.email or f"{user.username}@company.com"
                })
        
        return Response({
            'evaluators': evaluators,
            'total_evaluators': len(evaluators)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Failed to get available evaluators: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
