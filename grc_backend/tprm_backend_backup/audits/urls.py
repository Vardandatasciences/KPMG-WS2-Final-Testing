"""
URL patterns for the Audits app.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Audit CRUD
    path('', views.AuditListView.as_view(), name='audit-list'),
    path('<int:pk>/', views.AuditDetailView.as_view(), name='audit-detail'),
    
    # Static Questionnaires
    path('questionnaires/', views.StaticQuestionnaireListView.as_view(), name='questionnaire-list'),
    path('questionnaires/<int:pk>/', views.StaticQuestionnaireDetailView.as_view(), name='questionnaire-detail'),
    
    # Audit Versions
    path('versions/', views.AuditVersionListView.as_view(), name='audit-version-list'),
    path('versions/<int:pk>/', views.AuditVersionDetailView.as_view(), name='audit-version-detail'),
    
    # Audit Findings
    path('findings/', views.AuditFindingListView.as_view(), name='audit-finding-list'),
    path('findings/<int:pk>/', views.AuditFindingDetailView.as_view(), name='audit-finding-detail'),
    
    # Audit Reports
    path('reports/', views.AuditReportListView.as_view(), name='audit-report-list'),
    path('reports/<int:pk>/', views.AuditReportDetailView.as_view(), name='audit-report-detail'),
    
    # Dashboard and utilities
    path('dashboard/stats/', views.audit_dashboard_stats, name='audit-dashboard-stats'),
    path('available-slas/', views.available_slas, name='available-slas'),
    path('sla-metrics/<int:sla_id>/', views.sla_metrics, name='sla-metrics'),
    path('available-users/', views.available_users, name='available-users'),
    
    # Audit actions
    path('<int:audit_id>/submit-response/', views.submit_audit_response, name='submit-audit-response'),
    path('<int:audit_id>/review/', views.review_audit, name='review-audit'),
]
