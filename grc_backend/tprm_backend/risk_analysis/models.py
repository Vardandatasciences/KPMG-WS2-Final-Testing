from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from tprm_backend.utils.encrypted_fields_mixin import TPRMEncryptedFieldsMixin

# Removed TPRMModule and ModuleData models - using entity-data-row approach


class Risk(TPRMEncryptedFieldsMixin, models.Model):
    """Risk prediction model"""
    PRIORITY_CHOICES = [
        ('Critical', 'Critical'),
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Mitigated', 'Mitigated'),
        ('Closed', 'Closed'),
        ('Acknowledged', 'Acknowledged'),
    ]
    
    RISK_TYPE_CHOICES = [
        ('Inherent', 'Inherent'),
        ('Emerging', 'Emerging'),
        ('Current', 'Current'),
        ('Residual', 'Residual'),
        ('Accepted', 'Accepted'),
    ]
    
    id = models.CharField(max_length=20, primary_key=True, help_text="Risk ID format: R-XXXX")
    
    # MULTI-TENANCY: Link risk to tenant
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE, db_column='TenantId', 
                               related_name='risks', null=True, blank=True,
                               help_text="Tenant this risk belongs to")
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    # Removed module_id - using entity-data-row approach
    
    # Risk scoring
    likelihood = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Likelihood of risk occurring (1-5 scale)"
    )
    impact = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Impact of risk (1-5 scale)"
    )
    exposure_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Exposure rating - scope of organizational vulnerability (1-5 scale)",
        default=3
    )
    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Calculated risk score (0-100)"
    )
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    
    # AI-generated content
    ai_explanation = models.TextField(help_text="AI-generated explanation of the risk")
    suggested_mitigations = models.JSONField(default=list, blank=True, help_text="List of suggested mitigations")
    
    # Source tracking for entity-data-row approach
    entity = models.CharField(max_length=100, null=True, blank=True, help_text="Source entity/module name (e.g., vendor_management, bcp_drp_module)")
    data = models.CharField(max_length=100, null=True, blank=True, help_text="Source table/data type (e.g., bcp_drp_plans, vendor_profiles)")
    row = models.CharField(max_length=50, null=True, blank=True, help_text="Source row identifier/primary key")
    
    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    risk_type = models.CharField(max_length=20, choices=RISK_TYPE_CHOICES, default='Current', help_text="Type of risk assessment")
    assigned_to = models.IntegerField(null=True, blank=True)  # Foreign key to User table
    created_by = models.IntegerField(null=True, blank=True)   # Foreign key to User table
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    mitigated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'risk_tprm'  # Use your existing table name
        verbose_name = 'Risk'
        verbose_name_plural = 'Risks'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.id} - {self.title}"
    
    def save(self, *args, **kwargs):
        # Generate risk ID if not provided
        if not self.id:
            last_risk = Risk.objects.order_by('-id').first()
            if last_risk:
                try:
                    last_number = int(last_risk.id.split('-')[1])
                    new_number = last_number + 1
                except (IndexError, ValueError):
                    new_number = 1000
            else:
                new_number = 1000
            self.id = f"R-{new_number:04d}"
        
        # Calculate score if not provided
        if not self.score:
            # New formula: Likelihood × Impact × Exposure × 1.33
            self.score = int(self.likelihood * self.impact * self.exposure_rating * 1.33)
            # Ensure it stays within 0-100 range
            self.score = min(100, self.score)
        
        # Set priority based on score
        if not self.priority:
            if self.score >= 80:
                self.priority = 'Critical'
            elif self.score >= 60:
                self.priority = 'High'
            elif self.score >= 40:
                self.priority = 'Medium'
            else:
                self.priority = 'Low'
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_heatmap_data(cls, module_name=None, tenant_id=None):
        """
        Dynamically generate heatmap data from risk records
        
        Args:
            module_name: Optional module name to filter by (not used for now)
            tenant_id: Optional tenant_id to filter by (MULTI-TENANCY)
            
        Returns:
            List of heatmap data dictionaries
        """
        # MULTI-TENANCY: Filter by tenant if provided
        if tenant_id:
            from django.db.models import Q
            # Include records with matching tenant_id OR NULL tenant_id (for backward compatibility)
            queryset = cls.objects.filter(Q(tenant_id=tenant_id) | Q(tenant_id__isnull=True))
        else:
            queryset = cls.objects.all()
        # Module filtering disabled for now since we're using entity-data-row approach
        
        # Group risks by likelihood and impact ranges
        heatmap_data = {}
        
        for risk in queryset:
            # Create likelihood range
            if risk.likelihood <= 2:
                likelihood_range = "1-2"
            elif risk.likelihood <= 4:
                likelihood_range = "3-4"
            else:
                likelihood_range = "5"
            
            # Create impact range
            if risk.impact <= 2:
                impact_range = "1-2"
            elif risk.impact <= 4:
                impact_range = "3-4"
            else:
                impact_range = "5"
            
            # Use a simple key since we're not using modules anymore
            key = (likelihood_range, impact_range)
            
            if key not in heatmap_data:
                heatmap_data[key] = {
                    'likelihood_range': likelihood_range,
                    'impact_range': impact_range,
                    'risk_count': 0,
                    'total_score': 0
                }
            
            heatmap_data[key]['risk_count'] += 1
            heatmap_data[key]['total_score'] += risk.score
        
        # Calculate averages and format data
        result = []
        for data in heatmap_data.values():
            data['average_score'] = data['total_score'] / data['risk_count'] if data['risk_count'] > 0 else 0
            data['module_name'] = 'All'  # Since we're not using modules
            data['module_display_name'] = 'All Modules'
            # Remove total_score from the result
            del data['total_score']
            result.append(data)
        
        return result
