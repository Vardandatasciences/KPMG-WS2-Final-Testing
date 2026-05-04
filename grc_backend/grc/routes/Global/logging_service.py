import requests
import logging
from django.utils import timezone

from ...utils.log_sanitize import sanitize_for_log

logger = logging.getLogger(__name__)

LOGGING_SERVICE_URL = None  # Disabled external logging service

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    
    # Sanitize IP: remove port if present, truncate to 45 chars
    if ip and ip != 'unknown':
        # Remove port number if present (IPv4 only, not IPv6)
        if ':' in ip and not ip.startswith('['):
            parts = ip.split(':')
            if len(parts) == 2 and '.' in parts[0]:
                ip = parts[0]
        # Truncate to max 45 characters
        ip = ip[:45] if len(ip) > 45 else ip
    
    return ip

def send_log(module, actionType, description=None, userId=None, userName=None,
             userRole=None, entityType=None, logLevel='INFO', ipAddress=None,
             additionalInfo=None, entityId=None, frameworkId=None):
    from ...models import GRCLog, Framework  # Lazy import to avoid circular import
    from .data_masking import mask_log_data, get_masking_service
    from django.db.utils import ProgrammingError
    
    # Create log entry in database
    try:
        # Ensure userId is numeric (not encrypted) - UserId field should store plain numeric ID
        # RBACUtils.get_user_id_from_request returns numeric user ID, so just convert to string
        numeric_user_id = None
        if userId:
            try:
                # Convert to int first to ensure it's numeric, then to string
                if isinstance(userId, int):
                    numeric_user_id = str(userId)
                elif isinstance(userId, str):
                    # Try to convert to int to validate it's numeric
                    try:
                        int_val = int(userId)
                        numeric_user_id = str(int_val)
                    except (ValueError, TypeError):
                        # If it's not numeric, skip UserId (don't save encrypted values)
                        numeric_user_id = None
                else:
                    # For other types, try to convert to string then int
                    try:
                        int_val = int(str(userId))
                        numeric_user_id = str(int_val)
                    except (ValueError, TypeError):
                        numeric_user_id = None
            except Exception as e:
                logger.warning(f"Error processing userId: {e}")
                numeric_user_id = None
        
        is_routine_request_log = actionType == 'GET_REQUEST' and module == 'System'
        if not is_routine_request_log:
            logger.debug(
                "send_log called: module=%s, actionType=%s, userId=%s, numeric_user_id=%s, frameworkId=%s",
                sanitize_for_log(module, 128),
                sanitize_for_log(actionType, 128),
                sanitize_for_log(userId, 64),
                sanitize_for_log(numeric_user_id, 64),
                sanitize_for_log(frameworkId, 64),
            )
        # Prepare data for GRCLog model
        log_data = {
            'Module': module,
            'ActionType': actionType,
            'Description': description,
            'UserId': numeric_user_id,
            'UserName': userName,
            'EntityType': entityType,
            'EntityId': entityId,
            'LogLevel': logLevel,
            'IPAddress': ipAddress,
            'AdditionalInfo': additionalInfo,
        }
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Mask sensitive data before saving (but NOT for authentication and security-critical logs)
        # Authentication logs and password-related logs should keep UserName and UserId unmasked for audit purposes
        skip_masking = False
        if module == 'Authentication' and actionType in ['LOGIN', 'LOGOUT', 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGIN_ANOMALY', 'PASSWORD_RESET']:
            skip_masking = True
            logger.debug("Skipping masking for authentication log: %s", sanitize_for_log(actionType, 128))
        elif module == 'User Profile' and actionType in ['PASSWORD_UPDATE', 'PASSWORD_RESET', 'PASSWORD_CHANGE']:
            skip_masking = True
            logger.debug("Skipping masking for password-related log: %s", sanitize_for_log(actionType, 128))
        
        if skip_masking:
            # Don't mask security-critical logs - we need to know who performed the action
            masked_log_data = log_data
        else:
            masked_log_data = mask_log_data(log_data)
        
        # Get framework if not provided (required field)
        framework = None
        if frameworkId:
            try:
                framework = Framework.objects.get(FrameworkId=frameworkId)
                if not is_routine_request_log:
                    logger.debug("Found framework by ID: %s", sanitize_for_log(frameworkId, 64))
            except Framework.DoesNotExist:
                logger.warning(f"Framework {frameworkId} not found, using fallback")
                framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
        else:
            if not is_routine_request_log:
                logger.debug("No frameworkId provided, searching for approved active framework")
            framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
        
        if not framework:
            if not is_routine_request_log:
                logger.debug("No approved active framework found, using first available")
            framework = Framework.objects.first()
        
        # Add framework to log data (required field)
        # CRITICAL: We must have a framework to save the log. If none exists, create a log entry anyway
        # by using the first available framework or logging an error
        if framework:
            masked_log_data['FrameworkId'] = framework
            if not is_routine_request_log:
                logger.debug(
                    "Using framework ID: %s Name: %s",
                    sanitize_for_log(framework.FrameworkId, 64),
                    sanitize_for_log(framework.FrameworkName, 256),
                )
        else:
            # Last resort: Try to get ANY framework, even if inactive
            try:
                framework = Framework.objects.all().first()
                if framework:
                    masked_log_data['FrameworkId'] = framework
                    logger.warning(
                        "Using fallback framework %s for log entry. Module: %s ActionType: %s",
                        sanitize_for_log(framework.FrameworkId, 64),
                        sanitize_for_log(module, 128),
                        sanitize_for_log(actionType, 128),
                    )
                else:
                    # If absolutely no framework exists, we cannot save the log
                    logger.error(
                        "ERROR: No framework exists in database. Cannot save log entry. Module: %s ActionType: %s",
                        sanitize_for_log(module, 128),
                        sanitize_for_log(actionType, 128),
                    )
                    return None
            except Exception as e:
                logger.exception(
                    "ERROR: Failed to get framework for log entry. Module: %s ActionType: %s",
                    sanitize_for_log(module, 128),
                    sanitize_for_log(actionType, 128),
                )
                return None
        
        # Create and save the log entry
        if not is_routine_request_log:
            logger.info(
                "Creating GRCLog entry: module=%s actionType=%s userId=%s frameworkId=%s",
                sanitize_for_log(module, 128),
                sanitize_for_log(actionType, 128),
                sanitize_for_log(numeric_user_id, 64),
                sanitize_for_log(framework.FrameworkId if framework else None, 64),
            )
            logger.debug("Creating GRCLog entry with data: %s", sanitize_for_log(str(masked_log_data), max_len=1500))
        # print(f"[SEND_LOG] Creating GRCLog: module={module}, actionType={actionType}, userId={numeric_user_id}, frameworkId={framework.FrameworkId if framework else None}")
        log_entry = GRCLog(**masked_log_data)
        log_entry.save()
        if not is_routine_request_log:
            logger.info(
                "Successfully saved log entry with ID: %s for %s on %s",
                sanitize_for_log(log_entry.LogId, 32),
                sanitize_for_log(actionType, 128),
                sanitize_for_log(module, 128),
            )
        # print(f"[SEND_LOG] ✅ SUCCESS - Saved log entry with ID: {log_entry.LogId} for {actionType} on {module}")
        
        # Optionally still send to logging service if needed
        try:
            if LOGGING_SERVICE_URL:
                # Format for external service (matches expected format in loggingservice.js)
                api_log_data = {
                    "module": module,
                    "actionType": actionType,  # This is exactly what the service expects
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
                response = requests.post(LOGGING_SERVICE_URL, json=api_log_data)
                if response.status_code != 200:
                    logger.warning("Failed to send log to service: %s", sanitize_for_log(response.text, 500))
        except Exception as e:
            logger.warning("Error sending log to service: %s", sanitize_for_log(e, 500))
        
        return log_entry.LogId  # Return the ID of the created log
    except Exception as e:
        logger.exception("Error saving log to database")
        # Do not try to save error to GRCLog here - the table may be missing ValueBefore/ValueAfter
        # and would cause a cascade of the same error.
        return None 