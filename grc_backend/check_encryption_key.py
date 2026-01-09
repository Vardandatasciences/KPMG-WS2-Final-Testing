"""
Script to check which encryption key is being used by GRC
Run this to verify your GRC_ENCRYPTION_KEY is being loaded correctly
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings
from grc.utils.data_encryption import get_encryption_service
import base64

print("=" * 80)
print("GRC ENCRYPTION KEY CHECK")
print("=" * 80)
print()

# Check 1: Environment variable
env_key = os.environ.get('GRC_ENCRYPTION_KEY', None)
print(f"1. Environment Variable (GRC_ENCRYPTION_KEY):")
if env_key:
    print(f"   ✅ FOUND: {env_key[:20]}...{env_key[-10:] if len(env_key) > 30 else ''} (length: {len(env_key)})")
else:
    print(f"   ❌ NOT FOUND")
print()

# Check 2: Django settings
settings_key = getattr(settings, 'GRC_ENCRYPTION_KEY', None)
print(f"2. Django Settings (settings.GRC_ENCRYPTION_KEY):")
if settings_key:
    print(f"   ✅ FOUND: {settings_key[:20]}...{settings_key[-10:] if len(settings_key) > 30 else ''} (length: {len(settings_key)})")
else:
    print(f"   ❌ NOT FOUND")
print()

# Check 3: What key is actually being used
print(f"3. Key Actually Being Used by Encryption Service:")
encryption_service = get_encryption_service()
actual_key = encryption_service.encryption_key
actual_key_str = actual_key.decode() if isinstance(actual_key, bytes) else actual_key
print(f"   Key: {actual_key_str[:20]}...{actual_key_str[-10:] if len(actual_key_str) > 30 else ''} (length: {len(actual_key_str)})")
print()

# Check 4: Key source
print(f"4. Key Source:")
if env_key:
    print(f"   ✅ Using environment variable (GRC_ENCRYPTION_KEY)")
elif settings_key:
    print(f"   ✅ Using Django settings (settings.GRC_ENCRYPTION_KEY)")
else:
    print(f"   ⚠️  WARNING: No key found! Auto-generating from SECRET_KEY")
    print(f"   ⚠️  This means decryption will FAIL for data encrypted with a different key!")
    print(f"   ⚠️  Set GRC_ENCRYPTION_KEY in your environment or settings!")
print()

# Check 5: Test encryption/decryption
print(f"5. Testing Encryption/Decryption:")
test_text = "Test Framework Name"
try:
    encrypted = encryption_service.encrypt(test_text)
    decrypted = encryption_service.decrypt(encrypted)
    if decrypted == test_text:
        print(f"   ✅ Encryption/Decryption working correctly")
        print(f"   Encrypted: {encrypted[:30]}...")
    else:
        print(f"   ❌ Decryption failed - got '{decrypted}' instead of '{test_text}'")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
print()

# Check 6: Compare with TPRM key (if available)
print(f"6. TPRM Encryption Key (for comparison):")
try:
    tprm_key = os.environ.get('VENDOR_ENCRYPTION_KEY', None)
    if tprm_key:
        print(f"   TPRM Key: {tprm_key[:20]}...{tprm_key[-10:] if len(tprm_key) > 30 else ''}")
        if tprm_key == env_key:
            print(f"   ✅ GRC and TPRM keys MATCH")
        else:
            print(f"   ⚠️  GRC and TPRM keys are DIFFERENT")
    else:
        print(f"   TPRM key not found in environment")
except Exception as e:
    print(f"   Could not check TPRM key: {e}")
print()

print("=" * 80)
print("RECOMMENDATION:")
if env_key or settings_key:
    print("✅ Your encryption key is configured correctly")
    print("   If decryption still fails, the data might have been encrypted with a different key")
else:
    print("❌ CRITICAL: No GRC_ENCRYPTION_KEY found!")
    print("   The system is auto-generating a key from SECRET_KEY")
    print("   This will cause decryption to fail for existing encrypted data!")
    print()
    print("   SOLUTION:")
    print("   1. Generate a key: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
    print("   2. Set it in your .env file: GRC_ENCRYPTION_KEY=your-generated-key-here")
    print("   3. Restart your Django server")
print("=" * 80)


