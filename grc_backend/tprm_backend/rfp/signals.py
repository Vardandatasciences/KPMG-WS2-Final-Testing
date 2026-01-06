"""
RFP Signals

This module defines Django signals for RFP management operations including retention expiry.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
from .models import RFP, RFPEvaluationCriteria, RFPTypeCustomFields

logger = logging.getLogger(__name__)

# Import retention helpers from GRC models
try:
    from grc.models import compute_retention_expiry, upsert_retention_timeline
    RETENTION_AVAILABLE = True
except ImportError:
    RETENTION_AVAILABLE = False
    logger.warning("Retention helpers not available. Retention expiry will not be set automatically.")


@receiver(post_save, sender=RFP)
def rfp_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving an RFP - sets retention expiry"""
    try:
        if RETENTION_AVAILABLE:
            try:
                page_key = 'rfp_create' if created else 'rfp_update'
                expiry = compute_retention_expiry('rfp', page_key)
                if expiry:
                    RFP.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                    setattr(instance, 'retentionExpiry', expiry)
                    upsert_retention_timeline(
                        instance,
                        'rfp',
                        record_name=getattr(instance, 'rfp_title', None),
                        created_date=getattr(instance, 'created_at', None),
                        framework_id=None
                    )
            except Exception as e:
                logger.error(f"Error setting retention expiry for RFP {instance.pk}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in RFP post_save signal: {str(e)}")


@receiver(post_save, sender=RFPEvaluationCriteria)
def rfp_evaluation_criteria_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving RFP evaluation criteria - sets retention expiry"""
    try:
        if RETENTION_AVAILABLE:
            try:
                page_key = 'rfp_evaluation_criteria_create' if created else 'rfp_evaluation_criteria_update'
                expiry = compute_retention_expiry('rfp_evaluation_criteria', page_key)
                if expiry:
                    RFPEvaluationCriteria.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                    setattr(instance, 'retentionExpiry', expiry)
            except Exception as e:
                logger.error(f"Error setting retention expiry for RFP evaluation criteria {instance.pk}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in RFP evaluation criteria post_save signal: {str(e)}")


@receiver(post_save, sender=RFPTypeCustomFields)
def rfp_type_custom_fields_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving RFP type custom fields - sets retention expiry"""
    try:
        if RETENTION_AVAILABLE:
            try:
                page_key = 'rfp_type_custom_fields_create' if created else 'rfp_type_custom_fields_update'
                expiry = compute_retention_expiry('rfp_type_custom_fields', page_key)
                if expiry:
                    RFPTypeCustomFields.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                    setattr(instance, 'retentionExpiry', expiry)
            except Exception as e:
                logger.error(f"Error setting retention expiry for RFP type custom fields {instance.pk}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in RFP type custom fields post_save signal: {str(e)}")

