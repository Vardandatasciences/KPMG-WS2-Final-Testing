"""URL patterns for Admin Access Control (see admin_access.authz for BOLA rules)."""
from django.urls import path
from . import views

urlpatterns = [
    # User management
    path('users/', views.get_all_users, name='admin_get_all_users'),
    path('users/<int:user_id>/permissions/', views.get_user_permissions, name='admin_get_user_permissions'),
    
    # Permission management
    path('permissions/update/', views.update_user_permissions, name='admin_update_permissions'),
    path('permissions/bulk-update/', views.bulk_update_permissions, name='admin_bulk_update_permissions'),
    path('permissions/fields/', views.get_all_permission_fields, name='admin_get_permission_fields'),
]

