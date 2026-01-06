"""
URL patterns for TPRM RBAC system
"""

from django.urls import path
from . import tprm_views
from . import access_request_views

urlpatterns = [
    # Core RBAC endpoints
    path('permissions/', tprm_views.get_user_permissions, name='get_user_permissions'),
    path('role/', tprm_views.get_user_role, name='get_user_role'),
    path('bulk-check/', tprm_views.bulk_check_permissions, name='bulk_check_permissions'),
    
    # Module-specific permission checks
    path('rfp/', tprm_views.check_rfp_permission, name='check_rfp_permission'),
    path('contract/', tprm_views.check_contract_permission, name='check_contract_permission'),
    path('vendor/', tprm_views.check_vendor_permission, name='check_vendor_permission'),
    path('risk/', tprm_views.check_risk_permission, name='check_risk_permission'),
    path('compliance/', tprm_views.check_compliance_permission, name='check_compliance_permission'),
    path('bcp-drp/', tprm_views.check_bcp_drp_permission, name='check_bcp_drp_permission'),
    path('sla/', tprm_views.check_sla_permission, name='check_sla_permission'),
    
    # Module access checks
    path('module-access/', tprm_views.check_module_access, name='check_module_access'),
    
    # Access Request endpoints
    path('access-requests/', access_request_views.create_access_request, name='create_access_request'),
    path('access-requests/<int:user_id>/', access_request_views.get_access_requests, name='get_access_requests'),
    path('access-requests/<int:request_id>/update-status/', access_request_views.update_access_request_status, name='update_access_request_status'),
]
