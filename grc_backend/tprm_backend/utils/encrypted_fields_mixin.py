"""
TPRM Encrypted Fields Mixin
Reuses GRC EncryptedFieldsMixin for consistency.
"""

import sys
import os

# Add GRC module to Python path for importing
grc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'grc')
if grc_path not in sys.path:
    sys.path.insert(0, grc_path)

# Import from GRC
from grc.utils.encrypted_fields_mixin import (
    EncryptedFieldsMixin,
    add_plain_properties_to_model
)

# Import TPRM-specific encryption config
from .encryption_config import get_encrypted_fields_for_model

# Override get_encrypted_fields to use TPRM config
class TPRMEncryptedFieldsMixin(EncryptedFieldsMixin):
    """
    TPRM-specific encrypted fields mixin that uses TPRM encryption configuration.
    """
    
    @classmethod
    def get_encrypted_fields(cls):
        """
        Get list of field names that should be encrypted for this TPRM model.
        
        Returns:
            List of field names to encrypt
        """
        return get_encrypted_fields_for_model(cls.__name__)


# Re-export
__all__ = [
    'TPRMEncryptedFieldsMixin',
    'EncryptedFieldsMixin',  # Original for compatibility
    'add_plain_properties_to_model'
]

