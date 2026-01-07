"""
Audit models for Vendor Guard Hub matching MySQL schema.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from tprm_backend.slas.models import VendorSLA, SLAMetric
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin


class Audit(TPRMEncryptedFieldsMixin, models.Model):
    """Audit model matching MySQL schema."""
    audit_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link audit to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='audits', null=True, blank=True,
                               help_text="Tenant this audit belongs to")
    
    title = models.CharField(max_length=255)
    scope = models.TextField(blank=True, null=True)
    assignee_id = models.IntegerField(blank=True, null=True)
    auditor_id = models.IntegerField(blank=True, null=True)
    assign_date = models.DateField(blank=True, null=True)
    due_date = models.DateField()
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ],
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('created', 'Created'),
            ('in_progress', 'In Progress'),
            ('under_review', 'Under Review'),
            ('completed', 'Completed'),
            ('rejected', 'Rejected'),
        ],
        default='created'
    )
    completion_date = models.DateField(blank=True, null=True)
    reviewer_id = models.IntegerField(blank=True, null=True)
    metric_id = models.IntegerField(blank=True, null=True)
    sla = models.ForeignKey(
        VendorSLA,
        on_delete=models.CASCADE,
        related_name='audits',
        db_column='sla_id',
        blank=True,
        null=True
    )
    review_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    review_comments = models.TextField(blank=True, null=True)
    audit_type = models.CharField(
        max_length=20,
        choices=[
            ('internal', 'Internal'),
            ('external', 'External'),
            ('self', 'Self Assessment'),
        ],
        blank=True,
        null=True
    )
    evidence_comments = models.TextField(blank=True, null=True)
    review_start_date = models.DateField(blank=True, null=True)
    review_date = models.DateField(blank=True, null=True)
    reports_objective = models.TextField(blank=True, null=True)
    business_unit = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=100, blank=True, null=True)
    responsibility = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Audit')
        verbose_name_plural = _('Audits')
        ordering = ['-created_at']
        db_table = 'audits'
        managed = True
    
    def __str__(self):
        return f"{self.title} - {self.status}"


class StaticQuestionnaire(TPRMEncryptedFieldsMixin, models.Model):
    """Static questionnaires matching tprm_db schema."""
    question_id = models.AutoField(primary_key=True)
    
    # MULTI-TENANCY: Link static questionnaire to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='static_questionnaires', null=True, blank=True,
                               help_text="Tenant this static questionnaire belongs to")
    
    metric_name = models.CharField(max_length=255)
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Text'),
            ('number', 'Number'),
            ('boolean', 'Yes/No'),
            ('multiple_choice', 'Multiple Choice'),
        ]
    )
    is_required = models.BooleanField(default=False)
    scoring_weightings = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Static Questionnaire')
        verbose_name_plural = _('Static Questionnaires')
        ordering = ['question_id']
        db_table = 'static_questionnaires'
    
    def __str__(self):
        return f"{self.question_text[:50]}..."


class AuditVersion(TPRMEncryptedFieldsMixin, models.Model):
    """Audit versions matching tprm_db schema."""
    version_id = models.AutoField(primary_key=True)
    
    # MULTI-TENANCY: Link audit version to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='audit_versions', null=True, blank=True,
                               help_text="Tenant this audit version belongs to")
    
    audit_id = models.IntegerField()
    version_type = models.CharField(
        max_length=1,
        choices=[
            ('A', 'Audit'),
            ('R', 'Review'),
        ]
    )
    version_number = models.IntegerField()
    extended_information = models.JSONField(blank=True, null=True)
    user_id = models.IntegerField()
    approval_status = models.CharField(
        max_length=20,
        choices=[
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('pending', 'Pending'),
        ]
    )
    date_created = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Audit Version')
        verbose_name_plural = _('Audit Versions')
        ordering = ['-created_at']
        db_table = 'audit_versions'
    
    def __str__(self):
        return f"Version {self.version_number} - {self.audit_id}"


class AuditFinding(TPRMEncryptedFieldsMixin, models.Model):
    """Audit findings matching tprm_db schema."""
    audit_finding_id = models.AutoField(primary_key=True)
    
    # MULTI-TENANCY: Link audit finding to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='audit_findings', null=True, blank=True,
                               help_text="Tenant this audit finding belongs to")
    
    audit_id = models.IntegerField()
    metrics_id = models.IntegerField()
    evidence = models.TextField()
    user_id = models.IntegerField()
    how_to_verify = models.TextField()
    impact_recommendations = models.TextField()
    details_of_finding = models.TextField()
    comment = models.TextField(blank=True, null=True)
    check_date = models.DateField()
    questionnaire_responses = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Audit Finding')
        verbose_name_plural = _('Audit Findings')
        ordering = ['-created_at']
        db_table = 'audit_findings'
    
    def __str__(self):
        return f"Finding for Audit {self.audit_id}"


class AuditReport(TPRMEncryptedFieldsMixin, models.Model):
    """Audit reports matching tprm_db schema."""
    report_id = models.AutoField(primary_key=True)
    
    # MULTI-TENANCY: Link audit report to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='audit_reports', null=True, blank=True,
                               help_text="Tenant this audit report belongs to")
    
    audit_id = models.IntegerField()
    report_link = models.CharField(max_length=500)  # S3 bucket link
    sla_id = models.IntegerField()
    metrics_id = models.IntegerField()
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Audit Report')
        verbose_name_plural = _('Audit Reports')
        ordering = ['-generated_at']
        db_table = 'audit_reports'
    
    def __str__(self):
        return f"Report for Audit {self.audit_id}"
