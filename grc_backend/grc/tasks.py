"""
Celery tasks for GRC app.
"""

import logging
from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from django.db import transaction

from grc.models import RetentionTimeline

logger = logging.getLogger(__name__)


@shared_task(name='grc.tasks.delete_expired_retention_records')
def delete_expired_retention_records():
    """
    Celery task to automatically delete expired retention records.
    This task runs daily via Celery Beat and calls the delete_expired_records management command.
    """
    try:
        logger.info("Starting automatic deletion of expired retention records...")
        
        # Call the management command
        call_command('delete_expired_records')
        
        logger.info("Automatic deletion of expired retention records completed successfully.")
        return "Successfully processed expired retention records"
    except Exception as e:
        logger.error(f"Error in delete_expired_retention_records task: {str(e)}", exc_info=True)
        raise


@shared_task(name='grc.tasks.send_retention_warnings')
def send_retention_warnings():
    """
    Celery task to send retention warning notifications.
    This task runs daily via Celery Beat and calls the send_retention_warnings management command.
    """
    try:
        logger.info("Starting retention warning notifications...")
        
        # Call the management command
        call_command('send_retention_warnings')
        
        logger.info("Retention warning notifications completed successfully.")
        return "Successfully sent retention warnings"
    except Exception as e:
        logger.error(f"Error in send_retention_warnings task: {str(e)}", exc_info=True)
        raise




