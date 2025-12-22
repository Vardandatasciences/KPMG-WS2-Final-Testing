# Quick Start - Risk AI Comparison Test

## 🚀 Run the Comparison Test

### Step 1: Provide Your Document

You can test with either:
- **Local file**: `python test_risk_ai_comparison.py /path/to/document.pdf`
- **Document URL**: `python test_risk_ai_comparison.py --url https://your-document-link.com/file.pdf`

### Step 2: Wait for Results

The test will:
1. ✅ Check connections (Ollama + OpenAI)
2. 📄 Extract text from your document
3. 🧪 Test Normal version (OpenAI)
4. 🚀 Test Optimized version (Ollama)
5. 📊 Compare results
6. 💾 Save detailed report

### Step 3: Review Results

You'll see:
- ⏱️ **Performance**: How much faster is optimized version?
- 📊 **Quality**: Are extracted risks similar?
- 📋 **Details**: Risk-by-risk comparison

## 📁 Files Created

1. **`risk_ai_doc_optimized.py`** - Optimized version (ready to use)
2. **`test_risk_ai_comparison.py`** - Comparison test script
3. **`RISK_AI_COMPARISON_GUIDE.md`** - Full documentation

## 🎯 What to Expect

### Performance Improvement
- **Expected**: 2-3x faster processing
- **Time saved**: 50-60% reduction

### Quality Match
- **Expected**: 80-90% similarity
- **Both versions**: Should extract same number of risks

## 📝 Example Command

```bash
cd grc_backend
python test_risk_ai_comparison.py --url https://example.com/risk-assessment.pdf
```

## ⚠️ Requirements

- ✅ Ollama server running (configured in `settings.py`)
- ✅ Document in PDF/DOCX/XLSX/TXT format
- ⚠️ OpenAI API key (optional, for normal version comparison)

## 📊 After Testing

Once you see the results:
1. **If good** → We can integrate optimized version into your codebase
2. **If needs tuning** → We can adjust optimizations
3. **Questions?** → Check `RISK_AI_COMPARISON_GUIDE.md` for details

---

**Ready to test?** Just provide your document link or path! 🎉

