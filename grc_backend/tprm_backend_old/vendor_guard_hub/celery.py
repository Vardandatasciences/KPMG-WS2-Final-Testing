"""
Celery configuration for vendor_guard_hub project.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vendor_guard_hub.settings')

app = Celery('vendor_guard_hub')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'update-expired-slas': {
        'task': 'slas.tasks.update_expired_slas',
        'schedule': 3600.0,  # Every hour
    },
    'check-sla-compliance-daily': {
        'task': 'slas.tasks.check_sla_compliance',
        'schedule': 86400.0,  # Daily
    },
    'check-expiring-slas': {
        'task': 'slas.tasks.check_expiring_slas',
        'schedule': 86400.0,  # Daily
    },
    'generate-performance-reports': {
        'task': 'performance.tasks.generate_performance_reports',
        'schedule': 3600.0,  # Hourly
    },
    'cleanup-old-data': {
        'task': 'core.tasks.cleanup_old_data',
        'schedule': 604800.0,  # Weekly
    },
    'update-analytics-dashboard': {
        'task': 'analytics.tasks.update_dashboard_data',
        'schedule': 1800.0,  # Every 30 minutes
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
