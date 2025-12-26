# AI Model Optimization Implementation Plan

## 📋 Overview

This document outlines the step-by-step plan to optimize AI model performance in your GRC product using Ollama. The optimizations will improve speed by 5-10x and accuracy by 30-50% based on the AI Model Optimization guide.

---

## 🎯 Current State

- **AI Framework**: Ollama
- **Deployment**: EC2 Instance
- **Current Models**:
  - Llama 3.2 8B
  - Phi Mini 3
- **Use Cases**: Based on your codebase analysis:
  - Audit document processing
  - Data analysis
  - Risk assessment
  - Incident analysis
  - Policy extraction

---

## 🚀 Recommended Models

### Primary Recommendations (Based on Your Use Cases)

#### 1. **Llama 3.2 3B (Quantized) - RECOMMENDED for Most Tasks**
```bash
ollama pull llama3.2:3b-q4_K_M
```
- **Why**: Best balance of speed and quality for document processing
- **VRAM**: ~2GB
- **Speed**: 3-4x faster than 8B model
- **Use For**: 
  - General document processing
  - Text extraction
  - Summarization
  - Most audit/risk tasks

#### 2. **Llama 3.2 1B (Quantized) - For Simple Tasks**
```bash
ollama pull llama3.2:1b-q4_0
```
- **Why**: Ultra-fast for simple Q&A and basic extraction
- **VRAM**: ~1GB
- **Speed**: 5-8x faster than 8B
- **Use For**:
  - Simple queries
  - Basic text extraction
  - Quick summaries

#### 3. **Keep Llama 3.2 8B (Quantized) - For Complex Reasoning**
```bash
ollama pull llama3.2:8b-q4_K_M
```
- **Why**: Better accuracy for complex analysis
- **VRAM**: ~5GB
- **Use For**:
  - Complex compliance analysis
  - Deep risk assessments
  - Critical document review

#### 4. **Phi-3.5 Mini (Quantized) - Alternative Lightweight**
```bash
ollama pull phi3.5:mini-q4_K_M
```
- **Why**: Excellent for structured data extraction
- **VRAM**: ~2.5GB
- **Speed**: Fast and efficient
- **Use For**:
  - Structured data extraction
  - Form filling
  - Quick analysis

### Model Selection Matrix

| Task Type | Recommended Model | Speed Gain | Accuracy |
|-----------|------------------|------------|----------|
| Simple Q&A | Llama 3.2 1B-q4_0 | 5-8x | Good |
| Document Processing | Llama 3.2 3B-q4_K_M | 3-4x | Excellent |
| Complex Analysis | Llama 3.2 8B-q4_K_M | 2x | Best |
| Structured Extraction | Phi-3.5 Mini-q4_K_M | 3-4x | Excellent |

---

## 📝 Implementation Steps

### Phase 1: Quick Wins (1-2 Hours) - 40-60% Speed Improvement

#### Step 1: Download Quantized Models (15 minutes)
```bash
# SSH into your EC2 instance
ssh your-ec2-instance

# Download optimized quantized models
ollama pull llama3.2:3b-q4_K_M
ollama pull llama3.2:1b-q4_0
ollama pull llama3.2:8b-q4_K_M  # If you need to keep 8B, use quantized version
ollama pull phi3.5:mini-q4_K_M

# Verify models
ollama list
```

**Expected Result**: Models ready for use

---

#### Step 2: Configure Ollama Memory Settings (10 minutes)
```bash
# Edit Ollama service configuration
sudo systemctl edit ollama

# Add these environment variables:
[Service]
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_NUM_GPU=1"  # If you have GPU

# Save and reload
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Verify Ollama is running
sudo systemctl status ollama
```

**Expected Result**: Better memory utilization and stability

---

#### Step 3: Reduce Context Window in Code (5 minutes)

**Action**: Update your backend code to use dynamic context sizing

**Current Issue**: You're likely using default 4096 or 8192 tokens for all documents

**Solution**: Implement dynamic context sizing based on document size

**Files to Update**:
- `grc_backend/grc/routes/Audit/ai_audit_api.py`
- `grc_backend/grc/routes/DataAnalysis/aiDataAnalysis.py`
- `grc_backend/grc/routes/Risk/slm_service.py`
- Other AI route files

**Context Size Guidelines**:
- Small documents (< 1000 words): 2048 tokens
- Medium documents (1000-3000 words): 4096 tokens
- Large documents (> 3000 words): 8192 tokens

---

#### Step 4: Enable Streaming Responses (30 minutes)

**Action**: Update API calls to use streaming

**Benefits**: 
- Perceived 3x faster user experience
- Better UX with progressive results

**Implementation**: Change `stream: false` to `stream: true` in Ollama API calls

---

#### Step 5: Verify Improvements (20 minutes)
```bash
# Test with sample document
# Measure response time before and after
# Compare output quality
```

**Expected Result**: 40-60% faster responses

---

### Phase 2: Medium-Term Optimizations (1 Day) - 2-3x Faster, 30% More Accurate

#### Step 6: Implement Redis Caching Layer (3-4 hours)

**Why**: Cache frequently asked queries for 10-100x speed improvement on cache hits

**Implementation**:
1. Install Redis on EC2
2. Create cache wrapper for LLM calls
3. Implement cache key generation
4. Set appropriate TTL (Time To Live)

**Cache Strategy**:
- Cache key: Hash of (model_name + prompt + document_hash)
- TTL: 24 hours for document analysis, 1 hour for queries
- Cache size: Monitor and adjust based on memory

---

#### Step 7: Build Document Preprocessing Pipeline (2-3 hours)

**Why**: Clean and prepare documents before processing (1.5x speed improvement)

**Implementation**:
1. Text extraction from PDFs
2. Whitespace normalization
3. Text truncation for oversized documents
4. Format standardization

**Files to Create**:
- `grc_backend/grc/utils/document_preprocessor.py`

---

#### Step 8: Create Few-Shot Prompt Templates (2 hours)

**Why**: 25-35% accuracy improvement with examples

**Implementation**:
1. Identify main use cases
2. Create 3-5 example prompts per use case
3. Update prompt templates in code
4. Test against baseline

**Use Cases to Cover**:
- Document compliance analysis
- Risk assessment
- Data extraction
- Incident analysis

---

#### Step 9: Configure Task-Specific Temperature Settings (1-2 hours)

**Why**: Better accuracy and consistency

**Temperature Guidelines**:
- Extraction tasks: 0.1 (deterministic)
- Analysis tasks: 0.5 (balanced)
- Creative tasks: 0.8 (more creative)

**Implementation**: Create configuration presets and map tasks to presets

---

#### Step 10: End-of-Day Benchmarking (1 hour)

**Action**: Run comprehensive tests comparing:
- Before optimization baseline
- After Phase 1 (Quick Wins)
- After Phase 2 (Medium-term)

**Expected Result**: 2-3x faster, 30% more accurate overall

---

### Phase 3: Advanced Optimizations (Optional - 2-3 Days)

#### Step 11: Implement RAG (Retrieval Augmented Generation) (1 day)

**Why**: +40% accuracy improvement for domain-specific queries

**Implementation**:
1. Set up vector database (ChromaDB or Pinecone)
2. Create embeddings for your documents
3. Implement retrieval system
4. Integrate with LLM calls

---

#### Step 12: Model Routing System (4 hours)

**Why**: Automatically select best model for each task

**Implementation**:
- Create model selection logic based on:
  - Document size
  - Task complexity
  - Required accuracy level
  - Current system load

---

#### Step 13: Request Queuing and Rate Limiting (3 hours)

**Why**: Prevent system overload and ensure stability

**Implementation**:
- Implement queue system for requests
- Add rate limiting per user/IP
- Monitor queue length and wait times

---

## 🔧 Configuration Changes

### Backend Settings (`grc_backend/backend/settings.py`)

Add these configurations:

```python
# Ollama Configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3.2:3b-q4_K_M")

# Model Selection by Task
OLLAMA_MODELS = {
    'simple': 'llama3.2:1b-q4_0',
    'general': 'llama3.2:3b-q4_K_M',
    'complex': 'llama3.2:8b-q4_K_M',
    'extraction': 'phi3.5:mini-q4_K_M',
}

# Context Window Settings
CONTEXT_WINDOW_SIZES = {
    'small': 2048,   # < 1000 words
    'medium': 4096,  # 1000-3000 words
    'large': 8192,   # > 3000 words
}

# Temperature Settings by Task
TEMPERATURE_SETTINGS = {
    'extraction': 0.1,
    'analysis': 0.5,
    'creative': 0.8,
}

# Redis Cache Configuration
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_CACHE_TTL = int(os.environ.get("REDIS_CACHE_TTL", 86400))  # 24 hours
```

---

## 📊 Testing & Validation

### Performance Metrics to Track

1. **Response Time**:
   - Average response time
   - P95 response time
   - P99 response time

2. **Accuracy**:
   - Task completion rate
   - Output quality scores
   - User satisfaction

3. **Resource Usage**:
   - Memory consumption
   - CPU usage
   - GPU utilization (if available)

### Test Cases

1. **Simple Query Test**:
   - Query: "What is the compliance status?"
   - Expected: < 2 seconds
   - Model: llama3.2:1b-q4_0

2. **Document Analysis Test**:
   - Document: 2000-word audit report
   - Expected: < 10 seconds
   - Model: llama3.2:3b-q4_K_M

3. **Complex Analysis Test**:
   - Task: Full compliance mapping
   - Expected: < 30 seconds
   - Model: llama3.2:8b-q4_K_M

---

## 🚨 Important Notes

### Before Starting

1. **Backup Current Setup**: 
   - Document current model names in use
   - Save current configuration files
   - Note current performance metrics

2. **Test Environment**: 
   - Consider testing on a staging environment first
   - Have rollback plan ready

3. **Monitoring**: 
   - Set up logging for all LLM calls
   - Monitor error rates
   - Track performance metrics

### During Implementation

1. **One Change at a Time**: Implement and test each optimization separately
2. **Document Changes**: Keep track of what changed and why
3. **User Communication**: Inform users about potential improvements

### After Implementation

1. **Monitor Performance**: Watch for 1 week after deployment
2. **Gather Feedback**: Collect user feedback on speed and accuracy
3. **Fine-tune**: Adjust based on real-world usage patterns

---

## 📈 Expected Results Summary

| Phase | Time Investment | Speed Improvement | Accuracy Improvement |
|-------|----------------|-------------------|---------------------|
| Phase 1 (Quick Wins) | 1-2 hours | 40-60% faster | Minimal change |
| Phase 2 (Medium-term) | 1 day | 2-3x faster | +30% |
| Phase 3 (Advanced) | 2-3 days | 5-10x faster | +30-50% |

---

## 🎯 Next Steps

1. **Review this plan** - Understand all steps
2. **Prepare EC2 instance** - Ensure you have SSH access
3. **Backup current setup** - Document current state
4. **Start with Phase 1** - Quick wins first
5. **Test thoroughly** - Before moving to next phase
6. **Deploy gradually** - One optimization at a time

---

## 📞 Support & Questions

If you encounter issues during implementation:
1. Check Ollama logs: `journalctl -u ollama -f`
2. Verify model availability: `ollama list`
3. Test model directly: `ollama run llama3.2:3b-q4_K_M`
4. Check EC2 resources: `htop` or `nvidia-smi` (if GPU)

---

**Last Updated**: [Current Date]
**Version**: 1.0
**Status**: Ready for Implementation




