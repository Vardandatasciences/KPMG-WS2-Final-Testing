import requests
from django.utils import timezone

LOGGING_SERVICE_URL = None  # Disabled external logging service

def send_log(module, actionType, description=None, userId=None, userName=None,
             userRole=None, entityType=None, logLevel='INFO', ipAddress=None,
             additionalInfo=None, entityId=None, frameworkId=None):
    from ...models import GRCLog, Framework  # Lazy import to avoid circular import
    from .data_masking import mask_log_data, get_masking_service
    
    # Create log entry in database
    try:
        # Prepare data for GRCLog model
        log_data = {
            'Module': module,
            'ActionType': actionType,
            'Description': description,
            'UserId': userId,
            'UserName': userName,
            'EntityType': entityType,
            'EntityId': entityId,
            'LogLevel': logLevel,
            'IPAddress': ipAddress,
            'AdditionalInfo': additionalInfo
        }
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Mask sensitive data before saving
        masked_log_data = mask_log_data(log_data)
        
        # Get framework if not provided (required field)
        framework = None
        if frameworkId:
            try:
                framework = Framework.objects.get(FrameworkId=frameworkId)
            except Framework.DoesNotExist:
                framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
        else:
            framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
        
        if not framework:
            framework = Framework.objects.first()
        
        # Add framework to log data (required field)
        if framework:
            masked_log_data['FrameworkId'] = framework
        else:
            # If no framework exists, we can't create the log
            print(f"Warning: No framework found for log entry. Module: {module}, ActionType: {actionType}")
            return None
        
        # Create and save the log entry
        log_entry = GRCLog(**masked_log_data)
        log_entry.save()
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
                    print(f"Failed to send log to service: {response.text}")
        except Exception as e:
            print(f"Error sending log to service: {str(e)}")
        return log_entry.LogId  # Return the ID of the created log
    except Exception as e:
        print(f"Error saving log to database: {str(e)}")
        # Try to capture the error itself
        try:
            from ...models import GRCLog
            error_log = GRCLog(
                Module=module,
                ActionType='LOG_ERROR',
                Description=f"Error logging {actionType} on {module}: {str(e)}",
                LogLevel='ERROR'
            )
            error_log.save()
        except:
            pass  # If we can't even log the error, just continue
        return None 