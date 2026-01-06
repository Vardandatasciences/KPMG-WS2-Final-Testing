from django.contrib import admin
from .models import User, RBACTPRM

# Register models for Django admin interface (optional)
# These are unmanaged models, so we'll just make them visible

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['userid', 'username', 'email', 'firstname', 'lastname', 'isactive']
    search_fields = ['username', 'email', 'firstname', 'lastname']
    list_filter = ['isactive', 'departmentid']
    readonly_fields = ['userid', 'createdat', 'updatedat']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RBACTPRM)
class RBACTPRMAdmin(admin.ModelAdmin):
    list_display = ['rbac_id', 'user_id', 'username', 'role', 'is_active']
    search_fields = ['username', 'role']
    list_filter = ['role', 'is_active']
    readonly_fields = ['rbac_id', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

