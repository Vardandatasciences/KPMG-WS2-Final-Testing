"""
Vendor Lifecycle Models - Maps to existing database tables
"""

from django.db import models
from tprm_backend.apps.vendor_core.models import VendorBaseModel, Vendors, Users, VendorLifecycleStages


class VendorApprovals(VendorBaseModel):
    """Vendor approvals mapping to existing vendor_approvals table"""
    
    approval_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor approval to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_lifecycle_approvals', null=True, blank=True,
                               help_text="Tenant this vendor approval belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING)
    stage = models.ForeignKey(VendorLifecycleStages, models.DO_NOTHING)
    approver = models.ForeignKey(Users, models.DO_NOTHING)
    approval_status = models.CharField(max_length=9, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    conditions = models.TextField(blank=True, null=True)
    approval_date = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    escalated_to = models.ForeignKey(Users, models.DO_NOTHING, db_column='escalated_to', related_name='vendorapprovals_escalated_to_set', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_approvals'
        verbose_name = 'Vendor Approval'
        verbose_name_plural = 'Vendor Approvals'
    
    def __str__(self):
        return f"{self.vendor.company_name} - {self.stage.stage_name} - {self.approval_status}"


class VendorStatusHistory(VendorBaseModel):
    """Vendor status history mapping to existing vendor_status_history table"""
    
    history_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor status history to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_status_histories', null=True, blank=True,
                               help_text="Tenant this vendor status history belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING)
    old_status = models.CharField(max_length=50, blank=True, null=True)
    new_status = models.CharField(max_length=50, blank=True, null=True)
    old_stage = models.CharField(max_length=50, blank=True, null=True)
    new_stage = models.CharField(max_length=50, blank=True, null=True)
    changed_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='changed_by')
    change_reason = models.CharField(max_length=255, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    change_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_status_history'
        verbose_name = 'Vendor Status History'
        verbose_name_plural = 'Vendor Status History'
    
    def __str__(self):
        return f"{self.vendor.company_name} - {self.old_status} to {self.new_status}"


class VendorContracts(VendorBaseModel):
    """Vendor contracts mapping to existing vendor_contracts table"""
    
    contract_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor contract to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_lifecycle_contracts', null=True, blank=True,
                               help_text="Tenant this vendor contract belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING)
    contract_number = models.CharField(unique=True, max_length=100)
    contract_title = models.CharField(max_length=255)
    contract_type = models.CharField(max_length=17, blank=True, null=True)
    parent_contract = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    contract_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    renewal_terms = models.TextField(blank=True, null=True)
    auto_renewal = models.IntegerField(blank=True, null=True)
    notice_period_days = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=17, blank=True, null=True)
    contract_owner = models.ForeignKey(Users, models.DO_NOTHING, db_column='contract_owner', blank=True, null=True)
    legal_reviewer = models.ForeignKey(Users, models.DO_NOTHING, db_column='legal_reviewer', related_name='vendorcontracts_legal_reviewer_set', blank=True, null=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_contracts'
        verbose_name = 'Vendor Contract'
        verbose_name_plural = 'Vendor Contracts'
    
    def __str__(self):
        return f"{self.contract_number} - {self.vendor.company_name}"


class VendorSlas(VendorBaseModel):
    """Vendor SLAs mapping to existing vendor_slas table"""
    
    sla_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor SLA to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_lifecycle_slas', null=True, blank=True,
                               help_text="Tenant this vendor SLA belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING)
    contract_id = models.BigIntegerField(blank=True, null=True)
    sla_name = models.CharField(max_length=255)
    sla_type = models.CharField(max_length=15, blank=True, null=True)
    metric_name = models.CharField(max_length=255, blank=True, null=True)
    target_value = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    measurement_unit = models.CharField(max_length=50, blank=True, null=True)
    measurement_frequency = models.CharField(max_length=9, blank=True, null=True)
    penalty_clause = models.TextField(blank=True, null=True)
    effective_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=8, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_slas'
        verbose_name = 'Vendor SLA'
        verbose_name_plural = 'Vendor SLAs'
    
    def __str__(self):
        return f"{self.sla_name} - {self.vendor.company_name}"


class VendorLifecycleStages(VendorBaseModel):
    """Vendor lifecycle stages mapping to existing vendor_lifecycle_stages table"""
    
    stage_id = models.BigAutoField(primary_key=True)
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
