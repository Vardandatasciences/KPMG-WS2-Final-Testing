import fitz
print(f"Fitz file: {fitz.__file__}")
print(f"Fitz dir: {dir(fitz)}")
try:
    doc = fitz.open()
    print("fitz.open() exists")
    doc.close()
except AttributeError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"Other error: {e}")
