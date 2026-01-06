from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    """Model for storing document metadata"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('DELETED', 'Deleted'),
        ('QUARANTINED', 'Quarantined'),
    ]
    
    DocumentId = models.BigAutoField(primary_key=True)
    ModuleId = models.IntegerField(default=1)
    Title = models.CharField(max_length=255)
    Description = models.TextField(blank=True, null=True)
    OriginalFilename = models.CharField(max_length=255)
    DocumentLink = models.CharField(max_length=2048, blank=True, null=True)
    Category = models.CharField(max_length=100, blank=True, null=True)
    Department = models.CharField(max_length=100, blank=True, null=True)
    DocType = models.CharField(max_length=50, blank=True, null=True)
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    CreatedBy = models.IntegerField(default=1)  # Simple int field, not foreign key
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-CreatedAt']
    
    def __str__(self):
        return f"{self.Title} ({self.OriginalFilename})"


class OcrResult(models.Model):
    """Model for storing OCR processing results"""
    
    OcrResultId = models.BigAutoField(primary_key=True)
    DocumentId = models.BigIntegerField()  # Simple integer, not foreign key
    VersionId = models.BigIntegerField(default=1)
    OcrText = models.TextField()
    OcrLanguage = models.CharField(max_length=20, default='en')
    OcrConfidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    OcrEngine = models.CharField(max_length=100, default='Tesseract')
    CreatedAt = models.DateTimeField(auto_now_add=True)
    ocr_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'ocr_results'
        ordering = ['-CreatedAt']
    
    def __str__(self):
        return f"OCR Result for Document ID {self.DocumentId}"


class ExtractedData(models.Model):
    """Model for storing AI-extracted structured data from documents"""
    
    ExtractedDataId = models.BigAutoField(primary_key=True)
    DocumentId_id = models.BigIntegerField()  # Match actual database column name
    OcrResultId_id = models.BigIntegerField()  # Match actual database column name
    
    # SLA-specific fields
    sla_name = models.CharField(max_length=255, blank=True, null=True)
    vendor_id = models.CharField(max_length=100, blank=True, null=True)
    contract_id = models.CharField(max_length=100, blank=True, null=True)
    sla_type = models.CharField(max_length=100, blank=True, null=True)
    effective_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, default='PENDING')
    business_service_impacted = models.TextField(blank=True, null=True)
    reporting_frequency = models.CharField(max_length=50, default='monthly')
    baseline_period = models.CharField(max_length=100, blank=True, null=True)
    improvement_targets = models.JSONField(default=dict, blank=True)
    penalty_threshold = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    credit_threshold = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    measurement_methodology = models.TextField(blank=True, null=True)
    exclusions = models.TextField(blank=True, null=True)
    force_majeure_clauses = models.TextField(blank=True, null=True)
    compliance_framework = models.CharField(max_length=255, blank=True, null=True)
    audit_requirements = models.TextField(blank=True, null=True)
    document_versioning = models.CharField(max_length=50, blank=True, null=True)
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    priority = models.CharField(max_length=50, blank=True, null=True)
    approval_status = models.CharField(max_length=50, default='PENDING')
    
    # Store metrics as JSON
    metrics = models.JSONField(default=list, blank=True)
    
    # Additional fields for flexibility
    raw_extracted_data = models.JSONField(default=dict, blank=True)
    extraction_confidence = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    extraction_method = models.CharField(max_length=100, default='AI_LLAMA')
    
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'extracted_data'
        ordering = ['-CreatedAt']
    
    def __str__(self):
        return f"Extracted Data for {self.DocumentId.Title}"

