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

def get_status(fw_id):
    try:
        fw = Framework.objects.get(FrameworkId=fw_id)
        amendments = fw.Amendment if fw.Amendment else []
        print(f"Framework {fw_id} has {len(amendments)} amendments.")
        for i, a in enumerate(amendments):
            print(f"[{i}] {a.get('document_name')} | processed={a.get('processed')} | cancel={a.get('cancel_requested')} | error={a.get('processing_error')}")
            # If it's a huge list, maybe only show the last 5
            if len(amendments) > 10 and i < len(amendments) - 5:
                if i == 0: print("...")
                continue
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_status(392)
