"""
Data Encryption/Decryption Utility for GRC Models
Provides encryption and decryption for sensitive fields that need to be retrieved later.

New values are encrypted with AES-256-GCM (authenticated encryption).
Legacy Fernet (AES-128-CBC + HMAC) ciphertext remains supported for decrypt.

IMPORTANT:
- Encryption = Two-way (can encrypt and decrypt to see plain text later)
- Hashing = One-way (cannot reverse, only verify)
- Use ENCRYPTION for: Email, Phone, Address, License Key (data you need to read later)
- Use HASHING for: Passwords, OTPs (data you only need to verify, never read)
"""

import base64
import logging
import os
from typing import List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings

logger = logging.getLogger(__name__)

# v2 envelope: AES-256-GCM, 12-byte nonce, ciphertext||tag from cryptography's AESGCM
GCM_ENVELOPE_PREFIX = "GRCv2$"
GCM_NONCE_SIZE = 12

# Default encrypt backend: "gcm" (recommended). Set GRC_FIELD_ENCRYPTION_BACKEND=fernet to force legacy Fernet for new writes.
_DEFAULT_BACKEND = "gcm"


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _material_to_aes256_key(key_material) -> Optional[bytes]:
    """
    Derive 32-byte AES-256 key from the same material used for Fernet
    (url-safe base64 of 32 random bytes), or from a raw 32-byte secret.
    """
    if key_material is None:
        return None
    if isinstance(key_material, str):
        kb = key_material.encode("utf-8")
    else:
        kb = bytes(key_material)
    pad = b"=" * (-len(kb) % 4)
    try:
        decoded = base64.urlsafe_b64decode(kb + pad)
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass
    if len(kb) == 32:
        return bytes(kb)
    return None


class DataEncryptionService:
    """
    Encrypt/decrypt sensitive data. Writes use AES-256-GCM unless
    GRC_FIELD_ENCRYPTION_BACKEND=fernet. Reads support GCM and legacy Fernet.
    """

    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self._all_fernets = self._build_all_fernets()
        self._aes256_keys: List[bytes] = self._build_aes256_keys()

    def _encrypt_backend(self) -> str:
        b = getattr(settings, "GRC_FIELD_ENCRYPTION_BACKEND", None) or os.environ.get(
            "GRC_FIELD_ENCRYPTION_BACKEND", _DEFAULT_BACKEND
        )
        return str(b).strip().lower() or _DEFAULT_BACKEND

    def _get_candidate_keys(self) -> list:
        """
        Get a list of candidate encryption keys in priority order.

        Supports key-rotation by allowing multiple keys for decryption.
        The FIRST key is used for encryption; all keys are tried for decryption.
        """
        keys: list = []

        multi = getattr(settings, "GRC_ENCRYPTION_KEYS", None) or os.environ.get("GRC_ENCRYPTION_KEYS")
        if multi:
            if isinstance(multi, str):
                for part in multi.split(","):
                    part = part.strip()
                    if part:
                        keys.append(part)
            elif isinstance(multi, (list, tuple)):
                keys.extend([k for k in multi if k])

        single = getattr(settings, "GRC_ENCRYPTION_KEY", None) or os.environ.get("GRC_ENCRYPTION_KEY")
        if single:
            keys.append(single)

        for alt_name in ("TPRM_ENCRYPTION_KEY", "DATA_ENCRYPTION_KEY", "VENDOR_ENCRYPTION_KEY"):
            alt = getattr(settings, alt_name, None) or os.environ.get(alt_name)
            if alt:
                keys.append(alt)

        deduped = []
        seen = set()
        for k in keys:
            ks = k.decode() if isinstance(k, (bytes, bytearray)) else str(k)
            if ks not in seen:
                seen.add(ks)
                deduped.append(k)
        return deduped

    def _build_all_fernets(self) -> list:
        fernets = []
        for key in self._get_candidate_keys():
            if isinstance(key, str):
                key = key.encode()
            try:
                fernets.append(Fernet(key))
            except Exception as e:
                logger.warning(f"Invalid encryption key ignored: {e}")

        try:
            primary = self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key
            primary_fernet = Fernet(primary)
            fernets = [primary_fernet] + [f for f in fernets if f._signing_key != primary_fernet._signing_key]
        except Exception:
            pass
        return fernets

    def _build_aes256_keys(self) -> List[bytes]:
        out: List[bytes] = []
        seen = set()
        for k in self._get_candidate_keys():
            raw = _material_to_aes256_key(k)
            if raw and raw not in seen:
                seen.add(raw)
                out.append(raw)
        return out

    def _get_encryption_key(self) -> bytes:
        """
        Primary key material (Fernet-compatible base64url string as bytes).
        """
        candidates = self._get_candidate_keys()
        key = candidates[0] if candidates else None

        if not key:
            raise RuntimeError(
                "GRC_ENCRYPTION_KEY is not configured. "
                "Set it in your environment or Django settings to match the key "
                "used for existing encrypted data. No fallback key will be generated."
            )

        if isinstance(key, str):
            key = key.encode()

        return key

    def _encrypt_gcm(self, plain_text: str) -> str:
        if not self._aes256_keys:
            raise RuntimeError(
                "Cannot use AES-256-GCM: no valid 32-byte key material derived from GRC_ENCRYPTION_KEY."
            )
        key = self._aes256_keys[0]
        nonce = os.urandom(GCM_NONCE_SIZE)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
        blob = nonce + ciphertext
        return GCM_ENVELOPE_PREFIX + _b64url_encode(blob)

    def _decrypt_gcm(self, encrypted_text: str) -> Optional[str]:
        if not encrypted_text.startswith(GCM_ENVELOPE_PREFIX):
            return None
        try:
            raw = _b64url_decode(encrypted_text[len(GCM_ENVELOPE_PREFIX) :])
        except Exception:
            return None
        if len(raw) < GCM_NONCE_SIZE + 16:
            return None
        nonce = raw[:GCM_NONCE_SIZE]
        ct = raw[GCM_NONCE_SIZE:]
        last_error = None
        for key in self._aes256_keys:
            try:
                aesgcm = AESGCM(key)
                pt = aesgcm.decrypt(nonce, ct, None)
                return pt.decode("utf-8")
            except Exception as e:
                last_error = e
                continue
        if last_error:
            logger.debug(f"AES-GCM decrypt failed for all keys: {last_error}")
        return None

    def _peel_one_layer(self, text: str) -> Optional[str]:
        gcm_pt = self._decrypt_gcm(text)
        if gcm_pt is not None:
            return gcm_pt
        for f in getattr(self, "_all_fernets", [self.fernet]):
            try:
                return f.decrypt(text.encode("utf-8")).decode("utf-8")
            except Exception:
                continue
        return None

    def encrypt(self, plain_text: Optional[str]) -> Optional[str]:
        if plain_text is None:
            return None

        if not isinstance(plain_text, str):
            plain_text = str(plain_text)

        try:
            if self._encrypt_backend() == "fernet":
                encrypted_bytes = self.fernet.encrypt(plain_text.encode("utf-8"))
                return encrypted_bytes.decode("utf-8")
            return self._encrypt_gcm(plain_text)
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            return plain_text

    def decrypt(self, encrypted_text: Optional[str]) -> Optional[str]:
        if encrypted_text is None:
            return None

        if not isinstance(encrypted_text, str):
            encrypted_text = str(encrypted_text)

        try:
            current = encrypted_text
            for _ in range(3):
                peeled = self._peel_one_layer(current)
                if peeled is None:
                    break
                current = peeled
                if not self.is_encrypted(current):
                    return current
            return current
        except Exception as e:
            logger.debug(f"Decryption failed (data may be plain text): {str(e)}")
            return encrypted_text

    def is_encrypted(self, text: Optional[str]) -> bool:
        if not text:
            return False

        if isinstance(text, str) and text.startswith(GCM_ENVELOPE_PREFIX):
            return True

        if isinstance(text, str) and text.startswith("gAAAAA"):
            return True

        try:
            for f in getattr(self, "_all_fernets", [self.fernet]):
                try:
                    f.decrypt(text.encode("utf-8"))
                    return True
                except Exception:
                    continue
            return False
        except Exception:
            return False


_encryption_service = None


def get_encryption_service() -> DataEncryptionService:
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = DataEncryptionService()
    return _encryption_service


def encrypt_data(plain_text: Optional[str]) -> Optional[str]:
    return get_encryption_service().encrypt(plain_text)


def decrypt_data(encrypted_text: Optional[str]) -> Optional[str]:
    return get_encryption_service().decrypt(encrypted_text)


def is_encrypted_data(text: Optional[str]) -> bool:
    return get_encryption_service().is_encrypted(text)


def _key_bytes(key_material) -> bytes:
    if isinstance(key_material, str):
        return key_material.encode("utf-8")
    return bytes(key_material)


def encrypt_blob_with_key(key_material, plain_text: str) -> str:
    """
    AES-256-GCM envelope (same as field encryption) using a specific key material,
    e.g. VENDOR_SETTINGS['ENCRYPTION_KEY'], without relying on global key order.
    """
    key = _material_to_aes256_key(_key_bytes(key_material))
    if not key:
        raise ValueError(
            "Key must be Fernet-compatible (url-safe base64 of 32 bytes) or raw 32 bytes."
        )
    nonce = os.urandom(GCM_NONCE_SIZE)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
    return GCM_ENVELOPE_PREFIX + _b64url_encode(nonce + ciphertext)


def decrypt_blob_with_key(key_material, encrypted_text: str) -> str:
    """Decrypt a value produced by encrypt_blob_with_key, or legacy Fernet with the same key material."""
    kb = _key_bytes(key_material)
    if encrypted_text.startswith(GCM_ENVELOPE_PREFIX):
        key = _material_to_aes256_key(kb)
        if not key:
            raise ValueError("Invalid encryption key material")
        raw = _b64url_decode(encrypted_text[len(GCM_ENVELOPE_PREFIX) :])
        if len(raw) < GCM_NONCE_SIZE + 16:
            raise ValueError("Invalid GCM ciphertext")
        nonce = raw[:GCM_NONCE_SIZE]
        ct = raw[GCM_NONCE_SIZE:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ct, None).decode("utf-8")
    return Fernet(kb).decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
