"""
URL patterns for the core app.
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard endpoints
    path('dashboard/', views.dashboard_overview, name='dashboard'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    
    # File upload endpoints
    path('upload/', views.file_upload, name='file-upload'),
    path('upload/<int:pk>/', views.file_detail, name='file-detail'),
    
    # System configuration endpoints
    path('config/', views.system_config, name='system-config'),
    
    # Notification templates
    path('templates/', views.notification_templates, name='notification-templates'),
    path('templates/<int:pk>/', views.template_detail, name='template-detail'),
    
    # Reports
    path('reports/', views.reports_list, name='reports-list'),
    path('reports/<int:pk>/', views.report_detail, name='report-detail'),
    path('reports/<int:pk>/execute/', views.execute_report, name='execute-report'),
    
    # Integrations
    path('integrations/', views.integrations_list, name='integrations-list'),
    path('integrations/<int:pk>/', views.integration_detail, name='integration-detail'),
    
    # Audit logs
    path('audit-logs/', views.audit_logs, name='audit-logs'),
]
