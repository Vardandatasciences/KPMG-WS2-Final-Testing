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
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from ...models import ConsentConfiguration, ConsentAcceptance, ConsentWithdrawal, Users, Framework, RBAC
from ...serializers import ConsentConfigurationSerializer, ConsentAcceptanceSerializer, ConsentWithdrawalSerializer
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
        
        # If no configurations exist, create default ones
        if not configs.exists():
            framework = Framework.objects.get(FrameworkId=framework_id)
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
            
            for action_type, action_label in default_actions:
                ConsentConfiguration.objects.create(
                    action_type=action_type,
                    action_label=action_label,
                    is_enabled=False,
                    framework=framework,
                    consent_text=f"I consent to {action_label.lower()}. I understand that this action will be recorded and tracked for compliance purposes.",
                    created_by=created_by
                )
            
            configs = ConsentConfiguration.objects.filter(framework_id=framework_id)
        
        serializer = ConsentConfigurationSerializer(configs, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Framework.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Framework not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching consent configurations: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
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
            'message': str(e)
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
                    
                    if 'is_enabled' in config_data:
                        config.is_enabled = config_data['is_enabled']
                    if 'consent_text' in config_data:
                        config.consent_text = config_data['consent_text']
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
                    updated_configs.append(config)
                except ConsentConfiguration.DoesNotExist:
                    logger.warning(f"Consent configuration {config_id} not found")
                    continue
        
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
            'message': str(e)
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
            'message': str(e)
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
        
        # Get user and config
        user = Users.objects.get(UserId=user_id)
        config = ConsentConfiguration.objects.get(config_id=config_id)
        framework = Framework.objects.get(FrameworkId=framework_id)
        
        # Get IP address from request if not provided in data
        ip_address = data.get('ip_address')
        if not ip_address:
            ip_address = get_client_ip(request)
        
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
            ip_address=ip_address,
            user_agent=user_agent
        )
        
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
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_consent_history(request, user_id):
    """
    Get consent acceptance history for a user
    Query params: framework_id (optional), action_type (optional)
    """
    try:
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
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_consent_acceptances(request):
    """
    Get all consent acceptances (Admin view)
    Query params: framework_id (optional), action_type (optional)
    """
    try:
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
            'message': str(e)
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
        
        # Create consent withdrawal record
        withdrawal = ConsentWithdrawal.objects.create(
            user=user,
            config=config,
            action_type=action_type,
            framework=framework,
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            reason=data.get('reason')
        )
        
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
            'message': str(e)
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
        
        # Create withdrawal records for each consent
        withdrawals = []
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
                        ip_address=data.get('ip_address'),
                        user_agent=data.get('user_agent'),
                        reason=data.get('reason')
                    )
                    withdrawals.append(withdrawal)
        
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
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_consent_withdrawals(request, user_id):
    """
    Get consent withdrawal history for a user
    Query params: framework_id (optional), action_type (optional)
    """
    try:
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
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_consent_status(request, user_id):
    """
    Check the current consent status for a user (including withdrawals)
    Query params: framework_id (required), action_type (optional)
    Returns: {
        "action_type": "create_policy",
        "has_active_consent": true/false,
        "last_accepted": {...},
        "last_withdrawn": {...}
    }
    """
    try:
        framework_id = request.GET.get('framework_id')
        action_type = request.GET.get('action_type')
        
        if not framework_id:
            return Response({
                'status': 'error',
                'message': 'framework_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build query
        query = {'user_id': user_id, 'framework_id': framework_id}
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
        all_action_types = set(
            list(acceptances.values_list('action_type', flat=True)) +
            list(withdrawals.values_list('action_type', flat=True))
        )
        
        for act_type in all_action_types:
            last_acceptance = acceptances.filter(action_type=act_type).first()
            last_withdrawal = withdrawals.filter(action_type=act_type).first()
            
            has_active_consent = False
            if last_acceptance:
                if not last_withdrawal:
                    has_active_consent = True
                elif last_acceptance.accepted_at > last_withdrawal.withdrawn_at:
                    has_active_consent = True
            
            actions_status.append({
                'action_type': act_type,
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
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

