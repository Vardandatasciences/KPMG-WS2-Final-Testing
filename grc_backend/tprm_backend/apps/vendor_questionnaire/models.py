"""
Vendor Questionnaire Models - Maps to existing database tables
"""

from django.db import models
from tprm_backend.apps.vendor_core.models import VendorBaseModel, Vendors, Users, TempVendor, ExternalScreeningResult


class Questionnaires(VendorBaseModel):
    """Questionnaires mapping to existing questionnaires table"""
    
    # Use actual database column names (they match the user's schema!)
    questionnaire_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link questionnaire to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_questionnaires', null=True, blank=True,
                               help_text="Tenant this questionnaire belongs to")
    
    questionnaire_name = models.CharField(max_length=255)
    questionnaire_type = models.CharField(
        max_length=11,
        choices=[
            ('ONBOARDING', 'Onboarding'),
            ('ANNUAL', 'Annual'),
            ('INCIDENT', 'Incident'),
            ('CUSTOM', 'Custom'),
        ],
        blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)
    vendor_category_id = models.BigIntegerField(blank=True, null=True)
    vendor_id = models.BigIntegerField(blank=True, null=True)  # Column exists in database
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(
        max_length=8,
        choices=[
            ('DRAFT', 'Draft'),
            ('ACTIVE', 'Active'),
            ('ARCHIVED', 'Archived'),
        ],
        default='DRAFT'
    )
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = False  # Don't manage table creation
        db_table = 'questionnaires'
        verbose_name = 'Questionnaire'
        verbose_name_plural = 'Questionnaires'
        ordering = ['-created_at']  # Default ordering to fix pagination warning
    
    def __str__(self):
        return self.questionnaire_name or f"Questionnaire {self.questionnaire_id}"


class QuestionnaireQuestions(VendorBaseModel):
    """Questionnaire questions mapping to existing questionnaire_questions table"""
    
    # Use actual database column names (they match the user's schema!)
    question_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link questionnaire question to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='questionnaire_questions', null=True, blank=True,
                               help_text="Tenant this questionnaire question belongs to")
    
    questionnaire = models.ForeignKey(Questionnaires, models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(
        max_length=15,
        choices=[
            ('TEXT', 'Text'),
            ('MULTIPLE_CHOICE', 'Multiple Choice'),
            ('CHECKBOX', 'Checkbox'),
            ('RATING', 'Rating'),
            ('FILE_UPLOAD', 'File Upload'),
            ('DATE', 'Date'),
            ('NUMBER', 'Number'),
        ]
    )
    question_category = models.CharField(max_length=100, blank=True, null=True)
    is_required = models.BooleanField(default=False)
    display_order = models.IntegerField()
    scoring_weight = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    options = models.JSONField(blank=True, null=True)
    conditional_logic = models.JSONField(blank=True, null=True)
    help_text = models.TextField(blank=True, null=True)
    
    class Meta:
        managed = False  # Don't manage table creation
        db_table = 'questionnaire_questions'
        verbose_name = 'Questionnaire Question'
        verbose_name_plural = 'Questionnaire Questions'
        ordering = ['display_order', 'question_id']  # Stable ordering
    
    def __str__(self):
        return f"Q{self.display_order}: {self.question_text[:50]}..." if self.question_text else f"Question {self.question_id}"


class QuestionnaireResponses(VendorBaseModel):
    """Questionnaire responses mapping to existing questionnaire_responses table"""
    
    responseid = models.IntegerField(db_column='ResponseId', primary_key=True)
    
    # MULTI-TENANCY: Link questionnaire response to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='questionnaire_responses', null=True, blank=True,
                               help_text="Tenant this questionnaire response belongs to")
    
    questionnaireid = models.ForeignKey(Questionnaires, models.DO_NOTHING, db_column='QuestionnaireId', blank=True, null=True)
    vendorid = models.IntegerField(db_column='VendorId', blank=True, null=True)  # Reference to vendor
    responses = models.JSONField(db_column='Responses', blank=True, null=True)
    submittedat = models.DateTimeField(db_column='SubmittedAt', blank=True, null=True)
    submittedby = models.ForeignKey(Users, models.DO_NOTHING, db_column='SubmittedBy', blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'questionnaire_responses'
        unique_together = (('responseid', 'questionnaireid'),)
        verbose_name = 'Questionnaire Response'
        verbose_name_plural = 'Questionnaire Responses'
    
    def __str__(self):
        return f"Response {self.responseid} for Questionnaire {self.questionnaireid_id}"


class QuestionnaireAssignments(VendorBaseModel):
    """Questionnaire assignments table for tracking vendor assignments"""
    
    assignment_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link questionnaire assignment to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='questionnaire_assignments', null=True, blank=True,
                               help_text="Tenant this questionnaire assignment belongs to")
    
    temp_vendor = models.ForeignKey(TempVendor, models.CASCADE, related_name='questionnaire_assignments')
    questionnaire = models.ForeignKey(Questionnaires, models.CASCADE, related_name='assignments')
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('ASSIGNED', 'Assigned'),
            ('IN_PROGRESS', 'In Progress'),
            ('SUBMITTED', 'Submitted'),
            ('RESPONDED', 'Responded'),
            ('COMPLETED', 'Completed'),
            ('OVERDUE', 'Overdue'),
        ],
        default='ASSIGNED'
    )
    submission_date = models.DateTimeField(blank=True, null=True)
    completion_date = models.DateTimeField(blank=True, null=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    assigned_by = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = True  # We manage this table
        db_table = 'questionnaire_assignments'
        unique_together = (('temp_vendor', 'questionnaire'),)
        verbose_name = 'Questionnaire Assignment'
        verbose_name_plural = 'Questionnaire Assignments'
        ordering = ['-assigned_date', 'assignment_id']
    
    def __str__(self):
        return f"{self.temp_vendor.company_name} - {self.questionnaire.questionnaire_name}"


class QuestionnaireResponseSubmissions(VendorBaseModel):
    """Individual question responses for assignments"""
    
    response_id = models.BigAutoField(primary_key=True)
    assignment = models.ForeignKey(QuestionnaireAssignments, models.CASCADE, related_name='responses')
    question = models.ForeignKey(QuestionnaireQuestions, models.CASCADE, related_name='vendor_responses')
    vendor_response = models.TextField(blank=True, null=True)
    vendor_comment = models.TextField(blank=True, null=True)
    reviewer_comment = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    file_uploads = models.JSONField(blank=True, null=True)  # For file upload responses
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = True  # We manage this table
        db_table = 'questionnaire_response_submissions'
        unique_together = (('assignment', 'question'),)
        verbose_name = 'Questionnaire Response'
        verbose_name_plural = 'Questionnaire Responses'
        ordering = ['assignment', 'question__display_order', 'response_id']
    
    def __str__(self):
        return f"Response to Q{self.question.display_order} for {self.assignment.temp_vendor.company_name}"


class RFPResponses(VendorBaseModel):
    """RFP responses mapping to existing rfp_responses table"""
    
    response_id = models.BigAutoField(primary_key=True)
    
    # MULTI-TENANCY: Link RFP response to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.DO_NOTHING, db_column='TenantId', 
                               related_name='vendor_rfp_responses', null=True, blank=True,
                               help_text="Tenant this RFP response belongs to")
    
    rfp_id = models.BigIntegerField()
    vendor_id = models.BigIntegerField()
    invitation_id = models.BigIntegerField(blank=True, null=True)
    submission_date = models.DateTimeField(blank=True, null=True)
    response_documents = models.JSONField(blank=True, null=True)
    document_urls = models.JSONField(blank=True, null=True)
    proposed_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    technical_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    commercial_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    evaluation_status = models.CharField(
        max_length=20,
        choices=[
            ('SUBMITTED', 'Submitted'),
            ('UNDER_EVALUATION', 'Under Evaluation'),
            ('SHORTLISTED', 'Shortlisted'),
            ('REJECTED', 'Rejected'),
            ('AWARDED', 'Awarded'),
        ],
        default='SUBMITTED'
    )
    evaluated_by = models.IntegerField(blank=True, null=True)
    evaluation_date = models.DateTimeField(blank=True, null=True)
    evaluation_comments = models.TextField(blank=True, null=True)
    submitted_by = models.CharField(max_length=255, blank=True, null=True)
    proposal_data = models.JSONField(blank=True, null=True)
    external_submission_data = models.JSONField(blank=True, null=True)
    draft_data = models.JSONField(blank=True, null=True)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'rfp_responses'
        verbose_name = 'RFP Response'
        verbose_name_plural = 'RFP Responses'
        ordering = ['-submission_date']
    
    def __str__(self):
        return f"RFP Response {self.response_id} - Vendor {self.vendor_id}"


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

