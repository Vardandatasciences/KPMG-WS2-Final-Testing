"""
Diagnostic script to test RFP update and find the exact error
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tprm_project.settings')
django.setup()

from tprm_backend.rfp.models import RFP
from tprm_backend.rfp.serializers import RFPSerializer
from decimal import Decimal
import traceback

print("="*80)
print("DIAGNOSTIC TEST FOR RFP UPDATE")
print("="*80)

# Test data (same as your frontend is sending)
test_data = {
    'rfp_title': 'swdefr',
    'description': 'fwhe',
    'rfp_type': 'TECHNOLOGY',
    'category': 'security',
    'estimated_value': 20000
}

print("\nTest Data:")
print(test_data)
print("")

# Try to get RFP 128
print("Step 1: Getting RFP 128...")
try:
    rfp = RFP.objects.get(rfp_id=128)
    print(f"✅ Found RFP 128: {rfp.rfp_title}")
except Exception as e:
    print(f"❌ Error getting RFP: {e}")
    traceback.print_exc()
    exit(1)

# Try to create serializer
print("\nStep 2: Creating serializer with partial=True...")
try:
    serializer = RFPSerializer(rfp, data=test_data, partial=True)
    print("✅ Serializer created")
except Exception as e:
    print(f"❌ Error creating serializer: {e}")
    traceback.print_exc()
    exit(1)

# Try to validate
print("\nStep 3: Validating data...")
try:
    is_valid = serializer.is_valid()
    print(f"Is valid: {is_valid}")
    
    if is_valid:
        print("✅ Validation passed")
        print(f"Validated data: {serializer.validated_data}")
    else:
        print("❌ Validation failed")
        print(f"Errors: {serializer.errors}")
        exit(1)
except Exception as e:
    print(f"❌ Error during validation: {e}")
    traceback.print_exc()
    exit(1)

# Try to save
print("\nStep 4: Saving...")
try:
    updated_rfp = serializer.save()
    print(f"✅ Saved successfully: {updated_rfp.rfp_title}")
    print(f"   Estimated value: {updated_rfp.estimated_value}")
    print(f"   Type: {type(updated_rfp.estimated_value)}")
except Exception as e:
    print(f"❌ Error during save: {e}")
    traceback.print_exc()
    exit(1)

print("\n" + "="*80)
print("✅ ALL TESTS PASSED!")
print("="*80)
print("\nThe serializer works correctly.")
print("If you're still getting 500 error, it's NOT the serializer.")
print("It's something in the view or middleware.")
print("\nPlease check:")
print("1. Is the backend server restarted?")
print("2. Check backend terminal for the actual error")
print("3. Look for middleware or view-level errors")








