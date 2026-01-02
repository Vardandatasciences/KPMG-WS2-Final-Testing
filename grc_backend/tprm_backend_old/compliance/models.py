from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Framework(models.Model):
    FrameworkId = models.AutoField(primary_key=True)
    FrameworkName = models.CharField(max_length=255)
    CurrentVersion = models.FloatField()
    FrameworkDescription = models.TextField()
    EffectiveDate = models.DateField()
    CreatedByName = models.CharField(max_length=255)
    CreatedByDate = models.DateField()
    Category = models.CharField(max_length=100)
    DocURL = models.CharField(max_length=255, blank=True, null=True)
    Identifier = models.CharField(max_length=45, blank=True, null=True)
    StartDate = models.DateField(blank=True, null=True)
    EndDate = models.DateField(blank=True, null=True)
    Status = models.CharField(max_length=45)
    ActiveInactive = models.CharField(max_length=45)
    Reviewer = models.CharField(max_length=255, blank=True, null=True)
    InternalExternal = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        db_table = 'frameworks'

    def __str__(self):
        return f"{self.FrameworkName} (v{self.CurrentVersion})"

class ComplianceMapping(models.Model):
    AUDIT_FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
    ]

    mapping_id = models.BigAutoField(primary_key=True)
    sla_id = models.BigIntegerField()
    framework_id = models.IntegerField()
    compliance_status = models.CharField(max_length=50, default='Compliant')
    compliance_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)]
    )
    last_audited = models.DateField(blank=True, null=True)
    next_audit_due = models.DateField(blank=True, null=True)
    assigned_auditor = models.CharField(max_length=255, blank=True, null=True)
    audit_frequency = models.CharField(
        max_length=20, 
        choices=AUDIT_FREQUENCY_CHOICES, 
        default='MONTHLY'
    )
    compliance_version = models.CharField(max_length=50)
    compliance_description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'compliance_mapping'
        unique_together = ['sla_id', 'framework_id']

    def __str__(self):
        return f"SLA {self.sla_id} - Framework {self.framework_id} ({self.compliance_status})"