# Phase 2 Implementation Discussion & Plan

## 📊 Current Status Assessment

### ✅ Already Implemented (From Phase 1)
- Quantized models (3B, 1B, 8B)
- Dynamic context window sizing
- Intelligent model selection
- Temperature settings (0.1 for extraction tasks)

### 🔍 Phase 2 Requirements Analysis

Based on the implementation plan, Phase 2 includes:
1. **Redis Caching Layer** (Step 6) - 3-4 hours
2. **Document Preprocessing Pipeline** (Step 7) - 2-3 hours
3. **Few-Shot Prompt Templates** (Step 8) - 2 hours
4. **Task-Specific Temperature Settings** (Step 9) - Already done! ✅
5. **Benchmarking** (Step 10) - 1 hour

**Expected Results**: 2-3x faster, 30% more accurate

---

## 🎯 Phase 2 Implementation Details

### Step 6: Redis Caching Layer (3-4 hours)

#### Current State
- ✅ Redis is already installed (`redis>=5` in requirements.txt)
- ✅ Redis is configured in settings (`REDIS_URL` in config/settings.py)
- ❌ **NOT used for AI/LLM response caching**

#### What Needs to Be Done

**1. Create Cache Wrapper for LLM Calls**

Create: `grc_backend/grc/utils/ai_cache.py`

```python
"""
AI Response Caching Layer using Redis
- Caches LLM responses to avoid redundant API calls
- 10-100x speed improvement on cache hits
"""

import hashlib
import json
import redis
from django.conf import settings
from typing import Any, Optional

# Redis connection
redis_client = redis.Redis.from_url(
    getattr(settings, 'REDIS_URL', 'redis://localhost:6379/2'),  # Use DB 2 for AI cache
    decode_responses=True
)

def generate_cache_key(model_name: str, prompt: str, document_hash: str = None) -> str:
    """
    Generate cache key from model, prompt, and document hash.
    
    Args:
        model_name: LLM model name (e.g., 'llama3.2:3b-instruct-q4_K_M')
        prompt: The prompt text
        document_hash: Optional hash of document content
    
    Returns:
        Cache key string
    """
    key_parts = [model_name, prompt]
    if document_hash:
        key_parts.append(document_hash)
    
    key_string = "|".join(key_parts)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()
    return f"ai_cache:{key_hash}"

def get_cached_response(cache_key: str) -> Optional[Any]:
    """Get cached response if exists."""
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        print(f"⚠️  Cache read error: {e}")
    return None

def set_cached_response(cache_key: str, response: Any, ttl: int = 86400):
    """
    Cache response with TTL.
    
    Args:
        cache_key: Cache key
        response: Response to cache
        ttl: Time to live in seconds (default: 24 hours)
    """
    try:
        redis_client.setex(
            cache_key,
            ttl,
            json.dumps(response)
        )
    except Exception as e:
        print(f"⚠️  Cache write error: {e}")

def cached_llm_call(llm_function, model_name: str, prompt: str, 
                    document_hash: str = None, ttl: int = 86400, 
                    use_cache: bool = True) -> Any:
    """
    Wrapper for LLM calls with caching.
    
    Args:
        llm_function: The LLM call function (call_ollama_json or call_openai_json)
        model_name: Model name
        prompt: Prompt text
        document_hash: Optional document hash
        ttl: Cache TTL in seconds
        use_cache: Whether to use cache (can disable for testing)
    
    Returns:
        LLM response (from cache or fresh call)
    """
    if not use_cache:
        return llm_function(prompt, model=model_name if 'ollama' in llm_function.__name__ else None)
    
    cache_key = generate_cache_key(model_name, prompt, document_hash)
    
    # Try cache first
    cached = get_cached_response(cache_key)
    if cached:
        print(f"✅ Cache HIT for {model_name[:30]}...")
        return cached
    
    # Cache miss - call LLM
    print(f"❌ Cache MISS for {model_name[:30]}... - calling LLM")
    response = llm_function(prompt, model=model_name if 'ollama' in llm_function.__name__ else None)
    
    # Cache the response
    set_cached_response(cache_key, response, ttl)
    print(f"💾 Cached response for future use")
    
    return response
```

**2. Integrate Cache into Existing Functions**

Update `risk_ai_doc.py`:
- Wrap `call_ollama_json()` and `call_openai_json()` with caching
- Add document hash calculation
- Set appropriate TTLs (24 hours for document analysis, 1 hour for queries)

**3. Cache Strategy**
- **Cache Key**: `sha256(model_name + prompt + document_hash)`
- **TTL**: 
  - Document analysis: 24 hours (86400 seconds)
  - Simple queries: 1 hour (3600 seconds)
- **Cache Size**: Monitor Redis memory usage

**Expected Impact**: 10-100x faster on cache hits

---

### Step 7: Document Preprocessing Pipeline (2-3 hours)

#### Current State
- ✅ Text extraction exists (`extract_text_from_file()`)
- ❌ **No centralized preprocessing pipeline**
- ❌ **No text cleaning/normalization**
- ❌ **No intelligent truncation**

#### What Needs to Be Done

**Create: `grc_backend/grc/utils/document_preprocessor.py`**

```python
"""
Document Preprocessing Pipeline
- Cleans and normalizes text before AI processing
- 1.5x speed improvement
"""

import re
from typing import Tuple

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace (multiple spaces, tabs, newlines)."""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    return text.strip()

def remove_control_characters(text: str) -> str:
    """Remove non-printable control characters."""
    return ''.join(char for char in text if char.isprintable() or char in '\n\r\t')

def truncate_intelligently(text: str, max_length: int = 8000) -> str:
    """
    Truncate text intelligently, preserving:
    - Beginning (important context)
    - End (conclusions)
    - Middle section (summary)
    """
    if len(text) <= max_length:
        return text
    
    # Calculate split points
    start_len = max_length // 3
    end_len = max_length // 3
    mid_len = max_length - start_len - end_len
    
    start = text[:start_len]
    end = text[-end_len:]
    
    # Try to find sentence boundaries
    mid_start = len(text) // 2 - mid_len // 2
    mid_end = mid_start + mid_len
    
    # Find nearest sentence boundary
    mid_start = text.rfind('.', 0, mid_start) + 1
    mid_end = text.find('.', mid_end) + 1
    
    if mid_start == 0 or mid_end == 0:
        mid_start = len(text) // 2 - mid_len // 2
        mid_end = mid_start + mid_len
    
    middle = text[mid_start:mid_end]
    
    return f"{start}\n\n[... content truncated for performance ...]\n\n{middle}\n\n[... content truncated ...]\n\n{end}"

def preprocess_document(text: str, max_length: int = 8000) -> Tuple[str, dict]:
    """
    Full preprocessing pipeline.
    
    Returns:
        (processed_text, metadata_dict)
    """
    original_length = len(text)
    
    # Step 1: Remove control characters
    text = remove_control_characters(text)
    
    # Step 2: Normalize whitespace
    text = normalize_whitespace(text)
    
    # Step 3: Intelligent truncation
    was_truncated = len(text) > max_length
    if was_truncated:
        text = truncate_intelligently(text, max_length)
    
    metadata = {
        'original_length': original_length,
        'processed_length': len(text),
        'was_truncated': was_truncated,
        'reduction_percent': round((1 - len(text) / original_length) * 100, 2) if original_length > 0 else 0
    }
    
    return text, metadata
```

**Integration Points**:
- Update `extract_text_from_file()` to use preprocessing
- Apply preprocessing before AI calls in `risk_ai_doc.py` and `risk_instance_ai.py`

**Expected Impact**: 1.5x speed improvement

---

### Step 8: Few-Shot Prompt Templates (2 hours)

#### Current State
- ✅ Field-specific prompts exist (`FIELD_PROMPTS`)
- ❌ **No few-shot examples in prompts**
- ❌ **No structured prompt templates with examples**

#### What Needs to Be Done

**Create: `grc_backend/grc/utils/few_shot_prompts.py`**

```python
"""
Few-Shot Prompt Templates
- 25-35% accuracy improvement with examples
"""

# Risk Extraction Examples
RISK_EXTRACTION_EXAMPLES = """
Example 1:
Document: "Risk 1: Data Breach - Unauthorized access to customer database could result in exposure of 50,000 customer records."
Extracted:
{
  "RiskTitle": "Data Breach",
  "Criticality": "High",
  "PossibleDamage": "Exposure of 50,000 customer records, potential regulatory fines, reputation damage",
  "Category": "Information Security",
  "RiskType": "Current",
  "BusinessImpact": "Regulatory compliance violations, customer trust loss, potential GDPR fines up to 4% of revenue",
  "RiskDescription": "Unauthorized access to customer database could result in data exposure",
  "RiskLikelihood": 6,
  "RiskImpact": 9,
  "RiskExposureRating": 54.0,
  "RiskPriority": "High",
  "RiskMitigation": "1. Implement multi-factor authentication 2. Encrypt database at rest 3. Regular security audits 4. Access control reviews"
}

Example 2:
Document: "Risk 2: Vendor Dependency - Over-reliance on single cloud provider for critical infrastructure."
Extracted:
{
  "RiskTitle": "Vendor Dependency",
  "Criticality": "Medium",
  "PossibleDamage": "Service disruption if vendor fails, limited negotiation power, vendor lock-in",
  "Category": "Third-Party",
  "RiskType": "Current",
  "BusinessImpact": "Potential service outages affecting 80% of operations, increased costs due to lack of alternatives",
  "RiskDescription": "Over-reliance on single cloud provider creates dependency risk",
  "RiskLikelihood": 4,
  "RiskImpact": 7,
  "RiskExposureRating": 28.0,
  "RiskPriority": "Medium",
  "RiskMitigation": "1. Identify backup providers 2. Develop migration plan 3. Negotiate SLA terms 4. Regular vendor assessments"
}
"""

def build_few_shot_prompt(task_type: str, document_text: str, field_name: str = None) -> str:
    """
    Build prompt with few-shot examples.
    
    Args:
        task_type: 'risk_extraction', 'incident_analysis', 'compliance_check'
        document_text: Document to analyze
        field_name: Optional specific field to extract
    """
    examples = {
        'risk_extraction': RISK_EXTRACTION_EXAMPLES,
        # Add more example sets for other tasks
    }
    
    example_text = examples.get(task_type, "")
    
    if field_name:
        # Single field extraction
        prompt = f"""
You are a GRC analyst. Extract the field "{field_name}" from this document.

{example_text}

Document to analyze:
\"\"\"{document_text[:3000]}\"\"\"

Extract ONLY the "{field_name}" field. Return JSON: {{"value": "...", "confidence": 0.0-1.0}}
"""
    else:
        # Full extraction
        prompt = f"""
You are a GRC analyst. Extract ALL risk information from this document.

{example_text}

Document to analyze:
\"\"\"{document_text[:8000]}\"\"\"

Extract all risks following the examples above. Return JSON array of risks.
"""
    
    return prompt
```

**Integration Points**:
- Update `infer_single_field()` to use few-shot prompts
- Update `parse_risks_from_text()` to use few-shot examples

**Expected Impact**: 25-35% accuracy improvement

---

### Step 9: Task-Specific Temperature Settings ✅

#### Status: **ALREADY IMPLEMENTED**
- Temperature is set to 0.1 (deterministic) for extraction tasks
- This is appropriate for the current use case

**No action needed** ✅

---

### Step 10: Benchmarking (1 hour)

#### What Needs to Be Done

Create test suite to measure:
- Response times (before/after Phase 2)
- Cache hit rates
- Accuracy improvements
- Resource usage

**Create: `grc_backend/grc/utils/ai_benchmark.py`**

```python
"""
AI Performance Benchmarking
"""

import time
from typing import Dict, List

class AIBenchmark:
    def __init__(self):
        self.results = []
    
    def benchmark_call(self, llm_function, prompt: str, model: str = None) -> Dict:
        """Benchmark a single LLM call."""
        start = time.time()
        response = llm_function(prompt, model=model)
        elapsed = time.time() - start
        
        return {
            'model': model,
            'prompt_length': len(prompt),
            'response_time': elapsed,
            'response_length': len(str(response)),
            'timestamp': time.time()
        }
    
    def compare_before_after(self, before_results: List[Dict], after_results: List[Dict]):
        """Compare performance before and after optimization."""
        avg_before = sum(r['response_time'] for r in before_results) / len(before_results)
        avg_after = sum(r['response_time'] for r in after_results) / len(after_results)
        
        improvement = ((avg_before - avg_after) / avg_before) * 100
        
        print(f"📊 Benchmark Results:")
        print(f"   Before: {avg_before:.2f}s average")
        print(f"   After: {avg_after:.2f}s average")
        print(f"   Improvement: {improvement:.1f}% faster")
```

---

## 📋 Implementation Priority

### Recommended Order:

1. **Step 6: Redis Caching** (Highest Impact)
   - 10-100x speed improvement on cache hits
   - Most users will benefit immediately
   - **Time: 3-4 hours**

2. **Step 7: Document Preprocessing** (Quick Win)
   - 1.5x speed improvement
   - Relatively simple to implement
   - **Time: 2-3 hours**

3. **Step 8: Few-Shot Prompts** (Accuracy Boost)
   - 25-35% accuracy improvement
   - Requires creating good examples
   - **Time: 2 hours**

4. **Step 10: Benchmarking** (Validation)
   - Measure improvements
   - **Time: 1 hour**

---

## 🚀 Quick Start Implementation

### Option 1: Start with Caching (Recommended)
**Why**: Biggest impact, reusable across all AI endpoints

**Steps**:
1. Create `grc_backend/grc/utils/ai_cache.py`
2. Update `risk_ai_doc.py` to use caching
3. Test with sample documents
4. Monitor cache hit rates

### Option 2: Start with Preprocessing (Easier)
**Why**: Simpler implementation, immediate benefits

**Steps**:
1. Create `grc_backend/grc/utils/document_preprocessor.py`
2. Integrate into `extract_text_from_file()`
3. Test with various document types

---

## 📊 Expected Results After Phase 2

| Metric | Before Phase 2 | After Phase 2 | Improvement |
|--------|----------------|---------------|-------------|
| **Average Response Time** | 10-15s | 3-5s (cache miss), <0.1s (cache hit) | 2-3x faster |
| **Accuracy** | Baseline | +30% | 30% better |
| **Cache Hit Rate** | 0% | 40-60% (after warmup) | N/A |
| **Document Processing** | 15-20s | 5-8s | 2-3x faster |

---

## ❓ Questions for Discussion

1. **Caching Strategy**:
   - What TTL do you prefer? (24 hours for documents, 1 hour for queries?)
   - Should we cache all responses or only successful ones?
   - Do you want cache invalidation controls?

2. **Preprocessing**:
   - What's the maximum document size you typically process?
   - Should we preserve formatting or strip everything?
   - Any specific text cleaning requirements?

3. **Few-Shot Examples**:
   - Do you have sample documents we can use to create better examples?
   - Should examples be domain-specific (e.g., healthcare, finance)?

4. **Implementation Order**:
   - Which step would you like to start with?
   - Do you want all steps implemented, or prioritize specific ones?

---

## 🎯 Next Steps

1. **Decide on implementation order** (I recommend: Caching → Preprocessing → Few-Shot)
2. **Review and approve the approach** for each step
3. **Start implementation** - I can help implement any step you choose
4. **Test and validate** improvements

---

**Ready to proceed?** Let me know which step you'd like to start with, and I'll implement it! 🚀



