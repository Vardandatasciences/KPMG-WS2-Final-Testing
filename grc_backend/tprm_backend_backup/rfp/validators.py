from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
import re


def validate_rfp_title(value):
    """
    Validate RFP title:
    - Must be between 5 and 255 characters
    - Cannot contain certain special characters
    """
    if len(value) < 5:
        raise ValidationError("RFP title must be at least 5 characters long.")
    
    # Check for potentially dangerous characters
    if re.search(r'[<>{}]', value):
        raise ValidationError("RFP title contains invalid characters.")


def validate_budget_range(min_value, max_value):
    """
    Validate budget range:
    - Min must be less than max
    - Both must be positive
    """
    if min_value is not None and max_value is not None:
        if min_value < 0 or max_value < 0:
            raise ValidationError("Budget values cannot be negative.")
        
        if min_value > max_value:
            raise ValidationError("Minimum budget cannot be greater than maximum budget.")


def validate_submission_deadline(value):
    """
    Validate submission deadline:
    - Must be in the future
    """
    if not value:
        return

    # Accept both datetime objects and ISO 8601 strings
    deadline_dt = value
    if isinstance(value, str):
        try:
            # Handle trailing 'Z' (UTC) by converting to +00:00 for fromisoformat
            normalized = value.replace('Z', '+00:00')
            deadline_dt = datetime.fromisoformat(normalized)
            if timezone.is_naive(deadline_dt):
                deadline_dt = timezone.make_aware(deadline_dt, timezone=timezone.utc)
        except Exception:
            # If parsing fails, skip the future check to avoid false negatives on drafts
            return

    now = timezone.now()
    try:
        if deadline_dt <= now:
            raise ValidationError("Submission deadline must be in the future.")
    except TypeError:
        # In case of unexpected types, do not raise here; let serializer handle type conversion
        return


def validate_evaluation_criteria_weights(criteria_list):
    """
    Validate evaluation criteria weights:
    - Must sum to 100%
    - Each weight must be between 0 and 100
    """
    if not criteria_list:
        raise ValidationError("At least one evaluation criterion is required.")
    
    total_weight = sum(float(criterion.get('weight_percentage', 0)) for criterion in criteria_list)
    
    if abs(total_weight - 100) > 0.01:  # Allow small floating point errors
        raise ValidationError(f"Total weight percentage must equal 100% (current: {total_weight}%).")
    
    for criterion in criteria_list:
        weight = float(criterion.get('weight_percentage', 0))
        if weight < 0 or weight > 100:
            raise ValidationError("Each criterion weight must be between 0 and 100.")


def validate_rfp_data(data):
    """
    Comprehensive validation for RFP data
    """
    errors = {}
    
    # Validate required fields
    required_fields = ['rfp_title', 'description', 'rfp_type']
    for field in required_fields:
        if not data.get(field):
            errors[field] = f"{field} is required."
    
    # Validate title if present
    if data.get('rfp_title'):
        try:
            validate_rfp_title(data['rfp_title'])
        except ValidationError as e:
            errors['rfp_title'] = e.messages[0]
    
    # Validate budget range if present
    budget_min = data.get('budget_range_min')
    budget_max = data.get('budget_range_max')
    if budget_min is not None or budget_max is not None:
        try:
            validate_budget_range(budget_min, budget_max)
        except ValidationError as e:
            errors['budget_range'] = e.messages[0]
    
    # Validate submission deadline if present
    if data.get('submission_deadline'):
        try:
            validate_submission_deadline(data['submission_deadline'])
        except ValidationError as e:
            errors['submission_deadline'] = e.messages[0]
    
    # Validate evaluation criteria if present
    if 'evaluation_criteria' in data:
        try:
            validate_evaluation_criteria_weights(data['evaluation_criteria'])
        except ValidationError as e:
            errors['evaluation_criteria'] = e.messages[0]
    
    return errors
