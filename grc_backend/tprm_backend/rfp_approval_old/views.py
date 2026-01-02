"""
Views for RFP Approval Workflow Management
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection, transaction, models
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import uuid
import json
from .models import ApprovalWorkflows, ApprovalStages, ApprovalRequests, ApprovalComments, ApprovalRequestVersions
from rfp.models import RFP
from rfp.models import RFPResponse

# RBAC imports
from rbac.tprm_decorators import rbac_rfp_required
from rfp.rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission


def update_rfp_status_based_on_approval(approval_request):
    """
    Update RFP status based on approval request overall status
    Checks if ALL approval requests in the workflow have ALL stages approved
    This function is designed to be non-critical and won't throw exceptions
    """
    try:
        print(f"Updating RFP status for approval_id: {approval_request.approval_id}")
        print(f"Approval overall_status: {approval_request.overall_status}")
        
        # Find the RFP associated with this approval request
        # Try multiple methods to find the RFP
        rfp = None
        rfp_id = None
        
        # Method 1: Try to find RFP by approval_workflow_id (which matches the workflow_id in approval_requests)
        try:
            rfp = RFP.objects.get(approval_workflow_id=approval_request.workflow_id)
            rfp_id = rfp.rfp_id
            print(f"Found RFP by workflow_id: {rfp.rfp_id} with current status: {rfp.status}")
        except RFP.DoesNotExist:
            print(f"No RFP found for workflow_id: {approval_request.workflow_id}, trying request_data...")
            # Method 2: Try to extract RFP ID from request_data
            try:
                request_data = approval_request.request_data
                if isinstance(request_data, str):
                    request_data = json.loads(request_data)
                
                # Try different possible keys for RFP ID
                rfp_id = (
                    request_data.get('rfp_id') or
                    request_data.get('rfpId') or
                    request_data.get('id') or
                    None
                )
                
                # If it's an array, try to get from first item
                if not rfp_id and isinstance(request_data, list) and len(request_data) > 0:
                    first_item = request_data[0]
                    if isinstance(first_item, dict):
                        rfp_id = (
                            first_item.get('rfp_id') or
                            first_item.get('rfpId') or
                            first_item.get('id') or
                            None
                        )
                
                if rfp_id:
                    try:
                        rfp = RFP.objects.get(rfp_id=rfp_id)
                        print(f"Found RFP by rfp_id from request_data: {rfp.rfp_id} with current status: {rfp.status}")
                    except RFP.DoesNotExist:
                        print(f"RFP with rfp_id {rfp_id} not found in database")
                        rfp = None
            except Exception as data_error:
                print(f"Error extracting RFP ID from request_data: {str(data_error)}")
        
        # If still no RFP found, return
        if not rfp:
            print(f"⚠️  Could not find RFP for approval_id: {approval_request.approval_id}")
            print(f"    Tried workflow_id: {approval_request.workflow_id}")
            if rfp_id:
                print(f"    Tried rfp_id from request_data: {rfp_id}")
            return
        
        # Update RFP status based on approval overall status
        try:
            with transaction.atomic():
                old_status = rfp.status
                
                # Get ALL approval requests for this workflow
                all_approval_requests = ApprovalRequests.objects.filter(
                    workflow_id=approval_request.workflow_id
                )
                total_approval_requests = all_approval_requests.count()
                
                print(f"Checking workflow {approval_request.workflow_id}: {total_approval_requests} approval request(s)")
                
                # Check if any approval request is rejected
                rejected_approvals = all_approval_requests.filter(overall_status='REJECTED')
                if rejected_approvals.exists():
                    rfp.status = 'IN_REVIEW'  # RFP goes back to review for potential resubmission
                    print(f"RFP {rfp.rfp_id} status updated to IN_REVIEW (approval rejected)")
                
                # Check if ALL approval requests are approved AND all stages in each are approved
                elif total_approval_requests > 0:
                    all_approved = True
                    all_stages_approved = True
                    
                    # Check each approval request
                    for approval_req in all_approval_requests:
                        if approval_req.overall_status != 'APPROVED':
                            all_approved = False
                            print(f"  Approval request {approval_req.approval_id} status: {approval_req.overall_status} (not APPROVED)")
                            break
                        
                        # Double-check: Verify all stages in this approval request are approved
                        # Exclude SKIPPED and CANCELLED stages from the check (these don't count toward approval)
                        all_stages = ApprovalStages.objects.filter(approval_id=approval_req.approval_id)
                        # Only count stages that need to be processed (exclude SKIPPED and CANCELLED)
                        stages_to_process = all_stages.exclude(stage_status__in=['SKIPPED', 'CANCELLED'])
                        total_stages = stages_to_process.count()
                        
                        if total_stages > 0:
                            approved_stages_count = stages_to_process.filter(stage_status='APPROVED').count()
                            rejected_stages_count = stages_to_process.filter(stage_status='REJECTED').count()
                            pending_stages_count = stages_to_process.filter(stage_status__in=['PENDING', 'IN_PROGRESS']).count()
                            
                            print(f"  Approval request {approval_req.approval_id}: {approved_stages_count}/{total_stages} stages approved")
                            print(f"    Details: {approved_stages_count} approved, {rejected_stages_count} rejected, {pending_stages_count} pending/in_progress")
                            
                            # Check if all stages are approved (no rejected or pending stages)
                            if rejected_stages_count > 0:
                                all_stages_approved = False
                                print(f"    ❌ Not all stages approved: {rejected_stages_count} rejected stage(s) found")
                                break
                            elif pending_stages_count > 0:
                                all_stages_approved = False
                                print(f"    ⏳ Not all stages approved: {pending_stages_count} pending/in_progress stage(s) remaining")
                                break
                            elif approved_stages_count != total_stages:
                                all_stages_approved = False
                                print(f"    ⚠️  Not all stages approved: {approved_stages_count} approved out of {total_stages} total")
                                break
                    
                    # Only update RFP to APPROVED if ALL approval requests are approved AND all stages are approved
                    if all_approved and all_stages_approved:
                        rfp.status = 'APPROVED'
                        # Set approved_by to the last approver (from the most recently completed stage)
                        last_approved_stage = ApprovalStages.objects.filter(
                            approval_id__in=[ar.approval_id for ar in all_approval_requests],
                            stage_status='APPROVED'
                        ).order_by('-completed_at').first()
                        if last_approved_stage:
                            rfp.approved_by = last_approved_stage.assigned_user_id
                        print(f"✅ RFP {rfp.rfp_id} status updated to APPROVED (all {total_approval_requests} approval request(s) and all stages approved)")
                    else:
                        # If not all approved, set to IN_REVIEW if it was DRAFT
                        if rfp.status == 'DRAFT':
                            rfp.status = 'IN_REVIEW'
                            print(f"RFP {rfp.rfp_id} status updated to IN_REVIEW (approval in progress)")
                        else:
                            print(f"RFP {rfp.rfp_id} status unchanged: {rfp.status} (not all approvals/stages completed)")
                else:
                    # No approval requests found - handle based on current approval request status
                    if approval_request.overall_status == 'IN_PROGRESS':
                        # Keep status as is or set to IN_REVIEW if it was DRAFT
                        if rfp.status == 'DRAFT':
                            rfp.status = 'IN_REVIEW'
                            print(f"RFP {rfp.rfp_id} status updated to IN_REVIEW (approval in progress)")
                        else:
                            print(f"RFP {rfp.rfp_id} status unchanged: {rfp.status} (approval in progress)")
                
                # Only save if status changed
                if rfp.status != old_status:
                    rfp.updated_at = timezone.now()
                    rfp.save()
                    print(f"✅ RFP {rfp.rfp_id} status changed from {old_status} to {rfp.status}")
                else:
                    print(f"ℹ️  RFP {rfp.rfp_id} status unchanged: {rfp.status}")
                    
        except Exception as save_error:
            print(f"Error saving RFP status: {str(save_error)}")
            import traceback
            traceback.print_exc()
            # Don't re-raise the error - this is not critical
                
    except Exception as e:
        print(f"Error updating RFP status: {str(e)}")
        import traceback
        traceback.print_exc()
        # Don't re-raise the error - this is not critical for stage updates


def create_workflow_version(workflow_id, approval_ids, created_by, created_by_name=None, created_by_role=None, version_type='INITIAL', change_reason=None):
    """
    Create a version record for the approval workflow
    
    Args:
        workflow_id: The workflow ID
        approval_ids: List of approval request IDs
        created_by: User ID who created the workflow
        created_by_name: Name of the user who created the workflow
        created_by_role: Role of the user who created the workflow
        version_type: Type of version (INITIAL, REVISION, CONSOLIDATION, FINAL)
        change_reason: Reason for the change (if applicable)
    
    Returns:
        The created version record
    """
    try:
        print(f"Creating workflow version for workflow_id: {workflow_id}")
        
        # Get workflow details
        workflow = ApprovalWorkflows.objects.get(workflow_id=workflow_id)
        
        # Get all stages for this workflow
        all_stages = ApprovalStages.objects.filter(approval_id__in=approval_ids)
        
        # Prepare workflow data for version
        workflow_data = {
            'workflow_id': workflow.workflow_id,
            'workflow_name': workflow.workflow_name,
            'workflow_type': workflow.workflow_type,
            'description': workflow.description,
            'business_object_type': workflow.business_object_type,
            'is_active': workflow.is_active,
            'created_by': workflow.created_by,
            'created_at': workflow.created_at.isoformat(),
            'updated_at': workflow.updated_at.isoformat()
        }
        
        # Prepare approval requests data
        approval_requests_data = []
        for approval_id in approval_ids:
            try:
                approval_request = ApprovalRequests.objects.get(approval_id=approval_id)
                approval_requests_data.append({
                    'approval_id': approval_request.approval_id,
                    'workflow_id': approval_request.workflow_id,
                    'request_title': approval_request.request_title,
                    'request_description': approval_request.request_description,
                    'requester_id': approval_request.requester_id,
                    'requester_department': approval_request.requester_department,
                    'priority': approval_request.priority,
                    'request_data': approval_request.request_data,
                    'overall_status': approval_request.overall_status,
                    'submission_date': approval_request.submission_date.isoformat() if approval_request.submission_date else None,
                    'expiry_date': approval_request.expiry_date.isoformat() if approval_request.expiry_date else None,
                    'created_at': approval_request.created_at.isoformat(),
                    'updated_at': approval_request.updated_at.isoformat()
                })
            except ApprovalRequests.DoesNotExist:
                print(f"Warning: Approval request {approval_id} not found")
        
        # Prepare stages data
        stages_data = []
        for stage in all_stages:
            stages_data.append({
                'stage_id': stage.stage_id,
                'approval_id': stage.approval_id,
                'stage_order': stage.stage_order,
                'stage_name': stage.stage_name,
                'stage_description': stage.stage_description,
                'assigned_user_id': stage.assigned_user_id,
                'assigned_user_name': stage.assigned_user_name,
                'assigned_user_role': stage.assigned_user_role,
                'department': stage.department,
                'stage_type': stage.stage_type,
                'stage_status': stage.stage_status,
                'deadline_date': stage.deadline_date.isoformat() if stage.deadline_date else None,
                'is_mandatory': stage.is_mandatory,
                'created_at': stage.created_at.isoformat(),
                'updated_at': stage.updated_at.isoformat()
            })
        
        # Create complete JSON payload
        json_payload = {
            'workflow': workflow_data,
            'approval_requests': approval_requests_data,
            'stages': stages_data,
            'version_info': {
                'version_type': version_type,
                'created_at': timezone.now().isoformat(),
                'approval_count': len(approval_requests_data),
                'stage_count': len(stages_data)
            }
        }
        
        # Generate version ID
        version_id = f"VR_{uuid.uuid4().hex[:8].upper()}"
        
        # Get the next version number for this approval (if any)
        existing_versions = ApprovalRequestVersions.objects.filter(
            approval_id__in=approval_ids
        ).order_by('-version_number').first()
        
        version_number = (existing_versions.version_number + 1) if existing_versions else 1
        
        # Create version label
        version_label = f"Version {version_number} - {workflow.workflow_name}"
        
        # Create changes summary
        changes_summary = f"Created {workflow.workflow_name} workflow with {len(approval_requests_data)} approval request(s) and {len(stages_data)} stage(s)."
        if change_reason:
            changes_summary += f" Reason: {change_reason}"
        
        # Create version record
        version_record = ApprovalRequestVersions.objects.create(
            version_id=version_id,
            approval_id=approval_ids[0] if approval_ids else workflow_id,  # Use first approval_id or workflow_id
            version_number=version_number,
            version_label=version_label,
            json_payload=json_payload,
            changes_summary=changes_summary,
            created_by=created_by,
            created_by_name=created_by_name or f"User {created_by}",
            created_by_role=created_by_role or "User",
            version_type=version_type,
            is_current=True,
            is_approved=False,
            change_reason=change_reason
        )
        
        # Mark all previous versions as not current
        ApprovalRequestVersions.objects.filter(
            approval_id__in=approval_ids
        ).exclude(version_id=version_id).update(is_current=False)
        
        print(f"✅ Created workflow version {version_id} (v{version_number}) for workflow {workflow_id}")
        return version_record
        
    except Exception as e:
        print(f"Error creating workflow version: {str(e)}")
        import traceback
        traceback.print_exc()
        # Don't re-raise the error - version creation is not critical for workflow creation
        return None

def create_approval_version(approval_id, stage_id, old_status, new_status, user_id, user_name, user_role, change_reason=None, response_data=None):
    """
    Create a version record for an approval request when stage status changes
    
    Args:
        approval_id: The approval request ID
        stage_id: The stage ID that changed
        old_status: Previous stage status
        new_status: New stage status
        user_id: User ID who made the change
        user_name: Name of the user who made the change
        user_role: Role of the user who made the change
        change_reason: Reason for the change (if applicable)
        response_data: Response data from the stage change
    
    Returns:
        The created version record
    """
    try:
        import uuid
        from django.utils import timezone
        
        # Generate version ID
        version_id = f"VR_{uuid.uuid4().hex[:8].upper()}"
        
        # Get the latest version number for this approval
        latest_version = ApprovalRequestVersions.objects.filter(
            approval_id=approval_id
        ).order_by('-version_number').first()
        
        version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Determine version type based on status change
        version_type = 'REVISION'
        if new_status == 'APPROVED':
            version_type = 'FINAL'
        elif old_status == 'PENDING' and new_status == 'IN_PROGRESS':
            version_type = 'INITIAL'
        
        # Create comprehensive JSON payload
        try:
            # Get the approval request
            approval_request = ApprovalRequests.objects.get(approval_id=approval_id)
            
            # Get all stages for this approval
            all_stages = ApprovalStages.objects.filter(approval_id=approval_id)
            stages_data = []
            
            for stage in all_stages:
                stages_data.append({
                    'stage_id': stage.stage_id,
                    'stage_name': stage.stage_name,
                    'stage_status': stage.stage_status,
                    'assigned_user_id': stage.assigned_user_id,
                    'assigned_user_name': stage.assigned_user_name,
                    'assigned_user_role': stage.assigned_user_role,
                    'department': stage.department,
                    'stage_order': stage.stage_order,
                    'deadline_date': stage.deadline_date.isoformat() if stage.deadline_date else None,
                    'started_at': stage.started_at.isoformat() if stage.started_at else None,
                    'completed_at': stage.completed_at.isoformat() if stage.completed_at else None,
                    'response_data': stage.response_data,
                    'rejection_reason': stage.rejection_reason,
                    'is_mandatory': stage.is_mandatory
                })
            
            # Create comprehensive JSON payload
            json_payload = {
                'approval_id': approval_id,
                'workflow_id': approval_request.workflow_id,
                'request_title': approval_request.request_title,
                'request_description': approval_request.request_description,
                'requester_id': approval_request.requester_id,
                'requester_department': approval_request.requester_department,
                'priority': approval_request.priority,
                'overall_status': approval_request.overall_status,
                'request_data': approval_request.request_data,
                'stages': stages_data,
                'stage_change': {
                    'stage_id': stage_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'changed_by': {
                        'user_id': user_id,
                        'user_name': user_name,
                        'user_role': user_role
                    },
                    'change_timestamp': timezone.now().isoformat(),
                    'response_data': response_data
                },
                'version_metadata': {
                    'version_number': version_number,
                    'version_type': version_type,
                    'created_at': timezone.now().isoformat()
                }
            }
            
        except ApprovalRequests.DoesNotExist:
            # Fallback if approval request not found
            json_payload = {
                'approval_id': approval_id,
                'stage_change': {
                    'stage_id': stage_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'changed_by': {
                        'user_id': user_id,
                        'user_name': user_name,
                        'user_role': user_role
                    },
                    'change_timestamp': timezone.now().isoformat(),
                    'response_data': response_data
                },
                'version_metadata': {
                    'version_number': version_number,
                    'version_type': version_type,
                    'created_at': timezone.now().isoformat()
                }
            }
        
        # Create changes summary
        changes_summary = f"Stage status changed from {old_status} to {new_status}"
        if change_reason:
            changes_summary += f" - {change_reason}"
        
        # Create version record
        version_data = {
            'version_id': version_id,
            'approval_id': approval_id,
            'version_number': version_number,
            'version_label': f"Stage {stage_id} - {new_status}",
            'json_payload': json_payload,
            'changes_summary': changes_summary,
            'created_by': user_id,
            'created_by_name': user_name,
            'created_by_role': user_role,
            'version_type': version_type,
            'parent_version_id': latest_version.version_id if latest_version else None,
            'is_current': True,
            'is_approved': new_status == 'APPROVED',
            'change_reason': change_reason or f"Stage status change: {old_status} → {new_status}",
            'created_at': timezone.now()
        }
        
        # Mark previous versions as not current
        ApprovalRequestVersions.objects.filter(
            approval_id=approval_id
        ).update(is_current=False)
        
        # Create new version
        version = ApprovalRequestVersions.objects.create(**version_data)
        
        print(f"✅ Created approval version {version_number} for approval {approval_id} - Stage {stage_id}: {old_status} → {new_status}")
        return version
        
    except Exception as e:
        print(f"❌ Error creating approval version: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def get_approval_version_history(approval_id):
    """
    Get version history for an approval request
    
    Args:
        approval_id: The approval request ID
    
    Returns:
        List of version records
    """
    try:
        versions = ApprovalRequestVersions.objects.filter(
            approval_id=approval_id
        ).order_by('-version_number')
        
        version_history = []
        for version in versions:
            version_history.append({
                'version_id': version.version_id,
                'version_number': version.version_number,
                'version_label': version.version_label,
                'version_type': version.version_type,
                'changes_summary': version.changes_summary,
                'created_by_name': version.created_by_name,
                'created_by_role': version.created_by_role,
                'is_current': version.is_current,
                'is_approved': version.is_approved,
                'change_reason': version.change_reason,
                'created_at': version.created_at,
                'parent_version_id': version.parent_version_id
            })
        
        return version_history
        
    except Exception as e:
        print(f"❌ Error getting approval version history: {str(e)}")
        return []


@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def workflows(request):
    """
    Handle workflow creation and retrieval
    """
    if request.method == 'GET':
        # Get all workflows
        workflows = ApprovalWorkflows.objects.all()
        workflow_data = []
        
        for workflow in workflows:
            # Get stages for each workflow
            stages = ApprovalStages.objects.filter(approval_id=workflow.workflow_id)
            stages_data = []
            
            for stage in stages:
                stages_data.append({
                    'stage_id': stage.stage_id,
                    'stage_order': stage.stage_order,
                    'stage_name': stage.stage_name,
                    'stage_description': stage.stage_description,
                    'assigned_user_id': stage.assigned_user_id,
                    'assigned_user_name': stage.assigned_user_name,
                    'assigned_user_role': stage.assigned_user_role,
                    'department': stage.department,
                    'stage_type': stage.stage_type,
                    'stage_status': stage.stage_status,
                    'deadline_date': stage.deadline_date,
                    'is_mandatory': stage.is_mandatory
                })
            
            workflow_data.append({
                'workflow_id': workflow.workflow_id,
                'workflow_name': workflow.workflow_name,
                'workflow_type': workflow.workflow_type,
                'description': workflow.description,
                'business_object_type': workflow.business_object_type,
                'is_active': workflow.is_active,
                'created_by': workflow.created_by,
                'created_at': workflow.created_at,
                'updated_at': workflow.updated_at,
                'stages': stages_data
            })
        
        return Response(workflow_data)
    
    elif request.method == 'POST':
        try:
            # Extract workflow data
            workflow_data = request.data.copy()
            stages_config = workflow_data.pop('stages_config', [])
            rfp_data = workflow_data.pop('rfp_data', None)
            
            # Validate minimum stages requirement
            if len(stages_config) < 2:
                return Response({
                    'error': 'At least two stages are required for a workflow'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate workflow ID
            workflow_id = f"WF_{uuid.uuid4().hex[:8].upper()}"
            workflow_data['workflow_id'] = workflow_id
            
            # Create workflow
            workflow = ApprovalWorkflows.objects.create(**workflow_data)
            
            # Create stages only for single-RFP workflows.
            # For bulk proposal evaluation, committee evaluation, and RFP creation we create stages per approval request below; 
            # adding them here would duplicate stages at workflow level.
            create_workflow_level_stages = True
            try:
                # Check if this is a workflow that should NOT have workflow-level stages
                wf_type_hint = None
                if rfp_data:
                    wf_type_hint = rfp_data.get('workflow_type') or rfp_data.get('workflow_type_hint')
                
                business_object_type = workflow_data.get('business_object_type', '')
                
                print(f"[DEBUG] Workflow type hint from rfp_data: {wf_type_hint}")
                print(f"[DEBUG] business_object_type: {business_object_type}")
                print(f"[DEBUG] Has rfp_data: {rfp_data is not None}")
                
                # IMPORTANT: If rfp_data exists, it means this is an RFP-related workflow
                # RFP-related workflows should ONLY have request-level stages, NOT workflow-level stages
                if rfp_data is not None:
                    create_workflow_level_stages = False
                    print(f"[DEBUG] Skipping workflow-level stages - RFP data detected (workflow is RFP-related)")
                
                # Skip workflow-level stages for bulk proposal evaluation
                elif wf_type_hint == 'bulk_proposal_evaluation':
                    create_workflow_level_stages = False
                    print(f"[DEBUG] Skipping workflow-level stages for bulk_proposal_evaluation")
                
                # Skip workflow-level stages for committee evaluation (create only approval request stages)
                elif business_object_type == 'Committee Evaluation':
                    create_workflow_level_stages = False
                    print(f"[DEBUG] Skipping workflow-level stages for Committee Evaluation")
                
            except Exception as e:
                print(f"[DEBUG] Exception in workflow type check: {e}")
                import traceback
                traceback.print_exc()
                create_workflow_level_stages = True

            print(f"[DEBUG] FINAL DECISION: create_workflow_level_stages = {create_workflow_level_stages}")
            if create_workflow_level_stages:
                print(f"[WARNING] Creating workflow-level stages for workflow {workflow_id}")
                for stage_config in stages_config:
                    stage_id = f"ST_{uuid.uuid4().hex[:8].upper()}"

                    stage_data = {
                        'stage_id': stage_id,
                        'approval_id': workflow_id,
                        'stage_order': stage_config.get('stage_order', 1),
                        'stage_name': stage_config.get('stage_name', ''),
                        'stage_description': stage_config.get('stage_description', ''),
                        'assigned_user_id': stage_config.get('assigned_user_id', ''),
                        'assigned_user_name': stage_config.get('assigned_user_name', ''),
                        'assigned_user_role': stage_config.get('assigned_user_role', ''),
                        'department': stage_config.get('department', ''),
                        'stage_type': stage_config.get('stage_type', 'SEQUENTIAL'),
                        'stage_status': 'PENDING',
                        'deadline_date': stage_config.get('deadline_date'),
                        'is_mandatory': stage_config.get('is_mandatory', True),
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    }

                    ApprovalStages.objects.create(**stage_data)
            
            # Create approval requests based on workflow type
            approval_ids = []
            if rfp_data:
                workflow_type = rfp_data.get('workflow_type', '')
                selected_proposals = rfp_data.get('selected_proposals', [])
                
                # Check if this is a bulk proposal evaluation workflow
                if workflow_type == 'bulk_proposal_evaluation' and selected_proposals:
                    print(f"Creating bulk proposal evaluation workflow for {len(selected_proposals)} proposals")
                    
                    # Create separate approval request for each proposal
                    for proposal in selected_proposals:
                        approval_id = f"AR_{uuid.uuid4().hex[:8].upper()}"
                        
                        # Calculate expiry date (30 days from now by default)
                        expiry_date = timezone.now() + timezone.timedelta(days=30)
                        
                        # Determine priority based on RFP criticality
                        priority_map = {
                            'low': 'LOW',
                            'medium': 'MEDIUM', 
                            'high': 'HIGH',
                            'urgent': 'URGENT'
                        }
                        priority = priority_map.get(rfp_data.get('criticality_level', 'medium').lower(), 'MEDIUM')
                        
                        # Create approval request for this specific proposal
                        approval_request_data = {
                            'approval_id': approval_id,
                            'workflow_id': workflow_id,
                            'request_title': f"Proposal Evaluation: {proposal.get('vendor_name', 'Unknown Vendor')} - {rfp_data.get('rfp_title', 'Untitled RFP')}",
                            'request_description': f"Evaluation of proposal from {proposal.get('vendor_name', 'Unknown Vendor')} for RFP: {rfp_data.get('rfp_title', 'Untitled RFP')}",
                            'requester_id': workflow_data.get('created_by', 1),
                            'requester_department': rfp_data.get('category', 'General'),
                            'priority': priority,
                            'request_data': json.dumps({
                                **rfp_data,
                                'proposal_id': proposal.get('response_id'),
                                'proposal_data': proposal
                            }),
                            'overall_status': 'DRAFT',
                            'submission_date': timezone.now(),
                            'expiry_date': expiry_date,
                            'created_at': timezone.now(),
                            'updated_at': timezone.now()
                        }
                        
                        ApprovalRequests.objects.create(**approval_request_data)
                        approval_ids.append(approval_id)
                        print(f"Created approval request for proposal {proposal.get('response_id')}: {approval_id}")
                        
                        # Create one stage per evaluator for this proposal (parallel)
                        # Each evaluator gets one evaluation task per proposal
                        for stage_config in stages_config:
                            stage_id = f"ST_{uuid.uuid4().hex[:8].upper()}"
                            
                            # Prepare stage data with proposal-specific information
                            stage_data = {
                                'stage_id': stage_id,
                                'approval_id': approval_id,
                                'stage_order': stage_config.get('stage_order', 1),
                                'stage_name': f"{stage_config.get('stage_name', '')} - {proposal.get('vendor_name', 'Unknown')}",
                                'stage_description': f"{stage_config.get('stage_description', '')} for proposal from {proposal.get('vendor_name', 'Unknown Vendor')}",
                                'assigned_user_id': stage_config.get('assigned_user_id', ''),
                                'assigned_user_name': stage_config.get('assigned_user_name', ''),
                                'assigned_user_role': stage_config.get('assigned_user_role', ''),
                                'department': stage_config.get('department', ''),
                                'stage_type': 'PARALLEL',  # All evaluators work in parallel
                                'stage_status': 'PENDING',
                                'deadline_date': stage_config.get('deadline_date'),
                                'is_mandatory': stage_config.get('is_mandatory', True),
                                'created_at': timezone.now(),
                                'updated_at': timezone.now()
                            }
                            
                            # Create stage for this proposal
                            ApprovalStages.objects.create(**stage_data)
                            print(f"Created evaluation stage {stage_id} for proposal {proposal.get('response_id')} - Evaluator: {stage_config.get('assigned_user_name')} ({stage_config.get('stage_name')})")
                
                elif workflow_data.get('business_object_type') == 'Committee Evaluation':
                    # Handle committee evaluation workflow
                    print(f"Creating committee evaluation workflow for RFP {rfp_data.get('rfp_id')}")
                    
                    # Create single approval request for committee evaluation
                    approval_id = f"AR_{uuid.uuid4().hex[:8].upper()}"
                    
                    # Calculate expiry date (30 days from now by default)
                    expiry_date = timezone.now() + timezone.timedelta(days=30)
                    
                    # Create approval request for committee evaluation
                    approval_request_data = {
                        'approval_id': approval_id,
                        'workflow_id': workflow_id,
                        'request_title': f"Committee Evaluation - RFP {rfp_data.get('rfp_id')}",
                        'request_description': f"Final committee evaluation and ranking of shortlisted proposals for RFP {rfp_data.get('rfp_id')}",
                        'requester_id': workflow_data.get('created_by', 1),
                        'requester_department': 'Committee',
                        'priority': 'HIGH',
                        'request_data': json.dumps(rfp_data),
                        'overall_status': 'PENDING',
                        'submission_date': timezone.now(),
                        'expiry_date': expiry_date,
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    }
                    
                    ApprovalRequests.objects.create(**approval_request_data)
                    approval_ids.append(approval_id)
                    print(f"Created committee evaluation approval request: {approval_id}")
                    
                    # Create stages for each committee member (parallel execution)
                    for stage_config in stages_config:
                        stage_id = f"ST_{uuid.uuid4().hex[:8].upper()}"
                        
                        # Prepare stage data
                        stage_data = {
                            'stage_id': stage_id,
                            'approval_id': approval_id,
                            'stage_order': stage_config.get('stage_order', 0),  # All stages run in parallel
                            'stage_name': stage_config.get('stage_name', ''),
                            'stage_description': stage_config.get('stage_description', ''),
                            'assigned_user_id': stage_config.get('assigned_user_id', ''),
                            'assigned_user_name': stage_config.get('assigned_user_name', ''),
                            'assigned_user_role': stage_config.get('assigned_user_role', ''),
                            'department': stage_config.get('department', 'Committee'),
                            'stage_type': 'PARALLEL',  # All committee members work in parallel
                            'stage_status': 'PENDING',
                            'deadline_date': stage_config.get('deadline_date'),
                            'is_mandatory': stage_config.get('is_mandatory', True),
                            'created_at': timezone.now(),
                            'updated_at': timezone.now()
                        }
                        
                        # Create stage for committee member
                        ApprovalStages.objects.create(**stage_data)
                        print(f"Created committee evaluation stage for user {stage_config.get('assigned_user_id')}: {stage_id}")
                
                else:
                    # Single RFP approval request (existing logic)
                    existing_request = ApprovalRequests.objects.filter(workflow_id=workflow_id).first()
                    if existing_request:
                        approval_id = existing_request.approval_id
                        approval_ids.append(approval_id)
                        print(f"Approval request already exists for workflow {workflow_id}: {approval_id}")
                    else:
                        approval_id = f"AR_{uuid.uuid4().hex[:8].upper()}"
                        
                        # Calculate expiry date (30 days from now by default)
                        expiry_date = timezone.now() + timezone.timedelta(days=30)
                        
                        # Determine priority based on RFP criticality
                        priority_map = {
                            'low': 'LOW',
                            'medium': 'MEDIUM', 
                            'high': 'HIGH',
                            'urgent': 'URGENT'
                        }
                        priority = priority_map.get(rfp_data.get('criticality_level', 'medium').lower(), 'MEDIUM')
                        
                        # Create approval request
                        approval_request_data = {
                            'approval_id': approval_id,
                            'workflow_id': workflow_id,
                            'request_title': f"RFP Approval: {rfp_data.get('rfp_title', 'Untitled RFP')}",
                            'request_description': rfp_data.get('description', 'RFP approval request'),
                            'requester_id': workflow_data.get('created_by', 1),
                            'requester_department': rfp_data.get('category', 'General'),
                            'priority': priority,
                            'request_data': json.dumps(rfp_data),
                            'overall_status': 'DRAFT',
                            'submission_date': timezone.now(),
                            'expiry_date': expiry_date,
                            'created_at': timezone.now(),
                            'updated_at': timezone.now()
                        }
                        
                        ApprovalRequests.objects.create(**approval_request_data)
                        approval_ids.append(approval_id)
                        print(f"Created new approval request for workflow {workflow_id}: {approval_id}")
                        
                        # Create stages for the single RFP (request-level stages)
                        print(f"[INFO] Creating request-level stages for approval request {approval_id}")
                        for stage_config in stages_config:
                            stage_id = f"ST_{uuid.uuid4().hex[:8].upper()}"
                            
                            # Prepare stage data
                            stage_data = {
                                'stage_id': stage_id,
                                'approval_id': approval_id,
                                'stage_order': stage_config.get('stage_order', 1),
                                'stage_name': stage_config.get('stage_name', ''),
                                'stage_description': stage_config.get('stage_description', ''),
                                'assigned_user_id': stage_config.get('assigned_user_id', ''),
                                'assigned_user_name': stage_config.get('assigned_user_name', ''),
                                'assigned_user_role': stage_config.get('assigned_user_role', ''),
                                'department': stage_config.get('department', ''),
                                'stage_type': stage_config.get('stage_type', 'SEQUENTIAL'),
                                'stage_status': 'PENDING',
                                'deadline_date': stage_config.get('deadline_date'),
                                'is_mandatory': stage_config.get('is_mandatory', True),
                                'created_at': timezone.now(),
                                'updated_at': timezone.now()
                            }
                            
                            # Create stage
                            ApprovalStages.objects.create(**stage_data)
                    
                    # Create or update RFP record with approval_workflow_id (only for single RFP)
                    try:
                        # Try to find existing RFP by title or create new one
                        rfp_title = rfp_data.get('rfp_title', 'Untitled RFP')
                        rfp, created = RFP.objects.get_or_create(
                            rfp_title=rfp_title,
                            defaults={
                                'description': rfp_data.get('description', 'RFP description'),
                                'rfp_type': rfp_data.get('rfp_type', 'SERVICES'),
                                'category': rfp_data.get('category', 'General'),
                                'estimated_value': rfp_data.get('estimated_value'),
                                'currency': rfp_data.get('currency', 'USD'),
                                'criticality_level': rfp_data.get('criticality_level', 'medium'),
                                'created_by': workflow_data.get('created_by', 1),
                                'status': 'DRAFT',
                                'approval_workflow_id': workflow_id
                            }
                        )
                        
                        if not created:
                            # Update existing RFP with approval_workflow_id
                            rfp.approval_workflow_id = workflow_id
                            rfp.updated_at = timezone.now()
                            rfp.save()
                            print(f"Updated existing RFP {rfp.rfp_id} with approval_workflow_id: {workflow_id}")
                        else:
                            print(f"Created new RFP {rfp.rfp_id} with approval_workflow_id: {workflow_id}")
                            
                    except Exception as rfp_error:
                        print(f"Warning: Failed to create/update RFP record: {str(rfp_error)}")
                        # Continue without failing the workflow creation
            
            # Create workflow version record
            try:
                created_by_name = workflow_data.get('created_by_name', None)
                created_by_role = workflow_data.get('created_by_role', None)
                created_by = workflow_data.get('created_by', 1)
                
                version_record = create_workflow_version(
                    workflow_id=workflow_id,
                    approval_ids=approval_ids,
                    created_by=created_by,
                    created_by_name=created_by_name,
                    created_by_role=created_by_role,
                    version_type='INITIAL',
                    change_reason='Initial workflow creation'
                )
                
                if version_record:
                    print(f"✅ Workflow version created: {version_record.version_id}")
                else:
                    print(f"⚠️ Failed to create workflow version")
            except Exception as version_error:
                print(f"⚠️ Error creating workflow version: {str(version_error)}")
                # Don't fail the workflow creation if version creation fails
                import traceback
                traceback.print_exc()
            
            response_data = {
                'workflow_id': workflow_id,
                'message': 'Workflow created successfully',
                'stages_count': len(stages_config)
            }
            
            if approval_ids:
                if len(approval_ids) == 1:
                    response_data['approval_id'] = approval_ids[0]
                    response_data['message'] = 'Workflow and approval request created successfully'
                else:
                    response_data['approval_ids'] = approval_ids
                    response_data['approval_count'] = len(approval_ids)
                    response_data['message'] = f'Workflow created successfully with {len(approval_ids)} approval requests'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create workflow: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def users(request):
    """
    Get all users for dropdown selection
    Filtered based on workflow_type:
    - For 'rfp_creation': Only Management and Executive roles
    - For other workflows: Admin, System Owner, Procurement, Sourcing, Management, Executive
    """
    try:
        # Import required models
        from rfp.models import CustomUser
        from django.contrib.auth.models import User
        import django.db as db
        
        # Get workflow_type from query parameters
        workflow_type = request.query_params.get('workflow_type', '')
        
        # Get all active users from the database
        all_users = CustomUser.objects.filter(is_active='Y').order_by('first_name', 'last_name')
        
        # Determine which roles to filter by based on workflow_type
        if workflow_type == 'rfp_creation':
            # For RFP creation: Only Management and Executive
            allowed_roles = ['Management', 'Executive']
        else:
            # For other workflows: Admin, System Owner, Procurement, Sourcing, Management, Executive
            allowed_roles = ['Admin', 'System Owner', 'Procurement', 'Sourcing', 'Management', 'Executive']
        
        print(f"Workflow type: {workflow_type}")
        print(f"Allowed roles: {allowed_roles}")
        
        # Get user IDs with allowed roles from rbac_tprm
        with connection.cursor() as cursor:
            # Build the SQL IN clause dynamically
            placeholders = ','.join(['%s'] * len(allowed_roles))
            query = f"""
                SELECT DISTINCT UserId 
                FROM rbac_tprm 
                WHERE Role IN ({placeholders}) 
                AND IsActive = 'Y'
            """
            cursor.execute(query, allowed_roles)
            allowed_user_ids = [row[0] for row in cursor.fetchall()]
        
        # Filter users based on allowed roles
        users_data = []
        print(f"Total users in database: {all_users.count()}")
        print(f"Users with allowed roles: {len(allowed_user_ids)}")
        
        for user in all_users:
            # Check if user has an allowed role in rbac_tprm
            if user.user_id in allowed_user_ids:
                # Get user's role from rbac_tprm
                user_role = 'User'  # Default
                with connection.cursor() as cursor:
                    placeholders = ','.join(['%s'] * len(allowed_roles))
                    query = f"""
                        SELECT Role 
                        FROM rbac_tprm 
                        WHERE UserId = %s 
                        AND Role IN ({placeholders})
                        LIMIT 1
                    """
                    cursor.execute(query, [user.user_id] + allowed_roles)
                    result = cursor.fetchone()
                    if result:
                        user_role = result[0]
                
                # Only add users who have an allowed role
                user_data = {
                    'id': str(user.user_id),  # Convert to string for consistency
                    'username': user.username,
                    'first_name': user.first_name or 'Unknown',
                    'last_name': user.last_name or 'User',
                    'email': user.email or '',
                    'role': user_role,
                    'department': f'Department {user.department_id}' if user.department_id else 'General',
                    'is_active': user.is_active == 'Y'
                }
                users_data.append(user_data)
                print(f"Added user: {user_data['first_name']} {user_data['last_name']} ({user_role})")
        
        print(f"Total users returned: {len(users_data)}")
        return Response(users_data)
        
    except Exception as e:
        # Fallback to mock data if database query fails
        print(f"Error fetching users from database: {e}")
        import traceback
        traceback.print_exc()
        users_data = [
            {
                'id': '1',
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'email': 'admin@company.com',
                'role': 'Executive',
                'department': 'IT',
                'is_active': True
            },
            {
                'id': '2',
                'username': 'manager',
                'first_name': 'Manager',
                'last_name': 'User',
                'email': 'manager@company.com',
                'role': 'Management',
                'department': 'Operations',
                'is_active': True
            }
        ]
        return Response(users_data)


@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('approve_rfp')
def approval_requests(request):
    """
    Handle approval request creation and retrieval
    """
    if request.method == 'GET':
        workflow_id = request.query_params.get('workflow_id')
        
        if workflow_id:
            requests = ApprovalRequests.objects.filter(workflow_id=workflow_id)
        else:
            requests = ApprovalRequests.objects.all()
        
        request_data = []
        
        for req in requests:
            # Initialize with request data
            req_data = {
                'approval_id': req.approval_id,
                'workflow_id': req.workflow_id,
                'request_title': req.request_title,
                'request_description': req.request_description,
                'requester_id': req.requester_id,
                'requester_department': req.requester_department,
                'priority': req.priority,
                'overall_status': req.overall_status,
                'submission_date': req.submission_date,
                'completion_date': req.completion_date,
                'expiry_date': req.expiry_date,
                'request_data': req.request_data,
                'created_at': req.created_at,
                'updated_at': req.updated_at,
                
                # Default workflow values
                'workflow_name': 'Default Workflow',
                'workflow_type': 'SEQUENTIAL',
                'business_object_type': 'RFP'
            }
            
            # Try to get workflow details
            try:
                workflow = ApprovalWorkflows.objects.get(workflow_id=req.workflow_id)
                req_data.update({
                    'workflow_name': workflow.workflow_name,
                    'workflow_type': workflow.workflow_type,
                    'business_object_type': workflow.business_object_type,
                })
            except ApprovalWorkflows.DoesNotExist:
                pass  # Keep default workflow values
            
            request_data.append(req_data)
        
        return Response(request_data)
    
    elif request.method == 'POST':
        try:
            # Generate approval ID
            approval_id = f"AR_{uuid.uuid4().hex[:8].upper()}"
            
            # Create approval request
            request_data = request.data.copy()
            request_data['approval_id'] = approval_id
            
            approval_request = ApprovalRequests.objects.create(**request_data)
            
            return Response({
                'approval_id': approval_id,
                'message': 'Approval request created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create approval request: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('approve_rfp')
def stages(request):
    """
    Handle stage management
    """
    if request.method == 'GET':
        approval_id = request.query_params.get('approval_id')
        
        if approval_id:
            stages = ApprovalStages.objects.filter(approval_id=approval_id)
        else:
            stages = ApprovalStages.objects.all()
        
        stage_data = []
        for stage in stages:
            stage_data.append({
                'stage_id': stage.stage_id,
                'approval_id': stage.approval_id,
                'stage_order': stage.stage_order,
                'stage_name': stage.stage_name,
                'stage_description': stage.stage_description,
                'assigned_user_id': stage.assigned_user_id,
                'assigned_user_name': stage.assigned_user_name,
                'assigned_user_role': stage.assigned_user_role,
                'department': stage.department,
                'stage_type': stage.stage_type,
                'stage_status': stage.stage_status,
                'deadline_date': stage.deadline_date,
                'extended_deadline': stage.extended_deadline,
                'extension_reason': stage.extension_reason,
                'started_at': stage.started_at,
                'completed_at': stage.completed_at,
                'response_data': stage.response_data,
                'rejection_reason': stage.rejection_reason,
                'escalation_level': stage.escalation_level,
                'is_mandatory': stage.is_mandatory,
                'created_at': stage.created_at,
                'updated_at': stage.updated_at
            })
        
        return Response(stage_data)
    
    elif request.method == 'POST':
        try:
            # Generate stage ID
            stage_id = f"ST_{uuid.uuid4().hex[:8].upper()}"
            
            # Create stage
            stage_data = request.data.copy()
            stage_data['stage_id'] = stage_id
            
            stage = ApprovalStages.objects.create(**stage_data)
            
            return Response({
                'stage_id': stage_id,
                'message': 'Stage created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create stage: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def comments(request):
    """
    Handle approval comments
    """
    if request.method == 'GET':
        approval_id = request.query_params.get('approval_id')
        stage_id = request.query_params.get('stage_id')
        
        comments = ApprovalComments.objects.all()
        
        if approval_id:
            comments = comments.filter(approval_id=approval_id)
        if stage_id:
            comments = comments.filter(stage_id=stage_id)
        
        comment_data = []
        for comment in comments:
            comment_data.append({
                'comment_id': comment.comment_id,
                'approval_id': comment.approval_id,
                'stage_id': comment.stage_id,
                'parent_comment_id': comment.parent_comment_id,
                'comment_text': comment.comment_text,
                'comment_type': comment.comment_type,
                'commented_by': comment.commented_by,
                'commented_by_name': comment.commented_by_name,
                'is_internal': comment.is_internal,
                'created_at': comment.created_at
            })
        
        return Response(comment_data)
    
    elif request.method == 'POST':
        try:
            # Generate comment ID
            comment_id = f"CM_{uuid.uuid4().hex[:8].upper()}"
            
            # Create comment
            comment_data = request.data.copy()
            comment_data['comment_id'] = comment_id
            
            comment = ApprovalComments.objects.create(**comment_data)
            
            return Response({
                'comment_id': comment_id,
                'message': 'Comment created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create comment: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_proposal_id_from_approval(request, approval_id):
    """
    Get proposal/response ID from approval request data
    For proposal evaluation workflows, we need to find response IDs for the RFP
    """
    try:
        # Get approval request
        approval_request = ApprovalRequests.objects.get(approval_id=approval_id)
        
        # Parse request_data to find RFP ID
        request_data = approval_request.request_data
        if isinstance(request_data, str):
            try:
                request_data = json.loads(request_data)
            except json.JSONDecodeError:
                return Response({'error': 'Invalid request_data format'}, status=400)
        
        # Handle case where request_data is a list (array of proposals)
        if isinstance(request_data, list) and len(request_data) > 0:
            # For proposal evaluation, the first item should contain the response_id
            first_proposal = request_data[0]
            if isinstance(first_proposal, dict):
                proposal_id = first_proposal.get('response_id')
                if proposal_id:
                    return Response({
                        'proposal_id': proposal_id,
                        'all_response_ids': [item.get('response_id') for item in request_data if item.get('response_id')],
                        'approval_id': approval_id,
                        'request_data': request_data
                    })
        
        # First, try to find direct response_id in request_data (for dict format)
        proposal_id = None
        if isinstance(request_data, dict):
            proposal_id = (request_data.get('response_id') or 
                          request_data.get('proposal_id') or 
                          request_data.get('rfp_response_id') or
                          request_data.get('id') or
                          request_data.get('proposalId') or
                          request_data.get('responseId'))
        
        # If no direct response_id found, try to get RFP ID and find responses
        if not proposal_id and isinstance(request_data, dict):
            rfp_id = request_data.get('rfp_id')
            if rfp_id:
                # Import here to avoid circular imports
                from rfp.models import RFPResponse
                
                # Get all responses for this RFP
                responses = RFPResponse.objects.filter(rfp_id=rfp_id)
                
                if responses.exists():
                    # For now, return the first response ID
                    # In a real implementation, you might want to filter by evaluator assignment
                    first_response = responses.first()
                    proposal_id = first_response.response_id
                    
                    # Also return all response IDs for potential selection
                    all_response_ids = list(responses.values_list('response_id', flat=True))
                    
                    return Response({
                        'proposal_id': proposal_id,
                        'all_response_ids': all_response_ids,
                        'rfp_id': rfp_id,
                        'approval_id': approval_id,
                        'request_data': request_data
                    })
        
        if not proposal_id:
            return Response({'error': 'No proposal ID found in approval data'}, status=404)
        
        return Response({
            'proposal_id': proposal_id,
            'approval_id': approval_id,
            'request_data': request_data
        })
        
    except ApprovalRequests.DoesNotExist:
        return Response({'error': 'Approval request not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def user_approvals(request):
    """
    Get all approval stages assigned to a specific user
    """
    user_id = request.query_params.get('user_id')
    
    if not user_id:
        return Response({
            'error': 'user_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Convert user_id to integer for database query
        try:
            user_id_int = int(user_id)
        except ValueError:
            return Response({
                'error': 'user_id must be a valid integer'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all stages assigned to the user
        stages = ApprovalStages.objects.filter(assigned_user_id=user_id_int)
        
        approval_data = []
        for stage in stages:
            # Initialize with stage data
            stage_data = {
                'stage_id': stage.stage_id,
                'approval_id': stage.approval_id,
                'stage_order': stage.stage_order,
                'stage_name': stage.stage_name,
                'stage_description': stage.stage_description,
                'stage_status': stage.stage_status,
                'stage_type': stage.stage_type,
                'deadline_date': stage.deadline_date,
                'started_at': stage.started_at,
                'completed_at': stage.completed_at,
                'is_mandatory': stage.is_mandatory,
                'escalation_level': stage.escalation_level,
                'rejection_reason': stage.rejection_reason,
                'response_data': stage.response_data,
                
                # Default values for approval request details
                'request_title': f'Approval Request {stage.approval_id}',
                'request_description': stage.stage_description or 'No description available',
                'requester_id': None,
                'requester_department': 'Unknown',
                'priority': 'MEDIUM',
                'overall_status': stage.stage_status,
                'submission_date': stage.created_at,
                'completion_date': stage.completed_at,
                'expiry_date': stage.deadline_date,
                'request_data': None,
                
                # Default values for workflow details
                'workflow_name': 'Default Workflow',
                'workflow_type': 'SEQUENTIAL',
                'business_object_type': 'RFP',
                
                # Timestamps
                'created_at': stage.created_at,
                'updated_at': stage.updated_at
            }
            
            # Try to get approval request details if they exist
            # NOTE: approval_id in approval_stages table references approval_id in approval_requests table
            try:
                approval_request = ApprovalRequests.objects.get(approval_id=stage.approval_id)
                print(f"Found approval request for approval_id {stage.approval_id}: {approval_request.request_title}")
                print(f"Request data: {approval_request.request_data}")
                print(f"Request data type: {type(approval_request.request_data)}")
                
                stage_data.update({
                    'approval_id': approval_request.approval_id,  # Use the actual approval request ID
                    'request_title': approval_request.request_title,
                    'request_description': approval_request.request_description,
                    'requester_id': approval_request.requester_id,
                    'requester_department': approval_request.requester_department,
                    'priority': approval_request.priority,
                    'overall_status': approval_request.overall_status,
                    'submission_date': approval_request.submission_date,
                    'completion_date': approval_request.completion_date,
                    'expiry_date': approval_request.expiry_date,
                    'request_data': approval_request.request_data,
                })
                
                # Try to get workflow details if they exist
                try:
                    workflow = ApprovalWorkflows.objects.get(workflow_id=approval_request.workflow_id)
                    stage_data.update({
                        'workflow_name': workflow.workflow_name,
                        'workflow_type': workflow.workflow_type,
                        'business_object_type': workflow.business_object_type,
                    })
                except ApprovalWorkflows.DoesNotExist:
                    pass  # Keep default workflow values
                    
            except ApprovalRequests.DoesNotExist:
                print(f"No approval request found for approval_id: {stage.approval_id}")
                # Keep default approval request values
            
            approval_data.append(stage_data)
        
        return Response(approval_data)
        
    except Exception as e:
        return Response({
            'error': f'Failed to fetch user approvals: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def debug_approval_requests(request):
    """
    Debug endpoint to check approval requests data
    """
    try:
        # Get all approval requests
        approval_requests = ApprovalRequests.objects.all()
        
        debug_data = {
            'total_requests': approval_requests.count(),
            'requests': []
        }
        
        for req in approval_requests:
            debug_data['requests'].append({
                'approval_id': req.approval_id,
                'workflow_id': req.workflow_id,
                'request_title': req.request_title,
                'request_data': req.request_data,
                'request_data_type': str(type(req.request_data)),
                'created_at': req.created_at
            })
        
        return Response(debug_data)
        
    except Exception as e:
        return Response({
            'error': f'Failed to debug approval requests: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def debug_approval_stages(request):
    """
    Debug endpoint to check approval stages data
    """
    try:
        # Get all approval stages
        stages = ApprovalStages.objects.all()
        
        debug_data = {
            'total_stages': stages.count(),
            'stages': []
        }
        
        for stage in stages:
            debug_data['stages'].append({
                'stage_id': stage.stage_id,
                'approval_id': stage.approval_id,
                'stage_name': stage.stage_name,
                'assigned_user_id': stage.assigned_user_id,
                'stage_status': stage.stage_status,
                'created_at': stage.created_at
            })
        
        return Response(debug_data)
        
    except Exception as e:
        return Response({
            'error': f'Failed to debug approval stages: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('approve_rfp')
def start_stage_review(request):
    """
    Mark a stage as IN_PROGRESS when reviewer starts reviewing
    """
    try:
        stage_id = request.data.get('stage_id')
        
        if not stage_id:
            return Response({
                'error': 'stage_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the stage
        stage = ApprovalStages.objects.get(stage_id=stage_id)
        
        # Only update if currently PENDING
        if stage.stage_status == 'PENDING':
            stage.stage_status = 'IN_PROGRESS'
            stage.started_at = timezone.now()
            stage.save()
            
            # Update overall approval status to IN_PROGRESS if it's still DRAFT or PENDING
            try:
                approval_request = ApprovalRequests.objects.get(approval_id=stage.approval_id)
                
                if approval_request.overall_status in ['DRAFT', 'PENDING']:
                    approval_request.overall_status = 'IN_PROGRESS'
                    approval_request.updated_at = timezone.now()
                    approval_request.save()
                    print(f"✅ Updated overall approval status to IN_PROGRESS for approval_id {stage.approval_id}")
                    
                    # Update RFP status based on approval overall status
                    try:
                        update_rfp_status_based_on_approval(approval_request)
                    except Exception as rfp_error:
                        print(f"⚠️  Warning: Failed to update RFP status: {str(rfp_error)}")
                    
            except ApprovalRequests.DoesNotExist:
                print(f"⚠️  No approval request found for approval_id: {stage.approval_id}")
            except Exception as e:
                print(f"⚠️  Error updating overall approval status: {str(e)}")
            
            return Response({
                'message': 'Stage marked as IN_PROGRESS',
                'stage_id': stage_id,
                'new_status': 'IN_PROGRESS'
            })
        else:
            return Response({
                'message': f'Stage is already {stage.stage_status}',
                'stage_id': stage_id,
                'current_status': stage.stage_status
            })
        
    except ApprovalStages.DoesNotExist:
        return Response({
            'error': 'Stage not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': f'Failed to start stage review: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('create_rfp')
def create_sample_approval_request(request):
    """
    Create a sample approval request with request_data for testing
    """
    try:
        # Generate approval ID
        approval_id = f"AR_{uuid.uuid4().hex[:8].upper()}"
        
        # Sample request data
        sample_request_data = {
            "vendor_name": "TechCorp Solutions",
            "vendor_type": "Software Provider",
            "contract_value": 150000,
            "contract_duration": "12 months",
            "services": [
                "Cloud Infrastructure",
                "Data Analytics",
                "Security Services"
            ],
            "requirements": {
                "compliance": "SOC 2 Type II",
                "uptime": "99.9%",
                "support_level": "24/7"
            },
            "budget_approved": True,
            "risk_assessment": "Low",
            "approval_required_by": "2024-12-31T23:59:59Z"
        }
        
        # Create approval request
        # NOTE: The approval_id will be used as workflow_id in the relationship
        approval_request = ApprovalRequests.objects.create(
            approval_id=approval_id,
            workflow_id=approval_id,  # Use approval_id as workflow_id for the relationship
            request_title="Sample Vendor Approval Request",
            request_description="This is a sample approval request for testing the request_data display functionality.",
            requester_id=1,
            requester_department="IT",
            priority="HIGH",
            request_data=sample_request_data,
            overall_status="PENDING",
            submission_date=timezone.now()
        )
        
        # Create a corresponding approval stage for testing
        from .models import ApprovalStages
        stage_id = f"ST_{uuid.uuid4().hex[:8].upper()}"
        
        approval_stage = ApprovalStages.objects.create(
            stage_id=stage_id,
            approval_id=approval_id,  # This will be used as workflow_id in the relationship
            stage_order=1,
            stage_name="Initial Review",
            stage_description="Initial review of the vendor approval request",
            assigned_user_id="Current User",
            assigned_user_name="Current User",
            assigned_user_role="Reviewer",
            department="IT",
            stage_type="REVIEW",
            stage_status="PENDING",
            deadline_date=timezone.now() + timezone.timedelta(days=7),
            is_mandatory=True
        )
        
        # Create workflow version for sample approval request
        try:
            version_record = create_workflow_version(
                workflow_id=approval_id,  # Use approval_id as workflow_id for sample
                approval_ids=[approval_id],
                created_by=1,
                created_by_name="System",
                created_by_role="Administrator",
                version_type='INITIAL',
                change_reason='Sample approval request creation for testing'
            )
            
            if version_record:
                print(f"✅ Sample workflow version created: {version_record.version_id}")
        except Exception as version_error:
            print(f"⚠️ Error creating sample workflow version: {str(version_error)}")
            # Don't fail the sample creation if version creation fails
        
        return Response({
            'approval_id': approval_id,
            'stage_id': stage_id,
            'message': 'Sample approval request and stage created successfully',
            'request_data': sample_request_data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': f'Failed to create sample approval request: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('edit_rfp')
def test_rfp_status_update(request):
    """
    Test endpoint to manually trigger RFP status update
    """
    try:
        workflow_id = request.data.get('workflow_id')
        if not workflow_id:
            return Response({
                'error': 'workflow_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        print(f"Manual RFP status update test for workflow: {workflow_id}")
        update_rfp_status_based_on_approval(workflow_id)
        
        return Response({
            'message': f'RFP status update triggered for workflow {workflow_id}',
            'workflow_id': workflow_id
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to update RFP status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('approve_rfp')
def update_stage_status(request):
    """
    Update the status of an approval stage
    """
    try:
        print(f"Received request data: {request.data}")  # Debug log
        
        stage_id = request.data.get('stage_id')
        new_status = request.data.get('status')
        comments = request.data.get('comments', '')
        response_data = request.data.get('response_data', {})
        
        print(f"Parsed data - stage_id: {stage_id}, status: {new_status}")  # Debug log
        
        if not stage_id or not new_status:
            return Response({
                'error': 'stage_id and status are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_status == 'REJECT':
            return Response({
                'error': 'Direct rejection is no longer supported. Please use REQUEST_CHANGES.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Map frontend status values to database values
        status_mapping = {
            'APPROVE': 'APPROVED',
            # Map change requests to a valid status per ApprovalStages.STAGE_STATUS_CHOICES
            'REQUEST_CHANGES': 'REJECTED'
        }
        
        db_status = status_mapping.get(new_status, new_status)
        is_request_changes_action = new_status == 'REQUEST_CHANGES'
        print(f"Mapped status: {new_status} -> {db_status}")  # Debug log
        
        # Get the stage
        print(f"Looking for stage with ID: {stage_id}")  # Debug log
        stage = ApprovalStages.objects.get(stage_id=stage_id)
        print(f"Found stage: {stage.stage_name}")  # Debug log

       # Check if this is a multi-level workflow and enforce sequential approval
        try:
            approval_request = ApprovalRequests.objects.get(approval_id=stage.approval_id)
            workflow = ApprovalWorkflows.objects.get(workflow_id=approval_request.workflow_id)
            
            # Only enforce sequential approval for MULTI_LEVEL workflows
            if workflow.workflow_type == 'MULTI_LEVEL':
                print(f"Multi-level workflow detected. Checking stage order: {stage.stage_order}")
                
                # Get all stages for this approval, ordered by stage_order
                all_stages = ApprovalStages.objects.filter(
                    approval_id=stage.approval_id
                ).order_by('stage_order')
                
                # Find the current stage index
                current_stage_index = None
                for i, s in enumerate(all_stages):
                    if s.stage_id == stage_id:
                        current_stage_index = i
                        break
                
                # Check if this is not the first stage
                if current_stage_index is not None and current_stage_index > 0:
                    # Get the previous stage
                    previous_stage = all_stages[current_stage_index - 1]
                    print(f"Previous stage: {previous_stage.stage_name} (Status: {previous_stage.stage_status})")
                    
                    # Only allow processing if previous stage is approved
                    if previous_stage.stage_status != 'APPROVED':
                        return Response({
                            'error': f'Cannot process stage {stage.stage_name}. Previous stage {previous_stage.stage_name} must be approved first.',
                            'stage_id': stage_id,
                            'current_stage': stage.stage_name,
                            'previous_stage': previous_stage.stage_name,
                            'previous_stage_status': previous_stage.stage_status,
                            'workflow_type': 'MULTI_LEVEL'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        print(f"✅ Previous stage {previous_stage.stage_name} is approved. Allowing current stage processing.")
                else:
                    print(f"✅ First stage in sequence. No previous stage to check.")
            else:
                print(f"Non-multi-level workflow ({workflow.workflow_type}). No sequential enforcement.")
                
        except (ApprovalRequests.DoesNotExist, ApprovalWorkflows.DoesNotExist) as e:
            print(f"Warning: Could not verify workflow type: {str(e)}")
            # Continue without sequential enforcement if workflow data is not available
        
        # Update stage status
        stage.stage_status = db_status
        
        # Handle response_data safely
        try:
            if response_data:
                # Ensure response_data is properly formatted JSON
                if isinstance(response_data, dict):
                    stage.response_data = response_data
                else:
                    # Try to parse if it's a string
                    import json
                    stage.response_data = json.loads(response_data) if isinstance(response_data, str) else response_data
            else:
                stage.response_data = None
        except Exception as json_error:
            print(f"Warning: Failed to process response_data: {str(json_error)}")
            stage.response_data = None
        
        if db_status == 'APPROVED':
            stage.completed_at = timezone.now()
        elif db_status == 'REJECTED':
            stage.rejection_reason = comments
            stage.completed_at = timezone.now()
            if is_request_changes_action:
                print(f"Stage {stage_id} marked for request changes.")
        
        elif db_status == 'IN_PROGRESS':
            stage.started_at = timezone.now()

        # Store old status for version logging
        old_status = stage.stage_status
        
        try:
            stage.save()
            print(f"Stage {stage_id} saved successfully with status {db_status}")
        except Exception as save_error:
            print(f"Error saving stage {stage_id}: {str(save_error)}")
            raise save_error

        # Create version log for stage status change
        try:
            # Get user information for version logging
            user_id = request.data.get('user_id', stage.assigned_user_id)
            user_name = request.data.get('user_name', stage.assigned_user_name)
            user_role = request.data.get('user_role', stage.assigned_user_role)
            
            # Create version record
            version_change_reason = comments or (
                "Reviewer requested changes" if is_request_changes_action
                else f"Stage status change: {old_status} → {db_status}"
            )
            
            version = create_approval_version(
                approval_id=stage.approval_id,
                stage_id=stage_id,
                old_status=old_status,
                new_status=db_status,
                user_id=user_id,
                user_name=user_name,
                user_role=user_role,
                change_reason=version_change_reason,
                response_data=response_data
            )
            
            if version:
                print(f"✅ Version logged for stage {stage_id} status change: {old_status} → {db_status}")
            else:
                print(f"⚠️  Warning: Failed to create version log for stage {stage_id}")
                
        except Exception as version_error:
            print(f"⚠️  Warning: Error creating version log: {str(version_error)}")
            # Continue without error - version logging is not critical for stage update
    
        
        # Update RFP status based on approval workflow progress (optional)
        # This will be done after updating the overall status
        
        # Add comment if provided
        if comments:
            comment_id = f"CM_{uuid.uuid4().hex[:8].upper()}"
            if db_status == 'REJECTED':
                comment_type = 'CLARIFICATION' if is_request_changes_action else 'REJECTION_REASON'
            else:
                comment_type = 'APPROVAL_NOTE'
            
            # Convert assigned_user_id to integer for database compatibility
            try:
                assigned_user_id_int = int(stage.assigned_user_id) if isinstance(stage.assigned_user_id, str) and stage.assigned_user_id.isdigit() else stage.assigned_user_id
            except (ValueError, AttributeError):
                # Fallback to using the original values if conversion fails
                assigned_user_id_int = 1  # Default fallback
            
            # Handle approval_id conversion - database expects integer but model has CharField
            # Skip comment creation if approval_id cannot be converted to integer
            try:
                # Try to convert approval_id to integer if it's a string
                if isinstance(stage.approval_id, str) and stage.approval_id.isdigit():
                    approval_id_for_comment = int(stage.approval_id)
                elif isinstance(stage.approval_id, int):
                    approval_id_for_comment = stage.approval_id
                else:
                    # Skip comment creation if approval_id is not a valid integer
                    print(f"Warning: Skipping comment creation - approval_id '{stage.approval_id}' cannot be converted to integer")
                    approval_id_for_comment = None
                
                if approval_id_for_comment is not None:
                    ApprovalComments.objects.create(
                        comment_id=comment_id,
                        approval_id=approval_id_for_comment,  # Use converted integer
                        stage_id=stage_id,
                        comment_text=comments,
                        comment_type=comment_type,
                        commented_by=assigned_user_id_int,
                        commented_by_name=stage.assigned_user_name,
                        is_internal=False
                    )
                    print(f"Comment created successfully for stage {stage_id}")
                else:
                    print(f"Comment creation skipped for stage {stage_id} due to invalid approval_id")
                    
            except Exception as comment_error:
                print(f"Warning: Failed to create comment for stage {stage_id}: {str(comment_error)}")
                # Continue with stage update even if comment creation fails
        
        # Update overall approval status based on stage status
        try:
            # Find the approval request using approval_id (which is the stage's approval_id)
            approval_request = ApprovalRequests.objects.get(approval_id=stage.approval_id)
            
            # Get all stages for this approval request
            all_stages = ApprovalStages.objects.filter(approval_id=stage.approval_id)
            total_stages = all_stages.count()
            
            # Exclude SKIPPED and CANCELLED stages from approval checks (these don't count toward approval)
            stages_to_process = all_stages.exclude(stage_status__in=['SKIPPED', 'CANCELLED'])
            total_stages_to_process = stages_to_process.count()
            
            # Count stages by status (only for stages that need to be processed)
            approved_stages = stages_to_process.filter(stage_status='APPROVED').count()
            rejected_stages = stages_to_process.filter(stage_status='REJECTED').count()
            in_progress_stages = stages_to_process.filter(stage_status='IN_PROGRESS').count()
            pending_stages = stages_to_process.filter(stage_status='PENDING').count()
            completed_stages = stages_to_process.filter(stage_status__in=['APPROVED', 'REJECTED']).count()
            
            print(f"Stage status update for approval {stage.approval_id}:")
            print(f"  Total stages: {total_stages} (stages to process: {total_stages_to_process})")
            print(f"  Approved: {approved_stages}, Rejected: {rejected_stages}, In Progress: {in_progress_stages}, Pending: {pending_stages}")
            
            # Determine overall status based on stage statuses
            new_overall_status = approval_request.overall_status  # Keep current status by default
            
            if rejected_stages > 0:
                # If any stage is rejected, overall status is REJECTED
                new_overall_status = 'REJECTED'
                approval_request.completion_date = timezone.now()
                print(f"  → Overall status: REJECTED (rejected stages found)")
                
            elif total_stages_to_process > 0 and completed_stages == total_stages_to_process:
                # All stages that need to be processed are completed
                if approved_stages == total_stages_to_process and rejected_stages == 0:
                    # All stages approved (no rejected stages)
                    new_overall_status = 'APPROVED'
                    approval_request.completion_date = timezone.now()
                    print(f"  → Overall status: APPROVED (all {approved_stages} stage(s) approved)")
                else:
                    # Some stages rejected (shouldn't happen due to check above, but just in case)
                    new_overall_status = 'REJECTED'
                    approval_request.completion_date = timezone.now()
                    print(f"  → Overall status: REJECTED (some stages rejected)")
                    
            elif in_progress_stages > 0 or approved_stages > 0:
                # At least one stage is in progress or approved
                if new_overall_status == 'DRAFT':
                    new_overall_status = 'IN_PROGRESS'
                    print(f"  → Overall status: IN_PROGRESS (review started)")
                elif new_overall_status == 'PENDING':
                    new_overall_status = 'IN_PROGRESS'
                    print(f"  → Overall status: IN_PROGRESS (review in progress)")
            
            # Update approval request if status changed
            if new_overall_status != approval_request.overall_status:
                approval_request.overall_status = new_overall_status
                approval_request.updated_at = timezone.now()
                approval_request.save()
                print(f"✅ Updated overall approval status to {new_overall_status} for approval_id {stage.approval_id}")
                
                # Update RFP status based on approval overall status
                try:
                    update_rfp_status_based_on_approval(approval_request)
                except Exception as rfp_error:
                    print(f"⚠️  Warning: Failed to update RFP status: {str(rfp_error)}")
                    # Continue without error - this is not critical for stage update
            else:
                print(f"ℹ️  Overall status unchanged: {new_overall_status}")
                # Even if status didn't change, if it's APPROVED, double-check all approval requests
                # This ensures RFP status is updated if all approval requests in workflow are now approved
                if new_overall_status == 'APPROVED':
                    try:
                        update_rfp_status_based_on_approval(approval_request)
                    except Exception as rfp_error:
                        print(f"⚠️  Warning: Failed to update RFP status (double-check): {str(rfp_error)}")
                        # Continue without error - this is not critical for stage update
                
        except ApprovalRequests.DoesNotExist:
            print(f"⚠️  No approval request found for approval_id: {stage.approval_id}")
            # Continue without error - this is not critical for stage update
        except Exception as e:
            print(f"⚠️  Error updating overall approval status: {str(e)}")
            import traceback
            traceback.print_exc()
            # Continue without error - this is not critical for stage update
        
        response_message = 'Stage sent back for requested changes' if is_request_changes_action else f'Stage status updated to {db_status}'
        user_friendly_status = 'Request Changes' if is_request_changes_action else (db_status.replace('_', ' ').title() if isinstance(db_status, str) else db_status)
        
        return Response({
            'message': response_message,
            'stage_id': stage_id,
            'new_status': db_status,
            'new_status_display': user_friendly_status,
            'original_status': new_status
        })
        
    except ApprovalStages.DoesNotExist:
        return Response({
            'error': 'Stage not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Full error traceback: {error_traceback}")
        return Response({
            'error': f'Failed to update stage status: {str(e)}',
            'details': str(e),
            'traceback': error_traceback
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# DEBUGGING ENDPOINTS
# =============================================================================

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def debug_approval_requests(request):
    """
    Debug endpoint to show all approval requests and their data structure
    """
    try:
        requests = ApprovalRequests.objects.all().order_by('-created_at')
        debug_data = {
            'total_requests': requests.count(),
            'requests': []
        }
        
        for req in requests:
            request_data = req.request_data
            if isinstance(request_data, str):
                try:
                    request_data = json.loads(request_data)
                except:
                    pass
            
            debug_info = {
                'approval_id': req.approval_id,
                'workflow_id': req.workflow_id,
                'request_title': req.request_title,
                'overall_status': req.overall_status,
                'request_data_type': type(request_data).__name__,
                'request_data_preview': str(request_data)[:200] + '...' if len(str(request_data)) > 200 else str(request_data),
                'has_response_id': False,
                'response_ids_found': []
            }
            
            # Check for response_id in different formats
            if isinstance(request_data, dict):
                for key in ['response_id', 'proposal_id', 'rfp_response_id', 'id']:
                    if key in request_data:
                        debug_info['has_response_id'] = True
                        debug_info['response_ids_found'].append(f"{key}: {request_data[key]}")
            elif isinstance(request_data, list):
                for i, item in enumerate(request_data):
                    if isinstance(item, dict):
                        for key in ['response_id', 'proposal_id', 'rfp_response_id', 'id']:
                            if key in item:
                                debug_info['has_response_id'] = True
                                debug_info['response_ids_found'].append(f"item[{i}].{key}: {item[key]}")
            
            debug_data['requests'].append(debug_info)
        
        return Response(debug_data)
        
    except Exception as e:
        return Response({
            'error': 'Debug endpoint failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def debug_rfp_responses(request):
    """
    Debug endpoint to show all RFP responses and their data
    """
    try:
        responses = RFPResponse.objects.all().order_by('-created_at')
        debug_data = {
            'total_responses': responses.count(),
            'responses': []
        }
        
        for resp in responses:
            debug_info = {
                'response_id': resp.response_id,
                'rfp_id': resp.rfp_id,
                'vendor_id': resp.vendor_id,
                'vendor_name': resp.vendor_name,
                'org': resp.org,
                'submission_status': resp.submission_status,
                'evaluation_status': resp.evaluation_status,
                'proposed_value': resp.proposed_value,
                'technical_score': resp.technical_score,
                'commercial_score': resp.commercial_score,
                'overall_score': resp.overall_score,
                'submitted_at': resp.submitted_at,
                'created_at': resp.created_at
            }
            debug_data['responses'].append(debug_info)
        
        return Response(debug_data)
        
    except Exception as e:
        return Response({
            'error': 'Debug endpoint failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def debug_approval_workflow(request, workflow_id):
    """
    Debug endpoint to show detailed workflow information
    """
    try:
        # Get workflow
        try:
            workflow = ApprovalWorkflows.objects.get(workflow_id=workflow_id)
        except ApprovalWorkflows.DoesNotExist:
            return Response({'error': 'Workflow not found'}, status=404)
        
        # Get all stages
        stages = ApprovalStages.objects.filter(approval_id=workflow_id)
        
        # Get all approval requests for this workflow
        requests = ApprovalRequests.objects.filter(workflow_id=workflow_id)
        
        debug_data = {
            'workflow': {
                'workflow_id': workflow.workflow_id,
                'workflow_name': workflow.workflow_name,
                'workflow_type': workflow.workflow_type,
                'business_object_type': workflow.business_object_type,
                'created_at': workflow.created_at
            },
            'stages': [],
            'requests': []
        }
        
        for stage in stages:
            stage_info = {
                'stage_id': stage.stage_id,
                'stage_name': stage.stage_name,
                'stage_type': stage.stage_type,
                'stage_status': stage.stage_status,
                'stage_order': stage.stage_order,
                'deadline_date': stage.deadline_date,
                'started_at': stage.started_at,
                'completed_at': stage.completed_at
            }
            debug_data['stages'].append(stage_info)
        
        for req in requests:
            request_data = req.request_data
            if isinstance(request_data, str):
                try:
                    request_data = json.loads(request_data)
                except:
                    pass
            
            request_info = {
                'approval_id': req.approval_id,
                'request_title': req.request_title,
                'business_object_type': req.business_object_type,
                'overall_status': req.overall_status,
                'request_data_type': type(request_data).__name__,
                'request_data': request_data
            }
            debug_data['requests'].append(request_info)
        
        return Response(debug_data)
        
    except Exception as e:
        return Response({
            'error': 'Debug endpoint failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def debug_stage_request_data(request, stage_id):
    """
    Debug endpoint to check stage request data
    """
    try:
        stage = ApprovalStages.objects.get(stage_id=stage_id)
        
        debug_data = {
            'stage_id': stage.stage_id,
            'approval_id': stage.approval_id,
            'stage_name': stage.stage_name,
            'stage_status': stage.stage_status,
        }
        
        # Try to get approval request
        try:
            approval_request = ApprovalRequests.objects.get(approval_id=stage.approval_id)
            debug_data['approval_request'] = {
                'approval_id': approval_request.approval_id,
                'workflow_id': approval_request.workflow_id,
                'request_title': approval_request.request_title,
                'request_data': approval_request.request_data,
                'request_data_type': str(type(approval_request.request_data)),
            }
        except ApprovalRequests.DoesNotExist:
            debug_data['approval_request'] = 'NOT FOUND'
        
        return Response(debug_data)
        
    except ApprovalStages.DoesNotExist:
        return Response({'error': 'Stage not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def debug_api_connectivity(request):
    """
    Debug endpoint to test API connectivity and database connections
    """
    try:
        debug_info = {
            'api_status': 'OK',
            'database_connection': 'OK',
            'timestamp': timezone.now().isoformat(),
            'endpoints_available': {
                'debug_approval_requests': '/api/rfp-approval/debug-approval-requests/',
                'debug_rfp_responses': '/api/rfp-approval/debug-rfp-responses/',
                'debug_workflow': '/api/rfp-approval/debug-workflow/{workflow_id}/',
                'get_proposal_id': '/api/rfp-approval/get-proposal-id/{approval_id}/',
                'user_approvals': '/api/rfp-approval/user-approvals/',
                'rfp_responses_list': '/api/v1/rfp-responses-list/',
                'rfp_responses_detail': '/api/v1/rfp-responses-detail/{response_id}/'
            },
            'database_stats': {
                'approval_requests_count': ApprovalRequests.objects.count(),
                'approval_workflows_count': ApprovalWorkflows.objects.count(),
                'approval_stages_count': ApprovalStages.objects.count(),
                'rfp_responses_count': RFPResponse.objects.count()
            }
        }
        
        return Response(debug_info)
        
    except Exception as e:
        return Response({
            'error': 'Debug connectivity failed',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_document_url(request, file_id):
    """
    Get document URL from s3_files table by file ID
    """
    try:
        from rfp.models import S3Files
        
        # Get file from s3_files table
        s3_file = S3Files.objects.get(id=file_id)
        
        return Response({
            'file_id': s3_file.id,
            'url': s3_file.url,
            'file_name': s3_file.file_name,
            'file_type': s3_file.file_type,
            'uploaded_at': s3_file.uploaded_at.isoformat() if s3_file.uploaded_at else None
        })
        
    except S3Files.DoesNotExist:
        return Response({
            'error': f'File with ID {file_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Failed to fetch document URL: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_risks_for_response(request, response_id):
    """
    Get all risks associated with a specific RFP response
    Query: entity='RFP' AND row=response_id (as string)
    """
    try:
        from apps.vendor_risk.models import RiskTPRM
        
        # Convert response_id to string for comparison (row field is varchar(50))
        response_id_str = str(response_id)
        
        print(f"[RISKS_API] Fetching risks for response_id: {response_id} (as string: '{response_id_str}')")
        print(f"[RISKS_API] Query: entity='RFP' AND row='{response_id_str}'")
        
        # Get all risks where entity is "RFP" and row matches the response_id
        # Using exact match for both entity and row
        risks = RiskTPRM.objects.filter(
            entity='RFP',
            row=response_id_str
        ).order_by('-created_at')
        
        # Count the risks
        risk_count = risks.count()
        print(f"[RISKS_API] Found {risk_count} risks for response_id {response_id}")
        
        risk_data = []
        for risk in risks:
            # Safely parse suggested_mitigations
            mitigations = []
            try:
                if risk.suggested_mitigations:
                    if isinstance(risk.suggested_mitigations, (list, dict)):
                        mitigations = risk.suggested_mitigations if isinstance(risk.suggested_mitigations, list) else [risk.suggested_mitigations]
                    elif isinstance(risk.suggested_mitigations, str):
                        try:
                            parsed = json.loads(risk.suggested_mitigations)
                            mitigations = parsed if isinstance(parsed, list) else [parsed] if parsed else []
                        except (json.JSONDecodeError, TypeError):
                            # If JSON parsing fails, try splitting by common delimiters
                            mitigations = [m.strip() for m in risk.suggested_mitigations.split(',') if m.strip()]
            except Exception as e:
                print(f"[RISKS_API] Error parsing mitigations for risk {risk.id}: {e}")
                mitigations = []
            
            risk_dict = {
                'id': risk.id,
                'title': risk.title or '',
                'description': risk.description or '',
                'likelihood': risk.likelihood if risk.likelihood is not None else 0,
                'impact': risk.impact if risk.impact is not None else 0,
                'score': risk.score if risk.score is not None else 0,
                'priority': risk.priority or 'Medium',
                'ai_explanation': risk.ai_explanation or '',
                'suggested_mitigations': mitigations,
                'status': risk.status or 'Open',
                'exposure_rating': risk.exposure_rating if risk.exposure_rating is not None else None,
                'risk_type': risk.risk_type or '',
                'entity': risk.entity or 'RFP',
                'data': risk.data if hasattr(risk, 'data') else None,
                'row': risk.row or response_id_str,
                'created_at': risk.created_at.isoformat() if risk.created_at else None,
                'updated_at': risk.updated_at.isoformat() if risk.updated_at else None
            }
            
            risk_data.append(risk_dict)
            print(f"[RISKS_API] Added risk: {risk.id} - {risk.title}")
        
        print(f"[RISKS_API] Returning {len(risk_data)} risks")
        
        return Response({
            'response_id': response_id,
            'total_risks': len(risk_data),
            'risks': risk_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[RISKS_API] ERROR in get_risks_for_response: {str(e)}")
        print(f"[RISKS_API] Traceback: {error_traceback}")
        traceback.print_exc()
        return Response({
            'error': f'Failed to fetch risks for response {response_id}: {str(e)}',
            'details': error_traceback
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_approval_version_history_api(request, approval_id):
    """
    Get version history for an approval request
    """
    try:
        version_history = get_approval_version_history(approval_id)
        
        return Response({
            'success': True,
            'approval_id': approval_id,
            'version_count': len(version_history),
            'versions': version_history
        })
        
    except Exception as e:
        print(f"Error getting approval version history: {str(e)}")
        return Response({
            'success': False,
            'error': f'Failed to get version history: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_rfp_details_for_change_request(request, rfp_id):
    """
    Get RFP details with change request context for editing
    """
    try:
        from rfp.models import RFP, RFPEvaluationCriteria
        
        # Get RFP details - use rfp_id field, not id
        rfp = RFP.objects.get(rfp_id=rfp_id)
        
        # Get change requests for this RFP
        change_requests = []
        try:
            from rfp_approval.models import ApprovalRequests, ApprovalStages, ApprovalWorkflows
            from rfp_approval.models import ApprovalComments
            import json
            
            # Find approval requests for this RFP by:
            # 1. Getting workflows with business_object_type='RFP'
            # 2. Getting approval requests for those workflows
            # 3. Checking if request_data contains matching rfp_id
            rfp_approval_requests = []
            try:
                # Get all workflows for RFP
                try:
                    rfp_workflows = ApprovalWorkflows.objects.filter(
                        business_object_type='RFP'
                    )
                    workflow_ids = [w.workflow_id for w in rfp_workflows]
                except Exception as e:
                    print(f"Error fetching workflows: {str(e)}")
                    workflow_ids = []
                
                # Get approval requests for these workflows
                if workflow_ids:
                    try:
                        all_approval_requests = ApprovalRequests.objects.filter(
                            workflow_id__in=workflow_ids
                        )
                    except Exception as e:
                        print(f"Error fetching approval requests: {str(e)}")
                        all_approval_requests = ApprovalRequests.objects.none()
                else:
                    all_approval_requests = ApprovalRequests.objects.none()
                
                # Filter by rfp_id in request_data
                for approval in all_approval_requests:
                    try:
                        request_data = approval.request_data
                        if request_data is None:
                            continue
                            
                        # Handle both string and dict formats
                        if isinstance(request_data, str):
                            try:
                                request_data = json.loads(request_data)
                            except json.JSONDecodeError:
                                continue
                        
                        # Check if this approval request is for this RFP
                        if isinstance(request_data, dict):
                            request_rfp_id = request_data.get('rfp_id')
                            if request_rfp_id and str(request_rfp_id) == str(rfp_id):
                                rfp_approval_requests.append(approval)
                    except (json.JSONDecodeError, AttributeError, TypeError, KeyError) as e:
                        # Skip if request_data can't be parsed or doesn't have rfp_id
                        continue
                    except Exception as e:
                        print(f"Unexpected error processing approval {approval.approval_id}: {str(e)}")
                        continue
            except Exception as e:
                import traceback
                print(f"Error finding approval requests: {str(e)}")
                print(traceback.format_exc())
                rfp_approval_requests = []
            
            approval_requests = rfp_approval_requests
            
            for approval in approval_requests:
                try:
                    # Get stages with REQUEST_CHANGES status (also check for REJECTED which might be used)
                    try:
                        stages_with_changes = ApprovalStages.objects.filter(
                            approval_id=approval.approval_id,
                            stage_status__in=['REQUEST_CHANGES', 'REJECTED']
                        )
                    except Exception as e:
                        print(f"Error fetching stages for approval {approval.approval_id}: {str(e)}")
                        continue
                    
                    for stage in stages_with_changes:
                        try:
                            # Get change request comments
                            try:
                                change_comments = ApprovalComments.objects.filter(
                                    stage_id=stage.stage_id,
                                    comment_type='CHANGE_REQUEST'
                                ).order_by('-created_at')
                            except Exception as e:
                                print(f"Error fetching comments for stage {stage.stage_id}: {str(e)}")
                                continue
                            
                            for comment in change_comments:
                                try:
                                    change_requests.append({
                                        'change_request_id': f"cr_{comment.comment_id}",
                                        'stage_id': stage.stage_id,
                                        'stage_name': getattr(stage, 'stage_name', 'Unknown Stage'),
                                        'requested_by': getattr(stage, 'assigned_user_name', 'Unknown'),
                                        'requested_by_role': getattr(stage, 'assigned_user_role', 'Unknown'),
                                        'change_request_description': getattr(comment, 'comment_text', 'No description'),
                                        'requested_at': comment.created_at.isoformat() if comment.created_at else None,
                                        'approval_id': approval.approval_id
                                    })
                                except Exception as e:
                                    print(f"Error processing comment {comment.comment_id}: {str(e)}")
                                    continue
                        except Exception as e:
                            print(f"Error processing stage {stage.stage_id}: {str(e)}")
                            continue
                except Exception as e:
                    print(f"Error processing approval {approval.approval_id}: {str(e)}")
                    continue
        except Exception as e:
            import traceback
            print(f"Error fetching change requests: {str(e)}")
            print(traceback.format_exc())
            # Continue even if change requests can't be loaded
        
        # Serialize RFP data - handle None values safely
        try:
            rfp_data = {
                'rfp_id': rfp.rfp_id,
                'id': getattr(rfp, 'id', rfp.rfp_id),
                'rfp_number': getattr(rfp, 'rfp_number', None),
                'rfp_title': getattr(rfp, 'rfp_title', None),
                'title': getattr(rfp, 'rfp_title', None),  # For compatibility
                'description': getattr(rfp, 'description', None),
                'rfp_type': getattr(rfp, 'rfp_type', None),
                'type': getattr(rfp, 'rfp_type', None),  # For compatibility
                'category': getattr(rfp, 'category', None),
                'estimated_value': getattr(rfp, 'estimated_value', None),
                'estimatedValue': getattr(rfp, 'estimated_value', None),  # For compatibility
                'currency': getattr(rfp, 'currency', None),
                'budget_range_min': getattr(rfp, 'budget_range_min', None),
                'budgetMin': getattr(rfp, 'budget_range_min', None),  # For compatibility
                'budget_range_max': getattr(rfp, 'budget_range_max', None),
                'budgetMax': getattr(rfp, 'budget_range_max', None),  # For compatibility
                'issue_date': rfp.issue_date.isoformat() if hasattr(rfp, 'issue_date') and rfp.issue_date else None,
                'issueDate': rfp.issue_date.isoformat() if hasattr(rfp, 'issue_date') and rfp.issue_date else None,  # For compatibility
                'submission_deadline': rfp.submission_deadline.isoformat() if hasattr(rfp, 'submission_deadline') and rfp.submission_deadline else None,
                'deadline': rfp.submission_deadline.isoformat() if hasattr(rfp, 'submission_deadline') and rfp.submission_deadline else None,  # For compatibility
                'evaluation_period_end': rfp.evaluation_period_end.isoformat() if hasattr(rfp, 'evaluation_period_end') and rfp.evaluation_period_end else None,
                'evaluationPeriodEnd': rfp.evaluation_period_end.isoformat() if hasattr(rfp, 'evaluation_period_end') and rfp.evaluation_period_end else None,  # For compatibility
                'evaluation_method': getattr(rfp, 'evaluation_method', None),
                'evaluationMethod': getattr(rfp, 'evaluation_method', None),  # For compatibility
                'criticality_level': getattr(rfp, 'criticality_level', None),
                'criticalityLevel': getattr(rfp, 'criticality_level', None),  # For compatibility
                'geographical_scope': getattr(rfp, 'geographical_scope', None),
                'geographicalScope': getattr(rfp, 'geographical_scope', None),  # For compatibility
                'compliance_requirements': getattr(rfp, 'compliance_requirements', None),
                'complianceRequirements': getattr(rfp, 'compliance_requirements', None),  # For compatibility
                'allow_late_submissions': getattr(rfp, 'allow_late_submissions', False),
                'allowLateSubmissions': getattr(rfp, 'allow_late_submissions', False),  # For compatibility
                'auto_approved': getattr(rfp, 'auto_approved', False),
                'autoApproved': getattr(rfp, 'auto_approved', False),  # For compatibility
                'status': getattr(rfp, 'status', None),
                'created_at': rfp.created_at.isoformat() if hasattr(rfp, 'created_at') and rfp.created_at else None,
                'updated_at': rfp.updated_at.isoformat() if hasattr(rfp, 'updated_at') and rfp.updated_at else None,
                'change_requests': change_requests,
                'documents': getattr(rfp, 'documents', []) or []
            }
        except Exception as e:
            import traceback
            print(f"Error serializing RFP data: {str(e)}")
            print(traceback.format_exc())
            # Return minimal RFP data if serialization fails
            rfp_data = {
                'rfp_id': rfp.rfp_id,
                'rfp_number': getattr(rfp, 'rfp_number', None),
                'rfp_title': getattr(rfp, 'rfp_title', None),
                'description': getattr(rfp, 'description', None),
                'change_requests': change_requests,
                'documents': []
            }
        
        # Get evaluation criteria - try multiple methods to ensure we get all criteria
        evaluation_criteria = []
        
        # METHOD 1: Use Django's related manager (MOST RELIABLE)
        try:
            print(f"🔍 METHOD 1: Using Django related manager for rfp_id={rfp.rfp_id}")
            
            # First check what the relationship returns
            print(f"🔍 Checking rfp.evaluation_criteria relationship...")
            related_criteria = rfp.evaluation_criteria.all().order_by('display_order')
            criteria_count = related_criteria.count()
            print(f"🔍 Related manager returned {criteria_count} criteria")
            
            # Debug: Check what criteria exist for ALL RFPs to see if data exists
            from rfp.models import RFPEvaluationCriteria
            all_criteria_count = RFPEvaluationCriteria.objects.all().count()
            print(f"🔍 TOTAL criteria in entire database: {all_criteria_count}")
            
            if all_criteria_count > 0:
                # Show sample of what rfp_ids have criteria
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT DISTINCT rfp_id, COUNT(*) as cnt 
                        FROM rfp_evaluation_criteria 
                        GROUP BY rfp_id 
                        ORDER BY cnt DESC 
                        LIMIT 10
                    """)
                    sample = cursor.fetchall()
                    print(f"🔍 Sample RFP IDs with criteria: {[(row[0], row[1]) for row in sample]}")
                    
                    # Check if OUR rfp_id exists in the table
                    cursor.execute("""
                        SELECT COUNT(*) FROM rfp_evaluation_criteria WHERE rfp_id = %s
                    """, [rfp.rfp_id])
                    exact_count = cursor.fetchone()[0]
                    print(f"🔍 DIRECT SQL CHECK: Found {exact_count} criteria for rfp_id={rfp.rfp_id} in database")
                    
                    if exact_count > 0:
                        # Show what the actual data looks like
                        cursor.execute("""
                            SELECT criteria_id, rfp_id, criteria_name 
                            FROM rfp_evaluation_criteria 
                            WHERE rfp_id = %s 
                            LIMIT 5
                        """, [rfp.rfp_id])
                        sample_rows = cursor.fetchall()
                        print(f"🔍 Sample criteria data for rfp_id={rfp.rfp_id}: {[(r[0], r[1], r[2]) for r in sample_rows]}")
                        
                        # FORCE LOAD from raw SQL if ORM didn't find them
                        if exact_count > 0 and criteria_count == 0:
                            print(f"⚠️ ORM returned 0 but SQL found {exact_count} - FORCING LOAD from SQL")
                            cursor.execute("""
                                SELECT criteria_id, rfp_id, criteria_name, criteria_description, 
                                       weight_percentage, evaluation_type, min_score, max_score, 
                                       median_score, is_mandatory, veto_enabled, veto_threshold,
                                       min_word_count, expected_boolean_answer, display_order
                                FROM rfp_evaluation_criteria 
                                WHERE rfp_id = %s 
                                ORDER BY display_order
                            """, [rfp.rfp_id])
                            force_rows = cursor.fetchall()
                            for idx, row in enumerate(force_rows, 1):
                                criterion_data = {
                                    'id': str(row[0]),
                                    'criteria_id': str(row[0]),
                                    'name': str(row[2]) if row[2] else '',
                                    'criteria_name': str(row[2]) if row[2] else '',
                                    'description': str(row[3]) if row[3] else '',
                                    'criteria_description': str(row[3]) if row[3] else '',
                                    'weight': float(row[4]) if row[4] is not None else 0,
                                    'weight_percentage': float(row[4]) if row[4] is not None else 0,
                                    'isVeto': bool(row[10]) if row[10] is not None else False,
                                    'veto_enabled': bool(row[10]) if row[10] is not None else False,
                                    'isMandatory': bool(row[9]) if row[9] is not None else False,
                                    'is_mandatory': bool(row[9]) if row[9] is not None else False,
                                    'evaluationType': str(row[5]) if row[5] else 'scoring',
                                    'evaluation_type': str(row[5]) if row[5] else 'scoring',
                                    'minScore': float(row[6]) if row[6] is not None else None,
                                    'min_score': float(row[6]) if row[6] is not None else None,
                                    'maxScore': float(row[7]) if row[7] is not None else None,
                                    'max_score': float(row[7]) if row[7] is not None else None,
                                    'medianScore': float(row[8]) if row[8] is not None else None,
                                    'median_score': float(row[8]) if row[8] is not None else None,
                                    'vetoThreshold': float(row[11]) if row[11] is not None else None,
                                    'veto_threshold': float(row[11]) if row[11] is not None else None,
                                    'displayOrder': int(row[14]) if row[14] is not None else 0,
                                    'display_order': int(row[14]) if row[14] is not None else 0
                                }
                                evaluation_criteria.append(criterion_data)
                                print(f"  ✅ [{idx}] FORCE LOADED from SQL: {criterion_data['name']} (ID: {criterion_data['id']}, Weight: {criterion_data['weight']}%)")
            
            if related_criteria.exists() and len(evaluation_criteria) == 0:
                print(f"✅ USING RELATED MANAGER: Found {criteria_count} criteria")
                for criterion in related_criteria:
                    criterion_data = {
                        'id': str(criterion.criteria_id),
                        'criteria_id': str(criterion.criteria_id),
                        'name': criterion.criteria_name or '',
                        'criteria_name': criterion.criteria_name or '',
                        'description': criterion.criteria_description or '',
                        'criteria_description': criterion.criteria_description or '',
                        'weight': float(criterion.weight_percentage) if criterion.weight_percentage else 0,
                        'weight_percentage': float(criterion.weight_percentage) if criterion.weight_percentage else 0,
                        'isVeto': bool(criterion.veto_enabled),
                        'veto_enabled': bool(criterion.veto_enabled),
                        'isMandatory': bool(criterion.is_mandatory),
                        'is_mandatory': bool(criterion.is_mandatory),
                        'evaluationType': criterion.evaluation_type or 'scoring',
                        'evaluation_type': criterion.evaluation_type or 'scoring',
                        'minScore': float(criterion.min_score) if criterion.min_score else None,
                        'min_score': float(criterion.min_score) if criterion.min_score else None,
                        'maxScore': float(criterion.max_score) if criterion.max_score else None,
                        'max_score': float(criterion.max_score) if criterion.max_score else None,
                        'medianScore': float(criterion.median_score) if criterion.median_score else None,
                        'median_score': float(criterion.median_score) if criterion.median_score else None,
                        'vetoThreshold': float(criterion.veto_threshold) if criterion.veto_threshold else None,
                        'veto_threshold': float(criterion.veto_threshold) if criterion.veto_threshold else None,
                        'displayOrder': int(criterion.display_order) if criterion.display_order else 0,
                        'display_order': int(criterion.display_order) if criterion.display_order else 0
                    }
                    evaluation_criteria.append(criterion_data)
                    print(f"  ✅ [{len(evaluation_criteria)}] Loaded via related manager: {criterion_data['name']} (ID: {criterion_data['id']}, Weight: {criterion_data['weight']}%)")
        except Exception as related_err:
            print(f"⚠️ Related manager method failed: {related_err}")
            import traceback
            print(traceback.format_exc())
        
        # METHOD 2: Use raw SQL as fallback if related manager didn't work
        if len(evaluation_criteria) == 0:
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    # First, check what rfp_id we're working with
                    rfp_id_value = rfp.rfp_id
                    print(f"🔍 METHOD 2: Raw SQL fallback for rfp_id={rfp_id_value} (type: {type(rfp_id_value)})")
                    
                    # Check if table exists and has data
                    cursor.execute("SELECT COUNT(*) FROM rfp_evaluation_criteria")
                    total_criteria = cursor.fetchone()[0]
                    print(f"🔍 Total criteria in table: {total_criteria}")
                    
                    # Get sample rfp_ids to see what exists
                    cursor.execute("SELECT DISTINCT rfp_id FROM rfp_evaluation_criteria LIMIT 20")
                    all_rfp_ids = [row[0] for row in cursor.fetchall()]
                    print(f"🔍 All rfp_ids in criteria table: {all_rfp_ids}")
                    print(f"🔍 Our rfp_id ({rfp_id_value}) in list? {rfp_id_value in all_rfp_ids}")
                    
                    # Try exact match first
                    cursor.execute("""
                    SELECT criteria_id, rfp_id, criteria_name, criteria_description, 
                           weight_percentage, evaluation_type, min_score, max_score, 
                           median_score, is_mandatory, veto_enabled, veto_threshold,
                           min_word_count, expected_boolean_answer, display_order
                    FROM rfp_evaluation_criteria 
                    WHERE rfp_id = %s 
                    ORDER BY display_order
                    """, [rfp_id_value])
                    
                    rows = cursor.fetchall()
                    print(f"🔍 DIRECT SQL QUERY: Found {len(rows)} criteria for rfp_id={rfp_id_value}")
                    
                    # If no results, try as string
                    if len(rows) == 0:
                        print(f"⚠️ No results with integer rfp_id, trying string conversion...")
                        cursor.execute("""
                            SELECT criteria_id, rfp_id, criteria_name, criteria_description, 
                                   weight_percentage, evaluation_type, min_score, max_score, 
                                   median_score, is_mandatory, veto_enabled, veto_threshold,
                                   min_word_count, expected_boolean_answer, display_order
                            FROM rfp_evaluation_criteria 
                            WHERE rfp_id = %s 
                            ORDER BY display_order
                        """, [str(rfp_id_value)])
                        rows = cursor.fetchall()
                        print(f"🔍 String query result: Found {len(rows)} criteria")
                    
                    # If still no results, try without WHERE to see all data
                    if len(rows) == 0:
                        print(f"⚠️ Still no results, checking all criteria...")
                        cursor.execute("""
                            SELECT criteria_id, rfp_id, criteria_name, criteria_description, 
                                   weight_percentage, evaluation_type, min_score, max_score, 
                                   median_score, is_mandatory, veto_enabled, veto_threshold,
                                   min_word_count, expected_boolean_answer, display_order
                            FROM rfp_evaluation_criteria 
                            ORDER BY rfp_id, display_order
                            LIMIT 50
                        """)
                        all_rows = cursor.fetchall()
                        print(f"🔍 All criteria sample (first 50): {len(all_rows)} rows")
                        for sample_row in all_rows[:10]:  # Show first 10
                            print(f"   Sample: criteria_id={sample_row[0]}, rfp_id={sample_row[1]} (type: {type(sample_row[1])}), name={sample_row[2]}")
                    
                    if len(rows) > 0:
                        print(f"✅ LOADING {len(rows)} CRITERIA FROM DATABASE")
                        for idx, row in enumerate(rows, 1):
                            try:
                                criterion_data = {
                                    'id': str(row[0]),  # criteria_id
                                    'criteria_id': str(row[0]),
                                    'name': str(row[2]) if row[2] else '',  # criteria_name
                                    'criteria_name': str(row[2]) if row[2] else '',
                                    'description': str(row[3]) if row[3] else '',  # criteria_description
                                    'criteria_description': str(row[3]) if row[3] else '',
                                    'weight': float(row[4]) if row[4] is not None else 0,  # weight_percentage
                                    'weight_percentage': float(row[4]) if row[4] is not None else 0,
                                    'isVeto': bool(row[10]) if row[10] is not None else False,  # veto_enabled
                                    'veto_enabled': bool(row[10]) if row[10] is not None else False,
                                    'isMandatory': bool(row[9]) if row[9] is not None else False,  # is_mandatory
                                    'is_mandatory': bool(row[9]) if row[9] is not None else False,
                                    'evaluationType': str(row[5]) if row[5] else 'scoring',  # evaluation_type
                                    'evaluation_type': str(row[5]) if row[5] else 'scoring',
                                    'minScore': float(row[6]) if row[6] is not None else None,  # min_score
                                    'min_score': float(row[6]) if row[6] is not None else None,
                                    'maxScore': float(row[7]) if row[7] is not None else None,  # max_score
                                    'max_score': float(row[7]) if row[7] is not None else None,
                                    'medianScore': float(row[8]) if row[8] is not None else None,  # median_score
                                    'median_score': float(row[8]) if row[8] is not None else None,
                                    'vetoThreshold': float(row[11]) if row[11] is not None else None,  # veto_threshold
                                    'veto_threshold': float(row[11]) if row[11] is not None else None,
                                    'displayOrder': int(row[14]) if row[14] is not None else 0,  # display_order
                                    'display_order': int(row[14]) if row[14] is not None else 0
                                }
                                evaluation_criteria.append(criterion_data)
                                print(f"  ✅ [{idx}] Loaded: {criterion_data['name']} (ID: {criterion_data['id']}, Weight: {criterion_data['weight']}%, Veto: {criterion_data['isVeto']})")
                            except Exception as row_err:
                                print(f"  ❌ Error processing row {idx}: {row_err}")
                                import traceback
                                print(traceback.format_exc())
                    else:
                        print(f"⚠️ Raw SQL found no criteria for rfp_id={rfp_id_value}")
            except Exception as sql_err:
                import traceback
                print(f"❌ CRITICAL ERROR in raw SQL query: {sql_err}")
                print(traceback.format_exc())
                # Try ORM as last resort
                try:
                    print(f"🔄 Trying ORM as last resort for rfp_id={rfp.rfp_id}")
                    from rfp.models import RFPEvaluationCriteria
                    # Use the RFP object directly (most reliable)
                    orm_criteria = RFPEvaluationCriteria.objects.filter(rfp=rfp).order_by('display_order')
                    if not orm_criteria.exists():
                        orm_criteria = RFPEvaluationCriteria.objects.filter(rfp_id=rfp.rfp_id).order_by('display_order')
                    if not orm_criteria.exists():
                        orm_criteria = RFPEvaluationCriteria.objects.filter(rfp__rfp_id=rfp.rfp_id).order_by('display_order')
                    if orm_criteria.exists():
                        for criterion in orm_criteria:
                            evaluation_criteria.append({
                                'id': str(criterion.criteria_id),
                                'criteria_id': str(criterion.criteria_id),
                                'name': criterion.criteria_name or '',
                                'criteria_name': criterion.criteria_name or '',
                                'description': criterion.criteria_description or '',
                                'criteria_description': criterion.criteria_description or '',
                                'weight': float(criterion.weight_percentage) if criterion.weight_percentage else 0,
                                'weight_percentage': float(criterion.weight_percentage) if criterion.weight_percentage else 0,
                                'isVeto': bool(criterion.veto_enabled),
                                'veto_enabled': bool(criterion.veto_enabled),
                                'isMandatory': bool(criterion.is_mandatory),
                                'is_mandatory': bool(criterion.is_mandatory),
                                'evaluationType': criterion.evaluation_type or 'scoring',
                                'evaluation_type': criterion.evaluation_type or 'scoring',
                                'minScore': float(criterion.min_score) if criterion.min_score else None,
                                'min_score': float(criterion.min_score) if criterion.min_score else None,
                                'maxScore': float(criterion.max_score) if criterion.max_score else None,
                                'max_score': float(criterion.max_score) if criterion.max_score else None,
                                'medianScore': float(criterion.median_score) if criterion.median_score else None,
                                'median_score': float(criterion.median_score) if criterion.median_score else None,
                                'vetoThreshold': float(criterion.veto_threshold) if criterion.veto_threshold else None,
                                'veto_threshold': float(criterion.veto_threshold) if criterion.veto_threshold else None,
                                'displayOrder': int(criterion.display_order) if criterion.display_order else 0,
                                'display_order': int(criterion.display_order) if criterion.display_order else 0
                            })
                        print(f"✅ ORM loaded {len(evaluation_criteria)} criteria")
                except Exception as orm_err2:
                    print(f"⚠️ ORM last resort also failed: {orm_err2}")
                    import traceback
                    print(traceback.format_exc())
        
        # Set criteria in response - ALWAYS include even if empty
        rfp_data['evaluation_criteria'] = evaluation_criteria
        rfp_data['criteria'] = evaluation_criteria  # For compatibility
        print(f"✅ FINAL: Added {len(evaluation_criteria)} evaluation criteria to response (rfp_id={rfp.rfp_id})")
        print(f"🔍 CRITERIA DATA BEING RETURNED:", json.dumps(evaluation_criteria[:2] if len(evaluation_criteria) > 0 else [], indent=2))
        
        # Ensure criteria is at top level as well for easier access
        response_data = {
            'success': True,
            'rfp': rfp_data,
            'change_requests_count': len(change_requests),
            # Also include criteria at top level for easier frontend access
            'evaluation_criteria': evaluation_criteria
        }
        
        print(f"📤 RESPONSE STRUCTURE: rfp.evaluation_criteria count: {len(rfp_data.get('evaluation_criteria', []))}")
        print(f"📤 RESPONSE STRUCTURE: top-level evaluation_criteria count: {len(response_data.get('evaluation_criteria', []))}")
        
        return Response(response_data)
        
    except RFP.DoesNotExist:
        return Response({
            'success': False,
            'error': f'RFP with ID {rfp_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in get_rfp_details_for_change_request: {str(e)}")
        print(f"Traceback: {error_trace}")
        return Response({
            'success': False,
            'error': f'Failed to load RFP details: {str(e)}',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_rfp_details(request, rfp_id):
    """
    Get complete RFP details including documents
    """
    try:
        # Get RFP by ID
        rfp = RFP.objects.get(rfp_id=rfp_id)
        
        # Get evaluation criteria for this RFP - use raw SQL to ensure data is fetched
        evaluation_criteria = []
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT criteria_id, rfp_id, criteria_name, criteria_description, 
                           weight_percentage, evaluation_type, min_score, max_score, 
                           median_score, is_mandatory, veto_enabled, veto_threshold,
                           min_word_count, expected_boolean_answer, display_order
                    FROM rfp_evaluation_criteria 
                    WHERE rfp_id = %s 
                    ORDER BY display_order
                """, [rfp.rfp_id])
                
                rows = cursor.fetchall()
                print(f"🔍 Fallback endpoint: Found {len(rows)} criteria for rfp_id={rfp.rfp_id}")
                
                for row in rows:
                    evaluation_criteria.append({
                        'id': str(row[0]),  # criteria_id - also include for frontend compatibility
                        'criteria_id': str(row[0]),
                        'name': str(row[2]) if row[2] else '',  # criteria_name - also include for frontend
                        'criteria_name': str(row[2]) if row[2] else '',
                        'description': str(row[3]) if row[3] else '',  # criteria_description
                        'criteria_description': str(row[3]) if row[3] else '',
                        'weight': float(row[4]) if row[4] is not None else 0,  # weight_percentage
                        'weight_percentage': float(row[4]) if row[4] is not None else 0,
                        'isVeto': bool(row[10]) if row[10] is not None else False,  # veto_enabled
                        'veto_enabled': bool(row[10]) if row[10] is not None else False,
                        'isMandatory': bool(row[9]) if row[9] is not None else False,  # is_mandatory
                        'is_mandatory': bool(row[9]) if row[9] is not None else False,
                        'evaluationType': str(row[5]) if row[5] else 'scoring',  # evaluation_type
                        'evaluation_type': str(row[5]) if row[5] else 'scoring',
                        'minScore': float(row[6]) if row[6] is not None else None,  # min_score
                        'min_score': float(row[6]) if row[6] is not None else None,
                        'maxScore': float(row[7]) if row[7] is not None else None,  # max_score
                        'max_score': float(row[7]) if row[7] is not None else None,
                        'medianScore': float(row[8]) if row[8] is not None else None,  # median_score
                        'median_score': float(row[8]) if row[8] is not None else None,
                        'vetoThreshold': float(row[11]) if row[11] is not None else None,  # veto_threshold
                        'veto_threshold': float(row[11]) if row[11] is not None else None,
                        'displayOrder': int(row[14]) if row[14] is not None else 0,  # display_order
                        'display_order': int(row[14]) if row[14] is not None else 0
                    })
        except Exception as e:
            import traceback
            print(f"❌ Error fetching evaluation criteria: {str(e)}")
            print(traceback.format_exc())
        
        # Process documents - expand IDs to full document objects
        documents_data = []
        if rfp.documents:
            try:
                from rfp.models import S3Files
                
                # Handle both array of IDs and array of objects
                document_ids = rfp.documents
                if isinstance(document_ids, list):
                    for doc_item in document_ids:
                        # If it's an integer (file ID), fetch from s3_files
                        if isinstance(doc_item, int):
                            try:
                                s3_file = S3Files.objects.get(id=doc_item)
                                documents_data.append({
                                    'id': s3_file.id,
                                    'url': s3_file.url,
                                    'file_name': s3_file.file_name,
                                    'file_type': s3_file.file_type,
                                    'uploaded_at': s3_file.uploaded_at.isoformat() if s3_file.uploaded_at else None
                                })
                            except S3Files.DoesNotExist:
                                print(f"Warning: S3 file with ID {doc_item} not found")
                                continue
                        # If it's already an object, use it as is
                        elif isinstance(doc_item, dict):
                            documents_data.append(doc_item)
            except Exception as e:
                print(f"Error processing documents: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Prepare RFP data
        rfp_data = {
            # Basic Information
            'rfp_id': rfp.rfp_id,
            'rfp_number': rfp.rfp_number,
            'rfp_title': rfp.rfp_title,
            'description': rfp.description,
            'rfp_type': rfp.rfp_type,
            'category': rfp.category,
            
            # Budget Information
            'estimated_value': float(rfp.estimated_value) if rfp.estimated_value else None,
            'currency': rfp.currency,
            'budget_range_min': float(rfp.budget_range_min) if rfp.budget_range_min else None,
            'budget_range_max': float(rfp.budget_range_max) if rfp.budget_range_max else None,
            
            # Timeline Information
            'issue_date': rfp.issue_date.isoformat() if rfp.issue_date else None,
            'submission_deadline': rfp.submission_deadline.isoformat() if rfp.submission_deadline else None,
            'evaluation_period_end': rfp.evaluation_period_end.isoformat() if rfp.evaluation_period_end else None,
            'award_date': rfp.award_date.isoformat() if rfp.award_date else None,
            
            # Status and Workflow
            'status': rfp.status,
            'created_by': rfp.created_by,
            'approved_by': rfp.approved_by,
            'primary_reviewer_id': rfp.primary_reviewer_id,
            'executive_reviewer_id': rfp.executive_reviewer_id,
            'version_number': rfp.version_number,
            
            # Configuration Options
            'auto_approved': rfp.auto_approved,
            'allow_late_submissions': rfp.allow_late_submissions,
            
            # Workflow and Evaluation
            'approval_workflow_id': rfp.approval_workflow_id,
            'evaluation_method': rfp.evaluation_method,
            'criticality_level': rfp.criticality_level,
            'geographical_scope': rfp.geographical_scope,
            
            # JSON Fields
            'compliance_requirements': rfp.compliance_requirements,
            'custom_fields': rfp.custom_fields,
            'documents': documents_data,  # Expanded documents with full data
            
            # Award Information
            'final_evaluation_score': float(rfp.final_evaluation_score) if rfp.final_evaluation_score else None,
            'award_decision_date': rfp.award_decision_date.isoformat() if rfp.award_decision_date else None,
            'award_justification': rfp.award_justification,
            
            # Timestamps
            'created_at': rfp.created_at.isoformat(),
            'updated_at': rfp.updated_at.isoformat(),
            
            # Evaluation Criteria
            'evaluation_criteria': evaluation_criteria,
            'criteria': evaluation_criteria  # Also include for frontend compatibility
        }
        
        return Response(rfp_data)
        
    except RFP.DoesNotExist:
        return Response({
            'error': f'RFP with ID {rfp_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Failed to fetch RFP details: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def approval_request_versions(request):
    """
    Create a new version for an approval request
    """
    try:
        data = request.data
        
        # Generate version ID
        version_id = f"VR_{uuid.uuid4().hex[:8].upper()}"
        
        # Get the next version number for this approval
        approval_id = data.get('approval_id')
        if not approval_id:
            return Response({
                'success': False,
                'error': 'approval_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Compatibility: If an ApprovalRequest doesn't exist for this approval_id, create a minimal placeholder
        # This allows clients that use rfp_id as approval_id to work without additional coordination
        try:
            ApprovalRequests.objects.get(approval_id=approval_id)
        except ApprovalRequests.DoesNotExist:
            try:
                # Create a minimal approval request record so versions can be tracked
                placeholder_request = {
                    'approval_id': approval_id,
                    'workflow_id': data.get('workflow_id') or 'WF_AUTO',
                    'request_title': data.get('request_title') or 'Auto-created Approval Request',
                    'request_description': data.get('request_description') or 'Auto-created to support versioning',
                    'requester_id': int(data.get('created_by') or 1),
                    'requester_department': data.get('requester_department') or 'General',
                    'priority': data.get('priority') or 'MEDIUM',
                    'request_data': data.get('json_payload') or {},
                    'overall_status': 'DRAFT',
                }
                ApprovalRequests.objects.create(**placeholder_request)
            except Exception:
                # If placeholder creation fails, proceed without blocking version creation
                pass
        
        # Get the highest version number for this approval
        max_version = ApprovalRequestVersions.objects.filter(
            approval_id=approval_id
        ).aggregate(max_version=models.Max('version_number'))['max_version'] or 0
        
        # Create the version
        version = ApprovalRequestVersions.objects.create(
            version_id=version_id,
            approval_id=approval_id,
            version_number=max_version + 1,
            version_label=data.get('version_label', f'Version {max_version + 1}'),
            json_payload=data.get('json_payload', {}),
            changes_summary=data.get('changes_summary', ''),
            created_by=data.get('created_by', 1),
            created_by_name=data.get('created_by_name', 'Unknown'),
            created_by_role=data.get('created_by_role', 'User'),
            version_type=data.get('version_type', 'REVISION'),
            parent_version_id=data.get('parent_version_id'),
            is_current=True,
            is_approved=False,
            change_reason=data.get('change_reason', '')
        )
        
        # Mark all other versions as not current
        ApprovalRequestVersions.objects.filter(
            approval_id=approval_id
        ).exclude(version_id=version_id).update(is_current=False)
        
        return Response({
            'success': True,
            'version_id': version_id,
            'version_number': version.version_number,
            'message': 'Version created successfully'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Failed to create version: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
def get_approval_request_versions(request, approval_id):
    """
    Get all versions for an approval request
    """
    try:
        versions = ApprovalRequestVersions.objects.filter(
            approval_id=approval_id
        ).order_by('-version_number', '-created_at')
        
        versions_data = []
        for version in versions:
            versions_data.append({
                'version_id': version.version_id,
                'approval_id': version.approval_id,
                'version_number': version.version_number,
                'version_label': version.version_label,
                'json_payload': version.json_payload,
                'changes_summary': version.changes_summary,
                'created_by': version.created_by,
                'created_by_name': version.created_by_name,
                'created_by_role': version.created_by_role,
                'version_type': version.version_type,
                'parent_version_id': version.parent_version_id,
                'is_current': version.is_current,
                'is_approved': version.is_approved,
                'change_reason': version.change_reason,
                'created_at': version.created_at.isoformat()
            })
        
        return Response({
            'success': True,
            'approval_id': approval_id,
            'version_count': len(versions_data),
            'versions': versions_data
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Failed to get versions: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('approve_rfp')
def approve_version(request, version_id):
    """
    Approve a specific version
    """
    try:
        data = request.data
        
        # Get the version
        try:
            version = ApprovalRequestVersions.objects.get(version_id=version_id)
        except ApprovalRequestVersions.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Version not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Update version as approved
        version.is_approved = True
        version.save()
        
        return Response({
            'success': True,
            'version_id': version_id,
            'message': 'Version approved successfully'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'error': f'Failed to approve version: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Change Request Management Endpoints
@csrf_exempt
@require_http_methods(["GET", "POST"])
def change_requests(request):
    """
    GET: List change requests dynamically derived from approval data.
    POST: Create a reviewer change request and snapshot the current RFP as a new version.
    """
    try:
        if request.method == 'GET':
            # Optional filter to only show for a specific creator
            creator_id = request.GET.get('creator_id')

            # A change request exists if a stage has requested changes or was rejected
            # and there's a corresponding comment describing the change.
            change_requests_list = []

            # Collect candidate stages that need creator action
            candidate_stages = ApprovalStages.objects.filter(
                stage_status__in=['REJECTED']  # Using REJECTED as REQUEST_CHANGES is mapped to REJECTED
            ).order_by('-updated_at')

            for stage in candidate_stages:
                try:
                    # Get the approval request to enrich with context
                    approval_request = ApprovalRequests.objects.get(approval_id=stage.approval_id)

                    # Filter to only workflows for business_object_type == 'RFP'
                    try:
                        workflow = ApprovalWorkflows.objects.get(workflow_id=approval_request.workflow_id)
                        if (workflow.business_object_type or '').upper() != 'RFP':
                            continue
                    except ApprovalWorkflows.DoesNotExist:
                        continue

                    # Optionally filter by creator
                    if creator_id and str(approval_request.requester_id) != str(creator_id):
                        continue

                    # Resolve RFP title/id from request_data when available
                    rfp_id = None
                    rfp_title = 'Untitled RFP'
                    request_data = approval_request.request_data
                    try:
                        if isinstance(request_data, str):
                            request_data = json.loads(request_data)
                    except Exception:
                        pass
                    if isinstance(request_data, dict):
                        # Prefer canonical public identifier if present
                        rfp_id = request_data.get('rfp_id')
                        rfp_title = request_data.get('rfp_title') or request_data.get('title') or rfp_title
                        # If only numeric id present, translate to public rfp_id
                        if not rfp_id and request_data.get('id'):
                            try:
                                numeric_id = int(request_data.get('id'))
                                from rfp.models import RFP as RFPModel
                                rfp_obj = RFPModel.objects.get(id=numeric_id)
                                rfp_id = rfp_obj.rfp_id
                                if not rfp_title:
                                    rfp_title = rfp_obj.rfp_title
                            except Exception:
                                pass

                    # If still not present, try to get from RFP by workflow link
                    if not rfp_title or not rfp_id:
                        try:
                            linked_rfp = RFP.objects.get(approval_workflow_id=approval_request.workflow_id)
                            rfp_id = rfp_id or linked_rfp.rfp_id
                            rfp_title = rfp_title or linked_rfp.rfp_title
                        except Exception:
                            pass

                    # Find latest change-related comment on this stage
                    last_comment = (
                        ApprovalComments.objects
                        .filter(approval_id=approval_request.approval_id, stage_id=stage.stage_id)
                        .order_by('-created_at')
                        .first()
                    )

                    description = last_comment.comment_text if last_comment else 'Changes requested by reviewer.'
                    requested_at = last_comment.created_at.isoformat() if last_comment and last_comment.created_at else None

                    change_requests_list.append({
                        'change_request_id': f"CR_{stage.stage_id}",
                        'rfp_id': rfp_id,
                        'rfp_title': rfp_title,
                        'approval_id': approval_request.approval_id,
                        'stage_id': stage.stage_id,
                        'stage_name': stage.stage_name,
                        'requested_by': stage.assigned_user_id,
                        'requested_by_name': stage.assigned_user_name,
                        'requested_by_role': stage.assigned_user_role,
                        'change_request_description': description,
                        'specific_fields': [],
                        'status': 'pending',
                        'priority': approval_request.priority or 'MEDIUM',
                        'requested_at': requested_at,
                    })
                except Exception:
                    # Skip any malformed records, continue listing others
                    continue

            return JsonResponse({
                'success': True,
                'change_requests': change_requests_list,
                'total': len(change_requests_list)
            })

        elif request.method == 'POST':
            # Create new reviewer-originated change request and snapshot current RFP
            data = json.loads(request.body or '{}')

            change_request_id = f"CR_{uuid.uuid4().hex[:8].upper()}"

            approval_id = data.get('approval_id')
            rfp_id = data.get('rfp_id')
            requested_by = data.get('requested_by') or 1
            requested_by_name = data.get('requested_by_name') or 'Reviewer'
            requested_by_role = data.get('requested_by_role') or 'Reviewer'
            description = data.get('change_request_description') or 'Reviewer requested changes'

            created_version_id = None
            try:
                if approval_id and rfp_id:
                    from rfp.models import RFP
                    from rfp.serializers import RFPSerializer

                    rfp = RFP.objects.get(rfp_id=rfp_id)
                    rfp_payload = RFPSerializer(rfp).data

                    version_id = f"VR_{uuid.uuid4().hex[:8].upper()}"
                    max_version = ApprovalRequestVersions.objects.filter(
                        approval_id=approval_id
                    ).aggregate(max_version=models.Max('version_number'))['max_version'] or 0

                    ApprovalRequestVersions.objects.create(
                        version_id=version_id,
                        approval_id=approval_id,
                        version_number=max_version + 1,
                        version_label=f'Revision {max_version + 1}',
                        json_payload=rfp_payload,
                        changes_summary=description,
                        created_by=int(requested_by),
                        created_by_name=requested_by_name,
                        created_by_role=requested_by_role,
                        version_type='REVISION',
                        parent_version_id=None,
                        is_current=True,
                        is_approved=False,
                        change_reason=description
                    )
                    ApprovalRequestVersions.objects.filter(
                        approval_id=approval_id
                    ).exclude(version_id=version_id).update(is_current=False)

                    created_version_id = version_id
            except Exception as ve:
                print(f"Warning: Failed creating approval version on change request: {ve}")

            return JsonResponse({
                'success': True,
                'change_request_id': change_request_id,
                'message': 'Change request created successfully',
                'change_request': {
                    'change_request_id': change_request_id,
                    'rfp_id': rfp_id,
                    'approval_id': approval_id,
                    'stage_id': data.get('stage_id'),
                    'requested_by': requested_by,
                    'requested_by_name': requested_by_name,
                    'requested_by_role': requested_by_role,
                    'change_request_description': description,
                    'specific_fields': data.get('specific_fields', []),
                    'status': 'pending',
                    'priority': data.get('priority', 'MEDIUM'),
                    'requested_at': timezone.now().isoformat(),
                    'created_version_id': created_version_id
                }
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Failed to process change request',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def respond_to_change_request(request):
    """
    Respond to a change request (accept, decline, or complete)
    - accepted/declined: acknowledge the request
    - completed: persist a new ApprovalRequestVersions row with the latest RFP JSON and resume workflow from the same stage
    """
    try:
        data = json.loads(request.body or '{}')
        change_request_id = data.get('change_request_id')
        new_status = data.get('status')  # 'accepted', 'declined', 'completed'
        response_notes = data.get('response_notes', '')
        changes_made = data.get('changes_made', '')
        additional_notes = data.get('additional_notes', '')

        if not change_request_id or not new_status:
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: change_request_id and status'
            }, status=400)

        approval_id = data.get('approval_id')
        stage_id = data.get('stage_id')

        response_payload = {
            'change_request_id': change_request_id,
            'status': new_status,
            'response_notes': response_notes,
            'changes_made': changes_made,
            'additional_notes': additional_notes,
            'responded_at': timezone.now().isoformat(),
            'responded_by': data.get('responded_by', '1')
        }

        # On completion, create a persisted version and move the workflow forward from the same stage
        if new_status == 'completed' and approval_id:
            try:
                # Determine the JSON payload to persist
                # Prefer explicit json_payload from client; fallback to current RFP snapshot by rfp_id
                json_payload = data.get('json_payload')

                if not json_payload:
                    rfp_id = data.get('rfp_id')
                    if rfp_id:
                        from rfp.models import RFP
                        from rfp.serializers import RFPSerializer
                        rfp = RFP.objects.get(rfp_id=rfp_id)
                        json_payload = RFPSerializer(rfp).data
                    else:
                        json_payload = {}

                # Create new version row
                version_id = f"VR_{uuid.uuid4().hex[:8].upper()}"
                max_version = ApprovalRequestVersions.objects.filter(
                    approval_id=approval_id
                ).aggregate(max_version=models.Max('version_number'))['max_version'] or 0

                ApprovalRequestVersions.objects.create(
                    version_id=version_id,
                    approval_id=approval_id,
                    version_number=max_version + 1,
                    version_label=f'Revision {max_version + 1}',
                    json_payload=json_payload,
                    changes_summary=changes_made or 'Creator submitted revisions',
                    created_by=int(data.get('responded_by') or 1),
                    created_by_name=data.get('responded_by_name', 'RFP Creator'),
                    created_by_role='Creator',
                    version_type='REVISION',
                    parent_version_id=None,
                    is_current=True,
                    is_approved=False,
                    change_reason=response_notes
                )
                ApprovalRequestVersions.objects.filter(
                    approval_id=approval_id
                ).exclude(version_id=version_id).update(is_current=False)

                response_payload['new_version_id'] = version_id

                # Resume the workflow from the same stage onward
                try:
                    # Reset the rejected/request-changes stage back to PENDING
                    if stage_id:
                        try:
                            stage = ApprovalStages.objects.get(stage_id=stage_id)
                            stage.stage_status = 'PENDING'
                            stage.rejection_reason = None
                            stage.response_data = None
                            stage.started_at = None
                            stage.completed_at = None
                            stage.updated_at = timezone.now()
                            stage.save()
                        except ApprovalStages.DoesNotExist:
                            pass

                    # Set overall approval back to IN_PROGRESS
                    try:
                        approval_request = ApprovalRequests.objects.get(approval_id=approval_id)
                        approval_request.overall_status = 'IN_PROGRESS'
                        approval_request.updated_at = timezone.now()
                        approval_request.save()

                        # Also attempt to sync RFP status
                        try:
                            update_rfp_status_based_on_approval(approval_request)
                        except Exception:
                            pass
                    except ApprovalRequests.DoesNotExist:
                        pass
                    
                    # Persist the latest JSON into approval_requests.request_data for reviewer context
                    try:
                        if json_payload is not None:
                            approval_request = ApprovalRequests.objects.get(approval_id=approval_id)
                            approval_request.request_data = json_payload
                            approval_request.updated_at = timezone.now()
                            approval_request.save()
                    except ApprovalRequests.DoesNotExist:
                        pass
                except Exception:
                    pass
            except Exception as ve:
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to complete change request: {str(ve)}'
                }, status=500)

        return JsonResponse({
            'success': True,
            'message': f'Change request {new_status} successfully',
            'response_data': response_payload
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Failed to respond to change request',
            'message': str(e)
        }, status=500)
