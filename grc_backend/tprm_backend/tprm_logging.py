import requests
from django.utils import timezone
 
LOGGING_SERVICE_URL = None  # Disabled external logging service
 
def send_log(module, actionType, description=None, userId=None, userName=None,
             userRole=None, entityType=None, logLevel='INFO', ipAddress=None,
             additionalInfo=None, entityId=None):
    """
    Send log entry to grc_logs table
    
    Args:
        module: The module name (e.g., 'RFP', 'Vendor', 'Contract')
        actionType: The action type (e.g., 'CREATE', 'UPDATE', 'DELETE', 'VIEW')
        description: Description of the action
        userId: User ID performing the action
        userName: User name performing the action
        userRole: User role (optional, not stored in DB currently)
        entityType: Type of entity (e.g., 'RFP', 'Vendor', 'Contract')
        logLevel: Log level (default: 'INFO', options: 'INFO', 'WARNING', 'ERROR')
        ipAddress: IP address of the user
        additionalInfo: Additional information as dictionary (will be stored as JSON)
        entityId: ID of the entity being acted upon
        
    Returns:
        int: The log_id of the created log entry, or None if failed
    """
    from quick_access.models import GRCLog  # Import from quick_access app
    
    # Create log entry in database
    try:
        # Prepare data for GRCLog model (using snake_case field names)
        log_data = {
            'module': module,
            'action_type': actionType,
            'description': description or '',  # description is required in model
            'user_id': userId or '',  # user_id is required in model
            'user_name': userName or '',  # user_name is required in model
            'entity_type': entityType,
            'entity_id': entityId,
            'log_level': logLevel,
            'ip_address': ipAddress,
            'additional_info': additionalInfo if additionalInfo else {}
        }
        
        # Remove None values except for fields that have defaults
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Create and save the log entry
        log_entry = GRCLog.objects.create(**log_data)
        
        # Optionally still send to logging service if needed
        if LOGGING_SERVICE_URL:
            try:
                # Format for external service (matches expected format in loggingservice.js)
                api_log_data = {
                    "module": module,
                    "actionType": actionType,
                    "description": description,
                    "userId": userId,
                    "userName": userName,
                    "userRole": userRole,
                    "entityType": entityType,
                    "logLevel": logLevel,
                    "ipAddress": ipAddress,
                    "additionalInfo": additionalInfo
                }
                # Clean out None values
                api_log_data = {k: v for k, v in api_log_data.items() if v is not None}
                response = requests.post(LOGGING_SERVICE_URL, json=api_log_data, timeout=5)
                if response.status_code != 200:
                    print(f"Failed to send log to service: {response.text}")
            except Exception as e:
                print(f"Error sending log to service: {str(e)}")
        
        return log_entry.log_id  # Return the ID of the created log
        
    except Exception as e:
        print(f"Error saving log to database: {str(e)}")
        # Try to capture the error itself
        try:
            from quick_access.models import GRCLog
            error_log = GRCLog.objects.create(
                module=module,
                action_type='LOG_ERROR',
                description=f"Error logging {actionType} on {module}: {str(e)}",
                log_level='ERROR',
                user_id='',
                user_name='System'
            )
        except Exception as inner_e:
            print(f"Critical: Could not log error: {str(inner_e)}")
            pass  # If we can't even log the error, just continue
        return None


def get_client_ip(request):
    """
    Helper function to get client IP address from request
    
    Args:
        request: Django request object
        
    Returns:
        str: IP address of the client
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
 