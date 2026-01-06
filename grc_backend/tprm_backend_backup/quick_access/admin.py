from django.contrib import admin
from .models import GRCLog, QuickAccessFavorite


@admin.register(GRCLog)
class GRCLogAdmin(admin.ModelAdmin):
    list_display = ['log_id', 'user_name', 'module', 'action_type', 'timestamp', 'log_level']
    list_filter = ['module', 'action_type', 'log_level', 'timestamp']
    search_fields = ['user_name', 'description', 'module']
    readonly_fields = ['log_id', 'timestamp']
    ordering = ['-timestamp']


@admin.register(QuickAccessFavorite)
class QuickAccessFavoriteAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'title', 'module', 'created_at', 'order']
    list_filter = ['module', 'entity_type', 'created_at']
    search_fields = ['title', 'module', 'entity_type']
    readonly_fields = ['id', 'created_at']
    ordering = ['order', 'created_at']
