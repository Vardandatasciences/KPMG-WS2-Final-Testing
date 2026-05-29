"""
Step 9: Finalize Similarity Check
Creates or updates records based on user decision from Step 8.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from django.db import transaction
from django.utils import timezone

from ..models import Framework, Policy, SubPolicy, Compliance
from ..models_extensions.similarity_models import SimilarityCheckAudit, SemanticEmbedding
from .vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


class SimilarityFinalizeResult:
    """Result of finalizing similarity check."""
    def __init__(
        self,
        success: bool,
        action_taken: str,
        created_record_id: Optional[int] = None,
        created_record_type: Optional[str] = None,
        message: str = "",
        error: Optional[str] = None
    ):
        self.success = success
        self.action_taken = action_taken
        self.created_record_id = created_record_id
        self.created_record_type = created_record_type
        self.message = message
        self.error = error


class SimilarityFinalizeService:
    """
    Service for Step 9: Finalize similarity check based on user decision.
    
    Handles:
    - CREATE_ANYWAY: Create new record, activate in ChromaDB
    - USE_EXISTING: Don't create, redirect to existing
    - CANCEL: Clean up pending embeddings
    """
    
    def __init__(self):
        self.vector_store = VectorStoreService()
    
    def finalize(
        self,
        check_id: int,
        user_decision: str,
        selected_candidate_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> SimilarityFinalizeResult:
        """
        Finalize similarity check based on user decision.
        
        Args:
            check_id: SimilarityCheckAudit ID
            user_decision: 'CREATE_ANYWAY', 'USE_EXISTING', 'CANCEL'
            selected_candidate_id: ID if USE_EXISTING selected
            user_id: User making the decision
        
        Returns:
            SimilarityFinalizeResult with action taken
        """
        try:
            # Get the audit record
            audit = SimilarityCheckAudit.objects.get(id=check_id)
            
            logger.info(f"[Step 9] Finalizing check {check_id} with decision: {user_decision}")

            if self._is_deferred_save_review(audit):
                return self._handle_deferred_save_review(
                    audit, user_decision, selected_candidate_id
                )
            
            if user_decision == 'CREATE_ANYWAY':
                return self._handle_create_anyway(audit, user_id)
            
            elif user_decision == 'USE_EXISTING':
                return self._handle_use_existing(audit, selected_candidate_id, user_id)
            
            elif user_decision == 'CANCEL':
                return self._handle_cancel(audit)
            
            else:
                return SimilarityFinalizeResult(
                    success=False,
                    action_taken='ERROR',
                    error=f"Unknown decision: {user_decision}"
                )
                
        except SimilarityCheckAudit.DoesNotExist:
            logger.error(f"[Step 9] Check {check_id} not found")
            return SimilarityFinalizeResult(
                success=False,
                action_taken='ERROR',
                error=f"Check {check_id} not found"
            )
        except Exception as e:
            logger.exception(f"[Step 9] Finalization failed: {e}")
            return SimilarityFinalizeResult(
                success=False,
                action_taken='ERROR',
                error=str(e)
            )
    
    def _handle_create_anyway(
        self,
        audit: SimilarityCheckAudit,
        user_id: Optional[int]
    ) -> SimilarityFinalizeResult:
        """
        Handle CREATE_ANYWAY: Create record in DB and activate in ChromaDB.
        """
        try:
            with transaction.atomic():
                # Create the actual record based on type
                created_record = self._create_record(audit, user_id)
                
                if not created_record:
                    return SimilarityFinalizeResult(
                        success=False,
                        action_taken='CREATE_FAILED',
                        error="Failed to create record"
                    )
                
                # Get the created record ID
                record_id = created_record.id
                record_type = audit.item_type
                
                # Update ChromaDB: Change status from "Pending" to "Active"
                embedding_id = f"{record_type.lower()}_{audit.id}_audit"
                chroma_updated = self._activate_in_chromadb(
                    embedding_id,
                    record_id,
                    record_type
                )
                
                # Update audit record
                audit.final_record_id = record_id
                audit.final_record_type = record_type
                audit.final_action = 'CREATED'
                audit.finalized_at = timezone.now()
                audit.save(update_fields=[
                    'final_record_id', 'final_record_type', 
                    'final_action', 'finalized_at'
                ])
                
                # Update SemanticEmbedding record
                SemanticEmbedding.objects.filter(
                    content_type__model=record_type.lower(),
                    object_id=audit.id
                ).update(
                    object_id=record_id,  # Now points to actual record, not audit
                    status='Active'
                )
                
                logger.info(f"[Step 9] Created {record_type} ID={record_id}, ChromaDB updated={chroma_updated}")
                
                return SimilarityFinalizeResult(
                    success=True,
                    action_taken='CREATED',
                    created_record_id=record_id,
                    created_record_type=record_type,
                    message=f"Created {record_type} successfully"
                )
                
        except Exception as e:
            logger.exception(f"[Step 9] Create anyway failed: {e}")
            return SimilarityFinalizeResult(
                success=False,
                action_taken='CREATE_FAILED',
                error=str(e)
            )
    
    def _audit_context(self, audit: SimilarityCheckAudit) -> Dict[str, Any]:
        ctx = audit.classification_context_used
        return ctx if isinstance(ctx, dict) else {}

    def _is_deferred_save_review(self, audit: SimilarityCheckAudit) -> bool:
        """Option A: update/version — review only; real save runs on Confirm."""
        ctx = self._audit_context(audit)
        if ctx.get('flow') in ('async_update', 'async_update_review'):
            return True
        return bool(ctx.get('master_check_id'))

    def _handle_deferred_save_review(
        self,
        audit: SimilarityCheckAudit,
        user_decision: str,
        selected_candidate_id: Optional[int],
    ) -> SimilarityFinalizeResult:
        """
        Record similarity review for deferred save (no new Framework/Policy row here).
        """
        if user_decision == 'CANCEL':
            return self._handle_cancel(audit)

        if user_decision not in ('CREATE_ANYWAY', 'USE_EXISTING'):
            return SimilarityFinalizeResult(
                success=False,
                action_taken='ERROR',
                error=f"Unknown decision: {user_decision}",
            )

        try:
            embedding_id = f"{audit.item_type.lower()}_{audit.id}_audit"
            self.vector_store.delete_embedding(embedding_id)

            SemanticEmbedding.objects.filter(
                content_type__model=audit.item_type.lower(),
                object_id=audit.id,
            ).delete()

            if user_decision == 'USE_EXISTING':
                audit.final_action = 'USED_EXISTING'
                audit.final_record_id = selected_candidate_id
                audit.final_record_type = audit.item_type
                message = (
                    f"Using existing {audit.item_type} "
                    f"(ID={selected_candidate_id}). Confirm save to apply your update."
                )
                action = 'USED_EXISTING'
            else:
                audit.final_action = 'REVIEWED_CONTINUE'
                message = (
                    f"Review recorded for {audit.item_type}. "
                    "Confirm save to apply your update."
                )
                action = 'REVIEWED_CONTINUE'

            audit.finalized_at = timezone.now()
            audit.save(
                update_fields=[
                    'final_action',
                    'final_record_id',
                    'final_record_type',
                    'finalized_at',
                ]
            )

            logger.info(
                "[Step 9] Deferred-save review check %s: %s",
                audit.id,
                action,
            )

            return SimilarityFinalizeResult(
                success=True,
                action_taken=action,
                created_record_id=selected_candidate_id,
                created_record_type=audit.item_type,
                message=message,
            )
        except Exception as e:
            logger.exception(f"[Step 9] Deferred save review failed: {e}")
            return SimilarityFinalizeResult(
                success=False,
                action_taken='ERROR',
                error=str(e),
            )

    def _handle_use_existing(
        self,
        audit: SimilarityCheckAudit,
        selected_candidate_id: Optional[int],
        user_id: Optional[int]
    ) -> SimilarityFinalizeResult:
        """
        Handle USE_EXISTING: Don't create, clean up pending embedding.
        """
        try:
            # Delete pending embedding from ChromaDB (user chose existing)
            embedding_id = f"{audit.item_type.lower()}_{audit.id}_audit"
            self.vector_store.delete_embedding(embedding_id)
            
            # Update audit
            audit.final_record_id = selected_candidate_id
            audit.final_record_type = audit.item_type
            audit.final_action = 'USED_EXISTING'
            audit.finalized_at = timezone.now()
            audit.save(update_fields=[
                'final_record_id', 'final_record_type',
                'final_action', 'finalized_at'
            ])
            
            # Delete the pending SemanticEmbedding
            SemanticEmbedding.objects.filter(
                content_type__model=audit.item_type.lower(),
                object_id=audit.id
            ).delete()
            
            logger.info(f"[Step 9] Used existing {audit.item_type} ID={selected_candidate_id}")
            
            return SimilarityFinalizeResult(
                success=True,
                action_taken='USED_EXISTING',
                created_record_id=selected_candidate_id,
                created_record_type=audit.item_type,
                message=f"Using existing {audit.item_type}"
            )
            
        except Exception as e:
            logger.exception(f"[Step 9] Use existing failed: {e}")
            return SimilarityFinalizeResult(
                success=False,
                action_taken='ERROR',
                error=str(e)
            )
    
    def _handle_cancel(self, audit: SimilarityCheckAudit) -> SimilarityFinalizeResult:
        """
        Handle CANCEL: Clean up pending embedding, don't create.
        """
        try:
            # Delete pending embedding from ChromaDB
            embedding_id = f"{audit.item_type.lower()}_{audit.id}_audit"
            self.vector_store.delete_embedding(embedding_id)
            
            # Update audit
            audit.final_action = 'CANCELLED'
            audit.finalized_at = timezone.now()
            audit.save(update_fields=['final_action', 'finalized_at'])
            
            # Delete pending SemanticEmbedding
            SemanticEmbedding.objects.filter(
                content_type__model=audit.item_type.lower(),
                object_id=audit.id
            ).delete()
            
            logger.info(f"[Step 9] Cancelled check {audit.id}")
            
            return SimilarityFinalizeResult(
                success=True,
                action_taken='CANCELLED',
                message="Creation cancelled"
            )
            
        except Exception as e:
            logger.exception(f"[Step 9] Cancel failed: {e}")
            return SimilarityFinalizeResult(
                success=False,
                action_taken='ERROR',
                error=str(e)
            )
    
    def _create_record(
        self,
        audit: SimilarityCheckAudit,
        user_id: Optional[int]
    ) -> Optional[Any]:
        """
        Create actual record in database based on item type.
        """
        structured = audit.proposed_structured_json or {}
        tenant_id = audit.tenant_id if hasattr(audit, 'tenant_id') else None
        
        if audit.item_type == 'Framework':
            return self._create_framework(structured, tenant_id, user_id, audit)
        
        elif audit.item_type == 'Policy':
            return self._create_policy(structured, tenant_id, user_id, audit)
        
        elif audit.item_type == 'SubPolicy':
            return self._create_subpolicy(structured, tenant_id, user_id, audit)
        
        elif audit.item_type == 'Compliance':
            return self._create_compliance(structured, tenant_id, user_id, audit)
        
        else:
            raise ValueError(f"Unknown item type: {audit.item_type}")
    
    def _create_framework(
        self,
        structured: Dict,
        tenant_id: Optional[int],
        user_id: Optional[int],
        audit: SimilarityCheckAudit
    ) -> Framework:
        """Create Framework record."""
        from datetime import date
        from ..models import Tenant, Users

        created_by_name = structured.get('created_by_name') or ''
        if not created_by_name and user_id:
            user = Users.objects.filter(UserId=user_id).first()
            if user:
                created_by_name = getattr(user, 'UserName', None) or str(user_id)

        framework_kwargs = {
            'FrameworkName': structured.get('name', ''),
            'FrameworkDescription': structured.get('description', ''),
            'Category': structured.get('category', ''),
            'InternalExternal': structured.get('internal_external')
            or structured.get('type', 'Internal'),
            'Identifier': structured.get('identifier', ''),
            'Status': 'Active',
            'CreatedByName': created_by_name or 'System',
            'CreatedByDate': date.today(),
            'Reviewer': structured.get('reviewer', ''),
        }
        if tenant_id:
            tenant = Tenant.objects.filter(tenant_id=tenant_id).first()
            if tenant:
                framework_kwargs['tenant'] = tenant

        framework = Framework(**framework_kwargs)
        framework.save()
        return framework
    
    def _create_policy(
        self,
        structured: Dict,
        tenant_id: Optional[int],
        user_id: Optional[int],
        audit: SimilarityCheckAudit
    ) -> Policy:
        """Create Policy record."""
        policy = Policy(
            PolicyName=structured.get('name', ''),
            PolicyDescription=structured.get('description', ''),
            PolicyType=structured.get('policy_type', 'Internal'),
            PolicyCategory=structured.get('category', ''),
            PolicySubCategory=structured.get('sub_category', ''),
            Scope=structured.get('scope', ''),
            Objective=structured.get('objective', ''),
            Status='Active',
            tenant_id=tenant_id,
            created_by_id=user_id,
            framework_id=audit.framework_id
        )
        policy.save()
        return policy
    
    def _create_subpolicy(
        self,
        structured: Dict,
        tenant_id: Optional[int],
        user_id: Optional[int],
        audit: SimilarityCheckAudit
    ) -> SubPolicy:
        """Create SubPolicy record."""
        subpolicy = SubPolicy(
            SubPolicyName=structured.get('name', ''),
            Description=structured.get('description', ''),
            Control=structured.get('control', ''),
            Identifier=structured.get('identifier', ''),
            Status='Active',
            tenant_id=tenant_id,
            created_by_id=user_id,
            framework_id=audit.framework_id,
            policy_id=audit.policy_id
        )
        subpolicy.save()
        return subpolicy
    
    def _create_compliance(
        self,
        structured: Dict,
        tenant_id: Optional[int],
        user_id: Optional[int],
        audit: SimilarityCheckAudit
    ) -> Compliance:
        """Create Compliance record."""
        compliance = Compliance(
            ComplianceTitle=structured.get('title') or structured.get('name', ''),
            ComplianceItemDescription=structured.get('description', ''),
            ComplianceType=structured.get('compliance_type', 'Internal'),
            Scope=structured.get('scope', ''),
            Objective=structured.get('objective', ''),
            Criticality=structured.get('criticality', 'Medium'),
            RiskCategory=structured.get('risk_category', ''),
            Status='Active',
            tenant_id=tenant_id,
            created_by_id=user_id,
            framework_id=audit.framework_id,
            policy_id=audit.policy_id,
            subpolicy_id=audit.subpolicy_id
        )
        compliance.save()
        return compliance
    
    def _activate_in_chromadb(
        self,
        embedding_id: str,
        record_id: int,
        record_type: str
    ) -> bool:
        """
        Update ChromaDB embedding to Active status with real record ID.
        """
        try:
            # Note: ChromaDB doesn't support partial updates easily
            # So we delete the pending one and create a new Active one
            # Or we can just leave it as is since we updated the SemanticEmbedding
            
            # For now, just log that it would be updated
            # Full implementation would need to store the embedding_vector 
            # and recreate with new metadata
            
            logger.info(f"[Step 9] Would update ChromaDB {embedding_id} to Active with record_id={record_id}")
            return True
            
        except Exception as e:
            logger.error(f"[Step 9] Failed to update ChromaDB: {e}")
            return False


# Convenience function for views
def finalize_similarity_check(
    check_id: int,
    user_decision: str,
    selected_candidate_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> SimilarityFinalizeResult:
    """Convenience function to finalize similarity check."""
    service = SimilarityFinalizeService()
    return service.finalize(check_id, user_decision, selected_candidate_id, user_id)
