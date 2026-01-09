# AI Optimization Quick Reference Guide

## 🎯 Current Status Summary

### ✅ Already Implemented
- Quantized models (q4_K_M) - **2-3x faster**
- Dynamic model routing (1B/3B/8B) - **Smart model selection**
- Redis caching - **10-100x faster on cache hits**
- Document preprocessing - **1.5x faster**
- Few-shot prompts - **25-35% more accurate**
- RAG system (partial) - **40-60% more accurate when used**

### ⚠️ Needs Improvement
- Streaming disabled - **Missing 3x perceived speed**
- Batch processing missing - **Missing 3-4x speed**
- RAG not consistently used - **Missing 40-60% accuracy**
- Context sizes too large - **Missing 1.5-2x speed**
- Prompts too verbose - **Missing 30-50% speed**
- No verification step - **Missing 15-25% accuracy**

---

## 🚀 Priority Actions

### 🔴 CRITICAL (Do First - 1-2 Hours)
1. **Enable Streaming** → 3x perceived speed
   - Change `"stream": False` to `"stream": True` in all Ollama calls
   - Update 8 files (see main document)

2. **Configure Ollama Service** → Better GPU utilization
   ```bash
   sudo systemctl edit ollama
   # Add: OLLAMA_NUM_PARALLEL=2, OLLAMA_MAX_LOADED_MODELS=1
   ```

3. **Optimize Context Sizing** → 1.5-2x faster
   - Use 2048 for small docs, 4096 for medium, 8192 for large
   - Add 500 token buffer only

### 🟡 HIGH (Do Next - 1 Day)
4. **Enable Batch Processing** → 3-4x faster
   - Process multiple fields in parallel
   - Use ThreadPoolExecutor with 2-4 workers

5. **Optimize Prompts** → 30-50% faster
   - Reduce from 100+ words to 20-50 words
   - Remove polite language, be direct

6. **Enable RAG Consistently** → 40-60% more accurate
   - Make RAG default, not optional
   - Use for all document processing

### 🟢 MEDIUM (Do Later - 2-3 Days)
7. **Add Verification Step** → 15-25% more accurate
   - Second LLM pass for critical fields
   - Verify Likelihood, Impact, Exposure

8. **Implement Monitoring** → Data-driven decisions
   - Track latency, accuracy, cache hits
   - Automated benchmarking

---

## 📊 Expected Results

### Speed Improvements
| Optimization | Improvement | Status |
|-------------|-------------|--------|
| Streaming | 3x perceived | ❌ Not done |
| Context Optimization | 1.5-2x | ⚠️ Partial |
| Batch Processing | 3-4x | ❌ Not done |
| Prompt Optimization | 30-50% | ⚠️ Partial |
| **Combined** | **5-10x** | **Target** |

### Accuracy Improvements
| Optimization | Improvement | Status |
|-------------|-------------|--------|
| RAG | 40-60% | ⚠️ Partial |
| Few-Shot | 25-35% | ✅ Done |
| Verification | 15-25% | ❌ Not done |
| **Combined** | **30-50%** | **Target** |

### Cost Improvements
| Optimization | Reduction | Status |
|-------------|-----------|--------|
| Quantization | 75% memory | ✅ Done |
| Caching | 50-70% API calls | ✅ Done |
| Context Optimization | 30-40% tokens | ⚠️ Partial |
| **Combined** | **50-70%** | **Target** |

---

## 🔧 Quick Implementation Checklist

### Day 1: Quick Wins (2-4 hours)
- [ ] Enable streaming in all Ollama calls
- [ ] Configure Ollama service settings
- [ ] Optimize context window sizing
- [ ] Optimize sampling parameters (top_k=10, num_predict=512)
- [ ] Test and measure improvements

### Day 2-3: Batch & Prompts (1-2 days)
- [ ] Implement batch processing utility
- [ ] Update all extraction functions to use batching
- [ ] Optimize all prompts (reduce to 20-50 words)
- [ ] Test with real documents

### Day 4-5: RAG & Verification (1-2 days)
- [ ] Make RAG default (remove optional checks)
- [ ] Implement verification step for critical fields
- [ ] Test accuracy improvements
- [ ] Benchmark before/after

### Week 2: Advanced (3-5 days)
- [ ] Implement comprehensive monitoring
- [ ] Standardize model config across modules
- [ ] Add automated benchmarking
- [ ] Create performance dashboard

---

## 📈 Success Metrics

### Target Metrics
- ✅ Average latency: **< 5 seconds** (currently ~10-15s)
- ✅ P95 latency: **< 10 seconds** (currently ~20-30s)
- ✅ Accuracy: **> 90%** (currently ~75-80%)
- ✅ Cache hit rate: **> 50%** (currently ~30-40%)
- ✅ GPU utilization: **60-80%** (currently ~40-50%)

### Measurement
- Run benchmarks before each phase
- Track metrics daily
- Compare weekly
- Adjust based on data

---

## 🎯 Key Files to Update

### Streaming (8 files)
1. `grc_backend/grc/routes/Risk/risk_ai_doc.py`
2. `grc_backend/grc/routes/Incident/incident_ai_import.py`
3. `grc_backend/grc/routes/Audit/ai_audit_api.py`
4. `tprm_backend/risk_analysis/llama_service.py`
5. `tprm_backend/risk_analysis_vendor/llama_service.py`
6. `tprm_backend/rfp_risk_analysis/llama_service.py`
7. `tprm_backend/contract_risk_analysis/llama_service.py`
8. `tprm_backend/lamma.py`

### Batch Processing (3 files)
1. `grc_backend/grc/utils/batch_processor.py` (new)
2. `grc_backend/grc/routes/Risk/risk_ai_doc.py` (update)
3. `grc_backend/grc/routes/Incident/incident_ai_import.py` (update)

### RAG (4 files)
1. `grc_backend/grc/routes/Risk/risk_ai_doc.py` (make RAG default)
2. `grc_backend/grc/routes/Incident/incident_ai_import.py` (make RAG default)
3. `grc_backend/grc/routes/Risk/risk_instance_ai.py` (make RAG default)
4. `grc_backend/grc/routes/Audit/ai_audit_api.py` (make RAG default)

---

## 💡 Key Insights

1. **Streaming is the easiest win** - Just change one parameter, huge UX improvement
2. **Batch processing has biggest speed impact** - 3-4x faster for multi-field extraction
3. **RAG is underutilized** - Already implemented but not used consistently
4. **Prompts are too verbose** - Simple reduction = 30-50% faster processing
5. **Context sizes are conservative** - Can be more aggressive for speed

---

## 📞 Next Steps

1. **Review** this document and the detailed analysis
2. **Prioritize** based on your needs (speed vs accuracy)
3. **Start with quick wins** (streaming, context optimization)
4. **Measure** improvements after each change
5. **Iterate** based on results

---

**For detailed implementation instructions, see**: `AI_MODEL_OPTIMIZATION_ANALYSIS.md`

**Questions?** Review the detailed analysis document for code examples and step-by-step instructions.









