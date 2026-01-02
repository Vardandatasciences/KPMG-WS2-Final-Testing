from django.contrib import admin
from .models import SearchIndex, SearchAnalytics


@admin.register(SearchIndex)
class SearchIndexAdmin(admin.ModelAdmin):
    """Admin interface for SearchIndex model."""
    
    list_display = [
        'id',
        'entity_type',
        'entity_id',
        'title',
        'updated_at'
    ]
    
    list_filter = [
        'entity_type',
        'updated_at'
    ]
    
    search_fields = [
        'title',
        'summary',
        'keywords'
    ]
    
    readonly_fields = [
        'id',
        'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('entity_type', 'entity_id', 'title')
        }),
        ('Content', {
            'fields': ('summary', 'keywords')
        }),
        ('Additional Data', {
            'fields': ('payload_json',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset for admin interface."""
        return super().get_queryset(request).select_related()


@admin.register(SearchAnalytics)
class SearchAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for SearchAnalytics model."""
    
    list_display = [
        'id',
        'query',
        'results_count',
        'response_time',
        'created_at'
    ]
    
    list_filter = [
        'created_at'
    ]
    
    search_fields = [
        'query'
    ]
    
    readonly_fields = [
        'id',
        'created_at'
    ]
    
    fieldsets = (
        ('Search Information', {
            'fields': ('query', 'results_count', 'response_time')
        }),
        ('Filters', {
            'fields': ('filters_used',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual creation of analytics records."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of analytics records."""
        return False
