# Quick Reference - AI Analysis Testing

## 🚀 Quick Commands

### Test AI Analysis (No DB Changes)
```bash
cd backend
python grc/changeManagement/test_ai_analysis.py YOUR_PDF_FILE.pdf
```

### Full Processing (S3 + DB Update)
```bash
cd backend
python grc/changeManagement/test_ai_analysis.py YOUR_PDF_FILE.pdf --full
```

### Run All System Tests
```bash
cd backend
python grc/changeManagement/test_system.py
```

### List Available PDFs
```bash
cd backend
python grc/changeManagement/test_ai_analysis.py
```

## 📊 What Success Looks Like

### ✅ Good AI Analysis
```
🔄 Sending request to OpenAI (gpt-4o-mini)...
✅ AI analysis successful - extracted structured data
📊 AI extracted: 15 modified controls, 5 new additions, 2 framework references

Framework Name: PCI DSS v4.0
Confidence: 0.90
Modified Controls: 15
New Additions: 5
```

### ⚠️ Fallback (No AI)
```
⚠️ AI analysis disabled - using fallback detection
⚠️ AI analysis returned no results - using filename-based detection

Modified Sections: 1
- section_type: policy
- section_name: PCI DSS Requirements
- modification_type: update
```

## 🔧 Quick Fixes

### Problem: AI returns null
```bash
# Check if OpenAI is configured
grep OPENAI_API_KEY backend/settings.py

# Test with detailed output
python grc/changeManagement/test_ai_analysis.py YOUR_PDF.pdf
```

### Problem: Empty arrays in AI response
**Solution**: Increase text extraction in `changemanagement.py` line 339:
```python
max_pages: int = 15,     # from 10
max_chars: int = 15000   # from 12000
```

### Problem: Wrong framework detected
**Solution**: Check framework names in database:
```bash
python manage.py shell
>>> from grc.models import Framework
>>> list(Framework.objects.values_list('FrameworkName', flat=True))
```

## 📂 File Locations

```
backend/grc/changeManagement/
├── changemanagement.py          # Main service (MODIFIED)
├── test_system.py               # System tests
├── test_ai_analysis.py          # New AI test tool (NEW)
├── data/                        # PDF storage directory
│   ├── *.pdf                    # Your PDFs here
│   ├── processed_files.json     # Processing state
│   └── state.json               # Selenium state
├── CHANGES_SUMMARY.md           # This summary (NEW)
├── PROMPT_IMPROVEMENTS.md       # Detailed docs (NEW)
├── README_TESTING.md            # Testing guide (NEW)
└── QUICK_REFERENCE.md           # This file (NEW)
```

## 🎯 Framework Patterns

The system looks for these patterns:

| Framework | Control ID Pattern | Example |
|-----------|-------------------|---------|
| PCI DSS | `Requirement X.X.X` | Requirement 1.2.3 |
| NIST | `XX-NN` or `XX-NN(NN)` | AC-2, SI-7(12) |
| ISO | `A.X.X` or Clause N | A.5.1, Clause 8 |
| HIPAA | `§ X.X` | § 164.308 |
| GDPR | `Article X` | Article 32 |

## 💡 Pro Tips

1. **Start Simple**: Test AI analysis first without full processing
2. **Check Text**: Always verify text extraction is working
3. **Review Output**: Check the generated JSON file for quality
4. **Monitor Costs**: Use gpt-4o-mini unless you need higher accuracy
5. **Cache Results**: Save AI analysis to avoid reprocessing

## 📈 Expected Performance

- Text extraction: 1-2 seconds
- AI analysis: 5-15 seconds
- S3 upload: 2-5 seconds
- **Total**: ~10-25 seconds per PDF

## 🔍 Debugging Checklist

- [ ] OpenAI API key configured in settings
- [ ] PDF file exists in data directory
- [ ] PDF is text-based (not scanned image)
- [ ] Text extraction returns content
- [ ] OpenAI API call succeeds
- [ ] JSON parsing succeeds
- [ ] Framework exists in database

## 📞 Need Help?

1. Read `README_TESTING.md` for detailed troubleshooting
2. Check `PROMPT_IMPROVEMENTS.md` for technical details
3. Review `CHANGES_SUMMARY.md` for overview
4. Run test script to see detailed output

---

**Quick Link to Main Docs**:
- [Changes Summary](./CHANGES_SUMMARY.md)
- [Testing Guide](./README_TESTING.md)
- [Technical Details](./PROMPT_IMPROVEMENTS.md)

