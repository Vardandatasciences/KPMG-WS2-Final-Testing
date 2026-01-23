"""
GRC RBAC URL Configuration
This file contains only the RBAC routes for GRC, to be included under /api/grc/rbac/
"""
from django.urls import path
from grc.rbac import views as rbac_views
from .routes.Global import rbac_test_views
from . import views

urlpatterns = [
    # Core RBAC endpoints (without 'rbac/' prefix since it's added in the main urls.py)
    path('user-permissions/', rbac_views.get_user_permissions, name='grc-api-user-permissions'),
    path('user-role/', views.get_user_role_simple, name='grc-api-user-role'),
    path('check-permission/', rbac_views.check_permission, name='grc-rbac-check-permission'),
    path('check-permission', rbac_views.check_permission, name='grc-rbac-check-permission-no-slash'),
    path('users-for-dropdown/', views.get_users_for_dropdown_simple, name='grc-api-users-for-dropdown'),
    
    # User management test endpoints
    path('test-user-details/<int:user_id>/', views.get_user_details_by_id, name='grc-test-user-details'),
    path('save-user-session/', views.save_user_session, name='grc-save-user-session'),
    
    # RBAC Test endpoints for permission verification
    path('test/policy-view/', rbac_test_views.test_policy_view_permission, name='grc-test-policy-view'),
    path('test/policy-create/', rbac_test_views.test_policy_create_permission, name='grc-test-policy-create'),
    path('test/policy-edit/', rbac_test_views.test_policy_edit_permission, name='grc-test-policy-edit'),
    path('test/audit-view/', rbac_test_views.test_audit_view_permission, name='grc-test-audit-view'),
    path('test/audit-conduct/', rbac_test_views.test_audit_conduct_permission, name='grc-test-audit-conduct'),
    path('test/audit-review/', rbac_test_views.test_audit_review_permission, name='grc-test-audit-review'),
    path('test/public/', rbac_test_views.test_public_endpoint, name='grc-test-public'),
]
