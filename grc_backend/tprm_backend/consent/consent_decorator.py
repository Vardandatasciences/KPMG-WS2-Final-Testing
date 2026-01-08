"""
TPRM Consent Management Decorator
Common module for enforcing consent requirements across the TPRM system
"""

from functools import wraps
from rest_framework.response import Response
from rest_framework import status as http_status
from django.db import connections
import logging

logger = logging.getLogger(__name__)


def require_consent(action_type):
    """
    Decorator to enforce consent requirements for specific TPRM actions
    
    Usage:
        @require_consent('tprm_create_sla')
        def create_sla_view(request):
            # Your view logic here
            pass
    
    Args:
        action_type (str): The action type (e.g., 'tprm_create_sla', 'tprm_create_vendor')
    
    Returns:
        Decorated function that enforces consent
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            try:
                # Default framework_id for TPRM
                framework_id = '1'
                
                # Try to get from request
                if request.method == 'POST' or request.method == 'PUT':
                    framework_id = request.data.get('framework_id', '1')
                elif request.method == 'GET':
                    framework_id = request.GET.get('framework_id', '1')
                
                # Use TPRM database connection
                try:
                    tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connections['default']
                except:
                    tprm_connection = connections['default']
                
                # Check if consent is required for this action
                with tprm_connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT ConfigId, ActionType, ActionLabel, IsEnabled, ConsentText
                        FROM consent_configuration_tprm
                        WHERE ActionType = %s AND FrameworkId = %s
                        LIMIT 1
                    """, [action_type, framework_id])
                    
                    row = cursor.fetchone()
                    
                    if row:
                        columns = [col[0] for col in cursor.description]
                        consent_config = dict(zip(columns, row))
                        is_enabled = bool(consent_config.get('IsEnabled', 0))
                        
                        # If consent is not enabled, allow the request
                        if not is_enabled:
                            logger.debug(f"[TPRM Consent] Consent not enabled for {action_type}. Allowing request.")
                            return view_func(request, *args, **kwargs)
                        
                        # Consent is enabled - check if user has accepted
                        consent_accepted = request.data.get('consent_accepted', False) if request.method in ['POST', 'PUT'] else False
                        consent_config_id = request.data.get('consent_config_id') if request.method in ['POST', 'PUT'] else None
                        
                        if not consent_accepted or not consent_config_id:
                            logger.warning(f"[TPRM Consent] Consent required but not provided for {action_type}")
                            return Response({
                                'status': 'error',
                                'error': 'CONSENT_REQUIRED',
                                'message': 'Consent is required for this action',
                                'consent_required': True,
                                'consent_config': {
                                    'config_id': consent_config['ConfigId'],
                                    'action_type': consent_config['ActionType'],
                                    'action_label': consent_config['ActionLabel'],
                                    'consent_text': consent_config['ConsentText']
                                }
                            }, status=http_status.HTTP_403_FORBIDDEN)
                        
                        # Verify the consent_config_id matches
                        if int(consent_config_id) != consent_config['ConfigId']:
                            logger.error(f"[TPRM Consent] Consent config ID mismatch for {action_type}")
                            return Response({
                                'status': 'error',
                                'message': 'Invalid consent configuration'
                            }, status=http_status.HTTP_400_BAD_REQUEST)
                        
                        # Consent is properly accepted - allow the request
                        logger.info(f"[TPRM Consent] Consent verified for {action_type}. Proceeding with request.")
                        return view_func(request, *args, **kwargs)
                    else:
                        # No consent configuration exists - allow the request (backward compatibility)
                        logger.debug(f"[TPRM Consent] No consent configuration found for {action_type}. Allowing request.")
                        return view_func(request, *args, **kwargs)
            
            except Exception as e:
                logger.error(f"[TPRM Consent] Error in consent decorator: {str(e)}")
                # In case of error, allow the request to proceed (fail open for availability)
                return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


def check_consent_programmatically(action_type, framework_id='1'):
    """
    Programmatically check if consent is required for an action
    Useful for non-decorator use cases
    
    Args:
        action_type (str): The action type
        framework_id (str): The framework ID (defaults to '1' for TPRM)
    
    Returns:
        tuple: (is_required, config_dict or None)
    """
    try:
        # Use TPRM database connection
        try:
            tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connections['default']
        except:
            tprm_connection = connections['default']
        
        with tprm_connection.cursor() as cursor:
            cursor.execute("""
                SELECT ConfigId, ActionType, ActionLabel, IsEnabled, ConsentText
                FROM consent_configuration_tprm
                WHERE ActionType = %s AND FrameworkId = %s
                LIMIT 1
            """, [action_type, framework_id])
            
            row = cursor.fetchone()
            
            if row:
                columns = [col[0] for col in cursor.description]
                consent_config = dict(zip(columns, row))
                is_enabled = bool(consent_config.get('IsEnabled', 0))
                
                if is_enabled:
                    return True, {
                        'config_id': consent_config['ConfigId'],
                        'action_type': consent_config['ActionType'],
                        'action_label': consent_config['ActionLabel'],
                        'consent_text': consent_config['ConsentText']
                    }
                else:
                    return False, None
            else:
                return False, None
    
    except Exception as e:
        logger.error(f"[TPRM Consent] Error checking consent: {str(e)}")
        return False, None

