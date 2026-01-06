from django.contrib import admin
from .models import Risk

# Removed TPRMModuleAdmin and ModuleDataAdmin - using entity-data-row approach


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'likelihood', 'impact', 'exposure_rating', 'score', 
        'priority', 'status', 'assigned_to', 'created_at'
    ]
    list_filter = [
        'priority', 'status', 'likelihood', 'impact', 'exposure_rating',
        'created_at', 'updated_at'
    ]
    search_fields = ['id', 'title', 'description', 'ai_explanation']
    readonly_fields = ['id', 'score', 'priority', 'created_at', 'updated_at']
    filter_horizontal = []
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'title', 'description')
        }),
        ('Risk Scoring', {
            'fields': ('likelihood', 'impact', 'exposure_rating', 'score', 'priority')
        }),
        ('AI Analysis', {
            'fields': ('ai_explanation', 'suggested_mitigations')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_to', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'acknowledged_at', 'mitigated_at'),
            'classes': ('collapse',)
        }),
    )
