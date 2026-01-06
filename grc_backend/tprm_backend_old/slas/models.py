"""
SLA models for Vendor Guard Hub matching MySQL schema.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
# from simple_history.models import HistoricalRecords
# from core.models import BaseModel


class Vendor(models.Model):
    """Vendor information matching tprm_integration MySQL schema."""
    vendor_id = models.BigAutoField(primary_key=True)
    vendor_code = models.CharField(max_length=50, blank=True, null=True)
    company_name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    
    class Meta:
        managed = False
        verbose_name = _('Vendor')
        verbose_name_plural = _('Vendors')
        ordering = ['company_name']
        db_table = 'vendors'
    
    def __str__(self):
        return self.company_name


class Contract(models.Model):
    """Contract information matching MySQL schema."""
    contract_id = models.BigAutoField(primary_key=True)
    contract_name = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'contracts'
        verbose_name = _('Contract')
        verbose_name_plural = _('Contracts')
        ordering = ['contract_name']
    
    def __str__(self):
        return self.contract_name


class VendorSLA(models.Model):
    """Vendor SLA matching MySQL schema."""
    sla_id = models.BigAutoField(primary_key=True)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='vendor_slas',
        db_column='vendor_id'
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='vendor_slas',
        db_column='contract_id'
    )
    sla_name = models.CharField(max_length=255)
    sla_type = models.CharField(
        max_length=20,
        choices=[
            ('AVAILABILITY', 'Availability'),
            ('RESPONSE_TIME', 'Response Time'),
            ('RESOLUTION_TIME', 'Resolution Time'),
            ('QUALITY', 'Quality'),
            ('CUSTOM', 'Custom'),
        ]
    )
    effective_date = models.DateField()
    expiry_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('INACTIVE', 'Inactive'),
            ('EXPIRED', 'Expired'),
            ('PENDING', 'Pending'),
        ],
        default='PENDING'
    )
    business_service_impacted = models.CharField(max_length=255, blank=True)
    reporting_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ],
        default='monthly'
    )
    baseline_period = models.CharField(max_length=100, blank=True)
    improvement_targets = models.JSONField(default=dict, blank=True)
    penalty_threshold = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    credit_threshold = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    measurement_methodology = models.TextField(blank=True)
    exclusions = models.TextField(blank=True)
    force_majeure_clauses = models.TextField(blank=True)
    compliance_framework = models.CharField(max_length=255, blank=True)
    audit_requirements = models.TextField(blank=True)
    document_versioning = models.CharField(max_length=255, blank=True)
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    priority = models.CharField(
        max_length=20,
        choices=[
            ('HIGH', 'High'),
            ('MEDIUM', 'Medium'),
            ('LOW', 'Low'),
            ('CRITICAL', 'Critical'),
        ],
        default='MEDIUM'
    )
    approval_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('APPROVED', 'Approved'),
        ],
        default='PENDING'
    )
    
    # history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Vendor SLA')
        verbose_name_plural = _('Vendor SLAs')
        ordering = ['-effective_date']
        db_table = 'vendor_slas'
    
    def __str__(self):
        return f"{self.sla_name} - {self.vendor.company_name}"
    
    def is_expired(self):
        """Check if the SLA has expired based on expiry_date."""
        from django.utils import timezone
        return timezone.now().date() > self.expiry_date
    
    def update_status_if_expired(self):
        """Update status to EXPIRED if the SLA has expired."""
        if self.is_expired() and self.status != 'EXPIRED':
            self.status = 'EXPIRED'
            self.save(update_fields=['status'])
            return True
        return False


class SLAMetric(models.Model):
    """SLA metrics matching MySQL schema."""
    metric_id = models.BigAutoField(primary_key=True)
    sla = models.ForeignKey(
        VendorSLA,
        on_delete=models.CASCADE,
        related_name='sla_metrics',
        db_column='sla_id'
    )
    metric_name = models.CharField(max_length=255)
    threshold = models.DecimalField(max_digits=10, decimal_places=2)
    measurement_unit = models.CharField(max_length=50, default='%')
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
            ('QUARTERLY', 'Quarterly'),
        ]
    )
    penalty = models.TextField(blank=True)
    measurement_methodology = models.TextField(blank=True)
    
    # history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('SLA Metric')
        verbose_name_plural = _('SLA Metrics')
        ordering = ['metric_name']
        db_table = 'sla_metrics'
    
    def __str__(self):
        return f"{self.metric_name} - {self.threshold}"


class SLADocument(models.Model):
    """SLA documents matching MySQL schema."""
    document_id = models.BigAutoField(primary_key=True)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='sla_documents',
        db_column='vendor_id'
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='sla_documents',
        db_column='contract_id'
    )
    sla_name = models.CharField(max_length=255)
    document_file = models.BinaryField()
    file_type = models.CharField(max_length=50)
    extracted_data = models.JSONField(default=dict, blank=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_sla_documents'
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    processed_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PROCESSING', 'Processing'),
            ('PROCESSED', 'Processed'),
            ('FAILED', 'Failed'),
        ],
        default='PENDING'
    )
    
    # history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('SLA Document')
        verbose_name_plural = _('SLA Documents')
        ordering = ['-upload_date']
        db_table = 'sla_documents'
    
    def __str__(self):
        return f"{self.sla_name} - {self.file_type}"


class SLACompliance(models.Model):
    """SLA compliance tracking."""
    compliance_id = models.BigAutoField(primary_key=True)
    sla = models.ForeignKey(
        VendorSLA,
        on_delete=models.CASCADE,
        related_name='compliance_records',
        db_column='sla_id'
    )
    metric = models.ForeignKey(
        SLAMetric,
        on_delete=models.CASCADE,
        related_name='compliance_records',
        db_column='metric_id'
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    actual_value = models.DecimalField(max_digits=10, decimal_places=4)
    target_value = models.DecimalField(max_digits=10, decimal_places=4)
    compliance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Compliance percentage"
    )
    is_compliant = models.BooleanField()
    breach_duration = models.DurationField(null=True, blank=True)
    penalty_applied = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    
    # history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('SLA Compliance')
        verbose_name_plural = _('SLA Compliance Records')
        ordering = ['-period_start']
        db_table = 'sla_compliance'
    
    def __str__(self):
        return f"{self.sla.sla_name} - {self.metric.metric_name} - {self.period_start.date()}"


class SLAViolation(models.Model):
    """SLA violation records."""
    violation_id = models.BigAutoField(primary_key=True)
    sla = models.ForeignKey(
        VendorSLA,
        on_delete=models.CASCADE,
        related_name='violations',
        db_column='sla_id'
    )
    metric = models.ForeignKey(
        SLAMetric,
        on_delete=models.CASCADE,
        related_name='violations',
        db_column='metric_id'
    )
    violation_date = models.DateTimeField()
    violation_type = models.CharField(
        max_length=20,
        choices=[
            ('warning', 'Warning'),
            ('critical', 'Critical'),
            ('breach', 'Breach'),
        ]
    )
    actual_value = models.DecimalField(max_digits=10, decimal_places=4)
    expected_value = models.DecimalField(max_digits=10, decimal_places=4)
    duration = models.DurationField(null=True, blank=True)
    impact_assessment = models.TextField(blank=True)
    mitigation_actions = models.TextField(blank=True)
    penalty_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('investigating', 'Investigating'),
            ('mitigated', 'Mitigated'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ],
        default='open'
    )
    
    # history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('SLA Violation')
        verbose_name_plural = _('SLA Violations')
        ordering = ['-violation_date']
        db_table = 'sla_violations'
    
    def __str__(self):
        return f"{self.sla.sla_name} - {self.violation_type} - {self.violation_date}"


class SLAReview(models.Model):
    """SLA review and assessment."""
    review_id = models.BigAutoField(primary_key=True)
    sla = models.ForeignKey(
        VendorSLA,
        on_delete=models.CASCADE,
        related_name='reviews',
        db_column='sla_id'
    )
    review_date = models.DateField()
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sla_reviews'
    )
    review_type = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annual', 'Annual'),
            ('adhoc', 'Ad-hoc'),
        ]
    )
    overall_score = models.PositiveIntegerField(
        help_text="Overall SLA performance score (0-100)"
    )
    strengths = models.TextField(blank=True)
    weaknesses = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    action_items = models.JSONField(default=list)
    next_review_date = models.DateField()
    
    # history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('SLA Review')
        verbose_name_plural = _('SLA Reviews')
        ordering = ['-review_date']
        db_table = 'sla_reviews'
    
    def __str__(self):
        return f"{self.sla.sla_name} - {self.review_type} - {self.review_date}"