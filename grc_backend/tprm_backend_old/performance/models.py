"""
Performance monitoring models for Vendor Guard Hub.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from tprm_backend.core.models import BaseModel

User = get_user_model()


class PerformanceMetric(BaseModel):
    """Performance metric data points."""
    vendor = models.ForeignKey(
        'slas.Vendor',
        on_delete=models.CASCADE,
        related_name='performance_metrics'
    )
    sla = models.ForeignKey(
        'slas.SLA',
        on_delete=models.CASCADE,
        related_name='performance_metrics'
    )
    metric_name = models.CharField(max_length=200)
    metric_value = models.DecimalField(max_digits=10, decimal_places=4)
    unit = models.CharField(max_length=20)
    measurement_date = models.DateTimeField()
    target_value = models.DecimalField(max_digits=10, decimal_places=4)
    threshold_warning = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    threshold_critical = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    is_compliant = models.BooleanField()
    performance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Performance score (0-100)"
    )
    notes = models.TextField(blank=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Performance Metric')
        verbose_name_plural = _('Performance Metrics')
        ordering = ['-measurement_date']
        indexes = [
            models.Index(fields=['vendor', 'measurement_date']),
            models.Index(fields=['sla', 'measurement_date']),
            models.Index(fields=['metric_name', 'measurement_date']),
        ]
    
    def __str__(self):
        return f"{self.vendor.name} - {self.metric_name} - {self.measurement_date}"


class PerformanceAlert(BaseModel):
    """Performance-based alerts."""
    performance_metric = models.ForeignKey(
        PerformanceMetric,
        on_delete=models.CASCADE,
        related_name='alerts'
    )
    alert_type = models.CharField(
        max_length=20,
        choices=[
            ('warning', 'Warning'),
            ('critical', 'Critical'),
            ('breach', 'Breach'),
        ]
    )
    alert_message = models.TextField()
    threshold_value = models.DecimalField(max_digits=10, decimal_places=4)
    actual_value = models.DecimalField(max_digits=10, decimal_places=4)
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ]
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('acknowledged', 'Acknowledged'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ],
        default='active'
    )
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Performance Alert')
        verbose_name_plural = _('Performance Alerts')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.performance_metric.vendor.name} - {self.alert_type}"


class PerformanceReport(BaseModel):
    """Performance reports."""
    vendor = models.ForeignKey(
        'slas.Vendor',
        on_delete=models.CASCADE,
        related_name='performance_reports'
    )
    report_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annual', 'Annual'),
        ]
    )
    report_period_start = models.DateTimeField()
    report_period_end = models.DateTimeField()
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Overall performance score (0-100)"
    )
    total_metrics = models.PositiveIntegerField()
    compliant_metrics = models.PositiveIntegerField()
    violations_count = models.PositiveIntegerField()
    report_data = models.JSONField(default=dict)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_reports'
    )
    is_automated = models.BooleanField(default=False)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Performance Report')
        verbose_name_plural = _('Performance Reports')
        ordering = ['-report_period_end']
    
    def __str__(self):
        return f"{self.vendor.name} - {self.report_type} - {self.report_period_end}"


class PerformanceTrend(BaseModel):
    """Performance trend analysis."""
    vendor = models.ForeignKey(
        'slas.Vendor',
        on_delete=models.CASCADE,
        related_name='performance_trends'
    )
    metric_name = models.CharField(max_length=200)
    trend_period = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ]
    )
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    average_value = models.DecimalField(max_digits=10, decimal_places=4)
    min_value = models.DecimalField(max_digits=10, decimal_places=4)
    max_value = models.DecimalField(max_digits=10, decimal_places=4)
    trend_direction = models.CharField(
        max_length=20,
        choices=[
            ('improving', 'Improving'),
            ('declining', 'Declining'),
            ('stable', 'Stable'),
            ('fluctuating', 'Fluctuating'),
        ]
    )
    trend_strength = models.CharField(
        max_length=20,
        choices=[
            ('weak', 'Weak'),
            ('moderate', 'Moderate'),
            ('strong', 'Strong'),
        ]
    )
    confidence_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Confidence level (0-100)"
    )
    trend_data = models.JSONField(default=dict)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Performance Trend')
        verbose_name_plural = _('Performance Trends')
        ordering = ['-period_end']
    
    def __str__(self):
        return f"{self.vendor.name} - {self.metric_name} - {self.trend_direction}"


class PerformanceBenchmark(BaseModel):
    """Performance benchmarks."""
    benchmark_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    metric_name = models.CharField(max_length=200)
    industry = models.CharField(max_length=100, blank=True)
    benchmark_value = models.DecimalField(max_digits=10, decimal_places=4)
    unit = models.CharField(max_length=20)
    benchmark_type = models.CharField(
        max_length=20,
        choices=[
            ('target', 'Target'),
            ('average', 'Average'),
            ('best_practice', 'Best Practice'),
            ('regulatory', 'Regulatory'),
        ]
    )
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Performance Benchmark')
        verbose_name_plural = _('Performance Benchmarks')
        ordering = ['benchmark_name']
    
    def __str__(self):
        return f"{self.benchmark_name} - {self.metric_name}"


class PerformanceKPI(BaseModel):
    """Key Performance Indicators."""
    kpi_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    calculation_formula = models.TextField()
    target_value = models.DecimalField(max_digits=10, decimal_places=4)
    unit = models.CharField(max_length=20)
    measurement_frequency = models.CharField(
        max_length=20,
        choices=[
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
        ]
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_kpis'
    )
    stakeholders = models.ManyToManyField(
        User,
        related_name='stakeholder_kpis',
        blank=True
    )
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Performance KPI')
        verbose_name_plural = _('Performance KPIs')
        ordering = ['kpi_name']
    
    def __str__(self):
        return self.kpi_name
