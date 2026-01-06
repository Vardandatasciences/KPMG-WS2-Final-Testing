"""
Simple script to run in Django shell to grant BCP/DRP permissions
Usage: python manage.py shell < grant_bcp_perms_simple.py
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
    rbac_record, created = RBACTPRM.objects.get_or_create(
        user_id=user_id,
        defaults={
            'username': username,
            'role': 'Admin'
        }
    )
    
    if created:
        print(f"✓ Created new RBAC record")
    else:
        print(f"✓ Found existing RBAC record (Role: {rbac_record.role})")
    
    # Grant all BCP/DRP permissions
    bcp_drp_perms = [
        'create_bcp_drp_strategy_and_plans', 'view_plans_and_documents',
        'assign_plans_for_evaluation', 'approve_or_reject_plan_evaluations',
        'ocr_extraction_and_review', 'view_bcp_drp_plan_status',
        'add_vendor_to_bcp_drp_strategy', 'manage_server_resources_for_bcp_drp',
        'create_questionnaire_for_testing', 'review_questionnaire_answers',
        'final_approval_of_plan', 'create_questionnaire',
        'assign_questionnaires_for_review', 'view_all_questionnaires',
        'configure_system_settings', 'configure_questionnaire_settings',
        'generate_compliance_audit_reports', 'view_document_status_history',
        'view_available_vendors', 'assess_vendor_risk', 'view_vendor_risk_scores',
        'identify_risks_in_plans', 'view_identified_risks',
        'manage_risk_mitigation_plans', 'view_risk_mitigation_status',
    ]
    
    granted = 0
    for perm in bcp_drp_perms:
        if hasattr(rbac_record, perm):
            setattr(rbac_record, perm, True)
            granted += 1
    
    rbac_record.is_active = 'Y'
    rbac_record.save()
    
    print(f"\n✓ SUCCESS! Granted {granted} BCP/DRP permissions to {username}")
    print(f"✓ Key permissions verified:")
    for perm in ['create_bcp_drp_strategy_and_plans', 'view_plans_and_documents', 'approve_or_reject_plan_evaluations']:
        print(f"  - {perm}: {getattr(rbac_record, perm)}")
        
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

