"""
Vendor Input Validation Middleware - Centralized validation using allow-list approach
"""

import logging
import json
import re
from typing import Dict, Any, List, Union
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from cerberus import Validator
import html

vendor_validation_logger = logging.getLogger('vendor_security')


class VendorInputValidationMiddleware(MiddlewareMixin):
    """
    Centralized input validation middleware using allow-list validation
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self.vendor_validator = Validator()
        self.vendor_allowed_patterns = self._vendor_get_allowed_patterns()
        self.vendor_validation_schemas = self._vendor_get_validation_schemas()
    
    def _vendor_get_allowed_patterns(self) -> Dict[str, str]:
        """Define allowed patterns for different data types"""
        return {
            'vendor_email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'vendor_phone': r'^\+?1?[0-9]{10,15}$',
            'vendor_alphanumeric': r'^[a-zA-Z0-9\s\-_\.]+$',
            'vendor_numeric': r'^\d+$',
            'vendor_decimal': r'^\d+(\.\d{1,2})?$',
            'vendor_date': r'^\d{4}-\d{2}-\d{2}$',
            'vendor_uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            'vendor_safe_text': r'^[a-zA-Z0-9\s\-_\.,!?\(\)@#$%^&*+=:;"\'\[\]{}|\\`~]*$',
        }
    
    def _vendor_get_validation_schemas(self) -> Dict[str, Dict]:
        """Define validation schemas for different endpoints"""
        return {
            'vendor_auth_login': {
                'username': {
                    'type': 'string',
                    'required': True,
                    'regex': self.vendor_allowed_patterns['vendor_alphanumeric'],
                    'maxlength': 255
                },
                'password': {
                    'type': 'string',
                    'required': True,
                    'minlength': 1,
                    'maxlength': 255
                }
            },
            'vendor_registration': {
                'vendor_company_name': {
                    'type': 'string',
                    'required': True,
                    'regex': self.vendor_allowed_patterns['vendor_alphanumeric'],
                    'maxlength': 200
                },
                'vendor_email': {
                    'type': 'string',
                    'required': True,
                    'regex': self.vendor_allowed_patterns['vendor_email'],
                    'maxlength': 254
                },
                'vendor_phone': {
                    'type': 'string',
                    'required': True,
                    'regex': self.vendor_allowed_patterns['vendor_phone']
                },
                'vendor_address': {
                    'type': 'string',
                    'required': True,
                    'regex': self.vendor_allowed_patterns['vendor_safe_text'],
                    'maxlength': 500
                }
            },
            'vendor_risk_assessment': {
                'vendor_risk_score': {
                    'type': 'number',
                    'required': True,
                    'min': 0,
                    'max': 100
                },
                'vendor_assessment_notes': {
                    'type': 'string',
                    'required': False,
                    'regex': self.vendor_allowed_patterns['vendor_safe_text'],
                    'maxlength': 2000
                }
            }
        }
    
    def process_request(self, request: HttpRequest) -> HttpResponse:
        """Validate all incoming request data"""
        
        # Skip validation for certain endpoints
        if self._vendor_should_skip_validation(request):
            return None
        
        # Validate and sanitize request data
        validation_result = self._vendor_validate_request_data(request)
        
        if not validation_result['vendor_is_valid']:
            vendor_validation_logger.warning(
                f"Input validation failed for {request.path}",
                extra={
                    'ip_address': self._vendor_get_client_ip(request),
                    'validation_errors': validation_result['vendor_errors'],
                    'action': 'input_validation_failed'
                }
            )
            
            return JsonResponse({
                'error': 'Invalid input data',
                'details': validation_result['vendor_errors'] if hasattr(request, 'user') and hasattr(request.user, 'is_staff') and request.user.is_staff else 'Please check your input'
            }, status=400)
        
        # Store sanitized data in request for later use
        request.vendor_validated_data = validation_result['vendor_sanitized_data']
        
        return None
    
    def _vendor_should_skip_validation(self, request: HttpRequest) -> bool:
        """Check if validation should be skipped for this request"""
        skip_paths = [
            '/api/v1/health/',
            '/vendor-admin/',
            '/static/',
            '/media/',
            '/api/v1/vendor-approval/vendors/',  # Skip validation for vendor endpoints
            '/api/v1/vendor-approval/users/',     # Skip validation for user endpoints
            '/api/v1/vendor-approval/questionnaires/',  # Skip validation for questionnaire endpoints
        ]
        
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _vendor_validate_request_data(self, request: HttpRequest) -> Dict[str, Any]:
        """Validate and sanitize request data using allow-list approach"""
        result = {
            'vendor_is_valid': True,
            'vendor_errors': [],
            'vendor_sanitized_data': {}
        }
        
        try:
            # Determine validation schema based on endpoint
            schema = self._vendor_get_schema_for_endpoint(request.path)
            
            if not schema:
                # No specific schema, perform basic validation
                return self._vendor_basic_validation(request)
            
            # Extract data to validate
            data_to_validate = self._vendor_extract_request_data(request)
            
            # Validate using Cerberus
            if not self.vendor_validator.validate(data_to_validate, schema):
                result['vendor_is_valid'] = False
                result['vendor_errors'] = self.vendor_validator.errors
                return result
            
            # Sanitize validated data
            result['vendor_sanitized_data'] = self._vendor_sanitize_data(
                self.vendor_validator.document
            )
            
            vendor_validation_logger.info(
                f"Input validation passed for {request.path}",
                extra={
                    'ip_address': self._vendor_get_client_ip(request),
                    'action': 'input_validation_passed'
                }
            )
            
        except Exception as e:
            vendor_validation_logger.error(f"Validation error: {str(e)}")
            result['vendor_is_valid'] = False
            result['vendor_errors'] = ['Validation failed']
        
        return result
    
    def _vendor_get_schema_for_endpoint(self, path: str) -> Dict:
        """Get validation schema based on endpoint path"""
        if 'login' in path:
            return self.vendor_validation_schemas.get('vendor_auth_login')
        elif 'register' in path:
            return self.vendor_validation_schemas.get('vendor_registration')
        elif 'risk-assessment' in path:  # Only apply to actual risk assessment endpoints, not risk data retrieval
            return self.vendor_validation_schemas.get('vendor_risk_assessment')
        
        return None
    
    def _vendor_extract_request_data(self, request: HttpRequest) -> Dict:
        """Extract data from request for validation"""
        data = {}
        
        # Extract GET parameters
        data.update(request.GET.dict())
        
        # Extract POST data
        if hasattr(request, 'POST'):
            data.update(request.POST.dict())
        
        # Extract JSON data
        if request.content_type == 'application/json' and hasattr(request, 'body'):
            try:
                json_data = json.loads(request.body.decode('utf-8'))
                if isinstance(json_data, dict):
                    data.update(json_data)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
        
        return data
    
    def _vendor_basic_validation(self, request: HttpRequest) -> Dict[str, Any]:
        """Perform basic validation when no specific schema is available"""
        result = {
            'vendor_is_valid': True,
            'vendor_errors': [],
            'vendor_sanitized_data': {}
        }
        
        try:
            # Check for basic threats in all string inputs
            data = self._vendor_extract_request_data(request)
            sanitized_data = {}
            
            for key, value in data.items():
                if isinstance(value, str):
                    # Check for malicious patterns
                    if self._vendor_contains_malicious_patterns(value):
                        result['vendor_is_valid'] = False
                        result['vendor_errors'].append(f"Invalid characters in field: {key}")
                        continue
                    
                    # Sanitize the value
                    sanitized_data[key] = self._vendor_sanitize_string(value)
                else:
                    sanitized_data[key] = value
            
            result['vendor_sanitized_data'] = sanitized_data
            
        except Exception as e:
            vendor_validation_logger.error(f"Basic validation error: {str(e)}")
            result['vendor_is_valid'] = False
            result['vendor_errors'] = ['Basic validation failed']
        
        return result
    
    def _vendor_contains_malicious_patterns(self, value: str) -> bool:
        """Check for malicious patterns in input"""
        malicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'eval\s*\(',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'union\s+select',  # SQL injection
            r'insert\s+into',
            r'delete\s+from',
            r'drop\s+table',
            r'exec\s*\(',
        ]
        
        value_lower = value.lower()
        for pattern in malicious_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _vendor_sanitize_data(self, data: Dict) -> Dict:
        """Sanitize validated data"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._vendor_sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[key] = self._vendor_sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._vendor_sanitize_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _vendor_sanitize_string(self, value: str) -> str:
        """Sanitize string input to prevent XSS and other attacks"""
        # HTML escape
        sanitized = html.escape(value, quote=True)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    def _vendor_get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address safely"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
