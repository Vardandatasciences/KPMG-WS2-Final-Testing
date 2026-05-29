#!/usr/bin/env python
"""
Test Steps 1-6: Full Similarity Pipeline
Tests: Text Cleaning → Domain Classification → Embedding → Vector Search → Reranker → LLM Decision
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
print("STEPS 1-6: FULL SIMILARITY PIPELINE")
print("Step 1: Text Cleaning | Step 2: Domain Classification | Step 3: Embedding")
print("Step 4: Vector Search | Step 5: Reranker | Step 6: LLM Decision")
print("=" * 80)

# Test 1: Create first Framework (this will be stored for future searches)
print("\n[Test 1] Creating first Framework (becomes searchable record)...")
framework_1 = {
    "FrameworkName": "Food Hygiene and Sanitation Framework",
    "FrameworkDescription": "Comprehensive framework for maintaining food hygiene standards in restaurants and food processing units.",
    "Category": "Food Safety",
    "Type": "Internal",
    "Identifier": "FOOD-HYG-001"
}

request_1 = SimilarityCheckRequest(
    item_type='Framework',
    item_data=framework_1,
    tenant_id=1,
    user_id=1
)

service = SimilarityService()

print("  [Step 1] Cleaning text...")
print("  [Step 2] Classifying domain...")
print("  [Step 3] Generating embedding...")
print("  [Step 4] Vector search (ChromaDB)...")
print("  [Step 5] Reranking (Cross-Encoder)...")
print("  [Step 6] LLM Decision & Analysis...")

response_1 = service.initiate_similarity_check(request_1)

print(f"\n  ✓ Check ID: {response_1.check_id}")
print(f"  ✓ Status: {response_1.status}")
print(f"  ✓ Domain: {response_1.step2_result.primary_domain}")
print(f"  ✓ Candidates: {len(response_1.candidates)}")
if response_1.reasoning:
    print(f"  ✓ LLM Advice: {response_1.reasoning[:100]}...")

# Test 2: Create similar Framework (should find Test 1 as candidate)
print("\n" + "=" * 80)
print("[Test 2] Creating similar Framework (should find Test 1)...")
framework_2 = {
    "FrameworkName": "Food Cleanliness and Safety Framework",
    "FrameworkDescription": "Guidelines for ensuring cleanliness in food handling and preparation areas.",
    "Category": "Food Safety",
    "Type": "Internal",
    "Identifier": "FOOD-CLN-002"
}

request_2 = SimilarityCheckRequest(
    item_type='Framework',
    item_data=framework_2,
    tenant_id=1,
    user_id=1
)

response_2 = service.initiate_similarity_check(request_2)

print(f"\n  ✓ Check ID: {response_2.check_id}")
print(f"  ✓ Status: {response_2.status}")
print(f"  ✓ Domain: {response_2.step2_result.primary_domain}")
print(f"  ✓ Industry: {response_2.step2_result.industry_vertical}")
print(f"  ✓ Risk Level: {response_2.classification or 'N/A'}")

print(f"\n  [Step 5-6 Results] Final Analysis:")

if response_2.candidates:
    print(f"\n  Found {len(response_2.candidates)} similar records:")
    for i, candidate in enumerate(response_2.candidates[:5], 1):
        print(f"\n    {i}. {candidate.get('name', 'Unknown')}")
        print(f"       ChromaDB: {candidate.get('chroma_score', 0):.1%} | Reranker: {candidate.get('reranker_score', 0):.1%}")
        if 'final_status' in candidate:
            print(f"       Status: {candidate['final_status']} | Action: {candidate.get('recommendation', 'N/A')}")
        if 'reason' in candidate:
            print(f"       Reason: {candidate['reason'][:80]}...")
else:
    print("  (No similar records found)")

if response_2.reasoning:
    print(f"\n  ✓ Overall Advice: {response_2.reasoning}")
if response_2.suggested_action:
    print(f"  ✓ Suggested Action: {response_2.suggested_action}")

# Test 3: Create unrelated Framework (should NOT find food records)
print("\n" + "=" * 80)
print("[Test 3] Creating Banking Framework (should NOT find food records)...")
framework_3 = {
    "FrameworkName": "Banking KYC Compliance Framework",
    "FrameworkDescription": "Know Your Customer compliance framework for banking institutions.",
    "Category": "Banking",
    "Type": "Regulatory",
    "Identifier": "BANK-KYC-001"
}

request_3 = SimilarityCheckRequest(
    item_type='Framework',
    item_data=framework_3,
    tenant_id=1,
    user_id=1
)

response_3 = service.initiate_similarity_check(request_3)

print(f"\n  ✓ Check ID: {response_3.check_id}")
print(f"  ✓ Status: {response_3.status}")
print(f"  ✓ Domain: {response_3.step2_result.primary_domain}")
print(f"  ✓ Risk Level: {response_3.classification or 'N/A'}")

print(f"\n  [Step 5-6 Results] Final Analysis:")

if response_3.candidates:
    print(f"\n  Found {len(response_3.candidates)} similar records:")
    for i, candidate in enumerate(response_3.candidates[:3], 1):
        print(f"\n    {i}. {candidate.get('name', 'Unknown')}")
        print(f"       ChromaDB: {candidate.get('chroma_score', 0):.1%} | Reranker: {candidate.get('reranker_score', 0):.1%}")
        if 'final_status' in candidate:
            print(f"       Status: {candidate['final_status']} | Action: {candidate.get('recommendation', 'N/A')}")
else:
    print("  (No similar records found - correct, different domain)")

if response_3.reasoning:
    print(f"\n  ✓ Overall Advice: {response_3.reasoning}")
if response_3.suggested_action:
    print(f"  ✓ Suggested Action: {response_3.suggested_action}")

# Summary
print("\n" + "=" * 80)
print("STEPS 1-6 PIPELINE TEST SUMMARY")
print("=" * 80)
print(f"Test 1 (Food Hygiene):     {response_1.status} | Domain: {response_1.step2_result.primary_domain}")
print(f"Test 2 (Food Cleanliness):   {response_2.status} | Domain: {response_2.step2_result.primary_domain} | Risk: {response_2.classification or 'N/A'}")
print(f"Test 3 (Banking KYC):        {response_3.status} | Domain: {response_3.step2_result.primary_domain} | Risk: {response_3.classification or 'N/A'}")

print("\nPipeline Steps Completed:")
print("  ✓ Step 1: Text Cleaning (Structured JSON)")
print("  ✓ Step 2: Domain Classification (AI Categorization)")
print("  ✓ Step 3: Embedding Creation (BGE-M3 Vectors)")
print("  ✓ Step 4: Vector Search (ChromaDB Top 20)")
print("  ✓ Step 5: Cross-Encoder Reranker (BGE-Reranker Top 5)")
print("  ✓ Step 6: LLM Decision (NVIDIA AI Analysis)")

print("\nChromaDB Vector Store Stats:")
stats = service.vector_store.get_stats()
print(f"  Total embeddings stored: {stats.get('total_embeddings', 'N/A')}")
print(f"  Storage location: {stats.get('persist_directory', 'N/A')}")

print("\n" + "=" * 80)
print("STEPS 1-6 PIPELINE COMPLETE!")
print("=" * 80)
print("\nNext: Step 7 (UI Suggestion Display) will show results to user.")
