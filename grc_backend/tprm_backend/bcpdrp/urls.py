"""
URL patterns for BCP/DRP API - Clean slate for screen-by-screen development
"""
from django.urls import path
from . import views
from . import bcpdrp_dashboard

urlpatterns = [
    # Plan endpoints
    path('plans/', views.plan_list_view, name='plan-list'),
    path('plans/<int:plan_id>/comprehensive/', views.comprehensive_plan_detail_view, name='comprehensive-plan-detail'),
    path('strategies/', views.strategy_list_view, name='strategy-list'),
    
    # OCR endpoints
    path('ocr/plans/', views.ocr_plans_list_view, name='ocr-plans-list'),
    path('ocr/plans/<int:plan_id>/', views.ocr_plan_detail_view, name='ocr-plan-detail'),
    path('ocr/plans/<int:plan_id>/extract/', views.ocr_extraction_save_view, name='ocr-extraction-save'),
    path('ocr/plans/<int:plan_id>/status/', views.ocr_status_update_view, name='ocr-status-update'),
    
    # Evaluation endpoints
    path('evaluations/<int:plan_id>/', views.evaluation_list_view, name='evaluation-list'),
    path('evaluations/<int:plan_id>/save/', views.evaluation_save_view, name='evaluation-save'),
    
    # Plan risks endpoint
    path('plans/<int:plan_id>/risks/', views.plan_risks_view, name='plan-risks'),
    
    # Decision endpoints
    path('plans/<int:plan_id>/decision/', views.plan_decision_view, name='plan-decision'),
    path('plans/<int:plan_id>/approve/', views.plan_approve_view, name='plan-approve'),
    path('plans/<int:plan_id>/reject/', views.plan_reject_view, name='plan-reject'),
    
    # Vendor upload endpoint
    path('vendor-upload/', views.vendor_upload_view, name='vendor-upload'),
    
    # Dropdown endpoints
    path('dropdowns/', views.dropdown_list_view, name='dropdown-list'),
    
    # Plan type management endpoints
    path('plan-types/', views.plan_types_list_view, name='plan-types-list'),
    path('plan-types/create/', views.plan_type_create_view, name='plan-type-create'),
    path('plan-types/<int:plan_type_id>/update/', views.plan_type_update_view, name='plan-type-update'),
    path('plan-types/<int:plan_type_id>/delete/', views.plan_type_delete_view, name='plan-type-delete'),
    
    # Questionnaire endpoints
    path('questionnaires/', views.questionnaire_list_view, name='questionnaire-list'),
    path('questionnaires/<int:questionnaire_id>/', views.questionnaire_detail_view, name='questionnaire-detail'),
    path('questionnaires/<int:questionnaire_id>/review/', views.questionnaire_review_save_view, name='questionnaire-review-save'),
    path('questionnaires/save/', views.questionnaire_save_view, name='questionnaire-save'),
    path('questionnaire-templates/', views.questionnaire_template_list_view, name='questionnaire-template-list'),
    path('questionnaire-templates/<int:template_id>/', views.questionnaire_template_get_view, name='questionnaire-template-get'),
    path('questionnaire-templates/save/', views.questionnaire_template_save_view, name='questionnaire-template-save'),
    path('questionnaires/assign/', views.questionnaire_assignment_create_view, name='questionnaire-assignment-create'),
    path('questionnaires/assignments/', views.questionnaire_assignments_list_view, name='questionnaire-assignments-list'),
    path('questionnaires/assignments/<int:assignment_id>/save/', views.questionnaire_assignment_save_answers_view, name='questionnaire-assignment-save-answers'),
    path('questionnaires/assignments/<int:assignment_id>/approve/', views.assignment_approve_view, name='assignment-approve'),
    path('questionnaires/assignments/<int:assignment_id>/reject/', views.assignment_reject_view, name='assignment-reject'),
    path('questionnaires/<int:questionnaire_id>/approve/', views.questionnaire_approve_view, name='questionnaire-approve'),
    path('questionnaires/<int:questionnaire_id>/reject/', views.questionnaire_reject_view, name='questionnaire-reject'),
    
    # User management endpoints
    path('users/', views.users_list_view, name='users-list'),
    
    # Approval assignment endpoints
    path('approvals/', views.approval_assignments_list_view, name='approval-assignments-list'),
    path('approvals/assignments/', views.approval_assignment_create_view, name='approval-assignment-create'),
    path('approvals/<int:approval_id>/status/', views.approval_status_update_view, name='approval-status-update'),
    path('my-approvals/', views.my_approvals_view, name='my-approvals'),
    
    
    # Dashboard endpoints
    path('dashboard/debug/', bcpdrp_dashboard.dashboard_debug, name='dashboard-debug'),
    path('dashboard/db-test/', bcpdrp_dashboard.dashboard_db_test, name='dashboard-db-test'),
    path('dashboard/test/', bcpdrp_dashboard.dashboard_test, name='dashboard-test'),
    path('dashboard/overview/', bcpdrp_dashboard.dashboard_overview, name='dashboard-overview'),
    path('dashboard/plans/', bcpdrp_dashboard.dashboard_plan_metrics, name='dashboard-plan-metrics'),
    path('dashboard/evaluations/', bcpdrp_dashboard.dashboard_evaluation_metrics, name='dashboard-evaluation-metrics'),
    path('dashboard/evaluation-scores/', bcpdrp_dashboard.dashboard_evaluation_scores_metrics, name='dashboard-evaluation-scores-metrics'),
    path('dashboard/testing/', bcpdrp_dashboard.dashboard_testing_metrics, name='dashboard-testing-metrics'),
    path('dashboard/risks/', bcpdrp_dashboard.dashboard_risk_metrics, name='dashboard-risk-metrics'),
    path('dashboard/temporal/', bcpdrp_dashboard.dashboard_temporal_metrics, name='dashboard-temporal-metrics'),
    path('dashboard/kpi/', bcpdrp_dashboard.dashboard_kpi_metrics, name='dashboard-kpi-metrics'),
]