"""
Contract Management Signals

This module defines Django signals for contract management operations.
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
import logging
from .models import VendorContract, ContractTerm, ContractClause

logger = logging.getLogger(__name__)

# Import retention helpers from GRC models
try:
    from grc.models import compute_retention_expiry, upsert_retention_timeline
    RETENTION_AVAILABLE = True
except ImportError:
    RETENTION_AVAILABLE = False
    logger.warning("Retention helpers not available. Retention expiry will not be set automatically.")

# Store old term_id before save to track changes
_term_id_cache = {}


@receiver(pre_save, sender=VendorContract)
def contract_pre_save(sender, instance, **kwargs):
    """Signal triggered before saving a contract"""
    try:
        # Auto-update status based on dates
        if instance.end_date and instance.end_date < timezone.now().date() and instance.status != 'EXPIRED':
            instance.status = 'EXPIRED'
            logger.info(f"Contract {instance.contract_id} status updated to EXPIRED")
        
        # Auto-update workflow stage based on status
        if instance.status == 'ACTIVE' and instance.workflow_stage == 'executed':
            instance.workflow_stage = 'active'
            logger.info(f"Contract {instance.contract_id} workflow stage updated to active")
        
        # Log contract changes
        if instance.pk:
            try:
                old_instance = VendorContract.objects.get(pk=instance.pk)
                if old_instance.status != instance.status:
                    logger.info(f"Contract {instance.contract_id} status changed from {old_instance.status} to {instance.status}")
            except VendorContract.DoesNotExist:
                pass
                
    except Exception as e:
        logger.error(f"Error in contract pre_save signal: {str(e)}")


@receiver(post_save, sender=VendorContract)
def contract_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving a contract"""
    try:
        if created:
            logger.info(f"New contract created: {instance.contract_id} - {instance.contract_title}")
        else:
            logger.info(f"Contract updated: {instance.contract_id} - {instance.contract_title}")
        
        # Set retention expiry if retention is available
        if RETENTION_AVAILABLE:
            try:
                page_key = 'contract_create' if created else 'contract_update'
                expiry = compute_retention_expiry('vendor_contract', page_key)
                if expiry:
                    VendorContract.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                    setattr(instance, 'retentionExpiry', expiry)
                    upsert_retention_timeline(
                        instance,
                        'vendor_contract',
                        record_name=getattr(instance, 'contract_title', None),
                        created_date=getattr(instance, 'created_at', None),
                        framework_id=None
                    )
            except Exception as e:
                logger.error(f"Error setting retention expiry for contract {instance.contract_id}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in contract post_save signal: {str(e)}")


@receiver(pre_save, sender=ContractTerm)
def contract_term_pre_save(sender, instance, **kwargs):
    """Signal triggered before saving a contract term - track old term_id"""
    try:
        if instance.pk:
            # Get the old term_id before save
            old_term = ContractTerm.objects.filter(pk=instance.pk).first()
            if old_term:
                _term_id_cache[instance.pk] = old_term.term_id
                logger.info(f"Stored old term_id for term {instance.pk}: {old_term.term_id}")
    except Exception as e:
        logger.error(f"Error in contract term pre_save signal: {str(e)}")

@receiver(post_save, sender=ContractTerm)
def contract_term_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving a contract term"""
    try:
        if created:
            logger.info(f"New contract term created: {instance.term_id} for contract {instance.contract_id}")
            
            # Set retention expiry if retention is available
            if RETENTION_AVAILABLE:
                try:
                    page_key = 'contract_term_create'
                    expiry = compute_retention_expiry('contract_term', page_key)
                    if expiry:
                        ContractTerm.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                        setattr(instance, 'retentionExpiry', expiry)
                except Exception as e:
                    logger.error(f"Error setting retention expiry for contract term {instance.pk}: {str(e)}")
            
            # For newly created terms, try to find and update questionnaires that might have been created
            # with the original term_id (before it was modified due to duplicates)
            # This handles the case where questionnaires were created before the term was saved
            try:
                from audits_contract.models import ContractStaticQuestionnaire
                from django.utils import timezone
                from datetime import timedelta
                
                # Get the original term_id from the instance (set by serializer if it was changed)
                original_term_id = getattr(instance, '_original_term_id', None)
                saved_term_id = instance.term_id
                term_category = instance.term_category
                
                # Look for questionnaires created in the last 2 hours that don't have a matching term
                # This helps us find questionnaires that were created before the term was saved
                recent_cutoff = timezone.now() - timedelta(hours=2)
                orphaned_questionnaires = ContractStaticQuestionnaire.objects.filter(
                    created_at__gte=recent_cutoff
                ).exclude(
                    term_id__in=ContractTerm.objects.values_list('term_id', flat=True)
                )
                
                total_updated = 0
                
                if original_term_id and original_term_id != saved_term_id:
                    logger.info(f"📋 Term ID changed from {original_term_id} to {saved_term_id}, updating questionnaires...")
                    
                    # Find questionnaires that were created with the original term_id
                    # and update them to use the saved term_id
                    questionnaires_to_update = ContractStaticQuestionnaire.objects.filter(
                        term_id=original_term_id
                    )
                    
                    if questionnaires_to_update.exists():
                        updated_count = questionnaires_to_update.update(term_id=saved_term_id)
                        total_updated += updated_count
                        logger.info(f"✅ Updated {updated_count} questionnaires from term_id {original_term_id} to {saved_term_id}")
                    
                    # Also try to match by term_id patterns (in case the original_term_id format is slightly different)
                    # Build variations of the original term_id to catch different formats
                    if original_term_id:
                        term_id_variations = [
                            original_term_id,
                            original_term_id.replace('term_', ''),
                            f"term_{original_term_id.replace('term_', '')}"
                        ]
                        
                        # Extract numeric parts for partial matching
                        # e.g., if original_term_id is "term_1762415180553_0_abc123"
                        # try to match "term_1762415180553_0" or "1762415180553_0"
                        if '_' in original_term_id:
                            parts = original_term_id.split('_')
                            if len(parts) > 1:
                                # Try matching with fewer parts (e.g., "term_1762415180553_0" from "term_1762415180553_0_abc123")
                                for i in range(2, len(parts) + 1):
                                    partial_id = '_'.join(parts[:i])
                                    if partial_id not in term_id_variations:
                                        term_id_variations.append(partial_id)
                        
                        # Try to find questionnaires with any of these variations
                        for variation in term_id_variations:
                            if variation != saved_term_id:
                                matching_questionnaires = ContractStaticQuestionnaire.objects.filter(
                                    term_id=variation
                                )
                                if matching_questionnaires.exists():
                                    updated_count = matching_questionnaires.update(term_id=saved_term_id)
                                    total_updated += updated_count
                                    logger.info(f"✅ Updated {updated_count} questionnaires from term_id variation {variation} to {saved_term_id}")
                    
                    if total_updated > 0:
                        logger.info(f"✅ Total questionnaires updated: {total_updated}")
                    else:
                        logger.warning(f"⚠️ No questionnaires found with original term_id {original_term_id} or its variations")
                        
                        # Try to match orphaned questionnaires by checking if their term_id is similar
                        # Look for questionnaires with term_ids that contain parts of the original_term_id
                        if orphaned_questionnaires.exists():
                            logger.info(f"🔍 Checking {orphaned_questionnaires.count()} orphaned questionnaires for potential matches...")
                            for orphaned_q in orphaned_questionnaires[:10]:  # Limit to first 10 to avoid performance issues
                                orphaned_term_id = orphaned_q.term_id
                                # Check if the orphaned term_id contains parts of the original_term_id
                                # or if the original_term_id contains parts of the orphaned term_id
                                if (original_term_id in orphaned_term_id or 
                                    orphaned_term_id in original_term_id or
                                    (original_term_id.split('_')[:2] == orphaned_term_id.split('_')[:2] if '_' in original_term_id and '_' in orphaned_term_id else False)):
                                    logger.info(f"🔗 Potential match found: orphaned questionnaire {orphaned_q.question_id} with term_id {orphaned_term_id}")
                                    orphaned_q.term_id = saved_term_id
                                    orphaned_q.save()
                                    total_updated += 1
                                    logger.info(f"✅ Updated orphaned questionnaire {orphaned_q.question_id} from {orphaned_term_id} to {saved_term_id}")
                            
                            if total_updated > 0:
                                logger.info(f"✅ Total questionnaires updated (including orphaned): {total_updated}")
                else:
                    # If term_id wasn't changed, check if there are questionnaires with this term_id
                    # that don't have a matching term (shouldn't happen, but just in case)
                    matching_questionnaires = ContractStaticQuestionnaire.objects.filter(
                        term_id=saved_term_id
                    )
                    if matching_questionnaires.exists():
                        logger.info(f"✅ Found {matching_questionnaires.count()} questionnaires matching term_id {saved_term_id}")
                    else:
                        # If term_id wasn't changed, check for orphaned questionnaires that might match
                        # This handles edge cases where questionnaires were created but term_id format is slightly different
                        if orphaned_questionnaires.exists():
                            logger.info(f"ℹ️ Found {orphaned_questionnaires.count()} orphaned questionnaires (no matching term)")
                            # Try to match by checking if orphaned term_ids are similar to the saved term_id
                            for orphaned_q in orphaned_questionnaires[:5]:  # Limit to first 5
                                orphaned_term_id = orphaned_q.term_id
                                # Check if there's a partial match (e.g., same timestamp prefix)
                                if '_' in saved_term_id and '_' in orphaned_term_id:
                                    saved_parts = saved_term_id.split('_')
                                    orphaned_parts = orphaned_term_id.split('_')
                                    # If first 2 parts match, it might be the same term
                                    if len(saved_parts) >= 2 and len(orphaned_parts) >= 2:
                                        if saved_parts[:2] == orphaned_parts[:2]:
                                            logger.info(f"🔗 Potential match: updating orphaned questionnaire {orphaned_q.question_id} from {orphaned_term_id} to {saved_term_id}")
                                            orphaned_q.term_id = saved_term_id
                                            orphaned_q.save()
                                            logger.info(f"✅ Updated orphaned questionnaire {orphaned_q.question_id}")
                    
                    logger.info(f"Term {saved_term_id} created - questionnaires should match by this term_id")
                
            except Exception as e:
                logger.error(f"Error checking questionnaires for new term: {str(e)}")
        else:
            logger.info(f"Contract term updated: {instance.term_id} for contract {instance.contract_id}")
            
            # Set retention expiry if retention is available
            if RETENTION_AVAILABLE:
                try:
                    page_key = 'contract_term_update'
                    expiry = compute_retention_expiry('contract_term', page_key)
                    if expiry:
                        ContractTerm.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                        setattr(instance, 'retentionExpiry', expiry)
                except Exception as e:
                    logger.error(f"Error setting retention expiry for contract term {instance.pk}: {str(e)}")
            
            # If term_id changed, update questionnaires that reference the old term_id
            old_term_id = _term_id_cache.get(instance.pk)
            if old_term_id and old_term_id != instance.term_id:
                logger.info(f"Term ID changed from {old_term_id} to {instance.term_id}, updating questionnaires...")
                try:
                    from audits_contract.models import ContractStaticQuestionnaire
                    updated_count = ContractStaticQuestionnaire.objects.filter(
                        term_id=old_term_id
                    ).update(term_id=instance.term_id)
                    logger.info(f"Updated {updated_count} questionnaires from term_id {old_term_id} to {instance.term_id}")
                    # Clean up cache
                    if instance.pk in _term_id_cache:
                        del _term_id_cache[instance.pk]
                except Exception as e:
                    logger.error(f"Error updating questionnaires after term_id change: {str(e)}")
    except Exception as e:
        logger.error(f"Error in contract term post_save signal: {str(e)}")


@receiver(post_save, sender=ContractClause)
def contract_clause_post_save(sender, instance, created, **kwargs):
    """Signal triggered after saving a contract clause"""
    try:
        if created:
            logger.info(f"New contract clause created: {instance.clause_id} for contract {instance.contract_id}")
        else:
            logger.info(f"Contract clause updated: {instance.clause_id} for contract {instance.contract_id}")
        
        # Set retention expiry if retention is available
        if RETENTION_AVAILABLE:
            try:
                page_key = 'contract_clause_create' if created else 'contract_clause_update'
                expiry = compute_retention_expiry('contract_clause', page_key)
                if expiry:
                    ContractClause.objects.filter(pk=instance.pk).update(retentionExpiry=expiry)
                    setattr(instance, 'retentionExpiry', expiry)
            except Exception as e:
                logger.error(f"Error setting retention expiry for contract clause {instance.pk}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in contract clause post_save signal: {str(e)}")


@receiver(post_delete, sender=VendorContract)
def contract_post_delete(sender, instance, **kwargs):
    """Signal triggered after deleting a contract"""
    try:
        logger.info(f"Contract deleted: {instance.contract_id} - {instance.contract_title}")
    except Exception as e:
        logger.error(f"Error in contract post_delete signal: {str(e)}")
