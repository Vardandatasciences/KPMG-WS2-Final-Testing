"""
SLA Signals

This module defines Django signals for SLA management operations including retention expiry.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
from .models import VendorSLA, SLAMetric

logger = logging.getLogger(__name__)

# Import retention helpers from GRC models
try:
    from grc.models import compute_retention_expiry, upsert_retention_timeline
    RETENTION_AVAILABLE = True
except ImportError:
    RETENTION_AVAILABLE = False
    logger.warning("Retention helpers not available. Retention expiry will not be set automatically.")


@receiver(post_save, sender=VendorSLA)
def vendor_sla_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving a vendor SLA - sets retention expiry"""
    try:
        if RETENTION_AVAILABLE:
            try:
                page_key = 'sla_create' if created else 'sla_update'
                expiry = compute_retention_expiry('vendor_sla', page_key)
                if expiry:
                    VendorSLA.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                    setattr(instance, 'retentionExpiry', expiry)
                    upsert_retention_timeline(
                        instance,
                        'vendor_sla',
                        record_name=getattr(instance, 'sla_name', None),
                        created_date=getattr(instance, 'effective_date', None),
                        framework_id=None
                    )
            except Exception as e:
                logger.error(f"Error setting retention expiry for SLA {instance.pk}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in vendor SLA post_save signal: {str(e)}")


@receiver(post_save, sender=SLAMetric)
def sla_metric_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving an SLA metric - sets retention expiry"""
    try:
        if RETENTION_AVAILABLE:
            try:
                page_key = 'sla_metric_create' if created else 'sla_metric_update'
                expiry = compute_retention_expiry('sla_metric', page_key)
                if expiry:
                    SLAMetric.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                    setattr(instance, 'retentionExpiry', expiry)
            except Exception as e:
                logger.error(f"Error setting retention expiry for SLA metric {instance.pk}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in SLA metric post_save signal: {str(e)}")

