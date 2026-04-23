import os
import sys
import django
import json
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path("c:/Users/Admin/Desktop/GRC_TPRM/grc_backend").resolve()))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import Framework

def analyze_amendment_data(fw_id):
    try:
        fw = Framework.objects.get(FrameworkId=fw_id)
        amendments = fw.Amendment if fw.Amendment else []
        if not amendments:
            print(f"Framework {fw_id} has no amendments.")
            return

        latest = amendments[-1]
        summary = {
            'document_name': latest.get('document_name'),
            'processed': latest.get('processed'),
            'cancel_requested': latest.get('cancel_requested'),
            'processing_error': latest.get('processing_error'),
            'sections_count': len(latest.get('sections', [])),
            'total_characters': len(str(latest))
        }
        
        # Count compliances
        all_compliances = []
        for section in latest.get('sections', []):
            for policy in section.get('policies', []):
                for subpolicy in policy.get('subpolicies', []):
                    compliances = subpolicy.get('compliance_records', [])
                    all_compliances.extend(compliances)
        
        summary['compliance_records_count'] = len(all_compliances)
        
        # Check if there are any "in progress" markers?
        # The code doesn't seem to have them, it just appends to the list.
        
        print(json.dumps(summary, indent=2))
        
    except Exception as e:
        print(f"Error analyzing {fw_id}: {e}")

if __name__ == "__main__":
    print("Analyzing Framework 392:")
    analyze_amendment_data(392)
    print("\nAnalyzing Framework 3:")
    analyze_amendment_data(3)
