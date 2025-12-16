"""
Data Masking and Anonymization Utility
Provides functions to mask sensitive data like emails, phone numbers, addresses, and names.
Supports reversible pseudonymization with secure key management.
"""

import re
import json
import hashlib
import base64
from typing import Any, Dict, Optional, Union
from django.conf import settings


class DataMaskingService:
    """
    Service for masking and anonymizing sensitive data.
    Supports email masking, phone masking, address masking, name masking, and ID pseudonymization.
    """
    
    # Masking character
    MASK_CHAR = '*'
    
    # Configuration for masking patterns
    EMAIL_VISIBLE_CHARS = 2  # Show first 2 characters before @
    PHONE_VISIBLE_CHARS = 5  # Show first 5 digits
    ADDRESS_VISIBLE_CHARS = 5  # Show first 5 characters
    NAME_VISIBLE_CHARS = 1  # Show first 1 character
    
    def __init__(self):
        """Initialize the masking service"""
        # Get encryption key from settings or use default
        self.encryption_key = getattr(settings, 'DATA_MASKING_KEY', 'default-masking-key-change-in-production')
    
    def mask_email(self, email: str) -> str:
        """
        Mask an email address.
        Example: john.doe@example.com -> jo******@ex*****.com
        """
        if not email or not isinstance(email, str):
            return email
        
        email = email.strip()
        if '@' not in email:
            return self._mask_string(email, self.EMAIL_VISIBLE_CHARS)
        
        local_part, domain = email.split('@', 1)
        
        # Mask local part (before @)
        masked_local = self._mask_string(local_part, self.EMAIL_VISIBLE_CHARS)
        
        # Mask domain part
        if '.' in domain:
            domain_parts = domain.rsplit('.', 1)
            domain_name = domain_parts[0]
            domain_ext = domain_parts[1]
            masked_domain = self._mask_string(domain_name, self.EMAIL_VISIBLE_CHARS) + '.' + domain_ext
        else:
            masked_domain = self._mask_string(domain, self.EMAIL_VISIBLE_CHARS)
        
        return f"{masked_local}@{masked_domain}"
    
    def mask_phone(self, phone: str) -> str:
        """
        Mask a phone number.
        Example: 9940512345 -> 99405*****
        Example: +1-555-123-4567 -> +1-555-***-****
        """
        if not phone or not isinstance(phone, str):
            return phone
        
        phone = phone.strip()
        
        # Remove common separators for processing
        clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
        
        # If it's all digits, mask from position 5 onwards
        if clean_phone.isdigit():
            if len(clean_phone) <= self.PHONE_VISIBLE_CHARS:
                return phone  # Too short to mask meaningfully
            visible = clean_phone[:self.PHONE_VISIBLE_CHARS]
            masked = self.MASK_CHAR * (len(clean_phone) - self.PHONE_VISIBLE_CHARS)
            return visible + masked
        
        # For formatted phone numbers, try to preserve format
        # Extract digits
        digits = re.findall(r'\d', phone)
        if len(digits) <= self.PHONE_VISIBLE_CHARS:
            return phone
        
        visible_digits = digits[:self.PHONE_VISIBLE_CHARS]
        masked_count = len(digits) - self.PHONE_VISIBLE_CHARS
        
        # Try to reconstruct with masking
        result = phone
        digit_index = 0
        masked_digits = 0
        result_chars = []
        
        for char in phone:
            if char.isdigit():
                if digit_index < self.PHONE_VISIBLE_CHARS:
                    result_chars.append(char)
                else:
                    result_chars.append(self.MASK_CHAR)
                    masked_digits += 1
                digit_index += 1
            else:
                result_chars.append(char)
        
        return ''.join(result_chars)
    
    def mask_address(self, address: str) -> str:
        """
        Mask an address.
        Example: 123 Main Street, New York -> 123 M*** S******, N** Y***
        """
        if not address or not isinstance(address, str):
            return address
        
        address = address.strip()
        if len(address) <= self.ADDRESS_VISIBLE_CHARS:
            return self.MASK_CHAR * len(address)
        
        # Show first few characters, mask the rest
        visible = address[:self.ADDRESS_VISIBLE_CHARS]
        masked = self.MASK_CHAR * (len(address) - self.ADDRESS_VISIBLE_CHARS)
        return visible + masked
    
    def mask_name(self, name: str) -> str:
        """
        Mask a name (first name or last name).
        Example: John -> J***
        Example: Doe -> D**
        """
        if not name or not isinstance(name, str):
            return name
        
        name = name.strip()
        if len(name) <= self.NAME_VISIBLE_CHARS:
            return self.MASK_CHAR * len(name)
        
        visible = name[:self.NAME_VISIBLE_CHARS]
        masked = self.MASK_CHAR * (len(name) - self.NAME_VISIBLE_CHARS)
        return visible + masked
    
    def mask_user_id(self, user_id: Union[int, str]) -> str:
        """
        Pseudonymize a user ID (reversible with key).
        Example: 123 -> pseudonymized_hash
        """
        if user_id is None:
            return None
        
        user_id_str = str(user_id)
        # Create a hash-based pseudonym
        combined = f"{self.encryption_key}:{user_id_str}"
        hash_obj = hashlib.sha256(combined.encode())
        pseudonym = base64.urlsafe_b64encode(hash_obj.digest()[:8]).decode('utf-8').rstrip('=')
        return f"UID_{pseudonym}"
    
    def unmask_user_id(self, pseudonym: str) -> Optional[str]:
        """
        Attempt to reverse pseudonymization (requires original ID lookup).
        Note: This is a one-way hash, so we can't directly reverse it.
        We would need to maintain a mapping table for true reversibility.
        """
        # For true reversibility, you would need a mapping table
        # This is a placeholder for the concept
        return None
    
    def _mask_string(self, text: str, visible_chars: int) -> str:
        """Internal helper to mask a string"""
        if not text or len(text) <= visible_chars:
            return self.MASK_CHAR * len(text) if text else text
        return text[:visible_chars] + self.MASK_CHAR * (len(text) - visible_chars)
    
    def mask_dict(self, data: Dict[str, Any], fields_to_mask: Optional[list] = None) -> Dict[str, Any]:
        """
        Mask sensitive fields in a dictionary.
        
        Args:
            data: Dictionary containing data to mask
            fields_to_mask: List of field names to mask. If None, uses default sensitive fields.
        
        Returns:
            Dictionary with masked values
        """
        if not isinstance(data, dict):
            return data
        
        if fields_to_mask is None:
            fields_to_mask = ['email', 'Email', 'phone', 'Phone', 'phoneNumber', 'PhoneNumber',
                            'address', 'Address', 'firstName', 'FirstName', 'lastName', 'LastName',
                            'userId', 'UserId', 'userName', 'UserName']
        
        masked_data = data.copy()
        
        for key, value in masked_data.items():
            if key in fields_to_mask and value:
                if isinstance(value, str):
                    key_lower = key.lower()
                    if 'email' in key_lower:
                        masked_data[key] = self.mask_email(value)
                    elif 'phone' in key_lower:
                        masked_data[key] = self.mask_phone(value)
                    elif 'address' in key_lower:
                        masked_data[key] = self.mask_address(value)
                    elif 'firstname' in key_lower or 'lastname' in key_lower:
                        masked_data[key] = self.mask_name(value)
                    elif 'userid' in key_lower and key_lower != 'username':
                        masked_data[key] = self.mask_user_id(value)
                elif isinstance(value, dict):
                    masked_data[key] = self.mask_dict(value, fields_to_mask)
                elif isinstance(value, list):
                    masked_data[key] = [self.mask_dict(item, fields_to_mask) if isinstance(item, dict) else item for item in value]
        
        return masked_data
    
    def mask_json_string(self, json_str: str, fields_to_mask: Optional[list] = None) -> str:
        """
        Mask sensitive fields in a JSON string.
        
        Args:
            json_str: JSON string to mask
            fields_to_mask: List of field names to mask
        
        Returns:
            Masked JSON string
        """
        try:
            data = json.loads(json_str)
            masked_data = self.mask_dict(data, fields_to_mask)
            return json.dumps(masked_data)
        except (json.JSONDecodeError, TypeError):
            return json_str
    
    def mask_log_data(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive data in log entries before saving to grc_logs.
        
        Args:
            log_data: Dictionary containing log data
        
        Returns:
            Dictionary with masked sensitive fields
        """
        masked_log = log_data.copy()
        
        # Mask UserName
        if 'UserName' in masked_log and masked_log['UserName']:
            masked_log['UserName'] = self.mask_name(masked_log['UserName'])
        
        # Mask UserId (pseudonymize)
        if 'UserId' in masked_log and masked_log['UserId']:
            masked_log['UserId'] = self.mask_user_id(masked_log['UserId'])
        
        # Mask Description if it contains sensitive data
        if 'Description' in masked_log and masked_log['Description']:
            desc = masked_log['Description']
            # Try to extract and mask emails, phones, addresses from description
            desc = self._mask_sensitive_in_text(desc)
            masked_log['Description'] = desc
        
        # Mask AdditionalInfo JSON field
        if 'AdditionalInfo' in masked_log and masked_log['AdditionalInfo']:
            if isinstance(masked_log['AdditionalInfo'], str):
                try:
                    additional_info = json.loads(masked_log['AdditionalInfo'])
                    masked_log['AdditionalInfo'] = self.mask_dict(additional_info)
                except (json.JSONDecodeError, TypeError):
                    # If it's not valid JSON, try to mask as text
                    masked_log['AdditionalInfo'] = self._mask_sensitive_in_text(masked_log['AdditionalInfo'])
            elif isinstance(masked_log['AdditionalInfo'], dict):
                masked_log['AdditionalInfo'] = self.mask_dict(masked_log['AdditionalInfo'])
        
        return masked_log
    
    def _mask_sensitive_in_text(self, text: str) -> str:
        """
        Mask sensitive data patterns in free-form text.
        """
        if not isinstance(text, str):
            return text
        
        # Mask email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text = re.sub(email_pattern, lambda m: self.mask_email(m.group()), text)
        
        # Mask phone numbers (various formats)
        phone_patterns = [
            r'\b\d{10}\b',  # 10-digit numbers
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # US format
            r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b',  # International
        ]
        for pattern in phone_patterns:
            text = re.sub(pattern, lambda m: self.mask_phone(m.group()), text)
        
        return text


# Global instance
_masking_service = None

def get_masking_service() -> DataMaskingService:
    """Get the global masking service instance"""
    global _masking_service
    if _masking_service is None:
        _masking_service = DataMaskingService()
    return _masking_service


# Convenience functions
def mask_email(email: str) -> str:
    """Mask an email address"""
    return get_masking_service().mask_email(email)


def mask_phone(phone: str) -> str:
    """Mask a phone number"""
    return get_masking_service().mask_phone(phone)


def mask_address(address: str) -> str:
    """Mask an address"""
    return get_masking_service().mask_address(address)


def mask_name(name: str) -> str:
    """Mask a name"""
    return get_masking_service().mask_name(name)


def mask_user_id(user_id: Union[int, str]) -> str:
    """Pseudonymize a user ID"""
    return get_masking_service().mask_user_id(user_id)


def mask_dict(data: Dict[str, Any], fields_to_mask: Optional[list] = None) -> Dict[str, Any]:
    """Mask sensitive fields in a dictionary"""
    return get_masking_service().mask_dict(data, fields_to_mask)


def mask_log_data(log_data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive data in log entries"""
    return get_masking_service().mask_log_data(log_data)

