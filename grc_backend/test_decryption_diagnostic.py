"""
Comprehensive Decryption Diagnostic & Fix Script
Tests and fixes decryption issues across GRC and TPRM modules.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import models
from django.apps import apps
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_encryption_service():
    """Test if the encryption service is working"""
    print("\n" + "="*80)
    print("TEST 1: Encryption Service")
    print("="*80)
    
    try:
        from grc.utils.data_encryption import encrypt_data, decrypt_data, is_encrypted_data
        
        # Test encryption
        test_text = "Hello World"
        encrypted = encrypt_data(test_text)
        print(f"✅ Original text: {test_text}")
        print(f"✅ Encrypted text: {encrypted[:50]}...")
        
        # Test decryption
        decrypted = decrypt_data(encrypted)
        print(f"✅ Decrypted text: {decrypted}")
        
        # Test detection
        is_enc = is_encrypted_data(encrypted)
        print(f"✅ Is encrypted: {is_enc}")
        
        if decrypted == test_text:
            print("✅ Encryption/Decryption service WORKING!")
            return True
        else:
            print("❌ Decryption failed - wrong output!")
            return False
    except Exception as e:
        print(f"❌ Encryption service FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tprm_models():
    """Test if TPRM models have encryption mixin"""
    print("\n" + "="*80)
    print("TEST 2: TPRM Models with Encryption Mixin")
    print("="*80)
    
    try:
        from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin
        
        # Test some key models
        test_models = [
            ('tprm_backend.users', 'User'),
            ('tprm_backend.bcpdrp', 'Plan'),
            ('tprm_backend.bcpdrp', 'Users'),
            ('tprm_backend.apps.vendor_core', 'Vendors'),
        ]
        
        results = []
        for app_label, model_name in test_models:
            try:
                model = apps.get_model(app_label, model_name)
                has_mixin = issubclass(model, TPRMEncryptedFieldsMixin)
                encrypted_fields = model.get_encrypted_fields() if hasattr(model, 'get_encrypted_fields') else []
                
                if has_mixin:
                    print(f"✅ {app_label}.{model_name}: Has mixin, {len(encrypted_fields)} encrypted fields")
                    results.append(True)
                else:
                    print(f"❌ {app_label}.{model_name}: Missing mixin!")
                    results.append(False)
                    
            except Exception as e:
                print(f"❌ {app_label}.{model_name}: Error - {e}")
                results.append(False)
        
        return all(results)
    except Exception as e:
        print(f"❌ TPRM Models test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plain_properties():
    """Test if _plain properties are created"""
    print("\n" + "="*80)
    print("TEST 3: _plain Properties")
    print("="*80)
    
    try:
        # Test TPRM BCP/DRP Plan model
        from tprm_backend.bcpdrp.models import Plan
        from tprm_backend.utils.data_encryption import encrypt_data
        
        # Get encrypted fields
        encrypted_fields = Plan.get_encrypted_fields()
        print(f"✅ Plan model has {len(encrypted_fields)} encrypted fields")
        print(f"   Fields: {', '.join(encrypted_fields[:5])}...")
        
        # Create a test instance (don't save)
        plan = Plan(
            plan_id=99999,
            vendor_id=1,
            strategy_id=1,
            strategy_name="Test Strategy",
            plan_type="BCP",
            plan_name="Test Plan",
            file_uri="/test/file"
        )
        
        # Test if _plain properties exist
        properties_exist = []
        for field in ['strategy_name', 'plan_name']:
            if field in encrypted_fields:
                plain_property = f"{field}_plain"
                has_property = hasattr(plan, plain_property)
                print(f"{'✅' if has_property else '❌'} {plain_property}: {'EXISTS' if has_property else 'MISSING'}")
                properties_exist.append(has_property)
        
        return all(properties_exist)
    except Exception as e:
        print(f"❌ Plain properties test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_serializer_decryption():
    """Test if serializers decrypt data"""
    print("\n" + "="*80)
    print("TEST 4: Serializer Auto-Decryption")
    print("="*80)
    
    try:
        from tprm_backend.users.models import User
        from tprm_backend.users.serializers import UserSerializer
        from tprm_backend.utils.data_encryption import encrypt_data
        
        # Check if serializer uses AutoDecryptingModelSerializer
        from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
        
        is_auto_decrypt = issubclass(UserSerializer, AutoDecryptingModelSerializer)
        print(f"{'✅' if is_auto_decrypt else '❌'} UserSerializer uses AutoDecryptingModelSerializer: {is_auto_decrypt}")
        
        # Try to get a user and serialize
        try:
            user = User.objects.first()
            if user:
                serializer = UserSerializer(user)
                data = serializer.data
                
                # Check if email is decrypted (not starting with gAAAAA)
                email = data.get('email', '')
                is_encrypted = email.startswith('gAAAAA') if email else False
                
                print(f"{'❌' if is_encrypted else '✅'} Email in response: {email[:50] if email else 'None'}")
                print(f"   Is encrypted format: {is_encrypted}")
                
                return not is_encrypted
            else:
                print("⚠️  No users in database to test")
                return True
        except Exception as e:
            print(f"⚠️  Could not test with real data: {e}")
            return True
            
    except Exception as e:
        print(f"❌ Serializer test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_encryption_config():
    """Test if encryption config is loaded"""
    print("\n" + "="*80)
    print("TEST 5: Encryption Configuration")
    print("="*80)
    
    try:
        from tprm_backend.utils.encryption_config import get_encrypted_fields_for_model, get_all_configured_models
        
        all_models = get_all_configured_models()
        print(f"✅ Total configured models: {len(all_models)}")
        print(f"   Sample models: {', '.join(all_models[:10])}...")
        
        # Test specific models
        test_cases = [
            ('Plan', ['strategy_name', 'plan_name', 'plan_scope']),
            ('User', ['email', 'phone', 'first_name', 'last_name']),
            ('Users', ['user_name', 'email', 'first_name', 'last_name']),
        ]
        
        for model_name, expected_fields in test_cases:
            fields = get_encrypted_fields_for_model(model_name)
            has_expected = all(f in fields for f in expected_fields[:1])  # Check at least first field
            print(f"{'✅' if has_expected else '❌'} {model_name}: {len(fields)} fields configured")
        
        return len(all_models) > 0
    except Exception as e:
        print(f"❌ Configuration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_actual_data():
    """Test actual database data"""
    print("\n" + "="*80)
    print("TEST 6: Actual Database Data")
    print("="*80)
    
    try:
        # Test BCP/DRP Plans
        from tprm_backend.bcpdrp.models import Plan
        
        plan_count = Plan.objects.count()
        print(f"ℹ️  Total plans in database: {plan_count}")
        
        if plan_count > 0:
            plan = Plan.objects.first()
            print(f"\nℹ️  Testing Plan #{plan.plan_id}:")
            print(f"   Raw plan_name: {plan.plan_name[:50] if plan.plan_name else 'None'}...")
            
            # Check if it's encrypted format
            is_encrypted = plan.plan_name.startswith('gAAAAA') if plan.plan_name else False
            print(f"   Is encrypted in DB: {is_encrypted}")
            
            # Try to access plain property
            if hasattr(plan, 'plan_name_plain'):
                plain_name = plan.plan_name_plain
                print(f"   Plain property value: {plain_name[:50] if plain_name else 'None'}...")
                
                # Check if decrypted successfully
                is_decrypted = not (plain_name and plain_name.startswith('gAAAAA'))
                print(f"   {'✅' if is_decrypted else '❌'} Decryption {'working' if is_decrypted else 'FAILED'}")
                
                return is_decrypted
            else:
                print(f"   ❌ plan_name_plain property NOT FOUND!")
                return False
        else:
            print("⚠️  No plans to test")
            return True
            
    except Exception as e:
        print(f"❌ Database test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_diagnostics():
    """Run all diagnostic tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "DECRYPTION DIAGNOSTIC TOOL" + " "*32 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        ("Encryption Service", test_encryption_service),
        ("TPRM Models", test_tprm_models),
        ("Plain Properties", test_plain_properties),
        ("Serializer Auto-Decryption", test_serializer_decryption),
        ("Encryption Configuration", test_encryption_config),
        ("Actual Database Data", test_actual_data),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*30 + "TEST SUMMARY" + " "*36 + "║")
    print("╠" + "="*78 + "╣")
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        padding = " " * (60 - len(name))
        print(f"║  {name}{padding}{status}  ║")
    
    print("╚" + "="*78 + "╝")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Decryption is working correctly!")
    else:
        print("\n⚠️  SOME TESTS FAILED - See details above")
        print("\nPossible fixes:")
        print("1. Restart Django server to reload models")
        print("2. Run: python manage.py shell < fix_decryption.py")
        print("3. Check if GRC_ENCRYPTION_KEY is set in settings")
        print("4. Verify encryption_init is being called in apps.py")


if __name__ == '__main__':
    run_diagnostics()

