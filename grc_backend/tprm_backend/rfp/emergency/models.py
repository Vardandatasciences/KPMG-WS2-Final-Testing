from django.db import models
from django.utils import timezone
import json
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin


class EmergencyProcurement(TPRMEncryptedFieldsMixin, models.Model):
    """Model for Emergency Procurement data"""
    
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
    
    URGENCY_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    emergency_id = models.BigAutoField(primary_key=True, auto_created=True)
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='emergency_procurements', null=True, blank=True)
    emergency_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    emergency_title = models.CharField(max_length=255)
    description = models.TextField()
    emergency_type = models.TextField()
    category = models.CharField(max_length=100, null=True, blank=True)
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='USD')
    budget_range_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    budget_range_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    submission_deadline = models.DateTimeField(null=True, blank=True)
    evaluation_period_end = models.DateField(null=True, blank=True)
    award_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_by = models.IntegerField()
    approved_by = models.IntegerField(null=True, blank=True)
    primary_reviewer_id = models.IntegerField(null=True, blank=True)
    executive_reviewer_id = models.IntegerField(null=True, blank=True)
    version_number = models.IntegerField(default=1)
    auto_approve = models.BooleanField(default=False)
    allow_late_submissions = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approval_workflow_id = models.CharField(max_length=50, null=True, blank=True)
    evaluation_method = models.CharField(max_length=20, choices=EVALUATION_METHOD_CHOICES, default='weighted_scoring')
    criticality_level = models.CharField(max_length=10, choices=CRITICALITY_LEVEL_CHOICES, default='medium')
    geographical_scope = models.CharField(max_length=255, null=True, blank=True)
    compliance_requirements = models.JSONField(null=True, blank=True)
    custom_fields = models.JSONField(null=True, blank=True)
    data_inventory = models.JSONField(null=True, blank=True)
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry')
    final_evaluation_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    award_decision_date = models.DateTimeField(null=True, blank=True)
    award_justification = models.TextField(null=True, blank=True)
    documents = models.JSONField(null=True, blank=True)
    # Emergency-specific fields
    emergency_justification = models.TextField()
    emergency_type_category = models.CharField(max_length=100, null=True, blank=True)
    urgency_level = models.CharField(max_length=20, choices=URGENCY_LEVEL_CHOICES, default='HIGH')
    required_delivery_date = models.DateField(null=True, blank=True)
    impact_description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.emergency_title} ({self.emergency_number})"
    
    def save(self, *args, **kwargs):
        if isinstance(self.emergency_number, str):
            self.emergency_number = self.emergency_number.strip()
            if not self.emergency_number:
                self.emergency_number = None
        
        if not self.emergency_number and not self.pk:
            today = timezone.now()
            prefix = f"EMERGENCY-{today.year}-{today.month:02d}-"
            last_emergency = EmergencyProcurement.objects.filter(emergency_number__startswith=prefix).order_by('-emergency_number').first()
            if last_emergency:
                try:
                    last_number = int(last_emergency.emergency_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            self.emergency_number = f"{prefix}{new_number:04d}"
        
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
        db_table = 'emergency_procurements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['emergency_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
            models.Index(fields=['tenant']),
            models.Index(fields=['urgency_level']),
            models.Index(fields=['created_at']),
        ]


class EmergencyEvaluationCriteria(models.Model):
    """Model for Emergency Procurement evaluation criteria"""
    EVALUATION_TYPE_CHOICES = [
        ('scoring', 'Scoring'),
        ('binary', 'Binary'),
        ('narrative', 'Narrative'),
    ]
    
    criteria_id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='emergency_evaluation_criteria', null=True, blank=True)
    emergency = models.ForeignKey(EmergencyProcurement, on_delete=models.CASCADE, related_name='evaluation_criteria', db_column='emergency_id')
    criteria_name = models.CharField(max_length=255)
    criteria_description = models.TextField()
    weight_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    evaluation_type = models.CharField(max_length=10, choices=EVALUATION_TYPE_CHOICES, default='scoring')
    min_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    median_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_mandatory = models.BooleanField(default=False)
    veto_enabled = models.BooleanField(default=False)
    veto_threshold = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    min_word_count = models.IntegerField(null=True, blank=True)
    expected_boolean_answer = models.CharField(max_length=3, null=True, blank=True)
    display_order = models.IntegerField(default=0)
    created_by = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add=True)
    data_inventory = models.JSONField(null=True, blank=True)
    retentionExpiry = models.DateField(blank=True, null=True, db_column='retentionExpiry')
    
    def __str__(self):
        return f"{self.criteria_name} - {self.weight_percentage}%"
    
    class Meta:
        db_table = 'emergency_evaluation_criteria'
        ordering = ['display_order', 'criteria_id']
        indexes = [
            models.Index(fields=['emergency']),
            models.Index(fields=['is_mandatory']),
            models.Index(fields=['tenant']),
        ]
