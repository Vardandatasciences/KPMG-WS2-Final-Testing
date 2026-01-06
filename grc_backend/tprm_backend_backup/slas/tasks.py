"""
Celery tasks for the SLAs app.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import VendorSLA, SLACompliance, SLAViolation
import logging

logger = logging.getLogger(__name__)


@shared_task
def update_expired_slas():
    """Update SLA status to EXPIRED for SLAs that have passed their expiry date."""
    today = timezone.now().date()
    
    # Find SLAs that are expired but not marked as EXPIRED
    expired_slas = VendorSLA.objects.filter(
        expiry_date__lt=today,
        status__in=['ACTIVE', 'PENDING']
    )
    
    updated_count = 0
    for sla in expired_slas:
        try:
            if sla.update_status_if_expired():
                updated_count += 1
                logger.info(f"SLA {sla.sla_id} ({sla.sla_name}) marked as EXPIRED")
        except Exception as e:
            logger.error(f"Error updating SLA {sla.sla_id}: {str(e)}")
    
    # Also check for SLAs that should be marked as ACTIVE
    future_slas = VendorSLA.objects.filter(
        effective_date__lte=today,
        expiry_date__gte=today,
        status='PENDING'
    )
    
    active_count = 0
    for sla in future_slas:
        try:
            sla.status = 'ACTIVE'
            sla.save(update_fields=['status'])
            active_count += 1
            logger.info(f"SLA {sla.sla_id} ({sla.sla_name}) marked as ACTIVE")
        except Exception as e:
            logger.error(f"Error updating SLA {sla.sla_id}: {str(e)}")
    
    return f"Updated {updated_count} SLAs to EXPIRED, {active_count} SLAs to ACTIVE"


@shared_task
def check_sla_compliance():
    """Check SLA compliance and generate violations if needed."""
    active_slas = VendorSLA.objects.filter(status='ACTIVE')
    
    for sla in active_slas:
        # Check each metric for compliance
        for metric in sla.sla_metrics.all():
            # Add your compliance checking logic here
            # This is a simplified example
            pass
    
    return "SLA compliance check completed"


@shared_task
def generate_sla_reports():
    """Generate SLA performance reports."""
    # Add your SLA report generation logic here
    return "SLA reports generated"


@shared_task
def check_expiring_slas():
    """Check for SLAs that are expiring soon."""
    thirty_days_from_now = timezone.now().date() + timedelta(days=30)
    expiring_slas = VendorSLA.objects.filter(
        expiry_date__lte=thirty_days_from_now,
        status='ACTIVE'
    )
    
    # Add notification logic here
    return f"Found {expiring_slas.count()} SLAs expiring soon"
