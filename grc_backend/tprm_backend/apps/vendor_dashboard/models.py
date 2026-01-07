"""
Vendor Dashboard Models - Maps to existing database tables
"""

from django.db import models
from tprm_backend.apps.vendor_core.models import VendorBaseModel, Vendors, Users


class VendorNotifications(VendorBaseModel):
    """Vendor notifications mapping to existing vendor_notifications table"""
    
    notification_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor notification to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_notifications', null=True, blank=True,
                               help_text="Tenant this vendor notification belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING, blank=True, null=True)
    notification_type = models.CharField(max_length=17, blank=True, null=True)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    severity = models.CharField(max_length=8, blank=True, null=True)
    recipient_user = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    recipient_role = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=12, blank=True, null=True)
    scheduled_date = models.DateTimeField(blank=True, null=True)
    sent_date = models.DateTimeField(blank=True, null=True)
    read_date = models.DateTimeField(blank=True, null=True)
    acknowledged_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_notifications'
        verbose_name = 'Vendor Notification'
        verbose_name_plural = 'Vendor Notifications'
    
    def __str__(self):
        vendor_name = self.vendor.company_name if self.vendor else "System"
        return f"{self.title} - {vendor_name}"


class VendorAuditLog(VendorBaseModel):
    """Vendor audit log mapping to existing vendor_audit_log table"""
    
    log_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor audit log to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_audit_logs', null=True, blank=True,
                               help_text="Tenant this vendor audit log belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING, blank=True, null=True)
    table_name = models.CharField(max_length=100, blank=True, null=True)
    record_id = models.BigIntegerField(blank=True, null=True)
    action = models.CharField(max_length=7, blank=True, null=True)
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    user = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_audit_log'
        verbose_name = 'Vendor Audit Log'
        verbose_name_plural = 'Vendor Audit Logs'
    
    def __str__(self):
        vendor_name = self.vendor.company_name if self.vendor else "System"
        return f"{self.action} on {self.table_name} - {vendor_name}"


class VendorBcpPlans(VendorBaseModel):
    """Vendor BCP plans mapping to existing vendor_bcp_plans table"""
    
    plan_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor BCP plan to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_bcp_plans', null=True, blank=True,
                               help_text="Tenant this vendor BCP plan belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING)
    plan_name = models.CharField(max_length=255)
    plan_type = models.CharField(max_length=19, blank=True, null=True)
    version = models.CharField(max_length=20, blank=True, null=True)
    plan_document_path = models.CharField(max_length=500, blank=True, null=True)
    last_updated_date = models.DateField(blank=True, null=True)
    next_review_date = models.DateField(blank=True, null=True)
    approval_status = models.CharField(max_length=8, blank=True, null=True)
    approved_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='approved_by', blank=True, null=True)
    approval_date = models.DateField(blank=True, null=True)
    effectiveness_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    compliance_status = models.CharField(max_length=19, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_bcp_plans'
        verbose_name = 'Vendor BCP Plan'
        verbose_name_plural = 'Vendor BCP Plans'
    
    def __str__(self):
        return f"{self.plan_name} - {self.vendor.company_name}"


class VendorScreeningMatches(VendorBaseModel):
    """Vendor screening matches mapping to existing vendor_screening_matches table"""
    
    match_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor screening match to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_screening_matches', null=True, blank=True,
                               help_text="Tenant this vendor screening match belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING)
    screening_type = models.CharField(max_length=20)  # OFAC, PEP, Sanctions
    match_status = models.CharField(max_length=20)  # PENDING, CONFIRMED, FALSE_POSITIVE
    match_details = models.JSONField(blank=True, null=True)
    resolution_status = models.CharField(max_length=20, blank=True, null=True)  # PENDING, ESCALATED, BLOCKED
    is_false_positive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_screening_matches'
        verbose_name = 'Vendor Screening Match'
        verbose_name_plural = 'Vendor Screening Matches'
    
    def __str__(self):
        return f"{self.vendor.company_name} - {self.screening_type} Match"


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
