"""
Serializers for the core app.
"""
from rest_framework import serializers
from tprm_backend.utils.base_serializer import AutoDecryptingModelSerializer
from .models import (
    AuditLog, SystemConfiguration, NotificationTemplate,
    FileUpload, Dashboard, Widget, Report, ReportExecution, Integration
)


class AuditLogSerializer(AutoDecryptingModelSerializer):
    """Serializer for AuditLog model."""
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'action', 'entity_type', 'entity_id',
            'entity_name', 'changes', 'old_value', 'new_value',
            'ip_address', 'user_agent', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SystemConfigurationSerializer(AutoDecryptingModelSerializer):
    """Serializer for SystemConfiguration model."""
    
    class Meta:
        model = SystemConfiguration
        fields = [
            'id', 'key', 'value', 'description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationTemplateSerializer(AutoDecryptingModelSerializer):
    """Serializer for NotificationTemplate model."""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'template_type', 'subject', 'body',
            'variables', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FileUploadSerializer(AutoDecryptingModelSerializer):
    """Serializer for FileUpload model."""
    
    class Meta:
        model = FileUpload
        fields = [
            'id', 'file', 'original_filename', 'file_size',
            'content_type', 'uploaded_by', 'is_processed',
            'processing_status', 'processing_errors', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DashboardSerializer(AutoDecryptingModelSerializer):
    """Serializer for Dashboard model."""
    
    class Meta:
        model = Dashboard
        fields = [
            'id', 'name', 'description', 'layout', 'widgets',
            'is_default', 'is_public', 'owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class WidgetSerializer(AutoDecryptingModelSerializer):
    """Serializer for Widget model."""
    
    class Meta:
        model = Widget
        fields = [
            'id', 'name', 'widget_type', 'configuration',
            'data_source', 'refresh_interval', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReportSerializer(AutoDecryptingModelSerializer):
    """Serializer for Report model."""
    
    class Meta:
        model = Report
        fields = [
            'id', 'name', 'report_type', 'description', 'query',
            'parameters', 'schedule', 'recipients', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReportExecutionSerializer(AutoDecryptingModelSerializer):
    """Serializer for ReportExecution model."""
    report = ReportSerializer(read_only=True)
    
    class Meta:
        model = ReportExecution
        fields = [
            'id', 'report', 'status', 'started_at', 'completed_at',
            'result_file', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class IntegrationSerializer(AutoDecryptingModelSerializer):
    """Serializer for Integration model."""
    
    class Meta:
        model = Integration
        fields = [
            'id', 'name', 'integration_type', 'configuration',
            'is_active', 'last_sync', 'sync_status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
