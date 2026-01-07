"""
Vendor Risk Assessment Models - Maps to existing database tables
"""

from django.db import models
from tprm_backend.apps.vendor_core.models import VendorBaseModel, Vendors, Users, VendorCategories


class VendorRiskAssessments(VendorBaseModel):
    """Vendor risk assessments mapping to existing vendor_risk_assessments table"""
    
    assessment_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link risk assessment to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_risk_assessments', null=True, blank=True,
                               help_text="Tenant this risk assessment belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING)
    riskid = models.IntegerField(db_column='RiskId', blank=True, null=True)  # Reference to risk table
    assessment_type = models.CharField(max_length=15, blank=True, null=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    financial_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    operational_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cybersecurity_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    reputational_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    concentration_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    assessment_date = models.DateField(blank=True, null=True)
    assessed_by = models.IntegerField(blank=True, null=True)  # User ID
    next_assessment_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=9, blank=True, null=True)
    methodology_version = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_risk_assessments'
        verbose_name = 'Vendor Risk Assessment'
        verbose_name_plural = 'Vendor Risk Assessments'
    
    def __str__(self):
        return f"Risk Assessment - {self.vendor.company_name} ({self.overall_score})"


class VendorRiskFactors(VendorBaseModel):
    """Vendor risk factors mapping to existing vendor_risk_factors table"""
    
    factor_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link risk factor to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_risk_factors', null=True, blank=True,
                               help_text="Tenant this risk factor belongs to")
    
    assessment = models.ForeignKey(VendorRiskAssessments, models.DO_NOTHING)
    risk_category = models.CharField(max_length=13, blank=True, null=True)
    risk_factor = models.CharField(max_length=255, blank=True, null=True)
    risk_description = models.TextField(blank=True, null=True)
    likelihood = models.CharField(max_length=9, blank=True, null=True)
    impact = models.CharField(max_length=9, blank=True, null=True)
    inherent_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    control_effectiveness = models.CharField(max_length=8, blank=True, null=True)
    residual_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    mitigation_plan = models.TextField(blank=True, null=True)
    evidence_file = models.CharField(max_length=500, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_risk_factors'
        verbose_name = 'Vendor Risk Factor'
        verbose_name_plural = 'Vendor Risk Factors'
    
    def __str__(self):
        return f"{self.risk_factor} - {self.assessment.vendor.company_name}"


class VendorRiskThresholds(VendorBaseModel):
    """Vendor risk thresholds mapping to existing vendor_risk_thresholds table"""
    
    threshold_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link risk threshold to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_risk_thresholds', null=True, blank=True,
                               help_text="Tenant this risk threshold belongs to")
    
    vendor_category = models.ForeignKey(VendorCategories, models.DO_NOTHING, blank=True, null=True)
    risk_type = models.CharField(max_length=13, blank=True, null=True)
    low_threshold = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    medium_threshold = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    high_threshold = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    critical_threshold = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    action_required = models.TextField(blank=True, null=True)
    escalation_level = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_risk_thresholds'
        verbose_name = 'Vendor Risk Threshold'
        verbose_name_plural = 'Vendor Risk Thresholds'
    
    def __str__(self):
        return f"Risk Threshold - {self.vendor_category.category_name if self.vendor_category else 'Global'} - {self.risk_type}"


class RiskTPRM(VendorBaseModel):
    """Risk TPRM model mapping to existing risk_tprm table"""
    
    id = models.AutoField(primary_key=True)
    
    # MULTI-TENANCY: Link risk to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='risk_tprm', null=True, blank=True,
                               help_text="Tenant this risk belongs to")
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    likelihood = models.IntegerField()
    impact = models.IntegerField()
    score = models.FloatField()
    priority = models.CharField(max_length=20)
    ai_explanation = models.TextField(blank=True, null=True)
    suggested_mitigations = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20)
    exposure_rating = models.IntegerField(default=3)
    risk_type = models.CharField(max_length=20)
    entity = models.CharField(max_length=50)
    data = models.JSONField(blank=True, null=True)
    row = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'risk_tprm'
        verbose_name = 'Risk TPRM'
        verbose_name_plural = 'Risk TPRM'

    def __str__(self):
        return f"{self.title} - {self.priority}"


class VendorLifecycleStages(VendorBaseModel):
    """Vendor lifecycle stages mapping to existing vendor_lifecycle_stages table"""
    
    stage_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link lifecycle stage to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_lifecycle_stages', null=True, blank=True,
                               help_text="Tenant this lifecycle stage belongs to")
    
    stage_name = models.CharField(max_length=100)
    stage_code = models.CharField(unique=True, max_length=20)
    stage_order = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    approval_required = models.BooleanField(blank=True, null=True)
    max_duration_days = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_lifecycle_stages'
        verbose_name = 'Vendor Lifecycle Stage'
        verbose_name_plural = 'Vendor Lifecycle Stages'
    
    def __str__(self):
        return self.stage_name
