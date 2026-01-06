"""
URL configuration for RFP Approval Workflow Management
"""

from django.urls import path
from . import views

urlpatterns = [
    # Workflow management
    path('workflows/', views.workflows, name='approval-workflows'),
    
    # User management
    path('users/', views.users, name='approval-users'),
    
    # Approval request management
    path('requests/', views.approval_requests, name='approval-requests'),
    
    # Stage management
    path('stages/', views.stages, name='approval-stages'),
    
    # Comment management
    path('comments/', views.comments, name='approval-comments'),
    
    # User-specific approvals
    path('user-approvals/', views.user_approvals, name='user-approvals'),
    path('get-proposal-id/<str:approval_id>/', views.get_proposal_id_from_approval, name='get_proposal_id_from_approval'),
    
    # RFP details
    path('rfp-details/<int:rfp_id>/', views.get_rfp_details, name='get-rfp-details'),
   
    # Document URL
    path('document-url/<int:file_id>/', views.get_document_url, name='get-document-url'),

    # Risks for response
    path('risks-for-response/<str:response_id>/', views.get_risks_for_response, name='get-risks-for-response'),
   
    # Version history
    path('approval-version-history/<str:approval_id>/', views.get_approval_version_history_api, name='get-approval-version-history'),
   
    # Version management
    path('approval-request-versions/', views.approval_request_versions, name='approval-request-versions'),
    path('approval-request-versions/<str:approval_id>/', views.get_approval_request_versions, name='get-approval-request-versions'),
    path('approval-request-versions/<str:version_id>/approve/', views.approve_version, name='approve-version'),
    # Update stage status
    path('update-stage-status/', views.update_stage_status, name='update-stage-status'),
    path('start-stage-review/', views.start_stage_review, name='start-stage-review'),
    
    # Change request management
    path('change-requests/', views.change_requests, name='change-requests'),
    path('change-requests/respond/', views.respond_to_change_request, name='respond-to-change-request'),
    # Test endpoints
    path('test-rfp-status-update/', views.test_rfp_status_update, name='test-rfp-status-update'),
    
    # Debug endpoints
    path('debug-approval-requests/', views.debug_approval_requests, name='debug-approval-requests'),
    path('debug-approval-stages/', views.debug_approval_stages, name='debug-approval-stages'),
    path('debug-stage-request-data/<str:stage_id>/', views.debug_stage_request_data, name='debug-stage-request-data'),
    path('create-sample-approval-request/', views.create_sample_approval_request, name='create-sample-approval-request'),
    path('debug-rfp-responses/', views.debug_rfp_responses, name='debug-rfp-responses'),
    path('debug-workflow/<str:workflow_id>/', views.debug_approval_workflow, name='debug-approval-workflow'),
    path('debug-connectivity/', views.debug_api_connectivity, name='debug-api-connectivity'),
]
