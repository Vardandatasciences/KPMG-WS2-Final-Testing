"""
Auto-Decrypting Base Serializer for GRC Models

This serializer automatically decrypts encrypted fields when serializing model data.
All GRC serializers should inherit from AutoDecryptingModelSerializer instead of
serializers.ModelSerializer to ensure encrypted data is automatically decrypted
before being sent to the frontend.

Usage:
    from grc.utils.base_serializer import AutoDecryptingModelSerializer
    
    class MySerializer(AutoDecryptingModelSerializer):
        class Meta:
            model = MyModel
            fields = '__all__'
    
    # Encrypted fields will be automatically decrypted in the response!
"""

import logging
from rest_framework import serializers
from .encryption_config import get_encrypted_fields_for_model

logger = logging.getLogger(__name__)


class AutoDecryptingModelSerializer(serializers.ModelSerializer):
    """
    Base ModelSerializer that automatically decrypts encrypted fields.
    
    This serializer:
    1. Detects which fields are encrypted (from encryption_config.py)
    2. Returns decrypted values using _plain properties
    3. Handles null values and errors gracefully
    4. Works transparently - no changes needed to existing serializer code
    
    Benefits:
    - Automatic decryption for all encrypted fields
    - No need for manual SerializerMethodField declarations
    - Centralized decryption logic
    - Backward compatible with existing serializers
    - Safe error handling
    """
    
    def to_representation(self, instance):
        """
        Override to_representation to automatically decrypt encrypted fields.
        
        This method is called when converting a model instance to a dictionary
        for JSON serialization. We intercept it to replace encrypted field values
        with their decrypted counterparts.
        
        Args:
            instance: Model instance being serialized
            
        Returns:
            Dictionary with decrypted values for encrypted fields
        """
        # Get the normal representation from parent class
        ret = super().to_representation(instance)
        
        try:
            # Get encrypted fields for this model
            model_name = instance.__class__.__name__
            encrypted_fields = get_encrypted_fields_for_model(model_name)
            
            if not encrypted_fields:
                # No encrypted fields for this model, return as-is
                return ret
            
            # Replace encrypted values with decrypted ones
            for field_name in encrypted_fields:
                # Only process if field is in the serialized output
                if field_name in ret:
                    try:
                        # Get decrypted value using _plain property
                        plain_property = f"{field_name}_plain"
                        
                        # Try multiple decryption methods
                        decrypted_value = None
                        decryption_method = None
                        
                        # Method 1: Try _plain property
                        if hasattr(instance, plain_property):
                            try:
                                decrypted_value = getattr(instance, plain_property)
                                decryption_method = "_plain property"
                            except Exception as e:
                                logger.debug(f"_plain property failed for {field_name}: {e}")
                        
                        # Method 2: Try manual decryption if _plain failed or doesn't exist
                        if decrypted_value is None:
                            try:
                                from .data_encryption import decrypt_data, is_encrypted_data
                                
                                encrypted_value = getattr(instance, field_name, None)
                                if encrypted_value and isinstance(encrypted_value, str):
                                    # Only decrypt if it looks encrypted
                                    if is_encrypted_data(encrypted_value):
                                        decrypted_value = decrypt_data(encrypted_value)
                                        decryption_method = "manual decryption"
                                    else:
                                        # Already plain text
                                        decrypted_value = encrypted_value
                                        decryption_method = "already plain"
                            except Exception as e:
                                logger.debug(f"Manual decryption failed for {field_name}: {e}")
                        
                        # Update representation if we got a decrypted value
                        if decrypted_value is not None:
                            ret[field_name] = decrypted_value
                            logger.debug(
                                f"Decrypted '{field_name}' for {model_name} using {decryption_method}"
                            )
                    
                    except Exception as e:
                        # Log error but don't fail serialization
                        logger.warning(
                            f"Failed to decrypt field '{field_name}' for {model_name}: {str(e)}"
                        )
                        # Keep the original (possibly encrypted) value
                        pass
        
        except Exception as e:
            # If anything goes wrong with the entire decryption process,
            # log it but return the original representation
            logger.error(f"Error in auto-decryption for {instance.__class__.__name__}: {str(e)}")
        
        return ret
    
    def to_internal_value(self, data):
        """
        Override to_internal_value to handle incoming data.
        
        When data comes from the frontend (e.g., in POST/PUT requests),
        we receive it as plain text and let the model's save() method
        handle encryption automatically.
        
        Args:
            data: Dictionary of field values from request
            
        Returns:
            Validated data dictionary
        """
        # Parent class handles validation
        validated_data = super().to_internal_value(data)
        
        # No special handling needed - the model's EncryptedFieldsMixin
        # will automatically encrypt fields on save()
        
        return validated_data


# Convenience exports
__all__ = [
    'AutoDecryptingModelSerializer',
]


