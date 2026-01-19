import os
import json
import requests
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.conf import settings
import logging
import urllib.parse as up

from grc.models import Users, ExternalApplication, ExternalApplicationConnection, ExternalApplicationSyncLog
from grc.utils.data_encryption import decrypt_data, is_encrypted_data

logger = logging.getLogger(__name__)

def decrypt_projects_data(connection):
    """
    Safely decrypt and parse projects_data from ExternalApplicationConnection
    
    Args:
        connection: ExternalApplicationConnection instance
        
    Returns:
        dict: Parsed projects_data as dictionary
    """
    try:
        projects_data = connection.projects_data
        
        # Handle None or empty
        if not projects_data:
            return {}
        
        # If it's already a dict (JSONField returns dict), return as-is
        if isinstance(projects_data, dict):
            return projects_data
        
        # If it's a string, try to decrypt and parse
        if isinstance(projects_data, str):
            # First, try to decrypt if encrypted
            if is_encrypted_data(projects_data):
                logger.info(f"Decrypting encrypted projects_data for connection {connection.id}")
                decrypted_str = decrypt_data(projects_data)
                if decrypted_str:
                    try:
                        return json.loads(decrypted_str)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse decrypted projects_data as JSON: {e}")
                        return {}
            else:
                # Try to parse as plain JSON
                try:
                    return json.loads(projects_data)
                except json.JSONDecodeError as e:
                    logger.warning(f"projects_data is neither encrypted nor valid JSON: {e}")
                    return {}
        
        # If it's neither dict nor string, return empty dict
        logger.warning(f"projects_data is of unexpected type: {type(projects_data)}")
        return {}
        
    except Exception as e:
        logger.error(f"Error decrypting projects_data: {str(e)}")
        return {}

def get_decrypted_token(connection):
    """
    Safely decrypt connection_token from ExternalApplicationConnection
    
    Args:
        connection: ExternalApplicationConnection instance
        
    Returns:
        str: Decrypted connection token or None
    """
    try:
        token = connection.connection_token
        if not token:
            return None
        
        # If it's encrypted, decrypt it
        if isinstance(token, str) and is_encrypted_data(token):
            logger.info(f"Decrypting encrypted connection_token for connection {connection.id}")
            decrypted_token = decrypt_data(token)
            return decrypted_token
        
        # If it's already plain text, return as-is
        return token
        
    except Exception as e:
        logger.error(f"Error decrypting connection_token: {str(e)}")
        return None

def get_or_create_jira_application():
    """
    Get or create Jira application.
    Since 'name' field is encrypted, we can't query by it directly.
    Instead, we use non-encrypted fields (icon_class, category, type) to find existing app,
    or create a new one if not found.
    """
    # Try to find existing Jira app by non-encrypted fields
    jira_app = ExternalApplication.objects.filter(
        icon_class='fas fa-tasks',
        category='Project Management',
        type='Issue Tracking'
    ).first()
    
    if jira_app:
        return jira_app, False
    
    # If not found, create new one
    jira_app = ExternalApplication.objects.create(
        name='Jira',
        category='Project Management',
        type='Issue Tracking',
        description='Jira integration for project and issue management',
        icon_class='fas fa-tasks',
        status='connected',
        is_active=True
    )
    return jira_app, True

class JiraIntegration:
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

    def get_accessible_resources(self):
        """Get accessible Jira resources from Atlassian API"""
        try:
            url = "https://api.atlassian.com/oauth/token/accessible-resources"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}: {response.text}"
                }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

    def get_current_user(self, cloud_id):
        """Get current user information from Jira"""
        try:
            url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/myself"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}: {response.text}"
                }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

    def get_projects(self, cloud_id):
        """Get all projects from Jira"""
        try:
            url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project"
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f"API returned status {response.status_code}: {response.text}"
                }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

    def get_project_details(self, cloud_id, project_id=None, project_key=None):
        """Get detailed project information.
        
        Tries both project ID and project key to be resilient to Jira differences.
        """
        try:
            project_data = None
            
            # First, try with project ID if provided
            if project_id is not None:
                project_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/{project_id}"
                project_response = requests.get(project_url, headers=self.headers, timeout=30)
                
                if project_response.status_code == 200:
                    project_data = project_response.json()
                else:
                    logger.warning(f"Failed to fetch project by ID {project_id}: {project_response.status_code} {project_response.text}")
            
            # If project not found by ID, try with project key (if available)
            if project_data is None and project_key:
                project_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/{project_key}"
                project_response = requests.get(project_url, headers=self.headers, timeout=30)
                
                if project_response.status_code == 200:
                    project_data = project_response.json()
                else:
                    logger.warning(f"Failed to fetch project by key {project_key}: {project_response.status_code} {project_response.text}")
            
            if project_data is None:
                return {
                    'success': False,
                    'error': f"Failed to fetch project: {project_response.status_code if 'project_response' in locals() else 'unknown'}"
                }
            
            # Use the actual project ID and key from the successfully fetched project data
            # This ensures we use the correct identifiers even if the project was fetched by key
            actual_project_id = project_data.get('id')
            actual_project_key = project_data.get('key')
            
            # Get project components - use actual project ID or key from fetched project
            components_data = []
            try:
                # Try with actual project ID first
                if actual_project_id:
                    components_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/{actual_project_id}/components"
                    components_response = requests.get(components_url, headers=self.headers, timeout=30)
                    if components_response.status_code == 200:
                        components_data = components_response.json()
                    else:
                        logger.warning(f"Failed to fetch components by ID {actual_project_id}: {components_response.status_code}")
                
                # If that failed, try with project key
                if not components_data and actual_project_key:
                    components_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/{actual_project_key}/components"
                    components_response = requests.get(components_url, headers=self.headers, timeout=30)
                    if components_response.status_code == 200:
                        components_data = components_response.json()
            except Exception as e:
                logger.warning(f"Failed to fetch components: {str(e)}")
            
            # Get project versions - use actual project ID or key from fetched project
            versions_data = []
            try:
                # Try with actual project ID first
                if actual_project_id:
                    versions_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/{actual_project_id}/versions"
                    versions_response = requests.get(versions_url, headers=self.headers, timeout=30)
                    if versions_response.status_code == 200:
                        versions_data = versions_response.json()
                    else:
                        logger.warning(f"Failed to fetch versions by ID {actual_project_id}: {versions_response.status_code}")
                
                # If that failed, try with project key
                if not versions_data and actual_project_key:
                    versions_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/{actual_project_key}/versions"
                    versions_response = requests.get(versions_url, headers=self.headers, timeout=30)
                    if versions_response.status_code == 200:
                        versions_data = versions_response.json()
            except Exception as e:
                logger.warning(f"Failed to fetch versions: {str(e)}")
            
            # Get project issues (first 50) - JQL requires project key, not ID
            # IMPORTANT: Use the new /rest/api/3/search/jql endpoint (migrated from deprecated /rest/api/3/search)
            issues_data = {"issues": [], "total": 0}
            try:
                # Use the new /rest/api/3/search/jql endpoint with POST method
                # The old /rest/api/3/search endpoint was deprecated and removed
                search_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search/jql"
                
                if actual_project_key:
                    # Try different JQL formats - some Jira instances prefer different syntax
                    # Start with simplest format first
                    jql_formats = [
                        f'project={actual_project_key}',  # Simplest format (no spaces, no quotes)
                        f'project = {actual_project_key}',  # With spaces
                        f'project = "{actual_project_key}"',  # With quotes
                        f'project="{actual_project_key}"',  # Without spaces, with quotes
                    ]
                    
                    for jql_query in jql_formats:
                        # Use POST with JSON body (required for /rest/api/3/search/jql endpoint)
                        # Request all necessary fields
                        search_payload = {
                            'jql': jql_query,
                            'maxResults': 50,
                            'fields': ['summary', 'status', 'assignee', 'priority', 'updated', 'created', 'issuetype', 'description']
                        }
                        post_headers = {**self.headers, 'Content-Type': 'application/json'}
                        try:
                            issues_response = requests.post(
                                search_url,
                                headers=post_headers,
                                json=search_payload,
                                timeout=30
                            )
                            if issues_response.status_code == 200:
                                issues_data = issues_response.json()
                                logger.info(f"Successfully fetched {len(issues_data.get('issues', []))} issues for project {actual_project_key} using JQL: {jql_query}")
                                break
                            elif issues_response.status_code == 400:
                                # Bad JQL syntax, try next format
                                logger.debug(f"JQL format failed (400): {jql_query}, trying next format...")
                                continue
                            else:
                                logger.warning(f"Failed to fetch issues by project key {actual_project_key} with JQL '{jql_query}': {issues_response.status_code} {issues_response.text}")
                        except Exception as e:
                            logger.warning(f"Exception while trying JQL '{jql_query}': {str(e)}")
                            continue
                
                # Fallback: try with project ID if key didn't work (some Jira instances might accept it)
                if not issues_data.get('issues') and actual_project_id:
                    jql_query = f'project = {actual_project_id}'
                    search_payload = {'jql': jql_query, 'maxResults': 50}
                    post_headers = {**self.headers, 'Content-Type': 'application/json'}
                    try:
                        issues_response = requests.post(search_url, headers=post_headers, json=search_payload, timeout=30)
                        if issues_response.status_code == 200:
                            issues_data = issues_response.json()
                            logger.info(f"Successfully fetched {len(issues_data.get('issues', []))} issues for project ID {actual_project_id}")
                        else:
                            logger.warning(f"Failed to fetch issues by project ID {actual_project_id}: {issues_response.status_code} {issues_response.text}")
                    except Exception as e:
                        logger.warning(f"Exception fetching issues by project ID: {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to fetch issues: {str(e)}")
            
            # If issues couldn't be fetched but we have project data, still return success
            # with a note about issues
            if not issues_data.get('issues') and project_data:
                logger.info(f"Project details fetched successfully, but issues could not be retrieved. This may be due to API restrictions or permissions.")
                # Keep issues_data as empty but valid structure
                issues_data = {"issues": [], "total": 0, "warning": "Issues could not be fetched. This may be due to API restrictions or missing permissions."}
            
            return {
                'success': True,
                'data': {
                    'project': project_data,
                    'components': components_data,
                    'versions': versions_data,
                    'issues': issues_data
                }
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

    def get_project_issues(self, cloud_id, project_key=None, project_id=None, max_results=50):
        """Get issues/tasks for a specific Jira project"""
        try:
            # Use the new /rest/api/3/search/jql endpoint (migrated from deprecated /rest/api/3/search)
            search_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search/jql"
            issues_data = {"issues": [], "total": 0}
            
            # Build JQL queries to try
            jql_queries = []
            if project_key:
                jql_queries = [
                    f'project={project_key}',
                    f'project = {project_key}',
                    f'project = "{project_key}"',
                    f'project="{project_key}"',
                ]
            elif project_id:
                jql_queries = [
                    f'project={project_id}',
                    f'project = {project_id}',
                ]
            else:
                return {
                    'success': False,
                    'error': 'project_key or project_id is required'
                }
            
            # Try each JQL format until one works
            for jql_query in jql_queries:
                search_payload = {
                    'jql': jql_query,
                    'maxResults': max_results,
                    'fields': ['summary', 'status', 'assignee', 'priority', 'updated', 'created', 'issuetype', 'description'],
                    'startAt': 0
                }
                post_headers = {**self.headers, 'Content-Type': 'application/json'}
                
                try:
                    issues_response = requests.post(
                        search_url,
                        headers=post_headers,
                        json=search_payload,
                        timeout=30
                    )
                    
                    if issues_response.status_code == 200:
                        issues_data = issues_response.json()
                        logger.info(f"Successfully fetched {len(issues_data.get('issues', []))} issues using JQL: {jql_query}")
                        break
                    elif issues_response.status_code == 400:
                        # Bad JQL syntax, try next format
                        logger.debug(f"JQL format failed (400): {jql_query}, trying next format...")
                        continue
                    elif issues_response.status_code == 410:
                        # API deprecated - log and try next format
                        logger.warning(f"JQL format returned 410 (deprecated): {jql_query}, trying next format...")
                        continue
                    else:
                        logger.warning(f"Failed to fetch issues with JQL '{jql_query}': {issues_response.status_code} {issues_response.text}")
                        continue
                except Exception as e:
                    logger.warning(f"Exception while trying JQL '{jql_query}': {str(e)}")
                    continue
            
            if not issues_data.get('issues'):
                return {
                    'success': False,
                    'error': f'Failed to fetch issues for project {project_key or project_id} with all JQL formats'
                }
            
            return {
                'success': True,
                'data': issues_data
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

@csrf_exempt
@require_http_methods(["GET"])
def jira_oauth(request):
    """Handle Jira OAuth initiation - redirects directly to Atlassian"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        # Get OAuth configuration from Django settings
        client_id = getattr(settings, 'JIRA_CLIENT_ID', '')
        redirect_uri = getattr(settings, 'JIRA_REDIRECT_URI', 'http://127.0.0.1:8000/api/jira/oauth-callback/')
        scopes = getattr(settings, 'JIRA_SCOPES', 'read:jira-user read:jira-work')
        use_local_dev = getattr(settings, 'USE_LOCAL_DEVELOPMENT', True)
        
        # Force local redirect URI if in local development mode
        if use_local_dev:
            redirect_uri = 'http://127.0.0.1:8000/api/jira/oauth-callback/'
        else:
            # Ensure production redirect URI is clean (no quotes, no extra whitespace)
            redirect_uri = str(redirect_uri).strip().strip("'\"")
            # Fallback if somehow empty
            if not redirect_uri:
                redirect_uri = 'https://grc-backend.vardaands.com/api/jira/oauth-callback'
        
        # CRITICAL: Strip quotes from all parameters (they might be stored with quotes in env vars)
        def clean_value(value):
            """Remove quotes from anywhere in the string"""
            if not value:
                return ''
            original = str(value)
            value = str(value).strip()
            # Remove quotes from start and end multiple times to handle nested quotes
            while (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1].strip()
            # Also use strip to remove any remaining quotes
            value = value.strip("'\"")
            # Log if we removed quotes
            if original != value:
                logger.info(f"Cleaned value: '{original}' -> '{value}'")
            return value
        
        # Log raw values before cleaning
        logger.info(f"Raw values from settings:")
        logger.info(f"  Raw client_id: {repr(client_id)}")
        logger.info(f"  Raw scopes: {repr(scopes)}")
        logger.info(f"  Raw redirect_uri: {repr(redirect_uri)}")
        
        client_id = clean_value(client_id) if client_id else ''
        scopes = clean_value(scopes) if scopes else 'read:jira-user read:jira-work'
        redirect_uri = clean_value(redirect_uri)
        
        # Log cleaned values
        logger.info(f"Cleaned values:")
        logger.info(f"  Clean client_id: {repr(client_id)}")
        logger.info(f"  Clean scopes: {repr(scopes)}")
        logger.info(f"  Clean redirect_uri: {repr(redirect_uri)}")
        
        logger.info(f"Jira OAuth - USE_LOCAL_DEVELOPMENT: {use_local_dev}, Redirect URI: {redirect_uri}")
        
        # Validate all required parameters
        if not client_id:
            logger.error("Jira OAuth - CLIENT_ID is empty or missing")
            return JsonResponse({
                'success': False,
                'error': 'Jira OAuth not configured - missing CLIENT_ID'
            })
        
        if not redirect_uri:
            logger.error("Jira OAuth - REDIRECT_URI is empty or missing")
            return JsonResponse({
                'success': False,
                'error': 'Jira OAuth not configured - missing REDIRECT_URI'
            })
        
        if not scopes:
            logger.error("Jira OAuth - SCOPES is empty or missing")
            return JsonResponse({
                'success': False,
                'error': 'Jira OAuth not configured - missing SCOPES'
            })
        
        # Ensure session exists and is saved before storing state
        if not request.session.session_key:
            request.session.create()
        
        # Store user_id in session for callback
        request.session['jira_user_id'] = user_id
        
        # Generate state parameter for security
        import secrets
        state = secrets.token_urlsafe(24)
        request.session['jira_oauth_state'] = state
        request.session.modified = True  # Mark session as modified
        request.session.save()  # Explicitly save session to prevent conflicts
        
        # Check if we should force consent (useful for 409 conflicts)
        # 409 Conflict errors often occur when there's an existing consent session
        # Adding prompt=consent helps avoid these conflicts
        force_consent = request.GET.get('force_consent', 'true').lower() == 'true'  # Default to true to avoid 409s
        prompt_param = 'consent' if force_consent else None
        
        # Build Atlassian OAuth URL with correct parameters
        # Ensure all values are clean (no quotes)
        oauth_params = {
            'client_id': clean_value(client_id),
            'scope': clean_value(scopes),
            'response_type': 'code',
            'redirect_uri': clean_value(redirect_uri),
            'state': str(state).strip(),
            'audience': 'api.atlassian.com'
        }
        
        # Add prompt parameter to force consent screen (helps avoid 409 conflicts)
        # This ensures a fresh consent flow and prevents conflicts with existing sessions
        if prompt_param:
            oauth_params['prompt'] = prompt_param
            logger.info(f"Jira OAuth - Using prompt=consent to avoid 409 conflicts")
        
        # Validate no empty values
        for key, value in oauth_params.items():
            if not value:
                logger.error(f"Jira OAuth - Parameter '{key}' is empty!")
                return JsonResponse({
                    'success': False,
                    'error': f'OAuth parameter {key} is empty or invalid'
                })
        
        # Log the parameters being sent (without sensitive data)
        logger.info(f"Jira OAuth Parameters:")
        logger.info(f"  client_id: {oauth_params['client_id'][:20]}... (length: {len(oauth_params['client_id'])})")
        logger.info(f"  redirect_uri: {oauth_params['redirect_uri']}")
        logger.info(f"  scope: {oauth_params['scope']}")
        logger.info(f"  state: {oauth_params['state'][:20]}...")
        logger.info(f"  audience: {oauth_params['audience']}")
        
        atlassian_oauth_url = f"https://auth.atlassian.com/authorize?{up.urlencode(oauth_params)}"
        
        logger.info(f"Jira OAuth - Full URL (first 300 chars): {atlassian_oauth_url[:300]}")
        
        # Redirect directly to Atlassian
        return HttpResponseRedirect(atlassian_oauth_url)
        
    except Exception as e:
        logger.error(f"Jira OAuth initiation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'OAuth initiation failed: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def jira_oauth_callback(request):
    """Handle Jira OAuth callback directly from Atlassian"""
    try:
        if request.method == 'GET':
            # Handle OAuth callback from Atlassian
            code = request.GET.get('code')
            state = request.GET.get('state')
            error = request.GET.get('error')
            error_description = request.GET.get('error_description', '')
            
            # Get stored session data
            stored_state = request.session.get('jira_oauth_state')
            user_id = request.session.get('jira_user_id', 1)
            
            # Get redirect URI configuration for error messages
            redirect_uri = getattr(settings, 'JIRA_REDIRECT_URI', 'http://127.0.0.1:8000/api/jira/oauth-callback/')
            use_local_dev = getattr(settings, 'USE_LOCAL_DEVELOPMENT', True)
            scopes = getattr(settings, 'JIRA_SCOPES', 'read:jira-user read:jira-work')
            if use_local_dev:
                redirect_uri = 'http://127.0.0.1:8000/api/jira/oauth-callback/'
            else:
                redirect_uri = str(redirect_uri).strip().strip("'\"")
            
            # Verify state parameter
            if state != stored_state:
                logger.error("OAuth state mismatch")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/jira?error=state_mismatch"
                return HttpResponseRedirect(error_url)
            
            # Handle OAuth errors
            if error:
                logger.error(f"OAuth error: {error} - {error_description}")
                
                # Provide more helpful error messages for common issues
                if error == 'unauthorized_client' and 'redirect_uri' in error_description.lower():
                    logger.error(f"REDIRECT URI NOT REGISTERED: The redirect URI '{redirect_uri}' is not registered in your Atlassian OAuth app.")
                    logger.error(f"Please add this URI to your Atlassian OAuth app settings at: https://developer.atlassian.com/console/myapps/")
                    logger.error(f"Current redirect URI: {redirect_uri}")
                    logger.error(f"USE_LOCAL_DEVELOPMENT: {use_local_dev}")
                    logger.error(f"To fix: Either register '{redirect_uri}' in Atlassian, or set USE_LOCAL_DEVELOPMENT=false and use a registered production URI")
                
                elif error == 'access_denied' or 'jira site' in error_description.lower():
                    logger.error(f"ACCESS DENIED: {error_description}")
                    logger.error(f"This usually means:")
                    logger.error(f"  1. You don't have a Jira account/site - Create one at https://www.atlassian.com/software/jira")
                    logger.error(f"  2. Your OAuth app needs permissions - Check app settings at https://developer.atlassian.com/console/myapps/")
                    logger.error(f"  3. The app needs approval for your Jira site - Grant access when prompted")
                    logger.error(f"  4. Your account doesn't have permission to access the Jira site")
                    logger.error(f"Current scopes: {scopes}")
                    logger.error(f"Make sure your OAuth app has 'Jira' product access enabled in the Atlassian Developer Console")
                
                # Handle 409 Conflict errors (consent conflicts)
                elif 'conflict' in error_description.lower() or error == 'conflict':
                    logger.error(f"409 CONFLICT ERROR: {error_description}")
                    logger.error(f"This usually means there's a conflicting authorization session.")
                    logger.error(f"Try again with ?force_consent=true parameter to force re-authorization")
                    logger.error(f"Or clear your browser cookies/session and try again")
                
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                # Pass error_description to frontend for better error display
                error_param = f"{error}&error_description={up.quote(error_description)}" if error_description else error
                error_url = f"{frontend_base}/integration/jira?error={error_param}"
                return HttpResponseRedirect(error_url)
            
            if not code:
                logger.error("No authorization code received")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/jira?error=no_code"
                return HttpResponseRedirect(error_url)
            
            # Exchange code for access token
            try:
                client_id = getattr(settings, 'JIRA_CLIENT_ID', '')
                client_secret = getattr(settings, 'JIRA_CLIENT_SECRET', '')
                # redirect_uri and use_local_dev already defined above for error handling
                
                logger.info(f"Jira OAuth Callback - USE_LOCAL_DEVELOPMENT: {use_local_dev}, Redirect URI: {redirect_uri}")
                
                if not client_id or not client_secret:
                    logger.error("Jira OAuth credentials not configured")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/jira?error=oauth_not_configured"
                    return HttpResponseRedirect(error_url)
                
                # Exchange code for token
                # NOTE: For Atlassian OAuth 2.0 (3LO) the token endpoint typically expects:
                # grant_type, code, redirect_uri, client_id, client_secret.
                # The audience parameter is used in some flows but can cause issues here,
                # so we omit it to avoid 401 access_denied errors during token exchange.
                token_url = "https://auth.atlassian.com/oauth/token"
                token_data = {
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri,
                    'client_id': client_id,
                    'client_secret': client_secret
                }
                
                token_headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
                
                logger.info("Exchanging code for token with Atlassian")
                token_response = requests.post(token_url, data=token_data, headers=token_headers, timeout=30)
                
                if token_response.status_code != 200:
                    logger.error(f"Token exchange failed: {token_response.status_code} {token_response.text}")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/jira?error=token_exchange_failed"
                    return HttpResponseRedirect(error_url)
                
                token_json = token_response.json()
                access_token = token_json.get('access_token')
                
                if not access_token:
                    logger.error("No access token in response")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/jira?error=no_access_token"
                    return HttpResponseRedirect(error_url)
                
                logger.info(f"Access token received: {access_token[:20]}...")
                
                # Fetch accessible resources immediately after successful authentication
                logger.info("Fetching accessible Jira resources...")
                jira_integration = JiraIntegration(access_token)
                resources_result = jira_integration.get_accessible_resources()
                
                resources_data = []
                if resources_result['success']:
                    resources_data = resources_result['data']
                    logger.info(f"Successfully fetched {len(resources_data)} accessible resources")
                else:
                    logger.warning(f"Failed to fetch resources during OAuth: {resources_result['error']}")
                    # Don't fail the OAuth process if resources can't be fetched
                    # They can be fetched later when needed
                
                # Save the access token and connection details
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app, created = get_or_create_jira_application()
                    
                    # Update the application status to connected
                    jira_app.status = 'connected'
                    jira_app.save()
                    if created:
                        logger.info("Created new Jira application with 'connected' status")
                    else:
                        logger.info("Updated existing Jira application status to 'connected'")
                    
                    # Prepare projects_data with resources information
                    projects_data = {
                        'access_token': access_token,
                        'connected_at': datetime.now().isoformat(),
                        'resources': resources_data,
                        'last_sync': datetime.now().isoformat(),
                        'sync_status': 'success' if resources_data else 'pending'
                    }
                    
                    connection, created = ExternalApplicationConnection.objects.update_or_create(
                        application=jira_app,
                        user=user,
                        defaults={
                            'connection_token': access_token,
                            'connection_status': 'active',
                            'token_expires_at': datetime.now() + timedelta(days=365),
                            'projects_data': projects_data,
                            'last_used': datetime.now()
                        }
                    )
                    
                    if created:
                        logger.info(f"Created new Jira connection for user {user_id}")
                    else:
                        logger.info(f"Updated existing Jira connection for user {user_id}")
                    
                    # Create sync log
                    ExternalApplicationSyncLog.objects.create(
                        application=jira_app,
                        user=user,
                        sync_type='manual',
                        sync_status='success' if resources_data else 'pending',
                        records_synced=len(resources_data),
                        sync_started_at=datetime.now(),
                        sync_completed_at=datetime.now()
                    )
                    
                    logger.info(f"✅ Successfully saved Jira connection with {len(resources_data)} resources")
                    logger.info(f"📊 DEBUG: Connection ID: {connection.id}, User ID: {user_id}")
                    try:
                        resource_names = []
                        for r in resources_data:
                            if isinstance(r, dict):
                                resource_names.append(r.get('name', r.get('id', str(r))))
                            else:
                                resource_names.append(str(r))
                        logger.info(f"📊 DEBUG: Resources saved: {resource_names}")
                    except Exception as e:
                        logger.info(f"📊 DEBUG: Resources saved (error formatting): {resources_data}")
                    logger.info(f"📊 DEBUG: Connection status: {connection.connection_status}")
                    logger.info(f"📊 DEBUG: Connection has token: {bool(connection.connection_token)}")
                    
                    # Verify connection was saved correctly
                    verify_connection = ExternalApplicationConnection.objects.filter(
                        application=jira_app,
                        user=user,
                        connection_status='active'
                    ).first()
                    if verify_connection:
                        try:
                            verify_projects_data = decrypt_projects_data(verify_connection)
                            verify_resources = verify_projects_data.get('resources', []) if verify_projects_data else []
                            logger.info(f"✅ VERIFIED: Connection found in DB - ID: {verify_connection.id}, Resources count: {len(verify_resources)}")
                        except Exception as e:
                            logger.info(f"✅ VERIFIED: Connection found in DB - ID: {verify_connection.id} (error reading resources: {str(e)})")
                    else:
                        logger.error(f"❌ VERIFICATION FAILED: Connection NOT found in DB immediately after saving!")
                    
                    # Store success flag in session temporarily (token is already saved in DB)
                    request.session['jira_oauth_success'] = True
                    request.session['jira_oauth_user_id'] = user_id
                    
                    # Clear OAuth state data
                    request.session.pop('jira_oauth_state', None)
                    request.session.pop('jira_user_id', None)
                    
                    # Redirect back to frontend without token (to avoid URL length limit)
                    # Frontend will load stored data from database
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    frontend_url = f"{frontend_base}/integration/jira?success=true&user_id={user_id}"
                    
                    logger.info(f"Redirecting to frontend: {frontend_url}")
                    return HttpResponseRedirect(frontend_url)
                    
                except Users.DoesNotExist:
                    logger.error("User not found")
                    frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                    error_url = f"{frontend_base}/integration/jira?error=user_not_found"
                    return HttpResponseRedirect(error_url)
                    
            except requests.RequestException as e:
                logger.error(f"Request error during token exchange: {str(e)}")
                frontend_base = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
                error_url = f"{frontend_base}/integration/jira?error=network_error"
                return HttpResponseRedirect(error_url)
        
        elif request.method == 'POST':
            # Handle POST callback data from frontend
            data = json.loads(request.body)
            access_token = data.get('access_token')
            user_id = data.get('user_id', 1)
            account_info = data.get('account_info', {})
            
            if access_token:
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app, created = get_or_create_jira_application()
                    
                    connection, created = ExternalApplicationConnection.objects.update_or_create(
                        application=jira_app,
                        user=user,
                        defaults={
                            'connection_token': access_token,
                            'connection_status': 'active',
                            'token_expires_at': datetime.now() + timedelta(days=365),
                            'projects_data': {
                                'access_token': access_token,
                                'connected_at': datetime.now().isoformat(),
                                'account_info': account_info
                            }
                        }
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Jira connection established successfully',
                        'connection_id': connection.id
                    })
                    
                except Users.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'User not found'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No access token provided'
                })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Jira OAuth callback error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'OAuth callback failed: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def jira_projects(request):
    """Handle Jira projects requests"""
    try:
        if request.method == 'GET':
            # Get stored projects data
            user_id = request.GET.get('user_id', 1)
            
            try:
                user = Users.objects.get(UserId=user_id)
                jira_app, _ = get_or_create_jira_application()
                connection = ExternalApplicationConnection.objects.get(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                )
                
                # Decrypt projects_data if needed
                projects_data = decrypt_projects_data(connection)
                if projects_data:
                    projects_list = projects_data.get('projects', [])
                    
                    # If no projects array, try to extract from project_details
                    if not projects_list or len(projects_list) == 0:
                        project_details = projects_data.get('project_details', {})
                        if project_details:
                            # Convert project_details dict to projects array
                            projects_list = []
                            for project_id, project_info in project_details.items():
                                project_obj = project_info.get('project', {})
                                if project_obj:
                                    projects_list.append(project_obj)
                                else:
                                    # If no nested project object, construct from available data
                                    projects_list.append({
                                        'id': project_id,
                                        'key': project_info.get('project_key', ''),
                                        'name': project_info.get('project_name', ''),
                                        'projectTypeKey': project_info.get('project_type', 'software')
                                    })
                    
                    return JsonResponse({
                        'success': True,
                        'data': projects_list,
                        'resources': projects_data.get('resources', []),
                        'last_updated': connection.updated_at.isoformat(),
                        'sync_status': projects_data.get('sync_status', 'unknown')
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'No stored projects data found'
                    })
                    
            except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': 'Jira connection not found'
                })
        
        elif request.method == 'POST':
            # Fetch fresh projects data from Jira
            data = json.loads(request.body)
            user_id = data.get('user_id', 1)
            access_token = data.get('access_token')
            cloud_id = data.get('cloud_id')
            action = data.get('action', 'fetch_projects')
            
            # If no access token provided, try to get it from stored connection
            if not access_token:
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app, _ = get_or_create_jira_application()
                    connection = ExternalApplicationConnection.objects.get(
                        application=jira_app,
                        user=user,
                        connection_status='active'
                    )
                    # Decrypt token if needed
                    access_token = get_decrypted_token(connection)
                    if not access_token:
                        logger.error("Failed to decrypt connection token")
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to retrieve access token'
                        }, status=401)
                    logger.info("Using stored connection token for fetching projects (decrypted)")
                except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                    return JsonResponse({
                        'success': False,
                        'error': 'Access token is required and no stored connection found'
                    })
            
            if not access_token:
                return JsonResponse({
                    'success': False,
                    'error': 'Access token is required'
                })
            
            if not cloud_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Cloud ID is required'
                })
            
            # Initialize Jira integration
            jira_integration = JiraIntegration(access_token)
            
            if action == 'fetch_projects':
                # First, try to get stored data as fallback
                stored_data = None
                stored_resources = None
                connection = None
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app, _ = get_or_create_jira_application()
                    connection = ExternalApplicationConnection.objects.filter(
                        application=jira_app,
                        user=user,
                        connection_status='active'
                    ).first()
                    
                    if connection:
                        projects_data = decrypt_projects_data(connection)
                        if projects_data:
                            stored_data = projects_data.get('projects', [])
                            stored_resources = projects_data.get('resources', [])
                            
                            # If no projects array, try to extract from project_details
                            if not stored_data or len(stored_data) == 0:
                                project_details = projects_data.get('project_details', {})
                                if project_details:
                                    # Convert project_details dict to projects array
                                    stored_data = []
                                    for project_id, project_info in project_details.items():
                                        project_obj = project_info.get('project', {})
                                        if project_obj:
                                            stored_data.append(project_obj)
                                        else:
                                            # If no nested project object, use the data directly
                                            stored_data.append({
                                                'id': project_id,
                                                'key': project_info.get('project_key', ''),
                                                'name': project_info.get('project_name', ''),
                                                'projectTypeKey': project_info.get('project_type', 'software')
                                            })
                                    logger.info(f"📦 Extracted {len(stored_data)} projects from project_details")
                            
                            logger.info(f"📦 Found {len(stored_data) if stored_data else 0} stored projects to use as fallback")
                except Exception as stored_error:
                    logger.warning(f"Could not retrieve stored data: {str(stored_error)}")
                
                # Try to fetch fresh projects data from API
                projects_result = jira_integration.get_projects(cloud_id)
                
                if projects_result['success']:
                    # API succeeded - fetch and store full details for each project
                    projects_list = projects_result['data']
                    logger.info(f"✅ Fetched {len(projects_list)} projects from API. Now fetching full details + issues for each...")
                    
                    # Get connection if not already retrieved
                    if not connection:
                        try:
                            user = Users.objects.get(UserId=user_id)
                            jira_app, _ = get_or_create_jira_application()
                            connection = ExternalApplicationConnection.objects.filter(
                                application=jira_app,
                                user=user,
                                connection_status='active'
                            ).first()
                        except Exception as e:
                            logger.warning(f"Could not get connection for saving: {str(e)}")
                    
                    # Fetch full details (including issues) for each project
                    projects_data_stored = decrypt_projects_data(connection) or {} if connection else {}
                    project_details_dict = projects_data_stored.get('project_details', {})
                    total_issues_fetched = 0
                    
                    for project in projects_list:
                        project_id = str(project.get('id', ''))
                        project_key = project.get('key', '')
                        project_name = project.get('name', '')
                        
                        if not project_id or not project_key:
                            continue
                        
                        try:
                            logger.info(f"🔄 Fetching full details + issues for project {project_key} (ID: {project_id})")
                            details_result = jira_integration.get_project_details(
                                cloud_id=cloud_id,
                                project_id=project_id,
                                project_key=project_key
                            )
                            
                            full_details = {}
                            issues_count = 0
                            if details_result.get('success'):
                                full_details = details_result.get('data', {})
                                issues_data = full_details.get('issues', {})
                                issues_count = len(issues_data.get('issues', [])) if isinstance(issues_data, dict) else 0
                                total_issues_fetched += issues_count
                                logger.info(f"✅ Fetched {issues_count} issues for project {project_key}")
                            else:
                                error_msg = details_result.get('error', 'Unknown error')
                                logger.warning(f"⚠️ Failed to fetch details for {project_key}: {error_msg}")
                            
                            # Store complete project data
                            complete_project_data = {
                                'project': project,  # Basic project info
                                'full_details': full_details,  # Full details with issues
                                'fetched_at': timezone.now().isoformat(),
                                'fetched_by_user_id': user_id,
                                'fetch_success': details_result.get('success', False),
                                'fetch_error': details_result.get('error') if not details_result.get('success') else None
                            }
                            
                            project_details_dict[project_id] = complete_project_data
                            
                        except Exception as e:
                            logger.error(f"❌ Error fetching details for project {project_key}: {str(e)}")
                            # Store basic project data even if details fetch fails
                            project_details_dict[project_id] = {
                                'project': project,
                                'full_details': {},
                                'fetched_at': timezone.now().isoformat(),
                                'fetched_by_user_id': user_id,
                                'fetch_success': False,
                                'fetch_error': str(e)
                            }
                    
                    # Save all project details to database
                    if connection:
                        projects_data_stored['project_details'] = project_details_dict
                        projects_data_stored['projects'] = projects_list
                        projects_data_stored['last_updated'] = timezone.now().isoformat()
                        projects_data_stored['projects_count'] = len(projects_list)
                        
                        connection.projects_data = projects_data_stored
                        connection.last_used = timezone.now()
                        connection.save()
                        
                        # Verify the save worked
                        connection.refresh_from_db()
                        verify_projects_data = decrypt_projects_data(connection) or {}
                        verify_project_details = verify_projects_data.get('project_details', {})
                        logger.info(f"💾 Stored {len(projects_list)} projects with full details in database. Total issues fetched: {total_issues_fetched}")
                        logger.info(f"✅ VERIFY: After save, found {len(verify_project_details)} projects in connection {connection.id}")
                        
                        # Log details for each stored project
                        for proj_id, proj_data in verify_project_details.items():
                            full_details = proj_data.get('full_details', {})
                            issues_data = full_details.get('issues', {})
                            issues_count = len(issues_data.get('issues', [])) if isinstance(issues_data, dict) else 0
                            logger.info(f"✅ VERIFY: Project {proj_id} - {issues_count} issues stored")
                    
                    # Return fresh data
                    return JsonResponse({
                        'success': True,
                        'data': projects_list,
                        'message': f'Projects data fetched and stored successfully. Fetched {total_issues_fetched} total issues across {len(projects_list)} projects.',
                        'from_cache': False,
                        'projects_count': len(projects_list),
                        'total_issues_fetched': total_issues_fetched
                    })
                else:
                    # API failed - use stored data if available
                    api_error = projects_result.get('error', 'Unknown error')
                    logger.warning(f"⚠️ API call failed: {api_error}. Falling back to stored data...")
                    
                    if stored_data is not None:
                        logger.info(f"✅ Returning {len(stored_data)} stored projects (API unavailable)")
                        return JsonResponse({
                            'success': True,
                            'data': stored_data,
                            'resources': stored_resources or [],
                            'message': 'Using stored projects data (API unavailable)',
                            'from_cache': True,
                            'api_error': api_error,
                            'warning': f'API returned error: {api_error}. Showing cached data.'
                        })
                    else:
                        # No stored data - return error
                        logger.error(f"❌ API failed and no stored data available")
                        return JsonResponse({
                            'success': False,
                            'error': api_error,
                            'message': 'API call failed and no stored data available'
                        }, status=401)
            
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action'
                })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Jira projects endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def jira_project_details(request):
    """Handle Jira project details requests"""
    try:
        if request.method == 'GET':
            # Get stored project details from database
            user_id = request.GET.get('user_id', 1)
            project_id = request.GET.get('project_id')
            
            if not project_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Project ID is required'
                })
            
            try:
                user = Users.objects.get(UserId=user_id)
                jira_app, _ = get_or_create_jira_application()
                connection = ExternalApplicationConnection.objects.get(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                )
                
                # Decrypt projects_data and check if project details are stored
                projects_data = decrypt_projects_data(connection)
                project_details = projects_data.get('project_details', {}) if projects_data else {}
                
                # Try to find project details - handle both string and numeric project IDs
                project_detail = None
                if project_id in project_details:
                    project_detail = project_details[project_id]
                else:
                    # Try converting project_id to string or int to match stored keys
                    project_id_str = str(project_id)
                    project_id_int = None
                    try:
                        project_id_int = int(project_id)
                    except (ValueError, TypeError):
                        pass
                    
                    if project_id_str in project_details:
                        project_detail = project_details[project_id_str]
                    elif project_id_int is not None and project_id_int in project_details:
                        project_detail = project_details[project_id_int]
                    else:
                        # Try to find by iterating through keys (handles type mismatches)
                        for key, value in project_details.items():
                            if str(key) == str(project_id) or str(key) == project_id_str:
                                project_detail = value
                                break
                
                if project_detail:
                    return JsonResponse({
                        'success': True,
                        'project_details': project_detail,
                        'last_updated': connection.updated_at.isoformat()
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Project details not found'
                    })
                    
            except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': 'Jira connection not found'
                })
        
        elif request.method == 'POST':
            # Fetch fresh project details from Jira
            data = json.loads(request.body)
            user_id = data.get('user_id', 1)
            project_id = data.get('project_id')
            project_key = data.get('project_key')  # Optional, for robustness
            access_token = data.get('access_token')
            cloud_id = data.get('cloud_id')
            
            # Validate access token - if it's a placeholder or invalid, get from stored connection
            if not access_token or access_token in ['stored_data_token', 'oauth_success'] or len(access_token) < 20:
                logger.info("Access token not provided or invalid, fetching from stored connection")
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app, _ = get_or_create_jira_application()
                    connection = ExternalApplicationConnection.objects.get(
                        application=jira_app,
                        user=user,
                        connection_status='active'
                    )
                    # Decrypt token if needed
                    access_token = get_decrypted_token(connection)
                    if not access_token:
                        logger.error("Failed to decrypt connection token")
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to retrieve access token'
                        }, status=401)
                    logger.info("Using stored connection token (decrypted)")
                    
                    # If cloud_id not provided, try to get it from stored resources
                    projects_data = decrypt_projects_data(connection)
                    if not cloud_id and projects_data:
                        resources = projects_data.get('resources', [])
                        if resources and len(resources) > 0:
                            # Use the first resource's cloud ID
                            cloud_id = resources[0].get('id')
                            logger.info(f"Using cloud ID from stored resources: {cloud_id}")
                except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                    return JsonResponse({
                        'success': False,
                        'error': 'Access token is required and no stored connection found'
                    })
            
            if not access_token or not project_id or not cloud_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Access token, project ID, and cloud ID are required'
                })
            
            # Initialize Jira integration
            jira_integration = JiraIntegration(access_token)
            
            # First, try to get stored project details as fallback
            stored_project_detail = None
            try:
                user = Users.objects.get(UserId=user_id)
                jira_app, _ = get_or_create_jira_application()
                connection = ExternalApplicationConnection.objects.filter(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                ).first()
                
                if connection:
                    projects_data = decrypt_projects_data(connection) or {}
                    project_details = projects_data.get('project_details', {})
                    
                    # Try to find stored project details (handle both string and int keys)
                    project_id_str = str(project_id)
                    if project_id_str in project_details:
                        stored_project_detail = project_details[project_id_str]
                    elif project_id in project_details:
                        stored_project_detail = project_details[project_id]
                    else:
                        # Try to find by iterating
                        for key, value in project_details.items():
                            if str(key) == project_id_str or str(key) == str(project_id):
                                stored_project_detail = value
                                break
                    
                    if stored_project_detail:
                        logger.info(f"📦 Found stored project details for project {project_id} to use as fallback")
            except Exception as stored_error:
                logger.warning(f"Could not retrieve stored project details: {str(stored_error)}")
            
            # Fetch project details from API
            logger.info(f"Fetching project details for project_id={project_id}, project_key={project_key}, cloud_id={cloud_id}")
            details_result = jira_integration.get_project_details(cloud_id, project_id=project_id, project_key=project_key)
            
            if details_result['success']:
                logger.info(f"Successfully fetched project details for project_id={project_id}")
                # Save project details to database
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app, _ = get_or_create_jira_application()
                    connection = ExternalApplicationConnection.objects.get(
                        application=jira_app,
                        user=user
                    )
                    
                    # Update projects_data with project details
                    # Decrypt existing projects_data first
                    projects_data = decrypt_projects_data(connection) or {}
                    project_details = projects_data.get('project_details', {})
                    # Normalize project_id to string for consistent key storage
                    project_id_key = str(project_id)
                    project_details[project_id_key] = {
                        'data': details_result['data'],
                        'fetched_at': datetime.now().isoformat()
                    }
                    projects_data['project_details'] = project_details
                    
                    connection.projects_data = projects_data
                    connection.last_used = datetime.now()
                    connection.save()
                    
                    return JsonResponse({
                        'success': True,
                        'data': details_result['data'],
                        'message': 'Project details fetched and saved successfully',
                        'from_cache': False
                    })
                    
                except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                    return JsonResponse({
                        'success': False,
                        'error': 'Database error'
                    })
            else:
                # API failed - use stored data if available
                api_error = details_result.get('error', 'Unknown error')
                logger.warning(f"⚠️ API call failed: {api_error}. Falling back to stored data...")
                
                if stored_project_detail:
                    logger.info(f"✅ Returning stored project details (API unavailable)")
                    stored_data = stored_project_detail.get('data') or stored_project_detail.get('full_details') or stored_project_detail
                    return JsonResponse({
                        'success': True,
                        'data': stored_data,
                        'message': 'Using stored project details (API unavailable)',
                        'from_cache': True,
                        'api_error': api_error,
                        'warning': f'API returned error: {api_error}. Showing cached data.'
                    })
                else:
                    # No stored data - return error
                    logger.error(f"❌ API failed and no stored project details available")
                    return JsonResponse({
                        'success': False,
                        'error': api_error,
                        'message': 'API call failed and no stored project details available'
                    }, status=401)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Jira project details endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["POST"])
def jira_project_issues(request):
    """Get issues/tasks for a specific Jira project
    
    First checks stored data in ExternalApplicationConnection.projects_data,
    then falls back to API call if not found or if refresh is needed.
    """
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id', 1)
        project_key = data.get('project_key')
        project_id = data.get('project_id')
        max_results = data.get('max_results', 50)
        force_refresh = data.get('force_refresh', False)  # Option to force API refresh
        
        if not project_key and not project_id:
            return JsonResponse({
                'success': False,
                'error': 'project_key or project_id is required'
            }, status=400)
        
        try:
            user = Users.objects.get(UserId=user_id)
            jira_app, _ = get_or_create_jira_application()
            connection = ExternalApplicationConnection.objects.get(
                application=jira_app,
                user=user,
                connection_status='active'
            )
            
            # First, try to get issues from stored projects_data
            # Data might be in current user's connection OR in assigned_by_user's connection
            stored_issues = []
            issues_data = {"issues": [], "total": 0}
            from_stored = False
            
            # Normalize project_id to string for consistent lookup
            project_id_str = str(project_id) if project_id else None
            
            # Try current user's connection first
            projects_data = decrypt_projects_data(connection) or {}
            project_details = projects_data.get('project_details', {})
            
            # Try to find stored project data (check both string and int keys)
            stored_project = None
            if project_id_str and project_id_str in project_details:
                stored_project = project_details[project_id_str]
            elif project_id and project_id in project_details:
                stored_project = project_details[project_id]
            elif project_details:
                # Try to find by matching project_id as string in any key
                for key, value in project_details.items():
                    if str(key) == project_id_str or str(key) == str(project_id):
                        stored_project = value
                        break
            
            if stored_project:
                full_details = stored_project.get('full_details', {})
                if full_details:
                    stored_issues_data = full_details.get('issues', {})
                    if stored_issues_data:
                        stored_issues = stored_issues_data.get('issues', [])
                        issues_data = {
                            'issues': stored_issues,
                            'total': stored_issues_data.get('total', len(stored_issues))
                        }
                        from_stored = True
                        logger.info(f"Found {len(stored_issues)} issues in stored data for project {project_id_str} (from current user's connection)")
            
            # If not found in current user's connection, search in assigned_by_user connections
            if not from_stored and project_id_str:
                logger.info(f"Project {project_id_str} not found in current user's connection, searching in assigned_by_user connections...")
                try:
                    # Find UsersProjectList entries for this project
                    from ...models import UsersProjectList
                    project_assignments = UsersProjectList.objects.filter(
                        project_id=project_id_str,
                        is_active=True
                    ).select_related('assigned_by').distinct()
                    
                    for assignment in project_assignments:
                        try:
                            assigned_by_user = assignment.assigned_by
                            assigned_by_connection = ExternalApplicationConnection.objects.filter(
                                application=jira_app,
                                user=assigned_by_user,
                                connection_status='active'
                            ).first()
                            
                            if assigned_by_connection:
                                assigned_projects_data = decrypt_projects_data(assigned_by_connection) or {}
                                assigned_project_details = assigned_projects_data.get('project_details', {})
                                
                                # Try to find project data
                                assigned_stored_project = None
                                if project_id_str in assigned_project_details:
                                    assigned_stored_project = assigned_project_details[project_id_str]
                                elif project_id and project_id in assigned_project_details:
                                    assigned_stored_project = assigned_project_details[project_id]
                                elif assigned_project_details:
                                    for key, value in assigned_project_details.items():
                                        if str(key) == project_id_str or str(key) == str(project_id):
                                            assigned_stored_project = value
                                            break
                                
                                if assigned_stored_project:
                                    full_details = assigned_stored_project.get('full_details', {})
                                    if full_details:
                                        stored_issues_data = full_details.get('issues', {})
                                        if stored_issues_data:
                                            stored_issues = stored_issues_data.get('issues', [])
                                            issues_data = {
                                                'issues': stored_issues,
                                                'total': stored_issues_data.get('total', len(stored_issues))
                                            }
                                            from_stored = True
                                            logger.info(f"Found {len(stored_issues)} issues in stored data for project {project_id_str} (from assigned_by_user {assigned_by_user.UserId}'s connection)")
                                            break
                        except Exception as e:
                            logger.warning(f"Error checking assigned_by_user connection: {str(e)}")
                            continue
                except Exception as e:
                    logger.warning(f"Error searching assigned_by_user connections: {str(e)}")
            
            # If no stored data or force_refresh, fetch from API
            if not from_stored or force_refresh:
                logger.info(f"{'Force refresh requested' if force_refresh else 'No stored data found'}, fetching from API...")
                
                # Get decrypted token
                access_token = get_decrypted_token(connection)
                if not access_token:
                    # If no token but we have stored data, return stored data
                    if from_stored:
                        logger.warning("No access token but returning stored issues")
                        stored_issues = issues_data.get('issues', [])
                    else:
                        logger.error("Failed to decrypt connection token and no stored data")
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to retrieve access token'
                        }, status=401)
                else:
                    # Get cloud_id from stored resources
                    cloud_id = None
                    if projects_data:
                        resources = projects_data.get('resources', [])
                        if resources and len(resources) > 0:
                            cloud_id = resources[0].get('id')
                    
                    if not cloud_id:
                        # If no cloud_id but we have stored data, return stored data
                        if from_stored:
                            logger.warning("No cloud_id but returning stored issues")
                            stored_issues = issues_data.get('issues', [])
                        else:
                            return JsonResponse({
                                'success': False,
                                'error': 'Cloud ID not found. Please reconnect to Jira.'
                            }, status=400)
                    else:
                        # Use JiraIntegration class method to fetch project details (which includes issues)
                        jira_integration = JiraIntegration(access_token)
                        
                        # Try to get issues using get_project_details first
                        details_result = jira_integration.get_project_details(
                            cloud_id=cloud_id,
                            project_key=project_key,
                            project_id=project_id
                        )
                        
                        issues = []
                        
                        if details_result['success'] and details_result['data'].get('issues'):
                            issues_data = details_result['data']['issues']
                            issues = issues_data.get('issues', [])
                            logger.info(f"Successfully fetched {len(issues)} issues via get_project_details")
                        
                        # If get_project_details didn't return issues, try direct search as fallback
                        if not issues:
                            logger.info("get_project_details didn't return issues, trying direct search...")
                            issues_result = jira_integration.get_project_issues(
                                cloud_id=cloud_id,
                                project_key=project_key,
                                project_id=project_id,
                                max_results=max_results
                            )
                            
                            if issues_result['success']:
                                issues_data = issues_result['data']
                                issues = issues_data.get('issues', [])
                                logger.info(f"Successfully fetched {len(issues)} issues via direct search")
                            else:
                                logger.warning(f"Direct search also failed: {issues_result.get('error', 'Unknown error')}")
                                # Fall back to stored data if API fails
                                if from_stored:
                                    logger.info("API failed, using stored issues")
                                    issues = stored_issues
                                else:
                                    issues = []
                                    issues_data = {"issues": [], "total": 0}
                        
                        # Use API-fetched issues
                        stored_issues = issues
            else:
                # Use stored issues
                stored_issues = issues_data.get('issues', [])
            
            issues = stored_issues
            
            # Debug: Log first issue structure to understand the format
            if issues and len(issues) > 0:
                logger.info(f"DEBUG: First issue structure (full): {json.dumps(issues[0], indent=2, default=str)}")
            
            # Format issues for frontend - handle both raw Jira API format and already formatted
            formatted_issues = []
            for issue in issues:
                # Handle case where issue might already be formatted or is raw from API
                if isinstance(issue, dict):
                    # Check if it's already formatted (has 'summary' at top level)
                    if 'summary' in issue and 'fields' not in issue:
                        # Already formatted, use as-is but ensure all fields are present
                        formatted_issue = {
                            'id': issue.get('id'),
                            'key': issue.get('key'),
                            'summary': issue.get('summary', 'Untitled'),
                            'description': issue.get('description', ''),
                            'status': issue.get('status', 'Unknown'),
                            'status_id': issue.get('status_id'),
                            'assignee': issue.get('assignee'),
                            'priority': issue.get('priority', {'name': 'Medium'}),
                            'issue_type': issue.get('issue_type', {'name': 'Task'}),
                            'updated': issue.get('updated'),
                            'created': issue.get('created'),
                            'project_key': project_key or project_id
                        }
                    else:
                        # Raw Jira API format - extract from fields
                        fields = issue.get('fields', {})
                        if not fields:
                            # If fields are missing, try to fetch the full issue details
                            issue_id = issue.get('id')
                            issue_key = issue.get('key')
                            if issue_id or issue_key:
                                logger.info(f"Fetching full details for issue {issue_id or issue_key} (fields missing)")
                                try:
                                    issue_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{issue_key or issue_id}"
                                    issue_headers = {
                                        "Authorization": f"Bearer {access_token}",
                                        "Accept": "application/json"
                                    }
                                    issue_response = requests.get(issue_url, headers=issue_headers, timeout=30)
                                    if issue_response.status_code == 200:
                                        full_issue = issue_response.json()
                                        issue = full_issue  # Replace with full issue data
                                        fields = issue.get('fields', {})
                                        logger.info(f"Successfully fetched full details for issue {issue_key or issue_id}")
                                    else:
                                        logger.warning(f"Failed to fetch full issue details: {issue_response.status_code}")
                                except Exception as e:
                                    logger.warning(f"Exception fetching full issue details: {str(e)}")
                            
                            if not fields:
                                logger.warning(f"Issue {issue.get('id', 'unknown')} has no fields after fetch attempt, skipping")
                                continue
                        
                        status = fields.get('status', {}) or {}
                        assignee = fields.get('assignee') or {}
                        priority = fields.get('priority') or {}
                        issue_type = fields.get('issuetype') or {}
                        
                        # Extract status name - handle both dict and string
                        status_name = 'Unknown'
                        if isinstance(status, dict):
                            status_name = status.get('name', 'Unknown')
                        elif isinstance(status, str):
                            status_name = status
                        
                        # Extract priority name
                        priority_name = 'Medium'
                        if isinstance(priority, dict):
                            priority_name = priority.get('name', 'Medium')
                        elif isinstance(priority, str):
                            priority_name = priority
                        
                        # Extract issue type name
                        issue_type_name = 'Task'
                        if isinstance(issue_type, dict):
                            issue_type_name = issue_type.get('name', 'Task')
                        elif isinstance(issue_type, str):
                            issue_type_name = issue_type
                        
                        formatted_issue = {
                            'id': issue.get('id'),
                            'key': issue.get('key'),
                            'summary': fields.get('summary') or 'Untitled',
                            'description': fields.get('description') or '',
                            'status': status_name,
                            'status_id': status.get('id') if isinstance(status, dict) else None,
                            'assignee': {
                                'displayName': assignee.get('displayName') if assignee and isinstance(assignee, dict) else None,
                                'emailAddress': assignee.get('emailAddress') if assignee and isinstance(assignee, dict) else None,
                                'accountId': assignee.get('accountId') if assignee and isinstance(assignee, dict) else None
                            } if assignee else None,
                            'priority': {
                                'name': priority_name,
                                'id': priority.get('id') if isinstance(priority, dict) else None
                            },
                            'issue_type': {
                                'name': issue_type_name,
                                'id': issue_type.get('id') if isinstance(issue_type, dict) else None
                            },
                            'updated': fields.get('updated'),
                            'created': fields.get('created'),
                            'project_key': project_key or project_id
                        }
                    
                    formatted_issues.append(formatted_issue)
                else:
                    logger.warning(f"Unexpected issue format: {type(issue)}")
            
            logger.info(f"Successfully fetched {len(formatted_issues)} issues for project {project_key or project_id}")
            
            return JsonResponse({
                'success': True,
                'issues': formatted_issues,
                'total': issues_data.get('total', len(formatted_issues)),
                'max_results': max_results
            })
                
        except Users.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'User {user_id} not found'
            }, status=404)
        except ExternalApplicationConnection.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Jira connection not found. Please reconnect to Jira.'
            }, status=401)
        except Exception as e:
            logger.error(f"Error fetching Jira issues: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Jira project issues endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def jira_resources(request):
    """Get Jira accessible resources"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        try:
            user = Users.objects.get(UserId=user_id)
            logger.info(f"🔍 DEBUG: Found user {user_id}")
            jira_app, created = get_or_create_jira_application()
            if created:
                logger.info(f"🔍 DEBUG: Created new Jira app: {jira_app.id}")
            else:
                logger.info(f"🔍 DEBUG: Found existing Jira app: {jira_app.id}")
            
            # Debug: Check all connections for this user/app
            all_conns = ExternalApplicationConnection.objects.filter(
                application=jira_app,
                user=user
            )
            logger.info(f"🔍 DEBUG: Total connections for user {user_id} and Jira app: {all_conns.count()}")
            for conn in all_conns:
                logger.info(f"🔍 DEBUG: Connection {conn.id}: status={conn.connection_status}, created={conn.created_at}, has_token={bool(conn.connection_token)}")
            
            connection = ExternalApplicationConnection.objects.get(
                application=jira_app,
                user=user,
                connection_status='active'
            )
            
            logger.info(f"✅ Jira resources request for user {user_id}, connection {connection.id}")
            
            # Decrypt projects_data if needed
            projects_data = decrypt_projects_data(connection)
            logger.info(f"📊 Connection projects_data (decrypted): {projects_data}")
            
            if projects_data and 'resources' in projects_data:
                resources = projects_data['resources']
                logger.info(f"📊 Found {len(resources)} resources in database")
                try:
                    resource_list = []
                    for r in resources:
                        if isinstance(r, dict):
                            resource_list.append(r.get('name', r.get('id', str(r))))
                        else:
                            resource_list.append(str(r))
                    logger.info(f"📊 DEBUG: Available resources/projects: {resource_list}")
                except Exception as e:
                    logger.info(f"📊 DEBUG: Available resources/projects (error formatting): {resources}")
                
                return JsonResponse({
                    'success': True,
                    'resources': resources,
                    'count': len(resources)
                })
            else:
                # If no resources in database, try to fetch them fresh
                logger.info("No resources in database, attempting to fetch fresh resources")
                
                # Get decrypted token
                decrypted_token = get_decrypted_token(connection)
                if not decrypted_token:
                    logger.error(f"No connection token available for connection {connection.id}")
                    return JsonResponse({
                        'success': False,
                        'error': 'No connection token available. Please reconnect to Jira.'
                    })
                
                # Log token info for debugging (first 20 chars only for security)
                logger.info(f"Using decrypted token (first 20 chars): {decrypted_token[:20] if len(decrypted_token) > 20 else decrypted_token}...")
                
                jira_integration = JiraIntegration(decrypted_token)
                resources_result = jira_integration.get_accessible_resources()
                
                if resources_result['success']:
                    resources_data = resources_result['data']
                    logger.info(f"Successfully fetched {len(resources_data)} fresh resources")
                    
                    # Update the connection with fresh resources
                    # Use decrypted projects_data or create new dict
                    projects_data = decrypt_projects_data(connection) or {}
                    projects_data['resources'] = resources_data
                    projects_data['last_sync'] = datetime.now().isoformat()
                    connection.projects_data = projects_data
                    connection.save()
                    
                    return JsonResponse({
                        'success': True,
                        'resources': resources_data,
                        'count': len(resources_data)
                    })
                else:
                    error_msg = resources_result.get('error', 'Unknown error')
                    logger.error(f"Failed to fetch fresh resources: {error_msg}")
                    
                    # Check if it's a 401 error - token might be expired
                    if '401' in str(error_msg) or 'Unauthorized' in str(error_msg):
                        logger.warning("Token appears to be expired or invalid. User may need to reconnect.")
                        return JsonResponse({
                            'success': False,
                            'error': 'Authentication failed. Please reconnect to Jira.',
                            'error_code': 'TOKEN_EXPIRED',
                            'requires_reconnect': True
                        })
                    
                    return JsonResponse({
                        'success': False,
                        'error': f'Failed to fetch resources: {error_msg}'
                    })
                
        except Users.DoesNotExist:
            logger.error(f"❌ User {user_id} not found")
            return JsonResponse({
                'success': False,
                'error': f'User {user_id} not found'
            })
        except ExternalApplication.DoesNotExist:
            # This should never happen since we use get_or_create, but keep for safety
            logger.error(f"❌ Jira application not found in database")
            return JsonResponse({
                'success': False,
                'error': 'Jira application not found'
            })
        except ExternalApplicationConnection.DoesNotExist:
            logger.error(f"❌ Jira connection not found for user {user_id}")
            # Debug: Check what connections exist
            try:
                user = Users.objects.get(UserId=user_id)
                jira_app, _ = get_or_create_jira_application()
                all_conns = ExternalApplicationConnection.objects.filter(
                    application=jira_app,
                    user=user
                )
                logger.error(f"🔍 DEBUG: Found {all_conns.count()} total connections (any status) for user {user_id}")
                for conn in all_conns:
                    logger.error(f"🔍 DEBUG: Connection {conn.id}: status={conn.connection_status}, created={conn.created_at}, updated={conn.updated_at}")
            except Exception as debug_e:
                logger.error(f"❌ Debug query failed: {str(debug_e)}")
            
            return JsonResponse({
                'success': False,
                'error': 'Jira connection not found'
            })
    
    except Exception as e:
        logger.error(f"Jira resources endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["GET"])
def jira_users(request):
    """Get all users for JIRA project assignment"""
    try:
        # Import the JiraBackendManager
        from .jira_backend import JiraBackendManager
        jira_backend = JiraBackendManager()
        
        result = jira_backend.get_all_users()
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error getting JIRA users: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def jira_assign_project(request):
    """Assign a JIRA project to selected users"""
    try:
        # Import the JiraBackendManager
        from .jira_backend import JiraBackendManager
        jira_backend = JiraBackendManager()
        
        data = json.loads(request.body)
        assigned_by_user_id = data.get('assigned_by_user_id')
        project_data = data.get('project_data')
        selected_users = data.get('selected_users')
        
        result = jira_backend.assign_project_to_users(
            assigned_by_user_id, project_data, selected_users
        )
        
        if result['success']:
            return JsonResponse(result)
        else:
            return JsonResponse({'error': result['error']}, status=400)
            
    except Exception as e:
        logger.error(f"Error assigning JIRA project: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def jira_stored_data(request):
    """Get stored Jira data"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        try:
            user = Users.objects.get(UserId=user_id)
            jira_app, _ = get_or_create_jira_application()
            
            connection = ExternalApplicationConnection.objects.get(
                application=jira_app,
                user=user,
                connection_status='active'
            )
            
            # Decrypt projects_data if needed
            projects_data = decrypt_projects_data(connection)
            
            if projects_data:
                projects = projects_data.get('projects', [])
                project_details = projects_data.get('project_details', {})
                
                # Calculate detailed statistics
                project_stats = []
                total_issues = 0
                for proj_id, proj_data in project_details.items():
                    full_details = proj_data.get('full_details', {})
                    issues_data = full_details.get('issues', {})
                    issues_list = issues_data.get('issues', []) if isinstance(issues_data, dict) else []
                    issues_count = len(issues_list)
                    total_issues += issues_count
                    
                    project_stats.append({
                        'project_id': proj_id,
                        'project_name': proj_data.get('project', {}).get('name', 'Unknown'),
                        'project_key': proj_data.get('project', {}).get('key', 'Unknown'),
                        'issues_count': issues_count,
                        'has_full_details': bool(full_details),
                        'fetched_at': proj_data.get('fetched_at'),
                        'fetch_success': proj_data.get('fetch_success', False)
                    })
                
                logger.info(f"📊 Stored data verification for user {user_id}: {len(project_details)} projects, {total_issues} total issues")
                
                return JsonResponse({
                    'success': True,
                    'has_data': True,
                    'connection_id': connection.id,
                    'data': {  # Wrap in 'data' key for frontend
                        'projects': projects,
                        'resources': projects_data.get('resources', []),
                        'project_details': project_details,
                        'projects_count': len(projects),
                        'project_details_count': len(project_details),
                        'total_issues_stored': total_issues,
                        'project_stats': project_stats
                    },
                    'projects_data': projects_data,  # Keep full data for compatibility
                    'resources': projects_data.get('resources', []),
                    'projects': projects,
                    'project_details': project_details,
                    'project_stats': project_stats,
                    'total_issues_stored': total_issues,
                    'last_updated': connection.updated_at.isoformat(),
                    'sync_status': projects_data.get('sync_status', 'unknown')
                })
            else:
                return JsonResponse({
                    'success': True,
                    'has_data': False,
                    'message': 'No stored data found'
                })
                
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
            return JsonResponse({
                'success': True,
                'has_data': False,
                'message': 'No Jira connection found'
            })
    
    except Exception as e:
        logger.error(f"Jira stored data endpoint error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })
