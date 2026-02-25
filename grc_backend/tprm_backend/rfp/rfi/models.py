from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin


class RFI(TPRMEncryptedFieldsMixin, models.Model):
    """
    Model for Request for Information (RFI) data
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('IN_REVIEW', 'In Review'),
        ('APPROVED', 'Approved'),
        ('PUBLISHED', 'Published'),
        ('SUBMISSION_OPEN', 'Submission Open'),
        ('EVALUATION', 'Evaluation'),
        ('AWARDED', 'Awarded'),
        ('CANCELLED', 'Cancelled'),
        ('ARCHIVED', 'Archived'),
    ]
    
    EVALUATION_METHOD_CHOICES = [
        ('lowest_price', 'Lowest Price'),
        ('best_value', 'Best Value'),
        ('weighted_scoring', 'Weighted Scoring'),
    ]
    
    CRITICALITY_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Primary key
    rfi_id = models.BigAutoField(primary_key=True, auto_created=True)
    
    # MULTI-TENANCY: Link RFI to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfis', null=True, blank=True,
                               help_text="Tenant this RFI belongs to")
    
    # Basic information
    rfi_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    rfi_title = models.CharField(max_length=255)
    description = models.TextField()
    rfi_type = models.TextField()
    category = models.CharField(max_length=100, null=True, blank=True)
    
    # Budget information
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    budget_range_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    budget_range_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Timeline information
    issue_date = models.DateField(null=True, blank=True)
    submission_deadline = models.DateTimeField(null=True, blank=True)
    evaluation_period_end = models.DateField(null=True, blank=True)
    award_date = models.DateField(null=True, blank=True)
    
    # Status and workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_by = models.IntegerField()
    approved_by = models.IntegerField(null=True, blank=True)
    primary_reviewer_id = models.IntegerField(null=True, blank=True)
    executive_reviewer_id = models.IntegerField(null=True, blank=True)
    version_number = models.IntegerField(default=1)
    
    # Configuration options
    auto_approve = models.BooleanField(default=False)
    allow_late_submissions = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Workflow and evaluation
    approval_workflow_id = models.CharField(max_length=50, null=True, blank=True)
    evaluation_method = models.CharField(max_length=20, choices=EVALUATION_METHOD_CHOICES, default='weighted_scoring')
    criticality_level = models.CharField(max_length=10, choices=CRITICALITY_LEVEL_CHOICES, default='medium')
    geographical_scope = models.CharField(max_length=255, null=True, blank=True)
    
    # JSON fields
    compliance_requirements = models.JSONField(null=True, blank=True)
    custom_fields = models.JSONField(null=True, blank=True)
    data_inventory = models.JSONField(null=True, blank=True)
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry')
    
    # Award information
    final_evaluation_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    award_decision_date = models.DateTimeField(null=True, blank=True)
    award_justification = models.TextField(null=True, blank=True)
    documents = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.rfi_title} ({self.rfi_number})"
    
    def save(self, *args, **kwargs):
        # Normalize rfi_number
        if isinstance(self.rfi_number, str):
            self.rfi_number = self.rfi_number.strip()
            if not self.rfi_number:
                self.rfi_number = None
        
        # Generate RFI number only if not provided and creating new instance
        if not self.rfi_number and not self.pk:
            today = timezone.now()
            prefix = f"RFI-{today.year}-{today.month:02d}-"
            last_rfi = RFI.objects.filter(rfi_number__startswith=prefix).order_by('-rfi_number').first()
            if last_rfi:
                try:
                    last_number = int(last_rfi.rfi_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            self.rfi_number = f"{prefix}{new_number:04d}"
        
        # Ensure JSON fields are properly formatted
        if isinstance(self.compliance_requirements, str):
            try:
                self.compliance_requirements = json.loads(self.compliance_requirements)
            except (json.JSONDecodeError, TypeError):
                self.compliance_requirements = {}
        
        if isinstance(self.custom_fields, str):
            try:
                self.custom_fields = json.loads(self.custom_fields)
            except (json.JSONDecodeError, TypeError):
                self.custom_fields = {}
        
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'rfis'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rfi_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
            models.Index(fields=['tenant']),
            models.Index(fields=['created_at']),
        ]


class RFIEvaluationCriteria(models.Model):
    """
    Model for RFI evaluation criteria
    """
    EVALUATION_TYPE_CHOICES = [
        ('scoring', 'Scoring'),
        ('binary', 'Binary'),
        ('narrative', 'Narrative'),
    ]
    
    # Primary key
    criteria_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link evaluation criteria to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfi_evaluation_criteria', null=True, blank=True)
    
    # Foreign key to RFI
    # NOTE: db_constraint=False to avoid FK issues in existing DBs
    rfi = models.ForeignKey(RFI, on_delete=models.CASCADE, related_name='evaluation_criteria', db_column='rfi_id', db_constraint=False)
    
    # Criteria details
    criteria_name = models.CharField(max_length=255)
    criteria_description = models.TextField()
    weight_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    evaluation_type = models.CharField(max_length=10, choices=EVALUATION_TYPE_CHOICES, default='scoring')
    
    # Scoring parameters
    min_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    median_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Veto parameters
    is_mandatory = models.BooleanField(default=False)
    veto_enabled = models.BooleanField(default=False)
    veto_threshold = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Narrative parameters
    min_word_count = models.IntegerField(null=True, blank=True)
    
    # Binary parameters
    expected_boolean_answer = models.CharField(max_length=3, null=True, blank=True)
    
    # Display and creation info
    display_order = models.IntegerField(default=0)
    created_by = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add=True)
    data_inventory = models.JSONField(null=True, blank=True)
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry')
    
    def __str__(self):
        return f"{self.criteria_name} - {self.weight_percentage}%"
    
    class Meta:
        db_table = 'rfi_evaluation_criteria'
        ordering = ['display_order', 'criteria_id']
        indexes = [
            models.Index(fields=['rfi']),
            models.Index(fields=['is_mandatory']),
            models.Index(fields=['tenant']),
        ]


class RFIVendorInvitation(models.Model):
    """
    Model for RFI vendor invitations (similar to rfp_vendor_invitations)
    """
    INVITATION_STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('OPENED', 'Opened'),
        ('CLICKED', 'Clicked'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('DECLINED', 'Declined'),
        ('SUBMITTED', 'Submitted'),
        ('FAILED', 'Failed'),
    ]

    SUBMISSION_SOURCE_CHOICES = [
        ('invited', 'Invited'),
        ('open', 'Open'),
    ]

    invitation_id = models.BigAutoField(primary_key=True)

    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId',
                               related_name='rfi_vendor_invitations', null=True, blank=True)

    # NOTE: db_constraint=False to avoid FK issues in existing DBs
    rfi = models.ForeignKey(RFI, on_delete=models.CASCADE, related_name='invitations', db_constraint=False)
    vendor_id = models.BigIntegerField(null=True, blank=True)
    vendor_email = models.CharField(max_length=255, null=True, blank=True)
    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    vendor_phone = models.CharField(max_length=50, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    invited_date = models.DateTimeField(auto_now_add=True)
    invitation_status = models.CharField(max_length=20, choices=INVITATION_STATUS_CHOICES, default='CREATED')
    acknowledged_date = models.DateTimeField(null=True, blank=True)
    declined_reason = models.TextField(null=True, blank=True)
    invitation_url = models.CharField(max_length=500, null=True, blank=True)
    acknowledgment_url = models.CharField(max_length=500, null=True, blank=True)
    submission_url = models.CharField(max_length=500, null=True, blank=True)
    unique_token = models.CharField(max_length=255, null=True, blank=True)
    is_matched_vendor = models.BooleanField(default=False)
    submission_source = models.CharField(max_length=10, choices=SUBMISSION_SOURCE_CHOICES, default='invited')
    utm_parameters = models.JSONField(null=True, blank=True)
    custom_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RFI Invitation {self.invitation_id} - {self.vendor_name} ({self.company_name})"

    class Meta:
        db_table = 'rfi_vendor_invitations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rfi']),
            models.Index(fields=['unique_token']),
        ]


class RFIResponse(models.Model):
    """
    Model for storing RFI responses from vendors (similar to rfp_responses)
    """
    EVALUATION_STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_EVALUATION', 'Under Evaluation'),
        ('SHORTLISTED', 'Shortlisted'),
        ('REJECTED', 'Rejected'),
        ('AWARDED', 'Awarded'),
    ]

    SUBMISSION_SOURCE_CHOICES = [
        ('invited', 'Invited'),
        ('open', 'Open'),
    ]

    response_id = models.BigAutoField(primary_key=True)

    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId',
                               related_name='rfi_responses', null=True, blank=True)

    # NOTE: db_constraint=False to avoid FK issues in existing DBs
    rfi = models.ForeignKey(RFI, on_delete=models.CASCADE, related_name='responses', db_constraint=False)
    vendor_id = models.BigIntegerField(null=True, blank=True)
    invitation_id = models.BigIntegerField(null=True, blank=True)
    submission_date = models.DateTimeField(null=True, blank=True)

    response_documents = models.JSONField(null=True, blank=True)
    document_urls = models.JSONField(null=True, blank=True)

    proposed_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commercial_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weighted_final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    evaluation_status = models.CharField(max_length=20, choices=EVALUATION_STATUS_CHOICES, default='DRAFT')
    auto_rejected = models.BooleanField(default=False)
    rejection_reason = models.TextField(null=True, blank=True)

    submission_source = models.CharField(max_length=10, choices=SUBMISSION_SOURCE_CHOICES, default='invited')
    external_submission_data = models.JSONField(null=True, blank=True)
    draft_data = models.JSONField(null=True, blank=True)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    last_saved_at = models.DateTimeField(null=True, blank=True)

    submitted_by = models.CharField(max_length=255, null=True, blank=True)
    evaluated_by = models.IntegerField(null=True, blank=True)
    evaluation_date = models.DateTimeField(null=True, blank=True)
    evaluation_comments = models.TextField(null=True, blank=True)

    org = models.CharField(max_length=255, null=True, blank=True)
    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    contact_email = models.CharField(max_length=255, null=True, blank=True)
    contact_phone = models.CharField(max_length=50, null=True, blank=True)

    proposal_data = models.JSONField(null=True, blank=True)
    submission_status = models.CharField(max_length=20, default='DRAFT')
    submitted_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"RFI Response {self.response_id} - Vendor {self.vendor_id}"

    class Meta:
        db_table = 'rfi_responses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rfi']),
            models.Index(fields=['invitation_id']),
        ]
