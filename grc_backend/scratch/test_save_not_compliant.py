import os
import django
import json
from django.test import RequestFactory
from django.http import JsonResponse, HttpResponse
import sys

# Setup Django environment
sys.path.append(r'c:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.routes.Audit.auditing import save_audit_version

def test_save_not_compliant():
    factory = RequestFactory()
    
    # Mock payload for "Not Compliant"
    payload = {
        "user_id": 1050,
        "compliances": {
            "1792": {
                "description": "Test compliance item",
                "status": "0",
                "compliance_status": "Not Compliant",
                "evidence": "",
                "comments": "Test negative finding",
                "how_to_verify": "Visual inspection",
                "impact": "Low",
                "recommendation": "Fix it",
                "details_of_finding": "Found a gap",
                "major_minor": "0",
                "severity_rating": 4,
                "why_to_verify": "Safety",
                "what_to_verify": "Process",
                "underlying_cause": "Human error",
                "suggested_action_plan": "Train staff",
                "responsible_for_plan": "Manager",
                "mitigation_date": "2026-05-01",
                "re_audit": False,
                "re_audit_date": "",
                "selected_risks": [],
                "selected_mitigations": []
            }
        },
        "audit_evidence_urls": "",
        "audit_scope": "Test Scope",
        "audit_objective": "Test Objective",
        "overall_comments": "Test overall"
    }
    
    # Audit ID to test with (selecting one from DB)
    from grc.models import Audit
    audit = Audit.objects.first()
    if not audit:
        print("No audit found in DB to test with.")
        return
        
    audit_id = audit.AuditId
    print(f"Testing save_audit_version for AuditId: {audit_id}")
    
    # Create request
    request = factory.post(f'/api/audits/{audit_id}/save-version/', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    # Mock request.data as DRF would provide it
    request.data = payload
    
    # Mock tenant_id in request (needed for decorators/multitenancy)
    request.tenant_id = audit.tenant_id
    
    # Call the function
    try:
        response = save_audit_version(request, audit_id)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")
        
        if response.status_code == 200:
            print("SUCCESS: save_audit_version accepted Not Compliant payload.")
        else:
            print("FAILURE: save_audit_version rejected payload.")
            
    except Exception as e:
        import traceback
        print(f"EXCEPTION: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_save_not_compliant()
