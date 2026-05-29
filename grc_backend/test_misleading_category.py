#!/usr/bin/env python
"""Test: Misleading category vs actual content"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.dataclasses.similarity_dataclasses import SimilarityCheckRequest
from grc.services.similarity_service import SimilarityService

print("=" * 80)
print("TEST: MISLEADING CATEGORY vs ACTUAL CONTENT")
print("=" * 80)
print("\nInput: 'Food Safety and Administration'")
print("BUT Category deliberately set to: 'Banking'")
print("Identifier: 'FSSAI-2024'")
print("\nWill AI fall for 'Banking' or understand it's Food Safety?")
print("=" * 80)

framework_data = {
    "FrameworkName": "Food Safety and Administration",
    "FrameworkDescription": "Comprehensive framework for ensuring food safety standards, hygiene practices, and quality control in food processing and distribution.",
    "Category": "Banking",  # DELIBERATELY WRONG!
    "Type": "External",
    "Identifier": "FSSAI-2024"
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
print(f"✓ Cleaned Category: {cleaning_result.structured_json.get('category')}")
print(f"✓ Cleaned Identifier: {cleaning_result.structured_json.get('identifier')}")

print("\n[STEP 2] Domain Classification...")
try:
    classification_result = service.step2_classify_domain(request, cleaning_result, audit)
    print(f"\n{'='*80}")
    print("AI DECISION:")
    print(f"{'='*80}")
    print(f"Primary Domain: {classification_result.primary_domain}")
    print(f"Industry Vertical: {classification_result.industry_vertical}")
    print(f"Compliance Area: {classification_result.compliance_area}")
    print(f"Confidence: {classification_result.confidence}")
    print(f"Method: {classification_result.classification_method}")
    print(f"\nAI Reasoning:")
    print(classification_result.reasoning)
    print(f"{'='*80}")
    
    if classification_result.primary_domain.lower() in ['food', 'food safety', 'food services']:
        print("✓ SUCCESS: AI correctly identified FOOD domain despite 'Banking' category!")
    elif 'bank' in classification_result.primary_domain.lower():
        print("✗ FAILURE: AI was fooled by wrong category!")
    else:
        print(f"? UNEXPECTED: AI said '{classification_result.primary_domain}'")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("Why compliance standards from identifier?")
print("=" * 80)
print("""
The AI sees:
- Identifier: 'FSSAI-2024'
- Recognizes: FSSAI = Food Safety and Standards Authority of India
- Concludes: This is a compliance standard like PCI-DSS, ISO, HIPAA

So it returns compliance_standards = ['FSSAI-2024']
Just like PCI-DSS → ['PCI-DSS-v4.0']
""")
