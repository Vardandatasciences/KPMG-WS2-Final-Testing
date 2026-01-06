from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

# Removed TPRMModule and ModuleData models - using entity-data-row approach


class Risk(models.Model):
    """Risk TPRM mapping to risk_tprm table"""
    
    id = models.CharField(max_length=20, primary_key=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
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
    exposure_rating = models.IntegerField(blank=True, null=True)
    risk_type = models.CharField(max_length=20, blank=True, null=True)
    entity = models.CharField(max_length=100, blank=True, null=True)
    data = models.CharField(max_length=100, blank=True, null=True)
    row = models.CharField(max_length=50, blank=True, null=True)  # This field maps to vendor_id
    
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
    def get_heatmap_data(cls, module_name=None):
        """
        Dynamically generate heatmap data from risk records
        
        Args:
            module_name: Optional module name to filter by (not used for now)
            
        Returns:
            List of heatmap data dictionaries
        """
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
