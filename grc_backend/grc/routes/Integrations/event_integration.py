from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_protect as csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
import json
import logging

from ...models import ExternalApplication, ExternalApplicationConnection, ExternalApplicationSyncLog, Users
from .jira_backend import jira_backend
from ...rbac.utils import RBACUtils
from ...utils.log_sanitize import sanitize_for_log

logger = logging.getLogger(__name__)


def _safe_request_meta(request):
    """Return sanitized, bounded request metadata for logs."""
    method = sanitize_for_log(getattr(request, "method", ""))[:16]
    path = sanitize_for_log(getattr(request, "path", ""))[:512]
    # Log only a small allowlist of headers and sanitize values.
    allowed_headers = ("User-Agent", "Origin", "Referer", "Content-Type")
    headers = {}
    for name in allowed_headers:
        raw_val = request.headers.get(name)
        if raw_val:
            headers[name] = sanitize_for_log(str(raw_val))[:200]
    return method, path, headers


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_integration_auth(request):
    """
    Test endpoint to verify authentication is working for integrations
    """
    try:
        method, path, safe_headers = _safe_request_meta(request)
        logger.info("Test integration auth request: %s %s", method, path)
        logger.info("Request headers (sanitized): %s", safe_headers)
        
        # Get user from middleware (set by JWT middleware)
        user = getattr(request, 'user', None)
        logger.info("User from middleware present: %s", bool(user))
        
        if not user or not hasattr(user, 'UserId'):
            logger.warning("No user found in request - authentication required")
            return Response({
                'status': 'error',
                'message': 'Authentication required',
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'status': 'success',
            'message': 'Authentication working',
            'user': {
                'id': user.UserId,
                'username': user.UserName,
                'email': user.Email
            }
        })
        
    except Exception:
        logger.exception("Test integration auth error")
        return JsonResponse({
            'status': 'error',
            'message': 'Test failed due to an internal server error.'
        }, status=500)



@csrf_exempt
@require_http_methods(["GET"])
def _resolve_request_user_id(request, provided_user_id):
    """
    Safely resolve user_id from request or provided user_id.
    Returns (user_id, error_response).
    """
    auth_user = getattr(request, 'user', None)
    if not auth_user or not hasattr(auth_user, 'UserId'):
        return None, JsonResponse({'error': 'Authentication required'}, status=401)
    
    # If no user_id provided, use the authenticated user's ID
    if not provided_user_id:
        return auth_user.UserId, None
    
    try:
        user_id = int(provided_user_id)
        # If user is trying to access another user's data, check permissions
        if user_id != auth_user.UserId:
            # Check if user is admin
            if not RBACUtils.is_system_admin(auth_user.UserId):
                logger.warning(
                    "User %s unauthorized access attempt to user %s",
                    sanitize_for_log(auth_user.UserId, 32),
                    sanitize_for_log(provided_user_id, 64),
                )
                return None, JsonResponse({'error': 'Unauthorized access to other user data'}, status=403)
        
        return user_id, None
    except (ValueError, TypeError):
        return None, JsonResponse({'error': 'Invalid user_id format'}, status=400)
    except Exception:
        logger.exception("Error resolving user_id")
        return None, JsonResponse({'error': 'Internal server error resolving user'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_external_applications(request):
    """
    Get all external applications with their connection status for the current user
    """
    auth_user = getattr(request, 'user', None)
    if not auth_user or not hasattr(auth_user, 'UserId'):
        return JsonResponse({'error': 'Authentication required'}, status=401)
    try:
        # Debug logging (sanitized to prevent log injection/forging)
        method, path, safe_headers = _safe_request_meta(request)
        logger.info("External applications request: %s %s", method, path)
        logger.info("Request headers (sanitized): %s", safe_headers)
        
        user_id, auth_error = _resolve_request_user_id(request, request.GET.get('user_id'))
        if auth_error:
            return auth_error
        logger.info("Getting external applications for user_id: %s", sanitize_for_log(user_id, 32))
        
        # Get all active external applications.
        # NOTE: For some apps (e.g. Jira, Gmail) the `name` field may be stored
        # encrypted in the database, so querying/deduping by name is unreliable
        # and can lead to many duplicates. Instead we deduplicate by the
        # non‑encrypted identity tuple (category, type, icon_class).
        applications_qs = ExternalApplication.objects.filter(is_active=True).order_by(
            'category', 'type', 'icon_class', '-created_at'
        )
        logger.info("Found %s active external application rows", applications_qs.count())

        # Deduplicate by (category, type, icon_class) – keep the most recent record
        unique_apps = {}
        for app in applications_qs:
            key = (app.category, app.type, app.icon_class)
            if key not in unique_apps:
                unique_apps[key] = app

        applications = list(unique_apps.values())
        logger.info("After de-duplication: %s unique applications by category/type/icon", len(applications))
        
        applications_data = []
        connected_count = 0
        
        for app in applications:
            # Check if user has an active connection to this application
            connection = ExternalApplicationConnection.objects.filter(
                application=app,
                user_id=user_id,
                connection_status='active'
            ).first()
            
            # Determine connection status and last sync
            if connection:
                connection_status = 'connected'
                last_sync = connection.last_used or connection.created_at
                connected_count += 1
                logger.info(
                    "User %s has active connection to %s",
                    sanitize_for_log(user_id, 32),
                    sanitize_for_log(app.name, 256),
                )
            else:
                connection_status = 'disconnected'
                last_sync = None
                logger.info(
                    "User %s has no connection to %s",
                    sanitize_for_log(user_id, 32),
                    sanitize_for_log(app.name, 256),
                )

            app_data = {
                'id': app.id,
                'name': app.name,
                'category': app.category,
                'type': app.type,
                'description': app.description,
                'icon': app.icon_class,
                'version': app.version,
                'status': connection_status,
                'lastSync': last_sync.isoformat() if last_sync else None,
                'features': app.features or [],
                'api_endpoint': app.api_endpoint,
                'oauth_url': app.oauth_url
            }
            applications_data.append(app_data)

        # Calculate statistics
        total_apps = len(applications_data)
        disconnected_apps = total_apps - connected_count

        logger.info(
            "Returning %s applications: %s connected, %s disconnected",
            total_apps,
            connected_count,
            disconnected_apps,
        )

        return JsonResponse({
            'success': True,
            'applications': applications_data,
            'statistics': {
                'total': total_apps,
                'connected': connected_count,
                'disconnected': disconnected_apps
            }
        })

    except Exception:
        logger.exception("Error getting external applications")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def connect_external_application(request):
    """
    Connect to an external application
    """
    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')
        connection_token = data.get('connection_token')
        refresh_token = data.get('refresh_token')
        token_expires_at = data.get('token_expires_at')
        user_id, auth_error = _resolve_request_user_id(request, data.get('user_id'))
        if auth_error:
            return auth_error

        if not application_id:
            return JsonResponse({'error': 'Application ID is required'}, status=400)

        try:
            application = ExternalApplication.objects.get(id=application_id, is_active=True)
        except ExternalApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)

        # Get user by ID
        try:
            user = Users.objects.get(UserId=user_id)
        except Users.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        with transaction.atomic():
            # Create or update connection
            connection, created = ExternalApplicationConnection.objects.update_or_create(
                application=application,
                user=user,
                defaults={
                    'connection_token': connection_token,
                    'refresh_token': refresh_token,
                    'token_expires_at': timezone.datetime.fromisoformat(token_expires_at) if token_expires_at else None,
                    'connection_status': 'active',
                    'last_used': timezone.now()
                }
            )

            # Update application status
            application.status = 'connected'
            application.last_sync = timezone.now()
            application.save()

            # Log the connection
            ExternalApplicationSyncLog.objects.create(
                application=application,
                user=user,
                sync_type='manual',
                sync_status='success',
                records_synced=1,
                sync_started_at=timezone.now(),
                sync_completed_at=timezone.now()
            )

        return JsonResponse({
            'success': True,
            'message': f'Successfully connected to {application.name}',
            'connection_id': connection.id
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception:
        logger.exception("Error connecting to external application")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_external_application(request):
    """
    Disconnect from an external application
    """
    try:
        data = json.loads(request.body)
        application_id = data.get('application_id')
        user_id, auth_error = _resolve_request_user_id(request, data.get('user_id'))
        if auth_error:
            return auth_error

        if not application_id:
            return JsonResponse({'error': 'Application ID is required'}, status=400)

        try:
            application = ExternalApplication.objects.get(id=application_id, is_active=True)
            user = Users.objects.get(UserId=user_id)
            connection = ExternalApplicationConnection.objects.get(
                application=application,
                user=user,
                connection_status='active'
            )
        except (ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist, Users.DoesNotExist):
            return JsonResponse({'error': 'Connection not found'}, status=404)

        with transaction.atomic():
            # Update connection status
            connection.connection_status = 'revoked'
            connection.save()

            # Update application status if no other active connections
            active_connections = ExternalApplicationConnection.objects.filter(
                application=application,
                connection_status='active'
            ).count()

            if active_connections == 0:
                application.status = 'disconnected'
                application.save()

            # Log the disconnection
            ExternalApplicationSyncLog.objects.create(
                application=application,
                user=user,
                sync_type='manual',
                sync_status='success',
                records_synced=0,
                sync_started_at=timezone.now(),
                sync_completed_at=timezone.now(),
                error_message='User disconnected'
            )

        return JsonResponse({
            'success': True,
            'message': f'Successfully disconnected from {application.name}'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception:
        logger.exception("Error disconnecting from external application")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_application_details(request, application_id):
    """
    Get detailed information about a specific external application
    """
    try:
        user_id, auth_error = _resolve_request_user_id(request)
        if auth_error:
            return auth_error

        try:
            application = ExternalApplication.objects.get(id=application_id, is_active=True)
        except ExternalApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)

        user = Users.objects.filter(UserId=user_id).first()
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)

        try:
            connection = ExternalApplicationConnection.objects.get(
                application=application,
                user=user,
                connection_status='active'
            )
            connection_status = 'connected'
            last_used = connection.last_used
            token_expires_at = connection.token_expires_at
        except ExternalApplicationConnection.DoesNotExist:
            connection_status = 'disconnected'
            last_used = None
            token_expires_at = None

        # Get recent sync logs
        recent_syncs = ExternalApplicationSyncLog.objects.filter(
            application=application,
            user=user
        ).order_by('-sync_started_at')[:5]

        sync_logs = []
        for sync in recent_syncs:
            sync_logs.append({
                'id': sync.id,
                'sync_type': sync.get_sync_type_display(),
                'sync_status': sync.get_sync_status_display(),
                'records_synced': sync.records_synced,
                'sync_started_at': sync.sync_started_at.isoformat(),
                'sync_completed_at': sync.sync_completed_at.isoformat() if sync.sync_completed_at else None,
                'duration_seconds': sync.duration_seconds,
                'error_message': sync.error_message
            })

        application_data = {
            'id': application.id,
            'name': application.name,
            'category': application.category,
            'type': application.type,
            'description': application.description,
            'icon': application.icon_class,
            'version': application.version,
            'status': connection_status,
            'lastSync': last_used.isoformat() if last_used else None,
            'features': application.features or [],
            'api_endpoint': application.api_endpoint,
            'oauth_url': application.oauth_url,
            'created_at': application.created_at.isoformat(),
            'updated_at': application.updated_at.isoformat(),
            'token_expires_at': token_expires_at.isoformat() if token_expires_at else None,
            'recent_syncs': sync_logs
        }

        return JsonResponse({
            'success': True,
            'application': application_data
        })

    except Exception:
        logger.exception("Error getting application details")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_application_status(request):
    """
    Refresh the status of all external applications for the current user
    """
    try:
        user_id, auth_error = _resolve_request_user_id(request)
        if auth_error:
            return auth_error
        user = Users.objects.filter(UserId=user_id).first()
        if not user:
            return JsonResponse({'error': 'User not found'}, status=404)

        # Get all user's active connections
        connections = ExternalApplicationConnection.objects.filter(
            user=user,
            connection_status='active'
        ).select_related('application')

        refreshed_count = 0
        for connection in connections:
            # Check if token is expired
            if connection.is_token_expired():
                connection.connection_status = 'expired'
                connection.save()
                
                # Update application status if no other active connections
                active_connections = ExternalApplicationConnection.objects.filter(
                    application=connection.application,
                    connection_status='active'
                ).count()
                
                if active_connections == 0:
                    connection.application.status = 'disconnected'
                    connection.application.save()
            else:
                refreshed_count += 1

        return JsonResponse({
            'success': True,
            'message': f'Refreshed {refreshed_count} active connections',
            'refreshed_count': refreshed_count
        })

    except Exception:
        logger.exception("Error refreshing application status")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sync_logs(request, application_id):
    """
    Get sync logs for a specific external application
    """
    try:
        # Get user from middleware (set by JWT middleware)
        user = getattr(request, 'user', None)
        
        # Check if user is authenticated and is a Users model instance
        if not user or not hasattr(user, 'UserId') or user.is_anonymous:
            # Simplified response when not authenticated
            return JsonResponse({
                'success': True,
                'sync_logs': [],
                'total_count': 0
            })

        try:
            application = ExternalApplication.objects.get(id=application_id, is_active=True)
        except ExternalApplication.DoesNotExist:
            return JsonResponse({'error': 'Application not found'}, status=404)

        # Get sync logs for this application and user
        sync_logs = ExternalApplicationSyncLog.objects.filter(
            application=application,
            user=user
        ).order_by('-sync_started_at')

        logs_data = []
        for sync in sync_logs:
            logs_data.append({
                'id': sync.id,
                'sync_type': sync.get_sync_type_display(),
                'sync_status': sync.get_sync_status_display(),
                'records_synced': sync.records_synced,
                'sync_started_at': sync.sync_started_at.isoformat(),
                'sync_completed_at': sync.sync_completed_at.isoformat() if sync.sync_completed_at else None,
                'duration_seconds': sync.duration_seconds,
                'error_message': sync.error_message
            })

        return JsonResponse({
            'success': True,
            'sync_logs': logs_data,
            'total_count': len(logs_data)
        })

    except Exception:
        logger.exception("Error getting sync logs")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# Jira-specific endpoints
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def jira_oauth_callback(request):
    """
    Handle Jira OAuth callback and create connection
    """
    try:
        logger.info("Jira OAuth callback received")

        data = json.loads(request.body)
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        expires_in = data.get('expires_in')
        user_id = data.get('user_id', 1)  # Default to user ID 1 if not provided
        jira_account_info = data.get('account_info')  # Optional Jira account information

        if not access_token:
            return JsonResponse({'error': 'Access token is required'}, status=400)

        # Calculate token expiration
        token_expires_at = None
        if expires_in:
            token_expires_at = timezone.now() + timezone.timedelta(seconds=int(expires_in))

        # Save Jira connection using backend manager
        result = jira_backend.save_jira_connection(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            jira_account_info=jira_account_info
        )

        if result['success']:
            logger.info(
                "Jira OAuth callback processed successfully for user %s",
                sanitize_for_log(user_id, 32),
            )
            return JsonResponse({
                'success': True,
                'message': 'Jira OAuth callback processed successfully',
                'application': 'Jira',
                'connection_id': result.get('connection_id'),
                'created': result.get('created', False)
            })
        else:
            logger.error(f"Failed to save Jira connection: {result['error']}")
            return JsonResponse({'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception:
        logger.exception("Error handling Jira OAuth callback")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def get_jira_projects(request):
    """
    Get Jira projects and optionally save them to database
    """
    try:
        if request.method == 'GET':
            # Get projects from database or return mock data
            logger.info("Getting Jira projects")
            
            # For now, return mock data (can be enhanced to fetch from database)
            projects = [
                {
                    'id': '10001',
                    'key': 'PROJ1',
                    'name': 'Sample Project 1',
                    'projectTypeKey': 'software',
                    'description': 'A sample software project'
                },
                {
                    'id': '10002',
                    'key': 'PROJ2',
                    'name': 'Sample Project 2',
                    'projectTypeKey': 'business',
                    'description': 'A sample business project'
                }
            ]

            return JsonResponse({
                'success': True,
                'projects': projects,
                'message': 'Jira projects retrieved successfully'
            })
        
        elif request.method == 'POST':
            # Save projects data to database
            logger.info("Saving Jira projects to database")
            
            data = json.loads(request.body)
            projects_data = data.get('projects', [])
            user_id = data.get('user_id', 1)  # Default to user ID 1 if not provided
            
            if not projects_data:
                return JsonResponse({'error': 'Projects data is required'}, status=400)
            
            # Save projects using backend manager
            result = jira_backend.save_jira_projects(
                user_id=user_id,
                projects_data=projects_data
            )
            
            if result['success']:
                logger.info(
                    "Successfully saved %s Jira projects for user %s",
                    result.get("projects_count"),
                    sanitize_for_log(user_id, 32),
                )
                return JsonResponse({
                    'success': True,
                    'message': result['message'],
                    'projects_count': result['projects_count']
                })
            else:
                logger.error("Failed to save Jira projects: %s", sanitize_for_log(result.get("error"), 500))
                return JsonResponse({'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception:
        logger.exception("Error handling Jira projects")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_jira_project_details(request):
    """
    Save detailed Jira project information
    """
    try:
        logger.info("Saving Jira project details")
        
        data = json.loads(request.body)
        project_id = data.get('project_id')
        project_details = data.get('project_details')
        user_id = data.get('user_id', 1)  # Default to user ID 1 if not provided
        
        if not project_id or not project_details:
            return JsonResponse({'error': 'Project ID and project details are required'}, status=400)
        
        # Save project details using backend manager
        result = jira_backend.save_jira_project_details(
            user_id=user_id,
            project_id=project_id,
            project_details=project_details
        )
        
        if result['success']:
            logger.info(f"Successfully saved Jira project details for project {project_id}, user {user_id}")
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'project_id': result['project_id']
            })
        else:
            logger.error("Failed to save Jira project details: %s", sanitize_for_log(result.get("error"), 500))
            return JsonResponse({'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception:
        logger.exception("Error saving Jira project details")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disconnect_jira(request):
    """
    Disconnect Jira for a user
    """
    try:
        logger.info("Disconnecting Jira")
        
        data = json.loads(request.body)
        user_id = data.get('user_id', 1)  # Default to user ID 1 if not provided
        
        # Disconnect Jira using backend manager
        result = jira_backend.disconnect_jira(user_id=user_id)
        
        if result['success']:
            logger.info(f"Successfully disconnected Jira for user {user_id}")
            return JsonResponse({
                'success': True,
                'message': result['message']
            })
        else:
            logger.error("Failed to disconnect Jira: %s", sanitize_for_log(result.get("error"), 500))
            return JsonResponse({'error': result['error']}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception:
        logger.exception("Error disconnecting Jira")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_jira_connection_status(request):
    """
    Get Jira connection status for a user
    """
    try:
        user_id = request.GET.get('user_id', 1)  # Default to user ID 1 if not provided
        
        # Get connection status using backend manager
        result = jira_backend.get_jira_connection_status(user_id=user_id)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'connected': result['connected'],
                'connection_id': result.get('connection_id'),
                'last_used': result.get('last_used'),
                'token_expires_at': result.get('token_expires_at'),
                'is_token_expired': result.get('is_token_expired', False)
            })
        else:
            return JsonResponse({'error': result['error']}, status=400)

    except Exception:
        logger.exception("Error getting Jira connection status")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_jira_data(request):
    """
    Get all Jira data for a user (projects, configuration, etc.)
    """
    try:
        user_id = request.GET.get('user_id', 1)  # Default to user ID 1 if not provided
        
        # Get Jira data using backend manager
        result = jira_backend.get_jira_data(user_id=user_id)
        
        if result['success']:
            return JsonResponse({
                'success': True,
                'application': result['application'],
                'connection': result['connection']
            })
        else:
            return JsonResponse({'error': result['error']}, status=400)

    except Exception as e:
        logger.error(f"Error getting Jira data: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_stored_projects_data(request):
    """
    Get stored projects data from database for a user
    """
    try:
        user_id = request.GET.get('user_id', 1)  # Default to user ID 1 if not provided
        
        result = jira_backend.get_stored_projects_data(user_id)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception:
        logger.exception("Error getting stored projects data")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_jira_project_details_from_db(request):
    """
    Get Jira project details from database for a user
    """
    try:
        user_id = request.GET.get('user_id', 1)  # Default to user ID 1 if not provided
        project_id = request.GET.get('project_id')
        
        if not project_id:
            return JsonResponse({'error': 'project_id parameter is required'}, status=400)
        
        result = jira_backend.get_jira_project_details(user_id, project_id)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception:
        logger.exception("Error getting Jira project details")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_all_users(request):
    """
    Get all active users from the database
    """
    try:
        result = jira_backend.get_all_users()
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception:
        logger.exception("Error getting users")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def assign_project_to_users(request):
    """
    Assign a Jira project to selected users
    """
    try:
        data = json.loads(request.body)
        
        assigned_by_user_id = data.get('assigned_by_user_id')
        project_data = data.get('project_data')
        selected_users = data.get('selected_users', [])
        
        if not assigned_by_user_id:
            return JsonResponse({'error': 'assigned_by_user_id is required'}, status=400)
        
        if not project_data:
            return JsonResponse({'error': 'project_data is required'}, status=400)
        
        if not selected_users:
            return JsonResponse({'error': 'selected_users is required'}, status=400)
        
        result = jira_backend.assign_project_to_users(
            assigned_by_user_id=assigned_by_user_id,
            project_data=project_data,
            selected_users=selected_users
        )
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error assigning project to users: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_project_assignments(request):
    """
    Get project assignments
    """
    try:
        user_id = request.GET.get('user_id')
        project_id = request.GET.get('project_id')
        
        result = jira_backend.get_project_assignments(
            user_id=user_id,
            project_id=project_id
        )
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception:
        logger.exception("Error getting project assignments")
        return JsonResponse({'error': 'Internal server error'}, status=500)
