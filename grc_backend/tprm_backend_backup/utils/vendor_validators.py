"""
Vendor Input Validation Utilities - Secure input validation with vendor_ prefix
"""

import re
import html
from cerberus import Validator
from django.core.exceptions import ValidationError


def vendor_validate_input(vendor_input_value, vendor_input_type='general'):
    """
    Validate and sanitize input with vendor_ prefix
    
    Args:
        vendor_input_value: The input value to validate
        vendor_input_type: Type of input for specific validation rules
    
    Returns:
        Sanitized and validated input
    
    Raises:
        ValidationError: If input fails validation
    """
    
    if vendor_input_value is None:
        return None
    
    # Convert to string and strip whitespace
    vendor_clean_value = str(vendor_input_value).strip()
    
    # Basic sanitization - HTML escape
    vendor_clean_value = html.escape(vendor_clean_value)
    
    # Type-specific validation
    vendor_validation_rules = {
        'search_term': {
            'type': 'string',
            'minlength': 1,
            'maxlength': 100,
            'regex': r'^[a-zA-Z0-9\s\-_.]+$'
        },
        'status': {
            'type': 'string',
            'allowed': [
                'active', 'inactive', 'pending', 'suspended', 'approved', 'rejected',
                'ACTIVE', 'INACTIVE', 'PENDING', 'SUSPENDED', 'APPROVED', 'REJECTED',
                'DRAFT', 'SUBMITTED', 'IN_REVIEW', 'TERMINATED'
            ]
        },
        'risk_level': {
            'type': 'string',
            'allowed': [
                'low', 'medium', 'high', 'critical',
                'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
            ]
        },
        'category_id': {
            'type': 'string',
            'regex': r'^\d+$'
        },
        'vendor_id': {
            'type': 'string',
            'regex': r'^\d+$'
        },
        'contact_type': {
            'type': 'string',
            'allowed': [
                'PRIMARY', 'SECONDARY', 'TECHNICAL', 'BILLING', 'LEGAL', 'EMERGENCY'
            ]
        },
        'document_type': {
            'type': 'string',
            'allowed': [
                'contract', 'certificate', 'policy', 'report', 
                'compliance', 'financial', 'security', 'other'
            ]
        },
        'general': {
            'type': 'string',
            'minlength': 1,
            'maxlength': 255
        }
    }
    
    # Get validation schema
    vendor_schema = vendor_validation_rules.get(vendor_input_type, vendor_validation_rules['general'])
    vendor_validator = Validator({vendor_input_type: vendor_schema})
    
    # Validate
    vendor_document = {vendor_input_type: vendor_clean_value}
    
    if not vendor_validator.validate(vendor_document):
        vendor_errors = vendor_validator.errors.get(vendor_input_type, ['Invalid input'])
        raise ValidationError(f"Validation failed: {', '.join(vendor_errors)}")
    
    return vendor_clean_value


def vendor_validate_email(vendor_email):
    """Validate email address with vendor_ prefix"""
    if not vendor_email:
        return None
    
    vendor_email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(vendor_email_pattern, vendor_email):
        raise ValidationError("Invalid email format")
    
    return vendor_email.lower().strip()


def vendor_validate_phone(vendor_phone):
    """Validate phone number with vendor_ prefix"""
    if not vendor_phone:
        return None
    
    # Remove all non-digit characters
    vendor_digits_only = re.sub(r'\D', '', vendor_phone)
    
    # Check length (between 10 and 15 digits)
    if len(vendor_digits_only) < 10 or len(vendor_digits_only) > 15:
        raise ValidationError("Phone number must be between 10 and 15 digits")
    
    return vendor_digits_only


def vendor_validate_url(vendor_url):
    """Validate URL with vendor_ prefix"""
    if not vendor_url:
        return None
    
    vendor_url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    
    if not re.match(vendor_url_pattern, vendor_url):
        raise ValidationError("Invalid URL format")
    
    return vendor_url.strip()


def vendor_validate_file_type(vendor_filename, vendor_allowed_types=None):
    """Validate file type with vendor_ prefix"""
    if not vendor_filename:
        return False
    
    if vendor_allowed_types is None:
        vendor_allowed_types = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
            '.ppt', '.pptx', '.txt', '.csv', '.zip'
        ]
    
    vendor_file_ext = vendor_filename.lower().split('.')[-1]
    vendor_file_ext_with_dot = f'.{vendor_file_ext}'
    
    if vendor_file_ext_with_dot not in vendor_allowed_types:
        raise ValidationError(
            f"File type not allowed. Allowed types: {', '.join(vendor_allowed_types)}"
        )
    
    return True


def vendor_sanitize_filename(vendor_filename):
    """Sanitize filename with vendor_ prefix"""
    if not vendor_filename:
        return None
    
    # Remove path separators and special characters
    vendor_clean_name = re.sub(r'[<>:"/\\|?*]', '_', vendor_filename)
    
    # Remove multiple underscores
    vendor_clean_name = re.sub(r'_+', '_', vendor_clean_name)
    
    # Trim and ensure reasonable length
    vendor_clean_name = vendor_clean_name.strip('_')[:255]
    
    return vendor_clean_name


# Schema definitions for complex validation
VENDOR_COMPANY_SCHEMA = {
    'company_name': {
        'type': 'string',
        'required': True,
        'minlength': 2,
        'maxlength': 255,
        'regex': r'^[a-zA-Z0-9\s\-_.&,()]+$'
    },
    'vendor_code': {
        'type': 'string',
        'required': True,
        'minlength': 3,
        'maxlength': 50,
        'regex': r'^[A-Z0-9\-_]+$'
    },
    'email': {
        'type': 'string',
        'regex': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    },
    'website': {
        'type': 'string',
        'regex': r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    },
    'annual_revenue': {
        'type': 'float',
        'min': 0
    },
    'employee_count': {
        'type': 'integer',
        'min': 0
    }
}


def vendor_validate_company_data(vendor_company_data):
    """Validate complete company data with vendor_ prefix"""
    vendor_validator = Validator(VENDOR_COMPANY_SCHEMA)
    
    if not vendor_validator.validate(vendor_company_data):
        vendor_error_messages = []
        for vendor_field, vendor_errors in vendor_validator.errors.items():
            vendor_error_messages.append(f"{vendor_field}: {', '.join(vendor_errors)}")
        
        raise ValidationError(f"Company data validation failed: {'; '.join(vendor_error_messages)}")
    
    return vendor_validator.document
