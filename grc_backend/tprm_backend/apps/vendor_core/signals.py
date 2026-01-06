"""
Vendor Core Signals

This module defines Django signals for vendor management operations including retention expiry.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
from .models import Vendors

logger = logging.getLogger(__name__)

# Import retention helpers from GRC models
try:
    from grc.models import compute_retention_expiry, upsert_retention_timeline
    RETENTION_AVAILABLE = True
except ImportError:
    RETENTION_AVAILABLE = False
    logger.warning("Retention helpers not available. Retention expiry will not be set automatically.")


@receiver(post_save, sender=Vendors)
def vendor_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving a vendor - sets retention expiry"""
    try:
        if RETENTION_AVAILABLE:
            try:
                page_key = 'vendor_create' if created else 'vendor_update'
                expiry = compute_retention_expiry('vendor', page_key)
                if expiry:
                    Vendors.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                    setattr(instance, 'retentionExpiry', expiry)
                    upsert_retention_timeline(
                        instance,
                        'vendor',
                        record_name=getattr(instance, 'company_name', None),
                        created_date=getattr(instance, 'created_at', None),
                        framework_id=None
                    )
            except Exception as e:
                logger.error(f"Error setting retention expiry for vendor {instance.pk}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in vendor post_save signal: {str(e)}")

