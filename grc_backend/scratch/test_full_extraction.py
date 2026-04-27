import os
import sys
import django
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path("c:/Users/Admin/Desktop/GRC_TPRM/grc_backend").resolve()))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.routes.uploadNist.pdf_extractor import extract_sections_from_pdf
from django.conf import settings

def test_extraction():
    # Use the latest file for framework 392
    pdf_path = os.path.join(settings.MEDIA_ROOT, 'change_management', 'Banking_Regulation(RBI_Guidelines)_20260420_120841.pdf')
    output_dir = os.path.join(settings.BASE_DIR, 'scratch', 'test_extraction_out')
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found at {pdf_path}")
        return

    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting test extraction for: {pdf_path}")
    try:
        result = extract_sections_from_pdf(pdf_path, output_dir)
        print(f"Extraction result: {result}")
        
        # Check if index.json exists
        index_path = os.path.join(output_dir, 'index.json')
        if os.path.exists(index_path):
            print("Successfully generated index.json")
        else:
            print("Failed to generate index.json")
            
    except Exception as e:
        print(f"Extraction failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_extraction()
