"""
Script to check available audits in the database
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import Audit

def list_audits():
    """List available audits"""
    try:
        audits = Audit.objects.all()[:20]  # Get first 20 audits
        
        if not audits:
            print("[WARNING] No audits found in the database!")
            print("You need to create an audit first.")
            return
        
        print("=" * 70)
        print("AVAILABLE AUDITS")
        print("=" * 70)
        print()
        
        for audit in audits:
            print(f"Audit ID: {audit.AuditId}")
            print(f"  Audit Name: {getattr(audit, 'AuditName', 'N/A')}")
            print(f"  Status: {getattr(audit, 'Status', 'N/A')}")
            print(f"  Tenant ID: {getattr(audit, 'TenantId', getattr(audit, 'tenant_id', 'N/A'))}")
            print()
        
        print("=" * 70)
        print(f"Total audits found: {Audit.objects.count()}")
        print("=" * 70)
        print()
        print("USAGE IN POSTMAN:")
        print("Replace {{audit_id}} in your URL with one of the Audit IDs above")
        print(f"Example: http://localhost:8000/api/audits/{audits[0].AuditId}")
        
    except Exception as e:
        print(f"[ERROR] Error fetching audits: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    list_audits()
