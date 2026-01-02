from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'notification_type', 'priority', 'status', 'created_at']
    list_filter = ['priority', 'status', 'notification_type', 'channel']
    search_fields = ['title', 'message']
    readonly_fields = ['id', 'created_at', 'sent_at', 'delivered_at', 'read_at']
    ordering = ['-created_at']