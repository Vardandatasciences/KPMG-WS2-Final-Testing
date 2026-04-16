from django.core.validators import validate_email
import re
from datetime import datetime, date
import json
from urllib.parse import urlsplit

def validate_string(value, min_length=1, max_length=255, field_name="field", allow_none=False):
    """Validate string input"""
    if allow_none and value is None:
        return None
        
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
        
    if len(value.strip()) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters long")
        
    if len(value) > max_length:
        raise ValidationError(f"{field_name} cannot exceed {max_length} characters")
        
    # Remove any potentially dangerous characters
    cleaned = re.sub(r'[<>&;]', '', value)
    return cleaned.strip()

def validate_int(value, min_value=None, max_value=None, field_name="field", allow_none=False):
    """Validate integer input"""
    if allow_none and value is None:
        return None
        
    try:
        val = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid integer")
        
    if min_value is not None and val < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}")
        
    if max_value is not None and val > max_value:
        raise ValidationError(f"{field_name} must not exceed {max_value}")
        
    return val

def validate_date(value, field_name="date", allow_none=False, check_future=False, check_past=False):
    """Validate date string input - supports both DD/MM/YYYY and YYYY-MM-DD formats.
    
    check_future=True: rejects dates in the past (use for due dates)
    check_past=True: rejects dates more than 10 years in the future (use for due dates)
    """
    if allow_none and (value is None or value == ''):
        return None
        
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a valid date string")
    
    value = value.strip()
    if not value:
        return None
        
    # Try multiple date formats
    date_formats = [
        '%d/%m/%Y',    # DD/MM/YYYY
        '%d-%m-%Y',    # DD-MM-YYYY 
        '%Y-%m-%d',    # YYYY-MM-DD (ISO format)
        '%m/%d/%Y',    # MM/DD/YYYY
        '%m-%d-%Y'     # MM-DD-YYYY
    ]
    
    parsed_date = None
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(value, date_format).date()
            break
        except ValueError:
            continue

    if parsed_date is None:
        raise ValidationError(f"{field_name} must be a valid date in DD/MM/YYYY or YYYY-MM-DD format")

    today = date.today()
    if check_future and parsed_date < today:
        raise ValidationError(f"{field_name} cannot be in the past.")
    if check_past:
        max_allowed = today.replace(year=today.year + 10)
        if parsed_date > max_allowed:
            raise ValidationError(f"{field_name} cannot be more than 10 years in the future.")

    return parsed_date

def validate_audit_type(value):
    """Validate audit type"""
    allowed_types = ['I', 'E', 'S']
    if value not in allowed_types:
        raise ValidationError("Audit type must be 'I' (Internal), 'E' (External) or 'S' (Self-Audit)")
    return value

def validate_frequency(value):
    """Validate audit frequency"""
    allowed_frequencies = ['0', '1', '60', '120', '182', '365', '365a']
    if value not in allowed_frequencies:
        raise ValidationError("Invalid frequency value")
    return value

def validate_compliance_status(value):
    """Validate compliance status"""
    # Allow empty/None status - means user hasn't selected yet
    if value is None or value == '':
        return ''
    
    # Convert to string to handle numeric '0' etc.
    str_value = str(value)
    allowed_statuses = ['0', '1', '2', '3']  # Not Compliant, Partially Compliant, Fully Compliant, Not Applicable
    if str_value not in allowed_statuses:
        raise ValidationError("Invalid compliance status")
    return str_value

def validate_major_minor(value):
    """Validate major/minor finding type"""
    if value is None or value == '':
        return ''
    
    # Convert to string to handle numeric '0' etc.
    str_value = str(value)
    allowed_values = ['0', '1']  # Minor, Major
    if str_value not in allowed_values:
        raise ValidationError("Invalid finding type")
    return str_value

def validate_severity_rating(value):
    """Validate severity rating"""
    if value is None or value == '':
        return None
    try:
        rating = int(value)
        if rating < 1 or rating > 10:
            raise ValidationError("Severity rating must be between 1 and 10")
        return rating
    except (TypeError, ValueError):
        raise ValidationError("Severity rating must be a valid number")

def validate_boolean(value, field_name="field"):
    """Validate boolean input"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ['true', '1', 'yes']:
            return True
        elif value.lower() in ['false', '0', 'no']:
            return False
    raise ValidationError(f"{field_name} must be a valid boolean")

def validate_url(value, field_name="URL", allow_none=False):
    """Validate URL format"""
    if allow_none and (value is None or value == ''):
        return ''
    
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    
    # Basic URL validation - can be enhanced based on needs
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(value):
        raise ValidationError(f"{field_name} must be a valid URL")
    
    return value

def validate_json_data(value, field_name="JSON data"):
    """Validate JSON data"""
    if value is None:
        return None
    
    if isinstance(value, dict):
        return value
    
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            raise ValidationError(f"{field_name} must be valid JSON")
    
    raise ValidationError(f"{field_name} must be a valid JSON object")

def validate_compliance_data(compliance_data):
    """Validate compliance item data"""
    if not isinstance(compliance_data, dict):
        raise ValidationError("Compliance data must be a dictionary")
    
    validated_data = {}
    
    # Validate each field
    validated_data['description'] = validate_string(
        compliance_data.get('description', ''), 
        min_length=0, max_length=2000, field_name="Description", allow_none=True
    )
    
    validated_data['status'] = validate_compliance_status(
        compliance_data.get('status', '0')
    )
    
    validated_data['evidence'] = validate_string(
        compliance_data.get('evidence', ''), 
        min_length=0, max_length=5000, field_name="Evidence", allow_none=True
    )
    
    validated_data['comments'] = validate_string(
        compliance_data.get('comments', ''), 
        min_length=0, max_length=2000, field_name="Comments", allow_none=True
    )
    
    validated_data['how_to_verify'] = validate_string(
        compliance_data.get('how_to_verify', ''), 
        min_length=0, max_length=1000, field_name="How to Verify", allow_none=True
    )
    
    validated_data['impact'] = validate_string(
        compliance_data.get('impact', ''), 
        min_length=0, max_length=1000, field_name="Impact", allow_none=True
    )
    
    validated_data['details_of_finding'] = validate_string(
        compliance_data.get('details_of_finding', ''), 
        min_length=0, max_length=2000, field_name="Details of Finding", allow_none=True
    )
    
    validated_data['major_minor'] = validate_major_minor(
        compliance_data.get('major_minor', '')
    )
    
    validated_data['severity_rating'] = validate_severity_rating(
        compliance_data.get('severity_rating', '')
    )
    
    validated_data['why_to_verify'] = validate_string(
        compliance_data.get('why_to_verify', ''), 
        min_length=0, max_length=1000, field_name="Why to Verify", allow_none=True
    )
    
    validated_data['what_to_verify'] = validate_string(
        compliance_data.get('what_to_verify', ''), 
        min_length=0, max_length=1000, field_name="What to Verify", allow_none=True
    )
    
    validated_data['underlying_cause'] = validate_string(
        compliance_data.get('underlying_cause', ''), 
        min_length=0, max_length=1000, field_name="Underlying Cause", allow_none=True
    )
    
    validated_data['suggested_action_plan'] = validate_string(
        compliance_data.get('suggested_action_plan', ''), 
        min_length=0, max_length=2000, field_name="Suggested Action Plan", allow_none=True
    )
    
    validated_data['responsible_for_plan'] = validate_string(
        compliance_data.get('responsible_for_plan', ''), 
        min_length=0, max_length=200, field_name="Responsible for Plan", allow_none=True
    )
    
    validated_data['mitigation_date'] = validate_date(
        compliance_data.get('mitigation_date', ''), 
        field_name="Mitigation Date", allow_none=True
    )
    
    validated_data['re_audit'] = validate_boolean(
        compliance_data.get('re_audit', False), 
        field_name="Re-audit"
    )
    
    validated_data['re_audit_date'] = validate_date(
        compliance_data.get('re_audit_date', ''), 
        field_name="Re-audit Date", allow_none=True
    )
    
    # Validate selected risks and mitigations as lists
    selected_risks = compliance_data.get('selected_risks', [])
    if not isinstance(selected_risks, list):
        raise ValidationError("Selected risks must be a list")
    validated_data['selected_risks'] = selected_risks
    
    selected_mitigations = compliance_data.get('selected_mitigations', [])
    if not isinstance(selected_mitigations, list):
        raise ValidationError("Selected mitigations must be a list")
    validated_data['selected_mitigations'] = selected_mitigations
    
    return validated_data

def validate_audit_version_data(data):
    """Validate audit version save data"""
    if not isinstance(data, dict):
        raise ValidationError("Audit version data must be a dictionary")
    
    validated_data = {}
    
    # Validate user ID
    validated_data['user_id'] = validate_int(
        data.get('user_id', 1050), 
        min_value=1, field_name="User ID"
    )
    
    # Validate compliances data
    compliances = data.get('compliances', {})
    if not isinstance(compliances, dict):
        raise ValidationError("Compliances must be a dictionary")
    
    validated_compliances = {}
    for compliance_id, compliance_data in compliances.items():
        # Validate compliance ID
        validated_id = validate_int(compliance_id, min_value=1, field_name="Compliance ID")
        validated_compliances[str(validated_id)] = validate_compliance_data(compliance_data)
    
    validated_data['compliances'] = validated_compliances
    
    # Validate audit evidence URLs
    validated_data['audit_evidence_urls'] = validate_string(
        data.get('audit_evidence_urls', ''), 
        min_length=0, max_length=5000, field_name="Audit Evidence URLs", allow_none=True
    )
    
    # Validate audit metadata
    # validated_data['audit_title'] = validate_string(
    #     data.get('audit_title', ''), 
    #     min_length=0, max_length=200, field_name="Audit Title", allow_none=True
    # )
    
    validated_data['audit_scope'] = validate_string(
        data.get('audit_scope', ''), 
        min_length=0, max_length=1000, field_name="Audit Scope", allow_none=True
    )
    
    validated_data['audit_objective'] = validate_string(
        data.get('audit_objective', ''), 
        min_length=0, max_length=1000, field_name="Audit Objective", allow_none=True
    )
    
    # validated_data['business_unit'] = validate_string(
    #     data.get('business_unit', ''), 
    #     min_length=0, max_length=100, field_name="Business Unit", allow_none=True
    # )
    
    validated_data['overall_comments'] = validate_string(
        data.get('overall_comments', ''), 
        min_length=0, max_length=5000, field_name="Overall Comments", allow_none=True
    )
    
    return validated_data

def validate_new_compliance_data(data):
    """Validate new compliance creation data"""
    if not isinstance(data, dict):
        raise ValidationError("Compliance data must be a dictionary")
    
    validated_data = {}
    
    # Required fields
    validated_data['identifier'] = validate_string(
        data.get('identifier'), min_length=1, max_length=100, field_name="Identifier"
    )
    
    validated_data['complianceTitle'] = validate_string(
        data.get('complianceTitle'), min_length=1, max_length=200, field_name="Compliance Title"
    )
    
    validated_data['complianceItemDescription'] = validate_string(
        data.get('complianceItemDescription'), min_length=1, max_length=2000, field_name="Compliance Description"
    )
    
    validated_data['complianceType'] = validate_string(
        data.get('complianceType'), min_length=1, max_length=100, field_name="Compliance Type"
    )
    
    validated_data['scope'] = validate_string(
        data.get('scope'), min_length=1, max_length=500, field_name="Scope"
    )
    
    validated_data['objective'] = validate_string(
        data.get('objective'), min_length=1, max_length=1000, field_name="Objective"
    )
    
    # Optional fields
    validated_data['impact'] = validate_string(
        data.get('impact', ''), min_length=0, max_length=1000, field_name="Impact", allow_none=True
    )
    
    validated_data['isRisk'] = validate_int(
        data.get('isRisk', 0), min_value=0, max_value=1, field_name="Is Risk"
    )
    
    validated_data['possibleDamage'] = validate_string(
        data.get('possibleDamage', ''), min_length=0, max_length=1000, field_name="Possible Damage", allow_none=True
    )
    
    validated_data['mitigation'] = validate_string(
        data.get('mitigation', ''), min_length=0, max_length=1000, field_name="Mitigation", allow_none=True
    )
    
    # Validate criticality and probability
    allowed_criticality = ['high', 'medium', 'low']
    criticality = data.get('criticality', 'medium')
    if criticality not in allowed_criticality:
        raise ValidationError("Criticality must be 'high', 'medium', or 'low'")
    validated_data['criticality'] = criticality
    
    allowed_probability = ['high', 'medium', 'low']
    probability = data.get('probability', 'medium')
    if probability not in allowed_probability:
        raise ValidationError("Probability must be 'high', 'medium', or 'low'")
    validated_data['probability'] = probability
    
    return validated_data

def validate_audit_data(data):
    """Validate audit creation data"""
    errors = {}
    
    try:
        # Required fields
        title = validate_string(data.get('title'), min_length=3, max_length=200, field_name="Title")
        scope = validate_string(data.get('scope'), min_length=10, max_length=1000, field_name="Scope")
        objective = validate_string(data.get('objective'), min_length=10, max_length=1000, field_name="Objective")
        business_unit = validate_string(data.get('business_unit'), min_length=2, max_length=100, field_name="Business Unit")
        role = validate_string(data.get('role'), min_length=2, max_length=100, field_name="Role")
        responsibility = validate_string(data.get('responsibility'), min_length=10, max_length=500, field_name="Responsibility")
        
        # Validate IDs
        framework_id = validate_int(data.get('framework_id'), min_value=1, field_name="Framework ID")
        reviewer = validate_int(data.get('reviewer'), min_value=1, field_name="Reviewer ID")
        
        # Optional IDs
        policy_id = validate_int(data.get('policy_id'), min_value=1, field_name="Policy ID", allow_none=True)
        subpolicy_id = validate_int(data.get('subpolicy_id'), min_value=1, field_name="SubPolicy ID", allow_none=True)
        
        # Team members validation
        team_members = data.get('team_members', [])
        if not isinstance(team_members, list) or not team_members:
            raise ValidationError("At least one team member is required")
            
        validated_members = []
        for member in team_members:
            validated_member = validate_int(member, min_value=1, field_name="Team Member ID")
            validated_members.append(validated_member)
            
        # Other fields
        due_date = validate_date(data.get('due_date'), field_name="Due Date", check_future=True, check_past=True)
        frequency = validate_frequency(data.get('frequency'))
        audit_type = validate_audit_type(data.get('audit_type'))
        
        # Return validated data
        return {
            'title': title,
            'scope': scope,
            'objective': objective,
            'business_unit': business_unit,
            'role': role,
            'responsibility': responsibility,
            'framework_id': framework_id,
            'reviewer': reviewer,
            'policy_id': policy_id,
            'subpolicy_id': subpolicy_id,
            'team_members': validated_members,
            'due_date': due_date,
            'frequency': frequency,
            'audit_type': audit_type
        }
        
    except ValidationError as e:
        errors['validation_error'] = str(e)
        raise ValidationError(errors)

from datetime import date, time, datetime
from typing import Any, Dict, List, Optional


class ValidationError(Exception):
    """
    Custom exception for validation errors.
    Supports both legacy (message only) and modern (field, message) formats.
    """
    def __init__(self, *args, **kwargs):
        if len(args) == 2:
            self.field = args[0]
            self.message = args[1]
            super().__init__(f"{self.field}: {self.message}")
        elif len(args) == 1:
            self.field = "field"
            self.message = args[0]
            super().__init__(self.message)
        else:
            self.field = kwargs.get('field', 'field')
            self.message = kwargs.get('message', 'Invalid input')
            super().__init__(self.message)

def clamp_int(value: Any, min_val: int, max_val: int, default: int = 0) -> int:
    """Clamp an integer value between min and max. Returns default if parsing fails."""
    try:
        if value is None or value == '':
            return default
        val = int(value)
        return max(min_val, min(val, max_val))
    except (ValueError, TypeError):
        return default

def validate_numeric_input(value: Any, min_val: int = 1, max_val: int = 1000, field_name: str = "field") -> int:
    """Validate numeric input and raise ValidationError if out of range or invalid."""
    try:
        if value is None or value == '':
            raise ValidationError(field_name, "is required")
        val = int(value)
        if val < min_val:
            raise ValidationError(field_name, f"must be at least {min_val}")
        if val > max_val:
            raise ValidationError(field_name, f"cannot exceed {max_val}")
        return val
    except (ValueError, TypeError):
        raise ValidationError(field_name, "must be a valid integer")
 


class SecureValidator:
    """
    Centralized validator class implementing allow-list validation pattern
    All inputs are rejected unless explicitly allowed
    """
    
    # Define allowed character patterns
    ALPHANUMERIC_ONLY = r'^[a-zA-Z0-9]+$'
    ALPHANUMERIC_WITH_SPACES = r'^[a-zA-Z0-9\s\-_.,!?()]+$'
    BUSINESS_TEXT_PATTERN = r'^[a-zA-Z0-9\s\-_.,!?():;/\\@#$%&*+=<>[\]{}|~`"\']+$'
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    CURRENCY_PATTERN = r'^[$£€]?[0-9]+(\.[0-9]{1,2})?$'
    PHONE_PATTERN = r'^\+?[1-9]\d{1,14}$'  # E.164 international format
    URL_PATTERN = r'^https?://[^\s/$.?#].[^\s]*$'

    # Predefined choice lists
    INCIDENT_PRIORITIES = ['Critical', 'High', 'Medium', 'Low']
    INCIDENT_ORIGINS = ['Manual', 'Audit Finding', 'System Generated']
    INCIDENT_STATUSES = [
        'Open',
        'Closed',
        'In Progress',
        'Scheduled',
        'Under Review',
        'Pending Review',
        'Rejected',
        'Assigned',
    ]
    INCIDENT_CLASSIFICATIONS = ['NonConformance', 'Control GAP', 'Risk', 'Issue']
    CRITICALITY_LEVELS = ['Critical', 'High', 'Medium', 'Low']

    # Questionnaire validation choices
    IMPACT_SCALES = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
    YES_NO_MAYBE_CHOICES = ['yes', 'no', 'maybe']
    YES_NO_PARTIAL_CHOICES = ['yes', 'no', 'partially']

    # Enhanced patterns for questionnaire
    NUMERIC_HOURS_PATTERN = r'^[0-9]+(\.[0-9]{1,2})?$'  # For hours (allows decimals)
    CURRENCY_AMOUNT_PATTERN = r'^[0-9]+(\.[0-9]{1,2})?$'  # For currency amounts (no symbols)
    
    @staticmethod
    def validate_string(value: Any, field_name: str, max_length: int = 255, 
                       min_length: int = 0, required: bool = False, 
                       allowed_pattern: Optional[str] = None) -> Optional[str]:
        """Validate string with comprehensive allow-list checks"""
        
        # Handle None/empty values
        if value is None or value == '':
            if required:
                raise ValidationError(field_name, "This field is required")
            return None
        
        # Type validation
        if not isinstance(value, str):
            raise ValidationError(field_name, f"Must be a string, got {type(value).__name__}")
        
        # Trim whitespace
        cleaned_value = value.strip()
        
        # Length validation
        if len(cleaned_value) < min_length:
            raise ValidationError(field_name, f"Must be at least {min_length} characters")
        
        if len(cleaned_value) > max_length:
            raise ValidationError(field_name, f"Must be no more than {max_length} characters")
        
        # Pattern validation (allow-list approach)
        if allowed_pattern and not re.match(allowed_pattern, cleaned_value):
            raise ValidationError(field_name, "Contains invalid or potentially dangerous characters")
        
        return cleaned_value

    @staticmethod
    def validate_trusted_url(
        value: Any,
        field_name: str,
        *,
        allowed_hosts: Optional[List[str]] = None,
        allowed_host_suffixes: Optional[List[str]] = None,
        allow_fragment_prefixes: Optional[List[str]] = None,
        allow_relative: bool = False,
        allow_http_hosts: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Validate a security-critical URL that will be rendered/embedded by the UI.

        Allow-list based:
        - Only http/https URLs are accepted (https required unless host is explicitly allow-listed for http)
        - Host must match an allow-listed host or suffix
        - Optionally allow internal fragment identifiers like '#linked-event-...'
        """
        if value is None or value == "":
            return None

        if not isinstance(value, str):
            raise ValidationError(field_name, "must be a string URL")

        v = value.strip()
        if v == "":
            return None

        # Allow internal application placeholders (never network-fetched)
        if allow_fragment_prefixes:
            for prefix in allow_fragment_prefixes:
                if v.startswith(prefix):
                    return v

        if allow_relative and v.startswith("/"):
            return v

        try:
            parts = urlsplit(v)
        except Exception:
            raise ValidationError(field_name, "must be a valid URL")

        scheme = (parts.scheme or "").lower()
        host = (parts.hostname or "").lower()

        if scheme not in ("http", "https"):
            raise ValidationError(field_name, "URL scheme must be http or https")

        if not host:
            raise ValidationError(field_name, "URL host is required")

        # Reject credentials in URLs: https://user:pass@host/...
        if parts.username or parts.password:
            raise ValidationError(field_name, "URL must not contain credentials")

        allowed_hosts_norm = {(h or "").strip().lower() for h in (allowed_hosts or []) if (h or "").strip()}
        allowed_suffixes_norm = {
            (s or "").strip().lower().lstrip(".")
            for s in (allowed_host_suffixes or [])
            if (s or "").strip()
        }
        allow_http_hosts_norm = {
            (h or "").strip().lower()
            for h in (allow_http_hosts or [])
            if (h or "").strip()
        }

        def _host_allowed(h: str) -> bool:
            if h in allowed_hosts_norm:
                return True
            for suffix in allowed_suffixes_norm:
                if h == suffix or h.endswith("." + suffix):
                    return True
            return False

        if not _host_allowed(host):
            raise ValidationError(field_name, f"host '{host}' is not in the allow-list")

        if scheme == "http" and host not in allow_http_hosts_norm:
            raise ValidationError(field_name, "only https URLs are allowed for this host")

        return v

    @staticmethod
    def validate_choice(value: Any, field_name: str, choices: List[str],
                        required: bool = False) -> Optional[str]:
        """Validate that value is from allowed choices (strict allow-list)"""

        if value is None or value == '':
            if required:
                raise ValidationError(field_name, "This field is required")
            return None

        if not isinstance(value, str):
            raise ValidationError(field_name, f"Must be a string, got {type(value).__name__}")

        # Strict allow-list validation
        if value not in choices:
            raise ValidationError(field_name, f"Must be one of: {', '.join(choices)}")

        return value

    @staticmethod
    def validate_integer(
        value: Any,
        field_name: str,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        required: bool = False,
    ) -> Optional[int]:
        """Validate integer with range checks"""

        if value is None or value == '':
            if required:
                raise ValidationError(field_name, "This field is required")
            return None

        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Must be a valid integer")

        if min_value is not None and int_value < min_value:
            raise ValidationError(field_name, f"Must be at least {min_value}")

        if max_value is not None and int_value > max_value:
            raise ValidationError(field_name, f"Must be no more than {max_value}")

        return int_value

    @staticmethod
    def validate_currency(value: Any, field_name: str, required: bool = False) -> Optional[str]:
        """Validate currency amount"""

        if value is None or value == '':
            if required:
                raise ValidationError(field_name, "This field is required")
            return None

        currency_str = str(value).strip()
        if not re.match(SecureValidator.CURRENCY_PATTERN, currency_str):
            raise ValidationError(
                field_name,
                "Must be a valid currency amount (e.g., $100.50, 250.75)",
            )

        return currency_str

    @staticmethod
    def validate_currency_amount(
        value: Any, field_name: str, required: bool = False
    ) -> Optional[str]:
        """Validate currency amount without currency symbols (for questionnaire)"""

        if value is None or value == '':
            if required:
                raise ValidationError(field_name, "This field is required")
            return None

        amount_str = str(value).strip()
        if not re.match(SecureValidator.CURRENCY_AMOUNT_PATTERN, amount_str):
            raise ValidationError(
                field_name,
                "Must be a valid numeric amount (e.g., 100.50, 250)",
            )

        # Additional validation: check reasonable range
        try:
            amount_float = float(amount_str)
            if amount_float < 0:
                raise ValidationError(field_name, "Amount cannot be negative")
            if amount_float > 999999999.99:  # 1 billion limit
                raise ValidationError(field_name, "Amount exceeds maximum allowed value")
        except ValueError:
            raise ValidationError(field_name, "Must be a valid numeric amount")

        return amount_str

    @staticmethod
    def validate_hours(value: Any, field_name: str, required: bool = False) -> Optional[str]:
        """Validate hours (numeric with up to 2 decimal places)"""

        if value is None or value == '':
            if required:
                raise ValidationError(field_name, "This field is required")
            return None

        hours_str = str(value).strip()
        if not re.match(SecureValidator.NUMERIC_HOURS_PATTERN, hours_str):
            raise ValidationError(
                field_name,
                "Must be a valid number of hours (e.g., 8, 24.5)",
            )

        # Additional validation: check reasonable range
        try:
            hours_float = float(hours_str)
            if hours_float < 0:
                raise ValidationError(field_name, "Hours cannot be negative")
            if hours_float > 8760:  # 1 year in hours
                raise ValidationError(
                    field_name,
                    "Hours exceeds reasonable maximum (8760 hours = 1 year)",
                )
        except ValueError:
            raise ValidationError(field_name, "Must be a valid number of hours")

        return hours_str

    @staticmethod
    def validate_impact_scale(
        value: Any, field_name: str, required: bool = False
    ) -> Optional[str]:
        """Validate impact scale selection"""

        if value is None or value == '':
            if required:
                raise ValidationError(field_name, "This field is required")
            return None

        return SecureValidator.validate_choice(
            value,
            field_name,
            SecureValidator.IMPACT_SCALES,
            required,
        )

    @staticmethod
    def validate_date(value: Any, field_name: str, required: bool = False) -> Optional[date]:
        """Validate date format"""

        if value is None or value == '':
            if required:
                raise ValidationError(field_name, "This field is required")
            return None

        if isinstance(value, date):
            return value

        try:
            if isinstance(value, str):
                # Try ISO format YYYY-MM-DD
                parts = value.split('-')
                if len(parts) == 3:
                    year, month, day = map(int, parts)
                    return date(year, month, day)

            raise ValidationError(field_name, "Invalid date format, expected YYYY-MM-DD")
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Invalid date format, expected YYYY-MM-DD")

    @staticmethod
    def validate_time(value: Any, field_name: str, required: bool = False) -> Optional[time]:
        """Validate time format"""

        if value is None or value == '':
            if required:
                raise ValidationError(field_name, "This field is required")
            return None

        if isinstance(value, time):
            return value

        try:
            if isinstance(value, str):
                # Try ISO format HH:MM or HH:MM:SS
                parts = value.split(':')
                if len(parts) >= 2:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    second = int(parts[2]) if len(parts) > 2 else 0
                    return time(hour, minute, second)

            raise ValidationError(field_name, "Invalid time format, expected HH:MM or HH:MM:SS")
        except (ValueError, TypeError):
            raise ValidationError(field_name, "Invalid time format, expected HH:MM or HH:MM:SS")


def sanitize_mitigation_evidence_urls(
    assessment_data: Dict[str, Any],
    *,
    allowed_hosts: Optional[List[str]] = None,
    allowed_host_suffixes: Optional[List[str]] = None,
    allow_http_hosts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Framework-level sanitization for mitigation evidence URLs.

    This prevents attacker-controlled URLs (e.g. in 'aws-file_link') from being stored and later rendered
    as iframe/src or clickable links. It validates:
    - legacy mitigation['aws-file_link']
    - each mitigation.files[*]['aws-file_link']
    """
    if not isinstance(assessment_data, dict):
        return assessment_data

    mitigations = assessment_data.get("mitigations")
    if not isinstance(mitigations, dict):
        return assessment_data

    sanitized = assessment_data.copy()
    sanitized_mitigations = {}

    for mitigation_key, mitigation_data in mitigations.items():
        if not isinstance(mitigation_data, dict):
            sanitized_mitigations[mitigation_key] = mitigation_data
            continue

        m = mitigation_data.copy()

        # Validate files array (preferred format)
        files = m.get("files", [])
        if isinstance(files, list):
            new_files = []
            for idx, f in enumerate(files):
                if not isinstance(f, dict):
                    new_files.append(f)
                    continue
                f2 = f.copy()
                if "aws-file_link" in f2 and f2.get("aws-file_link"):
                    f2["aws-file_link"] = SecureValidator.validate_trusted_url(
                        f2.get("aws-file_link"),
                        f"mitigations[{mitigation_key}].files[{idx}].aws-file_link",
                        allowed_hosts=allowed_hosts,
                        allowed_host_suffixes=allowed_host_suffixes,
                        allow_fragment_prefixes=["#linked-event-"],
                        allow_http_hosts=allow_http_hosts,
                    )
                new_files.append(f2)
            m["files"] = new_files

        # Validate legacy single-field URL if present
        if "aws-file_link" in m and m.get("aws-file_link"):
            m["aws-file_link"] = SecureValidator.validate_trusted_url(
                m.get("aws-file_link"),
                f"mitigations[{mitigation_key}].aws-file_link",
                allowed_hosts=allowed_hosts,
                allowed_host_suffixes=allowed_host_suffixes,
                allow_fragment_prefixes=["#linked-event-"],
                allow_http_hosts=allow_http_hosts,
            )

        sanitized_mitigations[mitigation_key] = m

    sanitized["mitigations"] = sanitized_mitigations
    return sanitized


class IncidentValidator:
    """Specialized validator for incident data using SecureValidator"""
    
    @staticmethod
    def validate_incident_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        comprehensive incident validation with strict allow-list pattern
        Returns cleaned data or raises ValidationError
        """
        validated_data = {}
        validator = SecureValidator()
        
        # Required fields
        validated_data['IncidentTitle'] = validator.validate_string(
            data.get('IncidentTitle'), 'IncidentTitle', 
            max_length=255, min_length=3, required=True,
            allowed_pattern=validator.BUSINESS_TEXT_PATTERN
        )
        
        validated_data['Description'] = validator.validate_string(
            data.get('Description'), 'Description',
            max_length=2000, min_length=10, required=True,
            allowed_pattern=validator.BUSINESS_TEXT_PATTERN
        )
        
        validated_data['Date'] = validator.validate_date(
            data.get('Date'), 'Date', required=True
        )
        
        validated_data['Time'] = validator.validate_time(
            data.get('Time'), 'Time', required=True
        )
        
        validated_data['RiskPriority'] = validator.validate_choice(
            data.get('RiskPriority'), 'RiskPriority',
            choices=validator.INCIDENT_PRIORITIES, required=True
        )
        
        # Optional fields with strict validation
        if 'Origin' in data and data.get('Origin'):
            validated_data['Origin'] = validator.validate_choice(
                data.get('Origin'), 'Origin',
                choices=validator.INCIDENT_ORIGINS
            )
        
        if 'Status' in data and data.get('Status'):
            validated_data['Status'] = validator.validate_choice(
                data.get('Status'), 'Status',
                choices=validator.INCIDENT_STATUSES
            )
        
        if 'Criticality' in data and data.get('Criticality'):
            validated_data['Criticality'] = validator.validate_choice(
                data.get('Criticality'), 'Criticality',
                choices=validator.CRITICALITY_LEVELS
            )
        
        if 'IncidentClassification' in data and data.get('IncidentClassification'):
            validated_data['IncidentClassification'] = validator.validate_choice(
                data.get('IncidentClassification'), 'IncidentClassification',
                choices=validator.INCIDENT_CLASSIFICATIONS
            )
        
        # Text fields with length and pattern validation
        text_fields = [
            ('Mitigation', 2000), ('Comments', 1000), ('RiskCategory', 500),
            ('InitialImpactAssessment', 2000), ('InternalContacts', 500),
            ('ExternalPartiesInvolved', 500), ('RegulatoryBodies', 500),
            ('RelevantPoliciesProceduresViolated', 1000), ('ControlFailures', 1000),
            ('PossibleDamage', 1000)
        ]
        
        for field_name, max_length in text_fields:
            if field_name in data and data.get(field_name):
                validated_data[field_name] = validator.validate_string(
                    data.get(field_name), field_name,
                    max_length=max_length,
                    allowed_pattern=validator.BUSINESS_TEXT_PATTERN
                )
        
        # Simple alphanumeric fields
        simple_fields = [
            ('AffectedBusinessUnit', 100), ('GeographicLocation', 100),
            ('SystemsAssetsInvolved', 500)
        ]
        
        for field_name, max_length in simple_fields:
            if field_name in data and data.get(field_name):
                validated_data[field_name] = validator.validate_string(
                    data.get(field_name), field_name,
                    max_length=max_length,
                    allowed_pattern=validator.ALPHANUMERIC_WITH_SPACES
                )
        
        # Currency validation
        if 'CostOfIncident' in data and data.get('CostOfIncident'):
            validated_data['CostOfIncident'] = validator.validate_currency(
                data.get('CostOfIncident'), 'CostOfIncident'
            )
        
        # ComplianceId validation - must be positive integer
        if 'ComplianceId' in data and data.get('ComplianceId'):
            validated_data['ComplianceId'] = validator.validate_integer(
                data.get('ComplianceId'), 'ComplianceId', min_value=1
            )
        
        return validated_data


class QuestionnaireValidator:
    """Specialized validator for incident assessment questionnaire data"""
    
    @staticmethod
    def validate_questionnaire_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive questionnaire validation with strict allow-list pattern
        All fields are optional but must pass validation if provided
        Returns cleaned data or raises ValidationError
        """
        validated_data = {}
        validator = SecureValidator()
        
        # Cost validation (currency amount)
        if 'cost' in data and data.get('cost'):
            validated_data['cost'] = validator.validate_currency_amount(
                data.get('cost'), 'cost', required=False
            )
        
        # Impact validation (scale)
        if 'impact' in data and data.get('impact'):
            validated_data['impact'] = validator.validate_impact_scale(
                data.get('impact'), 'impact', required=False
            )
        
        # Financial Impact validation (scale)
        if 'financialImpact' in data and data.get('financialImpact'):
            validated_data['financialImpact'] = validator.validate_impact_scale(
                data.get('financialImpact'), 'financialImpact', required=False
            )
        
        # Financial Loss validation (currency amount)
        if 'financialLoss' in data and data.get('financialLoss'):
            validated_data['financialLoss'] = validator.validate_currency_amount(
                data.get('financialLoss'), 'financialLoss', required=False
            )
        
        # Reputational Impact validation (impact scale)
        if 'reputationalImpact' in data and data.get('reputationalImpact'):
            validated_data['reputationalImpact'] = validator.validate_impact_scale(
                data.get('reputationalImpact'), 'reputationalImpact', required=False
            )
        
        # Operational Impact validation (impact scale)
        if 'operationalImpact' in data and data.get('operationalImpact'):
            validated_data['operationalImpact'] = validator.validate_impact_scale(
                data.get('operationalImpact'), 'operationalImpact', required=False
            )
        
        # System Downtime validation (hours)
        if 'systemDowntime' in data and data.get('systemDowntime'):
            validated_data['systemDowntime'] = validator.validate_hours(
                data.get('systemDowntime'), 'systemDowntime', required=False
            )
        
        # Recovery Time validation (hours)
        if 'recoveryTime' in data and data.get('recoveryTime'):
            validated_data['recoveryTime'] = validator.validate_hours(
                data.get('recoveryTime'), 'recoveryTime', required=False
            )
        
        # Risk Recurrence validation (yes/no/maybe)
        if 'riskRecurrence' in data and data.get('riskRecurrence'):
            validated_data['riskRecurrence'] = validator.validate_choice(
                data.get('riskRecurrence'), 'riskRecurrence',
                choices=validator.YES_NO_MAYBE_CHOICES, required=False
            )
        
        # Improvement Initiative validation (yes/no/partially)
        if 'improvementInitiative' in data and data.get('improvementInitiative'):
            validated_data['improvementInitiative'] = validator.validate_choice(
                data.get('improvementInitiative'), 'improvementInitiative',
                choices=validator.YES_NO_PARTIAL_CHOICES, required=False
            )
        
        return validated_data 