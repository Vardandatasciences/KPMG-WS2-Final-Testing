"""
Django models for BCP/DRP system
Traditional Django ORM models representing all entities in the system
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import json


class Dropdown(models.Model):
    """Dropdown values model for various system dropdowns"""
    id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=45)
    value = models.CharField(max_length=45)

    class Meta:
        db_table = 'dropdown'
        ordering = ['source', 'value']

    def __str__(self):
        return f"{self.source}: {self.value}"


class Plan(models.Model):
    """BCP/DRP Plan model"""
    
    CRITICALITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('OCR_COMPLETED', 'OCR Completed'),
        ('ASSIGNED_FOR_EVALUATION', 'Assigned for Evaluation'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REVISION_REQUESTED', 'Revision Requested'),
    ]

    plan_id = models.IntegerField(primary_key=True)
    vendor_id = models.IntegerField()
    strategy_id = models.IntegerField()
    strategy_name = models.CharField(max_length=255)
    plan_type = models.CharField(max_length=45)  # Increased length to accommodate dynamic values
    plan_name = models.CharField(max_length=255)
    version = models.CharField(max_length=32, default='1.0')
    document_date = models.DateField(null=True, blank=True)
    file_uri = models.CharField(max_length=1024)
    mime_type = models.CharField(max_length=128, blank=True, null=True)
    sha256_checksum = models.CharField(max_length=64, blank=True, null=True)
    size_bytes = models.IntegerField(null=True, blank=True)
    plan_scope = models.TextField(blank=True, null=True)
    criticality = models.CharField(max_length=20, choices=CRITICALITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='SUBMITTED')
    
    # OCR related fields
    ocr_extracted = models.BooleanField(default=False)
    ocr_by_user_id = models.IntegerField(null=True, blank=True)
    ocr_extracted_at = models.DateTimeField(null=True, blank=True)
    ocr_extracted_data = models.JSONField(default=dict, blank=True, null=True)
    
    # Approval related fields
    approved_by = models.IntegerField(null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Submission tracking
    submitted_by = models.IntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bcp_drp_plans'
        ordering = ['plan_id']
    @property
    def id(self):
        """Alias for plan_id to maintain compatibility with code expecting .id"""
        return self.plan_id
    def __str__(self):
        return f"{self.plan_name} ({self.plan_type}) - {self.strategy_name}"

     
class BcpDetails(models.Model):
    """BCP extracted details model"""
    plan_id = models.IntegerField(primary_key=True)
    
    # Purpose and Scope
    purpose_scope = models.TextField(blank=True, null=True)
    regulatory_references = models.JSONField(default=list, blank=True)
    
    # Critical Services and Dependencies
    critical_services = models.JSONField(default=list, blank=True)
    dependencies_internal = models.JSONField(default=list, blank=True)
    dependencies_external = models.JSONField(default=list, blank=True)
    
    # Risk and Business Impact
    risk_assessment_summary = models.TextField(blank=True, null=True)
    bia_summary = models.TextField(blank=True, null=True)
    
    # Recovery Objectives
    rto_targets = models.JSONField(default=dict, blank=True)
    rpo_targets = models.JSONField(default=dict, blank=True)
    
    # Incident Management
    incident_types = models.JSONField(default=list, blank=True)
    alternate_work_locations = models.JSONField(default=list, blank=True)
    
    # Communication Plans
    communication_plan_internal = models.TextField(blank=True, null=True)
    communication_plan_bank = models.TextField(blank=True, null=True)
    
    # Roles and Responsibilities
    roles_responsibilities = models.JSONField(default=list, blank=True)
    
    # Training and Testing
    training_testing_schedule = models.TextField(blank=True, null=True)
    maintenance_review_cycle = models.TextField(blank=True, null=True)
    
    # Extraction metadata
    extracted_at = models.DateTimeField(auto_now_add=True)
    extractor_version = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        db_table = 'bcp_extracted_details'

    def __str__(self):
        return f"BCP Details for Plan {self.plan_id}"


class DrpDetails(models.Model):
    """DRP extracted details model"""
    plan_id = models.IntegerField(primary_key=True)
    
    # Purpose and Scope
    purpose_scope = models.TextField(blank=True, null=True)
    regulatory_references = models.JSONField(default=list, blank=True)
    
    # Critical Systems and Applications
    critical_systems = models.JSONField(default=list, blank=True)
    critical_applications = models.JSONField(default=list, blank=True)
    databases_list = models.JSONField(default=list, blank=True)
    supporting_infrastructure = models.JSONField(default=list, blank=True)
    third_party_services = models.JSONField(default=list, blank=True)
    
    # Recovery Objectives
    rto_targets = models.JSONField(default=dict, blank=True)
    rpo_targets = models.JSONField(default=dict, blank=True)
    
    # Disaster Scenarios
    disaster_scenarios = models.JSONField(default=list, blank=True)
    disaster_declaration_process = models.TextField(blank=True, null=True)
    
    # Backup and Recovery
    data_backup_strategy = models.TextField(blank=True, null=True)
    recovery_site_details = models.TextField(blank=True, null=True)
    failover_procedures = models.TextField(blank=True, null=True)
    failback_procedures = models.TextField(blank=True, null=True)
    network_recovery_steps = models.TextField(blank=True, null=True)
    application_restoration_order = models.JSONField(default=list, blank=True)
    
    # Testing and Maintenance
    testing_validation_schedule = models.TextField(blank=True, null=True)
    maintenance_review_cycle = models.TextField(blank=True, null=True)
    
    # Extraction metadata
    extracted_at = models.DateTimeField(auto_now_add=True)
    extractor_version = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        db_table = 'drp_extracted_details'

    def __str__(self):
        return f"DRP Details for Plan {self.plan_id}"


class Evaluation(models.Model):
    """Plan evaluation model"""
    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('CLOSED', 'Closed'),
    ]
    

    evaluation_id = models.IntegerField(primary_key=True)
    plan_id = models.IntegerField()
    
    # Assignment
    assigned_to_user_id = models.IntegerField()
    assigned_by_user_id = models.IntegerField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    
    # Evaluation lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by_user_id = models.IntegerField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Scores
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                      validators=[MinValueValidator(0), MaxValueValidator(100)])
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                      validators=[MinValueValidator(0), MaxValueValidator(100)])
    coverage_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                       validators=[MinValueValidator(0), MaxValueValidator(100)])
    recovery_capability_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                                  validators=[MinValueValidator(0), MaxValueValidator(100)])
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                         validators=[MinValueValidator(0), MaxValueValidator(100)])
    weighted_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Detail
    criteria_json = models.JSONField(default=dict, blank=True)
    evaluator_comments = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'bcp_drp_evaluations'
        ordering = ['evaluation_id']

    def __str__(self):
        return f"Evaluation {self.evaluation_id} for Plan {self.plan_id}"


class Questionnaire(models.Model):
    """Test questionnaire model"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('IN_REVIEW', 'In Review'),
        ('APPROVED', 'Approved'),
        ('ARCHIVED', 'Archived'),
    ]

    questionnaire_id = models.AutoField(primary_key=True)
    plan_id = models.IntegerField(null=True, blank=True)
    version = models.CharField(max_length=16, default='1.0')
    previous_questionnaire_id = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    plan_type = models.CharField(max_length=45)  # Increased length to accommodate dynamic values
    created_by_user_id = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    reviewer_user_id = models.IntegerField(null=True, blank=True)
    reviewer_comment = models.TextField(blank=True, null=True)
    approved_by_user_id = models.IntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'test_questionnaires'
        ordering = ['questionnaire_id']

    def __str__(self):
        return f"{self.title} v{self.version}"


class Question(models.Model):
    """Test question model"""
    ANSWER_TYPE_CHOICES = [
        ('TEXT', 'Text'),
        ('YES_NO', 'Yes/No'),
        ('MULTIPLE_CHOICE', 'Multiple Choice'),
    ]

    question_id = models.IntegerField(primary_key=True)
    questionnaire_id = models.IntegerField()
    seq_no = models.IntegerField()
    question_text = models.TextField()
    answer_type = models.CharField(max_length=50, choices=ANSWER_TYPE_CHOICES)  # Increased from 20 to 50
    is_required = models.BooleanField(default=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'test_questions'
        ordering = ['questionnaire_id', 'seq_no']

    def __str__(self):
        return f"Q{self.seq_no}: {self.question_text[:50]}..."


class TestAssignmentsResponses(models.Model):
    """
    Test assignments responses model - consolidated table for assignments, responses, and answers.
    
    This table consolidates the functionality of both test_assignments_responses and test_answers tables
    to eliminate redundancy. Each record represents:
    - An assignment of a questionnaire to a user for a specific plan
    - The answer to a specific question within that questionnaire
    
    Key relationships:
    - questionnaire_id: Links to test_questionnaires
    - question_id: Links to test_questions  
    - plan_id: Links to the BCP/DRP plan being tested
    """
    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    OWNER_DECISION_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REWORK_REQUESTED', 'Rework Requested'),
    ]
    
    RESPONSE_STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
    ]

    assignment_response_id = models.BigAutoField(primary_key=True)
    plan_id = models.BigIntegerField()
    questionnaire_id = models.BigIntegerField()
    question_id = models.IntegerField()  # NEW: Links to specific question (requires DB migration)
    assigned_to_user_id = models.BigIntegerField()
    assigned_by_user_id = models.BigIntegerField()
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    owner_decision = models.CharField(max_length=20, choices=OWNER_DECISION_CHOICES, default='PENDING')
    owner_comment = models.TextField(blank=True, null=True)
    response_status = models.CharField(max_length=20, choices=RESPONSE_STATUS_CHOICES, default='IN_PROGRESS')
    
    # Answer fields - all answers stored in JSON format in answer_text
    answer_text = models.TextField(blank=True, null=True)  # JSON data containing questions and answers
    reason_comment = models.TextField(blank=True, null=True)  # mandatory validation/reason
    evidence_uri = models.CharField(max_length=1024, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'test_assignments_responses'
        ordering = ['assignment_response_id']

    def __str__(self):
        return f"Assignment Response {self.assignment_response_id} for Plan {self.plan_id} - Question {self.question_id}"


class BcpDrpApprovals(models.Model):
    """BCP/DRP Approvals model for workflow management"""
    OBJECT_TYPE_CHOICES = [
        ('PLAN EVALUATION', 'Plan Evaluation'),
        ('NEW QUESTIONNAIRE', 'New Questionnaire'),
        ('QUESTIONNAIRE RESPONSE', 'Questionnaire Response'),
    ]
    
    STATUS_CHOICES = [
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMMENTED', 'Commented'),
        ('SKIPPED', 'Skipped'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    approval_id = models.AutoField(primary_key=True)
    workflow_id = models.IntegerField()
    workflow_name = models.CharField(max_length=255)
    assigner_id = models.IntegerField()
    assigner_name = models.CharField(max_length=255)
    assignee_id = models.IntegerField()
    assignee_name = models.CharField(max_length=255)
    object_type = models.CharField(max_length=45, choices=OBJECT_TYPE_CHOICES)
    object_id = models.IntegerField()
    plan_type = models.CharField(max_length=45)  # Increased length to accommodate dynamic values
    assigned_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ASSIGNED')
    comment_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bcp_drp_approvals'
        ordering = ['approval_id']

    def __str__(self):
        return f"Approval {self.approval_id}: {self.workflow_name} - {self.assignee_name}"


class Users(models.Model):
    """Users table model"""
    user_id = models.AutoField(primary_key=True, db_column='UserId')
    user_name = models.CharField(max_length=255, db_column='UserName')
    password = models.CharField(max_length=255, db_column='Password')
    created_at = models.DateTimeField(auto_now_add=True, db_column='CreatedAt')
    updated_at = models.DateTimeField(auto_now=True, db_column='UpdatedAt')
    email = models.CharField(max_length=100, db_column='Email')
    first_name = models.CharField(max_length=45, db_column='FirstName')
    last_name = models.CharField(max_length=45, db_column='LastName')
    is_active = models.CharField(max_length=45, default='Y', db_column='IsActive')
    department_id = models.IntegerField(null=True, blank=True, db_column='DepartmentId')
    session_token = models.CharField(max_length=1045, blank=True, null=True, db_column='session_token')
    consent_accepted = models.CharField(max_length=1, default='N', db_column='consent_accepted')
    license_key = models.CharField(max_length=255, blank=True, null=True, db_column='license_key')

    class Meta:
        db_table = 'users'
        ordering = ['user_id']

    def __str__(self):
        return f"{self.user_name} ({self.first_name} {self.last_name})"

class QuestionnaireTemplate(models.Model):
    """Unified Questionnaire Template model for all modules"""
    TEMPLATE_TYPE_CHOICES = [
        ('STATIC', 'Static'),
        ('DYNAMIC', 'Dynamic'),
        ('ASSESSMENT', 'Assessment'),
        ('EVALUATION', 'Evaluation'),
        ('TEST', 'Test'),
    ]
   
    MODULE_TYPE_CHOICES = [
        ('VENDOR', 'Vendor'),
        ('CONTRACT', 'Contract'),
        ('PLANS', 'Plans'),
        ('SLA', 'Service Level Agreement'),
        ('AUDIT', 'Audit'),
        ('GENERAL', 'General'),
    ]
   
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('IN_REVIEW', 'In Review'),
        ('APPROVED', 'Approved'),
        ('ARCHIVED', 'Archived'),
        ('DEPRECATED', 'Deprecated'),
    ]
   
    # Primary Key
    template_id = models.AutoField(primary_key=True)
   
    # Basic Information
    template_name = models.CharField(max_length=255)
    template_description = models.TextField(blank=True, null=True)
    template_version = models.CharField(max_length=20, default='1.0')
   
    # Template Type & Classification
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
   
    # Questions Data (JSON Array)
    template_questions_json = models.JSONField(default=list)
    """
    JSON Structure Example:
    [
        {
            "question_id": 1,
            "questionnaire_id": null,
            "display_order": 1,
            "question_text": "Question text here",
            "question_category": "Security",
            "answer_type": "TEXT|TEXTAREA|NUMBER|BOOLEAN|MULTIPLE_CHOICE|CHECKBOX|RATING|SCALE|DATE|FILE_UPLOAD",
            "is_required": true,
            "weightage": 10.0,
            "metric_name": "Security Score",
            "term_id": null,
            "allow_document_upload": false,
            "options": ["Option 1", "Option 2"],
            "help_text": "Help text here",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
    """
   
    # Module Association
    module_type = models.CharField(max_length=20, choices=MODULE_TYPE_CHOICES)
    module_subtype = models.CharField(max_length=50, blank=True, null=True)
   
    # Workflow & Approval
    approval_required = models.BooleanField(default=False)
   
    # Assignment
    assigner_id = models.IntegerField(null=True, blank=True)
    assignee_id = models.IntegerField(null=True, blank=True)
   
    # Status & Lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    is_active = models.BooleanField(default=True)
    is_template = models.BooleanField(default=True)
   
    # Audit Fields
    created_by = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    class Meta:
        db_table = 'questionnaire_templates'
        ordering = ['template_id']
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['module_type']),
            models.Index(fields=['module_subtype']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_template']),
            models.Index(fields=['created_at']),
        ]
   
    def __str__(self):
        return f"{self.template_name} v{self.template_version} ({self.module_type})"
