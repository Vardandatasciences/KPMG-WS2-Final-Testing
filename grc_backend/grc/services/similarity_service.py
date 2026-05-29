"""
Similarity Detection Service - Orchestrates the 9-step pipeline.

Step 1: Text Cleaning (IMPLEMENTED HERE)
Step 2: Domain Classification
Step 3: Embedding Creation
Step 4: Vector Search
Step 5: Cross-Encoder Reranker
Step 6: LLM Final Decision
Step 7: UI Suggestion
Step 8: User Choice
Step 9: Save to DB + Qdrant + Audit
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from django.utils import timezone

from django.db import transaction

from ..utils.text_cleaner import TextCleaner, CleaningResult
from ..services.domain_classifier import DomainClassifier, DomainClassificationResult
from ..services.embedding_service import EmbeddingService
from ..services.vector_store_service import VectorStoreService
from ..services.reranker_service import RerankerService
from ..services.llm_decision_service import LLMDecisionService, LLMDecisionResult
from ..models import Framework, Policy, SubPolicy, Compliance
from ..models_extensions.similarity_models import (
    SimilarityCheckAudit,
    SimilarityConfiguration,
    SemanticEmbedding,
)

logger = logging.getLogger(__name__)


def _parse_parent_id(value) -> Optional[int]:
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass
class SimilarityCheckRequest:
    """Request to check similarity for a new item."""
    item_type: str  # 'Framework', 'Policy', 'SubPolicy', 'Compliance'
    item_data: Dict[str, Any]  # Raw form data
    tenant_id: Optional[int] = None
    user_id: Optional[int] = None
    parent_framework_id: Optional[int] = None
    parent_policy_id: Optional[int] = None
    parent_subpolicy_id: Optional[int] = None
    exclude_entity_id: Optional[int] = None  # Edit mode: skip matching this DB record
    framework_context: Optional[Dict[str, Any]] = None  # In-memory context when framework not in DB yet
    policy_context: Optional[Dict[str, Any]] = None  # In-memory context when policy not in DB yet


@dataclass
class SimilarityCheckResponse:
    """Response from similarity check."""
    check_id: int  # SimilarityCheckAudit ID
    status: str  # 'PENDING', 'COMPLETED', 'FAILED'
    classification: Optional[str] = None  # 'DUPLICATE', 'SIMILAR', 'RELATED_BUT_DIFFERENT', 'DIFFERENT'
    candidates: List[Dict] = None
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    suggested_action: Optional[str] = None
    error: Optional[str] = None
    # Step results for debugging/testing
    step1_result: Any = None
    step2_result: Any = None
    step3_result: Any = None


class SimilarityService:
    """
    Service for similarity detection across Framework, Policy, SubPolicy, and Compliance.
    
    Implements the 9-step pipeline:
    1. Text Cleaning
    2. Domain Classification
    3. Embedding Creation
    4. Vector Search
    5. Cross-Encoder Reranker
    6. LLM Final Decision
    7. UI Suggestion
    8. User Choice
    9. Save Everything
    """
    
    def __init__(self, config: Optional[SimilarityConfiguration] = None):
        """
        Initialize similarity service.
        
        Args:
            config: Configuration object (uses default if not provided)
        """
        self.config = config or SimilarityConfiguration.get_for_tenant()
        self.text_cleaner = TextCleaner()
        self.domain_classifier = DomainClassifier()
        self.embedding_service = EmbeddingService()  # Step 3: Embedding Creation
        self.vector_store = VectorStoreService()  # Step 4: Vector Search
        try:
            self.reranker_service = RerankerService()  # Step 5: Reranker
        except Exception as e:
            logger.warning(f"[SimilarityService] Reranker unavailable, Step 5 will be skipped: {e}")
            self.reranker_service = None
        self.llm_decision_service = LLMDecisionService()  # Step 6: LLM Decision
        self._vector_db = None  # Lazy loaded
        self._embedding_model = None  # Lazy loaded
        self._reranker = None  # Lazy loaded
    
    # ==================== STEP 1: TEXT CLEANING ====================
    
    def step1_clean_text(self, request: SimilarityCheckRequest) -> Tuple[CleaningResult, SimilarityCheckAudit]:
        """
        Step 1: Clean text for the entity being created.
        
        Args:
            request: Similarity check request with raw item data
        
        Returns:
            Tuple of (CleaningResult, SimilarityCheckAudit)
        """
        logger.info(f"Step 1: Cleaning text for {request.item_type}")
        
        # Create audit record
        audit = SimilarityCheckAudit.objects.create(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            item_type=request.item_type,
            proposed_name=self._extract_name(request),
            proposed_description=self._extract_description(request),
            framework_id=request.parent_framework_id,
            policy_id=request.parent_policy_id,
            subpolicy_id=request.parent_subpolicy_id,
            check_status='PENDING',
        )
        
        try:
            # Normalize frontend field names to backend TextCleaner expected names
            item_data = request.item_data or {}
            if request.item_type == 'Framework':
                normalized = {
                    'FrameworkName': item_data.get('FrameworkName') or item_data.get('name', ''),
                    'FrameworkDescription': item_data.get('FrameworkDescription') or item_data.get('description', ''),
                    'Category': item_data.get('Category') or item_data.get('category', ''),
                    'Domain': item_data.get('Domain') or item_data.get('domain', ''),
                    'InternalExternal': item_data.get('InternalExternal') or item_data.get('type', ''),
                    'Identifier': item_data.get('Identifier') or item_data.get('identifier', ''),
                }
                cleaning_result = self.text_cleaner.clean_framework(normalized)
            elif request.item_type == 'Policy':
                normalized = {
                    'PolicyName': item_data.get('PolicyName') or item_data.get('name', ''),
                    'PolicyDescription': item_data.get('PolicyDescription') or item_data.get('description', ''),
                    'PolicyType': item_data.get('PolicyType') or item_data.get('type', ''),
                    'PolicyCategory': item_data.get('PolicyCategory') or item_data.get('category', ''),
                }
                cleaning_result = self.text_cleaner.clean_policy(normalized)
            elif request.item_type == 'SubPolicy':
                normalized = {
                    'SubPolicyName': item_data.get('SubPolicyName') or item_data.get('name', ''),
                    'Description': item_data.get('Description') or item_data.get('description', ''),
                    'Control': item_data.get('Control') or item_data.get('control', ''),
                    'Identifier': item_data.get('Identifier') or item_data.get('identifier', ''),
                }
                cleaning_result = self.text_cleaner.clean_subpolicy(normalized)
            elif request.item_type == 'Compliance':
                normalized = {
                    'ComplianceTitle': item_data.get('ComplianceTitle') or item_data.get('name', ''),
                    'ComplianceItemDescription': item_data.get('ComplianceItemDescription') or item_data.get('description', ''),
                    'ComplianceType': item_data.get('ComplianceType') or item_data.get('type', ''),
                    'Scope': item_data.get('Scope') or item_data.get('scope', ''),
                    'Identifier': item_data.get('Identifier') or item_data.get('identifier', ''),
                }
                cleaning_result = self.text_cleaner.clean_compliance(normalized)
            else:
                raise ValueError(f"Unknown item type: {request.item_type}")
            
            # Update audit with both structured JSON and embedding text
            audit.proposed_structured_json = cleaning_result.structured_json
            audit.proposed_cleaned_text = cleaning_result.embedding_text
            audit.save(update_fields=['proposed_structured_json', 'proposed_cleaned_text'])
            
            logger.info(f"Step 1 complete: Structured JSON created, Embedding text length {len(cleaning_result.embedding_text)}")
            logger.debug(f"Changes made: {cleaning_result.changes_made}")
            
            return cleaning_result, audit
            
        except Exception as e:
            logger.exception(f"Step 1 failed: {e}")
            audit.mark_failed(f"Text cleaning failed: {str(e)}")
            raise
    
    # ==================== STEP 2: DOMAIN CLASSIFICATION ====================
    
    def step2_classify_domain(self, request: SimilarityCheckRequest, 
                             cleaning_result: CleaningResult,
                             audit: SimilarityCheckAudit) -> DomainClassificationResult:
        """
        Step 2: Classify domain with hierarchical context.
        
        Framework: Uses its own fields
        Policy: Uses Framework context + Policy fields
        SubPolicy: Uses Framework + Policy context
        Compliance: Uses full hierarchy context
        
        Args:
            request: Similarity check request
            cleaning_result: Result from Step 1
            audit: Audit record to update
            
        Returns:
            DomainClassificationResult with full classification
        """
        logger.info(f"[STEP 2] Starting domain classification for {request.item_type}")
        
        try:
            structured = cleaning_result.structured_json
            
            if request.item_type == 'Framework':
                # Framework: Use its own fields
                framework_data = {
                    'name': structured.get('name', ''),
                    'description': structured.get('description', ''),
                    'category': structured.get('category', ''),
                    'type': structured.get('type', ''),
                    'identifier': structured.get('identifier', '')
                }
                classification = self.domain_classifier.classify_framework(framework_data)
                
            elif request.item_type == 'Policy':
                # Policy: Use in-memory context or fetch from DB (new framework may not exist yet)
                if request.framework_context:
                    framework_context = request.framework_context
                elif request.parent_framework_id:
                    framework_context = {
                        'domain': 'Unknown',
                        'industry_vertical': None,
                        'name': ''
                    }
                    try:
                        from ..models import Framework
                        framework = Framework.objects.get(FrameworkId=int(request.parent_framework_id))
                        framework_context = {
                            'domain': framework.Category or 'Unknown',
                            'industry_vertical': None,
                            'name': framework.FrameworkName
                        }
                    except Exception as fw_err:
                        logger.warning(f"[STEP 2] Framework context unavailable: {fw_err}")
                else:
                    framework_context = {
                        'domain': 'Unknown',
                        'industry_vertical': None,
                        'name': ''
                    }
                
                policy_data = {
                    'name': structured.get('name', ''),
                    'description': structured.get('description', ''),
                    'policy_type': structured.get('policy_type', ''),
                    'category': structured.get('category', ''),
                    'sub_category': structured.get('sub_category', ''),
                    'scope': structured.get('scope', ''),
                    'objective': structured.get('objective', '')
                }
                classification = self.domain_classifier.classify_policy(policy_data, framework_context)
                
            elif request.item_type == 'SubPolicy':
                # SubPolicy: Use provided context or fetch from DB
                framework_context = {'domain': 'Unknown', 'industry_vertical': None, 'name': ''}
                if request.parent_framework_id:
                    try:
                        from ..models import Framework
                        framework = Framework.objects.get(FrameworkId=int(request.parent_framework_id))
                        framework_context = {
                            'domain': framework.Category or 'Unknown',
                            'industry_vertical': None,
                            'name': framework.FrameworkName
                        }
                    except Exception as fw_err:
                        logger.warning(f"[STEP 2] Framework context unavailable: {fw_err}")

                policy_context = {'business_function': '', 'compliance_area': '', 'name': ''}
                if request.parent_policy_id:
                    try:
                        from ..models import Policy
                        policy = Policy.objects.get(PolicyId=int(request.parent_policy_id))
                        policy_context = {
                            'business_function': policy.PolicyCategory,
                            'compliance_area': policy.PolicySubCategory,
                            'name': policy.PolicyName
                        }
                    except Exception as pol_err:
                        logger.warning(f"[STEP 2] Policy context unavailable (new/unsaved policy?): {pol_err}")
                
                subpolicy_data = {
                    'name': structured.get('name', ''),
                    'description': structured.get('description', ''),
                    'control': structured.get('control', ''),
                    'identifier': structured.get('identifier', '')
                }
                classification = self.domain_classifier.classify_subpolicy(
                    subpolicy_data, framework_context, policy_context
                )
                
            elif request.item_type == 'Compliance':
                # Compliance: Use provided context or fetch full hierarchy (tolerant of stale/missing FKs)
                framework_context = getattr(request, 'framework_context', None)
                policy_context = getattr(request, 'policy_context', None)
                subpolicy_context = getattr(request, 'subpolicy_context', None)

                fw_id = _parse_parent_id(request.parent_framework_id)
                pol_id = _parse_parent_id(request.parent_policy_id)
                sub_id = _parse_parent_id(request.parent_subpolicy_id)

                if not framework_context and fw_id:
                    from ..models import Framework
                    framework = Framework.objects.filter(FrameworkId=fw_id).first()
                    if framework:
                        framework_context = {
                            'domain': framework.Category or 'Unknown',
                            'industry_vertical': None,
                            'name': framework.FrameworkName,
                        }

                if not policy_context and pol_id:
                    from ..models import Policy
                    policy = Policy.objects.filter(PolicyId=pol_id).first()
                    if policy:
                        policy_context = {
                            'business_function': policy.PolicyCategory,
                            'compliance_area': policy.PolicySubCategory,
                            'name': policy.PolicyName,
                        }

                if not subpolicy_context and sub_id:
                    from ..models import SubPolicy
                    subpolicy = SubPolicy.objects.filter(SubPolicyId=sub_id).first()
                    if subpolicy:
                        subpolicy_context = {
                            'control_type': None,
                            'control_category': None,
                            'name': subpolicy.SubPolicyName,
                        }
                    elif pol_id:
                        policy = Policy.objects.filter(PolicyId=pol_id).first()
                        if policy:
                            subpolicy_context = {
                                'control_type': None,
                                'control_category': None,
                                'name': policy.PolicyName,
                            }

                framework_context = framework_context or {
                    'domain': 'Unknown',
                    'industry_vertical': None,
                    'name': '',
                }
                policy_context = policy_context or {
                    'business_function': None,
                    'compliance_area': None,
                    'name': '',
                }
                subpolicy_context = subpolicy_context or {
                    'control_type': None,
                    'control_category': None,
                    'name': '',
                }
                
                compliance_data = {
                    'title': structured.get('title', ''),
                    'description': structured.get('description', ''),
                    'compliance_type': structured.get('compliance_type', ''),
                    'criticality': structured.get('criticality', ''),
                    'risk_category': structured.get('risk_category', ''),
                    'scope': structured.get('scope', ''),
                    'objective': structured.get('objective', '')
                }
                classification = self.domain_classifier.classify_compliance(
                    compliance_data, framework_context, policy_context, subpolicy_context
                )
            else:
                raise ValueError(f"Unknown item type: {request.item_type}")
            
            # Save classification results to audit
            audit.classified_primary_domain = classification.primary_domain
            audit.classified_industry_vertical = classification.industry_vertical
            audit.classified_business_function = classification.business_function
            audit.classified_compliance_area = classification.compliance_area
            audit.classified_control_type = classification.control_type
            audit.classified_risk_category = classification.risk_category
            audit.classification_confidence = classification.confidence
            audit.classification_method = classification.classification_method
            audit.classification_reasoning = classification.reasoning
            audit.classification_context_used = classification.context_used
            audit.save(update_fields=[
                'classified_primary_domain', 'classified_industry_vertical',
                'classified_business_function', 'classified_compliance_area',
                'classified_control_type', 'classified_risk_category',
                'classification_confidence', 'classification_method',
                'classification_reasoning', 'classification_context_used'
            ])
            
            logger.info(f"[STEP 2] Domain classification complete: {classification.primary_domain} "
                       f"(confidence: {classification.confidence:.2f}, method: {classification.classification_method})")
            
            return classification
            
        except Exception as e:
            logger.exception(f"[STEP 2] Domain classification failed: {e}")
            # Return fallback classification
            return DomainClassificationResult(
                primary_domain='Unknown',
                industry_vertical=None,
                business_function=None,
                compliance_area=None,
                control_type=None,
                risk_category=None,
                confidence=0.0,
                classification_method='fallback',
                reasoning=f'Classification failed: {str(e)}',
                context_used={}
            )
    
    # ==================== STEP 3: EMBEDDING CREATION ====================
    
    def step3_generate_embedding(self, 
                                 request: SimilarityCheckRequest,
                                 classification_result: DomainClassificationResult,
                                 audit: SimilarityCheckAudit) -> Dict[str, Any]:
        """
        Step 3: Generate embedding vector from classified text.
        
        Flow:
        1. Build rich embedding text from audit + classification
        2. Send to BGE-M3 to generate vector
        3. Store in semantic_embeddings table
        4. Return embedding data for Step 4
        
        Args:
            request: Original similarity check request
            classification_result: Result from Step 2 domain classification
            audit: Audit record with cleaned text and classification
            
        Returns:
            Dict with embedding_text, embedding_vector, and metadata
        """
        from ..models_extensions.similarity_models import SemanticEmbedding
        
        logger.info(f"[STEP 3] Starting embedding generation for {request.item_type}")
        
        try:
            # Step 3.1: Build rich embedding text
            embedding_text = self.embedding_service.build_embedding_text(
                request.item_type, 
                audit
            )
            logger.info(f"[STEP 3] Embedding text prepared: {len(embedding_text)} chars")
            
            # Step 3.2: Generate vector using BGE-M3
            embedding_vector = self.embedding_service.generate_embedding(embedding_text)
            logger.info(f"[STEP 3] Vector generated: {len(embedding_vector)} dimensions")
            
            # Step 3.3: Compute text hash for change detection
            text_hash = self.embedding_service.compute_text_hash(embedding_text)
            
            # Step 3.4: Store in semantic_embeddings table
            from django.contrib.contenttypes.models import ContentType
            
            # Get content type for the entity
            content_type_mapping = {
                'Framework': ContentType.objects.get_for_model(Framework),
                'Policy': ContentType.objects.get_for_model(Policy),
                'SubPolicy': ContentType.objects.get_for_model(SubPolicy),
                'Compliance': ContentType.objects.get_for_model(Compliance)
            }
            content_type = content_type_mapping.get(request.item_type)
            
            # Create or update semantic embedding record
            embedding_record, created = SemanticEmbedding.objects.update_or_create(
                content_type=content_type,
                object_id=audit.id,  # Use audit ID as reference
                defaults={
                    'tenant': audit.tenant,
                    'embedding_vector': embedding_vector,
                    'embedding_model': self.embedding_service.model_name,
                    'embedding_dimension': self.embedding_service.dimension,
                    'text_hash': text_hash,
                    'source_text': embedding_text[:1000],  # Store first 1000 chars for debugging
                    'entity_type': request.item_type,
                    'domain': classification_result.primary_domain,
                    'category': audit.proposed_structured_json.get('category', '') if audit.proposed_structured_json else ''
                }
            )
            
            logger.info(f"[STEP 3] Embedding stored in MySQL: ID={embedding_record.id}, created={created}")
            
            # Step 3.5: Also store in ChromaDB for vector search (Step 4)
            # Convert compliance_area to string if it's a list
            category_value = classification_result.compliance_area or classification_result.business_function
            if isinstance(category_value, list):
                category_value = ', '.join(category_value) if category_value else ''
            
            chroma_id = f"{request.item_type.lower()}_{audit.id}_audit"
            chroma_stored = self.vector_store.store_embedding(
                embedding_id=chroma_id,
                embedding_vector=embedding_vector,
                entity_type=request.item_type,
                entity_id=audit.id,
                tenant_id=request.tenant_id,
                domain=classification_result.primary_domain,
                category=category_value,
                name=audit.proposed_name,
                status="Pending",
                parent_framework_id=request.parent_framework_id,
                parent_policy_id=request.parent_policy_id,
                parent_subpolicy_id=request.parent_subpolicy_id
            )
            logger.info(f"[STEP 3] Embedding stored in ChromaDB: {chroma_stored}")
            
            # Step 3.6: Update audit record
            audit.embedding_text = embedding_text
            audit.embedding_generated_at = timezone.now()
            audit.save(update_fields=['embedding_text', 'embedding_generated_at'])
            
            logger.info(f"[STEP 3] Complete for {request.item_type}")
            
            return {
                'embedding_text': embedding_text,
                'embedding_vector': embedding_vector,
                'embedding_dimension': self.embedding_service.dimension,
                'embedding_model': self.embedding_service.model_name,
                'text_hash': text_hash,
                'semantic_embedding_id': embedding_record.id
            }
            
        except Exception as e:
            logger.exception(f"[STEP 3] Embedding generation failed: {e}")
            # Return fallback with empty embedding
            return {
                'embedding_text': '',
                'embedding_vector': [0.0] * self.embedding_service.dimension,
                'embedding_dimension': self.embedding_service.dimension,
                'embedding_model': self.embedding_service.model_name,
                'text_hash': '',
                'semantic_embedding_id': None,
                'error': str(e)
            }
    
    # ==================== STEP 4: VECTOR SEARCH ====================
    
    def step4_search_similar(
        self,
        request: SimilarityCheckRequest,
        embedding_result: Dict[str, Any],
        classification_result: DomainClassificationResult,
        audit: SimilarityCheckAudit
    ) -> List[Dict[str, Any]]:
        """
        Step 4: Search for similar records using ChromaDB vector search.
        
        Args:
            request: Original similarity check request
            embedding_result: Output from Step 3 (contains embedding_vector)
            classification_result: Output from Step 2 (contains domain, etc.)
            audit: Audit record for this check
            
        Returns:
            List of candidate records with similarity scores
        """
        try:
            logger.info(f"[STEP 4] Vector Search for {request.item_type}")
            
            # Get the embedding vector
            embedding_vector = embedding_result.get('embedding_vector')
            if not embedding_vector or embedding_vector == [0.0] * self.embedding_service.dimension:
                logger.warning("[STEP 4] No valid embedding vector, skipping search")
                return []
            
            parent_fw_id = _parse_parent_id(request.parent_framework_id)
            parent_pol_id = _parse_parent_id(request.parent_policy_id)
            parent_subpol_id = _parse_parent_id(request.parent_subpolicy_id)

            # Build search filters based on entity type
            domain_filter = (
                classification_result.primary_domain.replace(' ', '').lower()
                if classification_result.primary_domain
                and classification_result.primary_domain.lower() != 'unknown'
                else None
            )
            # Version/edit: strict domain often leaves only the record being excluded (e.g. FDA fw 352).
            if request.item_type == 'Framework' and request.exclude_entity_id:
                logger.info(
                    "[STEP 4] Framework edit/version (exclude_entity_id=%s) — "
                    "skipping domain filter so other frameworks can match",
                    request.exclude_entity_id,
                )
                domain_filter = None
            # Bulk index + runtime indexer store domain as "Unknown"; LLM domain never matches in Chroma.
            elif request.item_type in ('SubPolicy', 'Compliance'):
                logger.info(
                    "[STEP 4] %s search — skipping domain filter (indexed metadata uses Unknown)",
                    request.item_type,
                )
                domain_filter = None

            search_params = {
                'query_vector': embedding_vector,
                'entity_type': request.item_type,
                'tenant_id': request.tenant_id,
                'domain': domain_filter,
                'top_k': 20,
                'min_score': 0.55
            }
            
            # Add entity-specific filters
            if request.item_type == 'Policy':
                if parent_fw_id:
                    search_params['parent_framework_id'] = parent_fw_id
                search_params['category'] = audit.proposed_structured_json.get('category') if audit.proposed_structured_json else None
                
            elif request.item_type == 'SubPolicy':
                if parent_pol_id:
                    search_params['parent_policy_id'] = parent_pol_id
                if parent_fw_id:
                    search_params['parent_framework_id'] = parent_fw_id
                
            elif request.item_type == 'Compliance':
                if parent_subpol_id:
                    search_params['parent_subpolicy_id'] = parent_subpol_id
                if parent_pol_id:
                    search_params['parent_policy_id'] = parent_pol_id
                if parent_fw_id:
                    search_params['parent_framework_id'] = parent_fw_id
            
            # For Framework: search only other frameworks (no parent filters)

            def _without_audit_hits(hits):
                return [
                    c for c in hits
                    if not str(c.get('id', '')).endswith('_audit')
                    and c.get('status') != 'Pending'
                ]

            # Execute search with progressive filter relaxation
            candidates = self.vector_store.search_similar(**search_params)

            if not candidates and search_params.get('domain'):
                logger.info(
                    f"[STEP 4] Domain filter '{search_params['domain']}' returned 0, "
                    "retrying without domain"
                )
                relaxed = search_params.copy()
                relaxed.pop('domain', None)
                candidates = self.vector_store.search_similar(**relaxed)

            if not candidates and request.item_type == 'Framework':
                logger.info(
                    "[STEP 4] Framework search still empty, retrying with lower min_score (0.42)"
                )
                relaxed = {k: v for k, v in search_params.items() if k != 'domain'}
                candidates = _without_audit_hits(
                    self.vector_store.search_similar(
                        query_vector=relaxed['query_vector'],
                        entity_type=relaxed['entity_type'],
                        tenant_id=request.tenant_id,
                        top_k=relaxed.get('top_k', 20),
                        min_score=0.42,
                    )
                )
            if not candidates and request.item_type == 'Framework':
                logger.info(
                    "[STEP 4] Framework search still empty — retry without tenant filter "
                    "(run: python manage.py index_existing_records --type Framework --tenant_id=%s)",
                    request.tenant_id or '?',
                )
                relaxed = {k: v for k, v in search_params.items() if k != 'domain'}
                candidates = _without_audit_hits(
                    self.vector_store.search_similar(
                        query_vector=relaxed['query_vector'],
                        entity_type=relaxed['entity_type'],
                        tenant_id=None,
                        top_k=relaxed.get('top_k', 20),
                        min_score=0.42,
                    )
                )

            # Indexed policies often have parent_framework_id=0; form sends real FrameworkId
            if not candidates and request.item_type == 'Policy' and search_params.get('parent_framework_id'):
                logger.info(
                    f"[STEP 4] parent_framework_id={search_params['parent_framework_id']} "
                    "returned 0, retrying without framework/category filters"
                )
                relaxed = {
                    k: v for k, v in search_params.items()
                    if k not in ('domain', 'parent_framework_id', 'category')
                }
                candidates = self.vector_store.search_similar(**relaxed)

            # Exclude pending audit scratch embeddings from prior Suggest clicks
            candidates = _without_audit_hits(candidates)

            if not candidates and request.item_type == 'SubPolicy' and (
                search_params.get('parent_policy_id') or search_params.get('parent_framework_id')
                or search_params.get('domain')
            ):
                logger.info(
                    "[STEP 4] SubPolicy search empty after filters/audit cleanup, "
                    "retrying without domain/parent filters"
                )
                relaxed = {
                    k: v for k, v in search_params.items()
                    if k not in ('domain', 'parent_framework_id', 'parent_policy_id')
                }
                candidates = _without_audit_hits(self.vector_store.search_similar(**relaxed))

            if not candidates and request.item_type == 'SubPolicy':
                logger.info(
                    "[STEP 4] SubPolicy search still empty, retrying with lower min_score (0.42)"
                )
                relaxed = {
                    k: v for k, v in search_params.items()
                    if k not in ('domain', 'parent_framework_id', 'parent_policy_id')
                }
                candidates = _without_audit_hits(
                    self.vector_store.search_similar(
                        query_vector=relaxed['query_vector'],
                        entity_type=relaxed['entity_type'],
                        tenant_id=relaxed.get('tenant_id'),
                        top_k=relaxed.get('top_k', 20),
                        min_score=0.42,
                    )
                )
            if not candidates and request.item_type == 'SubPolicy':
                logger.info(
                    "[STEP 4] SubPolicy search still empty — retry without tenant filter "
                    "(run: python manage.py index_existing_records --type SubPolicy --tenant_id=%s)",
                    request.tenant_id or '?',
                )
                relaxed = {
                    k: v for k, v in search_params.items()
                    if k not in ('domain', 'parent_framework_id', 'parent_policy_id')
                }
                candidates = _without_audit_hits(
                    self.vector_store.search_similar(
                        query_vector=relaxed['query_vector'],
                        entity_type=relaxed['entity_type'],
                        tenant_id=None,
                        top_k=relaxed.get('top_k', 20),
                        min_score=0.42,
                    )
                )

            if not candidates and request.item_type == 'Compliance' and (
                search_params.get('parent_subpolicy_id')
                or search_params.get('parent_policy_id')
                or search_params.get('parent_framework_id')
                or search_params.get('domain')
            ):
                logger.info(
                    "[STEP 4] Compliance search empty after filters/audit cleanup, "
                    "retrying without domain/parent filters"
                )
                relaxed = {
                    k: v for k, v in search_params.items()
                    if k not in (
                        'domain', 'parent_framework_id', 'parent_policy_id', 'parent_subpolicy_id'
                    )
                }
                candidates = _without_audit_hits(self.vector_store.search_similar(**relaxed))

            # Exclude record being edited (update/save flows)
            if request.exclude_entity_id is not None:
                try:
                    exclude_id = int(request.exclude_entity_id)
                    before = len(candidates)
                    candidates = [
                        c for c in candidates
                        if int(c.get('entity_id', -1)) != exclude_id
                    ]
                    if before and not candidates:
                        logger.info(
                            "[STEP 4] exclude_entity_id=%s removed all %s match(es); "
                            "other similar frameworks may still exist in Chroma",
                            exclude_id,
                            before,
                        )
                except (TypeError, ValueError):
                    pass

            # Filter out self-matches (don't compare record with itself)
            # Current record ID format: "{type}_{audit_id}_audit"
            current_embedding_id = f"{request.item_type.lower()}_{audit.id}_audit"
            candidates = [c for c in candidates if c.get('id') != current_embedding_id]
            
            # Also store the new embedding in ChromaDB for future searches
            # (This makes it available for similarity checks going forward)
            if embedding_result.get('semantic_embedding_id'):
                embedding_id = f"{request.item_type.lower()}_{audit.id}_audit"
                # Convert to string if list
                step4_category = classification_result.compliance_area or classification_result.business_function
                if isinstance(step4_category, list):
                    step4_category = ', '.join(step4_category) if step4_category else ''
                
                self.vector_store.store_embedding(
                    embedding_id=embedding_id,
                    embedding_vector=embedding_vector,
                    entity_type=request.item_type,
                    entity_id=audit.id,  # Using audit ID as reference
                    tenant_id=request.tenant_id,
                    domain=classification_result.primary_domain,
                    category=step4_category,
                    name=audit.proposed_name,
                    status="Pending",  # Will update to Active after user confirms creation
                    parent_framework_id=request.parent_framework_id,
                    parent_policy_id=request.parent_policy_id,
                    parent_subpolicy_id=request.parent_subpolicy_id,
                    additional_metadata={
                        'audit_id': str(audit.id),
                        'classification_method': classification_result.classification_method
                    }
                )
            
            logger.info(f"[STEP 4] Found {len(candidates)} similar candidates")
            return candidates
            
        except Exception as e:
            logger.exception(f"[STEP 4] Vector search failed: {e}")
            return []
    
    # ==================== STEP 5: CROSS-ENCODER RERANKER ====================
    
    def step5_rerank_candidates(
        self,
        request: SimilarityCheckRequest,
        candidates: List[Dict[str, Any]],
        audit: SimilarityCheckAudit
    ) -> List[Dict[str, Any]]:
        """
        Step 5: Rerank candidates using cross-encoder for accurate similarity.
        
        Takes top candidates from Step 4 (ChromaDB) and uses BGE reranker
        to compute more accurate similarity scores by comparing text pairs.
        
        Args:
            request: Similarity check request
            candidates: List of candidates from Step 4
            audit: Audit record for tracking
        
        Returns:
            Reranked list of top candidates (default top 5)
            Each candidate has 'reranker_score' field added
        """
        try:
            logger.info(f"[STEP 5] Reranking {len(candidates)} candidates")
            
            if not candidates:
                logger.warning("[STEP 5] No candidates to rerank")
                return []
            
            # Skip reranking if model not available (e.g. insufficient memory)
            if self.reranker_service is None:
                logger.warning("[STEP 5] Reranker unavailable, returning top candidates by vector score")
                return sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)[:5]
            
            # Get the query text (new record's embedding text)
            query_text = audit.embedding_text
            if not query_text:
                logger.warning("[STEP 5] No embedding text for query, using cleaned text")
                query_text = f"{audit.proposed_name}\n{audit.proposed_description}"
            
            # Rerank candidates using cross-encoder
            # Returns top 5 by default
            reranked = self.reranker_service.rerank_candidates(
                query_text=query_text,
                candidates=candidates,
                top_k=5  # Send top 5 to Step 6 (LLM)
            )
            
            logger.info(f"[STEP 5] Reranking complete. Top candidate: {reranked[0].get('name', 'N/A') if reranked else 'None'}")
            
            return reranked
            
        except Exception as e:
            logger.exception(f"[STEP 5] Reranking failed: {e}")
            # Return original candidates sorted by ChromaDB score as fallback
            return sorted(
                candidates,
                key=lambda x: x.get('score', 0),
                reverse=True
            )[:5]
    
    # ==================== STEP 6: LLM FINAL DECISION ====================
    
    def step6_llm_decision(
        self,
        request: SimilarityCheckRequest,
        cleaning_result: CleaningResult,
        classification_result: DomainClassificationResult,
        reranked_candidates: List[Dict[str, Any]],
        audit: SimilarityCheckAudit
    ) -> LLMDecisionResult:
        """
        Step 6: LLM Final Decision and Explanation.
        
        Analyzes top reranked candidates with LLM to provide:
        - Final classification (duplicate, highly_similar, related_but_different, different)
        - Detailed reasoning
        - User recommendations (use_existing, create_anyway, review_manually, merge)
        
        Args:
            request: Similarity check request
            cleaning_result: Step 1 cleaned record data
            classification_result: Step 2 classification
            reranked_candidates: Top candidates from Step 5
            audit: Audit record
        
        Returns:
            LLMDecisionResult with final analysis
        """
        try:
            logger.info(f"[STEP 6] LLM Decision for {len(reranked_candidates)} candidates")
            
            if not reranked_candidates:
                logger.warning("[STEP 6] No candidates to analyze")
                return LLMDecisionResult(
                    can_create=True,
                    duplicate_risk="low",
                    overall_recommendation="No similar records found. Safe to create.",
                    suggestions=[]
                )
            
            # Prepare new record data from structured_json
            structured = cleaning_result.structured_json
            new_record = {
                "name": structured.get('name') or structured.get('title', ''),
                "description": structured.get('description', ''),
                "purpose": structured.get('purpose', ''),
                "scope": structured.get('scope', ''),
                "sub_category": structured.get('sub_category') or structured.get('category', ''),
                "control_objective": structured.get('control_objective') or structured.get('objective', ''),
                "evidence_requirement": structured.get('evidence_requirement', '')
            }
            
            # Get LLM decision
            decision = self.llm_decision_service.analyze_candidates(
                new_record=new_record,
                classification_result=classification_result,
                candidates=reranked_candidates
            )
            
            logger.info(f"[STEP 6] Decision: can_create={decision.can_create}, risk={decision.duplicate_risk}")
            
            return decision
            
        except Exception as e:
            logger.exception(f"[STEP 6] LLM decision failed: {e}")
            # Return safe default allowing creation
            return LLMDecisionResult(
                can_create=True,
                duplicate_risk="unknown",
                overall_recommendation="Analysis failed. Please review manually.",
                suggestions=reranked_candidates[:3]  # Return candidates without analysis
            )
    
    # ==================== MAIN PIPELINE ENTRY ====================
    
    def initiate_similarity_check(self, request: SimilarityCheckRequest) -> SimilarityCheckResponse:
        """
        Initiate the full similarity check pipeline.
        
        This is the main entry point called when user submits a create form.
        
        Args:
            request: Similarity check request
        
        Returns:
            SimilarityCheckResponse with check ID and initial status
        """
        try:
            print(f"\n{'='*60}")
            print(f"[SIMILARITY] Starting pipeline for {request.item_type}: '{request.item_data.get('name', 'unknown')}'")
            print(f"{'='*60}")

            # Step 1: Text Cleaning
            print(f"[STEP 1] Cleaning text...")
            cleaning_result, audit = self.step1_clean_text(request)
            print(f"[STEP 1] Done. Cleaned name: '{audit.proposed_name}'")
            
            # Step 2: Domain Classification with hierarchical context
            print(f"[STEP 2] Classifying domain...")
            domain_classification = self.step2_classify_domain(request, cleaning_result, audit)
            print(f"[STEP 2] Done. Domain: '{domain_classification.primary_domain}', Industry: '{domain_classification.industry_vertical}'")
            
            # Step 3: Embedding Creation
            print(f"[STEP 3] Generating embedding...")
            embedding_result = self.step3_generate_embedding(
                request, domain_classification, audit
            )
            if embedding_result.get('error'):
                print(f"[STEP 3] WARNING: Embedding failed: {embedding_result['error']}")
                logger.warning(f"[PIPELINE] Step 3 failed, continuing without embedding: {embedding_result['error']}")
            else:
                print(f"[STEP 3] Done. Embedding generated successfully.")
            
            # Step 4: Vector Search - Find similar records in ChromaDB
            print(f"[STEP 4] Searching for similar records in ChromaDB...")
            step4_candidates = self.step4_search_similar(
                request, embedding_result, domain_classification, audit
            )
            print(f"[STEP 4] Done. Found {len(step4_candidates)} candidate(s).")
            
            # Step 5: Cross-Encoder Reranker - Deep comparison of top candidates
            print(f"[STEP 5] Reranking candidates...")
            step5_reranked = self.step5_rerank_candidates(
                request, step4_candidates, audit
            )
            print(f"[STEP 5] Done. Top {len(step5_reranked)} candidate(s) after reranking.")
            
            # Step 6: LLM Final Decision - Analyze and classify candidates
            print(f"[STEP 6] Running LLM decision analysis...")
            step6_decision = self.step6_llm_decision(
                request, cleaning_result, domain_classification, step5_reranked, audit
            )
            print(f"[STEP 6] Done. Risk: '{step6_decision.duplicate_risk}', Can create: {step6_decision.can_create}")
            
            # Update audit with final decision
            audit.candidates_found = step6_decision.suggestions
            # Get classification from top suggestion's final_status
            top_status = None
            if step6_decision.suggestions:
                top_status = step6_decision.suggestions[0].get('final_status', '').upper().replace('HIGHLY_SIMILAR', 'SIMILAR')
            if not top_status and step6_decision.duplicate_risk:
                risk_map = {'high': 'DUPLICATE', 'medium': 'SIMILAR', 'low': 'RELATED_BUT_DIFFERENT'}
                top_status = risk_map.get(step6_decision.duplicate_risk, None)
            audit.llm_classification = top_status
            audit.llm_reasoning = step6_decision.overall_recommendation
            audit.llm_confidence = 0.85 if step6_decision.duplicate_risk == 'high' else (0.6 if step6_decision.duplicate_risk == 'medium' else 0.3)
            audit.llm_suggested_action = 'WARN' if step6_decision.duplicate_risk in ['high', 'medium'] else 'ALLOW'
            print(f"[PIPELINE] Saving audit to DB...")
            audit.save(update_fields=['candidates_found', 'llm_classification', 'llm_reasoning', 'llm_confidence', 'llm_suggested_action'])
            print(f"[PIPELINE] Audit saved! check_id={audit.id}")
            
            # Return response with steps 1-6 complete
            return SimilarityCheckResponse(
                check_id=audit.id,
                status='ANALYZED',  # Steps 1-6 complete
                classification=step6_decision.duplicate_risk.upper() if step6_decision.duplicate_risk else None,
                candidates=step6_decision.suggestions,
                reasoning=step6_decision.overall_recommendation,
                confidence=0.85 if step6_decision.duplicate_risk == 'high' else (0.6 if step6_decision.duplicate_risk == 'medium' else 0.3),
                suggested_action='WARN' if step6_decision.duplicate_risk in ['high', 'medium'] else 'ALLOW',
                error=None,
                step1_result=cleaning_result,
                step2_result=domain_classification,
                step3_result=embedding_result,
            )
            
        except Exception as e:
            logger.exception(f"Failed to initiate similarity check: {e}")
            return SimilarityCheckResponse(
                check_id=0,
                status='FAILED',
                error=str(e)
            )
    
    # ==================== HELPER METHODS ====================
    
    def _extract_name(self, request: SimilarityCheckRequest) -> str:
        """Extract name field based on item type."""
        data = request.item_data
        if request.item_type == 'Framework':
            return data.get('FrameworkName') or data.get('name', '')
        elif request.item_type == 'Policy':
            return data.get('PolicyName') or data.get('name', '')
        elif request.item_type == 'SubPolicy':
            return data.get('SubPolicyName') or data.get('name', '')
        elif request.item_type == 'Compliance':
            return data.get('ComplianceTitle') or data.get('name', '')
        return ''
    
    def _extract_description(self, request: SimilarityCheckRequest) -> str:
        """Extract description field based on item type."""
        data = request.item_data
        if request.item_type == 'Framework':
            return data.get('FrameworkDescription') or data.get('description', '')
        elif request.item_type == 'Policy':
            return data.get('PolicyDescription') or data.get('description', '')
        elif request.item_type == 'SubPolicy':
            return data.get('Description') or data.get('description', '')
        elif request.item_type == 'Compliance':
            return data.get('ComplianceItemDescription') or data.get('description', '')
        return ''
    
    # ==================== STEP 1 UTILITY FUNCTIONS ====================
    
    def quick_check_exact_duplicate(self, request: SimilarityCheckRequest) -> Optional[Dict]:
        """
        Quick check for exact duplicates before full pipeline.
        
        This is a fast path - if name matches exactly, return immediately.
        """
        from ..models import Framework, Policy, SubPolicy, Compliance
        
        name = self._extract_name(request)
        if not name:
            return None
        
        # Clean the name for comparison
        cleaned_name = self.text_cleaner._clean_name(name)
        
        # Check based on type
        if request.item_type == 'Framework':
            existing = Framework.objects.filter(
                tenant_id=request.tenant_id,
                FrameworkName__iexact=cleaned_name
            ).first()
        elif request.item_type == 'Policy':
            existing = Policy.objects.filter(
                tenant_id=request.tenant_id,
                PolicyName__iexact=cleaned_name,
                FrameworkId_id=request.parent_framework_id
            ).first()
        elif request.item_type == 'SubPolicy':
            existing = SubPolicy.objects.filter(
                tenant_id=request.tenant_id,
                SubPolicyName__iexact=cleaned_name,
                PolicyId_id=request.parent_policy_id
            ).first()
        elif request.item_type == 'Compliance':
            existing = Compliance.objects.filter(
                tenant_id=request.tenant_id,
                ComplianceTitle__iexact=cleaned_name,
                SubPolicy_id=request.parent_subpolicy_id
            ).first()
        else:
            return None
        
        if existing:
            return {
                'id': existing.pk,
                'type': request.item_type,
                'name': getattr(existing, f'{request.item_type}Name', getattr(existing, 'ComplianceTitle', 'Unknown')),
                'match_type': 'EXACT_NAME',
                'confidence': 1.0,
            }
        
        return None
    
    # ==================== CONFIGURATION ====================
    
    @classmethod
    def get_service_for_tenant(cls, tenant_id: Optional[int] = None):
        """Factory method to get configured service for tenant."""
        config = SimilarityConfiguration.get_for_tenant(tenant_id)
        return cls(config=config)


# ==================== CONVENIENCE FUNCTIONS ====================

def check_framework_similarity(
    framework_data: Dict[str, Any],
    tenant_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> SimilarityCheckResponse:
    """
    Convenience function to check similarity for a new framework.
    
    Args:
        framework_data: Framework form data
        tenant_id: Tenant ID
        user_id: User ID
    
    Returns:
        SimilarityCheckResponse
    """
    service = SimilarityService.get_service_for_tenant(tenant_id)
    request = SimilarityCheckRequest(
        item_type='Framework',
        item_data=framework_data,
        tenant_id=tenant_id,
        user_id=user_id,
    )
    return service.initiate_similarity_check(request)


def check_policy_similarity(
    policy_data: Dict[str, Any],
    framework_id: int,
    tenant_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> SimilarityCheckResponse:
    """Convenience function to check similarity for a new policy."""
    service = SimilarityService.get_service_for_tenant(tenant_id)
    request = SimilarityCheckRequest(
        item_type='Policy',
        item_data=policy_data,
        tenant_id=tenant_id,
        user_id=user_id,
        parent_framework_id=framework_id,
    )
    return service.initiate_similarity_check(request)


def check_subpolicy_similarity(
    subpolicy_data: Dict[str, Any],
    policy_id: int,
    framework_id: int,
    tenant_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> SimilarityCheckResponse:
    """Convenience function to check similarity for a new sub-policy."""
    service = SimilarityService.get_service_for_tenant(tenant_id)
    request = SimilarityCheckRequest(
        item_type='SubPolicy',
        item_data=subpolicy_data,
        tenant_id=tenant_id,
        user_id=user_id,
        parent_framework_id=framework_id,
        parent_policy_id=policy_id,
    )
    return service.initiate_similarity_check(request)


def check_compliance_similarity(
    compliance_data: Dict[str, Any],
    subpolicy_id: int,
    policy_id: int,
    framework_id: int,
    tenant_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> SimilarityCheckResponse:
    """Convenience function to check similarity for new compliance."""
    service = SimilarityService.get_service_for_tenant(tenant_id)
    request = SimilarityCheckRequest(
        item_type='Compliance',
        item_data=compliance_data,
        tenant_id=tenant_id,
        user_id=user_id,
        parent_framework_id=framework_id,
        parent_policy_id=policy_id,
        parent_subpolicy_id=subpolicy_id,
    )
    return service.initiate_similarity_check(request)
