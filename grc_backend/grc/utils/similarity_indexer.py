"""
Utility to auto-index a GRC record into ChromaDB after creation.
Call index_record() after any Framework/Policy/SubPolicy/Compliance is saved.
Failures are logged but never raise — indexing must never break the main flow.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def index_record(instance, record_type: str, tenant_id: Optional[int] = None):
    """
    Generate an embedding for `instance` and store it in ChromaDB.
    Safe to call anywhere — exceptions are caught and logged only.
    """
    try:
        from ..services.embedding_service import EmbeddingService
        from ..services.vector_store_service import VectorStoreService
        from ..utils.text_cleaner import TextCleaner

        text_cleaner = TextCleaner()
        embedding_service = EmbeddingService()
        vector_store = VectorStoreService()

        if record_type == 'Framework':
            data = {
                'FrameworkName': instance.FrameworkName or '',
                'FrameworkDescription': instance.FrameworkDescription or '',
                'Category': instance.Category or '',
                'InternalExternal': instance.InternalExternal or '',
                'Identifier': instance.Identifier or '',
            }
            cleaned = text_cleaner.clean_framework(data)
            embedding_id = f'framework_{instance.FrameworkId}'
            name = instance.FrameworkName or ''
            entity_id = instance.FrameworkId
            tid = str(getattr(instance, 'TenantId_id', tenant_id) or '')

        elif record_type == 'Policy':
            data = {
                'PolicyName': instance.PolicyName or '',
                'PolicyDescription': instance.PolicyDescription or '',
                'PolicyType': getattr(instance, 'PolicyType', '') or '',
                'PolicyCategory': getattr(instance, 'PolicyCategory', '') or '',
            }
            cleaned = text_cleaner.clean_policy(data)
            embedding_id = f'policy_{instance.PolicyId}'
            name = instance.PolicyName or ''
            entity_id = instance.PolicyId
            tid = str(getattr(instance, 'TenantId_id', tenant_id) or '')

        elif record_type == 'SubPolicy':
            data = {
                'SubPolicyName': instance.SubPolicyName or '',
                'Description': instance.Description or '',
                'Control': instance.Control or '',
                'Identifier': instance.Identifier or '',
            }
            cleaned = text_cleaner.clean_subpolicy(data)
            embedding_id = f'subpolicy_{instance.SubPolicyId}'
            name = instance.SubPolicyName or ''
            entity_id = instance.SubPolicyId
            tid = str(getattr(instance, 'TenantId_id', tenant_id) or '')

        elif record_type == 'Compliance':
            data = {
                'ComplianceTitle': instance.ComplianceTitle or '',
                'ComplianceItemDescription': instance.ComplianceItemDescription or '',
                'ComplianceType': getattr(instance, 'ComplianceType', '') or '',
                'Scope': getattr(instance, 'Scope', '') or '',
                'Identifier': getattr(instance, 'Identifier', '') or '',
            }
            cleaned = text_cleaner.clean_compliance(data)
            embedding_id = f'compliance_{instance.ComplianceId}'
            name = instance.ComplianceTitle or ''
            entity_id = instance.ComplianceId
            tid = str(getattr(instance, 'TenantId_id', tenant_id) or '')

        else:
            logger.warning(f'[SimilarityIndexer] Unknown record_type: {record_type}')
            return

        result = embedding_service.generate_embedding(cleaned.embedding_text)
        if result:
            vector_store.store_embedding(
                embedding_id=embedding_id,
                embedding_vector=result,
                entity_type=record_type,
                entity_id=entity_id,
                tenant_id=int(tid) if tid and str(tid).isdigit() else None,
                domain=None,
                category=None,
                name=name,
            )
            logger.info(f'[SimilarityIndexer] Indexed {record_type} {entity_id}: {name}')
        else:
            logger.warning(f'[SimilarityIndexer] Embedding failed for {record_type} {entity_id}')

    except Exception as e:
        logger.warning(f'[SimilarityIndexer] Auto-index failed for {record_type}: {e}')
