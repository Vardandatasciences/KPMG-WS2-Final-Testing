"""
Vendor Core Models - Maps to existing database tables
"""

from django.db import models
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin


class VendorBaseModel(TPRMEncryptedFieldsMixin, models.Model):
    """Base model for all vendor tables - unmanaged with encryption support"""
    
    class Meta:
        abstract = True
        managed = False  # Don't let Django manage these tables


class Users(VendorBaseModel):
    """User model mapping to existing users table"""
    
    userid = models.AutoField(db_column='UserId', primary_key=True)
    username = models.CharField(db_column='UserName', max_length=255)
    password = models.CharField(db_column='Password', max_length=255)
    createdat = models.DateTimeField(db_column='CreatedAt', blank=True, null=True)
    updatedat = models.DateTimeField(db_column='UpdatedAt', blank=True, null=True)
    email = models.CharField(db_column='Email', max_length=100, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.username


class VendorCategories(VendorBaseModel):
    """Vendor categories mapping to existing vendor_categories table"""
    
    category_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor category to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_categories', null=True, blank=True,
                               help_text="Tenant this vendor category belongs to")
    
    category_name = models.CharField(max_length=100)
    category_code = models.CharField(unique=True, max_length=20)
    description = models.TextField(blank=True, null=True)
    risk_weight = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    assessment_frequency_months = models.IntegerField(blank=True, null=True)
    approval_required = models.IntegerField(blank=True, null=True)
    criticality_level = models.CharField(max_length=8, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_categories'
        verbose_name = 'Vendor Category'
        verbose_name_plural = 'Vendor Categories'
    
    def __str__(self):
        return self.category_name


class Vendors(VendorBaseModel):
    """Main vendors table mapping"""
    
    vendor_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_core_vendors', null=True, blank=True,
                               help_text="Tenant this vendor belongs to")
    
    vendor_code = models.CharField(unique=True, max_length=50)
    company_name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    business_type = models.CharField(max_length=100, blank=True, null=True)
    incorporation_date = models.DateField(blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    duns_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    industry_sector = models.CharField(max_length=100, blank=True, null=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    employee_count = models.IntegerField(blank=True, null=True)
    headquarters_country = models.CharField(max_length=100, blank=True, null=True)
    headquarters_address = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    vendor_category = models.ForeignKey(VendorCategories, models.DO_NOTHING, blank=True, null=True)
    risk_level = models.CharField(max_length=8, blank=True, null=True)
    status = models.CharField(max_length=10, blank=True, null=True)
    lifecycle_stage = models.CharField(max_length=50, blank=True, null=True)
    onboarding_date = models.DateField(blank=True, null=True)
    last_assessment_date = models.DateField(blank=True, null=True)
    next_assessment_date = models.DateField(blank=True, null=True)
    is_critical_vendor = models.IntegerField(blank=True, null=True)
    has_data_access = models.IntegerField(blank=True, null=True)
    has_system_access = models.IntegerField(blank=True, null=True)
    created_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    updated_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='updated_by', related_name='vendors_updated_by_set', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry', help_text="Data retention expiry date")
    
    class Meta:
        managed = False
        db_table = 'vendors'
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
    
    def __str__(self):
        return self.company_name


class VendorContacts(VendorBaseModel):
    """Vendor contacts mapping to existing vendor_contacts table"""
    
    contact_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor contact to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_core_contacts', null=True, blank=True,
                               help_text="Tenant this vendor contact belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING)
    contact_type = models.CharField(max_length=9, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    mobile = models.CharField(max_length=50, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    is_primary = models.IntegerField(blank=True, null=True)
    is_active = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_contacts'
        verbose_name = 'Vendor Contact'
        verbose_name_plural = 'Vendor Contacts'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.vendor.company_name}"


class VendorDocuments(VendorBaseModel):
    """Vendor documents mapping to existing vendor_documents table"""
    
    document_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor document to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_core_documents', null=True, blank=True,
                               help_text="Tenant this vendor document belongs to")
    
    vendor = models.ForeignKey(Vendors, models.DO_NOTHING)
    document_type = models.CharField(max_length=13, blank=True, null=True)
    document_name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_path = models.CharField(max_length=500, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    document_category = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    version_number = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=8, blank=True, null=True)
    uploaded_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='uploaded_by', blank=True, null=True)
    approved_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='approved_by', related_name='vendordocuments_approved_by_set', blank=True, null=True)
    upload_date = models.DateTimeField(blank=True, null=True)
    approval_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'vendor_documents'
        verbose_name = 'Vendor Document'
        verbose_name_plural = 'Vendor Documents'
    
    def __str__(self):
        return f"{self.document_name} - {self.vendor.company_name}"


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


class TempVendor(VendorBaseModel):
    """Temporary vendor model mapping to temp_vendor table for registration"""
    
    id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link temp vendor to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='temp_vendors', null=True, blank=True,
                               help_text="Tenant this temp vendor belongs to")
    
    userid = models.IntegerField(db_column='UserId', blank=True, null=True)
    vendor_code = models.CharField(max_length=50, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    lifecycle_stage = models.BigIntegerField(blank=True, null=True)
    business_type = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    duns_number = models.CharField(max_length=50, blank=True, null=True)
    incorporation_date = models.DateField(blank=True, null=True)
    industry_sector = models.CharField(max_length=100, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    annual_revenue = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    employee_count = models.IntegerField(blank=True, null=True)
    headquarters_address = models.TextField(blank=True, null=True)
    vendor_category = models.CharField(max_length=100, blank=True, null=True)
    risk_level = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    is_critical_vendor = models.BooleanField(default=False)
    has_data_access = models.BooleanField(default=False)
    has_system_access = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    contacts = models.JSONField(blank=True, null=True)
    documents = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    response_id = models.BigIntegerField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'temp_vendor'
        verbose_name = 'Temporary Vendor'
        verbose_name_plural = 'Temporary Vendors'

    def save(self, *args, **kwargs):
        # Use default database (which is configured to use tprm_integration)
        kwargs['using'] = 'default'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.company_name or f"Temp Vendor {self.id}"


class ExternalScreeningResult(VendorBaseModel):
    """External screening results mapping to external_screening_results table"""
    
    SCREENING_TYPES = [
        ('WORLDCHECK', 'WorldCheck'),
        ('OFAC', 'OFAC'),
        ('PEP', 'PEP Database'),
        ('SANCTIONS', 'Sanctions'),
        ('ADVERSE_MEDIA', 'Adverse Media'),
    ]
    
    STATUS_CHOICES = [
        ('CLEAR', 'Clear'),
        ('POTENTIAL_MATCH', 'Potential Match'),
        ('CONFIRMED_MATCH', 'Confirmed Match'),
        ('UNDER_REVIEW', 'Under Review'),
    ]

    screening_id = models.BigAutoField(primary_key=True)
    vendor_id = models.BigIntegerField()
    screening_type = models.CharField(max_length=20, choices=SCREENING_TYPES)
    screening_date = models.DateTimeField(auto_now_add=True)
    search_terms = models.JSONField(blank=True, null=True)
    total_matches = models.IntegerField(default=0)
    high_risk_matches = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNDER_REVIEW')
    last_updated = models.DateTimeField(auto_now=True)
    reviewed_by = models.IntegerField(blank=True, null=True)
    review_date = models.DateTimeField(blank=True, null=True)
    review_comments = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'external_screening_results'
        verbose_name = 'External Screening Result'
        verbose_name_plural = 'External Screening Results'

    @property
    def vendor(self):
        """Get the associated temp vendor"""
        try:
            return TempVendor.objects.get(id=self.vendor_id)
        except TempVendor.DoesNotExist:
            return None
    
    def __str__(self):
        vendor = self.vendor
        vendor_name = vendor.company_name if vendor else f"Vendor {self.vendor_id}"
        return f"{vendor_name} - {self.screening_type} ({self.status})"


class ScreeningMatch(VendorBaseModel):
    """Screening matches mapping to screening_matches table"""
    
    RESOLUTION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CLEARED', 'Cleared'),
        ('ESCALATED', 'Escalated'),
        ('BLOCKED', 'Blocked'),
    ]

    match_id = models.BigAutoField(primary_key=True)
    screening = models.ForeignKey(ExternalScreeningResult, on_delete=models.CASCADE, 
                                 related_name='matches', db_column='screening_id')
    match_type = models.CharField(max_length=100)
    match_score = models.DecimalField(max_digits=5, decimal_places=2)
    match_details = models.JSONField()
    is_false_positive = models.BooleanField(default=False)
    resolution_status = models.CharField(max_length=20, choices=RESOLUTION_STATUS_CHOICES, default='PENDING')
    resolution_notes = models.TextField(blank=True, null=True)
    resolved_by = models.IntegerField(blank=True, null=True)
    resolved_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'screening_matches'
        verbose_name = 'Screening Match'
        verbose_name_plural = 'Screening Matches'

    def __str__(self):
        return f"{self.match_type} - Score: {self.match_score} ({self.resolution_status})"


class LifecycleTracker(VendorBaseModel):
    """Lifecycle tracker mapping to lifecycle_tracker table"""
    
    id = models.AutoField(primary_key=True)
    vendor_id = models.BigIntegerField()
    lifecycle_stage = models.BigIntegerField()
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'lifecycle_tracker'
        verbose_name = 'Lifecycle Tracker'
        verbose_name_plural = 'Lifecycle Tracker'
    
    def __str__(self):
        return f"Vendor {self.vendor_id} - Stage {self.lifecycle_stage}"


class S3Files(VendorBaseModel):
    """S3 files mapping to s3_files table for document storage"""
    
    id = models.AutoField(primary_key=True)
    url = models.TextField()
    file_type = models.CharField(max_length=50)
    file_name = models.CharField(max_length=255)
    user_id = models.CharField(max_length=100)
    metadata = models.JSONField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 's3_files'
        verbose_name = 'S3 File'
        verbose_name_plural = 'S3 Files'
    
    def __str__(self):
        return f"{self.file_name} ({self.file_type})"
