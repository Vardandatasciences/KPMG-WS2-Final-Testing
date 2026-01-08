"""
TPRM Consent Management Views
Handles consent configuration and acceptance tracking for TPRM system
Similar to GRC consent but for TPRM-specific actions
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
from django.db import transaction
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
    Check if a user has administrator privileges for TPRM
    Uses GRC database to check RBAC role
    """
    try:
        # Use GRC database connection to check user and RBAC
        grc_connection = connections['default']
        with grc_connection.cursor() as cursor:
            # Check if user exists
            cursor.execute("""
                SELECT UserId, UserName 
                FROM users
                WHERE UserId = %s
            """, [user_id])
            row = cursor.fetchone()
            
            if row:
                user_id_db, username = row
                # Check RBAC for admin role - RBAC table uses UserId (not user_id)
                # Escape % characters in LIKE patterns by doubling them (%%)
                cursor.execute("""
                    SELECT Role FROM rbac 
                    WHERE UserId = %s 
                    AND (Role LIKE '%%Administrator%%' OR Role LIKE '%%Admin%%')
                    LIMIT 1
                """, [user_id])
                role_row = cursor.fetchone()
                
                is_admin = role_row is not None
                if role_row:
                    role_name = role_row[0]
                    logger.info(f"[TPRM Consent] User {user_id} ({username}) role: {role_name}, is_admin: {is_admin}")
                else:
                    logger.info(f"[TPRM Consent] User {user_id} ({username}) no admin role found, is_admin: {is_admin}")
                return is_admin
            else:
                logger.warning(f"[TPRM Consent] User {user_id} not found in users table")
                return False
    except Exception as e:
        logger.error(f"[TPRM Consent] Error checking admin status: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"[TPRM Consent] Traceback: {traceback.format_exc()}")
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
    Get all consent configurations for TPRM actions
    Query params: framework_id (optional - defaults to 1 for TPRM), created_by (optional)
    """
    try:
        # NOTE:
        # For TPRM consents we don't currently scope by GRC framework.
        # Many deployments use a fixed FrameworkId (often 1) in the TPRM DB,
        # while the GRC framework ID can vary. To avoid "no data" situations
        # caused by mismatched IDs, we fetch ALL TPRM consent configurations
        # and let the frontend simply display them.
        framework_id = request.GET.get('framework_id', '1')  # Kept for logging/debug
        logger.info(f"[TPRM Consent] Fetching configurations (ignoring framework filter), requested framework_id: {framework_id}")

        # Use TPRM database connection for TPRM consent tables
        # Try to get TPRM connection, fallback to default if not available
        try:
            if 'tprm' in connections.databases:
                tprm_connection = connections['tprm']
                logger.info(f"[TPRM Consent] Using TPRM database connection: {connections.databases['tprm']['NAME']}")
            else:
                tprm_connection = connections['default']
                logger.warning("[TPRM Consent] TPRM database not found, using default connection")
        except Exception as conn_error:
            tprm_connection = connections['default']
            logger.warning(f"[TPRM Consent] Error getting TPRM connection, using default: {conn_error}")
        
        # Get existing configurations from TPRM consent table
        try:
            with tprm_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT ConfigId, ActionType, ActionLabel, IsEnabled, ConsentText, 
                           FrameworkId, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt
                    FROM consent_configuration_tprm
                    ORDER BY ActionLabel
                """)
                
                columns = [col[0] for col in cursor.description]
                configs = [dict(zip(columns, row)) for row in cursor.fetchall()]
                logger.info(f"[TPRM Consent] Found {len(configs)} existing configurations (no framework filter)")
        except Exception as query_error:
            logger.error(f"[TPRM Consent] Error querying consent_configuration_tprm table: {str(query_error)}")
            logger.error(f"[TPRM Consent] Table might not exist. Error details: {type(query_error).__name__}")
            # Return empty list if table doesn't exist
            configs = []
        
        # If no configurations exist, create default ones
        if not configs:
            logger.info("[TPRM Consent] No configurations found, creating default ones...")
            default_actions = [
                ('tprm_create_sla', 'Create SLA'),
                ('tprm_update_sla', 'Update SLA'),
                ('tprm_delete_sla', 'Delete SLA'),
                ('tprm_create_vendor', 'Create Vendor'),
                ('tprm_update_vendor', 'Update Vendor'),
                ('tprm_create_contract', 'Create Contract'),
                ('tprm_update_contract', 'Update Contract'),
                ('tprm_create_rfp', 'Create RFP'),
                ('tprm_submit_rfp', 'Submit RFP'),
                ('tprm_create_risk', 'Create Risk Assessment'),
                ('tprm_create_compliance', 'Create Compliance Record'),
            ]
            
            created_by_id = request.GET.get('created_by')
            
            try:
                with tprm_connection.cursor() as cursor:
                    for action_type, action_label in default_actions:
                        consent_text = f"I consent to {action_label.lower()}. I understand that this action will be recorded and tracked for compliance purposes."
                        try:
                            cursor.execute("""
                                INSERT INTO consent_configuration_tprm 
                                (ActionType, ActionLabel, IsEnabled, ConsentText, FrameworkId, CreatedBy, CreatedAt, UpdatedAt)
                                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                            """, [action_type, action_label, False, consent_text, framework_id, created_by_id])
                        except Exception as insert_error:
                            logger.error(f"[TPRM Consent] Error inserting {action_type}: {str(insert_error)}")
                            # Continue with other actions
                            continue
                    
                    tprm_connection.commit()
                    logger.info(f"[TPRM Consent] Created {len(default_actions)} default configurations")
                
                # Fetch again after creation (no framework filter - get all)
                with tprm_connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT ConfigId, ActionType, ActionLabel, IsEnabled, ConsentText, 
                               FrameworkId, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt
                        FROM consent_configuration_tprm
                        ORDER BY ActionLabel
                    """)
                    columns = [col[0] for col in cursor.description]
                    configs = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    logger.info(f"[TPRM Consent] Fetched {len(configs)} configurations after creation")
            except Exception as create_error:
                logger.error(f"[TPRM Consent] Error creating default configurations: {str(create_error)}")
                logger.error(f"[TPRM Consent] Table might not exist. Please run: python manage.py setup_tprm_consent_tables")
                # Return empty list if creation fails
                configs = []
        
        logger.info(f"[TPRM Consent] Returning {len(configs)} configurations")
        return Response({
            'status': 'success',
            'data': configs,
            'message': f'Found {len(configs)} consent configurations'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"[TPRM Consent] Error fetching consent configurations: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"[TPRM Consent] Traceback: {traceback.format_exc()}")
        return Response({
            'status': 'error',
            'message': str(e),
            'data': [],
            'error_details': "Table might not exist. Please run: python manage.py setup_tprm_consent_tables"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@authentication_classes([])
@permission_classes([AllowAny])
def update_consent_configuration(request, config_id):
    """
    Update a consent configuration (enable/disable, update text)
    REQUIRES: Administrator privileges
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
        
        # Use TPRM database connection
        try:
            tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connections['default']
        except:
            tprm_connection = connections['default']
        
        with tprm_connection.cursor() as cursor:
            # Check if config exists
            cursor.execute("""
                SELECT ConfigId FROM consent_configuration_tprm WHERE ConfigId = %s
            """, [config_id])
            if not cursor.fetchone():
                return Response({
                    'status': 'error',
                    'message': 'Consent configuration not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Update fields
            update_fields = []
            params = []
            
            if 'is_enabled' in data:
                update_fields.append("IsEnabled = %s")
                params.append(1 if data['is_enabled'] else 0)
            
            if 'consent_text' in data:
                update_fields.append("ConsentText = %s")
                params.append(data['consent_text'])
            
            if updated_by_id:
                update_fields.append("UpdatedBy = %s")
                params.append(updated_by_id)
            
            update_fields.append("UpdatedAt = NOW()")
            params.append(config_id)
            
            cursor.execute(f"""
                UPDATE consent_configuration_tprm 
                SET {', '.join(update_fields)}
                WHERE ConfigId = %s
            """, params)
            
            tprm_connection.commit()
            
            # Fetch updated config
            cursor.execute("""
                SELECT ConfigId, ActionType, ActionLabel, IsEnabled, ConsentText, 
                       FrameworkId, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt
                FROM consent_configuration_tprm
                WHERE ConfigId = %s
            """, [config_id])
            columns = [col[0] for col in cursor.description]
            config = dict(zip(columns, cursor.fetchone()))
        
        return Response({
            'status': 'success',
            'message': 'Consent configuration updated successfully',
            'data': config
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"[TPRM Consent] Error updating consent configuration: {str(e)}")
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
        
        # Use TPRM database connection
        try:
            tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connections['default']
        except:
            tprm_connection = connections['default']
        
        updated_configs = []
        
        try:
            with tprm_connection.cursor() as cursor:
                for config_data in configs_data:
                    config_id = config_data.get('config_id')
                    if not config_id:
                        continue
                    
                    try:
                        update_fields = []
                        params = []
                        
                        if 'is_enabled' in config_data:
                            update_fields.append("IsEnabled = %s")
                            params.append(1 if config_data['is_enabled'] else 0)
                        
                        if 'consent_text' in config_data:
                            update_fields.append("ConsentText = %s")
                            params.append(config_data['consent_text'])
                        
                        if updated_by_id:
                            update_fields.append("UpdatedBy = %s")
                            params.append(updated_by_id)
                        
                        update_fields.append("UpdatedAt = NOW()")
                        
                        # Add config_id as the last parameter for WHERE clause
                        params.append(config_id)
                        
                        cursor.execute(f"""
                            UPDATE consent_configuration_tprm 
                            SET {', '.join(update_fields)}
                            WHERE ConfigId = %s
                        """, params)
                        
                        logger.info(f"[TPRM Consent] Updated config {config_id}")
                    
                    except Exception as e:
                        logger.warning(f"[TPRM Consent] Error updating consent configuration {config_id}: {e}")
                        continue
                
                # Commit all changes after all updates
                tprm_connection.commit()
                logger.info(f"[TPRM Consent] Committed {len([c for c in configs_data if c.get('config_id')])} configuration updates")
            
            # Fetch all updated configs after commit
            with tprm_connection.cursor() as cursor:
                for config_data in configs_data:
                    config_id = config_data.get('config_id')
                    if not config_id:
                        continue
                    
                    try:
                        cursor.execute("""
                            SELECT ConfigId, ActionType, ActionLabel, IsEnabled, ConsentText, 
                                   FrameworkId, CreatedBy, CreatedAt, UpdatedBy, UpdatedAt
                            FROM consent_configuration_tprm
                            WHERE ConfigId = %s
                        """, [config_id])
                        columns = [col[0] for col in cursor.description]
                        row = cursor.fetchone()
                        if row:
                            config = dict(zip(columns, row))
                            updated_configs.append(config)
                    except Exception as e:
                        logger.warning(f"[TPRM Consent] Error fetching updated config {config_id}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"[TPRM Consent] Error in bulk update transaction: {str(e)}", exc_info=True)
            tprm_connection.rollback()
            return Response({
                'status': 'error',
                'message': f'Failed to update configurations: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'status': 'success',
            'message': f'{len(updated_configs)} consent configurations updated successfully',
            'data': updated_configs
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"[TPRM Consent] Error bulk updating consent configurations: {str(e)}")
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
    Check if consent is required for a specific TPRM action
    Body: { "action_type": "tprm_create_sla", "framework_id": 1 (optional), "user_id": 1 (optional) }
    Returns: { "required": true/false, "config": {...}, "has_active_consent": true/false }
    """
    try:
        data = request.data
        action_type = data.get('action_type')
        framework_id = data.get('framework_id', '1')  # Default to 1 for TPRM
        user_id = data.get('user_id')
        
        logger.info(f"[TPRM Consent] Checking consent requirement - action_type: {action_type}, framework_id: {framework_id}, user_id: {user_id}")
        
        if not action_type:
            logger.error(f"[TPRM Consent] Missing action_type in request")
            return Response({
                'status': 'error',
                'message': 'action_type is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use TPRM database connection
        try:
            tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connections['default']
            logger.info(f"[TPRM Consent] Using TPRM database: {tprm_connection.settings_dict.get('NAME', 'default')}")
        except Exception as conn_error:
            tprm_connection = connections['default']
            logger.warning(f"[TPRM Consent] Error getting TPRM connection, using default: {conn_error}")
        
        with tprm_connection.cursor() as cursor:
            # Check for consent configuration - don't filter by FrameworkId strictly
            # TPRM consent configurations may use different FrameworkId values
            logger.info(f"[TPRM Consent] Querying consent_configuration_tprm for ActionType: {action_type}")
            cursor.execute("""
                SELECT ConfigId, ActionType, ActionLabel, IsEnabled, ConsentText, FrameworkId
                FROM consent_configuration_tprm
                WHERE ActionType = %s
                ORDER BY FrameworkId
                LIMIT 1
            """, [action_type])
            
            row = cursor.fetchone()
            
            if row:
                columns = [col[0] for col in cursor.description]
                config = dict(zip(columns, row))
                is_enabled = bool(config.get('IsEnabled', 0))
                config_framework_id = config.get('FrameworkId')
                
                logger.info(f"[TPRM Consent] ✅ Found config for {action_type}: ConfigId={config['ConfigId']}, IsEnabled={is_enabled}, FrameworkId={config_framework_id}, requested FrameworkId={framework_id}")
                
                # Check if user has active consent (not withdrawn)
                # Use the config's FrameworkId instead of the requested one
                has_active_consent = None
                if user_id and is_enabled:
                    # Use the config's FrameworkId for checking acceptance
                    consent_check_framework_id = config_framework_id or framework_id
                    logger.info(f"[TPRM Consent] Checking active consent for user {user_id}, action {action_type}, FrameworkId: {consent_check_framework_id}")
                    
                    # Check if user has an active consent (accepted and not withdrawn)
                    cursor.execute("""
                        SELECT AcceptanceId, AcceptedAt
                        FROM consent_acceptance_tprm
                        WHERE UserId = %s AND ActionType = %s AND FrameworkId = %s
                        ORDER BY AcceptedAt DESC
                        LIMIT 1
                    """, [user_id, action_type, consent_check_framework_id])
                    
                    acceptance_row = cursor.fetchone()
                    
                    if acceptance_row:
                        acceptance_id, accepted_at = acceptance_row
                        # Check if there's a withdrawal after this acceptance
                        cursor.execute("""
                            SELECT WithdrawalId
                            FROM consent_withdrawal_tprm
                            WHERE UserId = %s AND ActionType = %s AND FrameworkId = %s
                            AND WithdrawnAt > %s
                            LIMIT 1
                        """, [user_id, action_type, consent_check_framework_id, accepted_at])
                        
                        withdrawal_row = cursor.fetchone()
                        has_active_consent = withdrawal_row is None
                    else:
                        has_active_consent = False
                
                # Format config for response
                config_data = {
                    'config_id': config['ConfigId'],
                    'action_type': config['ActionType'],
                    'action_label': config['ActionLabel'],
                    'consent_text': config['ConsentText'],
                    'framework_id': config['FrameworkId']
                }
                
                logger.info(f"[TPRM Consent] Returning consent check result: required={is_enabled}, has_active_consent={has_active_consent}, config_id={config_data['config_id']}")
                return Response({
                    'status': 'success',
                    'required': is_enabled,
                    'config': config_data,
                    'has_active_consent': has_active_consent
                }, status=status.HTTP_200_OK)
            else:
                # If no config exists, consent is not required
                logger.warning(f"[TPRM Consent] ⚠️ No consent configuration found for action_type: {action_type}")
                logger.warning(f"[TPRM Consent] Please verify that 'Create SLA' consent is enabled in the Consent Configuration page")
                return Response({
                    'status': 'success',
                    'required': False,
                    'config': None,
                    'has_active_consent': None
                }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"[TPRM Consent] Error checking consent requirement: {str(e)}")
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
        "action_type": "tprm_create_sla",
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
        framework_id = data.get('framework_id', '1')
        
        if not all([user_id, config_id, action_type, framework_id]):
            return Response({
                'status': 'error',
                'message': 'user_id, config_id, action_type, and framework_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get IP address from request if not provided
        ip_address = data.get('ip_address')
        if not ip_address:
            ip_address = get_client_ip(request)
        
        # Get user agent from request if not provided
        user_agent = data.get('user_agent')
        if not user_agent:
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Use TPRM database connection
        try:
            tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connections['default']
        except:
            tprm_connection = connections['default']
        
        with tprm_connection.cursor() as cursor:
            # Verify config exists
            cursor.execute("""
                SELECT ConfigId FROM consent_configuration_tprm WHERE ConfigId = %s
            """, [config_id])
            if not cursor.fetchone():
                return Response({
                    'status': 'error',
                    'message': 'Consent configuration not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Create consent acceptance record
            cursor.execute("""
                INSERT INTO consent_acceptance_tprm 
                (UserId, ConfigId, ActionType, AcceptedAt, IpAddress, UserAgent, FrameworkId)
                VALUES (%s, %s, %s, NOW(), %s, %s, %s)
            """, [user_id, config_id, action_type, ip_address, user_agent, framework_id])
            
            acceptance_id = cursor.lastrowid
            tprm_connection.commit()
            
            # Fetch created record
            cursor.execute("""
                SELECT AcceptanceId, UserId, ConfigId, ActionType, AcceptedAt, 
                       IpAddress, UserAgent, FrameworkId
                FROM consent_acceptance_tprm
                WHERE AcceptanceId = %s
            """, [acceptance_id])
            columns = [col[0] for col in cursor.description]
            acceptance = dict(zip(columns, cursor.fetchone()))
        
        return Response({
            'status': 'success',
            'message': 'Consent acceptance recorded successfully',
            'data': acceptance
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"[TPRM Consent] Error recording consent acceptance: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_consent_acceptances(request):
    """
    Get consent acceptance history for TPRM
    Query params: framework_id (optional - defaults to 1), limit (optional - defaults to 50)
    """
    try:
        framework_id = request.GET.get('framework_id', '1')
        limit = int(request.GET.get('limit', 50))
        
        # Use TPRM database connection
        try:
            tprm_connection = connections['tprm'] if 'tprm' in connections.databases else connections['default']
        except:
            tprm_connection = connections['default']
        
        with tprm_connection.cursor() as cursor:
            # Get consent acceptances with user names
            cursor.execute("""
                SELECT 
                    ca.AcceptanceId,
                    ca.UserId,
                    ca.ConfigId,
                    ca.ActionType,
                    ca.AcceptedAt,
                    ca.IpAddress,
                    ca.UserAgent,
                    ca.FrameworkId,
                    cc.ActionLabel
                FROM consent_acceptance_tprm ca
                LEFT JOIN consent_configuration_tprm cc ON ca.ConfigId = cc.ConfigId
                WHERE ca.FrameworkId = %s
                ORDER BY ca.AcceptedAt DESC
                LIMIT %s
            """, [framework_id, limit])
            
            columns = [col[0] for col in cursor.description]
            acceptances = []
            
            for row in cursor.fetchall():
                acceptance = dict(zip(columns, row))
                # Get user name from GRC database
                try:
                    grc_connection = connections['default']
                    with grc_connection.cursor() as grc_cursor:
                        grc_cursor.execute("""
                            SELECT UserName FROM users WHERE UserId = %s
                        """, [acceptance['UserId']])
                        user_row = grc_cursor.fetchone()
                        if user_row:
                            acceptance['user_name'] = user_row[0]
                        else:
                            acceptance['user_name'] = f"User {acceptance['UserId']}"
                except:
                    acceptance['user_name'] = f"User {acceptance['UserId']}"
                
                # Format for response
                acceptances.append({
                    'AcceptanceId': acceptance['AcceptanceId'],
                    'UserId': acceptance['UserId'],
                    'ConfigId': acceptance['ConfigId'],
                    'ActionType': acceptance['ActionType'],
                    'AcceptedAt': acceptance['AcceptedAt'].isoformat() if acceptance['AcceptedAt'] else None,
                    'IpAddress': acceptance['IpAddress'],
                    'UserAgent': acceptance['UserAgent'],
                    'FrameworkId': acceptance['FrameworkId'],
                    'action_label': acceptance['ActionLabel'] or acceptance['ActionType'],
                    'user_name': acceptance['user_name']
                })
        
        return Response({
            'status': 'success',
            'message': 'Consent acceptances retrieved successfully',
            'data': acceptances
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"[TPRM Consent] Error getting consent acceptances: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

