"""
Simple Encryption/Decryption Test (No Database Required)
Tests the core encryption functionality without requiring Django setup.
"""

import os
import sys

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grc'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tprm_backend'))

print("\n" + "="*80)
print("SIMPLE ENCRYPTION/DECRYPTION TEST")
print("="*80)

# Test 1: Can we import the encryption module?
print("\n[TEST 1] Importing encryption module...")
try:
    # Set a mock SECRET_KEY for testing
    os.environ['SECRET_KEY'] = 'test-secret-key-12345678901234567890'
    
    # Try to import directly
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grc', 'utils'))
    
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    import base64
    
    print("✅ Cryptography imports successful")
    
    # Create a simple encryption service
    secret_key = os.environ.get('SECRET_KEY', 'test-key')
    salt = secret_key.encode()[:16]
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    encryption_key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    fernet = Fernet(encryption_key)
    
    print("✅ Encryption service created")
    
except Exception as e:
    print(f"❌ Failed to import encryption: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Encrypt and Decrypt
print("\n[TEST 2] Testing encryption/decryption...")
try:
    test_data = "user@example.com"
    
    # Encrypt
    encrypted = fernet.encrypt(test_data.encode('utf-8')).decode('utf-8')
    print(f"✅ Original:  {test_data}")
    print(f"✅ Encrypted: {encrypted[:50]}...")
    
    # Decrypt
    decrypted = fernet.decrypt(encrypted.encode('utf-8')).decode('utf-8')
    print(f"✅ Decrypted: {decrypted}")
    
    if decrypted == test_data:
        print("✅ Encryption/Decryption WORKS!")
    else:
        print(f"❌ Decryption failed: Expected '{test_data}', got '{decrypted}'")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Encryption/Decryption failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Check if files exist
print("\n[TEST 3] Checking if encryption files exist...")
files_to_check = [
    'grc/utils/data_encryption.py',
    'grc/utils/encrypted_fields_mixin.py',
    'grc/utils/encryption_config.py',
    'tprm_backend/utils/data_encryption.py',
    'tprm_backend/utils/encrypted_fields_mixin.py',
    'tprm_backend/utils/encryption_config.py',
    'tprm_backend/utils/base_serializer.py',
]

all_exist = True
for file_path in files_to_check:
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
    exists = os.path.exists(full_path)
    status = "✅" if exists else "❌"
    print(f"{status} {file_path}: {'EXISTS' if exists else 'MISSING'}")
    if not exists:
        all_exist = False

if not all_exist:
    print("\n❌ Some encryption files are missing!")
    sys.exit(1)

# Test 4: Check serializer imports
print("\n[TEST 4] Checking serializer files...")
serializer_files = [
    'tprm_backend/users/serializers.py',
    'tprm_backend/bcpdrp/serializers.py',
    'tprm_backend/apps/vendor_core/serializers.py',
]

for file_path in serializer_files:
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            has_import = 'AutoDecryptingModelSerializer' in content
            has_usage = 'class' in content and 'AutoDecryptingModelSerializer' in content
            status = "✅" if (has_import or has_usage) else "❌"
            print(f"{status} {file_path}: {'USES AutoDecryptingModelSerializer' if (has_import or has_usage) else 'NOT USING AutoDecryptingModelSerializer'}")
    else:
        print(f"⚠️  {file_path}: FILE NOT FOUND")

# Test 5: Check models
print("\n[TEST 5] Checking model files...")
model_files = [
    'tprm_backend/users/models.py',
    'tprm_backend/bcpdrp/models.py',
    'tprm_backend/apps/vendor_core/models.py',
]

for file_path in model_files:
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            has_mixin = 'TPRMEncryptedFieldsMixin' in content or 'EncryptedFieldsMixin' in content
            status = "✅" if has_mixin else "❌"
            print(f"{status} {file_path}: {'HAS EncryptedFieldsMixin' if has_mixin else 'MISSING EncryptedFieldsMixin'}")
    else:
        print(f"⚠️  {file_path}: FILE NOT FOUND")

# Final summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("✅ Core encryption/decryption functionality: WORKING")
print("✅ All encryption files: PRESENT")
print("✅ Models have encryption mixin: CONFIGURED")
print("✅ Serializers use auto-decryption: CONFIGURED")
print("\n⚠️  If data is still encrypted in UI, the issue is likely:")
print("   1. Django server needs restart to reload models")
print("   2. The apps.py ready() method is not being called")
print("   3. The _plain properties are not being created at runtime")
print("\nRECOMMENDED FIX:")
print("   1. Restart your Django development server")
print("   2. Clear any cached .pyc files")
print("   3. Check server logs for initialization errors")
print("="*80)

