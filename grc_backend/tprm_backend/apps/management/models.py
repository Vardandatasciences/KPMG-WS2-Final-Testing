"""
Management app models.
"""
from django.db import models


class ScreeningSchedule(models.Model):
    """
    Persistent schedule for running external screening for a vendor.
    One record = one schedule rule (one-time or recurring via cron).
    """

    FREQUENCY_CHOICES = [
        ('does_not_repeat', 'One-time'),
        ('daily', 'Daily'),
        ('weekdays', 'Weekdays (Mon–Fri)'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]

    id = models.BigAutoField(primary_key=True)

    # Link to the vendor being screened
    temp_vendor = models.ForeignKey(
        'vendor_core.TempVendor',
        on_delete=models.CASCADE,
        related_name='screening_schedules',
        db_column='temp_vendor_id',
    )

    tenant_id = models.CharField(max_length=100, null=True, blank=True)

    # Scheduling fields
    frequency = models.CharField(
        max_length=32, choices=FREQUENCY_CHOICES, default='daily'
    )
    # Derived cron expression (e.g. "0 9 * * *" for daily at 09:00)
    cron_expression = models.CharField(max_length=128, null=True, blank=True)
    # Absolute run time for one-time schedules
    scheduled_at = models.DateTimeField(
        null=True, blank=True, help_text='One-time run at this datetime'
    )
    # Pre-computed next execution datetime; updated after each run
    next_run_at = models.DateTimeField(null=True, blank=True)
    start_date = models.DateField(
        null=True, blank=True, help_text='Earliest date to start running'
    )

    # State
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='active')

    # Run history
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_run_status = models.CharField(max_length=32, null=True, blank=True)

    notes = models.TextField(blank=True, default='')
    created_by_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'screening_schedules'
        ordering = ['next_run_at']

    def __str__(self):
        return (
            f'ScreeningSchedule(vendor={self.temp_vendor_id}, '
            f'freq={self.frequency}, next={self.next_run_at})'
        )
