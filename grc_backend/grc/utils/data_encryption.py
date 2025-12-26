"""
Data Encryption/Decryption Utility for GRC Models
Provides encryption and decryption functions for sensitive fields that need to be retrieved later.

IMPORTANT:
- Encryption = Two-way (can encrypt and decrypt to see plain text later)
- Hashing = One-way (cannot reverse, only verify)
- Use ENCRYPTION for: Email, Phone, Address, License Key (data you need to read later)
- Use HASHING for: Passwords, OTPs (data you only need to verify, never read)
"""

import logging
from typing import Optional
from django.conf import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os

logger = logging.getLogger(__name__)


class DataEncryptionService:
    """
    Service for encrypting and decrypting sensitive data in GRC models.
    
    This allows you to:
    1. Store encrypted data in the database
    2. Retrieve and decrypt it later to see the plain text
    
    Example:
        # Encrypt
        encrypted_email = encryption_service.encrypt("user@example.com")
        user.Email = encrypted_email
        user.save()
        
        # Decrypt later
        plain_email = encryption_service.decrypt(user.Email)
        print(plain_email)  # Output: user@example.com
    """
    
    def __init__(self):
        """Initialize encryption service with key from settings"""
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_encryption_key(self) -> bytes:
        """
        Get encryption key from settings or generate one.
        
        For production, set GRC_ENCRYPTION_KEY in your environment variables.
        The key should be a Fernet key (base64-encoded 32-byte key).
        
        To generate a key:
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            print(key.decode())  # Save this to your .env file
        """
        # First, try to get from settings
        key = getattr(settings, 'GRC_ENCRYPTION_KEY', None)
        
        if not key:
            # Try environment variable
            key = os.environ.get('GRC_ENCRYPTION_KEY', None)
        
        if not key:
            # Generate a key from Django SECRET_KEY (for development only)
            # WARNING: In production, use a dedicated encryption key!
            logger.warning("No GRC_ENCRYPTION_KEY found. Generating from SECRET_KEY (NOT RECOMMENDED for production)")
            secret_key = settings.SECRET_KEY
            salt = secret_key.encode()[:16]  # Use first 16 bytes as salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        else:
            # Convert string key to bytes if needed
            if isinstance(key, str):
                key = key.encode()
        
        return key
    
    def encrypt(self, plain_text: Optional[str]) -> Optional[str]:
        """
        Encrypt plain text data.
        
        Args:
            plain_text: The plain text string to encrypt (can be None)
            
        Returns:
            Encrypted string (base64-encoded), or None if input was None
            
        Example:
            encrypted = encryption_service.encrypt("user@example.com")
            # Returns: "gAAAAABh..." (encrypted string)
        """
        if plain_text is None:
            return None
        
        if not isinstance(plain_text, str):
            # Convert to string if not already
            plain_text = str(plain_text)
        
        try:
            # Encrypt the data
            encrypted_bytes = self.fernet.encrypt(plain_text.encode('utf-8'))
            # Return as base64-encoded string for database storage
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            # In case of error, return original text (fail-open for backward compatibility)
            # In production, you might want to raise the exception instead
            return plain_text
    
    def decrypt(self, encrypted_text: Optional[str]) -> Optional[str]:
        """
        Decrypt encrypted data to retrieve plain text.
        
        Args:
            encrypted_text: The encrypted string to decrypt (can be None)
            
        Returns:
            Plain text string, or None if input was None
            
        Example:
            plain = encryption_service.decrypt(user.Email)
            # Returns: "user@example.com" (original plain text)
        """
        if encrypted_text is None:
            return None
        
        if not isinstance(encrypted_text, str):
            # Convert to string if not already
            encrypted_text = str(encrypted_text)
        
        try:
            # Decrypt the data
            decrypted_bytes = self.fernet.decrypt(encrypted_text.encode('utf-8'))
            # Return as plain text string
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.warning(f"Decryption failed (data may be plain text): {str(e)}")
            # If decryption fails, assume it's already plain text (for backward compatibility)
            # This allows gradual migration from plain text to encrypted
            return encrypted_text
    
    def is_encrypted(self, text: Optional[str]) -> bool:
        """
        Check if a string appears to be encrypted.
        This is a best-effort check, not 100% reliable.
        
        Args:
            text: The string to check
            
        Returns:
            True if text appears encrypted, False otherwise
        """
        if not text:
            return False
        
        try:
            # Try to decrypt - if it works, it's encrypted
            self.fernet.decrypt(text.encode('utf-8'))
            return True
        except:
            # If decryption fails, assume it's plain text
            return False


# Global instance for easy access
_encryption_service = None

def get_encryption_service() -> DataEncryptionService:
    """Get or create the global encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = DataEncryptionService()
    return _encryption_service


# Convenience functions for direct use
def encrypt_data(plain_text: Optional[str]) -> Optional[str]:
    """
    Encrypt plain text data (convenience function).
    
    Example:
        encrypted_email = encrypt_data("user@example.com")
    """
    return get_encryption_service().encrypt(plain_text)


def decrypt_data(encrypted_text: Optional[str]) -> Optional[str]:
    """
    Decrypt encrypted data to retrieve plain text (convenience function).
    
    Example:
        plain_email = decrypt_data(user.Email)
        print(plain_email)  # Shows the original email address
    """
    return get_encryption_service().decrypt(encrypted_text)


def is_encrypted_data(text: Optional[str]) -> bool:
    """Check if text appears to be encrypted (convenience function)"""
    return get_encryption_service().is_encrypted(text)

