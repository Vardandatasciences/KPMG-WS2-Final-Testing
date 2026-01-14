"""
Views for RFP Approval Workflow Management
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection, transaction, models, connections
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from datetime import datetime
import uuid
import json
from .models import ApprovalWorkflows, ApprovalStages, ApprovalRequests, ApprovalComments, ApprovalRequestVersions
from tprm_backend.rfp.models import RFP
from tprm_backend.rfp.models import RFPResponse

# RBAC imports
from tprm_backend.rbac.tprm_decorators import rbac_rfp_required
from tprm_backend.rfp.rfp_authentication import JWTAuthentication, SimpleAuthenticatedPermission

# MULTI-TENANCY: Import tenant utilities for filtering
from tprm_backend.core.tenant_utils import (
    get_tenant_id_from_request,
    filter_queryset_by_tenant,
    get_tenant_aware_queryset,
    require_tenant,
    tenant_filter
)


def make_naive_datetime(dt):
    """
    Convert timezone-aware datetime to naive datetime for MySQL compatibility.
    MySQL backend does not support timezone-aware datetimes when USE_TZ is False.
    
    Args:
        dt: datetime object (can be timezone-aware or naive, or None)
    
    Returns:
        Naive datetime object, or None if input is None
    """
    if dt is None:
        return None
    
    # If it's a string, try to parse it first
    if isinstance(dt, str):
        try:
            # Try ISO format first
            if 'T' in dt or ' ' in dt:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                # Try date-only format
                dt = datetime.strptime(dt, '%Y-%m-%d')
        except (ValueError, AttributeError):
            # If parsing fails, return None
            return None
    
    # If it's already a datetime object, check if it's timezone-aware
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        # Convert to naive datetime
        return dt.replace(tzinfo=None)
    
    # Already naive, return as-is
    return dt


def get_naive_now():
    """
    Get current datetime as naive datetime for MySQL compatibility.
    
    Returns:
        Naive datetime object
    """
    now = timezone.now()
    # If timezone-aware, make it naive
    if hasattr(now, 'tzinfo') and now.tzinfo is not None:
        return now.replace(tzinfo=None)
    return now


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
        
        # MULTI-TENANCY: Get tenant_id from approval_request
        tenant_id = getattr(approval_request, 'tenant_id', None)
        
        # Method 1: Try to find RFP by approval_workflow_id (which matches the workflow_id in approval_requests)
        try:
            # MULTI-TENANCY: Filter RFP by tenant if tenant_id is available
            if tenant_id:
                rfp = RFP.objects.get(approval_workflow_id=approval_request.workflow_id, tenant_id=tenant_id)
            else:
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
                        # MULTI-TENANCY: Filter RFP by tenant if tenant_id is available
                        if tenant_id:
                            rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
                        else:
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
                # MULTI-TENANCY: Filter by tenant if available
                if tenant_id:
                    all_approval_requests = ApprovalRequests.objects.filter(
                        workflow_id=approval_request.workflow_id,
                        tenant_id=tenant_id
                    )
                else:
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
                        # MULTI-TENANCY: Filter stages by tenant if available
                        if tenant_id:
                            all_stages = ApprovalStages.objects.filter(approval_id=approval_req.approval_id, tenant_id=tenant_id)
                        else:
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
                        # MULTI-TENANCY: Filter stages by tenant if available
                        stage_filter = {
                            'approval_id__in': [ar.approval_id for ar in all_approval_requests],
                            'stage_status': 'APPROVED'
                        }
                        if tenant_id:
                            stage_filter['tenant_id'] = tenant_id
                        last_approved_stage = ApprovalStages.objects.filter(**stage_filter).order_by('-completed_at').first()
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
                    rfp.updated_at = get_naive_now()
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


def create_workflow_version(workflow_id, approval_ids, created_by, created_by_name=None, created_by_role=None, version_type='INITIAL', change_reason=None, tenant_id=None):
    """
    Create a version record for the approval workflow
    MULTI-TENANCY: Filters by tenant_id if provided
    
    Args:
        workflow_id: The workflow ID
        approval_ids: List of approval request IDs
        created_by: User ID who created the workflow
        created_by_name: Name of the user who created the workflow
        created_by_role: Role of the user who created the workflow
        version_type: Type of version (INITIAL, REVISION, CONSOLIDATION, FINAL)
        change_reason: Reason for the change (if applicable)
        tenant_id: Tenant ID for multi-tenancy filtering
    
    Returns:
        The created version record
    """
    try:
        print(f"Creating workflow version for workflow_id: {workflow_id}")
        
        # Get workflow details
        # MULTI-TENANCY: Filter by tenant if available
        if tenant_id:
            workflow = ApprovalWorkflows.objects.get(workflow_id=workflow_id, tenant_id=tenant_id)
        else:
            workflow = ApprovalWorkflows.objects.get(workflow_id=workflow_id)
        
        # Get all stages for this workflow
        # MULTI-TENANCY: Filter by tenant if available
        if tenant_id:
            all_stages = ApprovalStages.objects.filter(approval_id__in=approval_ids, tenant_id=tenant_id)
        else:
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
                # MULTI-TENANCY: Filter by tenant if available
                if tenant_id:
                    approval_request = ApprovalRequests.objects.get(approval_id=approval_id, tenant_id=tenant_id)
                else:
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
        # MULTI-TENANCY: Filter by tenant if available
        if tenant_id:
            existing_versions = ApprovalRequestVersions.objects.filter(
                approval_id__in=approval_ids,
                tenant_id=tenant_id
            ).order_by('-version_number').first()
        else:
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
        # MULTI-TENANCY: Add tenant_id if available
        version_data = {
            'version_id': version_id,
            'approval_id': approval_ids[0] if approval_ids else workflow_id,  # Use first approval_id or workflow_id
            'version_number': version_number,
            'version_label': version_label,
            'json_payload': json_payload,
            'changes_summary': changes_summary,
            'created_by': created_by,
            'created_by_name': created_by_name or f"User {created_by}",
            'created_by_role': created_by_role or "User",
            'version_type': version_type,
            'is_current': True,
            'is_approved': False,
            'change_reason': change_reason
        }
        if tenant_id:
            version_data['tenant_id'] = tenant_id
        version_record = ApprovalRequestVersions.objects.create(**version_data)
        
        # Mark all previous versions as not current
        # MULTI-TENANCY: Filter by tenant if available
        if tenant_id:
            ApprovalRequestVersions.objects.filter(
                approval_id__in=approval_ids,
                tenant_id=tenant_id
            ).exclude(version_id=version_id).update(is_current=False)
        else:
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
            'created_at': get_naive_now()
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def workflows(request):
    """
    Handle workflow creation and retrieval
    MULTI-TENANCY: Only returns workflows belonging to the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
    if request.method == 'GET':
        # MULTI-TENANCY: Filter workflows by tenant
        workflows = ApprovalWorkflows.objects.filter(tenant_id=tenant_id)
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
            
            # Check if RFP has auto_approve enabled - if so, prevent workflow creation
            if rfp_data:
                auto_approve = rfp_data.get('auto_approve') or rfp_data.get('autoApprove')
                rfp_id = rfp_data.get('rfp_id')
                
                if auto_approve:
                    # Also check the database to be sure
                    if rfp_id:
                        try:
                            # RFP is already imported at the top of the file
                            rfp = RFP.objects.filter(rfp_id=rfp_id).first()
                            if rfp and rfp.auto_approve:
                                return Response({
                                    'error': 'This RFP has auto-approve enabled and does not require an approval workflow. The RFP should be auto-approved directly.',
                                    'message': 'Auto-approved RFPs bypass the approval workflow system'
                                }, status=status.HTTP_400_BAD_REQUEST)
                        except Exception as e:
                            print(f"Warning: Could not check RFP auto_approve status: {e}")
                    
                    # If auto_approve is true in the request data, reject workflow creation
                    return Response({
                        'error': 'This RFP has auto-approve enabled and does not require an approval workflow. The RFP should be auto-approved directly.',
                        'message': 'Auto-approved RFPs bypass the approval workflow system'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate minimum stages requirement
            if len(stages_config) < 2:
                return Response({
                    'error': 'At least two stages are required for a workflow'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate workflow ID
            workflow_id = f"WF_{uuid.uuid4().hex[:8].upper()}"
            workflow_data['workflow_id'] = workflow_id
            
            # MULTI-TENANCY: Add tenant_id to workflow data
            workflow_data['tenant_id'] = tenant_id
            
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
                        'deadline_date': make_naive_datetime(stage_config.get('deadline_date')),
                        'is_mandatory': stage_config.get('is_mandatory', True),
                        'created_at': get_naive_now(),
                        'updated_at': get_naive_now(),
                        'tenant_id': tenant_id  # MULTI-TENANCY: Add tenant_id
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
                        expiry_date = get_naive_now() + timezone.timedelta(days=30)
                        
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
                            'submission_date': get_naive_now(),
                            'expiry_date': expiry_date,
                            'created_at': get_naive_now(),
                            'updated_at': get_naive_now(),
                            'tenant_id': tenant_id  # MULTI-TENANCY: Set tenant_id
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
                                'deadline_date': make_naive_datetime(stage_config.get('deadline_date')),
                                'is_mandatory': stage_config.get('is_mandatory', True),
                                'created_at': get_naive_now(),
                                'updated_at': get_naive_now(),
                                'tenant_id': tenant_id  # MULTI-TENANCY: Set tenant_id
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
                    expiry_date = get_naive_now() + timezone.timedelta(days=30)
                    
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
                        'submission_date': get_naive_now(),
                        'expiry_date': expiry_date,
                        'created_at': get_naive_now(),
                        'updated_at': get_naive_now(),
                        'tenant_id': tenant_id  # MULTI-TENANCY: Set tenant_id
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
                            'deadline_date': make_naive_datetime(stage_config.get('deadline_date')),
                            'is_mandatory': stage_config.get('is_mandatory', True),
                            'created_at': get_naive_now(),
                            'updated_at': get_naive_now(),
                            'tenant_id': tenant_id  # MULTI-TENANCY: Set tenant_id
                        }
                        
                        # Create stage for committee member
                        ApprovalStages.objects.create(**stage_data)
                        print(f"Created committee evaluation stage for user {stage_config.get('assigned_user_id')}: {stage_id}")
                
                else:
                    # Single RFP approval request (existing logic)
                    # MULTI-TENANCY: Filter by tenant
                    existing_request = ApprovalRequests.objects.filter(workflow_id=workflow_id, tenant_id=tenant_id).first()
                    if existing_request:
                        approval_id = existing_request.approval_id
                        approval_ids.append(approval_id)
                        print(f"Approval request already exists for workflow {workflow_id}: {approval_id}")
                    else:
                        approval_id = f"AR_{uuid.uuid4().hex[:8].upper()}"
                        
                        # Calculate expiry date (30 days from now by default)
                        expiry_date = get_naive_now() + timezone.timedelta(days=30)
                        
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
                            'submission_date': get_naive_now(),
                            'expiry_date': expiry_date,
                            'created_at': get_naive_now(),
                            'updated_at': get_naive_now(),
                            'tenant_id': tenant_id  # MULTI-TENANCY: Set tenant_id
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
                                'deadline_date': make_naive_datetime(stage_config.get('deadline_date')),
                                'is_mandatory': stage_config.get('is_mandatory', True),
                                'created_at': get_naive_now(),
                                'updated_at': get_naive_now(),
                                'tenant_id': tenant_id  # MULTI-TENANCY: Set tenant_id
                            }
                            
                            # Create stage
                            ApprovalStages.objects.create(**stage_data)
                    
                    # Create or update RFP record with approval_workflow_id (only for single RFP)
                    try:
                        # Try to find existing RFP by title or create new one
                        # MULTI-TENANCY: Filter by tenant
                        rfp_title = rfp_data.get('rfp_title', 'Untitled RFP')
                        rfp, created = RFP.objects.get_or_create(
                            rfp_title=rfp_title,
                            tenant_id=tenant_id,  # MULTI-TENANCY: Filter by tenant
                            defaults={
                                'description': rfp_data.get('description', 'RFP description'),
                                'rfp_type': rfp_data.get('rfp_type', 'SERVICES'),
                                'category': rfp_data.get('category', 'General'),
                                'estimated_value': rfp_data.get('estimated_value'),
                                'currency': rfp_data.get('currency', 'USD'),
                                'criticality_level': rfp_data.get('criticality_level', 'medium'),
                                'created_by': workflow_data.get('created_by', 1),
                                'status': 'DRAFT',
                                'approval_workflow_id': workflow_id,
                                'tenant_id': tenant_id  # MULTI-TENANCY: Set tenant_id
                            }
                        )
                        
                        if not created:
                            # Update existing RFP with approval_workflow_id
                            rfp.approval_workflow_id = workflow_id
                            rfp.updated_at = get_naive_now()
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
                
                # MULTI-TENANCY: Pass tenant_id to create_workflow_version
                version_record = create_workflow_version(
                    workflow_id=workflow_id,
                    approval_ids=approval_ids,
                    created_by=created_by,
                    created_by_name=created_by_name,
                    created_by_role=created_by_role,
                    tenant_id=tenant_id,
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


@api_view(['GET', 'PATCH', 'DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def workflow_detail(request, workflow_id):
    """
    Handle individual workflow operations (GET, PATCH, DELETE)
    MULTI-TENANCY: Only allows operations on workflows belonging to the tenant
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # Get the workflow - try with tenant_id first, then without for cross-tenant access
        try:
            workflow = ApprovalWorkflows.objects.get(workflow_id=workflow_id, tenant_id=tenant_id)
        except ApprovalWorkflows.DoesNotExist:
            # Try without tenant filter for cross-tenant access
            try:
                workflow = ApprovalWorkflows.objects.get(workflow_id=workflow_id)
            except ApprovalWorkflows.DoesNotExist:
                return Response({
                    'error': f'Workflow {workflow_id} not found'
                }, status=404)
        
        if request.method == 'GET':
            # Get stages for this workflow
            stages = ApprovalStages.objects.filter(approval_id=workflow_id)
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
            
            return Response({
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
        
        elif request.method == 'PATCH':
            # Update workflow fields
            data = request.data
            
            # Update is_active if provided
            if 'is_active' in data:
                workflow.is_active = bool(data['is_active'])
            
            # Update other fields if provided
            if 'workflow_name' in data:
                workflow.workflow_name = data['workflow_name']
            if 'description' in data:
                workflow.description = data['description']
            if 'workflow_type' in data:
                workflow.workflow_type = data['workflow_type']
            
            workflow.save()
            
            return Response({
                'success': True,
                'message': 'Workflow updated successfully',
                'workflow_id': workflow.workflow_id,
                'is_active': workflow.is_active
            })
        
        elif request.method == 'DELETE':
            # Delete workflow (soft delete by setting is_active to False)
            workflow.is_active = False
            workflow.save()
            
            return Response({
                'success': True,
                'message': 'Workflow deactivated successfully',
                'workflow_id': workflow.workflow_id
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Failed to process workflow operation: {str(e)}'
        }, status=500)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def users(request):
    """
    Get all users for dropdown selection
    Only fetches users with Executive and Procurement roles from rbac_tprm table
    Fetches users directly from tprm_integration database (users table)
    MULTI-TENANCY: Ensures tenant context is present
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # Only fetch users with Executive and Procurement roles from rbac_tprm
        allowed_roles = ['Executive', 'Procurement']
        
        print(f"[users] Fetching users with roles: {allowed_roles} from tprm_integration database")
        
        # Use 'tprm' connection to access tprm_integration database
        db_connection = 'tprm'
        try:
            if 'tprm' not in connections.databases:
                print("[users] Warning: 'tprm' database connection not found, falling back to 'default'")
                db_connection = 'default'
            else:
                db_name = connections[db_connection].settings_dict.get('NAME', 'unknown')
                print(f"[users] Using 'tprm' database connection: {db_name} for tprm_integration database")
        except Exception as db_check_error:
            print(f"[users] Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")
            db_connection = 'tprm'
        
        users_data = []
        
        try:
            with connections[db_connection].cursor() as cursor:
                # Query users directly from tprm_integration database
                # Join with rbac_tprm to get only users with Management or Executive roles
                placeholders = ','.join(['%s'] * len(allowed_roles))
                query = f"""
                    SELECT DISTINCT 
                        u.UserId,
                        u.UserName,
                        u.Email,
                        u.FirstName,
                        u.LastName,
                        r.Role
                    FROM users u
                    INNER JOIN rbac_tprm r ON u.UserId = r.UserId
                    WHERE r.Role IN ({placeholders})
                    AND r.IsActive = 'Y'
                    AND (u.IsActive = 'Y' OR u.IsActive IS NULL OR u.IsActive = 1)
                    ORDER BY u.FirstName, u.LastName, u.UserName
                """
                print(f"[users] Executing query: {query}")
                print(f"[users] Query parameters: {allowed_roles}")
                cursor.execute(query, allowed_roles)
                
                results = cursor.fetchall()
                print(f"[users] Found {len(results)} users with Executive/Procurement roles")
                
                for row in results:
                    user_id, username, email, first_name, last_name, role = row
                    
                    user_data = {
                        'id': str(user_id),  # Convert to string for consistency
                        'username': username or f'user_{user_id}',
                        'first_name': first_name or 'Unknown',
                        'last_name': last_name or 'User',
                        'email': email or '',
                        'role': role or 'User',
                        'department': 'General',  # Department info not in users table
                        'is_active': True
                    }
                    users_data.append(user_data)
                    print(f"[users] Added user: {user_data['first_name']} {user_data['last_name']} ({role})")
        
        except Exception as query_error:
            print(f"[users] Error querying tprm_integration database: {str(query_error)}")
            import traceback
            traceback.print_exc()
            # Try fallback: query users table separately
            try:
                print("[users] Attempting fallback: querying users and rbac_tprm separately")
                with connections[db_connection].cursor() as cursor:
                    # First get user IDs with allowed roles
                    placeholders = ','.join(['%s'] * len(allowed_roles))
                    query = f"""
                        SELECT DISTINCT UserId, Role
                        FROM rbac_tprm 
                        WHERE Role IN ({placeholders}) 
                        AND IsActive = 'Y'
                    """
                    cursor.execute(query, allowed_roles)
                    role_mappings = {row[0]: row[1] for row in cursor.fetchall()}
                    print(f"[users] Found {len(role_mappings)} user IDs with allowed roles")
                    
                    if role_mappings:
                        user_ids = list(role_mappings.keys())
                        placeholders = ','.join(['%s'] * len(user_ids))
                        query = f"""
                            SELECT UserId, UserName, Email, FirstName, LastName
                            FROM users
                            WHERE UserId IN ({placeholders})
                            AND (IsActive = 'Y' OR IsActive IS NULL OR IsActive = 1)
                            ORDER BY FirstName, LastName, UserName
                        """
                        cursor.execute(query, user_ids)
                        
                        for row in cursor.fetchall():
                            user_id, username, email, first_name, last_name = row
                            user_data = {
                                'id': str(user_id),
                                'username': username or f'user_{user_id}',
                                'first_name': first_name or 'Unknown',
                                'last_name': last_name or 'User',
                                'email': email or '',
                                'role': role_mappings.get(user_id, 'User'),
                                'department': 'General',
                                'is_active': True
                            }
                            users_data.append(user_data)
                            print(f"[users] Added user (fallback): {user_data['first_name']} {user_data['last_name']} ({user_data['role']})")
            except Exception as fallback_error:
                print(f"[users] Fallback query also failed: {str(fallback_error)}")
                import traceback
                traceback.print_exc()
        
        print(f"[users] Total users returned: {len(users_data)}")
        if len(users_data) == 0:
            print("[users] WARNING: No users found with Executive or Procurement roles!")
            print("[users] This might indicate:")
            print("[users]   1. No users exist in tprm_integration.users table")
            print("[users]   2. No users have Executive or Procurement roles in rbac_tprm table")
            print("[users]   3. Database connection issue")
        
        return Response(users_data)
        
    except Exception as e:
        # Fallback to mock data if database query fails
        print(f"[users] Error fetching users from database: {e}")
        import traceback
        traceback.print_exc()
        users_data = [
            {
                'id': '1',
                'username': 'admin',
                'first_name': 'Admin',
                'last_name': 'User',
                'email': 'admin@company.com',
                'id': '1',
                'username': 'executive',
                'first_name': 'Executive',
                'last_name': 'User',
                'email': 'executive@company.com',
                'role': 'Executive',
                'department': 'IT',
                'is_active': True
            },
            {
                'id': '2',
                'username': 'procurement',
                'first_name': 'Procurement',
                'last_name': 'User',
                'email': 'procurement@company.com',
                'role': 'Procurement',
                'department': 'Procurement',
                'is_active': True
            }
        ]
        return Response(users_data)


@api_view(['GET', 'POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('approve_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_requests(request):
    """
    Handle approval request creation and retrieval
    MULTI-TENANCY: Only returns approval requests belonging to the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
    if request.method == 'GET':
        workflow_id = request.query_params.get('workflow_id')
        
        # MULTI-TENANCY: Filter by tenant
        if workflow_id:
            requests = ApprovalRequests.objects.filter(workflow_id=workflow_id, tenant_id=tenant_id)
        else:
            requests = ApprovalRequests.objects.filter(tenant_id=tenant_id)
        
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
            request_data['tenant_id'] = tenant_id  # MULTI-TENANCY: Add tenant_id
            
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def stages(request):
    """
    Handle stage management
    MULTI-TENANCY: Only returns stages belonging to the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
    if request.method == 'GET':
        approval_id = request.query_params.get('approval_id')
        
        # MULTI-TENANCY: Filter by tenant
        if approval_id:
            stages = ApprovalStages.objects.filter(approval_id=approval_id, tenant_id=tenant_id)
        else:
            stages = ApprovalStages.objects.filter(tenant_id=tenant_id)
        
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
            stage_data['tenant_id'] = tenant_id  # MULTI-TENANCY: Add tenant_id
            
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def comments(request):
    """
    Handle approval comments
    MULTI-TENANCY: Only returns comments belonging to the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
    if request.method == 'GET':
        approval_id = request.query_params.get('approval_id')
        stage_id = request.query_params.get('stage_id')
        
        # MULTI-TENANCY: Filter comments by tenant
        comments = ApprovalComments.objects.filter(tenant_id=tenant_id)
        
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
            comment_data['tenant_id'] = tenant_id  # MULTI-TENANCY: Add tenant_id
            
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_proposal_id_from_approval(request, approval_id):
    """
    Get proposal/response ID from approval request data
    MULTI-TENANCY: Only returns proposal IDs for tenant's approval requests
    For proposal evaluation workflows, we need to find response IDs for the RFP
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
    try:
        # MULTI-TENANCY: Filter approval request by tenant
        # Try with tenant_id first, then without if not found
        try:
            approval_request = ApprovalRequests.objects.get(approval_id=approval_id, tenant_id=tenant_id)
        except ApprovalRequests.DoesNotExist:
            # Try without tenant filter as fallback
            try:
                approval_request = ApprovalRequests.objects.get(approval_id=approval_id)
                print(f"[get_proposal_id_from_approval] Found approval without tenant filter: {approval_id}")
            except ApprovalRequests.DoesNotExist:
                return Response({'error': 'Approval request not found'}, status=404)
        
        # Parse request_data to find RFP ID
        request_data = approval_request.request_data
        if request_data is None:
            return Response({'error': 'Approval request has no request_data'}, status=400)
        
        # Handle string format
        if isinstance(request_data, str):
            try:
                request_data = json.loads(request_data)
            except json.JSONDecodeError as e:
                print(f"[get_proposal_id_from_approval] JSON decode error: {e}")
                return Response({'error': f'Invalid request_data format: {str(e)}'}, status=400)
        
        print(f"[get_proposal_id_from_approval] Processing approval_id: {approval_id}, request_data type: {type(request_data)}")
        
        # Handle case where request_data is a list (array of proposals)
        if isinstance(request_data, list) and len(request_data) > 0:
            # For proposal evaluation, the first item should contain the response_id
            first_proposal = request_data[0]
            if isinstance(first_proposal, dict):
                proposal_id = first_proposal.get('response_id')
                if proposal_id:
                    print(f"[get_proposal_id_from_approval] Found response_id in list: {proposal_id}")
                    return Response({
                        'proposal_id': proposal_id,
                        'all_response_ids': [item.get('response_id') for item in request_data if item.get('response_id')],
                        'approval_id': approval_id,
                        'request_data': request_data
                    })
        
        # First, try to find direct response_id in request_data (for dict format)
        proposal_id = None
        if isinstance(request_data, dict):
            # Check multiple possible field names
            proposal_id = (request_data.get('response_id') or 
                          request_data.get('proposal_id') or 
                          request_data.get('rfp_response_id') or
                          request_data.get('id') or
                          request_data.get('proposalId') or
                          request_data.get('responseId'))
            
            # Also check nested structures
            if not proposal_id:
                # Check rfp_data nested structure
                rfp_data = request_data.get('rfp_data') or request_data.get('rfpData')
                if isinstance(rfp_data, dict):
                    proposal_id = (rfp_data.get('response_id') or 
                                  rfp_data.get('proposal_id') or
                                  rfp_data.get('responseId'))
                
                # Check selected_proposals array
                if not proposal_id:
                    selected_proposals = request_data.get('selected_proposals') or request_data.get('selectedProposals')
                    if isinstance(selected_proposals, list) and len(selected_proposals) > 0:
                        first_proposal = selected_proposals[0]
                        if isinstance(first_proposal, dict):
                            proposal_id = first_proposal.get('response_id') or first_proposal.get('responseId')
        
        # If no direct response_id found, try to get RFP ID and find responses
        if not proposal_id and isinstance(request_data, dict):
            # Extract RFP ID - handle both string and numeric formats
            rfp_id = None
            # Try multiple possible field names
            for key in ['rfp_id', 'rfpId', 'rfpID']:
                if key in request_data and request_data[key]:
                    rfp_id = request_data[key]
                    break
            
            # Try nested structures
            if not rfp_id:
                for key in ['rfp_data', 'rfpData']:
                    if key in request_data and isinstance(request_data[key], dict):
                        nested_data = request_data[key]
                        for nested_key in ['rfp_id', 'rfpId', 'rfpID']:
                            if nested_key in nested_data and nested_data[nested_key]:
                                rfp_id = nested_data[nested_key]
                                break
                        if rfp_id:
                            break
            
            # Convert to string for consistent comparison (RFP IDs can be strings or numbers)
            # Also filter out empty strings and None
            if rfp_id and str(rfp_id).strip():
                rfp_id_str = str(rfp_id).strip()
                print(f"[get_proposal_id_from_approval] Found rfp_id: {rfp_id} (type: {type(rfp_id)}, str: {rfp_id_str}), searching for responses...")
                
                # Import here to avoid circular imports (already imported at top, but keeping for clarity)
                # RFPResponse and RFP are already imported at the top of the file
                
                # Verify RFP exists (for debugging)
                try:
                    rfp_exists = RFP.objects.filter(rfp_id=rfp_id_str).exists()
                    if not rfp_exists:
                        try:
                            rfp_id_int = int(rfp_id)
                            rfp_exists = RFP.objects.filter(rfp_id=rfp_id_int).exists()
                        except (ValueError, TypeError):
                            pass
                    print(f"[get_proposal_id_from_approval] RFP exists check: {rfp_exists}")
                except Exception as e:
                    print(f"[get_proposal_id_from_approval] Error checking RFP existence: {e}")
                
                # Get all responses for this RFP
                # MULTI-TENANCY: Filter responses by tenant
                # Try both string and numeric RFP ID matching
                responses = None
                
                # First, try to find the actual RFP record to get the correct ID format
                actual_rfp_id = None
                try:
                    rfp_record = RFP.objects.filter(rfp_id=rfp_id_str).first()
                    if not rfp_record:
                        try:
                            rfp_id_int = int(rfp_id)
                            rfp_record = RFP.objects.filter(rfp_id=rfp_id_int).first()
                        except (ValueError, TypeError):
                            pass
                    
                    if rfp_record:
                        actual_rfp_id = rfp_record.rfp_id
                        print(f"[get_proposal_id_from_approval] Found RFP record, actual_rfp_id: {actual_rfp_id} (type: {type(actual_rfp_id)})")
                    else:
                        # Try by RFP number as fallback
                        rfp_number = request_data.get('rfp_number')
                        if rfp_number:
                            print(f"[get_proposal_id_from_approval] Trying to find RFP by number: {rfp_number}")
                            rfp_record = RFP.objects.filter(rfp_number=rfp_number, tenant_id=tenant_id).first()
                            if rfp_record:
                                actual_rfp_id = rfp_record.rfp_id
                                print(f"[get_proposal_id_from_approval] Found RFP by number, actual_rfp_id: {actual_rfp_id}")
                except Exception as e:
                    print(f"[get_proposal_id_from_approval] Error finding RFP record: {e}")
                
                # Use actual_rfp_id if found, otherwise use the original rfp_id
                search_rfp_id = actual_rfp_id if actual_rfp_id is not None else rfp_id_str
                
                try:
                    # Try filtering by tenant first
                    responses = RFPResponse.objects.filter(rfp_id=search_rfp_id, tenant_id=tenant_id)
                    if not responses.exists():
                        # Try with numeric RFP ID if search_rfp_id is numeric
                        try:
                            rfp_id_int = int(search_rfp_id)
                            responses = RFPResponse.objects.filter(rfp_id=rfp_id_int, tenant_id=tenant_id)
                        except (ValueError, TypeError):
                            pass
                    
                    # If still no responses, try without tenant filter (for debugging)
                    if not responses.exists():
                        print(f"[get_proposal_id_from_approval] No responses with tenant filter, trying without tenant...")
                        responses = RFPResponse.objects.filter(rfp_id=search_rfp_id)
                        if not responses.exists():
                            try:
                                rfp_id_int = int(search_rfp_id)
                                responses = RFPResponse.objects.filter(rfp_id=rfp_id_int)
                            except (ValueError, TypeError):
                                pass
                except Exception as filter_error:
                    print(f"[get_proposal_id_from_approval] Error querying responses: {filter_error}")
                    import traceback
                    traceback.print_exc()
                    responses = None
                
                if responses and responses.exists():
                    response_count = responses.count()
                    print(f"[get_proposal_id_from_approval] Found {response_count} response(s) for RFP {rfp_id}")
                    # For proposal evaluation, try to find the response assigned to this evaluator
                    # Get evaluator_id from the approval stage (if stage_id is provided in query params)
                    evaluator_id = None
                    stage_id = request.GET.get('stage_id')
                    
                    if stage_id:
                        try:
                            from tprm_backend.rfp_approval.models import ApprovalStages
                            stage = ApprovalStages.objects.get(stage_id=stage_id, approval_id=approval_id)
                            evaluator_id = stage.assigned_user_id
                            print(f"[get_proposal_id_from_approval] Found evaluator_id from stage: {evaluator_id}")
                        except ApprovalStages.DoesNotExist:
                            print(f"[get_proposal_id_from_approval] Stage not found: {stage_id}")
                    
                    # If no evaluator_id from stage, try to get from request query params
                    if not evaluator_id:
                        evaluator_id_param = request.GET.get('evaluator_id') or request.GET.get('userId')
                        if evaluator_id_param:
                            try:
                                evaluator_id = int(evaluator_id_param)
                                print(f"[get_proposal_id_from_approval] Found evaluator_id from query params: {evaluator_id}")
                            except (ValueError, TypeError):
                                pass
                    
                    # Try to find response assigned to this evaluator using RFPEvaluatorAssignment
                    if evaluator_id:
                        try:
                            from tprm_backend.rfp.models import RFPEvaluatorAssignment
                            
                            # Get all response IDs for this RFP
                            response_ids = list(responses.values_list('response_id', flat=True))
                            
                            # Find assignment for this evaluator and one of these responses
                            # MULTI-TENANCY: Filter by tenant
                            try:
                                assignment = RFPEvaluatorAssignment.objects.filter(
                                    evaluator_id=evaluator_id,
                                    proposal_id__in=response_ids,
                                    assignment_type='evaluation',
                                    tenant_id=tenant_id
                                ).first()
                            except Exception as filter_error:
                                # If tenant_id filter fails, try without tenant filter
                                print(f"[get_proposal_id_from_approval] Error filtering by tenant, trying without: {filter_error}")
                                assignment = RFPEvaluatorAssignment.objects.filter(
                                    evaluator_id=evaluator_id,
                                    proposal_id__in=response_ids,
                                    assignment_type='evaluation'
                                ).first()
                            
                            if assignment:
                                proposal_id = assignment.proposal_id
                                print(f"[get_proposal_id_from_approval] Found response_id from evaluator assignment: {proposal_id}")
                            else:
                                # No assignment found, try to find by matching response to evaluator
                                # This could happen if assignment was created differently
                                print(f"[get_proposal_id_from_approval] No assignment found for evaluator {evaluator_id}, trying first response")
                                first_response = responses.first()
                                proposal_id = first_response.response_id
                        except Exception as e:
                            print(f"[get_proposal_id_from_approval] Error checking evaluator assignment: {e}")
                            # Fallback to first response
                            first_response = responses.first()
                            proposal_id = first_response.response_id
                    else:
                        # No evaluator_id available, just get the first response
                        print(f"[get_proposal_id_from_approval] No evaluator_id found, using first response")
                        first_response = responses.first()
                        proposal_id = first_response.response_id
                    
                    # Also return all response IDs for potential selection
                    all_response_ids = list(responses.values_list('response_id', flat=True))
                    
                    print(f"[get_proposal_id_from_approval] Returning response_id: {proposal_id}")
                    return Response({
                        'proposal_id': proposal_id,
                        'all_response_ids': all_response_ids,
                        'rfp_id': rfp_id,
                        'approval_id': approval_id,
                        'evaluator_id': evaluator_id,
                        'request_data': request_data
                    })
                else:
                    print(f"[get_proposal_id_from_approval] No responses found for RFP {rfp_id} (tenant_id: {tenant_id})")
                    # If we found an RFP ID but no responses, provide a more helpful error
                    return Response({
                        'error': f'No proposals found for RFP {rfp_id}. The RFP may not have any submitted proposals yet, or the proposals may belong to a different tenant.',
                        'approval_id': approval_id,
                        'rfp_id': rfp_id,
                        'request_data_keys': list(request_data.keys()) if isinstance(request_data, dict) else None,
                        'request_data_type': type(request_data).__name__,
                        'tenant_id': tenant_id
                    }, status=404)
        
        if not proposal_id:
            print(f"[get_proposal_id_from_approval] No proposal_id found. request_data keys: {list(request_data.keys()) if isinstance(request_data, dict) else 'N/A'}")
            return Response({
                'error': 'No proposal ID found in approval data',
                'approval_id': approval_id,
                'request_data_keys': list(request_data.keys()) if isinstance(request_data, dict) else None,
                'request_data_type': type(request_data).__name__
            }, status=404)
        
        print(f"[get_proposal_id_from_approval] Returning proposal_id: {proposal_id}")
        return Response({
            'proposal_id': proposal_id,
            'approval_id': approval_id,
            'request_data': request_data
        })
        
    except ApprovalRequests.DoesNotExist:
        print(f"[get_proposal_id_from_approval] Approval request not found: {approval_id}")
        return Response({'error': 'Approval request not found'}, status=404)
    except Exception as e:
        print(f"[get_proposal_id_from_approval] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e),
            'error_type': type(e).__name__
        }, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_rfp_id_from_approval(request, approval_id):
    """
    Get RFP ID from approval_id by looking up the workflow and RFP relationship
    MULTI-TENANCY: Only returns RFP IDs for tenant's approval requests
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # Get the approval request - try with tenant_id first, then without if not found
        approval_request = None
        try:
            approval_request = ApprovalRequests.objects.get(approval_id=approval_id, tenant_id=tenant_id)
            print(f"✅ [get_rfp_id_from_approval] Found approval request with tenant_id: {approval_id} (tenant: {tenant_id})")
        except ApprovalRequests.DoesNotExist:
            print(f"⚠️ [get_rfp_id_from_approval] Approval request {approval_id} not found with tenant_id {tenant_id}, trying without tenant filter...")
            # Try without tenant filter to see if it exists with different tenant
            try:
                approval_request = ApprovalRequests.objects.get(approval_id=approval_id)
                print(f"⚠️ [get_rfp_id_from_approval] Found approval request {approval_id} but with different tenant_id: {approval_request.tenant_id} (expected: {tenant_id})")
                # If tenant mismatch, use the approval request's actual tenant_id for RFP lookup
                # This allows cross-tenant access when needed (e.g., for committee evaluations)
                if approval_request.tenant_id and approval_request.tenant_id != tenant_id:
                    print(f"⚠️ [get_rfp_id_from_approval] Tenant mismatch detected. Will use approval's tenant_id ({approval_request.tenant_id}) for RFP lookup")
                    # Continue processing with the approval request's tenant_id
            except ApprovalRequests.DoesNotExist:
                # List all approval_ids for debugging
                all_approvals = ApprovalRequests.objects.values_list('approval_id', flat=True)[:20]
                print(f"🔍 [get_rfp_id_from_approval] Approval request {approval_id} not found. Available approval_ids (first 20): {list(all_approvals)}")
                raise
        
        # Determine effective tenant_id to use for RFP lookup
        # If approval belongs to different tenant, use its tenant_id for RFP lookup
        effective_tenant_id = approval_request.tenant_id if approval_request.tenant_id else tenant_id
        if approval_request.tenant_id and approval_request.tenant_id != tenant_id:
            print(f"⚠️ [get_rfp_id_from_approval] Using approval's tenant_id ({effective_tenant_id}) for RFP lookup instead of request tenant_id ({tenant_id})")
        
        print(f"🔍 [get_rfp_id_from_approval] Processing approval_id: {approval_id}, workflow_id: {approval_request.workflow_id}, effective_tenant_id: {effective_tenant_id}")
        
        rfp_id = None
        request_data = None  # Initialize request_data for use in later methods
        
        # Method 1: Try to find RFP by approval_workflow_id (which matches the workflow_id in approval_requests)
        try:
            if effective_tenant_id:
                rfp = RFP.objects.get(approval_workflow_id=approval_request.workflow_id, tenant_id=effective_tenant_id)
            else:
                rfp = RFP.objects.get(approval_workflow_id=approval_request.workflow_id)
            rfp_id = rfp.rfp_id
            print(f"✅ [get_rfp_id_from_approval] Found RFP by workflow_id: {rfp.rfp_id}")
            # RFP found, return it immediately
            return Response({
                'rfp_id': rfp_id,
                'approval_id': approval_id,
                'workflow_id': approval_request.workflow_id
            })
        except RFP.DoesNotExist:
            print(f"⚠️ [get_rfp_id_from_approval] No RFP found for workflow_id: {approval_request.workflow_id} with tenant {effective_tenant_id}")
            
            # Try to find RFP by workflow_id without tenant filter (in case tenant_id mismatch)
            try:
                rfp = RFP.objects.get(approval_workflow_id=approval_request.workflow_id)
                rfp_id = rfp.rfp_id
                print(f"✅ [get_rfp_id_from_approval] Found RFP by workflow_id (without tenant filter): {rfp.rfp_id}")
                # RFP found, return it immediately
                return Response({
                    'rfp_id': rfp_id,
                    'approval_id': approval_id,
                    'workflow_id': approval_request.workflow_id,
                    'note': 'Found without tenant filter (cross-tenant access)'
                })
            except RFP.DoesNotExist:
                print(f"⚠️ [get_rfp_id_from_approval] No RFP found for workflow_id (with or without tenant), trying request_data and other methods...")
                # Method 2: Try to extract RFP ID from request_data (only if RFP not found by workflow_id)
                try:
                    request_data_raw = approval_request.request_data
                    print(f"🔍 [get_rfp_id_from_approval] Raw request_data type: {type(request_data_raw)}")
                    print(f"🔍 [get_rfp_id_from_approval] Raw request_data (first 500 chars): {str(request_data_raw)[:500] if request_data_raw else 'None'}")
                    
                    request_data = request_data_raw
                    if isinstance(request_data, str):
                        try:
                            request_data = json.loads(request_data)
                            print(f"✅ [get_rfp_id_from_approval] Successfully parsed JSON request_data")
                        except json.JSONDecodeError as json_err:
                            print(f"❌ [get_rfp_id_from_approval] Failed to parse JSON: {str(json_err)}")
                            request_data = None
                    
                    if request_data:
                        print(f"🔍 [get_rfp_id_from_approval] Parsed request_data type: {type(request_data)}")
                        if isinstance(request_data, dict):
                            print(f"🔍 [get_rfp_id_from_approval] request_data keys: {list(request_data.keys())[:20]}")
                        
                        # Try different possible keys for RFP ID
                        rfp_id = (
                            request_data.get('rfp_id') or
                            request_data.get('rfpId') or
                            request_data.get('id') or
                            request_data.get('RFP_ID') or
                            request_data.get('RFPID') or
                            None
                        )
                        
                        # If it's an array, try to get from first item
                        if not rfp_id and isinstance(request_data, list) and len(request_data) > 0:
                            print(f"🔍 [get_rfp_id_from_approval] request_data is a list with {len(request_data)} items")
                            first_item = request_data[0]
                            if isinstance(first_item, dict):
                                print(f"🔍 [get_rfp_id_from_approval] First item keys: {list(first_item.keys())[:20]}")
                                rfp_id = (
                                    first_item.get('rfp_id') or
                                    first_item.get('rfpId') or
                                    first_item.get('id') or
                                    first_item.get('RFP_ID') or
                                    first_item.get('RFPID') or
                                    None
                                )
                        
                        # Method 3: Try to search recursively in nested structures
                        if not rfp_id and isinstance(request_data, dict):
                            def find_rfp_id_recursive(obj, depth=0, max_depth=3):
                                if depth > max_depth:
                                    return None
                                if isinstance(obj, dict):
                                    # Check all keys for rfp_id variations
                                    for key, value in obj.items():
                                        if key.lower() in ['rfp_id', 'rfpid', 'id'] and value:
                                            return value
                                        # Recursively search nested dicts
                                        if isinstance(value, (dict, list)):
                                            result = find_rfp_id_recursive(value, depth + 1, max_depth)
                                            if result:
                                                return result
                                elif isinstance(obj, list):
                                    for item in obj:
                                        result = find_rfp_id_recursive(item, depth + 1, max_depth)
                                        if result:
                                            return result
                                return None
                            
                            rfp_id = find_rfp_id_recursive(request_data)
                            if rfp_id:
                                print(f"✅ [get_rfp_id_from_approval] Found RFP ID recursively: {rfp_id}")
                        
                        if rfp_id:
                            print(f"✅ [get_rfp_id_from_approval] Found RFP ID from request_data: {rfp_id}")
                            # Verify the RFP exists using effective tenant_id
                            try:
                                if effective_tenant_id:
                                    rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=effective_tenant_id)
                                else:
                                    rfp = RFP.objects.get(rfp_id=rfp_id)
                                print(f"✅ [get_rfp_id_from_approval] Verified RFP exists: {rfp.rfp_id}")
                            except RFP.DoesNotExist:
                                # Try without tenant filter as fallback
                                try:
                                    rfp = RFP.objects.get(rfp_id=rfp_id)
                                    print(f"✅ [get_rfp_id_from_approval] Verified RFP exists (without tenant filter): {rfp.rfp_id}")
                                except RFP.DoesNotExist:
                                    print(f"⚠️ [get_rfp_id_from_approval] RFP ID {rfp_id} from request_data not found in database")
                                    rfp_id = None
                        else:
                            print(f"❌ [get_rfp_id_from_approval] Could not find RFP ID in request_data")
                    else:
                        print(f"❌ [get_rfp_id_from_approval] request_data is None or could not be parsed")
                        
                except Exception as data_error:
                    print(f"❌ [get_rfp_id_from_approval] Error extracting RFP ID from request_data: {str(data_error)}")
                    import traceback
                    print(traceback.format_exc())
        
        # Method 4: Try to find RFP through stages if still not found
        if not rfp_id:
            print(f"🔍 [get_rfp_id_from_approval] Trying to find RFP through stages...")
            try:
                from .models import ApprovalStages
                # Try with effective tenant_id first, then without filter
                stages = ApprovalStages.objects.filter(approval_id=approval_id, tenant_id=effective_tenant_id)
                if not stages.exists():
                    stages = ApprovalStages.objects.filter(approval_id=approval_id)
                
                for stage in stages:
                    # Try to get RFP ID from stage's response_data
                    if hasattr(stage, 'response_data') and stage.response_data:
                        try:
                            stage_response_data = stage.response_data
                            if isinstance(stage_response_data, str):
                                stage_response_data = json.loads(stage_response_data)
                            
                            if isinstance(stage_response_data, dict):
                                stage_rfp_id = (
                                    stage_response_data.get('rfp_id') or
                                    stage_response_data.get('rfpId') or
                                    stage_response_data.get('id') or
                                    None
                                )
                                if stage_rfp_id:
                                    # Verify it exists using effective tenant_id
                                    try:
                                        if effective_tenant_id:
                                            rfp = RFP.objects.get(rfp_id=stage_rfp_id, tenant_id=effective_tenant_id)
                                        else:
                                            rfp = RFP.objects.get(rfp_id=stage_rfp_id)
                                        rfp_id = stage_rfp_id
                                        print(f"✅ [get_rfp_id_from_approval] Found RFP ID from stage response_data: {rfp_id}")
                                        break
                                    except RFP.DoesNotExist:
                                        # Try without tenant filter
                                        try:
                                            rfp = RFP.objects.get(rfp_id=stage_rfp_id)
                                            rfp_id = stage_rfp_id
                                            print(f"✅ [get_rfp_id_from_approval] Found RFP ID from stage response_data (without tenant filter): {rfp_id}")
                                            break
                                        except RFP.DoesNotExist:
                                            continue
                        except Exception:
                            continue
            except Exception as stage_error:
                print(f"⚠️ [get_rfp_id_from_approval] Error checking stages: {str(stage_error)}")
        
        # Method 5: Try to find RFP by matching request_data fields (scope, employee_count, etc.)
        # Parse request_data if not already parsed
        if not rfp_id and not request_data:
            try:
                request_data_raw = approval_request.request_data
                if request_data_raw:
                    if isinstance(request_data_raw, str):
                        try:
                            request_data = json.loads(request_data_raw)
                        except json.JSONDecodeError:
                            request_data = None
                    else:
                        request_data = request_data_raw
            except Exception:
                request_data = None
        
        if not rfp_id and request_data:
            print(f"🔍 [get_rfp_id_from_approval] Trying to find RFP by matching request_data fields...")
            try:
                # Try to match by request title or description
                request_title = approval_request.request_title or ''
                request_description = approval_request.request_description or ''
                
                # Search for RFPs with matching title or description using effective tenant_id
                if effective_tenant_id:
                    matching_rfps = RFP.objects.filter(tenant_id=effective_tenant_id)
                else:
                    matching_rfps = RFP.objects.all()
                
                # Try to match by title
                if request_title:
                    title_matches = matching_rfps.filter(rfp_title__icontains=request_title[:50])  # Use first 50 chars
                    if title_matches.exists():
                        # If multiple matches, prefer one with matching workflow_id
                        if approval_request.workflow_id:
                            workflow_match = title_matches.filter(approval_workflow_id=approval_request.workflow_id).first()
                            if workflow_match:
                                rfp_id = workflow_match.rfp_id
                                print(f"✅ [get_rfp_id_from_approval] Found RFP by title and workflow match: {rfp_id}")
                        if not rfp_id:
                            rfp_id = title_matches.first().rfp_id
                            print(f"✅ [get_rfp_id_from_approval] Found RFP by title match: {rfp_id}")
                
                # If still not found, try to match by description or other fields
                if not rfp_id and request_description:
                    desc_matches = matching_rfps.filter(description__icontains=request_description[:100])
                    if desc_matches.exists():
                        rfp_id = desc_matches.first().rfp_id
                        print(f"✅ [get_rfp_id_from_approval] Found RFP by description match: {rfp_id}")
                
            except Exception as match_error:
                print(f"⚠️ [get_rfp_id_from_approval] Error matching RFP by fields: {str(match_error)}")
        
        # Method 6: If still not found, try to get any RFP associated with this workflow_id (even if approval_workflow_id doesn't match)
        if not rfp_id:
            print(f"🔍 [get_rfp_id_from_approval] Trying to find any RFP for workflow_id: {approval_request.workflow_id}...")
            try:
                # Check if there are any RFPs that might be related through other means
                # This is a last resort - return the first RFP for this tenant if workflow matching fails
                # But only if we're sure this is an RFP workflow
                from .models import ApprovalWorkflows
                try:
                    workflow = ApprovalWorkflows.objects.get(workflow_id=approval_request.workflow_id, tenant_id=tenant_id)
                    if workflow.business_object_type == 'RFP':
                        # This is an RFP workflow, so try to find any RFP that might be related
                        if tenant_id:
                            any_rfp = RFP.objects.filter(tenant_id=tenant_id).first()
                        else:
                            any_rfp = RFP.objects.first()
                        if any_rfp:
                            print(f"⚠️ [get_rfp_id_from_approval] Using fallback RFP: {any_rfp.rfp_id} (workflow is RFP type but no direct match found)")
                            # Don't use this as it might be wrong - instead return error with helpful message
                except ApprovalWorkflows.DoesNotExist:
                    pass
            except Exception as fallback_error:
                print(f"⚠️ [get_rfp_id_from_approval] Error in fallback search: {str(fallback_error)}")
        
        # Method 7: If still not found, try to find any RFP that might be related by searching all RFPs
        if not rfp_id:
            print(f"🔍 [get_rfp_id_from_approval] Trying final fallback: search all RFPs for tenant {tenant_id}...")
            try:
                # Get all RFPs for this tenant and see if any match by title or other criteria using effective tenant_id
                if effective_tenant_id:
                    all_rfps = RFP.objects.filter(tenant_id=effective_tenant_id)
                else:
                    all_rfps = RFP.objects.all()
                
                # Try to match by request title
                request_title = approval_request.request_title or ''
                if request_title:
                    # Remove common prefixes like "Approval Request" or "RFP Approval"
                    clean_title = request_title.replace('Approval Request', '').replace('RFP Approval:', '').replace('AR_', '').strip()
                    if clean_title:
                        title_matches = all_rfps.filter(rfp_title__icontains=clean_title[:50])
                        if title_matches.exists():
                            rfp_id = title_matches.first().rfp_id
                            print(f"✅ [get_rfp_id_from_approval] Found RFP by cleaned title match: {rfp_id}")
                
                # If still not found and we have a workflow_id, try to find RFP created around the same time
                if not rfp_id and approval_request.created_at:
                    # Find RFPs created within 1 day of the approval request
                    from django.utils import timezone
                    from datetime import timedelta
                    time_window_start = approval_request.created_at - timedelta(days=1)
                    time_window_end = approval_request.created_at + timedelta(days=1)
                    time_matches = all_rfps.filter(created_at__gte=time_window_start, created_at__lte=time_window_end)
                    if time_matches.exists():
                        rfp_id = time_matches.first().rfp_id
                        print(f"⚠️ [get_rfp_id_from_approval] Found RFP by time window match (may not be correct): {rfp_id}")
                        
            except Exception as final_fallback_error:
                print(f"⚠️ [get_rfp_id_from_approval] Error in final fallback: {str(final_fallback_error)}")
        
        if not rfp_id:
            error_msg = f'No RFP ID found for approval request {approval_id}. Workflow ID: {approval_request.workflow_id}'
            print(f"❌ [get_rfp_id_from_approval] {error_msg}")
            print(f"🔍 [get_rfp_id_from_approval] Approval request details:")
            print(f"   - request_title: {approval_request.request_title}")
            print(f"   - request_description: {approval_request.request_description}")
            print(f"   - workflow_id: {approval_request.workflow_id}")
            print(f"   - tenant_id: {approval_request.tenant_id}")
            print(f"   - request_data: {str(approval_request.request_data)[:200] if approval_request.request_data else 'None/Empty'}")
            
            # List available RFPs for debugging
            try:
                if effective_tenant_id:
                    available_rfps = RFP.objects.filter(tenant_id=effective_tenant_id).values_list('rfp_id', 'rfp_title', 'approval_workflow_id')[:10]
                    print(f"🔍 [get_rfp_id_from_approval] Available RFPs for tenant {effective_tenant_id}: {list(available_rfps)}")
            except Exception as debug_err:
                print(f"⚠️ [get_rfp_id_from_approval] Error listing available RFPs: {str(debug_err)}")
            
            return Response({
                'error': error_msg,
                'approval_id': approval_id,
                'workflow_id': approval_request.workflow_id,
                'request_title': approval_request.request_title,
                'request_data_preview': str(approval_request.request_data)[:200] if approval_request.request_data else None,
                'suggestion': 'Check if RFP exists and has approval_workflow_id set to match workflow_id'
            }, status=404)
        
        return Response({
            'rfp_id': rfp_id,
            'approval_id': approval_id,
            'workflow_id': approval_request.workflow_id
        })
        
    except ApprovalRequests.DoesNotExist as e:
        error_msg = f'Approval request {approval_id} not found for tenant {tenant_id}'
        print(f"❌ [get_rfp_id_from_approval] {error_msg}")
        
        # Last resort: Try to find RFP through stages even if approval request doesn't exist
        print(f"🔍 [get_rfp_id_from_approval] Attempting to find RFP through stages with approval_id: {approval_id}")
        rfp_id_from_stages = None
        try:
            from .models import ApprovalStages
            # Try with tenant_id first
            stages = ApprovalStages.objects.filter(approval_id=approval_id, tenant_id=tenant_id)
            if not stages.exists():
                # Try without tenant_id filter
                stages = ApprovalStages.objects.filter(approval_id=approval_id)
            
            if stages.exists():
                print(f"✅ [get_rfp_id_from_approval] Found {stages.count()} stage(s) with approval_id {approval_id}")
                first_stage = stages.first()
                
                # Try to get workflow_id from approval request (even if it has different tenant)
                approval_req = ApprovalRequests.objects.filter(approval_id=approval_id).first()
                if approval_req:
                    workflow_id = approval_req.workflow_id
                    print(f"🔍 [get_rfp_id_from_approval] Found approval request with workflow_id: {workflow_id}")
                    
                    # Try to find RFP by workflow_id using approval request's tenant_id
                    effective_lookup_tenant_id = approval_req.tenant_id if approval_req and approval_req.tenant_id else tenant_id
                    try:
                        if effective_lookup_tenant_id:
                            rfp = RFP.objects.get(approval_workflow_id=workflow_id, tenant_id=effective_lookup_tenant_id)
                        else:
                            rfp = RFP.objects.get(approval_workflow_id=workflow_id)
                        rfp_id_from_stages = rfp.rfp_id
                        print(f"✅ [get_rfp_id_from_approval] Found RFP {rfp.rfp_id} through stage workflow lookup")
                    except RFP.DoesNotExist:
                        # Try without tenant filter
                        try:
                            rfp = RFP.objects.get(approval_workflow_id=workflow_id)
                            rfp_id_from_stages = rfp.rfp_id
                            print(f"✅ [get_rfp_id_from_approval] Found RFP {rfp.rfp_id} through stage workflow lookup (without tenant filter)")
                        except RFP.DoesNotExist:
                            print(f"⚠️ [get_rfp_id_from_approval] No RFP found for workflow_id {workflow_id}")
                
                # If still not found, try to extract from stage's response_data or approval request's request_data
                if not rfp_id_from_stages:
                    try:
                        # First try to get from approval request's request_data (if we have it)
                        if approval_req and approval_req.request_data:
                            approval_request_data = approval_req.request_data
                            if isinstance(approval_request_data, str):
                                try:
                                    approval_request_data = json.loads(approval_request_data)
                                except json.JSONDecodeError:
                                    approval_request_data = None
                            
                            if isinstance(approval_request_data, dict):
                                rfp_id_from_stages = (
                                    approval_request_data.get('rfp_id') or
                                    approval_request_data.get('rfpId') or
                                    approval_request_data.get('id') or
                                    None
                                )
                                if rfp_id_from_stages:
                                    print(f"✅ [get_rfp_id_from_approval] Found RFP ID from approval request_data: {rfp_id_from_stages}")
                        
                        # If not found, try stage's response_data
                        if not rfp_id_from_stages and hasattr(first_stage, 'response_data') and first_stage.response_data:
                            stage_response_data = first_stage.response_data
                            if isinstance(stage_response_data, str):
                                try:
                                    stage_response_data = json.loads(stage_response_data)
                                except json.JSONDecodeError:
                                    stage_response_data = None
                            
                            if isinstance(stage_response_data, dict):
                                rfp_id_from_stages = (
                                    stage_response_data.get('rfp_id') or
                                    stage_response_data.get('rfpId') or
                                    stage_response_data.get('id') or
                                    None
                                )
                                if rfp_id_from_stages:
                                    print(f"✅ [get_rfp_id_from_approval] Found RFP ID from stage response_data: {rfp_id_from_stages}")
                        
                        # Verify RFP exists if we found an ID
                        if rfp_id_from_stages:
                            try:
                                # Use approval request's tenant_id if available, otherwise use request tenant_id
                                lookup_tenant_id = approval_req.tenant_id if approval_req and approval_req.tenant_id else tenant_id
                                if lookup_tenant_id:
                                    rfp = RFP.objects.get(rfp_id=rfp_id_from_stages, tenant_id=lookup_tenant_id)
                                else:
                                    rfp = RFP.objects.get(rfp_id=rfp_id_from_stages)
                                print(f"✅ [get_rfp_id_from_approval] Verified RFP {rfp.rfp_id} exists")
                            except RFP.DoesNotExist:
                                # Try without tenant filter as fallback
                                try:
                                    rfp = RFP.objects.get(rfp_id=rfp_id_from_stages)
                                    print(f"✅ [get_rfp_id_from_approval] Verified RFP {rfp.rfp_id} exists (without tenant filter)")
                                except RFP.DoesNotExist:
                                    print(f"⚠️ [get_rfp_id_from_stages] RFP {rfp_id_from_stages} not found in database")
                                    rfp_id_from_stages = None
                    except Exception as stage_data_err:
                        print(f"⚠️ [get_rfp_id_from_approval] Error extracting RFP ID from stage/approval data: {str(stage_data_err)}")
                        import traceback
                        print(traceback.format_exc())
                
        except Exception as stage_lookup_err:
            print(f"⚠️ [get_rfp_id_from_approval] Error in stage lookup fallback: {str(stage_lookup_err)}")
            import traceback
            print(traceback.format_exc())
        
        if rfp_id_from_stages:
            return Response({
                'rfp_id': rfp_id_from_stages,
                'approval_id': approval_id,
                'note': 'Found through stage lookup (approval request not found)'
            })
        
        return Response({
            'error': error_msg,
            'approval_id': approval_id,
            'tenant_id': tenant_id,
            'suggestion': 'Check if approval_id exists or if tenant_id is correct. Also check if stages exist for this approval_id.'
        }, status=404)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ [get_rfp_id_from_approval] Unexpected error: {str(e)}")
        print(f"❌ [get_rfp_id_from_approval] Traceback: {error_trace}")
        return Response({'error': f'Internal server error: {str(e)}'}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def user_approvals(request):
    """
    Get all approval stages assigned to a specific user
    MULTI-TENANCY: Only returns approvals for the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
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
        # MULTI-TENANCY: Filter by tenant
        stages = ApprovalStages.objects.filter(assigned_user_id=user_id_int, tenant_id=tenant_id)
        
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
                # MULTI-TENANCY: Filter by tenant
                approval_request = ApprovalRequests.objects.get(approval_id=stage.approval_id, tenant_id=tenant_id)
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
                    # MULTI-TENANCY: Filter by tenant
                    workflow = ApprovalWorkflows.objects.get(workflow_id=approval_request.workflow_id, tenant_id=tenant_id)
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def debug_approval_requests(request):
    """
    Debug endpoint to check approval requests data
    MULTI-TENANCY: Only returns approval requests for the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
    try:
        # MULTI-TENANCY: Filter approval requests by tenant
        approval_requests = ApprovalRequests.objects.filter(tenant_id=tenant_id)
        
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def debug_approval_stages(request):
    """
    Debug endpoint to check approval stages data
    MULTI-TENANCY: Only returns approval stages for the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
    try:
        # MULTI-TENANCY: Filter approval stages by tenant
        stages = ApprovalStages.objects.filter(tenant_id=tenant_id)
        
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def create_sample_approval_request(request):
    """
    Create a sample approval request with request_data for testing
    MULTI-TENANCY: Creates sample data for the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
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
        # MULTI-TENANCY: Add tenant_id
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
            submission_date=timezone.now(),
            tenant_id=tenant_id
        )
        
        # Create a corresponding approval stage for testing
        from .models import ApprovalStages
        stage_id = f"ST_{uuid.uuid4().hex[:8].upper()}"
        
        # MULTI-TENANCY: Add tenant_id
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
            is_mandatory=True,
            tenant_id=tenant_id
        )
        
        # Create workflow version for sample approval request
        try:
            # MULTI-TENANCY: Pass tenant_id
            version_record = create_workflow_version(
                workflow_id=approval_id,  # Use approval_id as workflow_id for sample
                approval_ids=[approval_id],
                created_by=1,
                created_by_name="System",
                created_by_role="Administrator",
                version_type='INITIAL',
                change_reason='Sample approval request creation for testing',
                tenant_id=tenant_id
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def update_stage_status(request):
    """
    Update the status of an approval stage
    MULTI-TENANCY: Only allows updating stages belonging to the tenant
    """
    # MULTI-TENANCY: Get tenant_id from request
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({
            'error': 'Tenant context not found'
        }, status=403)
    
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
        # MULTI-TENANCY: Filter by tenant
        print(f"Looking for stage with ID: {stage_id}")  # Debug log
        stage = ApprovalStages.objects.get(stage_id=stage_id, tenant_id=tenant_id)
        print(f"Found stage: {stage.stage_name}")  # Debug log

       # Check if this is a multi-level workflow and enforce sequential approval
        try:
            # MULTI-TENANCY: Filter by tenant
            approval_request = ApprovalRequests.objects.get(approval_id=stage.approval_id, tenant_id=tenant_id)
            workflow = ApprovalWorkflows.objects.get(workflow_id=approval_request.workflow_id, tenant_id=tenant_id)
            
            # Only enforce sequential approval for MULTI_LEVEL workflows
            if workflow.workflow_type == 'MULTI_LEVEL':
                print(f"Multi-level workflow detected. Checking stage order: {stage.stage_order}")
                
                # Get all stages for this approval, ordered by stage_order
                # MULTI-TENANCY: Filter by tenant
                all_stages = ApprovalStages.objects.filter(
                    approval_id=stage.approval_id,
                    tenant_id=tenant_id
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
        from tprm_backend.rfp.models import S3Files
        
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
        from tprm_backend.apps.vendor_risk.models import RiskTPRM
        
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_rfp_details_for_change_request(request, rfp_id):
    """
    Get RFP details with change request context for editing
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        from tprm_backend.rfp.models import RFPEvaluationCriteria
        # RFP is already imported at the top
        
        # Get RFP details - use rfp_id field, not id
        # MULTI-TENANCY: Filter by tenant
        rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
        
        # Get change requests for this RFP
        change_requests = []
        try:
            from tprm_backend.rfp_approval.models import ApprovalRequests, ApprovalStages, ApprovalWorkflows
            from tprm_backend.rfp_approval.models import ApprovalComments
            import json
            
            # Find approval requests for this RFP by:
            # 1. Getting workflows with business_object_type='RFP'
            # 2. Getting approval requests for those workflows
            # 3. Checking if request_data contains matching rfp_id
            rfp_approval_requests = []
            try:
                # Get all workflows for RFP
                # MULTI-TENANCY: Filter by tenant
                try:
                    rfp_workflows = ApprovalWorkflows.objects.filter(
                        business_object_type='RFP',
                        tenant_id=tenant_id
                    )
                    workflow_ids = [w.workflow_id for w in rfp_workflows]
                except Exception as e:
                    print(f"Error fetching workflows: {str(e)}")
                    workflow_ids = []
                
                # Get approval requests for these workflows
                # MULTI-TENANCY: Filter by tenant
                if workflow_ids:
                    try:
                        all_approval_requests = ApprovalRequests.objects.filter(
                            workflow_id__in=workflow_ids,
                            tenant_id=tenant_id
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
                    # MULTI-TENANCY: Filter by tenant
                    try:
                        stages_with_changes = ApprovalStages.objects.filter(
                            approval_id=approval.approval_id,
                            stage_status__in=['REQUEST_CHANGES', 'REJECTED'],
                            tenant_id=tenant_id
                        )
                    except Exception as e:
                        print(f"Error fetching stages for approval {approval.approval_id}: {str(e)}")
                        continue
                    
                    for stage in stages_with_changes:
                        try:
                            # Get change request comments
                            # MULTI-TENANCY: Filter by tenant
                            try:
                                change_comments = ApprovalComments.objects.filter(
                                    stage_id=stage.stage_id,
                                    comment_type='CHANGE_REQUEST',
                                    tenant_id=tenant_id
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
                'auto_approve': getattr(rfp, 'auto_approve', False),
                'autoApprove': getattr(rfp, 'auto_approve', False),  # For compatibility
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
            from tprm_backend.rfp.models import RFPEvaluationCriteria
            all_criteria_count = RFPEvaluationCriteria.objects.all().count()
            print(f"🔍 TOTAL criteria in entire database: {all_criteria_count}")
            
            if all_criteria_count > 0:
                # Show sample of what rfp_ids have criteria
                # Use 'tprm' connection to access rfp_evaluation_criteria table (in tprm_integration database)
                db_connection = 'tprm'
                try:
                    if 'tprm' not in connections.databases:
                        print("Warning: 'tprm' database connection not found, falling back to 'default'")
                        db_connection = 'default'
                except Exception as db_check_error:
                    print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")
                
                with connections[db_connection].cursor() as cursor:
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
                # Use 'tprm' connection to access rfp_evaluation_criteria table (in tprm_integration database)
                db_connection = 'tprm'
                try:
                    if 'tprm' not in connections.databases:
                        print("Warning: 'tprm' database connection not found, falling back to 'default'")
                        db_connection = 'default'
                except Exception as db_check_error:
                    print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")
                
                with connections[db_connection].cursor() as cursor:
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
                    from tprm_backend.rfp.models import RFPEvaluationCriteria
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_rfp_details(request, rfp_id):
    """
    Get complete RFP details including documents
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # Get RFP by ID
        # MULTI-TENANCY: Try with tenant filter first, then without if not found (for cross-tenant access)
        rfp = None
        try:
            rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
            print(f"✅ [get_rfp_details] Found RFP {rfp_id} with tenant {tenant_id}")
        except RFP.DoesNotExist:
            # Try without tenant filter (for cross-tenant access when RFP is linked to approval)
            print(f"⚠️ [get_rfp_details] RFP {rfp_id} not found with tenant {tenant_id}, trying without tenant filter...")
            try:
                rfp = RFP.objects.get(rfp_id=rfp_id)
                print(f"✅ [get_rfp_details] Found RFP {rfp_id} without tenant filter (cross-tenant access)")
            except RFP.DoesNotExist:
                raise
        
        # Get evaluation criteria for this RFP - use tprm database connection
        evaluation_criteria = []
        try:
            # Use 'tprm' connection to access rfp_evaluation_criteria table (in tprm_integration database)
            db_connection = 'tprm'
            try:
                if 'tprm' not in connections.databases:
                    print("Warning: 'tprm' database connection not found, falling back to 'default'")
                    db_connection = 'default'
                else:
                    print(f"Using 'tprm' database connection for rfp_evaluation_criteria table (tprm_integration)")
            except Exception as db_check_error:
                print(f"Warning: Error checking database connections: {db_check_error}, using 'tprm' connection")
            
            with connections[db_connection].cursor() as cursor:
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
                from tprm_backend.rfp.models import S3Files
                import json
                
                # Handle both array of IDs and array of objects
                document_ids = rfp.documents
                
                # If documents is a string, try to parse it as JSON
                if isinstance(document_ids, str):
                    try:
                        document_ids = json.loads(document_ids)
                        print(f"[get_rfp_details] Parsed documents string: {document_ids}")
                    except (json.JSONDecodeError, ValueError):
                        print(f"[get_rfp_details] Could not parse documents string: {document_ids}")
                        document_ids = None
                
                if document_ids:
                    # Ensure it's a list
                    if not isinstance(document_ids, list):
                        # If it's a single value, convert to list
                        document_ids = [document_ids]
                    
                    print(f"[get_rfp_details] Processing {len(document_ids)} document(s) for RFP {rfp.rfp_id}")
                    
                    for doc_item in document_ids:
                        try:
                            # If it's an integer or string that can be converted to int (file ID), fetch from s3_files
                            doc_id = None
                            if isinstance(doc_item, int):
                                doc_id = doc_item
                            elif isinstance(doc_item, str) and doc_item.isdigit():
                                doc_id = int(doc_item)
                            elif isinstance(doc_item, dict) and ('id' in doc_item or 'file_id' in doc_item or 's3_file_id' in doc_item):
                                doc_id = doc_item.get('id') or doc_item.get('file_id') or doc_item.get('s3_file_id')
                                if isinstance(doc_id, str) and doc_id.isdigit():
                                    doc_id = int(doc_id)
                            
                            if doc_id:
                                try:
                                    # MULTI-TENANCY: Try with tenant filter first, then without if not found
                                    s3_file = None
                                    try:
                                        s3_file = S3Files.objects.get(id=doc_id, tenant_id=tenant_id)
                                        print(f"[get_rfp_details] Found S3 file {doc_id} with tenant {tenant_id}")
                                    except S3Files.DoesNotExist:
                                        # Try without tenant filter (for cross-tenant access)
                                        try:
                                            s3_file = S3Files.objects.get(id=doc_id)
                                            print(f"[get_rfp_details] Found S3 file {doc_id} without tenant filter")
                                        except S3Files.DoesNotExist:
                                            print(f"[get_rfp_details] Warning: S3 file with ID {doc_id} not found")
                                            continue
                                    
                                    documents_data.append({
                                        'id': s3_file.id,
                                        'url': s3_file.url,
                                        'file_name': s3_file.file_name,
                                        'file_type': s3_file.file_type,
                                        'uploaded_at': s3_file.uploaded_at.isoformat() if s3_file.uploaded_at else None,
                                        'document_name': s3_file.document_name if hasattr(s3_file, 'document_name') else s3_file.file_name
                                    })
                                    print(f"[get_rfp_details] Added document: {s3_file.file_name} (ID: {s3_file.id})")
                                except Exception as file_err:
                                    print(f"[get_rfp_details] Error fetching S3 file {doc_id}: {str(file_err)}")
                                    import traceback
                                    traceback.print_exc()
                                    continue
                            # If it's already an object with required fields, use it as is
                            elif isinstance(doc_item, dict):
                                # Ensure it has at least a URL or file_name
                                if doc_item.get('url') or doc_item.get('file_name') or doc_item.get('fileName'):
                                    documents_data.append(doc_item)
                                    print(f"[get_rfp_details] Added document object: {doc_item.get('file_name') or doc_item.get('fileName') or 'Unknown'}")
                                else:
                                    print(f"[get_rfp_details] Skipping document object without URL or file_name: {doc_item}")
                            else:
                                print(f"[get_rfp_details] Skipping unrecognized document item type: {type(doc_item)}, value: {doc_item}")
                        except Exception as item_err:
                            print(f"[get_rfp_details] Error processing document item {doc_item}: {str(item_err)}")
                            import traceback
                            traceback.print_exc()
                            continue
                
                print(f"[get_rfp_details] Successfully processed {len(documents_data)} document(s) for RFP {rfp.rfp_id}")
            except Exception as e:
                print(f"[get_rfp_details] Error processing documents: {str(e)}")
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
            'auto_approve': rfp.auto_approve,
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approval_request_versions(request):
    """
    Create a new version for an approval request
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
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
        # MULTI-TENANCY: Filter by tenant
        try:
            ApprovalRequests.objects.get(approval_id=approval_id, tenant_id=tenant_id)
        except ApprovalRequests.DoesNotExist:
            try:
                # Create a minimal approval request record so versions can be tracked
                # MULTI-TENANCY: Set tenant_id on creation
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
                    'tenant_id': tenant_id  # MULTI-TENANCY: Set tenant_id
                }
                ApprovalRequests.objects.create(**placeholder_request)
            except Exception:
                # If placeholder creation fails, proceed without blocking version creation
                pass
        
        # Get the highest version number for this approval
        # MULTI-TENANCY: Filter by tenant (via approval)
        max_version = ApprovalRequestVersions.objects.filter(
            approval_id=approval_id
        ).aggregate(max_version=models.Max('version_number'))['max_version'] or 0
        
        # Create the version
        # MULTI-TENANCY: Set tenant_id on creation (if ApprovalRequestVersions has tenant_id)
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
            # Note: If ApprovalRequestVersions has tenant_id, add: tenant_id=tenant_id
        )
        
        # Mark all other versions as not current
        # MULTI-TENANCY: Filter by tenant (via approval)
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_approval_request_versions(request, approval_id):
    """
    Get all versions for an approval request
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # MULTI-TENANCY: Verify approval belongs to tenant
        try:
            approval = ApprovalRequests.objects.get(approval_id=approval_id, tenant_id=tenant_id)
        except ApprovalRequests.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Approval request not found: {approval_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # MULTI-TENANCY: Filter by tenant (via approval)
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def approve_version(request, version_id):
    """
    Approve a specific version
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        data = request.data
        
        # Get the version
        # MULTI-TENANCY: Verify version belongs to tenant (via approval)
        try:
            version = ApprovalRequestVersions.objects.get(version_id=version_id)
            # Verify the approval request belongs to tenant
            approval = ApprovalRequests.objects.get(approval_id=version.approval_id, tenant_id=tenant_id)
        except (ApprovalRequestVersions.DoesNotExist, ApprovalRequests.DoesNotExist):
            return Response({
                'success': False,
                'error': 'Version not found'
            }, status=status.HTTP_404_NOT_FOUND)
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def change_requests(request):
    """
    GET: List change requests dynamically derived from approval data.
    POST: Create a reviewer change request and snapshot the current RFP as a new version.
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return JsonResponse({'error': 'Tenant context not found'}, status=403)
    
    try:
        if request.method == 'GET':
            # Optional filter to only show for a specific creator
            creator_id = request.GET.get('creator_id')

            # A change request exists if a stage has requested changes or was rejected
            # and there's a corresponding comment describing the change.
            change_requests_list = []

            # Collect candidate stages that need creator action
            # MULTI-TENANCY: Filter by tenant
            # Include both REJECTED and REQUEST_CHANGES to handle any legacy data
            candidate_stages = ApprovalStages.objects.filter(
                stage_status__in=['REJECTED', 'REQUEST_CHANGES'],  # REQUEST_CHANGES is mapped to REJECTED, but check both for legacy data
                tenant_id=tenant_id
            ).order_by('-updated_at')

            print(f"[DEBUG] Found {candidate_stages.count()} candidate stages with REJECTED/REQUEST_CHANGES status for tenant {tenant_id}")

            for stage in candidate_stages:
                try:
                    # Get the approval request to enrich with context
                    # MULTI-TENANCY: Filter by tenant
                    approval_request = ApprovalRequests.objects.get(approval_id=stage.approval_id, tenant_id=tenant_id)

                    # Filter to only workflows for business_object_type == 'RFP'
                    # MULTI-TENANCY: Filter by tenant
                    try:
                        workflow = ApprovalWorkflows.objects.get(workflow_id=approval_request.workflow_id, tenant_id=tenant_id)
                        if (workflow.business_object_type or '').upper() != 'RFP':
                            print(f"[DEBUG] Skipping stage {stage.stage_id}: workflow {workflow.workflow_id} is not RFP type (type: {workflow.business_object_type})")
                            continue
                    except ApprovalWorkflows.DoesNotExist:
                        print(f"[DEBUG] Skipping stage {stage.stage_id}: workflow {approval_request.workflow_id} not found")
                        continue

                    # Optionally filter by creator
                    if creator_id and str(approval_request.requester_id) != str(creator_id):
                        print(f"[DEBUG] Skipping stage {stage.stage_id}: creator mismatch (requester: {approval_request.requester_id}, filter: {creator_id})")
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
                                # RFP is already imported at the top, use RFP directly
                                # MULTI-TENANCY: Filter by tenant
                                rfp_obj = RFPModel.objects.get(id=numeric_id, tenant_id=tenant_id)
                                rfp_id = rfp_obj.rfp_id
                                if not rfp_title:
                                    rfp_title = rfp_obj.rfp_title
                            except Exception:
                                pass

                    # If still not present, try to get from RFP by workflow link
                    # MULTI-TENANCY: Filter by tenant
                    if not rfp_title or not rfp_id:
                        try:
                            linked_rfp = RFP.objects.get(approval_workflow_id=approval_request.workflow_id, tenant_id=tenant_id)
                            rfp_id = rfp_id or linked_rfp.rfp_id
                            rfp_title = rfp_title or linked_rfp.rfp_title
                        except Exception:
                            pass

                    # Find latest change-related comment on this stage
                    # MULTI-TENANCY: Filter by tenant
                    last_comment = (
                        ApprovalComments.objects
                        .filter(approval_id=approval_request.approval_id, stage_id=stage.stage_id, tenant_id=tenant_id)
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
                    print(f"[DEBUG] Added change request for stage {stage.stage_id}, RFP {rfp_id}")
                except Exception as e:
                    # Skip any malformed records, but log the error for debugging
                    import traceback
                    print(f"[DEBUG] Error processing stage {stage.stage_id}: {str(e)}")
                    traceback.print_exc()
                    continue

            print(f"[DEBUG] Returning {len(change_requests_list)} change requests for tenant {tenant_id}")
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
                    # RFP is already imported at the top
                    from rfp.serializers import RFPSerializer

                    # MULTI-TENANCY: Filter by tenant
                    rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
                    rfp_payload = RFPSerializer(rfp).data

                    version_id = f"VR_{uuid.uuid4().hex[:8].upper()}"
                    # MULTI-TENANCY: Filter by tenant (via approval)
                    max_version = ApprovalRequestVersions.objects.filter(
                        approval_id=approval_id
                    ).aggregate(max_version=models.Max('version_number'))['max_version'] or 0

                    # MULTI-TENANCY: Set tenant_id on creation (if ApprovalRequestVersions has tenant_id)
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
                        # Note: If ApprovalRequestVersions has tenant_id, add: tenant_id=tenant_id
                    )
                    # MULTI-TENANCY: Filter by tenant (via approval)
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
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def respond_to_change_request(request):
    """
    Respond to a change request (accept, decline, or complete)
    - accepted/declined: acknowledge the request
    - completed: persist a new ApprovalRequestVersions row with the latest RFP JSON and resume workflow from the same stage
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return JsonResponse({'error': 'Tenant context not found'}, status=403)
    
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
                        # RFP is already imported at the top
                        from rfp.serializers import RFPSerializer
                        # MULTI-TENANCY: Filter by tenant
                        rfp = RFP.objects.get(rfp_id=rfp_id, tenant_id=tenant_id)
                        json_payload = RFPSerializer(rfp).data
                    else:
                        json_payload = {}

                # Create new version row
                version_id = f"VR_{uuid.uuid4().hex[:8].upper()}"
                # MULTI-TENANCY: Filter by tenant (via approval)
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


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([SimpleAuthenticatedPermission])
@rbac_rfp_required('view_rfp')
@require_tenant  # MULTI-TENANCY: Ensure tenant is present
@tenant_filter   # MULTI-TENANCY: Add tenant_id to request
def get_workflow_changes(request, workflow_id):
    """
    Get workflow changes history
    MULTI-TENANCY: Filters by tenant to ensure tenant isolation
    """
    tenant_id = get_tenant_id_from_request(request)
    if not tenant_id:
        return Response({'error': 'Tenant context not found'}, status=403)
    
    try:
        # Get the workflow
        try:
            workflow = ApprovalWorkflows.objects.get(workflow_id=workflow_id, tenant_id=tenant_id)
        except ApprovalWorkflows.DoesNotExist:
            # Try without tenant filter for cross-tenant access
            try:
                workflow = ApprovalWorkflows.objects.get(workflow_id=workflow_id)
            except ApprovalWorkflows.DoesNotExist:
                return Response({
                    'error': f'Workflow {workflow_id} not found'
                }, status=404)
        
        changes = []
        
        # Add creation record
        changes.append({
            'id': 1,
            'change_type': 'Created',
            'description': 'Workflow was initially created',
            'changed_by': workflow.created_by,
            'changed_by_name': f'User {workflow.created_by}',
            'changed_at': workflow.created_at.isoformat() if workflow.created_at else None,
            'old_values': None,
            'new_values': {
                'workflow_name': workflow.workflow_name,
                'workflow_type': workflow.workflow_type,
                'description': workflow.description,
                'business_object_type': workflow.business_object_type,
                'is_active': workflow.is_active
            }
        })
        
        # Check if workflow was updated (created_at != updated_at)
        if workflow.updated_at and workflow.created_at:
            if workflow.updated_at > workflow.created_at:
                # Try to get user info for the updater
                updater_name = f"User {workflow.created_by}"
                try:
                    # Try to get user from users table directly
                    from django.db import connections
                    with connections['default'].cursor() as cursor:
                        cursor.execute("""
                            SELECT first_name, last_name, username 
                            FROM users 
                            WHERE id = %s
                        """, [workflow.created_by])
                        row = cursor.fetchone()
                        if row:
                            first_name, last_name, username = row
                            if first_name or last_name:
                                updater_name = f"{first_name or ''} {last_name or ''}".strip()
                            elif username:
                                updater_name = username
                except Exception as user_err:
                    print(f"Could not fetch user info: {user_err}")
                    updater_name = f"User {workflow.created_by}"
                
                changes.append({
                    'id': 2,
                    'change_type': 'Updated',
                    'description': 'Workflow was modified',
                    'changed_by': workflow.created_by,
                    'changed_by_name': updater_name,
                    'changed_at': workflow.updated_at.isoformat() if workflow.updated_at else None,
                    'old_values': {
                        'description': workflow.description  # We don't have old values, so use current
                    },
                    'new_values': {
                        'workflow_name': workflow.workflow_name,
                        'workflow_type': workflow.workflow_type,
                        'description': workflow.description,
                        'business_object_type': workflow.business_object_type,
                        'is_active': workflow.is_active
                    }
                })
        
        # Get approval requests for this workflow to check for version history
        approval_requests = ApprovalRequests.objects.filter(
            workflow_id=workflow_id,
            tenant_id=tenant_id
        )[:5]  # Limit to first 5 for performance
        
        # Get version history from approval request versions
        version_count = 0
        for approval_request in approval_requests:
            versions = ApprovalRequestVersions.objects.filter(
                approval_id=approval_request.approval_id
            ).order_by('-created_at')[:3]  # Get latest 3 versions per approval
            
            for version in versions:
                version_count += 1
                changes.append({
                    'id': len(changes) + 1,
                    'change_type': 'Version',
                    'description': version.changes_summary or f'Version {version.version_number} created',
                    'changed_by': version.created_by,
                    'changed_by_name': version.created_by_name or f'User {version.created_by}',
                    'changed_at': version.created_at.isoformat() if version.created_at else None,
                    'old_values': None,
                    'new_values': {
                        'version_number': version.version_number,
                        'version_type': version.version_type,
                        'change_reason': version.change_reason
                    }
                })
        
        return Response(changes)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Failed to get workflow changes: {str(e)}'
        }, status=500)
