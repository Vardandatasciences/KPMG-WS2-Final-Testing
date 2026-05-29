#!/usr/bin/env python
"""Test script for Step 1: Text Cleaning"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.utils.text_cleaner import clean_framework_text
import json

print("=" * 60)
print("STEP 1: TEXT CLEANING TEST")
print("=" * 60)

# Test with the form data from your screenshot
result = clean_framework_text({
    "FrameworkName": "food__drug - administration",
    "FrameworkDescription": "Framework for food and drug administration safety standards",
    "Category": "Food Safety",
    "Domain": {"DomainName": "Food Industry"},
    "InternalExternal": "External",
    "Identifier": "FDA-2024"
})

print("\n1. STRUCTURED JSON (for MySQL storage):")
print("-" * 60)
print(json.dumps(result.structured_json, indent=2))

print("\n2. EMBEDDING TEXT (for BGE-M3 → Qdrant):")
print("-" * 60)
print(result.embedding_text)

print("\n3. CHANGES MADE:")
print("-" * 60)
for change in result.changes_made:
    print(f"  • {change}")

print("\n4. ORIGINAL VALUES (for comparison):")
print("-" * 60)
print(f"  Original Name: '{result.original_values.get('FrameworkName')}'")
print(f"  Cleaned Name:  '{result.structured_json['name']}'")

print("\n5. ENTITY TYPE:")
print("-" * 60)
print(f"  {result.entity_type}")

print("\n" + "=" * 60)
print("STEP 1 COMPLETE!")
print("=" * 60)
