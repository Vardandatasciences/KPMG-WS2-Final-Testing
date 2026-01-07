from django.utils.dateparse import parse_date as django_parse_date
from datetime import datetime
import requests
from .models import GRCLog

def parse_date(date_str):
    """Safely parse a date string into a date object"""
    if not date_str:
        return None
    return django_parse_date(date_str)

def safe_isoformat(val):
    """Safely convert a date to ISO format string"""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)

# Logging service configuration
LOGGING_SERVICE_URL = None  # Disabled external logging service

def sanitize_ip_address(ip_address):
    """
    Sanitize IP address to fit database column (max 45 characters).
    - Strips whitespace
    - Removes port numbers (IPv4 only)
    - Truncates to 45 characters
    
    Args:
        ip_address: IP address string (can be None)
        
    Returns:
        Sanitized IP address string (max 45 chars) or None
    """
    if not ip_address:
        return None
    
    # Strip whitespace
    sanitized_ip = str(ip_address).strip()
    
    # Remove port number if present (IPv4 only, not IPv6)
    if ':' in sanitized_ip and not sanitized_ip.startswith('['):
        parts = sanitized_ip.split(':')
        if len(parts) == 2 and '.' in parts[0]:
            # Likely IPv4 with port (e.g., "192.168.1.1:8080")
            sanitized_ip = parts[0]
    
    # Truncate to max 45 characters (database column limit)
    sanitized_ip = sanitized_ip[:45] if len(sanitized_ip) > 45 else sanitized_ip
    
    return sanitized_ip

def send_log(module, actionType, description=None, userId=None, userName=None,
             userRole=None, entityType=None, logLevel='INFO', ipAddress=None,
             additionalInfo=None, entityId=None):
   
    # Create log entry in database
    try:
        # Sanitize IP address using helper function
        sanitized_ip = sanitize_ip_address(ipAddress)
        
        # Prepare data for GRCLog model
        log_data = {
            'Timestamp': datetime.now(),
            'Module': module,
            'ActionType': actionType,
            'Description': description,
            'UserId': str(userId) if userId else None,
            'UserName': userName,
            'EntityType': entityType,
            'EntityId': str(entityId) if entityId else None,
            'LogLevel': logLevel,
            'IPAddress': sanitized_ip,
            'AdditionalInfo': additionalInfo
        }
       
        # Remove None values
        log_data = {k: v for k, v in log_data.items() if v is not None}
       
        # Create and save the log entry
        log_entry = GRCLog(**log_data)
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
            error_log = GRCLog(
                Timestamp=datetime.now(),
                Module=module,
                ActionType='LOG_ERROR',
                Description=f"Error logging {actionType} on {module}: {str(e)}",
                LogLevel='ERROR'
            )
            error_log.save()
        except:
            pass  # If we can't even log the error, just continue
        return None

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