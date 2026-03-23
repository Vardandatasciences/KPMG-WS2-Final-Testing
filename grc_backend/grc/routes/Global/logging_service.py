import requests
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

LOGGING_SERVICE_URL = None  # Disabled external logging service

def send_log(module, actionType, description=None, userId=None, userName=None,
             userRole=None, entityType=None, logLevel='INFO', ipAddress=None,
             additionalInfo=None, entityId=None, frameworkId=None,
             valueBefore=None, valueAfter=None):
    from ...models import GRCLog, Framework  # Lazy import to avoid circular import
    from .data_masking import mask_log_data, get_masking_service
    from django.db.utils import ProgrammingError
    
    # Create log entry in database
    try:
        logger.debug(f"send_log called: module={module}, actionType={actionType}, userId={userId}, frameworkId={frameworkId}")
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
            'AdditionalInfo': additionalInfo,
            'ValueBefore': valueBefore,
            'ValueAfter': valueAfter
        }
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        # Mask sensitive data before saving (but NOT for authentication and security-critical logs)
        # Authentication logs and password-related logs should keep UserName and UserId unmasked for audit purposes
        skip_masking = False
        if module == 'Authentication' and actionType in ['LOGIN', 'LOGOUT', 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'PASSWORD_RESET']:
            skip_masking = True
            logger.debug(f"Skipping masking for authentication log: {actionType}")
        elif module == 'User Profile' and actionType in ['PASSWORD_UPDATE', 'PASSWORD_RESET', 'PASSWORD_CHANGE']:
            skip_masking = True
            logger.debug(f"Skipping masking for password-related log: {actionType}")
        
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
                logger.debug(f"Found framework by ID: {frameworkId}")
            except Framework.DoesNotExist:
                logger.warning(f"Framework {frameworkId} not found, using fallback")
                framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
        else:
            logger.debug("No frameworkId provided, searching for approved active framework")
            framework = Framework.objects.filter(Status='Approved', ActiveInactive='Active').first()
        
        if not framework:
            logger.debug("No approved active framework found, using first available")
            framework = Framework.objects.first()
        
        # Add framework to log data (required field)
        # CRITICAL: We must have a framework to save the log. If none exists, create a log entry anyway
        # by using the first available framework or logging an error
        if framework:
            masked_log_data['FrameworkId'] = framework
            logger.debug(f"Using framework ID: {framework.FrameworkId}, Name: {framework.FrameworkName}")
        else:
            # Last resort: Try to get ANY framework, even if inactive
            try:
                framework = Framework.objects.all().first()
                if framework:
                    masked_log_data['FrameworkId'] = framework
                    logger.warning(f"Using fallback framework {framework.FrameworkId} for log entry. Module: {module}, ActionType: {actionType}")
                else:
                    # If absolutely no framework exists, we cannot save the log
                    logger.error(f"ERROR: No framework exists in database. Cannot save log entry. Module: {module}, ActionType: {actionType}")
                    return None
            except Exception as e:
                logger.error(f"ERROR: Failed to get framework for log entry: {str(e)}. Module: {module}, ActionType: {actionType}")
                import traceback
                logger.error(traceback.format_exc())
                return None
        
        # Create and save the log entry
        logger.debug(f"Creating GRCLog entry with data: {masked_log_data}")
        log_entry = None
        try:
            log_entry = GRCLog(**masked_log_data)
            log_entry.save()
        except ProgrammingError as e:
            # Handle older DB schemas missing ValueBefore/ValueAfter columns:
            # Django model has these fields so a simple retry still inserts them; use raw SQL instead.
            msg = str(e)
            if ("ValueBefore" in msg) or ("ValueAfter" in msg):
                masked_log_data.pop("ValueBefore", None)
                masked_log_data.pop("ValueAfter", None)
                from django.db import connection
                framework = masked_log_data.get("FrameworkId")
                if not framework:
                    raise
                framework_id = framework.pk if hasattr(framework, "pk") else framework
                cols = []
                vals = []
                if "Module" in masked_log_data:
                    cols.append("Module")
                    vals.append(masked_log_data["Module"])
                if "ActionType" in masked_log_data:
                    cols.append("ActionType")
                    vals.append(masked_log_data["ActionType"])
                if "Description" in masked_log_data:
                    cols.append("Description")
                    vals.append(masked_log_data["Description"])
                if "UserId" in masked_log_data:
                    cols.append("UserId")
                    vals.append(str(masked_log_data["UserId"])[:50] if masked_log_data["UserId"] is not None else None)
                if "UserName" in masked_log_data:
                    cols.append("UserName")
                    vals.append(str(masked_log_data["UserName"])[:500] if masked_log_data["UserName"] else None)
                if "EntityType" in masked_log_data:
                    cols.append("EntityType")
                    vals.append(masked_log_data["EntityType"])
                if "EntityId" in masked_log_data:
                    cols.append("EntityId")
                    vals.append(str(masked_log_data["EntityId"])[:50] if masked_log_data["EntityId"] else None)
                if "LogLevel" in masked_log_data:
                    cols.append("LogLevel")
                    vals.append(masked_log_data["LogLevel"] or "INFO")
                else:
                    cols.append("LogLevel")
                    vals.append("INFO")
                if "IPAddress" in masked_log_data:
                    cols.append("IPAddress")
                    vals.append(masked_log_data["IPAddress"])
                if "AdditionalInfo" in masked_log_data and masked_log_data["AdditionalInfo"] is not None:
                    import json
                    cols.append("AdditionalInfo")
                    vals.append(json.dumps(masked_log_data["AdditionalInfo"]) if isinstance(masked_log_data["AdditionalInfo"], (dict, list)) else str(masked_log_data["AdditionalInfo"]))
                cols.extend(["FrameworkId", "Timestamp"])
                vals.extend([framework_id, timezone.now()])
                placeholders = ", ".join(["%s"] * len(vals))
                columns = ", ".join(cols)
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"INSERT INTO grc_logs ({columns}) VALUES ({placeholders})",
                        vals
                    )
                    log_id = cursor.lastrowid
                log_entry = type("LogEntry", (), {"LogId": log_id})()
            else:
                raise
        if log_entry and hasattr(log_entry, "LogId"):
            logger.info(f"✅ Successfully saved log entry with ID: {log_entry.LogId} for {actionType} on {module}")
        
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
                    logger.warning(f"Failed to send log to service: {response.text}")
        except Exception as e:
            logger.warning(f"Error sending log to service: {str(e)}")
        
        return log_entry.LogId  # Return the ID of the created log
    except Exception as e:
        logger.error(f"❌ Error saving log to database: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Do not try to save error to GRCLog here - the table may be missing ValueBefore/ValueAfter
        # and would cause a cascade of the same error.
        return None 