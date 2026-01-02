from django.urls import path
from . import views

app_name = 'slaapproval'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health-check'),
    
    # SLA Approval CRUD operations
    path('approvals/create/', views.approval_create, name='approval-create'),
    path('approvals/bulk-create/', views.approval_bulk_create, name='approval-bulk-create'),
    path('approvals/stats/', views.approval_stats, name='approval-stats'),
    path('approvals/<int:pk>/update/', views.approval_update, name='approval-update'),
    path('approvals/<int:pk>/delete/', views.approval_delete, name='approval-delete'),
    path('approvals/<int:pk>/', views.approval_detail, name='approval-detail'),
    path('approvals/', views.approval_list, name='approval-list'),
    
    # SLA-specific approval operations
    path('slas/<int:sla_id>/approvals/', views.sla_approvals_list, name='sla-approvals-list'),
    
    # Assigner review operations
    path('assigner-approvals/', views.get_assigner_approvals, name='assigner-approvals'),
    path('approvals/<int:approval_id>/approve/', views.approve_sla, name='approve-sla'),
    path('approvals/<int:approval_id>/reject/', views.reject_sla, name='reject-sla'),
    
    # User management
    path('available-users/', views.available_users, name='available-users'),
]