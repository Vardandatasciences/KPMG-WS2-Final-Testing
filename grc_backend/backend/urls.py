from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.generic import TemplateView

# Import RFP views for direct URL patterns
import tprm_backend.rfp.views as rfp_views
import tprm_backend.rfp.views_rfp_responses as rfp_response_views

# GRC Integration imports
from grc.routes.Integrations.Bamboohr.bamboohr import (
    bamboohr_oauth, bamboohr_oauth_callback, bamboohr_stored_data,
    bamboohr_employees, bamboohr_departments, bamboohr_sync_data, bamboohr_reports, bamboohr_debug
)

# Jira Integration imports
from grc.routes.Integrations.jira import (
    jira_oauth, jira_oauth_callback, jira_projects, jira_project_details,
    jira_resources, jira_stored_data, jira_users, jira_assign_project
)

# Streamline Integration imports
from grc.routes.Integrations.streamLine import (
    get_user_projects, get_project_details, get_user_statistics,
    save_task_action, get_user_task_actions
)

# External Applications imports
from grc.routes.Integrations.event_integration import (
    get_external_applications, refresh_application_status, get_application_details,
    disconnect_external_application, connect_external_application
)

# Integration Database Update imports
from grc.routes.Integrations.update_integrations_db import (
    disconnect_integration, connect_integration, get_integration_status, bulk_update_integration_status
)

# Gmail Integration imports
from grc.routes.Integrations.Gmail.gmail_integration import (
    gmail_oauth_initiate, gmail_oauth_callback, get_gmail_connection_status,
    get_gmail_messages, get_calendar_events, download_attachment,
    get_stored_gmail_data, get_stored_gmail_data_formatted, save_gmail_data_to_db, disconnect_gmail,
    test_gmail_headers, save_gmail_message_to_integration_list, save_calendar_event_to_integration_list
)
from grc.routes.Integrations.Sentinel.sentinel import (
    sentinel_oauth_start, sentinel_oauth_callback, sentinel_disconnect,
    sentinel_check_status, get_sentinel_alerts, get_sentinel_stats, get_sentinel_incident
)
 
@cache_control(max_age=86400)  # Cache for 24 hours
def favicon_view(request):
    """
    Handle favicon.ico requests to prevent 404 errors
    """
    # Return a simple 1x1 transparent PNG favicon
    favicon_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    response = HttpResponse(favicon_data, content_type='image/png')
    return response
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('favicon.ico', favicon_view, name='favicon'),  # Handle favicon requests
    path('api/', include('grc.urls')),  # Use the correct app name for API routes
    path('api/', include('backend.api.urls')),  # Include API module URLs
    
    # BambooHR Integration URLs (directly included)
    path('api/bamboohr/oauth/', bamboohr_oauth, name='bamboohr-oauth'),
    path('api/bamboohr/oauth-callback/', bamboohr_oauth_callback, name='bamboohr-oauth-callback'),
    path('api/bamboohr/stored-data/', bamboohr_stored_data, name='bamboohr-stored-data'),
    path('api/bamboohr/employees/', bamboohr_employees, name='bamboohr-employees'),
    path('api/bamboohr/departments/', bamboohr_departments, name='bamboohr-departments'),
    path('api/bamboohr/sync-data/', bamboohr_sync_data, name='bamboohr-sync-data'),
    path('api/bamboohr/reports/', bamboohr_reports, name='bamboohr-reports'),
    path('api/bamboohr/debug/', bamboohr_debug, name='bamboohr-debug'),
    
    # Jira Integration URLs (directly included)
    path('api/jira/oauth/', jira_oauth, name='jira-oauth'),
    path('api/jira/oauth-callback/', jira_oauth_callback, name='jira-oauth-callback'),
    path('api/jira/projects/', jira_projects, name='jira-projects'),
    path('api/jira/project-details/', jira_project_details, name='jira-project-details'),
    path('api/jira/resources/', jira_resources, name='jira-resources'),
    path('api/jira/stored-data/', jira_stored_data, name='jira-stored-data'),
    path('api/jira/users/', jira_users, name='jira-users'),
    path('api/jira/assign-project/', jira_assign_project, name='jira-assign-project'),

    # Streamline Integration URLs
    path('api/streamline/user-projects/', get_user_projects, name='streamline-user-projects'),
    path('api/streamline/project-details/', get_project_details, name='streamline-project-details'),
    path('api/streamline/user-statistics/', get_user_statistics, name='streamline-user-statistics'),
    path('api/streamline/save-task-action/', save_task_action, name='streamline-save-task-action'),
    path('api/streamline/user-task-actions/', get_user_task_actions, name='streamline-user-task-actions'),
    
    # External Applications endpoints
    path('api/external-applications/', get_external_applications, name='get-external-applications'),
    path('api/external-applications/refresh/', refresh_application_status, name='refresh-application-status'),
    path('api/external-applications/<int:application_id>/', get_application_details, name='get-application-details'),
    # Microsoft Sentinel OAuth URLs (root level for OAuth callbacks)
    # Using re_path with optional trailing slash to handle both with/without slash
    re_path(r'^auth/sentinel/?$', sentinel_oauth_start, name='sentinel-oauth-start'),
    re_path(r'^auth/sentinel/callback/?$', sentinel_oauth_callback, name='sentinel-oauth-callback'),
    re_path(r'^auth/sentinel/disconnect/?$', sentinel_disconnect, name='sentinel-disconnect'),
    # Gmail Integration URLs
    path('api/gmail/oauth-initiate/', gmail_oauth_initiate, name='gmail-oauth-initiate'),
    path('api/gmail/oauth-callback/', gmail_oauth_callback, name='gmail-oauth-callback'),
    path('api/gmail/connection-status/', get_gmail_connection_status, name='gmail-connection-status'),
    path('api/gmail/messages/', get_gmail_messages, name='gmail-messages'),
    path('api/gmail/calendar-events/', get_calendar_events, name='gmail-calendar-events'),
    path('api/gmail/download-attachment/', download_attachment, name='gmail-download-attachment'),
    path('api/gmail/stored-data/', get_stored_gmail_data, name='gmail-stored-data'),
    path('api/gmail/stored-data-formatted/', get_stored_gmail_data_formatted, name='gmail-stored-data-formatted'),
    path('api/gmail/save-to-db/', save_gmail_data_to_db, name='gmail-save-to-db'),
    path('api/gmail/disconnect/', disconnect_gmail, name='gmail-disconnect'),
    path('api/gmail/test-headers/', test_gmail_headers, name='gmail-test-headers'),
    path('api/gmail/save-message-to-integration/', save_gmail_message_to_integration_list, name='gmail-save-message-to-integration'),
    path('api/gmail/save-event-to-integration/', save_calendar_event_to_integration_list, name='gmail-save-event-to-integration'),
    path('api/external-applications/connect/', connect_external_application, name='connect-external-application'),

    path('api/external-applications/disconnect/', disconnect_external_application, name='disconnect-external-application'),
    
    # Integration Database Update endpoints
    path('api/integrations/disconnect/', disconnect_integration, name='disconnect-integration'),
    path('api/integrations/connect/', connect_integration, name='connect-integration'),
    path('api/integrations/status/', get_integration_status, name='get-integration-status'),
    path('api/integrations/bulk-update/', bulk_update_integration_status, name='bulk-update-integration-status'),
    
    path('oauth/callback/', bamboohr_oauth_callback, name='oauth-callback'),  # OAuth callback at root level
    
    # =========================================================================
    # TPRM INTEGRATION - Third Party Risk Management API Routes
    # =========================================================================
    # All TPRM routes are prefixed with /api/tprm/
    
    # TPRM Authentication (MFA)
    path('api/tprm/auth/', include('tprm_backend.mfa_auth.urls')),
    
    # TPRM RBAC
    path('api/tprm/rbac/', include('tprm_backend.rbac.tprm_urls')),
    
    # TPRM Admin Access Control
    path('api/tprm/admin-access/', include('tprm_backend.admin_access.urls')),
    
    # TPRM Global Search
    path('api/tprm/global-search/', include('tprm_backend.global_search.urls')),
    
    # TPRM Core APIs
    path('api/tprm/core/', include('tprm_backend.core.urls')),
    
    # TPRM OCR APIs
    path('api/tprm/ocr/', include('tprm_backend.ocr_app.urls')),
    
    # TPRM SLA Management APIs
    path('api/tprm/slas/', include('tprm_backend.slas.urls')),
    path('api/tprm/v1/sla-dashboard/', include('tprm_backend.slas.urls')),  # Frontend v1 compatibility URL
    
    # TPRM Audit Management APIs
    path('api/tprm/audits/', include('tprm_backend.audits.urls')),
    
    # TPRM Notifications APIs
    path('api/tprm/notifications/', include('tprm_backend.notifications.urls')),
    
    # TPRM Quick Access APIs
    path('api/tprm/quick-access/', include('tprm_backend.quick_access.urls')),
    
    # TPRM Compliance APIs
    path('api/tprm/compliance/', include('tprm_backend.compliance.urls')),
    
    # TPRM BCP/DRP Management APIs
    path('api/tprm/bcpdrp/', include('tprm_backend.bcpdrp.urls')),
    
    # TPRM Risk Analysis APIs
    path('api/tprm/risk-analysis/', include('tprm_backend.risk_analysis.urls')),
    
    # TPRM Contract Management APIs
    path('api/tprm/contracts/', include('tprm_backend.contracts.urls')),
    
    # TPRM Contract Audit APIs
    path('api/tprm/audits-contract/', include('tprm_backend.audits_contract.urls')),
    path('api/tprm/contract-risk-analysis/', include('tprm_backend.contract_risk_analysis.urls')),
    
    # TPRM RFP Management APIs
    path('api/tprm/rfp/', include('tprm_backend.rfp.urls')),
    path('api/tprm/v1/', include('tprm_backend.rfp.urls')),  # Frontend compatibility for /api/tprm/v1/
    path('api/tprm/rfp-approval/', include('tprm_backend.rfp_approval.urls')),
    path('api/tprm/rfp-risk-analysis/', include('tprm_backend.rfp_risk_analysis.urls')),
    
    # RFP Approval URLs - Additional paths for compatibility
    path('api/approval/', include('tprm_backend.rfp_approval.urls')),
    path('api/rfp-approval/', include('tprm_backend.rfp_approval.urls')),
    
    # TPRM Vendor Management APIs
    path('api/tprm/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),
    path('api/tprm/vendor-auth/', include('tprm_backend.apps.vendor_auth.urls')),
    path('api/tprm/vendor-risk/', include('tprm_backend.apps.vendor_risk.urls')),
    path('api/tprm/vendor-questionnaire/', include('tprm_backend.apps.vendor_questionnaire.urls')),
    path('api/tprm/vendor-dashboard/', include('tprm_backend.apps.vendor_dashboard.urls')),
    path('api/tprm/vendor-lifecycle/', include('tprm_backend.apps.vendor_lifecycle.urls')),
    path('api/tprm/vendor-approval/', include('tprm_backend.apps.vendor_approval.urls')),
    path('api/tprm/risk-analysis-vendor/', include('tprm_backend.risk_analysis_vendor.urls')),
    
    # TPRM v1 API routes (for frontend compatibility - /api/tprm/v1/*)
    # Core TPRM modules
    path('api/tprm/v1/core/', include('tprm_backend.core.urls')),
    path('api/tprm/v1/slas/', include('tprm_backend.slas.urls')),
    path('api/tprm/v1/audits/', include('tprm_backend.audits.urls')),
    path('api/tprm/v1/notifications/', include('tprm_backend.notifications.urls')),
    path('api/tprm/v1/quick-access/', include('tprm_backend.quick_access.urls')),
    path('api/tprm/v1/compliance/', include('tprm_backend.compliance.urls')),
    path('api/tprm/v1/bcpdrp/', include('tprm_backend.bcpdrp.urls')),
    path('api/tprm/v1/risk-analysis/', include('tprm_backend.risk_analysis.urls')),
    path('api/tprm/v1/contracts/', include('tprm_backend.contracts.urls')),
    path('api/tprm/v1/audits-contract/', include('tprm_backend.audits_contract.urls')),
    path('api/tprm/v1/contract-risk-analysis/', include('tprm_backend.contract_risk_analysis.urls')),
    path('api/tprm/v1/rfp/', include('tprm_backend.rfp.urls')),
    path('api/tprm/v1/rfp-approval/', include('tprm_backend.rfp_approval.urls')),
    path('api/tprm/v1/rfp-risk-analysis/', include('tprm_backend.rfp_risk_analysis.urls')),
    path('api/tprm/v1/global-search/', include('tprm_backend.global_search.urls')),
    path('api/tprm/v1/ocr/', include('tprm_backend.ocr_app.urls')),
    path('api/tprm/v1/rbac/', include('tprm_backend.rbac.tprm_urls')),
    path('api/tprm/v1/admin-access/', include('tprm_backend.admin_access.urls')),
    path('api/tprm/v1/auth/', include('tprm_backend.mfa_auth.urls')),
    
    # Vendor modules
    path('api/tprm/v1/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),
    path('api/tprm/v1/vendor-auth/', include('tprm_backend.apps.vendor_auth.urls')),
    path('api/tprm/v1/vendor-risk/', include('tprm_backend.apps.vendor_risk.urls')),
    path('api/tprm/v1/vendor-questionnaire/', include('tprm_backend.apps.vendor_questionnaire.urls')),
    path('api/tprm/v1/vendor-dashboard/', include('tprm_backend.apps.vendor_dashboard.urls')),
    path('api/tprm/v1/vendor-lifecycle/', include('tprm_backend.apps.vendor_lifecycle.urls')),
    path('api/tprm/v1/vendor-approval/', include('tprm_backend.apps.vendor_approval.urls')),
    path('api/tprm/v1/risk-analysis-vendor/', include('tprm_backend.risk_analysis_vendor.urls')),
    
    # Frontend v1 compatibility routes
    path('api/v1/', include('tprm_backend.rfp.urls')),  # Frontend compatibility for /api/v1/ (includes KPI endpoints)
    path('api/v1/rfps/', include('tprm_backend.rfp.urls')),  # Frontend compatibility for /api/v1/rfps/
    path('api/v1/vendor-approval/', include('tprm_backend.apps.vendor_approval.urls')),  # Frontend compatibility for /api/v1/vendor-approval/
    path('api/v1/vendor-core/', include('tprm_backend.apps.vendor_core.urls')),  # Frontend compatibility for /api/v1/vendor-core/
    path('api/v1/vendor-questionnaire/', include('tprm_backend.apps.vendor_questionnaire.urls')),  # Frontend compatibility for /api/v1/vendor-questionnaire/
    path('api/v1/vendor-lifecycle/', include('tprm_backend.apps.vendor_lifecycle.urls')),  # Frontend compatibility for /api/v1/vendor-lifecycle/
    # RFP responses endpoints for /api/v1/ compatibility
    path('api/v1/rfp-responses-detail/<int:response_id>/', rfp_response_views.get_rfp_response_by_id, name='get_rfp_response_by_id_v1'),
    path('api/v1/rfp-responses-list/', rfp_response_views.get_rfp_responses, name='get_rfp_responses_v1'),
    # Vendor invitations endpoints - direct paths without double prefix for /api/v1/vendor-invitations/
    path('api/v1/vendor-invitations/stats/<int:rfp_id>/', rfp_views.get_invitation_stats, name='get_invitation_stats_v1'),
    path('api/v1/vendor-invitations/rfp/<int:rfp_id>/', rfp_views.get_invitations_by_rfp, name='get_invitations_by_rfp_v1'),
    path('api/v1/vendor-invitations/create/<int:rfp_id>/', rfp_views.create_vendor_invitations, name='create_vendor_invitations_v1'),
    path('api/v1/vendor-invitations/send/<int:rfp_id>/', rfp_views.send_vendor_invitations, name='send_vendor_invitations_v1'),
    path('api/v1/vendor-invitations/primary-contacts/', rfp_views.get_primary_contacts, name='get_primary_contacts_v1'),
    path('api/v1/vendor-dashboard/', include('tprm_backend.apps.vendor_dashboard.urls')),  # Frontend compatibility for /api/v1/vendor-dashboard/
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# =============================================================================
# SPA ROUTING SUPPORT - Vue.js Frontend Catch-All
# =============================================================================
# This MUST be at the end to catch all non-API routes and serve index.html
# This allows Vue Router to handle client-side routing
# Important: All API routes should be prefixed with /api/ to avoid conflicts
urlpatterns += [
    # Catch-all pattern for Vue.js SPA routing
    # Matches any URL that doesn't start with 'api/' or 'admin/'
    # This allows direct URL access (e.g., http://yoursite.com/policy/dashboard)
    re_path(r'^(?!api/|admin/|media/|static/).*$', TemplateView.as_view(template_name='index.html'), name='spa_catchall'),
]
# =============================================================================
# SPA ROUTING SUPPORT - Vue.js Frontend Catch-All
# =============================================================================
# This MUST be at the end to catch all non-API routes and serve index.html
# This allows Vue Router to handle client-side routing
# Important: All API routes should be prefixed with /api/ to avoid conflicts
urlpatterns += [
    # Catch-all pattern for Vue.js SPA routing
    # Matches any URL that doesn't start with 'api/', 'admin/', 'auth/', 'oauth/', 'media/', or 'static/'
    # This allows direct URL access (e.g., http://yoursite.com/policy/dashboard)
    re_path(r'^(?!api/|admin/|auth/|oauth/|media/|static/).*$', TemplateView.as_view(template_name='index.html'), name='spa_catchall'),
]