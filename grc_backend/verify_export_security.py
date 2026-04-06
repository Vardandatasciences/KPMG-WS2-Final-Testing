import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append(r'C:\Users\Admin\Desktop\GRC_TPRM-1\grc_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.routes.Global.s3_fucntions import _sanitize_export_payload, EXPORT_MAX_NESTED_DEPTH, EXPORT_MAX_STRING_LEN

def test_template_neutralization():
    print("Testing template token neutralization...")
    payload = {
        "description": "User input with {{ config.SECRET_KEY }} and {% dangerous_loop %}"
    }
    sanitized = _sanitize_export_payload(payload)
    print(f"Original: {payload['description']}")
    print(f"Sanitized: {sanitized['description']}")
    assert "{{" not in sanitized["description"]
    assert "{%" not in sanitized["description"]
    print("Template neutralization passed!")

def test_recursion_limit():
    print("\nTesting recursion limits...")
    # Create a deeply nested object
    nested = {"a": "b"}
    for _ in range(EXPORT_MAX_NESTED_DEPTH + 1):
        nested = {"child": nested}
    
    try:
        _sanitize_export_payload(nested)
        print("❌ Recursion limit failed (should have raised ValueError)")
    except ValueError as e:
        print(f"Recursion limit passed: {str(e)}")

def test_string_length_limit():
    print("\nTesting string length limit...")
    long_string = "A" * (EXPORT_MAX_STRING_LEN + 100)
    payload = {"long": long_string}
    sanitized = _sanitize_export_payload(payload)
    print(f"Original length: {len(long_string)}")
    print(f"Sanitized length: {len(sanitized['long'])}")
    assert len(sanitized["long"]) == EXPORT_MAX_STRING_LEN
    print("String length limit passed!")

if __name__ == "__main__":
    try:
        test_template_neutralization()
        test_recursion_limit()
        test_string_length_limit()
        print("\nALL RENDERING PERIMETER SECURITY TESTS PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {str(e)}")
        sys.exit(1)
