"""
Auto-Decryption Helper for Raw SQL Queries
Automatically decrypts encrypted fields in raw SQL query results.

This utility is designed for views that use raw SQL queries and return dictionaries.
It automatically detects encrypted fields and decrypts them based on the encryption_config.

Usage:
    from grc.utils.auto_decrypt_helper import decrypt_query_results
    
    # After executing raw SQL query
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    # Automatically decrypt all encrypted fields
    decrypted_results = decrypt_query_results(results, field_model_mapping)
    
    return Response(decrypted_results, status=status.HTTP_200_OK)
"""

import logging
from typing import List, Dict, Any, Optional
from .data_encryption import decrypt_data, is_encrypted_data
from .encryption_config import get_encrypted_fields_for_model

logger = logging.getLogger(__name__)


def decrypt_query_results(
    results: List[Dict[str, Any]], 
    field_model_mapping: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Automatically decrypt encrypted fields in raw SQL query results.
    
    Args:
        results: List of dictionaries from raw SQL query results
        field_model_mapping: Optional mapping of field names to model names
                          e.g., {'title': 'Audit', 'framework': 'Framework', 'auditor': 'Users'}
                          If None, will try to auto-detect based on common patterns
    
    Returns:
        List of dictionaries with decrypted values
    """
    if not results:
        return results
    
    # Default field-to-model mappings for common GRC queries
    default_mappings = {
        # Audit fields
        'title': 'Audit',
        'scope': 'Audit',
        'objective': 'Audit',
        'business_unit': 'Audit',
        'businessunit': 'Audit',
        'business-unit': 'Audit',
        'evidence': 'Audit',
        'comments': 'Audit',
        
        # Framework fields
        'framework': 'Framework',
        'framework_name': 'Framework',
        'frameworkdescription': 'Framework',
        
        # Policy fields
        'policy': 'Policy',
        'policy_name': 'Policy',
        'policyname': 'Policy',
        'policydescription': 'Policy',
        
        # SubPolicy fields
        'subpolicy': 'SubPolicy',
        'subpolicy_name': 'SubPolicy',
        'subpolicyname': 'SubPolicy',
        'description': 'SubPolicy',
        
        # Compliance fields
        'compliance_title': 'Compliance',
        'compliancetitle': 'Compliance',
        'compliance_item_description': 'Compliance',
        
        # User fields
        'auditor': 'Users',
        'reviewer': 'Users',
        'assignee': 'Users',
        'user_name': 'Users',
        'username': 'Users',
        'email': 'Users',
        'first_name': 'Users',
        'last_name': 'Users',
        'firstname': 'Users',
        'lastname': 'Users',
        
        # Risk fields
        'risk_title': 'Risk',
        'risktitle': 'Risk',
        'risk_description': 'Risk',
        'riskdescription': 'Risk',
        
        # Incident fields
        'incident_title': 'Incident',
        'incidenttitle': 'Incident',
        'description': 'Incident',
    }
    
    # Merge with provided mappings (provided mappings take precedence)
    if field_model_mapping:
        default_mappings.update(field_model_mapping)
    
    field_model_mapping = default_mappings
    
    # Get encrypted fields for each model (cache for performance)
    model_encrypted_fields = {}
    
    decrypted_results = []
    for row in results:
        decrypted_row = row.copy()
        
        for field_name, field_value in row.items():
            if field_value is None:
                continue
            
            # Skip non-string values
            if not isinstance(field_value, str):
                continue
            
            # Determine which model this field belongs to
            model_name = field_model_mapping.get(field_name.lower())
            
            if not model_name:
                # Try to find model by checking if field_name matches any encrypted field
                # This is a fallback for fields not in the mapping
                continue
            
            # Get encrypted fields for this model
            if model_name not in model_encrypted_fields:
                model_encrypted_fields[model_name] = get_encrypted_fields_for_model(model_name)
            
            encrypted_fields = model_encrypted_fields[model_name]
            
            # Check if this field should be encrypted
            # Map field name back to model field name (handle case variations and underscores)
            model_field_name = None
            # Normalize both sides: remove underscores and convert to lowercase for comparison
            field_name_normalized = field_name.lower().replace('_', '').replace('-', '')
            
            for enc_field in encrypted_fields:
                enc_field_normalized = enc_field.lower().replace('_', '').replace('-', '')
                # Compare normalized versions (handles business_unit vs BusinessUnit)
                if enc_field_normalized == field_name_normalized:
                    model_field_name = enc_field
                    break
            
            if not model_field_name:
                # Field not in encrypted fields list, skip
                continue
            
            # Try to decrypt
            try:
                # Only decrypt if it looks encrypted
                if is_encrypted_data(field_value):
                    decrypted_value = decrypt_data(field_value)
                    decrypted_row[field_name] = decrypted_value
                    logger.debug(f"Decrypted field '{field_name}' (model: {model_name}, field: {model_field_name})")
                else:
                    # Already plain text, keep as-is
                    logger.debug(f"Field '{field_name}' already plain text")
            except Exception as e:
                # Log error but keep original value
                logger.warning(f"Failed to decrypt field '{field_name}' (model: {model_name}): {str(e)}")
                # Keep original value on error
        
        decrypted_results.append(decrypted_row)
    
    return decrypted_results


def decrypt_single_value(value: Any, model_name: str, field_name: str) -> Any:
    """
    Decrypt a single value if it's an encrypted field.
    
    Args:
        value: The value to decrypt
        model_name: Name of the model (e.g., 'Audit', 'Framework')
        field_name: Name of the field in the model (e.g., 'Title', 'FrameworkName')
    
    Returns:
        Decrypted value, or original value if not encrypted or decryption fails
    """
    if value is None:
        return value
    
    if not isinstance(value, str):
        return value
    
    try:
        # Check if field is encrypted
        encrypted_fields = get_encrypted_fields_for_model(model_name)
        if field_name not in encrypted_fields:
            return value
        
        # Try to decrypt
        if is_encrypted_data(value):
            return decrypt_data(value)
        else:
            return value
    except Exception as e:
        logger.warning(f"Failed to decrypt {model_name}.{field_name}: {str(e)}")
        return value


def decrypt_any_encrypted_value(value: Any) -> Any:
    """
    Try to decrypt any value that looks encrypted, regardless of model/field.
    This is a more aggressive approach that doesn't require field mappings.
    
    Args:
        value: Any value to check and potentially decrypt
        
    Returns:
        Decrypted value if it was encrypted, original value otherwise
    """
    if value is None:
        return value
    
    if not isinstance(value, str):
        return value
    
    # Quick check - encrypted strings start with 'gAAAAA'
    if not value.startswith('gAAAAA'):
        return value
    
    try:
        if is_encrypted_data(value):
            decrypted = decrypt_data(value)
            logger.debug(f"Decrypted value (length: {len(value)} -> {len(decrypted)})")
            return decrypted
        return value
    except Exception as e:
        logger.debug(f"Failed to decrypt value: {str(e)[:50]}")
        return value


def decrypt_all_encrypted_in_dict(data: Any) -> Any:
    """
    Recursively decrypt ALL encrypted values in a dictionary/list structure.
    This function doesn't require field mappings - it tries to decrypt
    any string that looks like encrypted data.
    
    Args:
        data: Dictionary, list, or any value
        
    Returns:
        Same structure with all encrypted values decrypted
        
    Usage:
        from grc.utils.auto_decrypt_helper import decrypt_all_encrypted_in_dict
        
        data = {'title': 'gAAAAA...', 'nested': {'name': 'gAAAAA...'}}
        decrypted = decrypt_all_encrypted_in_dict(data)
    """
    if isinstance(data, dict):
        return {key: decrypt_all_encrypted_in_dict(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [decrypt_all_encrypted_in_dict(item) for item in data]
    elif isinstance(data, str):
        return decrypt_any_encrypted_value(data)
    else:
        return data


def decrypt_response_data(data: Any) -> Any:
    """
    Convenience function to decrypt response data before sending to frontend.
    Alias for decrypt_all_encrypted_in_dict.
    
    Usage:
        from grc.utils.auto_decrypt_helper import decrypt_response_data
        
        return Response(decrypt_response_data(data), status=status.HTTP_200_OK)
    """
    return decrypt_all_encrypted_in_dict(data)
