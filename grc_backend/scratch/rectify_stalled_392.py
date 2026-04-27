import os
import sys
import django
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
BASE_DIR = "c:/Users/Admin/Desktop/GRC_TPRM/grc_backend"
sys.path.append(str(Path(BASE_DIR).resolve()))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import Framework

def rectify_stalled_392():
    try:
        fw_id = 392
        fw = Framework.objects.get(FrameworkId=fw_id)
        amendments = fw.Amendment if fw.Amendment else []
        if not isinstance(amendments, list):
            print(f"Framework {fw_id}: Amendment is not a list. Skipping.")
            return

        updated = False
        for a in amendments:
            if not isinstance(a, dict):
                continue

            # Identify entries that are stuck in 'processed=False'
            if not a.get('processed'):
                print(f"Rectifying stalled amendment: {a.get('document_name')}")
                a['processed'] = True
                a['processed_date'] = datetime.now().isoformat()
                a['processing_error'] = "Stalled analysis reset by system"
                a['processing_status'] = "failed"
                updated = True

        if updated:
            fw.Amendment = amendments
            fw.save(update_fields=['Amendment'])
            print(f"SUCCESS: Rectified Framework {fw_id}")
        else:
            print(f"INFO: No stalled amendments found for Framework {fw_id}")

    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    rectify_stalled_392()
