"""
Script to grant all BCP/DRP permissions to a user (testuser1)
Run with: python manage.py shell < backend/rbac/grant_bcp_permissions.py
Or: python -c "exec(open('backend/rbac/grant_bcp_permissions.py').read())"
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tprm_backend.rbac.models import RBACTPRM
from tprm_backend.mfa_auth.models import User

def grant_all_bcp_drp_permissions(username='testuser1'):
    """
    Grant all BCP/DRP related permissions to a user
    
    Args:
        username: Username to grant permissions to (default: testuser1)
    """
    try:
        # Find the user
        try:
            user = User.objects.get(username=username)
            user_id = user.userid
            print(f"✓ Found user: {username} (ID: {user_id})")
        except User.DoesNotExist:
            print(f"✗ User '{username}' not found in User table")
            return False
        
        # Check if RBAC record exists for this user
        rbac_record, created = RBACTPRM.objects.get_or_create(
            user_id=user_id,
            defaults={
                'username': username,
                'role': 'Admin'  # Default role
            }
        )
        
        if created:
            print(f"✓ Created new RBAC record for {username}")
        else:
            print(f"✓ Found existing RBAC record for {username} (Role: {rbac_record.role})")
        
        # List of all BCP/DRP related permissions
        bcp_drp_permissions = [
            # Core BCP/DRP Strategy Permissions
            'create_bcp_drp_strategy_and_plans',
            'view_plans_and_documents',
            'assign_plans_for_evaluation',
            'approve_or_reject_plan_evaluations',
            'ocr_extraction_and_review',
            'view_bcp_drp_plan_status',
            'add_vendor_to_bcp_drp_strategy',
            'manage_server_resources_for_bcp_drp',
            'integrate_bcp_drp_with_external_systems',
            
            # Questionnaire Permissions
            'create_questionnaire_for_testing',
            'review_questionnaire_answers',
            'final_approval_of_plan',
            'create_questionnaire',
            'assign_questionnaires_for_review',
            'view_all_questionnaires',
            
            # System Configuration
            'configure_system_settings',
            'configure_questionnaire_settings',
            'create_update_user_roles',
            'manage_document_access_controls',
            
            # Compliance and Audit
            'generate_compliance_audit_reports',
            'view_document_status_history',
            'request_document_revisions_from_vendor',
            'view_vendor_submitted_documents',
            
            # Vendor Coordination
            'coordinate_vendor_feedback',
            'evaluate_plan_based_on_criteria',
            'submit_evaluation_feedback',
            'view_vendor_contracts',
            'create_modify_contracts',
            'view_available_vendors',
            'assess_vendor_risk',
            'view_vendor_risk_scores',
            
            # Risk Management
            'identify_risks_in_plans',
            'view_identified_risks',
            'manage_risk_mitigation_plans',
            'view_risk_mitigation_status',
            
            # Compliance and Regulatory
            'view_compliance_status_of_plans',
            'audit_compliance_of_documents',
            'configure_document_security_settings',
            'view_document_access_logs',
            'review_regulatory_compliance',
            'audit_compliance_against_regulations',
            
            # Legal and Contractual
            'review_and_approve_legal_aspects_of_plans',
            'generate_legal_compliance_reports',
            'view_contractual_obligations',
            
            # Audit and Documentation
            'audit_plan_documentation',
            'view_audit_logs',
            'generate_internal_audit_reports',
            'conduct_external_compliance_audit',
            'generate_external_audit_reports',
            'review_external_auditor_comments',
            'audit_compliance_of_plans',
            'view_compliance_audit_results',
            'generate_compliance_reports',
            
            # System Management
            'monitor_system_health',
            'backup_system_configuration',
            
            # Incident Response
            'view_incident_response_plans',
            'create_incident_response_plans',
        ]
        
        # Grant all permissions
        granted_count = 0
        for permission in bcp_drp_permissions:
            if hasattr(rbac_record, permission):
                setattr(rbac_record, permission, True)
                granted_count += 1
        
        # Set active status
        rbac_record.is_active = True
        
        # Save the record
        rbac_record.save()
        
        print(f"\n✓ SUCCESS! Granted {granted_count} BCP/DRP permissions to {username}")
        print(f"✓ RBAC Record ID: {rbac_record.rbac_id}")
        print(f"✓ User ID: {rbac_record.user_id}")
        print(f"✓ Role: {rbac_record.role}")
        print(f"✓ Active: {rbac_record.is_active}")
        
        # Verify key permissions
        print("\n✓ Key BCP/DRP Permissions Verified:")
        key_permissions = [
            'create_bcp_drp_strategy_and_plans',
            'view_plans_and_documents',
            'assign_plans_for_evaluation',
            'approve_or_reject_plan_evaluations',
            'ocr_extraction_and_review',
            'create_questionnaire_for_testing',
            'review_questionnaire_answers',
            'final_approval_of_plan',
        ]
        
        for perm in key_permissions:
            value = getattr(rbac_record, perm, False)
            status = "✓" if value else "✗"
            print(f"  {status} {perm}: {value}")
        
        return True
        
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # You can change the username here if needed
    username = 'testuser1'
    
    # Try to get username from command line args
    if len(sys.argv) > 1:
        username = sys.argv[1]
    
    print(f"\n{'='*60}")
    print(f"  GRANTING BCP/DRP PERMISSIONS TO: {username}")
    print(f"{'='*60}\n")
    
    success = grant_all_bcp_drp_permissions(username)
    
    if success:
        print(f"\n{'='*60}")
        print(f"  ✓ ALL PERMISSIONS GRANTED SUCCESSFULLY!")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print(f"  ✗ FAILED TO GRANT PERMISSIONS")
        print(f"{'='*60}\n")
        sys.exit(1)

