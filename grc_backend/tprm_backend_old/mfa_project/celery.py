"""
Celery configuration for MFA Project

This module configures Celery for background task processing, particularly
for risk analysis tasks that should not block contract creation.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mfa_project.settings')

app = Celery('mfa_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery to handle connection failures gracefully
app.conf.update(
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    result_expires=3600,       # 1 hour
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
