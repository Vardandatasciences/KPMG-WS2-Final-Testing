"""
Script to grant all RFP permissions to a user
Usage: Get-Content grant_rfp_permissions.py | python manage.py shell
"""

from tprm_backend.rbac.models import RBACTPRM
from tprm_backend.mfa_auth.models import User

username = 'testuser1'

try:
    # Find the user
    user = User.objects.get(username=username)
    user_id = user.userid
    print(f"✓ Found user: {username} (ID: {user_id})")
    
    # Get or create RBAC record
    rbac, created = RBACTPRM.objects.get_or_create(
        user_id=user_id,
        defaults={
            'username': username,
            'role': 'Admin'
        }
    )
    
    if created:
        print(f"✓ Created new RBAC record")
    else:
        print(f"✓ Found existing RBAC record (Role: {rbac.role})")
    
    # Grant all RFP permissions
    rfp_perms = [
        # Core RFP Permissions
        'create_rfp', 'edit_rfp', 'view_rfp', 'delete_rfp', 'clone_rfp',
        
        # Review & Approval
        'submit_rfp_for_review', 'approve_rfp', 'reject_rfp',
        'assign_rfp_reviewers', 'view_rfp_approval_status',
        
        # Versioning
        'view_rfp_versions', 'create_rfp_version', 'edit_rfp_version', 'view_rfp_version',
        
        # Evaluation Criteria
        'create_evaluation_criteria', 'edit_evaluation_criteria', 'delete_evaluation_criteria',
        
        # Vendor Management
        'select_vendors_for_rfp', 'invite_vendors_for_rfp', 'track_rfp_invitations',
        
        # Document Management
        'upload_documents_for_rfp', 'download_rfp_documents', 
        'preview_rfp_documents', 'validate_rfp_documents', 'scan_rfp_files_for_virus',
        
        # RFP Responses
        'view_rfp_responses', 'submit_rfp_response', 'withdraw_rfp_response',
        
        # Evaluation
        'auto_screen_rfp', 'assign_rfp_evaluators', 'score_rfp_response',
        'view_rfp_response_scores', 'rank_vendors_for_rfp',
        'finalize_rfp_evaluation', 'send_rfp_award_notification',
        
        # Analytics & Reporting
        'view_rfp_analytics', 'generate_rfp_reports', 'download_rfp_report',
        
        # Workflow & Lifecycle
        'manage_rfp_lifecycle', 'trigger_rfp_workflow', 'escalate_rfp_workflow',
        'generate_rfp_tokens', 'validate_rfp_access', 'view_rfp_audit_trail',
        
        # Communications
        'send_rfp_notifications', 'broadcast_rfp_communications',
        'clarify_rfp_communications', 'amend_rfp_communications',
        
        # Vendor from RFP
        'create_rfp_vendor_from_rfp', 'match_rfp_vendor',
        
        # System Health
        'perform_rfp_health_check', 'validate_rfp_data', 'track_rfp_activity_log'
    ]
    
    granted = 0
    for perm in rfp_perms:
        if hasattr(rbac, perm):
            setattr(rbac, perm, True)
            granted += 1
    
    rbac.is_active = 'Y'
    rbac.save()
    
    print(f"\n✓ SUCCESS! Granted {granted} RFP permissions to {username}")
    print(f"✓ Key permissions verified:")
    for perm in ['create_rfp', 'view_rfp', 'approve_rfp', 'view_rfp_responses']:
        print(f"  - {perm}: {getattr(rbac, perm)}")
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

