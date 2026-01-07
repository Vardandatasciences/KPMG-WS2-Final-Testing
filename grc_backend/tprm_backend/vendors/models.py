"""
Vendor management models for Vendor Guard Hub.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from tprm_backend.core.models import BaseModel

User = get_user_model()


class VendorCategory(BaseModel):
    """Vendor categories."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Vendor Category')
        verbose_name_plural = _('Vendor Categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class VendorRiskAssessment(BaseModel):
    """Vendor risk assessment."""
    vendor = models.ForeignKey(
        'slas.Vendor',
        on_delete=models.CASCADE,
        related_name='risk_assessments'
    )
    assessment_date = models.DateField()
    assessor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conducted_risk_assessments'
    )
    risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Risk score (0-100)"
    )
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    assessment_factors = models.JSONField(default=dict)
    mitigation_actions = models.JSONField(default=list)
    next_assessment_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Vendor Risk Assessment')
        verbose_name_plural = _('Vendor Risk Assessments')
        ordering = ['-assessment_date']
    
    def __str__(self):
        return f"{self.vendor.name} - {self.assessment_date}"


class VendorDocument(BaseModel):
    """Vendor documents."""
    vendor = models.ForeignKey(
        'slas.Vendor',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('contract', 'Contract'),
            ('certificate', 'Certificate'),
            ('insurance', 'Insurance'),
            ('financial', 'Financial Statement'),
            ('compliance', 'Compliance Document'),
            ('other', 'Other'),
        ]
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_upload = models.FileField(upload_to='vendor_documents/')
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    expiry_date = models.DateField(null=True, blank=True)
    is_required = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Vendor Document')
        verbose_name_plural = _('Vendor Documents')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.vendor.name} - {self.title}"


class VendorContact(BaseModel):
    """Vendor contacts."""
    vendor = models.ForeignKey(
        'slas.Vendor',
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    contact_type = models.CharField(
        max_length=50,
        choices=[
            ('primary', 'Primary'),
            ('technical', 'Technical'),
            ('billing', 'Billing'),
            ('emergency', 'Emergency'),
            ('other', 'Other'),
        ]
    )
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Vendor Contact')
        verbose_name_plural = _('Vendor Contacts')
        ordering = ['vendor', 'contact_type', 'name']
    
    def __str__(self):
        return f"{self.vendor.name} - {self.name}"
    
    @property
    def email_plain(self):
        """Get decrypted email address"""
        from tprm_backend.utils.data_encryption import decrypt_data
        return decrypt_data(self.email) if self.email else None
    
    @property
    def phone_plain(self):
        """Get decrypted phone number"""
        from tprm_backend.utils.data_encryption import decrypt_data
        return decrypt_data(self.phone) if self.phone else None
    
    @property
    def mobile_plain(self):
        """Get decrypted mobile number"""
        from tprm_backend.utils.data_encryption import decrypt_data
        return decrypt_data(self.mobile) if self.mobile else None


class VendorFinancial(BaseModel):
    """Vendor financial information."""
    vendor = models.ForeignKey(
        'slas.Vendor',
        on_delete=models.CASCADE,
        related_name='financial_records'
    )
    fiscal_year = models.PositiveIntegerField()
    revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    profit_margin = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    credit_rating = models.CharField(max_length=10, blank=True)
    financial_strength = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
        ],
        blank=True
    )
    last_updated = models.DateField()
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Vendor Financial')
        verbose_name_plural = _('Vendor Financial Records')
        ordering = ['vendor', '-fiscal_year']
    
    def __str__(self):
        return f"{self.vendor.name} - FY{self.fiscal_year}"


class VendorPerformance(BaseModel):
    """Vendor performance summary."""
    vendor = models.ForeignKey(
        'slas.Vendor',
        on_delete=models.CASCADE,
        related_name='performance_summaries'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Overall performance score (0-100)"
    )
    sla_compliance_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="SLA compliance rate (0-100)"
    )
    response_time_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Response time score (0-100)"
    )
    quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Quality score (0-100)"
    )
    cost_effectiveness_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Cost effectiveness score (0-100)"
    )
    violations_count = models.PositiveIntegerField(default=0)
    incidents_count = models.PositiveIntegerField(default=0)
    performance_data = models.JSONField(default=dict)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Vendor Performance')
        verbose_name_plural = _('Vendor Performance Summaries')
        ordering = ['vendor', '-period_end']
    
    def __str__(self):
        return f"{self.vendor.name} - {self.period_end}"


class VendorIncident(BaseModel):
    """Vendor incidents."""
    vendor = models.ForeignKey(
        'slas.Vendor',
        on_delete=models.CASCADE,
        related_name='incidents'
    )
    incident_type = models.CharField(
        max_length=50,
        choices=[
            ('service_outage', 'Service Outage'),
            ('security_breach', 'Security Breach'),
            ('data_loss', 'Data Loss'),
            ('performance_degradation', 'Performance Degradation'),
            ('compliance_violation', 'Compliance Violation'),
            ('other', 'Other'),
        ]
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    incident_date = models.DateTimeField()
    detected_date = models.DateTimeField()
    resolved_date = models.DateTimeField(null=True, blank=True)
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
    impact_assessment = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents'
    )
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Vendor Incident')
        verbose_name_plural = _('Vendor Incidents')
        ordering = ['-incident_date']
    
    def __str__(self):
        return f"{self.vendor.name} - {self.title}"
