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
        # Primary fernet (used for encryption)
        self.fernet = Fernet(self.encryption_key)
        # Additional fernets (used for decryption key-rotation / legacy data)
        self._all_fernets = self._build_all_fernets()
    
    def _get_candidate_keys(self) -> list:
        """
        Get a list of candidate encryption keys in priority order.

        Supports key-rotation by allowing multiple keys for decryption.
        The FIRST key is used for encryption; all keys are tried for decryption.
        """
        keys: list = []

        # 1) Explicit multi-key config (comma-separated)
        multi = getattr(settings, 'GRC_ENCRYPTION_KEYS', None) or os.environ.get('GRC_ENCRYPTION_KEYS')
        if multi:
            if isinstance(multi, str):
                for part in multi.split(','):
                    part = part.strip()
                    if part:
                        keys.append(part)
            elif isinstance(multi, (list, tuple)):
                keys.extend([k for k in multi if k])

        # 2) Single key (preferred)
        single = getattr(settings, 'GRC_ENCRYPTION_KEY', None) or os.environ.get('GRC_ENCRYPTION_KEY')
        if single:
            keys.append(single)

        # 3) Backward-compat keys used in parts of this repo / deployments
        for alt_name in ('TPRM_ENCRYPTION_KEY', 'DATA_ENCRYPTION_KEY', 'VENDOR_ENCRYPTION_KEY'):
            alt = getattr(settings, alt_name, None) or os.environ.get(alt_name)
            if alt:
                keys.append(alt)

        # De-dup while preserving order
        deduped = []
        seen = set()
        for k in keys:
            ks = k.decode() if isinstance(k, (bytes, bytearray)) else str(k)
            if ks not in seen:
                seen.add(ks)
                deduped.append(k)
        return deduped

    def _build_all_fernets(self) -> list:
        """Build Fernet instances for all candidate keys (primary first)."""
        fernets = []
        for key in self._get_candidate_keys():
            if isinstance(key, str):
                key = key.encode()
            try:
                fernets.append(Fernet(key))
            except Exception as e:
                logger.warning(f"Invalid encryption key ignored: {e}")

        # Ensure primary is first (self.encryption_key)
        try:
            primary = self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key
            primary_fernet = Fernet(primary)
            fernets = [primary_fernet] + [f for f in fernets if f._signing_key != primary_fernet._signing_key]
        except Exception:
            pass
        return fernets

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
        # Choose the first candidate key as the primary encryption key
        candidates = self._get_candidate_keys()
        key = candidates[0] if candidates else None
        
        # HARD REQUIREMENT: Do NOT silently fall back to a derived key.
        # If no key is configured, fail fast so we don't "change keys"
        # without you knowing and break decryption of existing data.
        if not key:
            raise RuntimeError(
                "GRC_ENCRYPTION_KEY is not configured. "
                "Set it in your environment or Django settings to match the key "
                "used for existing encrypted data. No fallback key will be generated."
            )
        
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
            # Try all keys (key rotation / legacy data)
            last_error = None
            for f in getattr(self, '_all_fernets', [self.fernet]):
                try:
                    # Support accidental double-encryption: decrypt up to 3 layers
                    current = encrypted_text
                    for _ in range(3):
                        decrypted_bytes = f.decrypt(current.encode('utf-8'))
                        current = decrypted_bytes.decode('utf-8')
                        # If the decrypted value no longer looks like a Fernet token, stop
                        if not self.is_encrypted(current):
                            break
                    return current
                except Exception as e:
                    last_error = e
                    continue
            # If all fail, fall back to original (backward compatibility)
            if last_error:
                logger.debug(f"Decryption failed for all keys: {last_error}")
            return encrypted_text
        except Exception as e:
            # logger.warning(f"Decryption failed (data may be plain text): {str(e)}")
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

        # Fast-path heuristic: Fernet tokens almost always start with 'gAAAAA'
        # (this prevents false negatives when the key has rotated or is misconfigured,
        # and avoids accidentally double-encrypting already-encrypted values).
        if isinstance(text, str) and text.startswith('gAAAAA'):
            return True
        
        try:
            # Try to decrypt with any key - if it works, it's encrypted
            for f in getattr(self, '_all_fernets', [self.fernet]):
                try:
                    f.decrypt(text.encode('utf-8'))
                    return True
                except Exception:
                    continue
            return False
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

