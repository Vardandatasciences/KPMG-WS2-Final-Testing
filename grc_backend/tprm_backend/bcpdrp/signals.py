"""
BCP/DRP Signals

This module defines Django signals for BCP/DRP management operations including retention expiry.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
from .models import Plan, Evaluation

logger = logging.getLogger(__name__)

# Import retention helpers from GRC models
try:
    from grc.models import compute_retention_expiry, upsert_retention_timeline
    RETENTION_AVAILABLE = True
except ImportError:
    RETENTION_AVAILABLE = False
    logger.warning("Retention helpers not available. Retention expiry will not be set automatically.")


@receiver(post_save, sender=Plan)
def bcp_drp_plan_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving a BCP/DRP plan - sets retention expiry"""
    try:
        if RETENTION_AVAILABLE:
            try:
                page_key = 'bcp_drp_plan_create' if created else 'bcp_drp_plan_update'
                expiry = compute_retention_expiry('bcp_drp_plan', page_key)
                if expiry:
                    Plan.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                    setattr(instance, 'retentionExpiry', expiry)
                    upsert_retention_timeline(
                        instance,
                        'bcp_drp_plan',
                        record_name=getattr(instance, 'plan_name', None),
                        created_date=getattr(instance, 'submitted_at', None),
                        framework_id=None
                    )
            except Exception as e:
                logger.error(f"Error setting retention expiry for BCP/DRP plan {instance.pk}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in BCP/DRP plan post_save signal: {str(e)}")


@receiver(post_save, sender=Evaluation)
def bcp_drp_evaluation_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving a BCP/DRP evaluation - sets retention expiry"""
    try:
        if RETENTION_AVAILABLE:
            try:
                page_key = 'bcp_drp_evaluation_create' if created else 'bcp_drp_evaluation_update'
                expiry = compute_retention_expiry('bcp_drp_evaluation', page_key)
                if expiry:
                    Evaluation.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                    setattr(instance, 'retentionExpiry', expiry)
            except Exception as e:
                logger.error(f"Error setting retention expiry for BCP/DRP evaluation {instance.pk}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in BCP/DRP evaluation post_save signal: {str(e)}")

