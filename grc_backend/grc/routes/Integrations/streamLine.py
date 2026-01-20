"""
Streamline Backend Integration
Handles user-specific project assignments and streamlined project views
"""
import json
import logging
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ...models import (
    Users,
    UsersProjectList,
    IntegrationDataList
)
from ...authentication import get_user_from_jwt

logger = logging.getLogger(__name__)


class StreamlineManager:
    """
    Manager class for handling streamlined project views
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_user_assigned_projects(self, user_id):
        """
        Get all projects assigned to a specific user
        
        Loads project details + issues from stored ExternalApplicationConnection.projects_data
        
        Args:
            user_id (int): User ID to get projects for
            
        Returns:
            dict: List of projects assigned to the user with full details and issues
        """
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': f'Invalid user_id format: {user_id}'
                }
            
            # Get the user
            try:
                user = Users.objects.get(UserId=user_id, IsActive='Y')
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found or inactive'
                }
            
            # Find all project assignments where the user is in the users_list
            project_assignments = UsersProjectList.objects.filter(
                is_active=True,
                users_list__contains=[user_id]  # Check if user_id is in the JSON array
            ).order_by('-created_at')
            
            # Get stored project data from ExternalApplicationConnection
            # Try to get connection from the user who assigned (or any active connection)
            stored_project_data = {}
            try:
                from ...models import ExternalApplication, ExternalApplicationConnection
                from .jira import decrypt_projects_data
                
                # Get Jira application
                jira_app = ExternalApplication.objects.filter(
                    icon_class__in=['fas fa-tasks', 'fab fa-jira'],
                    category='Project Management',
                    type='Issue Tracking'
                ).first()
                
                if jira_app:
                    # Try to get connection from assigned_by users (who have the stored data)
                    # Get unique assigned_by users from project_assignments
                    assigned_by_user_ids = list(project_assignments.values_list('assigned_by__UserId', flat=True).distinct())
                    self.logger.info(f"🔍 DEBUG: Looking for connections from assigned_by users: {assigned_by_user_ids}")
                    
                    # Collect from ALL connections, don't break early
                    checked_connections = []
                    
                    for assigned_by_id in assigned_by_user_ids:
                        try:
                            assigned_by_user = Users.objects.get(UserId=assigned_by_id)
                            connection = ExternalApplicationConnection.objects.filter(
                                application=jira_app,
                                user=assigned_by_user,
                                connection_status='active'
                            ).first()
                            
                            if connection:
                                checked_connections.append(connection.id)
                                # Decrypt projects_data
                                try:
                                    projects_data = decrypt_projects_data(connection) or {}
                                    project_details = projects_data.get('project_details', {})
                                    
                                    self.logger.info(f"🔍 DEBUG: Checking connection {connection.id} for user {assigned_by_id}")
                                    self.logger.info(f"🔍 DEBUG: Found {len(project_details)} projects in connection.projects_data")
                                    self.logger.info(f"🔍 DEBUG: Project IDs: {list(project_details.keys()) if project_details else 'None'}")
                                    
                                    # Store in our lookup dict (normalize keys to strings)
                                    for proj_id, proj_data in project_details.items():
                                        proj_id_str = str(proj_id)
                                        if proj_id_str not in stored_project_data:
                                            stored_project_data[proj_id_str] = proj_data
                                        # Also store with original key for backward compatibility
                                        if proj_id not in stored_project_data:
                                            stored_project_data[proj_id] = proj_data
                                    
                                    if project_details:
                                        self.logger.info(f"✅ Loaded {len(project_details)} projects from connection {connection.id} (user {assigned_by_id})")
                                except Exception as decrypt_error:
                                    self.logger.error(f"❌ Error decrypting projects_data from connection {connection.id}: {str(decrypt_error)}")
                                    import traceback
                                    self.logger.error(traceback.format_exc())
                                    continue
                            else:
                                self.logger.warning(f"⚠️ No active connection found for assigned_by user {assigned_by_id}")
                        except Users.DoesNotExist:
                            self.logger.warning(f"⚠️ Assigned_by user {assigned_by_id} does not exist")
                        except Exception as e:
                            self.logger.warning(f"⚠️ Error loading stored data from user {assigned_by_id}: {str(e)}")
                            continue
                    
                    # Fallback: Also check current user's connection if nothing found
                    if not stored_project_data:
                        self.logger.info(f"🔍 DEBUG: No data found from assigned_by users, checking current user's connection...")
                        try:
                            current_user = Users.objects.get(UserId=user_id)
                            current_connection = ExternalApplicationConnection.objects.filter(
                                application=jira_app,
                                user=current_user,
                                connection_status='active'
                            ).first()
                            
                            if current_connection:
                                self.logger.info(f"🔍 DEBUG: Found current user's connection {current_connection.id}")
                                projects_data = decrypt_projects_data(current_connection) or {}
                                project_details = projects_data.get('project_details', {})
                                self.logger.info(f"🔍 DEBUG: Found {len(project_details)} projects in current user's connection")
                                
                                for proj_id, proj_data in project_details.items():
                                    proj_id_str = str(proj_id)
                                    if proj_id_str not in stored_project_data:
                                        stored_project_data[proj_id_str] = proj_data
                                    if proj_id not in stored_project_data:
                                        stored_project_data[proj_id] = proj_data
                        except Exception as e:
                            self.logger.warning(f"⚠️ Error checking current user's connection: {str(e)}")
                    
                    total_found = len(stored_project_data)
                    self.logger.info(f"📊 Total stored projects found: {total_found} (checked {len(checked_connections)} connections)")
                else:
                    self.logger.warning("⚠️ Jira application not found in database")
            except Exception as e:
                self.logger.warning(f"Error loading stored project data: {str(e)}")
                # Continue without stored data - will use basic project info
            
            projects = []
            for assignment in project_assignments:
                # Check if current user is assigned to this project
                is_user_assigned = assignment.is_user_assigned(user_id)
                
                if is_user_assigned:
                    # Get assigned users details
                    assigned_users = assignment.get_assigned_users()
                    assigned_users_details = []
                    
                    for assigned_user in assigned_users:
                        assigned_users_details.append({
                            'id': assigned_user.UserId,
                            'username': assigned_user.UserName,
                            'email': assigned_user.Email,
                            'full_name': assigned_user.get_full_name()
                        })
                    
                    # Get stored project data (full details + issues)
                    project_id = assignment.project_id
                    project_id_str = str(project_id)
                    
                    # Try to find stored data (check both string and original key)
                    stored_data = stored_project_data.get(project_id_str, {})
                    if not stored_data:
                        stored_data = stored_project_data.get(project_id, {})
                    if not stored_data and stored_project_data:
                        # Try to find by matching project_id as string in any key
                        for key, value in stored_project_data.items():
                            if str(key) == project_id_str or str(key) == str(project_id):
                                stored_data = value
                                break
                    
                    # Build project response with stored data
                    project_response = {
                        'id': assignment.id,
                        'project_id': project_id,
                        'project_name': assignment.project_name,
                        'project_key': assignment.project_key,
                        'project_details': assignment.project_details,  # Basic project info
                        'assigned_users': assigned_users_details,
                        'assigned_users_count': assignment.get_assigned_users_count(),
                        'list_type': assignment.list_type,
                        'assigned_by': {
                            'id': assignment.assigned_by.UserId,
                            'username': assignment.assigned_by.UserName,
                            'full_name': assignment.assigned_by.get_full_name()
                        },
                        'created_at': assignment.created_at.isoformat(),
                        'updated_at': assignment.updated_at.isoformat(),
                        'is_current_user_assigned': True
                    }
                    
                    # Add stored full details and issues if available
                    if stored_data:
                        full_details = stored_data.get('full_details', {})
                        if full_details:
                            project_response['full_project_details'] = full_details.get('project', {})
                            project_response['components'] = full_details.get('components', [])
                            project_response['versions'] = full_details.get('versions', [])
                            
                            # Add issues/tasks
                            issues_data = full_details.get('issues', {})
                            if issues_data:
                                issues = issues_data.get('issues', [])
                                project_response['issues'] = issues
                                project_response['issues_total'] = issues_data.get('total', len(issues))
                                project_response['has_issues'] = len(issues) > 0
                                self.logger.info(f"✅ Loaded stored data for project {project_id_str}: {len(issues)} issues, {len(full_details.get('components', []))} components")
                            else:
                                project_response['issues'] = []
                                project_response['issues_total'] = 0
                                project_response['has_issues'] = False
                                self.logger.warning(f"⚠️ Stored data found for project {project_id_str} but no issues in full_details")
                            
                            project_response['data_fetched_at'] = stored_data.get('fetched_at')
                        else:
                            project_response['issues'] = []
                            project_response['issues_total'] = 0
                            project_response['has_issues'] = False
                    else:
                        # No stored data - return empty issues
                        project_response['issues'] = []
                        project_response['issues_total'] = 0
                        project_response['has_issues'] = False
                        self.logger.warning(f"❌ No stored data found for project {project_id_str} (searched in {len(stored_project_data)} stored projects)")
                    
                    projects.append(project_response)
            
            self.logger.info(f"Found {len(projects)} projects assigned to user {user_id}")
            
            return {
                'success': True,
                'projects': projects,
                'count': len(projects),
                'user_info': {
                    'id': user.UserId,
                    'username': user.UserName,
                    'email': user.Email,
                    'full_name': user.get_full_name()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user assigned projects: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_project_details_for_user(self, user_id, project_id):
        """
        Get detailed project information for a specific user and project
        
        Args:
            user_id (int): User ID
            project_id (str): Project ID
            
        Returns:
            dict: Detailed project information including stored issues/tasks when available
        """
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': f'Invalid user_id format: {user_id}'
                }
            
            # Get the user
            try:
                user = Users.objects.get(UserId=user_id, IsActive='Y')
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found or inactive'
                }
            
            # Find the project assignment
            try:
                assignment = UsersProjectList.objects.get(
                    project_id=project_id,
                    is_active=True,
                    users_list__contains=[user_id]
                )
            except UsersProjectList.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Project {project_id} not found or user not assigned to it'
                }
            
            # Get assigned users details
            assigned_users = assignment.get_assigned_users()
            assigned_users_details = []
            
            for assigned_user in assigned_users:
                assigned_users_details.append({
                    'id': assigned_user.UserId,
                    'username': assigned_user.UserName,
                    'email': assigned_user.Email,
                    'full_name': assigned_user.get_full_name()
                })
            
            # Base project details (from UsersProjectList)
            project_details = {
                'id': assignment.id,
                'project_id': assignment.project_id,
                'project_name': assignment.project_name,
                'project_key': assignment.project_key,
                'project_details': assignment.project_details,
                'assigned_users': assigned_users_details,
                'assigned_users_count': assignment.get_assigned_users_count(),
                'list_type': assignment.list_type,
                'assigned_by': {
                    'id': assignment.assigned_by.UserId,
                    'username': assignment.assigned_by.UserName,
                    'full_name': assignment.assigned_by.get_full_name()
                },
                'created_at': assignment.created_at.isoformat(),
                'updated_at': assignment.updated_at.isoformat(),
                'is_current_user_assigned': True
            }

            # Try to enrich with stored Jira project data (full details + issues)
            try:
                from ...models import ExternalApplication, ExternalApplicationConnection
                from .jira import decrypt_projects_data

                project_id_str = str(assignment.project_id)

                # Find Jira application
                jira_app = ExternalApplication.objects.filter(
                    icon_class__in=['fas fa-tasks', 'fab fa-jira'],
                    category='Project Management',
                    type='Issue Tracking'
                ).first()

                if jira_app:
                    # Use the connection of the user who assigned the project
                    assigned_by_user = assignment.assigned_by
                    connection = ExternalApplicationConnection.objects.filter(
                        application=jira_app,
                        user=assigned_by_user,
                        connection_status='active'
                    ).first()

                    if connection:
                        projects_data = decrypt_projects_data(connection) or {}
                        project_details_dict = projects_data.get('project_details', {})

                        # Look up stored project data (check string and original key)
                        stored_data = project_details_dict.get(project_id_str) or project_details_dict.get(assignment.project_id)
                        if not stored_data and project_details_dict:
                            for key, value in project_details_dict.items():
                                if str(key) == project_id_str or str(key) == str(assignment.project_id):
                                    stored_data = value
                                    break

                        if stored_data:
                            full_details = stored_data.get('full_details', {})
                            if full_details:
                                project_details['full_project_details'] = full_details.get('project', {})
                                project_details['components'] = full_details.get('components', [])
                                project_details['versions'] = full_details.get('versions', [])

                                issues_data = full_details.get('issues', {})
                                if issues_data:
                                    issues = issues_data.get('issues', [])
                                    project_details['issues'] = issues
                                    project_details['issues_total'] = issues_data.get('total', len(issues))
                                    project_details['has_issues'] = len(issues) > 0
                                else:
                                    project_details['issues'] = []
                                    project_details['issues_total'] = 0
                                    project_details['has_issues'] = False

                                project_details['data_fetched_at'] = stored_data.get('fetched_at')
                                self.logger.info(
                                    f"Loaded stored project details for user {user_id}, project {project_id_str}: "
                                    f"{len(project_details.get('issues', []))} issues"
                                )
                            else:
                                project_details['issues'] = []
                                project_details['issues_total'] = 0
                                project_details['has_issues'] = False
                        else:
                            # No stored data for this project
                            project_details['issues'] = []
                            project_details['issues_total'] = 0
                            project_details['has_issues'] = False
                    else:
                        # No connection found; return base details only
                        project_details['issues'] = []
                        project_details['issues_total'] = 0
                        project_details['has_issues'] = False
                else:
                    # No Jira application found
                    project_details['issues'] = []
                    project_details['issues_total'] = 0
                    project_details['has_issues'] = False
            except Exception as e:
                # If enrichment fails, still return base project details
                self.logger.warning(f"Error enriching project details with stored Jira data: {str(e)}")
                project_details.setdefault('issues', [])
                project_details.setdefault('issues_total', 0)
                project_details.setdefault('has_issues', False)

            self.logger.info(f"Retrieved project details for user {user_id}, project {project_id}")
            
            return {
                'success': True,
                'project': project_details
            }
            
        except Exception as e:
            self.logger.error(f"Error getting project details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_project_statistics(self, user_id):
        """
        Get statistics about user's project assignments
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: Project statistics for the user
        """
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': f'Invalid user_id format: {user_id}'
                }
            
            # Get the user
            try:
                user = Users.objects.get(UserId=user_id, IsActive='Y')
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found or inactive'
                }
            
            # Get all project assignments for the user
            project_assignments = UsersProjectList.objects.filter(
                is_active=True,
                users_list__contains=[user_id]
            )
            
            # Calculate statistics
            total_projects = project_assignments.count()
            single_user_projects = project_assignments.filter(list_type='single').count()
            multiple_user_projects = project_assignments.filter(list_type='multiple').count()
            
            # Get recent projects (last 30 days)
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            recent_projects = project_assignments.filter(created_at__gte=thirty_days_ago).count()
            
            # Get projects by platform (assuming all are Jira for now)
            jira_projects = project_assignments.count()  # All current projects are from Jira
            
            statistics = {
                'total_projects': total_projects,
                'single_user_projects': single_user_projects,
                'multiple_user_projects': multiple_user_projects,
                'recent_projects': recent_projects,
                'platforms': {
                    'jira': jira_projects
                },
                'user_info': {
                    'id': user.UserId,
                    'username': user.UserName,
                    'email': user.Email,
                    'full_name': user.get_full_name()
                }
            }
            
            self.logger.info(f"Retrieved statistics for user {user_id}: {total_projects} total projects")
            
            return {
                'success': True,
                'statistics': statistics
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user project statistics: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_task_action(self, user_id, task_data, action_type, project_data=None, platform='jira'):
        """
        Save task action performed by user to IntegrationDataList
        
        Args:
            user_id (int): User ID who performed the action
            task_data (dict): Task information
            action_type (str): Type of action performed
            project_data (dict): Optional project information
            platform (str): Platform source (jira, gmail, sentinel, bamboohr, etc.)
            
        Returns:
            dict: Result of the save operation
        """
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': f'Invalid user_id format: {user_id}'
                }
            
            # Get the user
            try:
                user = Users.objects.get(UserId=user_id, IsActive='Y')
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found or inactive'
                }
            
            # Validate and normalize platform
            valid_platforms = ['jira', 'gmail', 'sentinel', 'bamboohr', 'streamline']
            platform_lower = platform.lower() if platform else 'jira'
            
            if platform_lower not in valid_platforms:
                self.logger.warning(f"Unknown platform '{platform}', using as-is")
            
            # Prepare heading for the action
            task_name = task_data.get('summary') or task_data.get('title') or 'Untitled Task'
            task_id = task_data.get('id') or task_data.get('task_id')
            
            # Check for duplicate action (same user, task, action_type within last 5 minutes)
            five_minutes_ago = timezone.now() - timezone.timedelta(minutes=5)
            
            duplicate_check = IntegrationDataList.objects.filter(
                source=platform_lower,
                username=user.UserName,
                metadata__task_id=str(task_id),
                data__action_type=action_type,
                created_at__gte=five_minutes_ago
            ).first()
            
            if duplicate_check:
                self.logger.info(
                    f"Duplicate action detected for user {user_id}: "
                    f"Task '{task_name}', Action '{action_type}' already recorded at {duplicate_check.created_at}"
                )
                return {
                    'success': True,
                    'already_added': True,
                    'message': 'This action was already recorded recently',
                    'record_id': duplicate_check.id,
                    'action_type': action_type,
                    'task_name': task_name,
                    'platform': platform_lower,
                    'previous_timestamp': duplicate_check.created_at.isoformat(),
                    'timestamp': timezone.now().isoformat()
                }
            
            heading = f"{platform_lower.upper()} - {action_type} - {task_name}"
            
            # Prepare full data payload
            data_payload = {
                'task': task_data,
                'action_type': action_type,
                'platform': platform_lower,
                'user': {
                    'id': user.UserId,
                    'username': user.UserName,
                    'email': user.Email,
                    'full_name': user.get_full_name()
                }
            }
            
            # Add project data if provided
            if project_data:
                data_payload['project'] = project_data
            
            # Prepare metadata
            metadata = {
                'task_id': str(task_id) if task_id else None,
                'task_status': task_data.get('status'),
                'task_priority': task_data.get('priority', {}).get('name') if isinstance(task_data.get('priority'), dict) else task_data.get('priority'),
                'action_timestamp': timezone.now().isoformat(),
                'platform': platform_lower,
                'project_key': project_data.get('project_key') if project_data else None
            }
            
            # Create IntegrationDataList entry with platform as source
            integration_record = IntegrationDataList.objects.create(
                heading=heading,
                source=platform_lower,  # Store platform name in source
                username=user.UserName,
                time=timezone.now(),
                data=data_payload,
                metadata=metadata
            )
            
            self.logger.info(
                f"Saved task action for user {user_id} on platform '{platform_lower}': "
                f"Task '{task_name}', Action '{action_type}', Record ID: {integration_record.id}"
            )
            
            return {
                'success': True,
                'already_added': False,
                'message': 'Task action saved successfully',
                'record_id': integration_record.id,
                'action_type': action_type,
                'task_name': task_name,
                'platform': platform_lower,
                'timestamp': integration_record.created_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error saving task action: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_task_actions(self, user_id, limit=50, platform=None):
        """
        Get task actions performed by a specific user
        
        Args:
            user_id (int): User ID
            limit (int): Maximum number of records to return
            platform (str): Optional filter by platform (jira, gmail, sentinel, bamboohr)
            
        Returns:
            dict: List of task actions
        """
        try:
            # Convert user_id to integer if it's a string
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return {
                    'success': False,
                    'error': f'Invalid user_id format: {user_id}'
                }
            
            # Get the user
            try:
                user = Users.objects.get(UserId=user_id, IsActive='Y')
            except Users.DoesNotExist:
                return {
                    'success': False,
                    'error': f'User with ID {user_id} not found or inactive'
                }
            
            # Build query - filter by user
            query_filter = {
                'username': user.UserName
            }
            
            # Add platform filter if specified
            if platform:
                platform_lower = platform.lower()
                query_filter['source'] = platform_lower
            else:
                # Get all platform sources (not 'streamline_task_action' anymore)
                valid_platforms = ['jira', 'gmail', 'sentinel', 'bamboohr', 'streamline']
                # Filter by any of the valid platforms
                pass  # Will use username filter only
            
            # Query IntegrationDataList for user's task actions
            actions = IntegrationDataList.objects.filter(
                **query_filter
            ).order_by('-created_at')[:limit]
            
            actions_list = []
            for action in actions:
                actions_list.append({
                    'id': action.id,
                    'heading': action.heading,
                    'source': action.source,
                    'platform': action.metadata.get('platform') if action.metadata else action.source,
                    'action_type': action.data.get('action_type') if action.data else None,
                    'task': action.data.get('task') if action.data else None,
                    'project': action.data.get('project') if action.data else None,
                    'metadata': action.metadata,
                    'timestamp': action.created_at.isoformat(),
                    'time': action.time.isoformat()
                })
            
            self.logger.info(f"Retrieved {len(actions_list)} task actions for user {user_id}" + 
                           (f" on platform '{platform}'" if platform else ""))
            
            return {
                'success': True,
                'actions': actions_list,
                'count': len(actions_list),
                'platform_filter': platform if platform else 'all',
                'user_info': {
                    'id': user.UserId,
                    'username': user.UserName,
                    'full_name': user.get_full_name()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user task actions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
streamline_manager = StreamlineManager()


# API Views
@csrf_exempt
@require_http_methods(["GET"])
def get_user_projects(request):
    """
    Get all projects assigned to the current user
    """
    try:
        # Get user_id from query parameter or from authenticated user
        user_id = request.GET.get('user_id')
        
        # If no user_id in query, try to get from authenticated user
        if not user_id:
            # Try to get user from JWT token
            user = get_user_from_jwt(request)
            if user:
                user_id = user.UserId
                logger.info(f"Using authenticated user ID from JWT: {user_id}")
            elif hasattr(request, 'user') and request.user:
                user_id = request.user.UserId
                logger.info(f"Using authenticated user ID from request: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id parameter is required or user must be authenticated'}, status=400)
        
        result = streamline_manager.get_user_assigned_projects(user_id)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error in get_user_projects: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_project_details(request):
    """
    Get detailed project information for a specific project
    """
    try:
        # Get user_id from query parameter or from authenticated user
        user_id = request.GET.get('user_id')
        project_id = request.GET.get('project_id')
        
        # If no user_id in query, try to get from authenticated user
        if not user_id and hasattr(request, 'user') and request.user:
            user_id = request.user.UserId
            logger.info(f"Using authenticated user ID: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id parameter is required or user must be authenticated'}, status=400)
        
        if not project_id:
            return JsonResponse({'error': 'project_id parameter is required'}, status=400)
        
        result = streamline_manager.get_project_details_for_user(user_id, project_id)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error in get_project_details: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_user_statistics(request):
    """
    Get project statistics for the current user
    """
    try:
        # Get user_id from query parameter or from authenticated user
        user_id = request.GET.get('user_id')
        
        # If no user_id in query, try to get from authenticated user
        if not user_id:
            # Try to get user from JWT token
            user = get_user_from_jwt(request)
            if user:
                user_id = user.UserId
                logger.info(f"Using authenticated user ID from JWT: {user_id}")
            elif hasattr(request, 'user') and request.user:
                user_id = request.user.UserId
                logger.info(f"Using authenticated user ID from request: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id parameter is required or user must be authenticated'}, status=400)
        
        result = streamline_manager.get_user_project_statistics(user_id)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error in get_user_statistics: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_task_action(request):
    """
    Save a task action performed by a user
    
    Expected JSON payload:
    {
        "user_id": 1,
        "task": {
            "id": 123,
            "summary": "Task name",
            "status": "In Progress",
            "assignee": {...},
            "priority": {...}
        },
        "action_type": "Task Viewed|Task Started|Task Completed|etc",
        "project": {
            "project_id": "10001",
            "project_name": "Project Name",
            "project_key": "PROJ"
        },
        "platform": "jira|gmail|sentinel|bamboohr"
    }
    """
    try:
        # Parse JSON body
        try:
            body = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        
        # Get user_id from payload or from authenticated user
        user_id = body.get('user_id')
        
        # If no user_id in payload, try to get from authenticated user
        if not user_id:
            # Try to get user from JWT token
            user = get_user_from_jwt(request)
            if user:
                user_id = user.UserId
                logger.info(f"Using authenticated user ID from JWT: {user_id}")
            elif hasattr(request, 'user') and request.user:
                user_id = request.user.UserId
                logger.info(f"Using authenticated user ID from request: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id is required or user must be authenticated'}, status=400)
        
        # Get task data
        task_data = body.get('task')
        if not task_data:
            return JsonResponse({'error': 'task data is required'}, status=400)
        
        # Get action type (default to "Task Action")
        action_type = body.get('action_type', 'Task Action')
        
        # Get project data (optional)
        project_data = body.get('project')
        
        # Get platform (default to 'jira')
        platform = body.get('platform', 'jira')
        
        # Save the task action
        result = streamline_manager.save_task_action(
            user_id=user_id,
            task_data=task_data,
            action_type=action_type,
            project_data=project_data,
            platform=platform
        )
        
        if result['success']:
            # Return 200 for duplicate, 201 for new record
            status_code = 200 if result.get('already_added') else 201
            return JsonResponse(result, status=status_code)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error in save_task_action: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_project_tasks(request):
    """
    Save project tasks to the database
    
    Expected JSON payload:
    {
        "user_id": 1,
        "project": {
            "project_id": "10001",
            "project_name": "Project Name",
            "project_key": "PROJ"
        },
        "tasks": [
            {
                "id": "12345",
                "key": "PROJ-1",
                "summary": "Task name",
                "status": "In Progress",
                "assignee": {...},
                "priority": {...},
                ...
            },
            ...
        ],
        "platform": "jira"
    }
    """
    try:
        # Parse JSON body
        try:
            body = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        
        # Get user_id from payload or from authenticated user
        user_id = body.get('user_id')
        
        # If no user_id in payload, try to get from authenticated user
        if not user_id:
            # Try to get user from JWT token
            user = get_user_from_jwt(request)
            if user:
                user_id = user.UserId
                logger.info(f"Using authenticated user ID from JWT: {user_id}")
            elif hasattr(request, 'user') and request.user:
                user_id = request.user.UserId
                logger.info(f"Using authenticated user ID from request: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id is required or user must be authenticated'}, status=400)
        
        # Get project data
        project_data = body.get('project')
        if not project_data:
            return JsonResponse({'error': 'project data is required'}, status=400)
        
        # Get tasks array
        tasks = body.get('tasks', [])
        if not tasks:
            return JsonResponse({'error': 'tasks array is required'}, status=400)
        
        # Get platform (default to 'jira')
        platform = body.get('platform', 'jira')
        
        # Get the user
        try:
            user = Users.objects.get(UserId=user_id, IsActive='Y')
        except Users.DoesNotExist:
            return JsonResponse({'error': f'User with ID {user_id} not found or inactive'}, status=404)
        
        saved_count = 0
        skipped_count = 0
        errors = []
        
        # Save each task to IntegrationDataList
        for task in tasks:
            try:
                task_id = task.get('id') or task.get('key')
                task_summary = task.get('summary') or task.get('title') or 'Untitled Task'
                
                # Check if task already exists (same task_id, project_key, user within last 24 hours)
                # This prevents duplicate entries when tasks are refreshed
                twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
                
                existing_task = IntegrationDataList.objects.filter(
                    source=platform.lower(),
                    username=user.UserName,
                    metadata__task_id=str(task_id),
                    metadata__project_key=project_data.get('project_key'),
                    created_at__gte=twenty_four_hours_ago
                ).first()
                
                if existing_task:
                    skipped_count += 1
                    continue
                
                # Prepare heading
                heading = f"{task_summary} - {project_data.get('project_name', 'Project')}"
                
                # Prepare data payload
                data_payload = {
                    'task': task,
                    'project': project_data,
                    'action_type': 'Task Loaded',
                    'platform': platform.lower(),
                    'loaded_at': timezone.now().isoformat()
                }
                
                # Prepare metadata
                metadata = {
                    'task_id': str(task_id),
                    'task_key': task.get('key'),
                    'task_status': task.get('status'),
                    'task_priority': task.get('priority', {}).get('name') if isinstance(task.get('priority'), dict) else task.get('priority'),
                    'project_id': project_data.get('project_id'),
                    'project_key': project_data.get('project_key'),
                    'project_name': project_data.get('project_name'),
                    'platform': platform.lower(),
                    'saved_at': timezone.now().isoformat()
                }
                
                # Create IntegrationDataList entry
                integration_record = IntegrationDataList.objects.create(
                    heading=heading,
                    source=platform.lower(),
                    username=user.UserName,
                    time=timezone.now(),
                    data=data_payload,
                    metadata=metadata
                )
                
                saved_count += 1
                logger.info(f"Saved task {task_id} for user {user_id} in project {project_data.get('project_key')}")
                
            except Exception as e:
                error_msg = f"Error saving task {task.get('id', 'unknown')}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
        
        logger.info(f"Saved {saved_count} tasks, skipped {skipped_count} duplicates for user {user_id}")
        
        return JsonResponse({
            'success': True,
            'message': f'Saved {saved_count} tasks, skipped {skipped_count} duplicates',
            'saved_count': saved_count,
            'skipped_count': skipped_count,
            'total_tasks': len(tasks),
            'errors': errors if errors else None
        })
        
    except Exception as e:
        logger.error(f"Error in save_project_tasks: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_user_task_actions(request):
    """
    Get all task actions performed by a user
    Query parameters:
    - user_id: User ID (optional if authenticated)
    - limit: Maximum number of records (default: 50)
    - platform: Filter by platform (jira, gmail, sentinel, bamboohr) - optional
    """
    try:
        # Get user_id from query parameter or from authenticated user
        user_id = request.GET.get('user_id')
        
        # If no user_id in query, try to get from authenticated user
        if not user_id:
            # Try to get user from JWT token
            user = get_user_from_jwt(request)
            if user:
                user_id = user.UserId
                logger.info(f"Using authenticated user ID from JWT: {user_id}")
            elif hasattr(request, 'user') and request.user:
                user_id = request.user.UserId
                logger.info(f"Using authenticated user ID from request: {user_id}")
        
        if not user_id:
            return JsonResponse({'error': 'user_id parameter is required or user must be authenticated'}, status=400)
        
        # Get limit parameter (default to 50)
        limit = int(request.GET.get('limit', 50))
        
        # Get platform parameter (optional)
        platform = request.GET.get('platform')
        
        result = streamline_manager.get_user_task_actions(user_id, limit, platform)
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error in get_user_task_actions: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
