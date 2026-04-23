import os
import sys
import django
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path("c:/Users/Admin/Desktop/GRC_TPRM/grc_backend").resolve()))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grc_backend.settings')
django.setup()

from grc.models import Framework

def check_framework_status(fw_id):
    try:
        fw = Framework.objects.get(FrameworkId=fw_id)
        print(f"Framework: {fw_id}")
        # Decrypt name if needed
        from grc.utils.data_encryption import decrypt_data
        try:
            name = decrypt_data(fw.FrameworkName)
            print(f"Name: {name}")
        except:
            print(f"Name (raw): {fw.FrameworkName}")
            
        print(f"Amendment: {fw.Amendment}")
        print(f"Latest Comparison Date: {fw.latestComparisionCheckDate}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_framework_status(392)
    check_framework_status(3)
