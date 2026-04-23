try:
    import pymupdf
    print(f"PyMuPDF file: {pymupdf.__file__}")
    print(f"PyMuPDF dir: {dir(pymupdf)}")
    doc = pymupdf.open()
    print("pymupdf.open() exists")
    doc.close()
except ImportError:
    print("pymupdf module NOT found")
except AttributeError as e:
    print(f"PyMuPDF Error: {e}")
except Exception as e:
    print(f"Other error: {e}")

try:
    import fitz
    print(f"Fitz file: {fitz.__file__}")
    print(f"Fitz dir: {dir(fitz)}")
    doc = fitz.open()
    print("fitz.open() exists")
    doc.close()
except ImportError:
    print("fitz module NOT found")
except AttributeError as e:
    print(f"fitz Error: {e}")
except Exception as e:
    print(f"Other error: {e}")
