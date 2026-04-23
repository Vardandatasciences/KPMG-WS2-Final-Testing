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

def fix_stuck_amendments(framework_ids):
    for fw_id in framework_ids:
        try:
            fw = Framework.objects.get(FrameworkId=fw_id)
            amendments = fw.Amendment if fw.Amendment else []
            if not isinstance(amendments, list):
                print(f"Framework {fw_id}: Amendment is not a list. Skipping.")
                continue

            updated = False
            for idx, a in enumerate(amendments):
                if not isinstance(a, dict):
                    continue

                # 1. Fix stuck processing or cancelled state
                is_stuck = not a.get('processed') or a.get('cancel_requested')
                
                if is_stuck:
                    print(f"Fixing stuck amendment in FW {fw_id}: {a.get('document_name')}")
                    a['processed'] = True
                    if a.get('cancel_requested'):
                        a['processing_error'] = "Cancelled by user (Reset)"
                        a['processing_status'] = "cancelled"
                    else:
                        a['processing_error'] = "Analysis interrupted or failed (Reset)"
                        a['processing_status'] = "failed"
                    
                    a['processed_date'] = datetime.now().isoformat()
                    a['cancel_requested'] = False # Clear flag
                    updated = True

                # 2. Fix path if it's a Linux path starting with /app/
                doc_path = a.get('document_path')
                if doc_path and isinstance(doc_path, str) and doc_path.startswith('/app/'):
                    new_path = doc_path.replace('/app/', BASE_DIR + '/')
                    new_path = new_path.replace('/', os.sep)
                    print(f"Fixing path in FW {fw_id}: {doc_path} -> {new_path}")
                    a['document_path'] = new_path
                    updated = True

            if updated:
                fw.Amendment = amendments
                fw.save(update_fields=['Amendment'])
                print(f"SUCCESS: Updated Framework {fw_id}")
            else:
                print(f"INFO: No changes needed for Framework {fw_id}")

        except Exception as e:
            print(f"ERROR fixing Framework {fw_id}: {str(e).encode('ascii', 'ignore').decode('ascii')}")

if __name__ == "__main__":
    print("Starting cleanup of stuck amendments...")
    fix_stuck_amendments([3, 392])
    print("Cleanup complete.")
