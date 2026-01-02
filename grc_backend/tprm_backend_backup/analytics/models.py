"""
Analytics models for Vendor Guard Hub.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from tprm_backend.core.models import BaseModel

User = get_user_model()


class AnalyticsDashboard(BaseModel):
    """Analytics dashboard configuration."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    dashboard_type = models.CharField(
        max_length=50,
        choices=[
            ('executive', 'Executive'),
            ('operational', 'Operational'),
            ('vendor', 'Vendor'),
            ('compliance', 'Compliance'),
            ('performance', 'Performance'),
            ('custom', 'Custom'),
        ]
    )
    layout = models.JSONField(default=dict)
    widgets = models.JSONField(default=list)
    is_public = models.BooleanField(default=False)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analytics_dashboards'
    )
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Analytics Dashboard')
        verbose_name_plural = _('Analytics Dashboards')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AnalyticsWidget(BaseModel):
    """Analytics widget configuration."""
    dashboard = models.ForeignKey(
        AnalyticsDashboard,
        on_delete=models.CASCADE,
        related_name='widgets'
    )
    widget_type = models.CharField(
        max_length=50,
        choices=[
            ('chart', 'Chart'),
            ('metric', 'Metric'),
            ('table', 'Table'),
            ('gauge', 'Gauge'),
            ('heatmap', 'Heatmap'),
            ('trend', 'Trend'),
        ]
    )
    title = models.CharField(max_length=200)
    configuration = models.JSONField(default=dict)
    data_source = models.CharField(max_length=100)
    refresh_interval = models.PositiveIntegerField(default=300)
    position = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Analytics Widget')
        verbose_name_plural = _('Analytics Widgets')
        ordering = ['dashboard', 'title']
    
    def __str__(self):
        return f"{self.dashboard.name} - {self.title}"


class AnalyticsReport(BaseModel):
    """Analytics report."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(
        max_length=50,
        choices=[
            ('vendor_performance', 'Vendor Performance'),
            ('sla_compliance', 'SLA Compliance'),
            ('risk_assessment', 'Risk Assessment'),
            ('cost_analysis', 'Cost Analysis'),
            ('trend_analysis', 'Trend Analysis'),
            ('custom', 'Custom'),
        ]
    )
    parameters = models.JSONField(default=dict)
    schedule = models.CharField(max_length=100, blank=True)
    recipients = models.JSONField(default=list)
    is_automated = models.BooleanField(default=False)
    last_generated = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_analytics_reports'
    )
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Analytics Report')
        verbose_name_plural = _('Analytics Reports')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AnalyticsMetric(BaseModel):
    """Analytics metrics."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    metric_type = models.CharField(
        max_length=50,
        choices=[
            ('kpi', 'KPI'),
            ('kri', 'KRI'),
            ('custom', 'Custom'),
        ]
    )
    calculation_formula = models.TextField()
    unit = models.CharField(max_length=20)
    target_value = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Analytics Metric')
        verbose_name_plural = _('Analytics Metrics')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AnalyticsDataPoint(BaseModel):
    """Analytics data points."""
    metric = models.ForeignKey(
        AnalyticsMetric,
        on_delete=models.CASCADE,
        related_name='data_points'
    )
    value = models.DecimalField(max_digits=10, decimal_places=4)
    timestamp = models.DateTimeField()
    context = models.JSONField(default=dict)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Analytics Data Point')
        verbose_name_plural = _('Analytics Data Points')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.metric.name} - {self.timestamp}"


class AnalyticsInsight(BaseModel):
    """Analytics insights."""
    insight_type = models.CharField(
        max_length=50,
        choices=[
            ('trend', 'Trend'),
            ('anomaly', 'Anomaly'),
            ('correlation', 'Correlation'),
            ('prediction', 'Prediction'),
            ('recommendation', 'Recommendation'),
        ]
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    confidence_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Confidence level (0-100)"
    )
    impact_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Impact score (0-100)"
    )
    data_sources = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_actionable = models.BooleanField(default=True)
    action_items = models.JSONField(default=list)
    
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = _('Analytics Insight')
        verbose_name_plural = _('Analytics Insights')
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.insight_type} - {self.title}"
