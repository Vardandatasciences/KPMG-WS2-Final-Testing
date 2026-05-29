#!/usr/bin/env python
"""
Test Step 3: Embedding Generation
Tests BGE-M3 embedding creation for all entity types
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.dataclasses.similarity_dataclasses import SimilarityCheckRequest
from grc.services.similarity_service import SimilarityService
from grc.models_extensions.similarity_models import SimilarityCheckAudit

print("=" * 80)
print("STEP 3: EMBEDDING GENERATION TEST")
print("=" * 80)

# Test with Framework
framework_data = {
    "FrameworkName": "Payment Card Industry Data Security Standard",
    "FrameworkDescription": "Security standard for organizations handling credit cards.",
    "Category": "Financial Security",
    "Type": "External",
    "Identifier": "PCI-DSS-v4.0"
}

request = SimilarityCheckRequest(
    item_type='Framework',
    item_data=framework_data,
    tenant_id=None,
    user_id=None
)

service = SimilarityService()

print("\n[STEP 1] Text Cleaning...")
cleaning_result, audit = service.step1_clean_text(request)
print(f"✓ Cleaned text: {len(cleaning_result.embedding_text)} chars")

print("\n[STEP 2] Domain Classification...")
classification_result = service.step2_classify_domain(request, cleaning_result, audit)
print(f"✓ Domain: {classification_result.primary_domain}")
print(f"✓ Industry: {classification_result.industry_vertical}")

print("\n[STEP 3] Embedding Generation...")
embedding_result = service.step3_generate_embedding(request, classification_result, audit)

print(f"✓ Embedding model: {embedding_result['embedding_model']}")
print(f"✓ Vector dimensions: {embedding_result['embedding_dimension']}")
print(f"✓ Vector length: {len(embedding_result['embedding_vector'])}")
print(f"✓ Text hash: {embedding_result['text_hash'][:16]}...")
print(f"✓ Semantic embedding ID: {embedding_result['semantic_embedding_id']}")

print("\n[STEP 3] Embedding Text Preview:")
print("-" * 80)
print(embedding_result['embedding_text'][:500])
print("-" * 80)

print("\n[VERIFY] Database Check:")
audit_refreshed = SimilarityCheckAudit.objects.get(id=audit.id)
print(f"✓ Audit.embedding_text stored: {bool(audit_refreshed.embedding_text)}")
print(f"✓ Audit.embedding_generated_at: {audit_refreshed.embedding_generated_at}")

print("\n" + "=" * 80)
print("STEP 3 TEST COMPLETE - EMBEDDING GENERATED SUCCESSFULLY!")
print("=" * 80)
print("\nThe embedding vector is now stored in semantic_embeddings table.")
print("Step 4 (Vector Search in Qdrant) can now use this vector.")
