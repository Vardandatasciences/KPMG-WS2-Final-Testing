"""
Fix Decryption Properties Script
Explicitly adds _plain properties to all TPRM models with encrypted fields.
Run this after Django is fully loaded to ensure decryption works.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    django.setup()
except:
    print("⚠️  Could not setup Django, trying to continue...")

import logging
from django.apps import apps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_plain_properties_to_model(model_class, field_names):
    """
    Dynamically add _plain properties to a model for decryption.
    
    Args:
        model_class: Django model class
        field_names: List of field names that should have _plain properties
    """
    from tprm_backend.utils.data_encryption import decrypt_data
    
    for field_name in field_names:
        property_name = f"{field_name}_plain"
        
        # Skip if property already exists
        if hasattr(model_class, property_name):
            continue
        
        # Create property getter function
        def make_property(fname):
            """Factory function to create property with correct closure"""
            def prop_getter(self):
                """Get decrypted value for field"""
                try:
                    # Get the encrypted value
                    field_value = getattr(self, fname, None)
                    
                    if field_value is None or field_value == '':
                        return None
                    
                    # Convert to string if needed
                    if not isinstance(field_value, str):
                        return field_value
                    
                    # Try to decrypt
                    decrypted = decrypt_data(field_value)
                    return decrypted
                    
                except Exception as e:
                    logger.warning(f"Error decrypting {fname} on {self.__class__.__name__}: {e}")
                    # Return original value if decryption fails
                    return getattr(self, fname, None)
            
            return property(prop_getter)
        
        # Add property to class
        setattr(model_class, property_name, make_property(field_name))
        logger.info(f"✅ Added {property_name} to {model_class.__name__}")


def fix_all_models():
    """Add _plain properties to all TPRM models with encryption"""
    
    print("\n" + "="*80)
    print("FIXING DECRYPTION PROPERTIES FOR ALL TPRM MODELS")
    print("="*80 + "\n")
    
    try:
        from tprm_backend.utils.encryption_config import get_all_encrypted_fields
        
        # Get all models with encryption configured
        all_encrypted = get_all_encrypted_fields()
        
        print(f"Found {len(all_encrypted)} models with encryption configured\n")
        
        fixed_count = 0
        failed_count = 0
        
        for model_name, field_names in all_encrypted.items():
            try:
                # Try to find the model
                model_class = None
                
                # Search through all apps
                for app_config in apps.get_app_configs():
                    try:
                        model_class = app_config.get_model(model_name)
                        break
                    except LookupError:
                        continue
                
                if model_class:
                    print(f"Processing {model_name}...")
                    add_plain_properties_to_model(model_class, field_names)
                    fixed_count += 1
                else:
                    print(f"⚠️  Model {model_name} not found in any app")
                    failed_count += 1
                    
            except Exception as e:
                print(f"❌ Error processing {model_name}: {e}")
                failed_count += 1
        
        print("\n" + "="*80)
        print(f"SUMMARY: Fixed {fixed_count} models, {failed_count} failed/not found")
        print("="*80 + "\n")
        
        if fixed_count > 0:
            print("✅ Decryption properties have been added!")
            print("   Restart your Django server to use the updated models.")
        else:
            print("⚠️  No models were fixed. Check if Django is properly configured.")
        
        return fixed_count > 0
        
    except Exception as e:
        print(f"\n❌ FAILED to fix models: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = fix_all_models()
    sys.exit(0 if success else 1)

