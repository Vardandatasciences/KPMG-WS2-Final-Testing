from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin


class RFP(TPRMEncryptedFieldsMixin, models.Model):
    """
    Model for Request for Proposal (RFP) data
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
    rfp_id = models.BigAutoField(primary_key=True, auto_created=True)
    
    # MULTI-TENANCY: Link RFP to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfps', null=True, blank=True,
                               help_text="Tenant this RFP belongs to")
    
    # Basic information
    rfp_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    rfp_title = models.CharField(max_length=255)
    description = models.TextField()
    rfp_type = models.TextField()  # Changed from CharField with choices to TextField - now accepts any text value
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
    created_by = models.IntegerField()  # Changed from ForeignKey to IntegerField to match MySQL schema
    approved_by = models.IntegerField(null=True, blank=True)  # Changed from ForeignKey to IntegerField
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
    data_inventory = models.JSONField(null=True, blank=True, help_text="JSON mapping RFP field labels to data types (personal, confidential, regular)")
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry', help_text="Data retention expiry date")
    
    # Award information
    final_evaluation_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    award_decision_date = models.DateTimeField(null=True, blank=True)
    award_justification = models.TextField(null=True, blank=True)
    documents=models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.rfp_title} ({self.rfp_number})"
    
    def save(self, *args, **kwargs):
        # Normalize rfp_number: strip whitespace if it's a string
        if isinstance(self.rfp_number, str):
            self.rfp_number = self.rfp_number.strip()
            if not self.rfp_number:
                self.rfp_number = None
        
        # Generate RFP number only if not provided and creating new instance
        if not self.rfp_number and not self.pk:
            # Format: RFP-YYYY-MM-XXXX (XXXX is a sequential number)
            today = timezone.now()
            prefix = f"RFP-{today.year}-{today.month:02d}-"
            
            # Get the highest number with the same prefix
            last_rfp = RFP.objects.filter(rfp_number__startswith=prefix).order_by('-rfp_number').first()
            
            if last_rfp:
                try:
                    last_number = int(last_rfp.rfp_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
                
            self.rfp_number = f"{prefix}{new_number:04d}"
        
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
        db_table = 'rfps'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rfp_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
        ]


class RFPEvaluationCriteria(models.Model):
    """
    Model for RFP evaluation criteria
    """
    EVALUATION_TYPE_CHOICES = [
        ('scoring', 'Scoring'),
        ('binary', 'Binary'),
        ('narrative', 'Narrative'),
    ]
    
    EXPECTED_BOOLEAN_ANSWER_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]
    
    # Primary key
    criteria_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link evaluation criteria to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_evaluation_criteria', null=True, blank=True,
                               help_text="Tenant this evaluation criteria belongs to")
    
    # Foreign key to RFP
    rfp = models.ForeignKey(RFP, on_delete=models.CASCADE, related_name='evaluation_criteria')
    
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
    expected_boolean_answer = models.CharField(max_length=3, choices=EXPECTED_BOOLEAN_ANSWER_CHOICES, null=True, blank=True)
    
    # Display and creation info
    display_order = models.IntegerField(default=0)
    created_by = models.IntegerField()  # Changed from ForeignKey to IntegerField to match MySQL schema
    created_date = models.DateTimeField(auto_now_add=True)
    data_inventory = models.JSONField(null=True, blank=True, help_text="JSON mapping criteria field labels to data types (personal, confidential, regular)")
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry', help_text="Data retention expiry date")
    
    def __str__(self):
        return f"{self.criteria_name} - {self.weight_percentage}%"
    
    class Meta:
        db_table = 'rfp_evaluation_criteria'
        ordering = ['display_order', 'criteria_id']
        indexes = [
            models.Index(fields=['rfp']),
            models.Index(fields=['is_mandatory']),
        ]


class CustomUser(models.Model):
    """
    Model for custom user data from the users table
    """
    user_id = models.AutoField(primary_key=True, db_column='UserId')
    username = models.CharField(max_length=255, db_column='UserName')
    password = models.CharField(max_length=255, db_column='Password')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')
    email = models.EmailField(max_length=100, db_column='Email')
    first_name = models.CharField(max_length=45, db_column='FirstName')
    last_name = models.CharField(max_length=45, db_column='LastName')
    is_active = models.CharField(max_length=45, db_column='IsActive')
    department_id = models.IntegerField(null=True, blank=True, db_column='DepartmentId')
    session_token = models.CharField(max_length=1045, null=True, blank=True)
    consent_accepted = models.CharField(max_length=1, null=True, blank=True)
    license_key = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    class Meta:
        db_table = 'users'
        ordering = ['user_id']


class FileStorage(models.Model):
    """
    Model for tracking files stored in S3 via the microservice
    """
    OPERATION_TYPE_CHOICES = [
        ('upload', 'Upload'),
        ('download', 'Download'),
        ('export', 'Export'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Primary key
    id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link file storage to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='file_storage', null=True, blank=True,
                               help_text="Tenant this file storage belongs to")
    
    # File information
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPE_CHOICES)
    user_id = models.CharField(max_length=255)
    file_name = models.CharField(max_length=500)
    original_name = models.CharField(max_length=500, null=True, blank=True)
    stored_name = models.CharField(max_length=500, null=True, blank=True)
    
    # S3 information
    s3_url = models.TextField(null=True, blank=True)
    s3_key = models.CharField(max_length=1000, null=True, blank=True)
    s3_bucket = models.CharField(max_length=255, null=True, blank=True)
    
    # File metadata
    file_type = models.CharField(max_length=50, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=255, null=True, blank=True)
    
    # Export specific
    export_format = models.CharField(max_length=20, null=True, blank=True)
    record_count = models.IntegerField(null=True, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    
    # Platform information
    platform = models.CharField(max_length=50, default='S3_Microservice')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.operation_type} - {self.file_name} ({self.status})"
    
    class Meta:
        db_table = 'file_storage'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['operation_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['file_type']),
        ]


class S3Files(models.Model):
    """
    Model for tracking files stored in S3 - matches the existing s3_files table
    """
    id = models.AutoField(primary_key=True)
    
    # MULTI-TENANCY: Link S3 file to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='s3_files', null=True, blank=True,
                               help_text="Tenant this S3 file belongs to")
    
    url = models.TextField(null=True, blank=True)
    file_type = models.CharField(max_length=50, null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=100, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"S3 File - {self.file_name} ({self.uploaded_at})"
    
    class Meta:
        db_table = 's3_files'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['file_type']),
            models.Index(fields=['uploaded_at']),
        ]


class RFPEvaluationScore(models.Model):
    """
    Model for RFP Evaluation Scores - stores individual criterion scores for each evaluator
    Matches the existing rfp_evaluation_scores table
    """
    EVALUATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]
    
    score_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link evaluation score to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_evaluation_scores', null=True, blank=True,
                               help_text="Tenant this evaluation score belongs to")
    
    response_id = models.BigIntegerField(db_index=True)  # FK to rfp_responses table
    criteria_id = models.BigIntegerField(db_index=True)  # FK to evaluation criteria
    evaluator_id = models.IntegerField(db_index=True)  # FK to users table
    score_value = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    raw_response = models.TextField(null=True, blank=True)  # For text responses
    auto_calculated = models.BooleanField(default=False)  # If score was auto-calculated
    comments = models.TextField(null=True, blank=True)
    evaluation_date = models.DateTimeField(auto_now_add=True)
    evaluation_status = models.CharField(
        max_length=20, 
        choices=EVALUATION_STATUS_CHOICES, 
        default='pending'
    )
    
    def __str__(self):
        return f"Evaluation Score {self.score_id} - Response {self.response_id} by Evaluator {self.evaluator_id}"
    
    class Meta:
        db_table = 'rfp_evaluation_scores'
        ordering = ['-evaluation_date']
        indexes = [
            models.Index(fields=['response_id']),
            models.Index(fields=['criteria_id']),
            models.Index(fields=['evaluator_id']),
            models.Index(fields=['evaluation_status']),
            models.Index(fields=['evaluation_date']),
        ]
        # Ensure one score per evaluator per criterion per response
        unique_together = [['response_id', 'criteria_id', 'evaluator_id']]


class RFPEvaluatorAssignment(models.Model):
    """
    Model for tracking evaluator assignments to proposals
    """
    ASSIGNMENT_STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    ASSIGNMENT_TYPE_CHOICES = [
        ('evaluation', 'Evaluation'),
        ('review', 'Review'),
        ('approval', 'Approval'),
    ]
    
    assignment_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link evaluator assignment to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_evaluator_assignments', null=True, blank=True,
                               help_text="Tenant this evaluator assignment belongs to")
    
    proposal_id = models.BigIntegerField(db_index=True)  # FK to rfp_responses table
    evaluator_id = models.IntegerField(db_index=True)  # FK to users table
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default='evaluation')
    assigned_by_id = models.IntegerField(db_index=True)  # FK to users table (who assigned)
    assigned_date = models.DateTimeField(auto_now_add=True)
    started_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    deadline_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS_CHOICES, default='ASSIGNED')
    notes = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Assignment {self.assignment_id} - Evaluator {self.evaluator_id} to Proposal {self.proposal_id}"
    
    class Meta:
        db_table = 'rfp_evaluator_assignments'
        ordering = ['-assigned_date']
        indexes = [
            models.Index(fields=['proposal_id']),
            models.Index(fields=['evaluator_id']),
            models.Index(fields=['assignment_type']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_date']),
            models.Index(fields=['deadline_date']),
        ]
        # Ensure one assignment per evaluator per proposal per assignment type
        unique_together = [['proposal_id', 'evaluator_id', 'assignment_type']]


class RFPCommittee(models.Model):
    """
    Model for RFP Committee assignments
    Maps to rfp_committee table
    """
    committee_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link committee to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_committees', null=True, blank=True,
                               help_text="Tenant this committee belongs to")
    
    rfp_id = models.BigIntegerField(db_index=True)
    response_id = models.JSONField(null=True, blank=True)  # JSON array of response IDs
    member_id = models.IntegerField(db_index=True)
    member_role = models.CharField(max_length=100, default='Committee Member')
    is_chair = models.BooleanField(default=False)
    added_date = models.DateTimeField(auto_now_add=True)
    added_by = models.IntegerField()
    rfp_committeecol = models.CharField(max_length=45, null=True, blank=True)
    response_ids = models.JSONField(null=True, blank=True)  # JSON array of response IDs (alternative field)
    
    def __str__(self):
        return f"Committee {self.committee_id} - RFP {self.rfp_id} - Member {self.member_id}"
    
    class Meta:
        db_table = 'rfp_committee'
        ordering = ['-added_date']
        indexes = [
            models.Index(fields=['rfp_id']),
            models.Index(fields=['member_id']),
            models.Index(fields=['is_chair']),
        ]


class RFPFinalEvaluation(models.Model):
    """
    Model for RFP Final Evaluation results
    Maps to rfp_final_evaluation table
    """
    final_eval_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link final evaluation to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_final_evaluations', null=True, blank=True,
                               help_text="Tenant this final evaluation belongs to")
    
    rfp_id = models.BigIntegerField(db_index=True)
    response_id = models.BigIntegerField(db_index=True)
    evaluator_id = models.IntegerField(db_index=True)
    ranking_position = models.IntegerField()
    ranking_score = models.DecimalField(max_digits=5, decimal_places=2)
    evaluation_comments = models.TextField(null=True, blank=True)
    evaluation_date = models.DateTimeField(auto_now_add=True)
    consensus_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"Final Eval {self.final_eval_id} - RFP {self.rfp_id} - Response {self.response_id} by Evaluator {self.evaluator_id}"
    
    class Meta:
        db_table = 'rfp_final_evaluation'
        ordering = ['-evaluation_date']
        indexes = [
            models.Index(fields=['rfp_id']),
            models.Index(fields=['response_id']),
            models.Index(fields=['evaluator_id']),
            models.Index(fields=['ranking_position']),
        ]
        # Ensure one evaluation per evaluator per response per RFP
        unique_together = [['rfp_id', 'response_id', 'evaluator_id']]


class RFPVersions(models.Model):
    """
    Model for tracking RFP versions and changes
    """
    VERSION_TYPE_CHOICES = [
        ('INITIAL', 'Initial'),
        ('REVISION', 'Revision'),
        ('CONSOLIDATION', 'Consolidation'),
        ('FINAL', 'Final'),
        ('ROLLBACK', 'Rollback'),
    ]
    
    # Primary key
    version_id = models.CharField(max_length=50, primary_key=True)
    
    # MULTI-TENANCY: Link RFP version to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_versions', null=True, blank=True,
                               help_text="Tenant this RFP version belongs to")
    
    # Foreign key to RFP
    rfp_id = models.BigIntegerField(db_index=True)
    
    # Version details
    version_number = models.IntegerField()
    version_label = models.CharField(max_length=255)
    json_payload = models.JSONField()  # Complete RFP data at this version
    changes_summary = models.TextField()
    created_by = models.IntegerField()
    created_by_name = models.CharField(max_length=255)
    created_by_role = models.CharField(max_length=100)
    version_type = models.CharField(max_length=20, choices=VERSION_TYPE_CHOICES, default='REVISION')
    parent_version_id = models.CharField(max_length=50, null=True, blank=True)
    is_current = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    change_reason = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Version {self.version_number} - {self.version_label}"
    
    class Meta:
        db_table = 'rfp_versions'
        ordering = ['-version_number', '-created_at']
        indexes = [
            models.Index(fields=['rfp_id']),
            models.Index(fields=['version_number']),
            models.Index(fields=['is_current']),
            models.Index(fields=['parent_version_id']),
            models.Index(fields=['created_at']),
        ]


class RFPChangeRequests(models.Model):
    """
    Model for tracking change requests for RFPs
    """
    REQUEST_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('ADDRESSED', 'Addressed'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    # Primary key
    change_request_id = models.CharField(max_length=50, primary_key=True)
    
    # MULTI-TENANCY: Link change request to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_change_requests', null=True, blank=True,
                               help_text="Tenant this change request belongs to")
    
    # Foreign keys
    rfp_id = models.BigIntegerField(db_index=True)
    stage_id = models.CharField(max_length=50, null=True, blank=True)
    approval_id = models.CharField(max_length=50, null=True, blank=True)
    
    # Request details
    requested_by = models.IntegerField()
    requested_by_name = models.CharField(max_length=255)
    requested_by_role = models.CharField(max_length=100)
    request_description = models.TextField()
    specific_fields = models.JSONField(null=True, blank=True)  # Fields that need to be changed
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default='PENDING')
    
    # Response details
    addressed_by = models.IntegerField(null=True, blank=True)
    addressed_by_name = models.CharField(max_length=255, null=True, blank=True)
    addressed_by_role = models.CharField(max_length=100, null=True, blank=True)
    response_notes = models.TextField(null=True, blank=True)
    addressed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Change Request {self.change_request_id} - {self.rfp_id}"
    
    class Meta:
        db_table = 'rfp_change_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rfp_id']),
            models.Index(fields=['stage_id']),
            models.Index(fields=['approval_id']),
            models.Index(fields=['requested_by']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
        ]


class RFPVersionComparisons(models.Model):
    """
    Model for tracking comparisons between RFP versions
    """
    # Primary key
    comparison_id = models.CharField(max_length=50, primary_key=True)
    
    # MULTI-TENANCY: Link version comparison to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_version_comparisons', null=True, blank=True,
                               help_text="Tenant this version comparison belongs to")
    
    # Foreign keys
    rfp_id = models.BigIntegerField(db_index=True)
    from_version_id = models.CharField(max_length=50)
    to_version_id = models.CharField(max_length=50)
    
    # Comparison details
    comparison_data = models.JSONField()  # Detailed comparison results
    fields_changed = models.JSONField()  # List of fields that changed
    changes_summary = models.TextField()
    created_by = models.IntegerField()
    created_by_name = models.CharField(max_length=255)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comparison {self.comparison_id} - {self.from_version_id} to {self.to_version_id}"
    
    class Meta:
        db_table = 'rfp_version_comparisons'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rfp_id']),
            models.Index(fields=['from_version_id']),
            models.Index(fields=['to_version_id']),
            models.Index(fields=['created_at']),
        ]


class Vendor(models.Model):
    """
    Model for Vendor data
    """
    RISK_LEVEL_CHOICES = [
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
    
    # Primary key
    vendor_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='vendors', null=True, blank=True,
                               help_text="Tenant this vendor belongs to")
    
    # Basic information
    vendor_code = models.CharField(max_length=50, blank=True, null=True)
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
    
    # Location information
    headquarters_country = models.CharField(max_length=100, blank=True, null=True)
    headquarters_address = models.TextField(blank=True, null=True)
    
    # Description
    description = models.TextField(blank=True, null=True)
    
    # Classification
    vendor_category_id = models.BigIntegerField(blank=True, null=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    lifecycle_stage = models.CharField(max_length=50, blank=True, null=True)
    
    # Assessment dates
    onboarding_date = models.DateField(blank=True, null=True)
    last_assessment_date = models.DateField(blank=True, null=True)
    next_assessment_date = models.DateField(blank=True, null=True)
    
    # Risk flags
    is_critical_vendor = models.BooleanField(default=False)
    has_data_access = models.BooleanField(default=False)
    has_system_access = models.BooleanField(default=False)
    
    # Audit fields
    created_by = models.IntegerField(blank=True, null=True)
    updated_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields that match database schema
    match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    # NOTE: The following fields were removed as they don't exist in the database:
    # - rating: Use calculateVendorRating() in frontend or sustainability_rating
    # - location: Use headquarters_country and headquarters_address instead
    # - experience_years: Calculate from onboarding_date or incorporation_date
    # - email: Use vendor_contacts table for contact emails
    # - phone: Use vendor_contacts table for contact phones
      
    def __str__(self):
        return f"{self.company_name} ({self.vendor_code})"
    
    def save(self, *args, **kwargs):
        # Generate vendor code if not provided
        if not self.vendor_code and not self.pk:
            # Format: VEN-YYYY-MM-XXXX (XXXX is a sequential number)
            today = timezone.now()
            prefix = f"VEN-{today.year}-{today.month:02d}-"
            
            # Get the highest number with the same prefix
            last_vendor = Vendor.objects.filter(vendor_code__startswith=prefix).order_by('-vendor_code').first()
            
            if last_vendor:
                try:
                    last_number = int(last_vendor.vendor_code.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
                
            self.vendor_code = f"{prefix}{new_number:04d}"
                
        super().save(*args, **kwargs)
    
    class Meta:
        db_table = 'vendors'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vendor_code']),
            models.Index(fields=['company_name']),
            models.Index(fields=['status']),
        ]


class VendorCapability(models.Model):
    """
    Model for vendor capabilities
    """
    capability_id = models.BigAutoField(primary_key=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='capabilities')
    capability_name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.capability_name
    
    class Meta:
        db_table = 'vendor_capabilities'
        unique_together = ('vendor', 'capability_name')


class VendorCertification(models.Model):
    """
    Model for vendor certifications
    """
    certification_id = models.BigAutoField(primary_key=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='certifications')
    certification_name = models.CharField(max_length=100)
    expiry_date = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return self.certification_name
    
    class Meta:
        db_table = 'vendor_certifications'
        unique_together = ('vendor', 'certification_name')


class RFPUnmatchedVendor(models.Model):
    """
    Model for unmatched vendors from RFP invitations
    """
    MATCHING_STATUS_CHOICES = [
        ('unmatched', 'Unmatched'),
        ('pending_review', 'Pending Review'),
        ('matched', 'Matched'),
        ('rejected', 'Rejected'),
    ]
    
    unmatched_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link unmatched vendor to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_unmatched_vendors', null=True, blank=True,
                               help_text="Tenant this unmatched vendor belongs to")
    
    # Link to vendor invitation (which contains the RFP reference)
    invitation_id = models.BigIntegerField(blank=True, null=True, default=None,
                                          help_text="Links to rfp_vendor_invitations table")
    vendor_name = models.CharField(max_length=255)
    vendor_email = models.CharField(max_length=255)
    vendor_phone = models.CharField(max_length=50, blank=True, null=True)
    company_name = models.CharField(max_length=255)
    submission_data = models.JSONField(blank=True, null=True)
    matched_vendor_id = models.BigIntegerField(blank=True, null=True)
    matching_status = models.CharField(max_length=20, choices=MATCHING_STATUS_CHOICES, default='unmatched')
    created_at = models.DateTimeField(auto_now_add=True)
    matched_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.vendor_name} - {self.company_name}"
    
    class Meta:
        db_table = 'rfp_unmatched_vendors'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vendor_email']),
            models.Index(fields=['matching_status']),
        ]


class VendorInvitation(models.Model):
    """
    Model for vendor invitations
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
    
    # MULTI-TENANCY: Link vendor invitation to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_vendor_invitations', null=True, blank=True,
                               help_text="Tenant this vendor invitation belongs to")
    
    rfp = models.ForeignKey('RFP', on_delete=models.CASCADE, related_name='invitations')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True)
    vendor_email = models.EmailField(max_length=255, null=True, blank=True)
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
    is_matched_vendor = models.BooleanField(default=True)
    submission_source = models.CharField(max_length=10, choices=SUBMISSION_SOURCE_CHOICES, default='invited')
    utm_parameters = models.JSONField(null=True, blank=True)
    custom_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invitation {self.invitation_id} - {self.vendor_name} ({self.company_name})"
    
    class Meta:
        db_table = 'rfp_vendor_invitations'
        ordering = ['-created_at']


class RFPVendorSelection(models.Model):
    """
    Model for linking RFPs with selected vendors
    """
    selection_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link vendor selection to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_vendor_selections', null=True, blank=True,
                               help_text="Tenant this vendor selection belongs to")
    
    rfp = models.ForeignKey('RFP', on_delete=models.CASCADE, related_name='selected_vendors')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='rfp_selections')
    match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    selection_date = models.DateTimeField(auto_now_add=True)
    selected_by = models.IntegerField()
    invitation_sent = models.BooleanField(default=False)
    invitation_url = models.CharField(max_length=255, blank=True, null=True)
    invitation_sent_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.rfp} - {self.vendor}"
    
    class Meta:
        db_table = 'rfp_vendor_selections'
        unique_together = ('rfp', 'vendor')
        indexes = [
            models.Index(fields=['rfp']),
            models.Index(fields=['vendor']),
        ]


class RFPResponse(models.Model):
    """
    Model for storing RFP responses from vendors
    This is a minimal model that only includes fields that exist in the actual database
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
    
    # MULTI-TENANCY: Link RFP response to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_responses', null=True, blank=True,
                               help_text="Tenant this RFP response belongs to")
    
    vendor_id = models.BigIntegerField(null=True, blank=True)
    invitation_id = models.BigIntegerField(null=True, blank=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    
    # Document management
    response_documents = models.JSONField(null=True, blank=True)
    document_urls = models.JSONField(null=True, blank=True)
    
    # Financial information
    proposed_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Scoring
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commercial_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weighted_final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Evaluation
    evaluation_status = models.CharField(max_length=20, choices=EVALUATION_STATUS_CHOICES, default='DRAFT')
    auto_rejected = models.BooleanField(default=False)
    rejection_reason = models.TextField(null=True, blank=True)
    
    # Submission details
    submission_source = models.CharField(max_length=10, choices=SUBMISSION_SOURCE_CHOICES, default='invited')
    external_submission_data = models.JSONField(null=True, blank=True)
    draft_data = models.JSONField(null=True, blank=True)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    last_saved_at = models.DateTimeField(auto_now=True)
    
    # User tracking
    submitted_by = models.CharField(max_length=255)
    evaluated_by = models.IntegerField(null=True, blank=True)
    evaluation_date = models.DateTimeField(null=True, blank=True)
    evaluation_comments = models.TextField(null=True, blank=True)
    
    # Vendor contact information (direct fields for easier querying)
    org = models.CharField(max_length=255, null=True, blank=True)
    vendor_name = models.CharField(max_length=255, null=True, blank=True)
    contact_email = models.CharField(max_length=255, null=True, blank=True)
    contact_phone = models.CharField(max_length=50, null=True, blank=True)
    
    # Additional data fields
    proposal_data = models.JSONField(null=True, blank=True)
    submission_status = models.CharField(max_length=20, default='DRAFT')  # NOT NULL in database, default to DRAFT (cannot be null)
    submitted_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Foreign key to RFP
    rfp = models.ForeignKey('RFP', on_delete=models.CASCADE, related_name='responses')
    
    def __str__(self):
        return f"Response {self.response_id} - Vendor {self.vendor_id}"
    
    class Meta:
        db_table = 'rfp_responses'
        ordering = ['-submission_date']


class RFPAwardNotification(models.Model):
    """
    Model for tracking award notifications sent to vendors
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('winner', 'Winner'),
        ('participant_thanks', 'Participant Thanks'),
    ]
    
    NOTIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    # Primary key
    notification_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link award notification to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_award_notifications', null=True, blank=True,
                               help_text="Tenant this award notification belongs to")
    
    # Foreign key to RFP response
    response_id = models.BigIntegerField(db_index=True)  # FK to rfp_responses table
    
    # Notification details
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    recipient_email = models.CharField(max_length=255)
    notification_status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS_CHOICES, default='pending')
    
    # Timestamps
    sent_date = models.DateTimeField(null=True, blank=True)
    acknowledged_date = models.DateTimeField(null=True, blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    
    # Token for secure response
    accept_reject_token = models.CharField(max_length=255, null=True, blank=True)
    
    # Message content
    award_message = models.TextField(null=True, blank=True)
    next_steps = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)  # Temporarily disabled
    
    def __str__(self):
        return f"Award Notification {self.notification_id} - {self.recipient_email} ({self.notification_status})"
    
    class Meta:
        db_table = 'rfp_award_notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['response_id']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['notification_status']),
            models.Index(fields=['recipient_email']),
            models.Index(fields=['accept_reject_token']),
        ]


class RFPTypeCustomFields(models.Model):
    """
    Model for storing custom fields associated with RFP types
    """
    # Primary key
    rfp_type_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link RFP type custom fields to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='rfp_type_custom_fields', null=True, blank=True,
                               help_text="Tenant this RFP type custom fields belongs to")
    
    # RFP type name
    rfp_type = models.CharField(max_length=255)
    
    # Custom fields stored as JSON
    custom_fields = models.JSONField(null=True, blank=True)
    
    # Response fields stored as JSON
    response_fields = models.JSONField(null=True, blank=True)
    data_inventory = models.JSONField(null=True, blank=True, help_text="JSON mapping RFP type custom field labels to data types (personal, confidential, regular)")
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry', help_text="Data retention expiry date")
    
    def __str__(self):
        return f"RFP Type: {self.rfp_type} (ID: {self.rfp_type_id})"
    
    class Meta:
        db_table = 'rfp_type_custom_fields'
        ordering = ['rfp_type']
        indexes = [
            models.Index(fields=['rfp_type']),
        ]