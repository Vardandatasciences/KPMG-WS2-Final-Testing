"""
Vendor Approval URLs - URL patterns for approval workflow management
"""

from django.urls import path
from . import views

urlpatterns = [
    # User management
    path('users/me/', views.get_current_user, name='get_current_user'),
    path('users/', views.get_users, name='get_users'),
    path('users/add-dummy/', views.add_dummy_users, name='add_dummy_users'),
    
    # Questionnaire management
    path('questionnaires/active/', views.get_active_questionnaires, name='get_active_questionnaires'),
    path('questionnaire-assignments/submitted/', views.get_submitted_questionnaire_assignments, name='get_submitted_questionnaire_assignments'),
    path('reviewer-scores/save/', views.save_reviewer_scores, name='save_reviewer_scores'),
    path('stage-draft/save/', views.save_stage_draft, name='save_stage_draft'),
    path('stage-draft/load/<str:stage_id>/', views.load_stage_draft, name='load_stage_draft'),
    path('parallel-scoring/<str:approval_id>/', views.get_parallel_approval_scoring_data, name='get_parallel_approval_scoring_data'),
    path('final-assignee-scores/save/', views.save_final_assignee_scores, name='save_final_assignee_scores'),
    
    # Workflow management
    path('workflows/', views.create_workflow, name='create_workflow'),
    path('workflows/list/', views.get_workflows, name='get_workflows'),
    path('workflows/<str:workflow_id>/stages/', views.get_workflow_stages, name='get_workflow_stages'),
    
    # Comprehensive workflow creation
    path('create-workflow-request/', views.create_comprehensive_workflow, name='create_comprehensive_workflow'),
    
    # Approval request management
    path('requests/', views.create_workflow_request, name='create_workflow_request'),
    path('requests/by-requester/', views.get_approvals_by_requester, name='get_approvals_by_requester'),

    # My approvals
    path('my-approvals/', views.get_my_approvals, name='get_my_approvals'),

    # Stage reviewer utilities
    path('stages/reviewers/', views.get_stage_reviewers, name='get_stage_reviewers'),
    path('stages/assigned/<str:user_id>/', views.get_user_assigned_stages, name='get_user_assigned_stages'),
    path('stages/<str:stage_id>/action/', views.post_stage_action, name='post_stage_action'),

    # Single request + requester final decision
    path('requests/<str:approval_id>/', views.get_request_with_stages, name='get_request_with_stages'),
    path('requests/<str:approval_id>/requester-final-decision/', views.requester_final_decision, name='requester_final_decision'),
    path('requests/<str:approval_id>/versions/', views.get_request_versions, name='get_request_versions'),
    path('requests/<str:approval_id>/version-history/', views.get_approval_version_history, name='get_approval_version_history'),
    path('requests/<str:approval_id>/debug-versions/', views.debug_version_data, name='debug_version_data'),
    
    # Admin controls for multi-level workflows
    path('requests/<str:approval_id>/admin-handle-rejection/', views.admin_handle_rejection, name='admin_handle_rejection'),

    # Questionnaire helper (scoped under vendor_approval for convenience)
    path('questionnaires/<int:questionnaire_id>/questions/', views.get_questionnaire_questions, name='get_questionnaire_questions'),
    
    # Dashboard and Analytics URLs
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('dashboard/recent-requests/', views.recent_requests, name='recent_requests'),
    path('dashboard/user-tasks/<str:user_id>/', views.user_tasks, name='user_tasks'),
    path('dashboard/user-requests/<str:user_id>/', views.user_requests, name='user_requests'),
    
    # Vendor management
    path('vendors/', views.get_vendors, name='get_vendors'),
    path('vendors/<int:vendor_id>/', views.get_vendor_detail, name='get_vendor_detail'),
    path('vendors/<int:vendor_id>/risks/', views.get_vendor_risks, name='get_vendor_risks'),
    
    # Risk generation status
    path('risk-generation-status/<str:approval_id>/', views.check_risk_generation_status, name='check_risk_generation_status'),
    
    # Test lifecycle stage 3
    path('test-lifecycle-stage-3/<int:vendor_id>/', views.test_lifecycle_stage_3, name='test_lifecycle_stage_3'),
]
