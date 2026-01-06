"""
Core models for Vendor Guard Hub.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords

User = get_user_model()


class BaseModel(models.Model):
    """Base model with common fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    
    class Meta:
        abstract = True


class AuditLog(BaseModel):
    """Audit log for tracking changes."""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('escalate', 'Escalate'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    entity_name = models.CharField(max_length=255)
    changes = models.JSONField(default=dict)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('warning', 'Warning'),
        ],
        default='success'
    )
    
    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.entity_name}"


class SystemConfiguration(BaseModel):
    """System configuration settings."""
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('System Configuration')
        verbose_name_plural = _('System Configurations')
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value}"


class NotificationTemplate(BaseModel):
    """Notification templates."""
    TEMPLATE_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('slack', 'Slack'),
        ('webhook', 'Webhook'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    variables = models.JSONField(default=list, help_text="Available template variables")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"


class FileUpload(BaseModel):
    """File upload model."""
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploads'
    )
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    processing_errors = models.JSONField(default=list)
    
    class Meta:
        verbose_name = _('File Upload')
        verbose_name_plural = _('File Uploads')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.original_filename} ({self.uploaded_by.username})"


class Dashboard(BaseModel):
    """Dashboard configuration."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    layout = models.JSONField(default=dict)
    widgets = models.JSONField(default=list)
    is_default = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboards'
    )
    
    class Meta:
        verbose_name = _('Dashboard')
        verbose_name_plural = _('Dashboards')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Widget(BaseModel):
    """Dashboard widget configuration."""
    WIDGET_TYPE_CHOICES = [
        ('chart', 'Chart'),
        ('metric', 'Metric'),
        ('table', 'Table'),
        ('list', 'List'),
        ('gauge', 'Gauge'),
        ('heatmap', 'Heatmap'),
    ]
    
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPE_CHOICES)
    configuration = models.JSONField(default=dict)
    data_source = models.CharField(max_length=100, blank=True)
    refresh_interval = models.PositiveIntegerField(default=300, help_text="Refresh interval in seconds")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Widget')
        verbose_name_plural = _('Widgets')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.widget_type})"


class Report(BaseModel):
    """Report configuration."""
    REPORT_TYPE_CHOICES = [
        ('sla', 'SLA Report'),
        ('performance', 'Performance Report'),
        ('compliance', 'Compliance Report'),
        ('vendor', 'Vendor Report'),
        ('custom', 'Custom Report'),
    ]
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    query = models.JSONField(default=dict)
    parameters = models.JSONField(default=dict)
    schedule = models.CharField(max_length=100, blank=True, help_text="Cron expression for scheduling")
    recipients = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"


class ReportExecution(BaseModel):
    """Report execution history."""
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result_file = models.FileField(upload_to='reports/', null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Report Execution')
        verbose_name_plural = _('Report Executions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.report.name} - {self.status}"


class Integration(BaseModel):
    """External system integrations."""
    INTEGRATION_TYPE_CHOICES = [
        ('email', 'Email Service'),
        ('slack', 'Slack'),
        ('webhook', 'Webhook'),
        ('api', 'API'),
        ('database', 'Database'),
    ]
    
    name = models.CharField(max_length=100)
    integration_type = models.CharField(max_length=20, choices=INTEGRATION_TYPE_CHOICES)
    configuration = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('pending', 'Pending'),
        ],
        default='pending'
    )
    
    class Meta:
        verbose_name = _('Integration')
        verbose_name_plural = _('Integrations')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.integration_type})"
