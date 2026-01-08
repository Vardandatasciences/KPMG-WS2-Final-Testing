"""
Auto-Decryption Middleware for GRC API Responses

This middleware automatically decrypts any encrypted data in API responses.
It acts as a safety net to ensure NO encrypted data is ever sent to the frontend.

Usage:
    Add to MIDDLEWARE in settings.py:
    MIDDLEWARE = [
        ...
        'grc.utils.auto_decrypt_middleware.AutoDecryptMiddleware',
        ...
    ]
"""

import json
import logging
import re
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .data_encryption import decrypt_data, is_encrypted_data

logger = logging.getLogger(__name__)

# Pattern to detect Fernet encrypted strings (they start with 'gAAAAA')
ENCRYPTED_PATTERN = re.compile(r'^gAAAAA[A-Za-z0-9_=-]+$')


def is_likely_encrypted(value):
    """
    Check if a value looks like encrypted data.
    Fernet encrypted strings start with 'gAAAAA' and are base64-encoded.
    """
    if not isinstance(value, str):
        return False
    
    if len(value) < 20:  # Encrypted strings are typically longer
        return False
    
    # Quick check for Fernet prefix
    if value.startswith('gAAAAA'):
        return True
    
    # Use the actual is_encrypted_data check as fallback
    try:
        return is_encrypted_data(value)
    except:
        return False


def decrypt_value(value):
    """
    Attempt to decrypt a single value.
    Returns the decrypted value or original if decryption fails.
    """
    if not isinstance(value, str):
        return value
    
    if not is_likely_encrypted(value):
        return value
    
    try:
        decrypted = decrypt_data(value)
        if decrypted != value:  # Successfully decrypted
            logger.debug(f"Middleware decrypted a value (length: {len(value)} -> {len(decrypted)})")
        return decrypted
    except Exception as e:
        logger.debug(f"Middleware decryption failed (keeping original): {str(e)[:50]}")
        return value


def decrypt_dict(data):
    """
    Recursively decrypt all string values in a dictionary.
    """
    if isinstance(data, dict):
        return {key: decrypt_dict(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [decrypt_dict(item) for item in data]
    elif isinstance(data, str):
        return decrypt_value(data)
    else:
        return data


class AutoDecryptMiddleware(MiddlewareMixin):
    """
    Middleware that automatically decrypts any encrypted data in API responses.
    
    This is a safety net to ensure no encrypted data ever reaches the frontend.
    It processes all JSON responses and decrypts any values that look encrypted.
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_response(self, request, response):
        """
        Process the response and decrypt any encrypted data.
        """
        # Only process JSON responses
        content_type = response.get('Content-Type', '')
        if 'application/json' not in content_type:
            return response
        
        # Skip if response is empty or streaming
        if not hasattr(response, 'content') or not response.content:
            return response
        
        # Skip if it's a streaming response
        if getattr(response, 'streaming', False):
            return response
        
        try:
            # Parse the JSON content
            content = response.content.decode('utf-8')
            data = json.loads(content)
            
            # Decrypt the data
            decrypted_data = decrypt_dict(data)
            
            # Only update response if something was decrypted
            if decrypted_data != data:
                response.content = json.dumps(decrypted_data).encode('utf-8')
                response['Content-Length'] = len(response.content)
                logger.debug(f"Middleware decrypted response for {request.path}")
        
        except json.JSONDecodeError:
            # Not valid JSON, skip
            pass
        except Exception as e:
            # Log error but don't break the response
            logger.warning(f"AutoDecryptMiddleware error for {request.path}: {str(e)}")
        
        return response


def auto_decrypt_response_data(data):
    """
    Utility function to decrypt response data.
    Can be called manually in views if needed.
    
    Usage:
        from grc.utils.auto_decrypt_middleware import auto_decrypt_response_data
        
        data = {'title': 'gAAAAA...encrypted...', 'id': 1}
        decrypted_data = auto_decrypt_response_data(data)
    """
    return decrypt_dict(data)


