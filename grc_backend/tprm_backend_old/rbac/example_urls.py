"""
URL patterns for TPRM RBAC Example Views
"""

from django.urls import path
from . import example_views

urlpatterns = [
    # RFP Module Examples
    path('list-rfps/', example_views.list_rfps, name='list_rfps'),
    path('create-rfp/', example_views.create_rfp, name='create_rfp'),
    path('update-rfp/<int:rfp_id>/', example_views.update_rfp, name='update_rfp'),
    path('delete-rfp/<int:rfp_id>/', example_views.delete_rfp, name='delete_rfp'),
    
    # Contract Module Examples
    path('list-contracts/', example_views.list_contracts, name='list_contracts'),
    path('create-contract/', example_views.create_contract, name='create_contract'),
    path('update-contract/<int:contract_id>/', example_views.update_contract, name='update_contract'),
    
    # Vendor Module Examples
    path('list-vendors/', example_views.list_vendors, name='list_vendors'),
    path('create-vendor/', example_views.create_vendor, name='create_vendor'),
    
    # Risk Module Examples
    path('list-risk-assessments/', example_views.list_risk_assessments, name='list_risk_assessments'),
    path('create-risk-assessment/', example_views.create_risk_assessment, name='create_risk_assessment'),
    
    # Compliance Module Examples
    path('compliance-status/', example_views.get_compliance_status, name='get_compliance_status'),
    path('generate-compliance-report/', example_views.generate_compliance_report, name='generate_compliance_report'),
    
    # BCP/DRP Module Examples
    path('list-bcp-drp-plans/', example_views.list_bcp_drp_plans, name='list_bcp_drp_plans'),
    path('create-bcp-drp-plan/', example_views.create_bcp_drp_plan, name='create_bcp_drp_plan'),
    
    # Admin Module Examples
    path('admin-dashboard/', example_views.admin_dashboard, name='admin_dashboard'),
    path('configure-system-settings/', example_views.configure_system_settings, name='configure_system_settings'),
    
    # Combined Permission Examples
    path('cross-module-report/', example_views.cross_module_report, name='cross_module_report'),
    path('vendor-risk-assessment/', example_views.vendor_risk_assessment, name='vendor_risk_assessment'),
    
    # Utility Views
    path('test-user-permissions/', example_views.test_user_permissions, name='test_user_permissions'),
    path('debug-permission-check/', example_views.debug_permission_check, name='debug_permission_check'),
    path('test-jwt-auth/', example_views.test_jwt_auth, name='test_jwt_auth'),
    path('test-no-auth/', example_views.test_no_auth, name='test_no_auth'),
]
