"""
Encrypted Fields Mixin for Django Models
Automatically encrypts and decrypts specified fields.

Usage:
    from .encrypted_fields_mixin import EncryptedFieldsMixin
    
    class MyModel(EncryptedFieldsMixin, models.Model):
        # Model fields...
        pass

The mixin will automatically:
1. Encrypt configured fields before saving to database
2. Provide decrypted properties for accessing plain text values
3. Handle backward compatibility with plain text data
"""

import logging
from django.db import models
from django.core.exceptions import FieldError
from .data_encryption import encrypt_data, decrypt_data, is_encrypted_data
from .encryption_config import get_encrypted_fields_for_model, get_all_encryptable_fields

logger = logging.getLogger(__name__)


class EncryptedFieldsMixin:
    """
    Mixin to automatically encrypt/decrypt specified fields.
    
    Fields to encrypt are configured in encryption_config.py
    
    The mixin:
    - Encrypts fields on save() if not already encrypted
    - Provides _plain properties for decrypted access (e.g., user.email_plain)
    - Handles backward compatibility with existing plain text data
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with decrypted flag to prevent infinite recursion"""
        super().__init__(*args, **kwargs)
        self._decryption_in_progress = False
        self._encrypted_fields_cache = None
    
    @classmethod
    def get_encrypted_fields(cls):
        """
        Get list of field names that should be encrypted for this model.
        
        Returns:
            List of field names to encrypt
        """
        return get_encrypted_fields_for_model(cls.__name__)
    
    def save(self, *args, **kwargs):
        """
        Override save to encrypt sensitive fields before storing.
        Handles both new data and updates, with backward compatibility.
        """
        # CRITICAL: If update_fields contains ONLY password fields, skip ALL encryption
        # This prevents interference when updating passwords
        update_fields = kwargs.get('update_fields')
        if update_fields:
            password_field_names_check = [
                'password', 'Password', 'user_password', 'userPassword',
                'OldPassword', 'NewPassword', 'old_password', 'new_password'
            ]
            # If all update_fields are password fields, skip encryption entirely
            if all(field in password_field_names_check for field in update_fields):
                logger.info(f"Skipping encryption for password-only update on {self.__class__.__name__}")
                return super().save(*args, **kwargs)
        
        # Get list of fields to encrypt for this model
        encrypted_fields = self.get_encrypted_fields()
        
        # CRITICAL: Never encrypt password fields - they must be hashed, not encrypted!
        # Passwords should use Django's password hashing (PBKDF2, bcrypt, etc.), not encryption
        password_field_names = [
            'password', 'Password', 'user_password', 'userPassword',
            'OldPassword', 'NewPassword',  # PasswordLog fields - already hashed
            'old_password', 'new_password'  # Alternative naming conventions
        ]
        
        if encrypted_fields:
            # Encrypt each field if it has a value and isn't already encrypted
            for field_name in encrypted_fields:
                # Skip password fields - they should be hashed, not encrypted
                if field_name.lower() in [p.lower() for p in password_field_names]:
                    logger.warning(f"Skipping encryption of password field '{field_name}' for {self.__class__.__name__}. Passwords must be hashed, not encrypted!")
                    continue
                
                if hasattr(self, field_name):
                    try:
                        field_value = getattr(self, field_name)
                        
                        # Skip None, empty strings, and already encrypted data
                        if field_value is None or field_value == '':
                            continue
                        
                        # Convert non-string values to string for encryption
                        if not isinstance(field_value, str):
                            # Handle JSON fields - encrypt the JSON string
                            if isinstance(field_value, (dict, list)):
                                import json
                                field_value = json.dumps(field_value)
                            else:
                                field_value = str(field_value)
                        
                        # Check if already encrypted
                        if not is_encrypted_data(field_value):
                            # Encrypt the value
                            encrypted_value = encrypt_data(field_value)
                            if encrypted_value:
                                setattr(self, field_name, encrypted_value)
                                logger.debug(f"Encrypted field {field_name} for {self.__class__.__name__} #{getattr(self, 'pk', 'new')}")
                    
                    except Exception as e:
                        logger.error(f"Error encrypting field {field_name} for {self.__class__.__name__}: {str(e)}")
                        # Continue with other fields even if one fails
        
        # Call parent save
        super().save(*args, **kwargs)
    
    def _get_decrypted_value(self, field_name):
        """
        Get decrypted value for a field.
        
        Args:
            field_name: Name of the field to decrypt
            
        Returns:
            Decrypted plain text value, or original value if decryption fails
        """
        if self._decryption_in_progress:
            # Prevent infinite recursion
            return getattr(self, field_name, None)
        
        try:
            self._decryption_in_progress = True
            field_value = getattr(self, field_name, None)
            
            if field_value is None:
                return None
            
            # Convert to string if needed
            if not isinstance(field_value, str):
                return field_value
            
            # Try to decrypt
            decrypted = decrypt_data(field_value)
            return decrypted
        
        except Exception as e:
            logger.warning(f"Error decrypting field {field_name} for {self.__class__.__name__}: {str(e)}")
            # Return original value if decryption fails (backward compatibility)
            return getattr(self, field_name, None)
        
        finally:
            self._decryption_in_progress = False
    
    def get_plain_fields_dict(self):
        """
        Get dictionary of all encrypted fields with their decrypted values.
        
        Returns:
            Dictionary mapping field names to decrypted values
        """
        encrypted_fields = self.get_encrypted_fields()
        plain_dict = {}
        
        for field_name in encrypted_fields:
            if hasattr(self, field_name):
                plain_dict[field_name] = self._get_decrypted_value(field_name)
        
        return plain_dict
    
    def __getattribute__(self, name):
        """
        Intercept attribute access to provide _plain properties.
        
        Example:
            user.email  # Returns encrypted value
            user.email_plain  # Returns decrypted value
        """
        # Check if accessing a _plain property
        if name.endswith('_plain') and not name.startswith('_'):
            # Get the base field name
            base_field = name[:-6]  # Remove '_plain' suffix
            
            # Get encrypted fields for this model
            encrypted_fields = None
            try:
                # Try to get from class (avoid recursion)
                if hasattr(self, '__class__'):
                    encrypted_fields = self.__class__.get_encrypted_fields()
            except:
                pass
            
            # If this field should be encrypted, return decrypted value
            if encrypted_fields and base_field in encrypted_fields:
                # Use _get_decrypted_value to get decrypted version
                try:
                    return object.__getattribute__(self, '_get_decrypted_value')(base_field)
                except:
                    # Fallback to normal attribute access
                    return object.__getattribute__(self, name)
        
        # Normal attribute access
        return object.__getattribute__(self, name)


def add_plain_properties_to_model(model_class):
    """
    Dynamically add _plain properties to a model class.
    
    This is an alternative to using __getattribute__ that creates
    explicit properties for each encrypted field.
    
    Args:
        model_class: Django model class to add properties to
    """
    encrypted_fields = get_encrypted_fields_for_model(model_class.__name__)
    
    for field_name in encrypted_fields:
        # Create property name
        property_name = f"{field_name}_plain"
        
        # Skip if property already exists
        if hasattr(model_class, property_name):
            continue
        
        # Create property getter
        def make_property(fname):
            def prop_getter(self):
                if hasattr(self, '_get_decrypted_value'):
                    return self._get_decrypted_value(fname)
                else:
                    # Fallback: decrypt directly
                    field_value = getattr(self, fname, None)
                    if field_value:
                        return decrypt_data(field_value)
                    return None
            return property(prop_getter)
        
        # Add property to class
        setattr(model_class, property_name, make_property(field_name))
        logger.debug(f"Added {property_name} property to {model_class.__name__}")

