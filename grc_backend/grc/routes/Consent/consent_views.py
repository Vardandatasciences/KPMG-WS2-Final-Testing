"""
Consent Management Views
Handles consent configuration and acceptance tracking for GRC system
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from django.utils.decorators import method_decorator
from ...models import ConsentConfiguration, ConsentAcceptance, ConsentWithdrawal, Users, Framework, RBAC, GRCLog
from ...serializers import ConsentConfigurationSerializer, ConsentAcceptanceSerializer, ConsentWithdrawalSerializer
from ...rbac.utils import RBACUtils
import logging
import json

logger = logging.getLogger(__name__)

# Helper function to get client IP address
def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip

# Helper function to check if user is administrator
def is_user_administrator(user_id):
    """
    Check if a user has administrator privileges
    Returns True if user is GRC Administrator or system admin
    Checks the RBAC table for user roles
    """
    try:
        # Check if user exists
        user = Users.objects.get(UserId=user_id)
        
        # Check RBAC table for GRC Administrator role
        try:
            rbac_entry = RBAC.objects.get(user_id=user_id)
            user_role = rbac_entry.role or ''
            
            # Check if user has GRC Administrator role
            is_admin = (
                rbac_entry.role == 'GRC Administrator' or
                'GRC Administrator' in user_role or 
                'Administrator' in user_role or
                'System Administrator' in user_role
            )
            
            logger.info(f"[Consent] User {user_id} ({user.UserName}) role check: {rbac_entry.role}, is_admin: {is_admin}")
            return is_admin
            
        except RBAC.DoesNotExist:
            # No RBAC entry found - check if user has any admin indicators
            logger.warning(f"[Consent] No RBAC entry found for user {user_id}")
            
            # Fallback: Check if username suggests admin (for backward compatibility)
            username_lower = user.UserName.lower()
            is_admin = (
                'admin' in username_lower or
                'administrator' in username_lower
            )
            
            logger.info(f"[Consent] User {user_id} ({user.UserName}) fallback check, is_admin: {is_admin}")
            return is_admin
            
        except RBAC.MultipleObjectsReturned:
            # Multiple RBAC entries - check if any is GRC Administrator
            rbac_entries = RBAC.objects.filter(user_id=user_id)
            is_admin = any(
                entry.role == 'GRC Administrator' or
                'GRC Administrator' in (entry.role or '') or
                'Administrator' in (entry.role or '')
                for entry in rbac_entries
            )
            
            logger.info(f"[Consent] User {user_id} has multiple RBAC entries, is_admin: {is_admin}")
        return is_admin
            
    except Users.DoesNotExist:
        logger.error(f"[Consent] User {user_id} not found in Users table")
        return False
    except Exception as e:
        logger.error(f"Error checking admin status: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

# CSRF exempt session authentication for API
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Disable CSRF check


def _get_authenticated_user_id(request):
    """Resolve authenticated user id from request auth context."""
    try:
        return RBACUtils.get_user_id_from_request(request)
    except Exception as e:
        logger.warning(f"[Consent] Failed to resolve authenticated user id: {str(e)}")
        return None


def _require_user_scope(request, requested_user_id, allow_admin=False):
    """
    Enforce authenticated access and ownership (or admin override when enabled).
    Returns (resolved_user_id, error_response_or_none)
    """
    auth_user_id = _get_authenticated_user_id(request)
    if not auth_user_id:
        return None, Response({
            'status': 'error',
            'message': 'Authentication required'
        }, status=status.HTTP_401_UNAUTHORIZED)

    requested_id_str = str(requested_user_id)
    auth_id_str = str(auth_user_id)
    if requested_id_str != auth_id_str:
        if not (allow_admin and is_user_administrator(auth_user_id)):
            return None, Response({
                'status': 'error',
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)

    return auth_user_id, None


# =============================================================================
# CONSENT CONFIGURATION MANAGEMENT (Admin Only)
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def get_consent_configurations(request):
    """
    Get all consent configurations for a framework
    Query params: framework_id (required), created_by (optional - for setting creator when creating defaults)
    """
    try:
        framework_id = request.GET.get('framework_id')
        
        if not framework_id:
            return Response({
                'status': 'error',
                'message': 'framework_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get existing configurations
        configs = ConsentConfiguration.objects.filter(framework_id=framework_id)
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Define all default actions that should exist
        default_actions = [
            ('create_policy', 'Create Policy'),
            ('create_compliance', 'Create Compliance'),
            ('create_audit', 'Create Audit'),
            ('create_incident', 'Create Incident'),
            ('create_risk', 'Create Risk'),
            ('create_event', 'Create Event'),
            ('upload_policy', 'Upload in Policy'),
            ('upload_audit', 'Upload in Audit'),
            ('upload_incident', 'Upload in Incident'),
            ('upload_risk', 'Upload in Risk'),
            ('upload_event', 'Upload in Event'),
        ]
        
        # Get created_by from request if available
        created_by_id = request.GET.get('created_by')
        created_by = None
        if created_by_id:
            try:
                created_by = Users.objects.get(UserId=created_by_id)
                logger.info(f"[Consent] Setting created_by to user {created_by_id} for default configurations")
            except Users.DoesNotExist:
                logger.warning(f"[Consent] User {created_by_id} not found for created_by")
                pass
        
        # Get existing action types to check what's missing
        existing_action_types = set(configs.values_list('action_type', flat=True))
        
        # Create missing default configurations
        created_count = 0
        for action_type, action_label in default_actions:
            # Only create if it doesn't start with 'tprm_' (TPRM configs are handled separately)
            if not action_type.startswith('tprm_'):
                # Use the full action_label - database column is now VARCHAR(1000) to accommodate encryption
                truncated_label = action_label
                
                try:
                    # Use get_or_create to avoid duplicates and handle existing records
                    config, created = ConsentConfiguration.objects.get_or_create(
                        action_type=action_type,
                        framework=framework,
                        defaults={
                            'action_label': truncated_label,
                            'is_enabled': False,
                            'consent_text': f"I consent to {action_label.lower()}. I understand that this action will be recorded and tracked for compliance purposes.",
                            'created_by': created_by
                        }
                    )
                    
                    # If config already exists, ensure label is correct length
                    # Don't update if it's already correct to avoid unnecessary encryption
                    if not created:
                        # Check if we need to update the label
                        try:
                            # Try to get decrypted value to compare
                            existing_label_plain = None
                            if hasattr(config, 'action_label_plain'):
                                existing_label_plain = config.action_label_plain
                            else:
                                # If we can't get plain text, check if current encrypted value might be too long
                                # by checking if the action_label field itself is too long
                                existing_label_raw = getattr(config, 'action_label', '')
                                # No need to check length anymore - database supports up to 1000 chars
                            
                            # Only update if label is different
                            if existing_label_plain != truncated_label:
                                config.action_label = truncated_label  # Will be encrypted on save
                                config.save(update_fields=['action_label'])
                                logger.info(f"[Consent] Updated action_label for existing configuration: {action_type} ({truncated_label})")
                        except Exception as update_error:
                            logger.error(f"[Consent] Error updating action_label for {action_type}: {str(update_error)}")
                            # Continue - don't fail the whole process
                            continue
                    elif created:
                        created_count += 1
                        logger.info(f"[Consent] Created missing configuration: {action_type} ({truncated_label})")
                        
                except Exception as create_error:
                    logger.error(f"[Consent] Error creating/updating configuration for {action_type}: {str(create_error)}")
                    logger.error(f"[Consent] Action label length: {len(truncated_label)}, Action type: {action_type}")
                    import traceback
                    logger.error(f"[Consent] Traceback: {traceback.format_exc()}")
                    # Continue with other configurations even if one fails
                    continue
        
        if created_count > 0:
            logger.info(f"[Consent] Created {created_count} missing default configurations for framework {framework_id}")
            # Reload configurations after creating missing ones
            configs = ConsentConfiguration.objects.filter(framework_id=framework_id)
        
        # No need to fix label lengths anymore - database column is now VARCHAR(1000)
        
        try:
            serializer = ConsentConfigurationSerializer(configs, many=True)
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as serialize_error:
            logger.error(f"[Consent] Error serializing configurations: {str(serialize_error)}")
            logger.error(f"[Consent] Number of configs: {configs.count()}")
            # Try to identify problematic configs
            for config in configs:
                if config.action_label and len(config.action_label) > 1000:
                    logger.error(f"[Consent] Config {config.config_id} has label length {len(config.action_label)}: '{config.action_label[:50]}...'")
            raise
    
    except Framework.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Framework not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching consent configurations: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([AllowAny])
def update_consent_configuration(request, config_id):
    """
    Update a consent configuration (enable/disable, update text)
    REQUIRES: Administrator privileges - Only admins can configure consent
    """
    try:
        data = request.data
        updated_by_id = data.get('updated_by')
        
        # Check if user is administrator
        if not updated_by_id or not is_user_administrator(updated_by_id):
            return Response({
                'status': 'error',
                'message': 'Access denied. Only administrators can update consent configurations.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        config = ConsentConfiguration.objects.get(config_id=config_id)
        
        # Update fields
        if 'is_enabled' in data:
            config.is_enabled = data['is_enabled']
        if 'consent_text' in data:
            config.consent_text = data['consent_text']
        if updated_by_id:
            try:
                user = Users.objects.get(UserId=updated_by_id)
                config.updated_by = user
                # Set created_by if not already set
                if not config.created_by:
                    config.created_by = user
            except Users.DoesNotExist:
                pass
        
        config.save()
        
        # Log the configuration change
        try:
            user_obj = Users.objects.get(UserId=updated_by_id) if updated_by_id else None
            client_ip = get_client_ip(request)
            framework = config.framework
            
            if framework:
                log_entry = GRCLog(
                    Module='Consent Policy',
                    ActionType='CONFIG_UPDATE',
                    Description=f'Consent configuration updated: {config.action_type} (enabled: {config.is_enabled})',
                    UserId=str(updated_by_id) if updated_by_id else None,
                    UserName=user_obj.UserName if user_obj else None,
                    LogLevel='INFO',
                    IPAddress=client_ip[:45] if client_ip else None,
                    FrameworkId=framework,
                    AdditionalInfo={
                        'config_id': config.config_id,
                        'action_type': config.action_type,
                        'is_enabled': config.is_enabled,
                        'consent_text_length': len(config.consent_text) if config.consent_text else 0
                    }
                )
                log_entry.save()
        except Exception as log_error:
            logger.error(f"Error logging consent config update: {str(log_error)}")
        
        serializer = ConsentConfigurationSerializer(config)
        return Response({
            'status': 'success',
            'message': 'Consent configuration updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except ConsentConfiguration.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Consent configuration not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error updating consent configuration: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([AllowAny])
def bulk_update_consent_configurations(request):
    """
    Bulk update multiple consent configurations
    Body: { "configs": [{ "config_id": 1, "is_enabled": true, "consent_text": "..." }, ...], "updated_by": user_id }
    REQUIRES: Administrator privileges
    """
    try:
        data = request.data
        configs_data = data.get('configs', [])
        updated_by_id = data.get('updated_by')
        
        # Check if user is administrator
        if not updated_by_id or not is_user_administrator(updated_by_id):
            return Response({
                'status': 'error',
                'message': 'Only administrators can update consent configurations'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not configs_data:
            return Response({
                'status': 'error',
                'message': 'No configurations provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        updated_configs = []
        
        with transaction.atomic():
            for config_data in configs_data:
                config_id = config_data.get('config_id')
                if not config_id:
                    continue
                
                try:
                    config = ConsentConfiguration.objects.get(config_id=config_id)
                    
                    # Track which fields need to be updated
                    fields_to_update = []
                    
                    # Only update is_enabled if provided (toggle ON = True/1, OFF = False/0)
                    if 'is_enabled' in config_data:
                        # Ensure boolean conversion: True/1 -> True, False/0/None -> False
                        is_enabled_value = bool(config_data['is_enabled']) if config_data['is_enabled'] is not None else False
                        config.is_enabled = is_enabled_value
                        fields_to_update.append('is_enabled')
                        logger.debug(f"[Consent] Updating config {config_id}: is_enabled = {is_enabled_value} ({type(is_enabled_value).__name__})")
                    
                    # Only update consent_text if provided
                    if 'consent_text' in config_data:
                        config.consent_text = config_data['consent_text']
                        fields_to_update.append('consent_text')
                    
                    # Update updated_by and updated_at if we're making changes
                    if fields_to_update and updated_by_id:
                        try:
                            user = Users.objects.get(UserId=updated_by_id)
                            config.updated_by = user
                            fields_to_update.append('updated_by')
                            # Set created_by if not already set (only once)
                            if not config.created_by:
                                config.created_by = user
                                fields_to_update.append('created_by')
                        except Users.DoesNotExist:
                            logger.warning(f"User {updated_by_id} not found for updated_by")
                    
                    # Only save if there are fields to update, and use update_fields to ensure other fields aren't touched
                    if fields_to_update:
                        # updated_at is auto-updated, so add it to update_fields
                        if 'updated_by' in fields_to_update:
                            fields_to_update.append('updated_at')
                        config.save(update_fields=fields_to_update)
                        updated_configs.append(config)
                        logger.info(f"[Consent] Updated config {config_id} ({config.action_type}): fields={fields_to_update}, is_enabled={config.is_enabled}")
                except ConsentConfiguration.DoesNotExist:
                    logger.warning(f"Consent configuration {config_id} not found")
                    continue
        
        # Log the bulk configuration change
        try:
            user_obj = Users.objects.get(UserId=updated_by_id) if updated_by_id else None
            client_ip = get_client_ip(request)
            
            # Get framework from first config if available
            framework = None
            if updated_configs:
                framework = updated_configs[0].framework
            
            if framework:
                action_types = [c.action_type for c in updated_configs]
                enabled_count = sum(1 for c in updated_configs if c.is_enabled)
                log_entry = GRCLog(
                    Module='Consent Policy',
                    ActionType='CONFIG_UPDATE',
                    Description=f'Bulk consent configurations updated: {len(updated_configs)} configuration(s) modified ({enabled_count} enabled)',
                    UserId=str(updated_by_id) if updated_by_id else None,
                    UserName=user_obj.UserName if user_obj else None,
                    LogLevel='INFO',
                    IPAddress=client_ip[:45] if client_ip else None,
                    FrameworkId=framework,
                    AdditionalInfo={
                        'configs_updated': len(updated_configs),
                        'enabled_count': enabled_count,
                        'action_types': action_types[:10]  # Limit to first 10
                    }
                )
                log_entry.save()
        except Exception as log_error:
            logger.error(f"Error logging bulk consent config update: {str(log_error)}")
        
        serializer = ConsentConfigurationSerializer(updated_configs, many=True)
        return Response({
            'status': 'success',
            'message': f'{len(updated_configs)} consent configurations updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error bulk updating consent configurations: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# CONSENT CHECKING AND ACCEPTANCE
# =============================================================================

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def check_consent_required(request):
    """
    Check if consent is required for a specific action
    Body: { "action_type": "create_policy", "framework_id": 1, "user_id": 1 (optional) }
    Returns: { "required": true/false, "config": {...}, "has_active_consent": true/false }
    """
    try:
        data = request.data
        action_type = data.get('action_type')
        framework_id = data.get('framework_id')
        user_id = data.get('user_id')  # Optional - if provided, check if user has active consent
        
        if not action_type or not framework_id:
            return Response({
                'status': 'error',
                'message': 'action_type and framework_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Convert framework_id to int if it's a string
            try:
                framework_id_int = int(framework_id)
            except (ValueError, TypeError):
                framework_id_int = framework_id
            
            config = ConsentConfiguration.objects.get(
                action_type=action_type,
                framework_id=framework_id_int
            )
            
            logger.info(f"[Consent] Found config for {action_type}, framework {framework_id_int}, is_enabled: {config.is_enabled}")
            
            serializer = ConsentConfigurationSerializer(config)
            config_data = serializer.data
            
            # Ensure config_id is in the response (it might be named differently)
            if 'config_id' not in config_data and hasattr(config, 'config_id'):
                config_data['config_id'] = config.config_id
            
            # Ensure framework_id is in the response
            if 'framework_id' not in config_data:
                config_data['framework_id'] = config.framework.FrameworkId if config.framework else framework_id_int
            
            # Check if user has active consent (not withdrawn)
            has_active_consent = None
            if user_id and config.is_enabled:
                # Check if user has an active consent (accepted and not withdrawn)
                last_acceptance = ConsentAcceptance.objects.filter(
                    user_id=user_id,
                    action_type=action_type,
                    framework_id=framework_id_int
                ).order_by('-accepted_at').first()
                
                if last_acceptance:
                    # Check if there's a withdrawal after this acceptance
                    last_withdrawal = ConsentWithdrawal.objects.filter(
                        user_id=user_id,
                        action_type=action_type,
                        framework_id=framework_id_int,
                        withdrawn_at__gt=last_acceptance.accepted_at
                    ).first()
                    
                    has_active_consent = last_withdrawal is None
                else:
                    has_active_consent = False
            
            logger.info(f"[Consent] Returning config data: {config_data}, has_active_consent: {has_active_consent}")
            
            return Response({
                'status': 'success',
                'required': config.is_enabled,
                'config': config_data,
                'has_active_consent': has_active_consent
            }, status=status.HTTP_200_OK)
        
        except ConsentConfiguration.DoesNotExist:
            # If no config exists, consent is not required
            return Response({
                'status': 'success',
                'required': False,
                'config': None,
                'has_active_consent': None
            }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error checking consent requirement: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def record_consent_acceptance(request):
    """
    Record user's consent acceptance
    Body: {
        "user_id": 1,
        "config_id": 1,
        "action_type": "create_policy",
        "framework_id": 1,
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0..."
    }
    """
    try:
        data = request.data
        user_id = data.get('user_id')
        config_id = data.get('config_id')
        action_type = data.get('action_type')
        framework_id = data.get('framework_id')
        
        if not all([user_id, config_id, action_type, framework_id]):
            return Response({
                'status': 'error',
                'message': 'user_id, config_id, action_type, and framework_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        _, scope_error = _require_user_scope(request, user_id, allow_admin=False)
        if scope_error:
            return scope_error
        
        # Get user and config
        user = Users.objects.get(UserId=user_id)
        config = ConsentConfiguration.objects.get(config_id=config_id)
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Get IP address from request if not provided in data
        ip_address = data.get('ip_address')
        if not ip_address:
            ip_address = get_client_ip(request)
        
        # Sanitize IP address to fit database column (max 45 chars)
        from ...utils import sanitize_ip_address
        sanitized_ip = sanitize_ip_address(ip_address)
        
        # Get user agent from request if not provided in data
        user_agent = data.get('user_agent')
        if not user_agent:
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Create consent acceptance record
        acceptance = ConsentAcceptance.objects.create(
            user=user,
            config=config,
            action_type=action_type,
            framework=framework,
            ip_address=sanitized_ip,
            user_agent=user_agent
        )
        
        # Log the consent creation/acceptance to grc_logs table
        # This must happen after successful creation
        try:
            # Get acceptance_id safely
            acceptance_id = None
            try:
                acceptance_id = acceptance.acceptance_id
            except:
                try:
                    acceptance_id = acceptance.pk
                except:
                    pass
            
            # Ensure we have a framework for logging
            log_framework = framework
            if not log_framework:
                try:
                    log_framework = Framework.objects.filter(ActiveInactive='Active').first()
                    if not log_framework:
                        log_framework = Framework.objects.first()
                except:
                    pass
            
            if log_framework:
                log_entry = GRCLog(
                    Module='Consent',
                    ActionType='CONSENT_CREATE',
                    Description=f'User {user.UserName} (ID: {user_id}) accepted consent for action: {action_type}',
                    UserId=str(user_id),
                    UserName=user.UserName,
                    LogLevel='INFO',
                    IPAddress=sanitized_ip,
                    FrameworkId=log_framework,
                    AdditionalInfo={
                        'acceptance_id': acceptance_id,
                        'config_id': config_id,
                        'action_type': action_type,
                        'user_agent': user_agent[:200] if user_agent else None
                    }
                )
                log_entry.save()
                logger.info(f"✅ Successfully logged consent acceptance to grc_logs: acceptance_id={acceptance_id}, user_id={user_id}, action_type={action_type}")
            else:
                logger.warning(f"⚠️ Cannot log consent acceptance: No framework available")
        except Exception as log_error:
            logger.error(f"❌ Error logging consent acceptance to grc_logs: {str(log_error)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Don't fail the request if logging fails, but log the error
        
        serializer = ConsentAcceptanceSerializer(acceptance)
        return Response({
            'status': 'success',
            'message': 'Consent acceptance recorded successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    except Users.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except ConsentConfiguration.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Consent configuration not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Framework.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Framework not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error recording consent acceptance: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_consent_history(request, user_id):
    """
    Get consent acceptance history for a user
    Query params: framework_id (optional), action_type (optional)
    """
    try:
        _, scope_error = _require_user_scope(request, user_id, allow_admin=True)
        if scope_error:
            return scope_error

        framework_id = request.GET.get('framework_id')
        action_type = request.GET.get('action_type')
        
        # Build query
        query = {'user_id': user_id}
        if framework_id:
            query['framework_id'] = framework_id
        if action_type:
            query['action_type'] = action_type
        
        acceptances = ConsentAcceptance.objects.filter(**query)
        serializer = ConsentAcceptanceSerializer(acceptances, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching user consent history: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_consent_acceptances(request):
    """
    Get all consent acceptances (Admin view)
    Query params: framework_id (optional), action_type (optional)
    """
    try:
        auth_user_id = _get_authenticated_user_id(request)
        if not auth_user_id:
            return Response({
                'status': 'error',
                'message': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        if not is_user_administrator(auth_user_id):
            return Response({
                'status': 'error',
                'message': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)

        framework_id = request.GET.get('framework_id')
        action_type = request.GET.get('action_type')
        
        # Build query
        query = {}
        if framework_id:
            query['framework_id'] = framework_id
        if action_type:
            query['action_type'] = action_type
        
        acceptances = ConsentAcceptance.objects.filter(**query).select_related('user', 'config')
        serializer = ConsentAcceptanceSerializer(acceptances, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'count': acceptances.count()
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching consent acceptances: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# CONSENT WITHDRAWAL MANAGEMENT
# =============================================================================

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def withdraw_consent(request):
    """
    Withdraw consent for a specific action
    Body: {
        "user_id": 1,
        "action_type": "create_policy",
        "framework_id": 1,
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
        "reason": "Optional reason for withdrawal"
    }
    """
    try:
        data = request.data
        user_id = data.get('user_id')
        action_type = data.get('action_type')
        framework_id = data.get('framework_id')
        
        if not all([user_id, action_type, framework_id]):
            return Response({
                'status': 'error',
                'message': 'user_id, action_type, and framework_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        _, scope_error = _require_user_scope(request, user_id, allow_admin=False)
        if scope_error:
            return scope_error
        
        # Get user and framework
        user = Users.objects.get(UserId=user_id)
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Try to get the config for this action (optional)
        config = None
        try:
            config = ConsentConfiguration.objects.get(
                action_type=action_type,
                framework_id=framework_id
            )
        except ConsentConfiguration.DoesNotExist:
            # Config might not exist, but we still allow withdrawal
            logger.warning(f"Consent configuration not found for action_type={action_type}, framework_id={framework_id}")
        
        # Get IP address and sanitize it
        ip_address = data.get('ip_address')
        if not ip_address:
            ip_address = get_client_ip(request)
        from ...utils import sanitize_ip_address
        sanitized_ip = sanitize_ip_address(ip_address)
        
        # Create consent withdrawal record
        withdrawal = ConsentWithdrawal.objects.create(
            user=user,
            config=config,
            action_type=action_type,
            framework=framework,
            ip_address=sanitized_ip,
            user_agent=data.get('user_agent'),
            reason=data.get('reason')
        )
        
        # Log the consent withdrawal to grc_logs table
        try:
            # Get withdrawal_id safely
            withdrawal_id = None
            try:
                withdrawal_id = withdrawal.withdrawal_id
            except:
                try:
                    withdrawal_id = withdrawal.pk
                except:
                    pass
            
            # Ensure we have a framework for logging
            log_framework = framework
            if not log_framework:
                try:
                    log_framework = Framework.objects.filter(ActiveInactive='Active').first()
                    if not log_framework:
                        log_framework = Framework.objects.first()
                except:
                    pass
            
            if log_framework:
                log_entry = GRCLog(
                    Module='Consent',
                    ActionType='CONSENT_WITHDRAW',
                    Description=f'User {user.UserName} (ID: {user_id}) withdrew consent for action: {action_type}',
                    UserId=str(user_id),
                    UserName=user.UserName,
                    LogLevel='INFO',
                    IPAddress=sanitized_ip,
                    FrameworkId=log_framework,
                    AdditionalInfo={
                        'withdrawal_id': withdrawal_id,
                        'action_type': action_type,
                        'reason': data.get('reason')[:200] if data.get('reason') else None,
                        'config_id': config.config_id if config else None
                    }
                )
                log_entry.save()
                logger.info(f"✅ Successfully logged consent withdrawal to grc_logs: withdrawal_id={withdrawal_id}, user_id={user_id}, action_type={action_type}")
            else:
                logger.warning(f"⚠️ Cannot log consent withdrawal: No framework available")
        except Exception as log_error:
            logger.error(f"❌ Error logging consent withdrawal to grc_logs: {str(log_error)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        serializer = ConsentWithdrawalSerializer(withdrawal)
        return Response({
            'status': 'success',
            'message': 'Consent withdrawn successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    
    except Users.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Framework.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Framework not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error withdrawing consent: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def withdraw_all_consents(request):
    """
    Withdraw all consents for a user (for a specific framework or all frameworks)
    Body: {
        "user_id": 1,
        "framework_id": 1,  # Optional - if not provided, withdraws from all frameworks
        "ip_address": "192.168.1.1",
        "user_agent": "Mozilla/5.0...",
        "reason": "Optional reason for withdrawal"
    }
    """
    try:
        data = request.data
        user_id = data.get('user_id')
        framework_id = data.get('framework_id')
        
        if not user_id:
            return Response({
                'status': 'error',
                'message': 'user_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        _, scope_error = _require_user_scope(request, user_id, allow_admin=False)
        if scope_error:
            return scope_error
        
        # Get user
        user = Users.objects.get(UserId=user_id)
        
        # Get all active consents for this user
        query = {'user_id': user_id}
        if framework_id:
            query['framework_id'] = framework_id
        
        acceptances = ConsentAcceptance.objects.filter(**query).select_related('config', 'framework')
        
        if not acceptances.exists():
            return Response({
                'status': 'success',
                'message': 'No active consents found to withdraw',
                'data': [],
                'count': 0
            }, status=status.HTTP_200_OK)
        
        # Get IP address and sanitize it
        ip_address = data.get('ip_address')
        if not ip_address:
            ip_address = get_client_ip(request)
        from ...utils import sanitize_ip_address
        sanitized_ip = sanitize_ip_address(ip_address)
        
        # Get framework for logging (use first acceptance's framework or provided framework_id)
        framework_for_log = None
        if framework_id:
            try:
                framework_for_log = Framework.objects.get(FrameworkId=framework_id)
            except Framework.DoesNotExist:
                pass
        
        # Create withdrawal records for each consent
        withdrawals = []
        withdrawn_action_types = []
        with transaction.atomic():
            for acceptance in acceptances:
                # Check if already withdrawn
                existing_withdrawal = ConsentWithdrawal.objects.filter(
                    user_id=user_id,
                    action_type=acceptance.action_type,
                    framework_id=acceptance.framework_id,
                    withdrawn_at__gt=acceptance.accepted_at
                ).exists()
                
                if not existing_withdrawal:
                    withdrawal = ConsentWithdrawal.objects.create(
                        user=user,
                        config=acceptance.config,
                        action_type=acceptance.action_type,
                        framework=acceptance.framework,
                        ip_address=sanitized_ip,
                        user_agent=data.get('user_agent'),
                        reason=data.get('reason')
                    )
                    withdrawals.append(withdrawal)
                    withdrawn_action_types.append(acceptance.action_type)
                    
                    # Use first acceptance's framework for logging if not set
                    if not framework_for_log and acceptance.framework:
                        framework_for_log = acceptance.framework
        
        # Log the bulk consent withdrawal to grc_logs table
        try:
            # Ensure we have a framework for logging
            if not framework_for_log:
                try:
                    framework_for_log = Framework.objects.filter(ActiveInactive='Active').first()
                    if not framework_for_log:
                        framework_for_log = Framework.objects.first()
                except:
                    pass
            
            if framework_for_log and len(withdrawals) > 0:
                log_entry = GRCLog(
                    Module='Consent',
                    ActionType='CONSENT_WITHDRAW_ALL',
                    Description=f'User {user.UserName} (ID: {user_id}) withdrew {len(withdrawals)} consent(s)',
                    UserId=str(user_id),
                    UserName=user.UserName,
                    LogLevel='INFO',
                    IPAddress=sanitized_ip,
                    FrameworkId=framework_for_log,
                    AdditionalInfo={
                        'withdrawals_count': len(withdrawals),
                        'action_types': withdrawn_action_types[:10],  # Limit to first 10
                        'framework_id': framework_id,
                        'reason': data.get('reason')[:200] if data.get('reason') else None
                    }
                )
                log_entry.save()
                logger.info(f"✅ Successfully logged bulk consent withdrawal to grc_logs: {len(withdrawals)} withdrawals, user_id={user_id}")
            elif len(withdrawals) > 0:
                logger.warning(f"⚠️ Cannot log bulk consent withdrawal: No framework available")
        except Exception as log_error:
            logger.error(f"❌ Error logging bulk consent withdrawal to grc_logs: {str(log_error)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        serializer = ConsentWithdrawalSerializer(withdrawals, many=True)
        return Response({
            'status': 'success',
            'message': f'{len(withdrawals)} consent(s) withdrawn successfully',
            'data': serializer.data,
            'count': len(withdrawals)
        }, status=status.HTTP_201_CREATED)
    
    except Users.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error withdrawing all consents: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_consent_withdrawals(request, user_id):
    """
    Get consent withdrawal history for a user
    Query params: framework_id (optional), action_type (optional)
    """
    try:
        _, scope_error = _require_user_scope(request, user_id, allow_admin=True)
        if scope_error:
            return scope_error

        framework_id = request.GET.get('framework_id')
        action_type = request.GET.get('action_type')
        
        # Build query
        query = {'user_id': user_id}
        if framework_id:
            query['framework_id'] = framework_id
        if action_type:
            query['action_type'] = action_type
        
        withdrawals = ConsentWithdrawal.objects.filter(**query).select_related('user', 'config', 'framework')
        serializer = ConsentWithdrawalSerializer(withdrawals, many=True)
        
        return Response({
            'status': 'success',
            'data': serializer.data,
            'count': withdrawals.count()
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error fetching user consent withdrawals: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_consent_status(request, user_id):
    """
    Check the current consent status for a user (including withdrawals)
    Query params: framework_id (optional), action_type (optional)
    Returns: {
        "action_type": "create_policy",
        "has_active_consent": true/false,
        "last_accepted": {...},
        "last_withdrawn": {...}
    }
    """
    try:
        _, scope_error = _require_user_scope(request, user_id, allow_admin=True)
        if scope_error:
            return scope_error

        framework_id = request.GET.get('framework_id')
        action_type = request.GET.get('action_type')
        
        # Build query
        query = {'user_id': user_id}
        if framework_id:
            query['framework_id'] = framework_id
        if action_type:
            query['action_type'] = action_type
        
        # Get all acceptances and withdrawals
        acceptances = ConsentAcceptance.objects.filter(**query).order_by('-accepted_at')
        withdrawals = ConsentWithdrawal.objects.filter(**query).order_by('-withdrawn_at')
        
        # If action_type is specified, return status for that action
        if action_type:
            last_acceptance = acceptances.filter(action_type=action_type).first()
            last_withdrawal = withdrawals.filter(action_type=action_type).first()
            
            # Check if there's an active consent (accepted after last withdrawal)
            has_active_consent = False
            if last_acceptance:
                if not last_withdrawal:
                    has_active_consent = True
                elif last_acceptance.accepted_at > last_withdrawal.withdrawn_at:
                    has_active_consent = True
            
            acceptance_data = ConsentAcceptanceSerializer(last_acceptance).data if last_acceptance else None
            withdrawal_data = ConsentWithdrawalSerializer(last_withdrawal).data if last_withdrawal else None
            
            return Response({
                'status': 'success',
                'action_type': action_type,
                'has_active_consent': has_active_consent,
                'last_accepted': acceptance_data,
                'last_withdrawn': withdrawal_data
            }, status=status.HTTP_200_OK)
        
        # If no action_type, return status for all actions
        actions_status = []
        all_action_framework_pairs = set(
            list(acceptances.values_list('action_type', 'framework_id')) +
            list(withdrawals.values_list('action_type', 'framework_id'))
        )
        
        for act_type, act_framework_id in all_action_framework_pairs:
            action_acceptances = acceptances.filter(action_type=act_type, framework_id=act_framework_id)
            action_withdrawals = withdrawals.filter(action_type=act_type, framework_id=act_framework_id)

            last_acceptance = action_acceptances.first()
            last_withdrawal = action_withdrawals.first()
            
            has_active_consent = False
            if last_acceptance:
                if not last_withdrawal:
                    has_active_consent = True
                elif last_acceptance.accepted_at > last_withdrawal.withdrawn_at:
                    has_active_consent = True
            
            actions_status.append({
                'action_type': act_type,
                'framework_id': act_framework_id,
                'has_active_consent': has_active_consent,
                'last_accepted': ConsentAcceptanceSerializer(last_acceptance).data if last_acceptance else None,
                'last_withdrawn': ConsentWithdrawalSerializer(last_withdrawal).data if last_withdrawal else None
            })
        
        return Response({
            'status': 'success',
            'data': actions_status,
            'count': len(actions_status)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error checking consent status: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'An internal server error occurred.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

