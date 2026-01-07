from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin


class Vendor(TPRMEncryptedFieldsMixin, models.Model):
    """Vendor model for managing vendor information"""
    
    VENDOR_CATEGORIES = [
        ('technology', 'Technology'),
        ('consulting', 'Consulting'),
        ('manufacturing', 'Manufacturing'),
        ('services', 'Services'),
        ('logistics', 'Logistics'),
        ('other', 'Other'),
    ]
    
    RISK_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('IN_REVIEW', 'In Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
        ('TERMINATED', 'Terminated'),
    ]
    
    DATA_CLASSIFICATION = [
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ]
    
    BUSINESS_CRITICALITY = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    VENDOR_SIZE = [
        ('micro', 'Micro'),
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('enterprise', 'Enterprise'),
    ]
    
    # Basic Information
    vendor_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='contract_vendors', null=True, blank=True,
                               help_text="Tenant this vendor belongs to")
    
    vendor_code = models.CharField(max_length=50, help_text="Unique vendor identifier")
    company_name = models.CharField(max_length=255, help_text="Display name of the company")
    legal_name = models.CharField(max_length=255, blank=True, null=True, help_text="Legal registered name")
    business_type = models.CharField(max_length=100, blank=True, null=True)
    incorporation_date = models.DateField(blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    duns_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)  # Using CharField instead of URLField
    industry_sector = models.CharField(max_length=100, blank=True, null=True)
    
    # Financial Information
    annual_revenue = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)]
    )
    employee_count = models.PositiveIntegerField(blank=True, null=True)
    
    # Location Information
    headquarters_country = models.CharField(max_length=100, blank=True, null=True)
    headquarters_address = models.TextField(blank=True, null=True)
    geographic_presence = models.JSONField(default=dict, blank=True)
    
    # Business Information
    description = models.TextField(blank=True, null=True)
    vendor_category_id = models.BigIntegerField(blank=True, null=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='LOW')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    lifecycle_stage = models.CharField(max_length=50, blank=True, null=True)
    
    # Assessment Information
    onboarding_date = models.DateField(blank=True, null=True)
    last_assessment_date = models.DateField(blank=True, null=True)
    next_assessment_date = models.DateField(blank=True, null=True)
    
    # Access and Security
    is_critical_vendor = models.BooleanField(default=False)
    has_data_access = models.BooleanField(default=False)
    has_system_access = models.BooleanField(default=False)
    data_classification_handled = models.CharField(
        max_length=20, 
        choices=DATA_CLASSIFICATION, 
        default='public'
    )
    business_criticality = models.CharField(
        max_length=10, 
        choices=BUSINESS_CRITICALITY, 
        default='low'
    )
    
    # Vendor Classification
    vendor_size_category = models.CharField(
        max_length=20, 
        choices=VENDOR_SIZE, 
        default='small'
    )
    preferred_vendor_flag = models.BooleanField(default=False)
    diversity_certification = models.JSONField(default=dict, blank=True)
    sustainability_rating = models.CharField(max_length=20, blank=True, null=True)
    
    # Relationships
    parent_vendor_id = models.BigIntegerField(blank=True, null=True)
    vendor_tier_id = models.BigIntegerField(blank=True, null=True)
    
    # Data Inventory
    data_inventory = models.JSONField(null=True, blank=True, help_text="JSON mapping vendor field labels to data types (personal, confidential, regular)")
    
    # Audit Fields - using IntegerField to match existing database schema
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendors'
        managed = False  # Don't let Django manage this table since it already exists
        ordering = ['company_name']
    
    def __str__(self):
        return f"{self.company_name} ({self.vendor_code})"
    
    def get_geographic_presence_display(self):
        """Return formatted geographic presence"""
        if isinstance(self.geographic_presence, dict):
            return ', '.join(self.geographic_presence.get('countries', []))
        return ''
    
    def get_diversity_certifications_display(self):
        """Return formatted diversity certifications"""
        if isinstance(self.diversity_certification, dict):
            return ', '.join(self.diversity_certification.get('certifications', []))
        return ''
    
    def get_primary_contact(self):
        """Get the primary contact for this vendor"""
        try:
            return VendorContact.objects.filter(vendor_id=self.vendor_id, is_primary=True, is_active=True).first()
        except VendorContact.DoesNotExist:
            return None
    
    def get_active_contacts(self):
        """Get all active contacts for this vendor"""
        return VendorContact.objects.filter(vendor_id=self.vendor_id, is_active=True).order_by('is_primary', 'contact_type', 'last_name')


class VendorContract(models.Model):
    """Contract model for managing vendor contracts"""
    
    CONTRACT_TYPES = [
        ('MASTER_AGREEMENT', 'Master Agreement'),
        ('SOW', 'Statement of Work'),
        ('PURCHASE_ORDER', 'Purchase Order'),
        ('SERVICE_AGREEMENT', 'Service Agreement'),
        ('LICENSE', 'License'),
        ('NDA', 'Non-Disclosure Agreement'),
    ]
    
    CONTRACT_KINDS = [
        ('MAIN', 'Main Contract'),
        ('SUBCONTRACT', 'Subcontract'),
        ('AMENDMENT', 'Amendment'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('UNDER_NEGOTIATION', 'Under Negotiation'),
        ('PENDING_ASSIGNMENT', 'Pending Assignment'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('TERMINATED', 'Terminated'),
    ]
    
    CONTRACT_CATEGORIES = [
        ('goods', 'Goods'),
        ('services', 'Services'),
        ('technology', 'Technology'),
        ('consulting', 'Consulting'),
        ('maintenance', 'Maintenance'),
        ('licensing', 'Licensing'),
        ('others', 'Others'),
    ]
    
    TERMINATION_CLAUSE_TYPES = [
        ('convenience', 'Convenience'),
        ('cause', 'For Cause'),
        ('both', 'Both'),
        ('none', 'None'),
    ]
    
    DISPUTE_RESOLUTION_METHODS = [
        ('negotiation', 'Negotiation'),
        ('mediation', 'Mediation'),
        ('arbitration', 'Arbitration'),
        ('litigation', 'Litigation'),
    ]
    
    WORKFLOW_STAGES = [
        ('draft', 'Draft'),
        ('pending_assignment', 'Pending Assignment'),
        ('under_review', 'Under Review'),
        ('approval_pending', 'Approval Pending'),
        ('approved', 'Approved'),
        ('executed', 'Executed'),
        ('active', 'Active'),
        ('terminated', 'Terminated'),
        ('archived', 'Archived'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    COMPLIANCE_STATUS = [
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('under_review', 'Under Review'),
        ('exempt', 'Exempt'),
    ]
    
    ARCHIVE_REASONS = [
        ('CONTRACT_EXPIRED', 'Contract Expired'),
        ('EARLY_TERMINATION', 'Early Termination'),
        ('PROJECT_COMPLETED', 'Project Completed'),
        ('MUTUAL_AGREEMENT', 'Mutual Agreement'),
        ('BREACH', 'Breach of Contract'),
        ('OTHER', 'Other'),
    ]
    
    # Basic Contract Information
    contract_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor contract to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='vendor_contracts', null=True, blank=True,
                               help_text="Tenant this vendor contract belongs to")
    
    vendor = models.ForeignKey(
        Vendor, 
        on_delete=models.CASCADE, 
        related_name='contracts',
        help_text="Associated vendor"
    )
    contract_number = models.CharField(max_length=100, unique=True, help_text="Unique contract number")
    contract_title = models.CharField(max_length=255, help_text="Contract title")
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES, help_text="Type of contract")
    contract_kind = models.CharField(max_length=15, choices=CONTRACT_KINDS, default='MAIN')
    
    # Contract Hierarchy
    parent_contract_id = models.BigIntegerField(blank=True, null=True, help_text="Parent contract ID")
    main_contract_id = models.BigIntegerField(blank=True, null=True, help_text="Main contract ID")
    
    # Subcontract Visibility Permission
    permission_required = models.BooleanField(
        default=False, 
        help_text="Whether parent contract has permission to view this subcontract (0=No, 1=Yes)"
    )
    
    # Contract Versioning
    version_number = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Contract version number")
    previous_version_id = models.BigIntegerField(blank=True, null=True, help_text="Previous version contract ID")
    
    # Financial Information
    contract_value = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Contract value"
    )
    currency = models.CharField(max_length=10, default='USD', help_text="Currency code")
    liability_cap = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Liability cap amount"
    )
    
    # Dates and Terms
    start_date = models.DateField(blank=True, null=True, help_text="Contract start date")
    end_date = models.DateField(blank=True, null=True, help_text="Contract end date")
    renewal_terms = models.TextField(blank=True, null=True, help_text="Renewal terms and conditions")
    auto_renewal = models.BooleanField(default=False, help_text="Auto renewal enabled")
    notice_period_days = models.PositiveIntegerField(
        default=30, 
        help_text="Notice period in days"
    )
    
    # Contract Status and Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    workflow_stage = models.CharField(max_length=20, choices=WORKFLOW_STAGES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    compliance_status = models.CharField(
        max_length=15, 
        choices=COMPLIANCE_STATUS, 
        default='under_review'
    )
    
    # Contract Details
    contract_category = models.CharField(
        max_length=20, 
        choices=CONTRACT_CATEGORIES, 
        blank=True, 
        null=True
    )
    termination_clause_type = models.CharField(
        max_length=15, 
        choices=TERMINATION_CLAUSE_TYPES, 
        blank=True, 
        null=True
    )
    
    # Legal and Risk Information
    dispute_resolution_method = models.CharField(
        max_length=15, 
        choices=DISPUTE_RESOLUTION_METHODS, 
        blank=True, 
        null=True
    )
    governing_law = models.CharField(max_length=100, blank=True, null=True)
    contract_risk_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Risk score from 0-10"
    )
    
    # JSON Fields for Complex Data
    insurance_requirements = models.JSONField(default=dict, blank=True)
    data_protection_clauses = models.JSONField(default=dict, blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)
    data_inventory = models.JSONField(null=True, blank=True, help_text="JSON mapping contract field labels to data types (personal, confidential, regular)")
    
    # File Management
    file_path = models.CharField(max_length=500, blank=True, null=True, help_text="Path to contract file")
    
    # Assignment and Ownership - using IntegerField to match existing database schema
    contract_owner = models.IntegerField(blank=True, null=True, help_text="Contract owner ID")
    legal_reviewer = models.IntegerField(blank=True, null=True, help_text="Legal reviewer ID")
    assigned_to = models.BigIntegerField(blank=True, null=True, help_text="Assigned user ID")
    
    # Archive Information
    is_archived = models.BooleanField(default=False)
    archived_date = models.DateTimeField(blank=True, null=True)
    archived_by = models.IntegerField(blank=True, null=True, help_text="Archived by user ID")
    archive_reason = models.CharField(
        max_length=20, 
        choices=ARCHIVE_REASONS, 
        blank=True, 
        null=True
    )
    archive_comments = models.TextField(blank=True, null=True)
    can_be_restored = models.BooleanField(default=True)
    
    # Compliance
    compliance_framework = models.CharField(max_length=255, blank=True, null=True)
    
    # Data Retention
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry', help_text="Data retention expiry date")
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_contracts'
        managed = False  # Don't let Django manage this table since it already exists
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contract_title} ({self.contract_number})"
    
    def is_expired(self):
        """Check if contract is expired"""
        if self.end_date and self.end_date < timezone.now().date():
            return True
        return False
    
    def days_until_expiry(self):
        """Calculate days until contract expiry"""
        if self.end_date:
            delta = self.end_date - timezone.now().date()
            return delta.days
        return None
    
    def get_insurance_requirements_display(self):
        """Return formatted insurance requirements"""
        if isinstance(self.insurance_requirements, dict):
            # Handle new structure with 'requirements' field
            if 'requirements' in self.insurance_requirements:
                return self.insurance_requirements.get('requirements', '')
            # Handle old structure (list)
            elif isinstance(self.insurance_requirements.get('requirements', []), list):
                return self.insurance_requirements.get('requirements', [])
            # Handle direct string
            else:
                return str(self.insurance_requirements)
        return ''
    
    def get_data_protection_clauses_display(self):
        """Return formatted data protection clauses"""
        if isinstance(self.data_protection_clauses, dict):
            # Handle new structure with 'clauses' field
            if 'clauses' in self.data_protection_clauses:
                return self.data_protection_clauses.get('clauses', '')
            # Handle old structure (list)
            elif isinstance(self.data_protection_clauses.get('clauses', []), list):
                return self.data_protection_clauses.get('clauses', [])
            # Handle direct string
            else:
                return str(self.data_protection_clauses)
        return ''
    
    def get_custom_fields_display(self):
        """Return formatted custom fields"""
        if isinstance(self.custom_fields, dict):
            return self.custom_fields
        return {}
    
    def save(self, *args, **kwargs):
        # Auto-update status based on dates
        if self.end_date and self.end_date < timezone.now().date() and self.status != 'EXPIRED':
            self.status = 'EXPIRED'
        
        # Auto-update workflow stage based on status
        if self.status == 'ACTIVE' and self.workflow_stage == 'executed':
            self.workflow_stage = 'active'
        
        super().save(*args, **kwargs)


class ContractTerm(models.Model):
    """Model for contract terms and conditions"""
    
    TERM_CATEGORIES = [
        ('Payment', 'Payment'),
        ('Delivery', 'Delivery'),
        ('Performance', 'Performance'),
        ('Liability', 'Liability'),
        ('Termination', 'Termination'),
        ('Intellectual Property', 'Intellectual Property'),
        ('Confidentiality', 'Confidentiality'),
        ('Other', 'Other'),
    ]
    
    RISK_LEVELS = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    ]
    
    COMPLIANCE_STATUS = [
        ('Pending', 'Pending'),
        ('Compliant', 'Compliant'),
        ('Non-Compliant', 'Non-Compliant'),
        ('Under Review', 'Under Review'),
        ('pending_review', 'Pending Review'),
    ]
    
    APPROVAL_STATUS = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Under Review', 'Under Review'),
    ]
    
    # Primary key - using id field to match database schema
    id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link contract term to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='contract_terms', null=True, blank=True,
                               help_text="Tenant this contract term belongs to")
    
    # Foreign key to contract - using contract_id field to match database schema
    contract_id = models.BigIntegerField(help_text="Contract ID")
    
    # Term fields matching exact database schema
    term_id = models.CharField(max_length=100)
    term_category = models.CharField(max_length=30)
    term_title = models.CharField(max_length=255, blank=True, null=True)
    term_text = models.TextField()
    risk_level = models.CharField(max_length=10, default='Low')
    compliance_status = models.CharField(max_length=20, default='Pending')
    is_standard = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=15, default='Pending')
    approved_by = models.IntegerField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    version_number = models.CharField(max_length=20, default='1.0')
    parent_term_id = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    data_inventory = models.JSONField(null=True, blank=True, help_text="JSON mapping term field labels to data types (personal, confidential, regular)")
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry', help_text="Data retention expiry date")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contract_terms'
        managed = True  # Let Django manage this table
        ordering = ['term_category', 'created_at']
    
    def __str__(self):
        return f"{self.term_title or f'Term {self.term_id}'}"


class ContractClause(models.Model):
    """Model for contract clauses - matching exact database schema"""
    
    CLAUSE_TYPES = [
        ('standard', 'Standard'),
        ('risk', 'Risk'),
        ('compliance', 'Compliance'),
        ('financial', 'Financial'),
        ('operational', 'Operational'),
        ('renewal', 'Renewal'),
        ('termination', 'Termination'),
        ('other', 'Other'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
        ('urgent', 'Urgent'),
    ]
    
    # Primary key - matching database schema
    id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link contract clause to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='contract_clauses', null=True, blank=True,
                               help_text="Tenant this contract clause belongs to")
    
    # Foreign key to contract - using contract_id field to match database schema
    contract_id = models.BigIntegerField(help_text="Contract ID", default=1)
    clause_id = models.CharField(max_length=100)
    clause_name = models.CharField(max_length=255)
    clause_type = models.CharField(max_length=20, default='standard')  # Remove choices to match raw schema
    clause_text = models.TextField()
    risk_level = models.CharField(max_length=10, default='low')  # Remove choices to match raw schema
    legal_category = models.CharField(max_length=100, blank=True, null=True)
    version_number = models.CharField(max_length=20, default='1.0')
    is_standard = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='Pending', null=True, blank=True, help_text="Clause approval status")
    created_by = models.IntegerField(blank=True, null=True, help_text="Created by user ID")
    
    # Renewal specific fields - matching exact database schema
    notice_period_days = models.IntegerField(blank=True, null=True)  # Changed from PositiveIntegerField
    auto_renew = models.BooleanField(default=False)
    renewal_terms = models.TextField(blank=True, null=True)
    
    # Termination specific fields - matching exact database schema
    termination_notice_period = models.IntegerField(blank=True, null=True)  # Changed from PositiveIntegerField
    early_termination_fee = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)]
    )
    termination_conditions = models.TextField(blank=True, null=True)
    data_inventory = models.JSONField(null=True, blank=True, help_text="JSON mapping clause field labels to data types (personal, confidential, regular)")
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry', help_text="Data retention expiry date")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contract_clauses'
        managed = True  # Let Django manage this table
        ordering = ['clause_type', 'clause_name']
    
    def __str__(self):
        return f"{self.clause_name}"


class VendorContact(models.Model):
    """Model for vendor contacts - matching exact database schema"""
    
    CONTACT_TYPES = [
        ('PRIMARY', 'Primary'),
        ('SECONDARY', 'Secondary'),
        ('TECHNICAL', 'Technical'),
        ('BILLING', 'Billing'),
        ('LEGAL', 'Legal'),
        ('EMERGENCY', 'Emergency'),
    ]
    
    # Primary key - matching database schema
    contact_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor contact to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='vendor_contacts', null=True, blank=True,
                               help_text="Tenant this vendor contact belongs to")
    
    # Foreign key to vendor - using vendor_id field to match database schema
    vendor_id = models.BigIntegerField(help_text="Vendor ID")
    
    # Contact information
    contact_type = models.CharField(
        max_length=20, 
        choices=CONTACT_TYPES, 
        default='PRIMARY',
        help_text="Type of contact"
    )
    first_name = models.CharField(max_length=100, help_text="First name")
    last_name = models.CharField(max_length=100, help_text="Last name")
    email = models.EmailField(max_length=255, help_text="Email address")
    phone = models.CharField(max_length=50, blank=True, null=True, help_text="Phone number")
    mobile = models.CharField(max_length=50, blank=True, null=True, help_text="Mobile number")
    designation = models.CharField(max_length=100, blank=True, null=True, help_text="Job designation")
    department = models.CharField(max_length=100, blank=True, null=True, help_text="Department")
    
    # Status flags - using BooleanField to match tinyint(1) in database
    is_primary = models.BooleanField(default=False, help_text="Is primary contact")
    is_active = models.BooleanField(default=True, help_text="Is active contact")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_contacts'
        managed = False  # Don't let Django manage this table since it already exists
        ordering = ['vendor_id', 'is_primary', 'contact_type', 'last_name', 'first_name']
        unique_together = [['vendor_id', 'email']]  # Prevent duplicate emails per vendor
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.contact_type})"
    
    @property
    def full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def display_name(self):
        """Return display name with designation"""
        name = self.full_name
        if self.designation:
            name += f" - {self.designation}"
        return name
    
    def get_primary_phone(self):
        """Get primary phone number (mobile preferred, then phone)"""
        if self.mobile:
            return self.mobile
        return self.phone or ''
    
    def clean(self):
        """Validate contact data"""
        from django.core.exceptions import ValidationError
        
        # Ensure at least one phone number is provided
        if not self.phone and not self.mobile:
            raise ValidationError("At least one phone number (phone or mobile) must be provided")
        
        # Ensure email is unique per vendor
        if self.email and self.vendor_id:
            existing = VendorContact.objects.filter(
                vendor_id=self.vendor_id, 
                email=self.email
            ).exclude(contact_id=self.contact_id)
            if existing.exists():
                raise ValidationError("Email address already exists for this vendor")
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one primary contact per vendor"""
        if self.is_primary and self.vendor_id:
            # Remove primary flag from other contacts for this vendor
            VendorContact.objects.filter(
                vendor_id=self.vendor_id,
                is_primary=True
            ).exclude(contact_id=self.contact_id).update(is_primary=False)
        
        super().save(*args, **kwargs)


class ContractAmendment(models.Model):
    """Model for contract amendments - matching exact database schema"""
    
    # Primary key - matching database schema
    amendment_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link contract amendment to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='contract_amendments', null=True, blank=True,
                               help_text="Tenant this contract amendment belongs to")
    
    # Foreign key to contract - using contract_id field to match database schema
    contract_id = models.BigIntegerField(help_text="Contract ID")
    
    # Amendment information
    amendment_number = models.CharField(max_length=50, help_text="Amendment number")
    amendment_date = models.DateTimeField(help_text="Amendment date")
    amendment_reason = models.TextField(help_text="Reason for amendment")
    changes_summary = models.TextField(help_text="Summary of changes")
    financial_impact = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Financial impact of amendment"
    )
    approved_by = models.IntegerField(blank=True, null=True, help_text="Approved by user ID")
    effective_date = models.DateTimeField(help_text="Effective date of amendment")
    attachment_path = models.CharField(max_length=500, blank=True, null=True, help_text="Path to amendment attachment")
    
    # New fields for enhanced amendment tracking
    amended_clause_ids = models.TextField(blank=True, null=True, help_text="Comma-separated list of amended clause IDs")
    amended_term_ids = models.TextField(blank=True, null=True, help_text="Comma-separated list of amended term IDs")
    affected_area = models.CharField(
        max_length=10,
        choices=[
            ('terms', 'Terms'),
            ('clauses', 'Clauses'),
            ('both', 'Both'),
        ],
        blank=True,
        null=True,
        help_text="Area affected by the amendment"
    )
    workflow_status = models.CharField(
        max_length=15,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('under_review', 'Under Review'),
        ],
        default='pending',
        help_text="Current workflow status of the amendment"
    )
    approval_date = models.DateTimeField(blank=True, null=True, help_text="Date when amendment was approved")
    amendment_version = models.CharField(max_length=20, blank=True, null=True, help_text="Version of the amendment")
    justification = models.TextField(blank=True, null=True, help_text="Detailed justification for the amendment")
    supporting_documents = models.JSONField(blank=True, null=True, help_text="JSON array of supporting document paths")
    initiated_by = models.IntegerField(blank=True, null=True, help_text="User ID who initiated the amendment")
    initiated_date = models.DateTimeField(blank=True, null=True, help_text="Date when amendment was initiated")
    amendment_notes = models.TextField(blank=True, null=True, help_text="Additional notes about the amendment")
    
    class Meta:
        db_table = 'contract_amendments'
        managed = True  # Let Django manage this table
        ordering = ['-amendment_date']
    
    def __str__(self):
        return f"Amendment {self.amendment_number} for Contract {self.contract_id}"
    
    def get_approved_by_display(self):
        """Get display name for approved_by user"""
        if self.approved_by:
            try:
                from mfa_auth.models import User
                user = User.objects.get(userid=self.approved_by)
                first_name = user.first_name or ""
                last_name = user.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
                return full_name if full_name else user.username
            except ImportError:
                return f"User {self.approved_by} (not found)"
            except Exception as e:
                # Handle User.DoesNotExist or any other exception
                return f"User {self.approved_by} (not found)"
        return None
    
    def get_initiated_by_display(self):
        """Get display name for initiated_by user"""
        if self.initiated_by:
            try:
                from mfa_auth.models import User
                user = User.objects.get(userid=self.initiated_by)
                first_name = user.first_name or ""
                last_name = user.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
                return full_name if full_name else user.username
            except ImportError:
                return f"User {self.initiated_by} (not found)"
            except Exception as e:
                # Handle User.DoesNotExist or any other exception
                return f"User {self.initiated_by} (not found)"
        return None
    
    def get_amended_clause_ids_list(self):
        """Get amended clause IDs as a list"""
        if self.amended_clause_ids:
            return [id.strip() for id in self.amended_clause_ids.split(',') if id.strip()]
        return []
    
    def get_amended_term_ids_list(self):
        """Get amended term IDs as a list"""
        if self.amended_term_ids:
            return [id.strip() for id in self.amended_term_ids.split(',') if id.strip()]
        return []
    
    def get_supporting_documents_list(self):
        """Get supporting documents as a list"""
        if self.supporting_documents:
            if isinstance(self.supporting_documents, list):
                return self.supporting_documents
            elif isinstance(self.supporting_documents, str):
                import json
                try:
                    return json.loads(self.supporting_documents)
                except json.JSONDecodeError:
                    return [self.supporting_documents]
        return []
    
    def clean(self):
        """Validate amendment data"""
        from django.core.exceptions import ValidationError
        
        # Ensure effective_date is not before amendment_date
        if self.effective_date and self.amendment_date and self.effective_date < self.amendment_date:
            raise ValidationError("Effective date cannot be before amendment date")
        
        # Ensure financial_impact is not negative
        if self.financial_impact is not None and self.financial_impact < 0:
            raise ValidationError("Financial impact cannot be negative")
        
        # Validate approval_date is not before amendment_date
        if self.approval_date and self.amendment_date and self.approval_date < self.amendment_date:
            raise ValidationError("Approval date cannot be before amendment date")
        
        # Validate initiated_date is not after amendment_date
        if self.initiated_date and self.amendment_date and self.initiated_date > self.amendment_date:
            raise ValidationError("Initiated date cannot be after amendment date")
        
        # Validate workflow_status transitions
        if self.workflow_status == 'approved' and not self.approval_date:
            raise ValidationError("Approval date is required when workflow status is approved")
        
        # Validate affected_area consistency
        if self.affected_area == 'terms' and self.amended_clause_ids:
            raise ValidationError("Cannot have amended clause IDs when affected area is 'terms'")
        if self.affected_area == 'clauses' and self.amended_term_ids:
            raise ValidationError("Cannot have amended term IDs when affected area is 'clauses'")
    
    def save(self, *args, **kwargs):
        """Override save to validate data"""
        self.clean()
        super().save(*args, **kwargs)


class ContractRenewal(models.Model):
    """Model for managing contract renewals"""
    
    RENEWAL_DECISIONS = [
        ('RENEW', 'Renew'),
        ('RENEGOTIATE', 'Renegotiate'),
        ('TERMINATE', 'Terminate'),
        ('PENDING', 'Pending'),
    ]
    
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('under_review', 'Under Review'),
        ('decision_made', 'Decision Made'),
    ]
    
    renewal_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link contract renewal to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='contract_renewals', null=True, blank=True,
                               help_text="Tenant this contract renewal belongs to")
    
    contract_id = models.BigIntegerField(help_text="Reference to the original contract")
    renewal_date = models.DateField(help_text="Date when renewal process was initiated")
    notification_sent_date = models.DateField(blank=True, null=True, help_text="Date when the renewal notification was sent")
    decision_due_date = models.DateField(blank=True, null=True, help_text="Date by which a decision must be made")
    renewal_decision = models.CharField(
        max_length=20,
        choices=RENEWAL_DECISIONS,
        default='PENDING',
        help_text="Renewal decision"
    )
    new_contract_id = models.BigIntegerField(blank=True, null=True, help_text="ID of the new contract created after renewal")
    decided_by = models.IntegerField(blank=True, null=True, help_text="User who made the decision")
    decision_date = models.DateField(blank=True, null=True, help_text="Date of decision")
    comments = models.TextField(blank=True, null=True, help_text="Any comments regarding the renewal")
    initiated_by = models.IntegerField(blank=True, null=True, help_text="User who initiated the renewal process")
    initiated_date = models.DateTimeField(blank=True, null=True, help_text="Date when the renewal process was initiated outside the system")
    renewal_reason = models.TextField(blank=True, null=True, help_text="Reason for the renewal")
    renewal_documents = models.CharField(max_length=500, blank=True, null=True, help_text="Path or reference to renewal-related documents")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated',
        help_text="Status of the renewal process"
    )
    renewed_contract_id = models.BigIntegerField(blank=True, null=True, help_text="Link to the original contract being renewed")
    
    # Note: Timestamps are not included as the table already exists without these fields
    
    class Meta:
        db_table = 'contract_renewals'
        managed = False  # Don't let Django manage this table since it already exists
        verbose_name = 'Contract Renewal'
        verbose_name_plural = 'Contract Renewals'
        ordering = ['-renewal_date']
    
    def __str__(self):
        return f"Renewal {self.renewal_id} - Contract {self.contract_id} - {self.renewal_decision}"
    
    def get_initiated_by_display(self):
        """Get display name for initiated_by user"""
        if self.initiated_by:
            try:
                from mfa_auth.models import User
                user = User.objects.get(userid=self.initiated_by)
                first_name = user.first_name or ""
                last_name = user.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
                return full_name if full_name else user.username
            except ImportError:
                return f"User {self.initiated_by} (not found)"
            except Exception as e:
                # Handle User.DoesNotExist or any other exception
                return f"User {self.initiated_by} (not found)"
        return None
    
    def get_decided_by_display(self):
        """Get display name for decided_by user"""
        if self.decided_by:
            try:
                from mfa_auth.models import User
                user = User.objects.get(userid=self.decided_by)
                first_name = user.first_name or ""
                last_name = user.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
                return full_name if full_name else user.username
            except ImportError:
                return f"User {self.decided_by} (not found)"
            except Exception as e:
                # Handle User.DoesNotExist or any other exception
                return f"User {self.decided_by} (not found)"
        return None
    
    def get_renewal_documents_list(self):
        """Get renewal documents as a list"""
        if self.renewal_documents:
            if isinstance(self.renewal_documents, str):
                try:
                    return json.loads(self.renewal_documents)
                except json.JSONDecodeError:
                    return [self.renewal_documents]
        return []
    
    def clean(self):
        """Validate renewal data"""
        from django.core.exceptions import ValidationError
        
        # Date validation removed - allow any date combinations
        # if self.decision_date and self.renewal_date and self.decision_date < self.renewal_date:
        #     raise ValidationError("Decision date cannot be before renewal date")
        
        # Date validation removed - allow any date combinations
        # if self.decision_due_date and self.renewal_date and self.decision_due_date < self.renewal_date:
        #     raise ValidationError("Decision due date cannot be before renewal date")
        
        # Date validation removed - allow any date combinations
        # if self.notification_sent_date and self.renewal_date and self.notification_sent_date < self.renewal_date:
        #     raise ValidationError("Notification sent date cannot be before renewal date")
        
        # Validate decision_date is required when renewal_decision is not PENDING
        if self.renewal_decision != 'PENDING' and not self.decision_date:
            raise ValidationError("Decision date is required when renewal decision is not pending")
        
        # Validate decided_by is required when renewal_decision is not PENDING
        if self.renewal_decision != 'PENDING' and not self.decided_by:
            raise ValidationError("Decided by is required when renewal decision is not pending")
        
        # Validate new_contract_id is required when renewal_decision is RENEW
        if self.renewal_decision == 'RENEW' and not self.new_contract_id:
            raise ValidationError("New contract ID is required when renewal decision is RENEW")
    
    def save(self, *args, **kwargs):
        """Override save to validate data"""
        self.clean()
        super().save(*args, **kwargs)


class ContractApproval(models.Model):
    """Model for managing contract approval workflows"""
    
    OBJECT_TYPE_CHOICES = [
        ('CONTRACT_CREATION', 'Contract Creation'),
        ('CONTRACT_AMENDMENT', 'Contract Amendment'),
        ('SUBCONTRACT_CREATION', 'Subcontract Creation'),
        ('CONTRACT_RENEWAL', 'Contract Renewal'),
    ]
    
    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMMENTED', 'Commented'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SKIPPED', 'Skipped'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    approval_id = models.AutoField(primary_key=True)
    
    # MULTI-TENANCY: Link contract approval to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='contract_approvals', null=True, blank=True,
                               help_text="Tenant this contract approval belongs to")
    
    workflow_id = models.IntegerField(help_text="ID of the workflow this approval belongs to")
    workflow_name = models.CharField(max_length=255, help_text="Name of the workflow")
    assigner_id = models.IntegerField(help_text="ID of the user who assigned this approval")
    assigner_name = models.CharField(max_length=255, help_text="Name of the user who assigned this approval")
    assignee_id = models.IntegerField(help_text="ID of the user assigned to approve")
    assignee_name = models.CharField(max_length=255, help_text="Name of the user assigned to approve")
    object_type = models.CharField(
        max_length=50, 
        choices=OBJECT_TYPE_CHOICES,
        help_text="Type of object requiring approval"
    )
    object_id = models.IntegerField(help_text="ID of the contract requiring approval")
    assigned_date = models.DateTimeField(help_text="Date when the approval was assigned")
    due_date = models.DateTimeField(help_text="Date when the approval is due")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ASSIGNED',
        help_text="Current status of the approval"
    )
    comment_text = models.TextField(blank=True, null=True, help_text="Comments from the approver")
    approved_date = models.DateTimeField(blank=True, null=True, help_text="Date when the approval was approved")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'contract_approvals'
        managed = True
        verbose_name = 'Contract Approval'
        verbose_name_plural = 'Contract Approvals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_id']),
            models.Index(fields=['assignee_id']),
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"Approval {self.approval_id} - {self.workflow_name} - {self.assignee_name}"
    
    def is_overdue(self):
        """Check if the approval is overdue"""
        return self.status in ['ASSIGNED', 'IN_PROGRESS'] and timezone.now() > self.due_date
    
    def get_contract(self):
        """Get the related contract object"""
        if self.object_type == 'CONTRACT_CREATION':
            try:
                return VendorContract.objects.get(contract_id=self.object_id)
            except VendorContract.DoesNotExist:
                return None
        elif self.object_type == 'CONTRACT_AMENDMENT':
            try:
                return ContractAmendment.objects.get(amendment_id=self.object_id)
            except ContractAmendment.DoesNotExist:
                return None
        elif self.object_type == 'SUBCONTRACT_CREATION':
            try:
                return VendorContract.objects.get(contract_id=self.object_id, contract_kind='SUBCONTRACT')
            except VendorContract.DoesNotExist:
                return None
        elif self.object_type == 'CONTRACT_RENEWAL':
            try:
                return ContractRenewal.objects.get(renewal_id=self.object_id)
            except ContractRenewal.DoesNotExist:
                return None
        return None
    
    def clean(self):
        """Validate approval data"""
        from django.core.exceptions import ValidationError
        
        # Validate due_date is not before assigned_date
        if self.due_date and self.assigned_date and self.due_date < self.assigned_date:
            raise ValidationError("Due date cannot be before assigned date")
        
        # Validate object_id exists for the given object_type
        if self.object_id:
            contract = self.get_contract()
            if not contract:
                raise ValidationError(f"Object with ID {self.object_id} not found for type {self.object_type}")
    
    def save(self, *args, **kwargs):
        """Override save to validate data"""
        self.clean()
        super().save(*args, **kwargs)