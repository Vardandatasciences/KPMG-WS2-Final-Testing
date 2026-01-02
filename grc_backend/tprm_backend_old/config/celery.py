"""
Celery configuration for Vendor TPRM System
Handles async tasks including backup/restore operations
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('vendor_tprm')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Configure Celery with secure settings
app.conf.update(
    # Security settings
    worker_disable_rate_limits=False,
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Task routing
    task_routes={
        'tasks.vendor_backup_tasks.*': {'queue': 'vendor_backup'},
        'tasks.vendor_security_tasks.*': {'queue': 'vendor_security'},
        'tasks.vendor_notification_tasks.*': {'queue': 'vendor_notifications'},
    },
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_compression='gzip',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
)


@app.task(bind=True)
def vendor_debug_task(self):
    """Debug task for testing Celery configuration"""
    print(f'Request: {self.request!r}')
    return 'Vendor Celery is working!'
