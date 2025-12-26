# Phase 1 Optimization Test Guide

## 📋 Overview

This guide explains how to run the Phase 1 optimization tests step by step.

## 🚀 Quick Start

### Prerequisites

1. **Ollama running on EC2**: Ensure Ollama is accessible at `http://13.126.18.17:11434`
2. **Python environment**: Activate your Django virtual environment
3. **Required packages**: `requests` (should already be installed)

### Running the Tests

```bash
# Navigate to backend directory
cd grc_backend

# Run the test script
python test_ai_optimization.py
```

## 📝 Test Steps Explained

### Step 1: Baseline Test
**Purpose**: Establish current performance baseline

**What it tests**:
- Current model (`llama3.2:3b` - non-quantized)
- Default context window (4096)
- Non-streaming response

**What to look for**:
- Response time (this is your baseline)
- Response quality
- Any errors

**Expected time**: 30-60 seconds

---

### Step 2: Quantized Models Test
**Purpose**: Compare speed and quality of quantized models

**What it tests**:
- `llama3.2:1b-q4_0` (ultra-fast)
- `llama3.2:3b-q4_K_M` (recommended)
- `llama3.2:8b-q4_K_M` (quantized version of current)

**What to look for**:
- Speed improvement vs baseline
- Response quality comparison
- Which models are available

**Note**: If models are not available, you'll see a message to download them:
```bash
ollama pull llama3.2:3b-q4_K_M
```

**Expected time**: 2-3 minutes (for all models)

---

### Step 3: Dynamic Context Window Test
**Purpose**: Test context sizing based on document size

**What it tests**:
- Small documents → 2048 tokens context
- Medium documents → 4096 tokens context
- Large documents → 8192 tokens context

**What to look for**:
- Speed improvement with smaller contexts
- No quality loss
- Appropriate context selection

**Expected time**: 1-2 minutes

---

### Step 4: Streaming Response Test
**Purpose**: Compare streaming vs non-streaming

**What it tests**:
- Non-streaming (current method)
- Streaming (new method)

**What to look for**:
- Similar total time (processing is same)
- Better UX with streaming (results appear immediately)
- Any implementation issues

**Expected time**: 1-2 minutes

---

### Step 5: Performance Comparison
**Purpose**: Comprehensive comparison of all optimizations

**What it tests**:
- Baseline vs Optimized
- Combined optimizations
- Overall improvement percentage

**What to look for**:
- Total improvement percentage
- Best configuration
- Ready for implementation

**Expected time**: 1-2 minutes

---

## ✅ After Each Step

1. **Review the results** displayed in the terminal
2. **Check the metrics**:
   - Response time
   - Response quality
   - Any errors
3. **Press Enter** to continue to next step
4. **Take notes** if needed

## 📊 Understanding Results

### Response Time
- **Baseline**: Your current performance (e.g., 45 seconds)
- **Optimized**: Should be 40-60% faster (e.g., 18-27 seconds)
- **Target**: 40-60% improvement

### Response Quality
- Check that responses are still accurate
- Compare response length
- Verify no degradation

### Model Availability
- ✅ Available: Model is ready to use
- ⚠️ Not Available: Need to download model
- ❌ Failed: Error occurred

## 🔧 Troubleshooting

### Connection Issues
```
❌ Failed to connect to Ollama
```
**Solution**:
1. Check Ollama is running: `ssh your-ec2 && systemctl status ollama`
2. Verify URL in settings: `OLLAMA_BASE_URL = 'http://13.126.18.17:11434'`
3. Check firewall/security groups allow port 11434

### Model Not Available
```
⚠️ Model not available
```
**Solution**:
```bash
# SSH into EC2
ssh your-ec2-instance

# Download the model
ollama pull llama3.2:3b-q4_K_M
ollama pull llama3.2:1b-q4_0
ollama pull llama3.2:8b-q4_K_M

# Verify
ollama list
```

### Timeout Errors
```
❌ Request timeout
```
**Solution**:
1. Check EC2 instance resources (CPU/Memory)
2. Increase timeout in script if needed
3. Check network connectivity

### Import Errors
```
ModuleNotFoundError: No module named 'requests'
```
**Solution**:
```bash
pip install requests
```

## 📈 Expected Results Summary

| Step | Expected Improvement | Notes |
|------|---------------------|-------|
| Step 1 (Baseline) | 0% | Establishes baseline |
| Step 2 (Quantized) | 40-50% faster | Model-dependent |
| Step 3 (Dynamic Context) | 10-20% faster | Document-dependent |
| Step 4 (Streaming) | Better UX | Same speed, better perception |
| Step 5 (Combined) | 40-60% faster | All optimizations together |

## 🎯 Decision Points

After running all tests, you should be able to answer:

1. **Which quantized model works best?**
   - Usually `llama3.2:3b-q4_K_M` for most tasks

2. **What context sizes to use?**
   - Small: 2048
   - Medium: 4096
   - Large: 8192

3. **Should we use streaming?**
   - Yes, for better UX (same speed, better perception)

4. **Ready for implementation?**
   - If tests pass and show improvements: YES ✅

## 📝 Next Steps After Testing

Once you confirm the tests show improvements:

1. **Document your results** - Save the output
2. **Choose optimal configuration** - Based on test results
3. **Proceed to implementation** - We'll update the codebase
4. **Deploy gradually** - One optimization at a time

## 💡 Tips

- **Run tests during low-traffic periods** - More accurate results
- **Run multiple times** - Average the results for better accuracy
- **Take screenshots** - Document the results
- **Compare with production** - If possible, test with real data

---

**Ready to start?** Run: `python test_ai_optimization.py`




