import sys
import os
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path("c:/Users/Admin/Desktop/GRC_TPRM/grc_backend").resolve()))

def test_load_doc():
    try:
        from grc.routes.uploadNist.index_content_extractor import load_doc
        print("Successfully imported load_doc")
        
        # We don't necessarily need a real PDF to test if the attribute exists
        # But let's check the module itself
        import pymupdf as fitz
        print(f"fitz module: {fitz}")
        print(f"fitz.open attribute: {getattr(fitz, 'open', 'MISSING')}")
        
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_load_doc()
