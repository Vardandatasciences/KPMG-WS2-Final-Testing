# Phase 2 Testing Guide

## 🧪 How to Check if Phase 2 is Working

### Quick Test Checklist

1. ✅ **Check Redis Connection** (for caching)
2. ✅ **Test Document Upload** (preprocessing + caching)
3. ✅ **Verify Cache Hits** (check logs)
4. ✅ **Check Few-Shot Prompts** (verify in logs)
5. ✅ **Monitor Performance** (response times)

---

## 📋 Step-by-Step Testing

### Step 1: Check Redis Connection

**Test if Redis is available for caching:**

```python
# In Django shell or Python
python manage.py shell

# Then run:
from grc.utils.ai_cache import get_redis_client, get_cache_stats

# Check Redis connection
client = get_redis_client()
if client:
    print("✅ Redis is connected!")
    stats = get_cache_stats()
    print(f"Cache stats: {stats}")
else:
    print("⚠️  Redis not available - caching will be disabled")
```

**Expected Output:**
- ✅ `Redis is connected!` - Caching will work
- ⚠️ `Redis not available` - Caching disabled (but other features work)

---

### Step 2: Test Document Upload with Phase 2

**Upload a risk document and check logs:**

1. **Upload a document** via the API endpoint:
   ```
   POST /api/risk/upload-and-process/
   ```

2. **Check the logs** for Phase 2 indicators:

   **Look for these log messages:**

   ```
   ✅ STEP 1B: Preprocessing document (Phase 2 optimization)...
   ✅ STEP 1B COMPLETE: Preprocessed document
      Original length: 15000 chars
      Processed length: 8000 chars
      ⚠️  Document was truncated (46.7% reduction)
   📝 Document hash: abc123def456... (for caching)
   
   🤖 STEP 3: Calling OLLAMA to extract risks (Phase 2: cached + few-shot)...
   ❌ Cache MISS for llama3.2:3b-instruct... - calling LLM
   💾 Cached response for future use
   📚 Using few-shot prompt template for Criticality
   ```

3. **Upload the SAME document again** (should see cache hit):
   ```
   ⚡ Cache HIT for llama3.2:3b-instruct... (saved API call)
   ```

---

### Step 3: Verify Cache is Working

**Test cache hits and misses:**

1. **First upload** (cache miss):
   - Look for: `❌ Cache MISS` in logs
   - Look for: `💾 Cached response for future use`

2. **Second upload of same document** (cache hit):
   - Look for: `⚡ Cache HIT` in logs
   - Response should be **much faster** (< 0.1s vs 5-10s)

3. **Check cache statistics:**
   ```python
   from grc.utils.ai_cache import get_cache_stats
   stats = get_cache_stats()
   print(stats)
   ```

**Expected:**
- `total_keys` should increase after each unique document
- Cache hits should be instant

---

### Step 4: Verify Document Preprocessing

**Check preprocessing metadata in response:**

After uploading a document, check the API response:

```json
{
  "status": "success",
  "preprocessing_metadata": {
    "original_length": 15000,
    "processed_length": 8000,
    "was_truncated": true,
    "reduction_percent": 46.67
  },
  ...
}
```

**What to verify:**
- ✅ `preprocessing_metadata` exists in response
- ✅ Large documents are truncated intelligently
- ✅ Original and processed lengths are tracked

---

### Step 5: Verify Few-Shot Prompts

**Check logs for few-shot prompt usage:**

Look for these log messages:

```
📚 Using few-shot prompt template for Criticality
📚 Using few-shot prompt template for RiskLikelihood
📚 Using few-shot prompt template for RiskImpact
```

**If you see:**
- ✅ `Using few-shot prompt template` - Few-shot prompts are working
- ⚠️ `Few-shot prompt failed, using basic prompt` - Fallback to basic prompts

---

### Step 6: Performance Comparison

**Measure response times:**

1. **First request** (cache miss):
   - Time: ~5-10 seconds
   - Log: `Cache MISS - calling LLM`

2. **Second request** (cache hit):
   - Time: < 0.1 seconds
   - Log: `Cache HIT`

3. **Compare:**
   - Cache hit should be **100-150x faster**
   - Overall processing should be **2-3x faster** even on cache miss

---

## 🔍 Detailed Verification

### Check Phase 2 Files Exist

```bash
# Verify all Phase 2 files are present
ls grc_backend/grc/utils/
# Should see:
# - __init__.py
# - ai_cache.py
# - document_preprocessor.py
# - few_shot_prompts.py
```

### Check Imports Work

```python
# Test imports
from grc.utils.ai_cache import cached_llm_call
from grc.utils.document_preprocessor import preprocess_document
from grc.utils.few_shot_prompts import get_field_extraction_prompt

print("✅ All Phase 2 imports successful!")
```

### Check Integration in risk_ai_doc.py

```python
# Verify Phase 2 is integrated
import inspect
from grc.routes.Risk.risk_ai_doc import call_ollama_json, infer_single_field

# Check if caching is enabled
sig = inspect.signature(call_ollama_json)
print("call_ollama_json parameters:", list(sig.parameters.keys()))
# Should include: document_hash, use_cache

sig = inspect.signature(infer_single_field)
print("infer_single_field parameters:", list(sig.parameters.keys()))
# Should include: document_hash
```

---

## 🐛 Troubleshooting

### Issue: "Redis not available"

**Solution:**
1. Install Redis: `pip install redis`
2. Start Redis server: `redis-server`
3. Check connection: `redis-cli ping` (should return `PONG`)

### Issue: "Cache always MISS"

**Check:**
1. Is Redis running? `redis-cli ping`
2. Check Redis URL in settings
3. Check logs for Redis connection errors

### Issue: "Few-shot prompts not used"

**Check:**
1. Look for errors in logs
2. Verify `few_shot_prompts.py` exists
3. Check if field name matches examples

### Issue: "Preprocessing not working"

**Check:**
1. Look for `STEP 1B` in logs
2. Check if `preprocessing_metadata` in response
3. Verify `document_preprocessor.py` is imported

---

## 📊 Expected Results Summary

| Feature | Indicator | Expected Result |
|---------|-----------|-----------------|
| **Redis Caching** | Cache HIT log | < 0.1s response |
| **Document Preprocessing** | preprocessing_metadata | Document optimized |
| **Few-Shot Prompts** | "Using few-shot prompt" log | Better accuracy |
| **Overall Speed** | Response time | 2-3x faster |
| **Cache Hit Rate** | Cache stats | 40-60% after warmup |

---

## ✅ Success Criteria

Phase 2 is working correctly if:

1. ✅ Redis caching shows cache hits on repeated requests
2. ✅ Document preprocessing metadata appears in responses
3. ✅ Few-shot prompts are used (check logs)
4. ✅ Response times are 2-3x faster
5. ✅ No import errors
6. ✅ All Phase 2 files exist and are importable

---

## 🚀 Quick Test Script

Create a test file `test_phase2.py`:

```python
#!/usr/bin/env python
"""Quick Phase 2 verification script"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tprm_backend.config.settings')
django.setup()

print("🧪 Testing Phase 2 Implementation...\n")

# Test 1: Imports
print("1. Testing imports...")
try:
    from grc.utils.ai_cache import get_redis_client, get_cache_stats
    from grc.utils.document_preprocessor import preprocess_document
    from grc.utils.few_shot_prompts import get_field_extraction_prompt
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import error: {e}")

# Test 2: Redis
print("\n2. Testing Redis connection...")
client = get_redis_client()
if client:
    try:
        client.ping()
        stats = get_cache_stats()
        print(f"   ✅ Redis connected: {stats.get('total_keys', 0)} cache keys")
    except Exception as e:
        print(f"   ⚠️  Redis error: {e}")
else:
    print("   ⚠️  Redis not available (caching disabled)")

# Test 3: Preprocessing
print("\n3. Testing document preprocessing...")
test_text = "This is a test document. " * 1000
processed, metadata = preprocess_document(test_text)
print(f"   ✅ Preprocessing works: {metadata['original_length']} → {metadata['processed_length']} chars")

# Test 4: Few-shot prompts
print("\n4. Testing few-shot prompts...")
try:
    prompt = get_field_extraction_prompt("Criticality", "Test document", {})
    if "Example" in prompt:
        print("   ✅ Few-shot prompts working")
    else:
        print("   ⚠️  Few-shot prompts may not be working")
except Exception as e:
    print(f"   ❌ Few-shot prompt error: {e}")

print("\n✅ Phase 2 testing complete!")
```

Run it:
```bash
python test_phase2.py
```

---

**Last Updated**: [Current Date]
**Status**: Ready for Testing

