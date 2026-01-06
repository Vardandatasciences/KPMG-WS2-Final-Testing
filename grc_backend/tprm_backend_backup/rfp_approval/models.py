from django.db import models
from django.utils import timezone


class ApprovalWorkflows(models.Model):
    """
    Model for approval workflows
    """
    WORKFLOW_TYPE_CHOICES = [
        ('MULTI_LEVEL', 'Multi Level'),
        ('MULTI_PERSON', 'Multi Person'),
    ]
    
    # Primary key
    workflow_id = models.CharField(max_length=50, primary_key=True)
    
    # Workflow details
    workflow_name = models.CharField(max_length=255)
    workflow_type = models.CharField(max_length=20, choices=WORKFLOW_TYPE_CHOICES)
    description = models.TextField()
    business_object_type = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_by = models.IntegerField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.workflow_name} ({self.workflow_type})"
    
    class Meta:
        db_table = 'approval_workflows'
        ordering = ['-created_at']


class ApprovalRequests(models.Model):
    """
    Model for approval requests
    """
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    # Primary key
    approval_id = models.CharField(max_length=50, primary_key=True)
    
    # Foreign key to workflow
    workflow_id = models.CharField(max_length=50)
    
    # Request details
    request_title = models.CharField(max_length=255)
    request_description = models.TextField()
    requester_id = models.IntegerField()
    requester_department = models.CharField(max_length=100)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    request_data = models.JSONField()
    overall_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Timeline
    submission_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.request_title} ({self.overall_status})"
    
    class Meta:
        db_table = 'approval_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workflow_id']),
            models.Index(fields=['requester_id']),
            models.Index(fields=['overall_status']),
            models.Index(fields=['priority']),
        ]


class ApprovalStages(models.Model):
    """
    Model for approval stages
    """
    STAGE_TYPE_CHOICES = [
        ('SEQUENTIAL', 'Sequential'),
        ('PARALLEL', 'Parallel'),
    ]
    
    STAGE_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('SKIPPED', 'Skipped'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Primary key
    stage_id = models.CharField(max_length=50, primary_key=True)
    
    # Foreign key to approval request
    approval_id = models.CharField(max_length=50)
    
    # Stage details
    stage_order = models.IntegerField()
    stage_name = models.CharField(max_length=255)
    stage_description = models.TextField()
    assigned_user_id = models.IntegerField()
    assigned_user_name = models.CharField(max_length=255)
    assigned_user_role = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    stage_type = models.CharField(max_length=20, choices=STAGE_TYPE_CHOICES, default='SEQUENTIAL')
    stage_status = models.CharField(max_length=15, choices=STAGE_STATUS_CHOICES, default='PENDING')
    
    # Timeline
    deadline_date = models.DateTimeField(null=True, blank=True)
    extended_deadline = models.DateTimeField(null=True, blank=True)
    extension_reason = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Response data
    response_data = models.JSONField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    escalation_level = models.IntegerField(default=0)
    is_mandatory = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.stage_name} - {self.stage_status}"
    
    class Meta:
        db_table = 'approval_stages'
        ordering = ['stage_order', 'stage_id']
        indexes = [
            models.Index(fields=['approval_id']),
            models.Index(fields=['assigned_user_id']),
            models.Index(fields=['stage_status']),
            models.Index(fields=['stage_order']),
        ]


class ApprovalComments(models.Model):
    """
    Model for approval comments
    """
    COMMENT_TYPE_CHOICES = [
        ('GENERAL', 'General'),
        ('REJECTION_REASON', 'Rejection Reason'),
        ('CLARIFICATION', 'Clarification'),
        ('APPROVAL_NOTE', 'Approval Note'),
    ]
    
    # Primary key
    comment_id = models.CharField(max_length=50, primary_key=True)
    
    # Foreign keys
    approval_id = models.CharField(max_length=50)
    stage_id = models.CharField(max_length=50, null=True, blank=True)
    parent_comment_id = models.CharField(max_length=50, null=True, blank=True)
    
    # Comment details
    comment_text = models.TextField()
    comment_type = models.CharField(max_length=20, choices=COMMENT_TYPE_CHOICES, default='GENERAL')
    commented_by = models.IntegerField()
    commented_by_name = models.CharField(max_length=255)
    is_internal = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.commented_by_name} - {self.comment_type}"
    
    class Meta:
        db_table = 'approval_comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['approval_id']),
            models.Index(fields=['stage_id']),
            models.Index(fields=['parent_comment_id']),
            models.Index(fields=['commented_by']),
        ]


class ApprovalRequestVersions(models.Model):
    """
    Model for approval request versions
    """
    VERSION_TYPE_CHOICES = [
        ('INITIAL', 'Initial'),
        ('REVISION', 'Revision'),
        ('CONSOLIDATION', 'Consolidation'),
        ('FINAL', 'Final'),
    ]
    
    # Primary key
    version_id = models.CharField(max_length=50, primary_key=True)
    
    # Foreign key to approval request
    approval_id = models.CharField(max_length=50)
    
    # Version details
    version_number = models.IntegerField()
    version_label = models.CharField(max_length=100)
    json_payload = models.JSONField()
    changes_summary = models.TextField()
    created_by = models.IntegerField()
    created_by_name = models.CharField(max_length=255)
    created_by_role = models.CharField(max_length=100)
    version_type = models.CharField(max_length=20, choices=VERSION_TYPE_CHOICES, default='INITIAL')
    parent_version_id = models.CharField(max_length=50, null=True, blank=True)
    is_current = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    change_reason = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Version {self.version_number} - {self.version_label}"
    
    class Meta:
        db_table = 'approval_request_versions'
        ordering = ['-version_number', '-created_at']
        indexes = [
            models.Index(fields=['approval_id']),
            models.Index(fields=['version_number']),
            models.Index(fields=['is_current']),
            models.Index(fields=['parent_version_id']),
        ]
