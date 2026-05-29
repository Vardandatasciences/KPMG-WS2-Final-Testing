"""
Models for similarity detection and semantic search.

These models store:
1. Pre-computed embeddings for fast similarity search
2. Audit trail of all similarity checks and user decisions
"""

import hashlib
import json
from datetime import datetime
from typing import Optional

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from ..models import Tenant, Users, Framework, Policy, SubPolicy, Compliance


class SemanticEmbedding(models.Model):
    """
    Store pre-computed embeddings for GRC entities.
    
    This allows fast similarity search without regenerating embeddings.
    """
    id = models.BigAutoField(primary_key=True)
    
    # Generic relation to any entity (Framework, Policy, SubPolicy, Compliance)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        help_text="Type of entity (Framework, Policy, SubPolicy, Compliance)"
    )
    object_id = models.PositiveIntegerField(help_text="ID of the entity")
    entity = GenericForeignKey('content_type', 'object_id')
    
    # Multi-tenancy
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        db_column='TenantId',
        null=True,
        blank=True,
        help_text="Tenant this embedding belongs to"
    )
    
    # Embedding data
    embedding_vector = models.JSONField(
        help_text="Vector embedding as JSON array (e.g., [0.1, 0.2, ...])"
    )
    embedding_model = models.CharField(
        max_length=50,
        default='BGE-M3',
        help_text="Model used to generate embedding"
    )
    embedding_dimension = models.IntegerField(
        default=768,
        help_text="Dimension of embedding vector"
    )
    
    # Source text tracking
    text_hash = models.CharField(
        max_length=64,
        help_text="SHA256 hash of source text - for detecting when re-embedding is needed"
    )
    source_text = models.TextField(
        help_text="The cleaned text that was embedded (for debugging)"
    )
    
    # Context for filtering
    entity_type = models.CharField(
        max_length=20,
        choices=[
            ('Framework', 'Framework'),
            ('Policy', 'Policy'),
            ('SubPolicy', 'SubPolicy'),
            ('Compliance', 'Compliance'),
        ],
        help_text="Type of entity for quick filtering"
    )
    domain = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Domain/category for filtering searches"
    )
    category = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Category for filtering searches"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'semantic_embeddings'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['tenant', 'entity_type']),
            models.Index(fields=['entity_type', 'domain']),
            models.Index(fields=['text_hash']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Semantic Embedding'
        verbose_name_plural = 'Semantic Embeddings'
    
    def __str__(self):
        return f"{self.entity_type} {self.object_id} ({self.embedding_model})"
    
    @classmethod
    def compute_text_hash(cls, text: str) -> str:
        """Compute SHA256 hash of text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    @classmethod
    def needs_update(cls, entity_type: str, object_id: int, new_text: str) -> bool:
        """Check if entity needs re-embedding (text changed)."""
        try:
            embedding = cls.objects.get(
                content_type__model=entity_type.lower(),
                object_id=object_id
            )
            new_hash = cls.compute_text_hash(new_text)
            return embedding.text_hash != new_hash
        except cls.DoesNotExist:
            return True


class SimilarityCheckAudit(models.Model):
    """
    Audit trail for every similarity check performed.
    
    Tracks:
    - What was being created
    - AI suggestions and reasoning
    - User decisions
    - Compliance and traceability
    """
    id = models.BigAutoField(primary_key=True)
    
    # Multi-tenancy
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        db_column='TenantId',
        null=True,
        blank=True,
        help_text="Tenant where check occurred"
    )
    
    # User who triggered the check
    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        db_column='UserId',
        null=True,
        blank=True,
        help_text="User who initiated the similarity check"
    )
    
    # What was being created
    item_type = models.CharField(
        max_length=20,
        choices=[
            ('Framework', 'Framework'),
            ('Policy', 'Policy'),
            ('SubPolicy', 'SubPolicy'),
            ('Compliance', 'Compliance'),
        ],
        help_text="Type of item being created"
    )
    
    # Proposed item details (what user wanted to create)
    proposed_name = models.CharField(max_length=1000)
    proposed_description = models.TextField()
    proposed_structured_json = models.JSONField(
        null=True,
        blank=True,
        help_text="Structured JSON after Step 1 cleaning (for storage/querying)"
    )
    proposed_cleaned_text = models.TextField(
        help_text="Generated embedding text from structured JSON (for similarity search)"
    )
    
    # Context
    framework_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Parent framework ID (for Policy/SubPolicy/Compliance)"
    )
    policy_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Parent policy ID (for SubPolicy/Compliance)"
    )
    subpolicy_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="Parent sub-policy ID (for Compliance)"
    )
    
    # Domain/Category classification (Step 2 result)
    classified_primary_domain = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Primary domain from Step 2 (Food/Banking/IT/Healthcare/etc.)"
    )
    classified_industry_vertical = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Specific industry vertical from Step 2"
    )
    classified_business_function = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Business function from Step 2 (HR/IT/Finance/Operations/etc.)"
    )
    classified_compliance_area = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Compliance area from Step 2 (Access Control/Data Privacy/etc.)"
    )
    classified_control_type = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Control type from Step 2 (Preventive/Detective/Corrective/etc.)"
    )
    classified_risk_category = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Risk category from Step 2"
    )
    classification_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence of domain classification (0-1)"
    )
    classification_method = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Method used: nvidia/openai/fallback"
    )
    classification_reasoning = models.TextField(
        null=True,
        blank=True,
        help_text="AI reasoning for classification"
    )
    classification_context_used = models.JSONField(
        null=True,
        blank=True,
        help_text="What parent context was used for classification"
    )
    
    # Embedding generation (Step 3 result)
    embedding_text = models.TextField(
        null=True,
        blank=True,
        help_text="Final text used for embedding generation (after Step 1 + Step 2 enrichment)"
    )
    embedding_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When embedding was generated"
    )
    
    # Similarity search results (Step 4 result)
    candidates_found = models.JSONField(
        help_text="List of similar items found with scores",
        default=list
    )
    search_scope = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Scope of search (e.g., 'same_framework', 'same_domain')"
    )
    
    # LLM analysis (Step 6 result)
    llm_classification = models.TextField(
        null=True,
        blank=True,
        help_text="LLM classification of similarity (DUPLICATE, SIMILAR, RELATED_BUT_DIFFERENT, DIFFERENT)"
    )
    llm_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="LLM confidence score (0-1)"
    )
    llm_reasoning = models.TextField(
        null=True,
        blank=True,
        help_text="LLM explanation for classification"
    )
    llm_suggested_action = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Suggested action from LLM"
    )
    
    # Reranker scores (Step 5)
    reranker_scores = models.JSONField(
        null=True,
        blank=True,
        help_text="Cross-encoder reranker scores for candidates"
    )
    
    # User decision (Step 8)
    user_decision = models.CharField(
        max_length=20,
        choices=[
            ('USE_EXISTING', 'Use Existing'),
            ('CREATE_NEW', 'Create New'),
            ('MERGE', 'Merge with Existing'),
        ],
        null=True,
        blank=True,
        help_text="User's final decision"
    )
    selected_existing_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of existing item selected (if USE_EXISTING or MERGE)"
    )
    selected_existing_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Type of existing item selected"
    )
    
    # Outcome (Step 9)
    final_action = models.CharField(
        max_length=20,
        choices=[
            ('CREATED', 'New Item Created'),
            ('USED_EXISTING', 'Used Existing Item'),
            ('MERGED', 'Items Merged'),
            ('CANCELLED', 'Cancelled by User'),
        ],
        null=True,
        blank=True,
        help_text="Final outcome of the process"
    )
    final_record_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of created or selected record"
    )
    final_record_type = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Type of final record (Framework/Policy/SubPolicy/Compliance)"
    )
    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When Step 9 finalization completed"
    )
    created_entity_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of newly created entity (if CREATE_NEW) - legacy field"
    )
    
    # Metadata
    check_status = models.CharField(
        max_length=20,
        default='PENDING',
        choices=[
            ('PENDING', 'Pending User Decision'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
            ('TIMEOUT', 'Timed Out'),
        ]
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Error tracking
    error_message = models.TextField(
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'similarity_check_audit'
        indexes = [
            models.Index(fields=['tenant', 'item_type']),
            models.Index(fields=['user']),
            models.Index(fields=['check_status']),
            models.Index(fields=['started_at']),
            models.Index(fields=['framework_id']),
            models.Index(fields=['policy_id']),
        ]
        verbose_name = 'Similarity Check Audit'
        verbose_name_plural = 'Similarity Check Audits'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.item_type} check by {self.user} at {self.started_at}"
    
    def mark_completed(self, action: str, entity_id: Optional[int] = None):
        """Mark this audit as completed."""
        self.final_action = action
        self.created_entity_id = entity_id
        self.check_status = 'COMPLETED'
        self.completed_at = datetime.utcnow()
        self.save(update_fields=['final_action', 'created_entity_id', 'check_status', 'completed_at'])
    
    def mark_failed(self, error: str):
        """Mark this audit as failed."""
        self.error_message = error
        self.check_status = 'FAILED'
        self.completed_at = datetime.utcnow()
        self.save(update_fields=['error_message', 'check_status', 'completed_at'])


class SimilarityConfiguration(models.Model):
    """
    Configuration settings for similarity detection pipeline.
    
    Allows per-tenant or global configuration of thresholds and models.
    """
    id = models.AutoField(primary_key=True)
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        db_column='TenantId',
        null=True,
        blank=True,
        help_text="Tenant-specific config (null = global default)"
    )
    
    # Model settings
    embedding_model = models.CharField(
        max_length=50,
        default='BGE-M3',
        help_text="Sentence transformer model for embeddings"
    )
    embedding_dimension = models.IntegerField(default=768)
    
    reranker_model = models.CharField(
        max_length=100,
        default='cross-encoder/ms-marco-MiniLM-L-6-v2',
        help_text="Cross-encoder model for reranking"
    )
    
    # Similarity thresholds
    threshold_duplicate = models.FloatField(
        default=0.90,
        help_text="Similarity >= this is DUPLICATE"
    )
    threshold_similar = models.FloatField(
        default=0.75,
        help_text="Similarity >= this but < duplicate is SIMILAR"
    )
    threshold_related = models.FloatField(
        default=0.60,
        help_text="Similarity >= this but < similar is RELATED_BUT_DIFFERENT"
    )
    # Below threshold_related = DIFFERENT
    
    # Search settings
    max_candidates = models.IntegerField(
        default=10,
        help_text="Maximum candidates to fetch from vector DB"
    )
    top_k_rerank = models.IntegerField(
        default=5,
        help_text="Top K candidates to rerank with cross-encoder"
    )
    
    # LLM settings
    llm_model = models.CharField(
        max_length=50,
        default='gpt-4',
        help_text="LLM for final classification"
    )
    llm_temperature = models.FloatField(default=0.1)
    
    # Feature flags
    enable_step1_cleaning = models.BooleanField(default=True)
    enable_step2_classification = models.BooleanField(default=True)
    enable_step3_embedding = models.BooleanField(default=True)
    enable_step4_vector_search = models.BooleanField(default=True)
    enable_step5_reranker = models.BooleanField(default=True)
    enable_step6_llm = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'similarity_configuration'
        verbose_name = 'Similarity Configuration'
        verbose_name_plural = 'Similarity Configurations'
        unique_together = [('tenant',)]  # One config per tenant (or global)
    
    def __str__(self):
        if self.tenant:
            return f"Config for {self.tenant}"
        return "Global Similarity Config"
    
    @classmethod
    def get_for_tenant(cls, tenant_id: Optional[int] = None):
        """Get configuration for tenant or global default."""
        if tenant_id:
            try:
                return cls.objects.get(tenant_id=tenant_id, is_active=True)
            except cls.DoesNotExist:
                pass
        
        # Return global config or create default
        try:
            return cls.objects.get(tenant=None, is_active=True)
        except cls.DoesNotExist:
            return cls.objects.create(tenant=None)  # Creates with defaults
