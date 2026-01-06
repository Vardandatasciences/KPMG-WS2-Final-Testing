from django.urls import path
from . import views

app_name = 'contractapproval'

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health-check'),
    
    # Contract Approval CRUD operations
    path('approvals/', views.approval_list, name='approval-list'),
    path('approvals/<int:pk>/', views.approval_detail, name='approval-detail'),
    path('approvals/create/', views.approval_create, name='approval-create'),
    path('approvals/bulk-create/', views.approval_bulk_create, name='approval-bulk-create'),
    path('approvals/<int:pk>/update/', views.approval_update, name='approval-update'),
    path('approvals/<int:pk>/delete/', views.approval_delete, name='approval-delete'),
    
    # Contract Approval Statistics
    path('approvals/stats/', views.approval_stats, name='approval-stats'),
    
    # Contract-specific approval operations
    path('contracts/<int:contract_id>/approvals/', views.contract_approvals_list, name='contract-approvals-list'),
    path('get-contract-approvals/', views.get_contract_approvals, name='get-contract-approvals'),
    
    # Assigner review operations
    path('assigner-approvals/', views.get_assigner_approvals, name='assigner-approvals'),
    path('approvals/<int:approval_id>/approve/', views.approve_contract, name='approve-contract'),
    path('approvals/<int:approval_id>/reject/', views.reject_contract, name='reject-contract'),
    
    # Comprehensive contract detail for review
    path('contracts/<int:contract_id>/comprehensive/', views.contract_comprehensive_detail, name='contract-comprehensive-detail'),
]
