"""
TPRM Data Encryption Utility
Reuses GRC encryption service for consistency across modules.
"""

# Import GRC encryption utilities
import sys
import os

# Add GRC module to Python path for importing
grc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'grc')
if grc_path not in sys.path:
    sys.path.insert(0, grc_path)

# Import encryption functions from GRC
from grc.utils.data_encryption import (
    DataEncryptionService,
    decrypt_blob_with_key,
    decrypt_data,
    encrypt_blob_with_key,
    encrypt_data,
    get_encryption_service,
    is_encrypted_data,
)

# Re-export for TPRM module usage
__all__ = [
    'DataEncryptionService',
    'get_encryption_service',
    'encrypt_data',
    'decrypt_data',
    'is_encrypted_data',
    'encrypt_blob_with_key',
    'decrypt_blob_with_key',
]

