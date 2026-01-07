"""
Core Models for TPRM Multi-Tenancy

This module contains the Tenant model and TenantAwareModel base class
for implementing multi-tenancy across all TPRM modules.
"""
"""
Core models for Vendor Guard Hub.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin

User = get_user_model()


class BaseModel(TPRMEncryptedFieldsMixin, models.Model):
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

from django.db import models
from django.utils import timezone


class TenantAwareModel(models.Model):
    """
    Abstract base model that automatically sets tenant_id when creating records.
    
    Usage:
        class MyModel(TenantAwareModel):
            # Your fields here
            pass
            
        # When creating:
        my_model = MyModel.objects.create(...)  # tenant_id automatically set!
    """
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically set tenant_id if not already set
        """
        # Only set tenant if:
        # 1. Model has tenant field
        # 2. tenant is not already set
        # 3. We're creating a new record (pk is None)
        if hasattr(self, 'tenant') and self.tenant is None and self.pk is None:
            from .tenant_context import get_current_tenant
            tenant_id = get_current_tenant()
            
            if tenant_id:
                try:
                    # Set tenant using the Tenant model
                    tenant = Tenant.objects.get(tenant_id=tenant_id)
                    self.tenant = tenant
                except Tenant.DoesNotExist:
                    pass  # Tenant not found, skip auto-assignment
        
        super().save(*args, **kwargs)


class Tenant(models.Model):
    """
    Tenant model for multi-tenancy support.
    Each tenant represents an organization/company using the TPRM platform.
    
    This matches the GRC tenants table schema exactly for consistency.
    """
    tenant_id = models.AutoField(primary_key=True, db_column='TenantId')
    name = models.CharField(max_length=255, db_column='Name', help_text="Organization/Company Name")
    subdomain = models.CharField(max_length=100, unique=True, db_column='Subdomain', 
                                  help_text="Unique subdomain for tenant")
    license_key = models.CharField(max_length=100, unique=True, null=True, blank=True, db_column='LicenseKey',
                                    help_text="Unique license key for tenant")
    subscription_tier = models.CharField(max_length=50, default='starter', db_column='SubscriptionTier',
                                        choices=[
                                            ('starter', 'Starter'),
                                            ('professional', 'Professional'),
                                            ('enterprise', 'Enterprise')
                                        ])
    status = models.CharField(max_length=20, default='trial', db_column='Status',
                             choices=[
                                 ('trial', 'Trial'),
                                 ('active', 'Active'),
                                 ('suspended', 'Suspended'),
                                 ('cancelled', 'Cancelled')
                             ])
    max_users = models.IntegerField(default=10, db_column='MaxUsers', 
                                    help_text="Maximum number of users allowed for this tenant")
    storage_limit_gb = models.IntegerField(default=10, db_column='StorageLimitGB',
                                          help_text="Storage limit in GB")
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')
    trial_ends_at = models.DateTimeField(null=True, blank=True, db_column='TrialEndsAt',
                                        help_text="Date when trial period ends")
    
    # Tenant settings (stored as JSON)
    settings = models.JSONField(default=dict, db_column='Settings',
                               help_text="Tenant-specific configuration settings")
    
    # Contact information
    primary_contact_email = models.EmailField(max_length=254, null=True, blank=True, db_column='PrimaryContactEmail',
                                             help_text="Primary contact email address")
    primary_contact_name = models.CharField(max_length=255, null=True, blank=True, db_column='PrimaryContactName',
                                           help_text="Primary contact name")
    primary_contact_phone = models.CharField(max_length=50, null=True, blank=True, db_column='PrimaryContactPhone',
                                            help_text="Primary contact phone number")
    
    class Meta:
        db_table = 'tenants'  # Note: table name is 'tenants' (plural) to match GRC
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['name']
        indexes = [
            models.Index(fields=['subdomain'], name='uniq_tenants_subdomain'),
            models.Index(fields=['license_key'], name='uniq_tenants_licensekey'),
            models.Index(fields=['status'], name='idx_tenants_status'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.subdomain})"
    
    def is_active(self):
        """Check if tenant is active"""
        return self.status == 'active'
    
    def is_trial_expired(self):
        """Check if trial period has expired"""
        if self.status == 'trial' and self.trial_ends_at:
            return timezone.now() > self.trial_ends_at
        return False
