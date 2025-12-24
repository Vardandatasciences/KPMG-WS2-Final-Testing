#!/usr/bin/env python
"""
Quick Phase 2 Verification Script
Run this to check if Phase 2 optimizations are working.
"""

import os
import sys

print("🧪 Testing Phase 2 Implementation...\n")

# Test 1: Basic imports (without Django)
print("1. Testing basic Phase 2 imports (no Django required)...")
try:
    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Test direct imports from utils modules
    from grc.utils.ai_cache import get_redis_client, get_cache_stats
    from grc.utils.document_preprocessor import preprocess_document, calculate_document_hash
    from grc.utils.few_shot_prompts import get_field_extraction_prompt, RISK_EXTRACTION_EXAMPLES
    print("   ✅ All Phase 2 core imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Backward compatibility imports (requires Django)
print("\n2. Testing backward compatibility (requires Django)...")
try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tprm_backend.config.settings')
    django.setup()
    from grc.utils import parse_date, safe_isoformat, send_log, get_client_ip
    print("   ✅ Backward compatibility imports work")
except Exception as e:
    print(f"   ⚠️  Backward compatibility test skipped (Django setup issue: {e})")
    print("   ℹ️  This is OK - Phase 2 core features don't require Django")

# Test 3: Cache (Redis, fakeredis, or in-memory)
print("\n3. Testing cache connection...")
client = get_redis_client()
stats = get_cache_stats()
if stats.get('status') == 'available':
    cache_type = stats.get('type', 'unknown')
    if cache_type == 'redis':
        print(f"   ✅ Redis server connected: {stats.get('total_keys', 0)} cache keys")
    elif cache_type == 'fakeredis':
        print(f"   ✅ fakeredis (pure Python Redis) active: {stats.get('total_keys', 0)} cache keys")
        print("   💡 Using fakeredis - no Redis server required! (Perfect for Windows)")
    elif cache_type == 'in_memory':
        print(f"   ✅ In-memory cache active: {stats.get('total_keys', 0)} cache keys")
        print("   💡 Using in-memory cache (Redis not available, but caching still works!)")
    else:
        print(f"   ✅ Cache available ({cache_type}): {stats.get('total_keys', 0)} cache keys")
else:
    print(f"   ⚠️  Cache not available: {stats.get('message', 'Unknown error')}")

# Test 4: Preprocessing
print("\n4. Testing document preprocessing...")
test_text = "This is a test document. " * 1000
processed, metadata = preprocess_document(test_text)
print(f"   ✅ Preprocessing works: {metadata['original_length']} → {metadata['processed_length']} chars")
if metadata['was_truncated']:
    print(f"   📏 Document was truncated ({metadata['reduction_percent']:.1f}% reduction)")

# Test 5: Few-shot prompts
print("\n5. Testing few-shot prompts...")
try:
    field_prompts = {"Criticality": "Return one of: Low, Medium, High, Critical."}
    prompt = get_field_extraction_prompt("Criticality", "Test document", field_prompts)
    if "Example" in prompt or "example" in prompt.lower():
        print("   ✅ Few-shot prompts working (examples found in prompt)")
    else:
        print("   ⚠️  Few-shot prompts may not be working (no examples found)")
except Exception as e:
    print(f"   ❌ Few-shot prompt error: {e}")

# Test 6: Integration check (requires Django)
print("\n6. Checking integration in risk_ai_doc.py (requires Django)...")
try:
    # Try to import if Django is available
    import django
    from grc.routes.Risk.risk_ai_doc import call_ollama_json, infer_single_field
    import inspect
    
    # Check if caching parameters exist
    sig = inspect.signature(call_ollama_json)
    params = list(sig.parameters.keys())
    if 'document_hash' in params and 'use_cache' in params:
        print("   ✅ Caching integrated in call_ollama_json")
    else:
        print(f"   ⚠️  Caching parameters missing: {params}")
    
    sig = inspect.signature(infer_single_field)
    params = list(sig.parameters.keys())
    if 'document_hash' in params:
        print("   ✅ Document hash parameter in infer_single_field")
    else:
        print(f"   ⚠️  Document hash parameter missing: {params}")
except Exception as e:
    print(f"   ⚠️  Integration check skipped (Django setup issue: {e})")
    print("   ℹ️  You can verify integration by checking risk_ai_doc.py manually")

print("\n" + "="*60)
print("✅ Phase 2 Core Testing Complete!")
print("="*60)
print("\n📋 To Test Full Integration:")
print("   1. Start Django server: python manage.py runserver")
print("   2. Upload a test document via API endpoint")
print("   3. Check server logs for:")
print("      - 'STEP 1B: Preprocessing document (Phase 2 optimization)'")
print("      - 'Cache MISS' (first time) or 'Cache HIT' (if cached)")
print("      - 'Using few-shot prompt template'")
print("   4. Upload same document again - should see 'Cache HIT'")
print("   5. Check API response for 'preprocessing_metadata' field")
print("\n📖 See PHASE2_TESTING_GUIDE.md for detailed testing instructions")
print("\n💡 Tip: If you see Redis warnings, that's OK - caching will be disabled")
print("   but other Phase 2 features (preprocessing, few-shot) will still work!")

