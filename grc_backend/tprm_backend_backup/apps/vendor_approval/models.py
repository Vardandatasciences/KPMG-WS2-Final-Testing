"""
Vendor Approval Models - Maps to approval-related database tables
"""

from django.db import models
from tprm_backend.apps.vendor_core.models import VendorBaseModel
from tprm_backend.apps.vendor_questionnaire.models import QuestionnaireAssignments


class Users(VendorBaseModel):
    """Users table mapping to existing users table"""

    user_id = models.AutoField(primary_key=True, db_column='UserId')
    user_name = models.CharField(max_length=255, db_column='UserName')
    password = models.CharField(max_length=255, db_column='Password')
    created_at = models.DateTimeField(db_column='CreatedAt')
    updated_at = models.DateTimeField(db_column='UpdatedAt')
    email = models.CharField(max_length=100, db_column='Email', blank=True, null=True)
    first_name = models.CharField(max_length=45, db_column='FirstName', blank=True, null=True)
    last_name = models.CharField(max_length=45, db_column='LastName', blank=True, null=True)
    is_active = models.CharField(max_length=45, db_column='IsActive', blank=True, null=True)
    department_id = models.IntegerField(db_column='DepartmentId', blank=True, null=True)
    session_token = models.CharField(max_length=1045, db_column='session_token', blank=True, null=True)
    consent_accepted = models.CharField(max_length=1, db_column='consent_accepted', blank=True, null=True)
    license_key = models.CharField(max_length=255, db_column='license_key', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.user_name


class ApprovalWorkflows(VendorBaseModel):
    """Approval workflows mapping to existing approval_workflows table"""
    
    workflow_id = models.CharField(max_length=50, primary_key=True)
    workflow_name = models.CharField(max_length=255)
    workflow_type = models.CharField(
        max_length=20,
        choices=[
            ('MULTI_LEVEL', 'Multi Level'),
            ('MULTI_PERSON', 'Multi Person'),
        ]
    )
    description = models.TextField(blank=True, null=True)
    business_object_type = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(Users, models.DO_NOTHING, db_column='created_by', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'approval_workflows'
        verbose_name = 'Approval Workflow'
        verbose_name_plural = 'Approval Workflows'
    
    def __str__(self):
        return self.workflow_name


class ApprovalRequests(VendorBaseModel):
    """Approval requests mapping to existing approval_requests table"""
    
    approval_id = models.CharField(max_length=50, primary_key=True)
    workflow = models.ForeignKey(ApprovalWorkflows, models.DO_NOTHING, db_column='workflow_id', blank=True, null=True)
    request_title = models.CharField(max_length=255)
    request_description = models.TextField(blank=True, null=True)
    requester_id = models.ForeignKey(Users, models.DO_NOTHING, db_column='requester_id', blank=True, null=True)
    requester_department = models.CharField(max_length=100, blank=True, null=True)
    priority = models.CharField(
        max_length=10,
        choices=[
            ('LOW', 'Low'),
            ('MEDIUM', 'Medium'),
            ('HIGH', 'High'),
            ('URGENT', 'Urgent'),
        ],
        default='MEDIUM'
    )
    request_data = models.JSONField(blank=True, null=True)
    overall_status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Draft'),
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
            ('CANCELLED', 'Cancelled'),
            ('EXPIRED', 'Expired'),
        ],
        default='DRAFT'
    )
    submission_date = models.DateTimeField(blank=True, null=True)
    completion_date = models.DateTimeField(blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'approval_requests'
        verbose_name = 'Approval Request'
        verbose_name_plural = 'Approval Requests'
    
    def __str__(self):
        return f"{self.request_title} - {self.overall_status}"


class ApprovalStages(VendorBaseModel):
    """Approval stages mapping to existing approval_stages table"""
    
    stage_id = models.CharField(max_length=50, primary_key=True)
    approval = models.ForeignKey(ApprovalRequests, models.DO_NOTHING, db_column='approval_id', blank=True, null=True)
    stage_order = models.IntegerField()
    # New optional weightage column used primarily for MULTI_PERSON / response approval workflows
    weightage = models.IntegerField(blank=True, null=True, db_column='weightage')
    stage_name = models.CharField(max_length=255)
    stage_description = models.TextField(blank=True, null=True)
    assigned_user_id = models.ForeignKey(Users, models.DO_NOTHING, db_column='assigned_user_id', blank=True, null=True)
    assigned_user_name = models.CharField(max_length=255, blank=True, null=True)
    assigned_user_role = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    stage_type = models.CharField(
        max_length=20,
        choices=[
            ('SEQUENTIAL', 'Sequential'),
            ('PARALLEL', 'Parallel'),
        ],
        default='SEQUENTIAL'
    )
    stage_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
            ('SKIPPED', 'Skipped'),
            ('EXPIRED', 'Expired'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='PENDING'
    )
    deadline_date = models.DateTimeField(blank=True, null=True)
    extended_deadline = models.DateTimeField(blank=True, null=True)
    extension_reason = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    response_data = models.JSONField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    escalation_level = models.IntegerField(default=0)
    is_mandatory = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False
        db_table = 'approval_stages'
        verbose_name = 'Approval Stage'
        verbose_name_plural = 'Approval Stages'
    
    def __str__(self):
        return f"{self.stage_name} - {self.stage_status}"


class TempVendor(VendorBaseModel):
    """Temporary vendor data mapping to temp_vendor table"""
    
    id = models.BigAutoField(primary_key=True)
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
    
    def __str__(self):
        return f"{self.company_name} ({self.vendor_code})"


class TprmRisk(VendorBaseModel):
    """TPRM Risk mapping to tprm_risk table"""
    
    id = models.CharField(max_length=20, primary_key=True)
    vendor_id = models.BigIntegerField(blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    module_id = models.IntegerField(blank=True, null=True)
    likelihood = models.IntegerField(blank=True, null=True)
    impact = models.IntegerField(blank=True, null=True)
    score = models.IntegerField(blank=True, null=True)
    priority = models.CharField(max_length=20, blank=True, null=True)
    ai_explanation = models.TextField(blank=True, null=True)
    suggested_mitigations = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    assigned_to = models.IntegerField(blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    mitigated_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'tprm_risk'
        verbose_name = 'TPRM Risk'
        verbose_name_plural = 'TPRM Risks'
    
    def __str__(self):
        return f"{self.title} - {self.priority}"


class ApprovalRequestVersions(VendorBaseModel):
    """Approval request versions mapping to existing approval_request_versions table"""
    
    version_id = models.CharField(max_length=50, primary_key=True)
    approval = models.ForeignKey(ApprovalRequests, models.DO_NOTHING, db_column='approval_id', blank=True, null=True)
    version_number = models.IntegerField()
    version_label = models.CharField(max_length=100, blank=True, null=True)
    json_payload = models.JSONField(blank=True, null=True)
    changes_summary = models.TextField(blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    created_by_name = models.CharField(max_length=255, blank=True, null=True)
    created_by_role = models.CharField(max_length=100, blank=True, null=True)
    version_type = models.CharField(
        max_length=20,
        choices=[
            ('INITIAL', 'Initial'),
            ('REVISION', 'Revision'),
            ('CONSOLIDATION', 'Consolidation'),
            ('FINAL', 'Final'),
        ],
        default='INITIAL'
    )
    parent_version_id = models.CharField(max_length=50, blank=True, null=True)
    is_current = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    change_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'approval_request_versions'
        verbose_name = 'Approval Request Version'
        verbose_name_plural = 'Approval Request Versions'
    
    def __str__(self):
        return f"{self.approval.request_title if self.approval else 'Unknown'} - Version {self.version_number}"


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


class ExternalScreeningResults(VendorBaseModel):
    """External screening results mapping to external_screening_results table"""
    
    screening_id = models.BigAutoField(primary_key=True)
    vendor_id = models.BigIntegerField()
    screening_type = models.CharField(
        max_length=20,
        choices=[
            ('WORLDCHECK', 'WorldCheck'),
            ('OFAC', 'OFAC'),
            ('PEP', 'PEP'),
            ('SANCTIONS', 'Sanctions'),
            ('ADVERSE_MEDIA', 'Adverse Media'),
        ]
    )
    screening_date = models.DateTimeField()
    search_terms = models.JSONField(blank=True, null=True)
    total_matches = models.IntegerField(default=0)
    high_risk_matches = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('CLEAR', 'Clear'),
            ('POTENTIAL_MATCH', 'Potential Match'),
            ('CONFIRMED_MATCH', 'Confirmed Match'),
            ('UNDER_REVIEW', 'Under Review'),
        ]
    )
    last_updated = models.DateTimeField()
    reviewed_by = models.IntegerField(blank=True, null=True)
    review_date = models.DateTimeField(blank=True, null=True)
    review_comments = models.TextField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'external_screening_results'
        verbose_name = 'External Screening Result'
        verbose_name_plural = 'External Screening Results'
    
    def __str__(self):
        return f"{self.screening_type} - {self.vendor_id} - {self.status}"


class ScreeningMatches(VendorBaseModel):
    """Screening matches mapping to screening_matches table"""
    
    match_id = models.BigAutoField(primary_key=True)
    screening_id = models.BigIntegerField()
    match_type = models.CharField(max_length=100, blank=True, null=True)
    match_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    match_details = models.JSONField(blank=True, null=True)
    is_false_positive = models.BooleanField(default=False)
    resolution_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('CLEARED', 'Cleared'),
            ('ESCALATED', 'Escalated'),
            ('BLOCKED', 'Blocked'),
        ],
        default='PENDING'
    )
    resolution_notes = models.TextField(blank=True, null=True)
    resolved_by = models.IntegerField(blank=True, null=True)
    resolved_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'screening_matches'
        verbose_name = 'Screening Match'
        verbose_name_plural = 'Screening Matches'
    
    def __str__(self):
        return f"Match {self.match_id} - {self.match_type} - {self.resolution_status}"
