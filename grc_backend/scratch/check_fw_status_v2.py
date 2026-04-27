import os
import sys
import django
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path("c:/Users/Admin/Desktop/GRC_TPRM/grc_backend").resolve()))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.models import Framework

def check_framework_status(fw_id):
    try:
        fw = Framework.objects.get(FrameworkId=fw_id)
        print(f"--- Framework: {fw_id} ---")
        # Decrypt name if needed
        from grc.utils.data_encryption import decrypt_data
        try:
            name = decrypt_data(fw.FrameworkName)
            print(f"Name: {name}")
        except:
            print(f"Name (raw): {fw.FrameworkName}")
            
        print(f"Latest Comparison Date: {fw.latestComparisionCheckDate}")
        print(f"Amendment field length: {len(str(fw.Amendment)) if fw.Amendment else 0}")
        if fw.Amendment:
            # Show the last part of the amendment field if it's a list
            if isinstance(fw.Amendment, list) and len(fw.Amendment) > 0:
                last = fw.Amendment[-1]
                print(f"Latest amendment status: {last.get('status') if isinstance(last, dict) else 'N/A'}")
                print(f"Latest amendment cancel_requested: {last.get('cancel_requested') if isinstance(last, dict) else 'N/A'}")
            else:
                print(f"Amendment content: {fw.Amendment}")
                
    except Exception as e:
        print(f"Error checking {fw_id}: {e}")

if __name__ == "__main__":
    check_framework_status(392)
    check_framework_status(3)
