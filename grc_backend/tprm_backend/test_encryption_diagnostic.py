"""
TPRM Encryption Diagnostic Script
Run this to diagnose encryption issues across all TPRM modules.

Usage:
    python manage.py shell < test_encryption_diagnostic.py
    OR
    python test_encryption_diagnostic.py
"""

import os
import sys
import django

# Setup Django
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tprm_project.settings')
    django.setup()

from django.conf import settings
from tprm_backend.utils.data_encryption import (
    get_encryption_service,
    encrypt_data,
    decrypt_data,
    is_encrypted_data
)

print("=" * 80)
print("TPRM ENCRYPTION DIAGNOSTIC")
print("=" * 80)
print()

# Check 1: Encryption Key Configuration
print("1. ENCRYPTION KEY CONFIGURATION")
print("-" * 80)

env_key = os.environ.get('GRC_ENCRYPTION_KEY', None)
settings_key = getattr(settings, 'GRC_ENCRYPTION_KEY', None)

if env_key:
    print(f"   ✅ Environment Variable (GRC_ENCRYPTION_KEY): FOUND")
    print(f"      Key: {env_key[:20]}...{env_key[-10:] if len(env_key) > 30 else ''} (length: {len(env_key)})")
else:
    print(f"   ❌ Environment Variable (GRC_ENCRYPTION_KEY): NOT FOUND")

if settings_key:
    print(f"   ✅ Django Settings (settings.GRC_ENCRYPTION_KEY): FOUND")
    print(f"      Key: {settings_key[:20]}...{settings_key[-10:] if len(settings_key) > 30 else ''} (length: {len(settings_key)})")
else:
    print(f"   ❌ Django Settings (settings.GRC_ENCRYPTION_KEY): NOT FOUND")

if not env_key and not settings_key:
    print()
    print("   ⚠️  CRITICAL: No encryption key found!")
    print("   ⚠️  Encryption will FAIL. Set GRC_ENCRYPTION_KEY in environment or settings.")
    print()
    print("   To generate a key:")
    print("   python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    print()
    sys.exit(1)

print()

# Check 2: Encryption Service Initialization
print("2. ENCRYPTION SERVICE INITIALIZATION")
print("-" * 80)
try:
    encryption_service = get_encryption_service()
    actual_key = encryption_service.encryption_key
    actual_key_str = actual_key.decode() if isinstance(actual_key, bytes) else actual_key
    print(f"   ✅ Encryption service initialized successfully")
    print(f"      Key in use: {actual_key_str[:20]}...{actual_key_str[-10:] if len(actual_key_str) > 30 else ''}")
    print(f"      Key source: {'ENV' if env_key else 'SETTINGS'}")
except RuntimeError as e:
    print(f"   ❌ FAILED: {str(e)}")
    print()
    print("   SOLUTION: Set GRC_ENCRYPTION_KEY in your environment or Django settings")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ ERROR: {str(e)}")
    sys.exit(1)

print()

# Check 3: Encryption/Decryption Test
print("3. ENCRYPTION/DECRYPTION FUNCTIONALITY TEST")
print("-" * 80)
test_cases = [
    "Test Framework Name",
    "user@example.com",
    "123-45-6789",
    "Acme Corporation Inc.",
]

all_passed = True
for test_text in test_cases:
    try:
        encrypted = encrypt_data(test_text)
        if not encrypted:
            print(f"   ❌ Encryption returned None for: '{test_text}'")
            all_passed = False
            continue
        
        if not is_encrypted_data(encrypted):
            print(f"   ❌ Encrypted data doesn't appear encrypted: '{test_text}'")
            all_passed = False
            continue
        
        decrypted = decrypt_data(encrypted)
        if decrypted != test_text:
            print(f"   ❌ Decryption failed for: '{test_text}'")
            print(f"      Expected: '{test_text}'")
            print(f"      Got: '{decrypted}'")
            all_passed = False
            continue
        
        print(f"   ✅ '{test_text}' → encrypted → decrypted correctly")
    except Exception as e:
        print(f"   ❌ Error testing '{test_text}': {str(e)}")
        all_passed = False

if all_passed:
    print()
    print("   ✅ All encryption/decryption tests PASSED")
else:
    print()
    print("   ❌ Some encryption/decryption tests FAILED")
    print("   Check the errors above for details")

print()

# Check 4: Model Encryption Configuration
print("4. MODEL ENCRYPTION CONFIGURATION")
print("-" * 80)
from tprm_backend.utils.encryption_config import (
    get_all_encrypted_fields,
    get_all_models_with_encryption
)

all_encrypted_fields = get_all_encrypted_fields()
models_with_encryption = get_all_configured_models()

print(f"   ✅ Found {len(models_with_encryption)} models with encryption configured")
print(f"   ✅ Total encrypted fields: {sum(len(fields) for fields in all_encrypted_fields.values())}")

# Check a few key models
key_models = ['User', 'Vendor', 'VendorContact', 'RFP', 'Contract', 'Vendors']
print()
print("   Key models encryption status:")
for model_name in key_models:
    if model_name in all_encrypted_fields:
        fields = all_encrypted_fields[model_name]
        print(f"   ✅ {model_name}: {len(fields)} fields encrypted ({', '.join(fields[:3])}{'...' if len(fields) > 3 else ''})")
    else:
        print(f"   ❌ {model_name}: NOT CONFIGURED for encryption")

print()

# Check 5: Model Mixin Usage
print("5. MODEL MIXIN USAGE")
print("-" * 80)
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin

# Check key models
test_models = [
    ('users.models', 'User'),
    ('vendors.models', 'VendorCategory'),
    ('rfp.models', 'RFP'),
    ('contracts.models', 'Vendor'),
    ('apps.vendor_core.models', 'Vendors'),
    ('apps.vendor_core.models', 'VendorBaseModel'),
]

print("   Checking if models have TPRMEncryptedFieldsMixin:")
for module_path, model_name in test_models:
    try:
        module = __import__(module_path, fromlist=[model_name])
        model_class = getattr(module, model_name)
        
        # Check if model has mixin
        if issubclass(model_class, TPRMEncryptedFieldsMixin):
            print(f"   ✅ {module_path}.{model_name}: Has TPRMEncryptedFieldsMixin")
        else:
            print(f"   ❌ {module_path}.{model_name}: MISSING TPRMEncryptedFieldsMixin")
    except ImportError as e:
        print(f"   ⚠️  {module_path}.{model_name}: Could not import ({str(e)})")
    except AttributeError as e:
        print(f"   ⚠️  {module_path}.{model_name}: Model not found ({str(e)})")
    except Exception as e:
        print(f"   ⚠️  {module_path}.{model_name}: Error checking ({str(e)})")

print()

# Check 6: Serializer Usage
print("6. SERIALIZER DECRYPTION")
print("-" * 80)
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer

# Check key serializers
test_serializers = [
    ('users.serializers', 'UserSerializer'),
    ('rfp.serializers', 'RFPSerializer'),
    ('contracts.serializers', 'VendorContractSerializer'),
]

print("   Checking if serializers use AutoDecryptingModelSerializer:")
for module_path, serializer_name in test_serializers:
    try:
        module = __import__(module_path, fromlist=[serializer_name])
        serializer_class = getattr(module, serializer_name)
        
        if issubclass(serializer_class, AutoDecryptingModelSerializer):
            print(f"   ✅ {module_path}.{serializer_name}: Uses AutoDecryptingModelSerializer")
        else:
            print(f"   ❌ {module_path}.{serializer_name}: NOT using AutoDecryptingModelSerializer")
    except ImportError as e:
        print(f"   ⚠️  {module_path}.{serializer_name}: Could not import ({str(e)})")
    except AttributeError as e:
        print(f"   ⚠️  {module_path}.{serializer_name}: Serializer not found ({str(e)})")
    except Exception as e:
        print(f"   ⚠️  {module_path}.{serializer_name}: Error checking ({str(e)})")

print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)

if env_key or settings_key:
    print("✅ Encryption key is configured")
else:
    print("❌ Encryption key is NOT configured - encryption will fail")

if all_passed:
    print("✅ Encryption/decryption functionality is working")
else:
    print("❌ Encryption/decryption has issues - check errors above")

print()
print("If encryption is not working:")
print("1. Ensure GRC_ENCRYPTION_KEY is set in environment or Django settings")
print("2. Verify all models inherit from TPRMEncryptedFieldsMixin or BaseModel")
print("3. Verify all serializers inherit from AutoDecryptingModelSerializer")
print("4. Check that fields are configured in encryption_config.py")
print("5. Restart Django server after making changes")
print()

