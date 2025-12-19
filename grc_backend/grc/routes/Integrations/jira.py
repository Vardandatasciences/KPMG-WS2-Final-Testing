import os
import json
import requests
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
import logging
import urllib.parse as up

from grc.models import Users, ExternalApplication, ExternalApplicationConnection, ExternalApplicationSyncLog

logger = logging.getLogger(__name__)

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
            # IMPORTANT: Use POST method with JSON body (GET with query params returns 410 error)
            issues_data = {"issues": [], "total": 0}
            try:
                # Use standard /rest/api/3/search endpoint with POST method
                # The 410 error occurs when using GET - POST with JSON body is required
                search_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/search"
                
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
                        search_payload = {
                            'jql': jql_query,
                            'maxResults': 50
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
                    jira_app, created = ExternalApplication.objects.get_or_create(
                        name='Jira',
                        defaults={
                            'category': 'Project Management',
                            'type': 'Issue Tracking',
                            'description': 'Jira integration for project and issue management',
                            'icon_class': 'fas fa-tasks',
                            'status': 'connected'
                        }
                    )
                    
                    # Update the application status to connected if it was created or already exists
                    if not created:
                        jira_app.status = 'connected'
                        jira_app.save()
                        logger.info("Updated existing Jira application status to 'connected'")
                    else:
                        logger.info("Created new Jira application with 'connected' status")
                    
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
                    
                    logger.info(f"Successfully saved Jira connection with {len(resources_data)} resources")
                    
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
                    jira_app, created = ExternalApplication.objects.get_or_create(
                        name='Jira',
                        defaults={
                            'category': 'Project Management',
                            'type': 'Issue Tracking',
                            'description': 'Jira integration for project and issue management',
                            'icon_class': 'fas fa-tasks',
                            'status': 'connected'
                        }
                    )
                    
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
                jira_app = ExternalApplication.objects.get(name='Jira')
                connection = ExternalApplicationConnection.objects.get(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                )
                
                if connection.projects_data:
                    return JsonResponse({
                        'success': True,
                        'data': connection.projects_data.get('projects', []),
                        'resources': connection.projects_data.get('resources', []),
                        'last_updated': connection.updated_at.isoformat(),
                        'sync_status': connection.projects_data.get('sync_status', 'unknown')
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
                    jira_app = ExternalApplication.objects.get(name='Jira')
                    connection = ExternalApplicationConnection.objects.get(
                        application=jira_app,
                        user=user,
                        connection_status='active'
                    )
                    access_token = connection.connection_token
                    logger.info("Using stored connection token for fetching projects")
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
                # Fetch projects data
                projects_result = jira_integration.get_projects(cloud_id)
                
                if projects_result['success']:
                    return JsonResponse({
                        'success': True,
                        'data': projects_result['data'],
                        'message': 'Projects data fetched successfully'
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': projects_result['error']
                    })
            
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
                jira_app = ExternalApplication.objects.get(name='Jira')
                connection = ExternalApplicationConnection.objects.get(
                    application=jira_app,
                    user=user,
                    connection_status='active'
                )
                
                # Check if project details are stored
                project_details = connection.projects_data.get('project_details', {})
                
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
                    jira_app = ExternalApplication.objects.get(name='Jira')
                    connection = ExternalApplicationConnection.objects.get(
                        application=jira_app,
                        user=user,
                        connection_status='active'
                    )
                    access_token = connection.connection_token
                    logger.info("Using stored connection token")
                    
                    # If cloud_id not provided, try to get it from stored resources
                    if not cloud_id and connection.projects_data:
                        resources = connection.projects_data.get('resources', [])
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
            
            # Fetch project details
            logger.info(f"Fetching project details for project_id={project_id}, project_key={project_key}, cloud_id={cloud_id}")
            details_result = jira_integration.get_project_details(cloud_id, project_id=project_id, project_key=project_key)
            
            if details_result['success']:
                logger.info(f"Successfully fetched project details for project_id={project_id}")
                # Save project details to database
                try:
                    user = Users.objects.get(UserId=user_id)
                    jira_app = ExternalApplication.objects.get(name='Jira')
                    connection = ExternalApplicationConnection.objects.get(
                        application=jira_app,
                        user=user
                    )
                    
                    # Update projects_data with project details
                    projects_data = connection.projects_data or {}
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
                        'message': 'Project details fetched and saved successfully'
                    })
                    
                except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
                    return JsonResponse({
                        'success': False,
                        'error': 'Database error'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': details_result['error']
                })
    
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
@require_http_methods(["GET"])
def jira_resources(request):
    """Get Jira accessible resources"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        try:
            user = Users.objects.get(UserId=user_id)
            jira_app = ExternalApplication.objects.get(name='Jira')
            connection = ExternalApplicationConnection.objects.get(
                application=jira_app,
                user=user,
                connection_status='active'
            )
            
            logger.info(f"Jira resources request for user {user_id}, connection {connection.id}")
            logger.info(f"Connection projects_data: {connection.projects_data}")
            
            if connection.projects_data and 'resources' in connection.projects_data:
                resources = connection.projects_data['resources']
                logger.info(f"Found {len(resources)} resources in database")
                
                return JsonResponse({
                    'success': True,
                    'resources': resources,
                    'count': len(resources)
                })
            else:
                # If no resources in database, try to fetch them fresh
                logger.info("No resources in database, attempting to fetch fresh resources")
                
                if connection.connection_token:
                    jira_integration = JiraIntegration(connection.connection_token)
                    resources_result = jira_integration.get_accessible_resources()
                    
                    if resources_result['success']:
                        resources_data = resources_result['data']
                        logger.info(f"Successfully fetched {len(resources_data)} fresh resources")
                        
                        # Update the connection with fresh resources
                        projects_data = connection.projects_data or {}
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
                        logger.error(f"Failed to fetch fresh resources: {resources_result['error']}")
                        return JsonResponse({
                            'success': False,
                            'error': f'Failed to fetch resources: {resources_result["error"]}'
                        })
                else:
                    logger.error("No connection token available")
                    return JsonResponse({
                        'success': False,
                        'error': 'No connection token available'
                    })
                
        except (Users.DoesNotExist, ExternalApplication.DoesNotExist, ExternalApplicationConnection.DoesNotExist):
            logger.error(f"Jira connection not found for user {user_id}")
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
            jira_app = ExternalApplication.objects.get(name='Jira')
            connection = ExternalApplicationConnection.objects.get(
                application=jira_app,
                user=user,
                connection_status='active'
            )
            
            if connection.projects_data:
                projects = connection.projects_data.get('projects', [])
                return JsonResponse({
                    'success': True,
                    'has_data': True,
                    'data': {  # Wrap in 'data' key for frontend
                        'projects': projects,
                        'resources': connection.projects_data.get('resources', []),
                        'project_details': connection.projects_data.get('project_details', {}),
                        'projects_count': len(projects)
                    },
                    'projects_data': connection.projects_data,  # Keep full data for compatibility
                    'resources': connection.projects_data.get('resources', []),
                    'projects': projects,
                    'project_details': connection.projects_data.get('project_details', {}),
                    'last_updated': connection.updated_at.isoformat(),
                    'sync_status': connection.projects_data.get('sync_status', 'unknown')
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
