from django.contrib import admin
from .models import User, MfaEmailChallenge, MfaAuditLog


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('userid', 'username', 'email', 'first_name', 'last_name', 'is_active', 'created_at')
    list_filter = ('is_active_raw', 'department_id', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('userid', 'created_at', 'updated_at')
    
    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True


@admin.register(MfaEmailChallenge)
class MfaEmailChallengeAdmin(admin.ModelAdmin):
    list_display = ('challenge_id', 'user', 'status', 'attempts', 'expires_at', 'created_at')
    list_filter = ('status', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('challenge_id', 'otp_hash', 'created_at', 'used_at')
    raw_id_fields = ('user',)
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Prevent manual editing


@admin.register(MfaAuditLog)
class MfaAuditLogAdmin(admin.ModelAdmin):
    list_display = ('mfa_event_id', 'user', 'event_type', 'ip_address', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('mfa_event_id', 'created_at')
    raw_id_fields = ('user',)
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Prevent manual editing
