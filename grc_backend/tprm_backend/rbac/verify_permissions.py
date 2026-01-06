"""
Quick script to verify testuser1's RBAC permissions
Run: python manage_contract.py shell < backend/rbac/verify_permissions.py
"""

from tprm_backend.rbac.models import RBACTPRM
from tprm_backend.mfa_auth.models import User

print("\n" + "="*60)
print("RBAC Permission Verification for testuser1")
print("="*60 + "\n")

try:
    # Get testuser1
    user = User.objects.get(username='testuser1')
    print(f"✓ Found user: {user.username} (ID: {user.userid})")
    
    # Get RBAC record
    try:
        rbac = RBACTPRM.objects.get(user_id=user.userid, is_active='Y')
        print(f"✓ Found active RBAC record")
        print(f"  - Role: {rbac.role}")
        print(f"  - RBAC ID: {rbac.rbac_id}")
        
        # Check contract permissions
        print("\n" + "-"*60)
        print("Contract Permissions Status:")
        print("-"*60)
        
        permissions_to_check = {
            'list_contracts': 'List Contracts',
            'create_contract': 'Create Contract',
            'update_contract': 'Update Contract',
            'delete_contract': 'Delete Contract',
            'approve_contract': 'Approve Contract',
            'reject_contract': 'Reject Contract',
            'list_contract_terms': 'List Contract Terms',
            'create_contract_term': 'Create Contract Term',
            'update_contract_term': 'Update Contract Term',
            'delete_contract_term': 'Delete Contract Term',
            'list_contract_renewals': 'List Contract Renewals',
            'create_contract_renewal': 'Create Contract Renewal',
            'approve_contract_renewal': 'Approve Contract Renewal',
            'reject_contract_renewal': 'Reject Contract Renewal',
            'contract_dashboard': 'Contract Dashboard',
            'contract_search': 'Contract Search',
            'trigger_ocr': 'Trigger OCR',
            'get_nlp_clauses': 'Get NLP Clauses',
            'create_contract_audit': 'Create Contract Audit',
            'perform_contract_audit': 'Perform Contract Audit',
            'validate_contract_data': 'Validate Contract Data'
        }
        
        all_granted = True
        missing_permissions = []
        
        for field_name, display_name in permissions_to_check.items():
            has_permission = getattr(rbac, field_name, False)
            status = "✓ GRANTED" if has_permission else "✗ DENIED"
            color = "" if has_permission else "⚠️ "
            print(f"{color}{status:12} - {display_name}")
            
            if not has_permission:
                all_granted = False
                missing_permissions.append(field_name)
        
        print("\n" + "-"*60)
        if all_granted:
            print("✅ SUCCESS: All contract permissions are granted!")
            print("\nThe dashboard should work now. Try:")
            print("1. Restart your Django server")
            print("2. Clear browser cache and refresh")
            print("3. Access: http://localhost:5173/contracts/dashboard")
        else:
            print(f"⚠️  WARNING: {len(missing_permissions)} permissions are DENIED")
            print("\nMissing permissions:")
            for perm in missing_permissions:
                print(f"  - {perm}")
            
            print("\nTo grant these permissions, run:")
            print("UPDATE rbac_tprm SET")
            update_fields = ", ".join([f"{perm}=1" for perm in missing_permissions[:3]])
            if len(missing_permissions) > 3:
                update_fields += f", ... (and {len(missing_permissions)-3} more)"
            print(f"  {update_fields}")
            print(f"WHERE UserId = {user.userid};")
        
        print("="*60 + "\n")
        
    except RBACTPRM.DoesNotExist:
        print(f"✗ No RBAC record found for user_id {user.userid}")
        print("\nYou need to create an RBAC record for this user.")
        print("Run the following SQL:")
        print(f"""
INSERT INTO rbac_tprm (UserId, UserName, Role, 
    ListContracts, CreateContract, UpdateContract, DeleteContract,
    ApproveContract, RejectContract,
    ListContractTerms, CreateContractTerm, UpdateContractTerm, DeleteContractTerm,
    ListContractRenewals, CreateContractRenewal, ApproveContractRenewal, RejectContractRenewal,
    ContractDashboard, ContractSearch, TriggerOCR, GetNLPClauses, CreateContractAudit, PerformContractAudit, ValidateContractData,
    IsActive, CreatedAt, UpdatedAt
) VALUES (
    {user.userid}, '{user.username}', 'Contract Manager',
    1, 1, 1, 1, 1, 1,
    1, 1, 1, 1,
    1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1,
    'Y', NOW(), NOW()
);
        """)
        
except User.DoesNotExist:
    print(f"✗ User 'testuser1' not found in database")
    print("\nPlease create the user first or change the username in this script.")
    
except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

