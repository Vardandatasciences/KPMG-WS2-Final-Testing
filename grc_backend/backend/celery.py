"""
Celery configuration for GRC backend project.
"""

import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('grc_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule - Periodic tasks
app.conf.beat_schedule = {
    'delete-expired-retention-records': {
        'task': 'grc.tasks.delete_expired_retention_records',
        'schedule': 86400.0,  # Run daily (24 hours in seconds)
    },
    'send-retention-warnings': {
        'task': 'grc.tasks.send_retention_warnings',
        'schedule': 86400.0,  # Run daily
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')





