# Testing the Improved AI Analysis

## Quick Start

### 1. Test AI Analysis Only (No DB Changes)
This tests the AI prompt and shows what it extracts without making any changes to the database:

```bash
cd backend
python grc/changeManagement/test_ai_analysis.py PCI-DSS-v3-2-1-to-v4-0-Summary-of-Changes-r1.pdf
```

### 2. Full Processing Test (With S3 Upload & DB Update)
This performs the complete workflow including S3 upload and database updates:

```bash
cd backend
python grc/changeManagement/test_ai_analysis.py PCI-DSS-v3-2-1-to-v4-0-Summary-of-Changes-r1.pdf --full
```

### 3. Run System Tests
This runs all system tests including the new PDF processing:

```bash
cd backend
python grc/changeManagement/test_system.py
```

## What to Look For

### ✅ Success Indicators

1. **Text Extraction**
   ```
   ✅ Extracted 12000 characters
   📝 Preview (first 500 chars): Payment Card Industry Data Security Standard...
   ```

2. **AI Analysis Success**
   ```
   🔄 Sending request to OpenAI (gpt-4o-mini)...
   ✅ AI analysis successful - extracted structured data
   📊 AI extracted: 15 modified controls, 5 new additions, 2 framework references
   ```

3. **Structured Data Extraction**
   ```
   Modified Controls: 15
   1. Requirement 1.2.3: Network Segmentation
      Type: modified
      Description: Updated to include cloud environments...
   
   New Additions: 5
   1. Requirement 6.4.3: Secure Software Development
      Scope: Applies to all custom software...
   ```

### ⚠️ Warning Signs

1. **AI Disabled**
   ```
   ⚠️ AI analysis disabled - using fallback detection
   ```
   **Fix**: Check `OPENAI_API_KEY` in Django settings

2. **No Text Extracted**
   ```
   ⚠️ Could not extract text from PDF for AI analysis
   ```
   **Fix**: PDF might be image-based (scanned). Consider OCR or try different PDF

3. **Empty Analysis**
   ```
   📊 AI extracted: 0 modified controls, 0 new additions, 0 framework references
   ```
   **Fix**: Increase max_pages/max_chars or check PDF content structure

4. **Generic Fallback Data**
   ```
   Modified Sections: 1
   - section_type: policy
   - section_name: PCI DSS Requirements
   - modification_type: update
   ```
   **Fix**: AI analysis failed, using filename-based fallback

### ❌ Errors

1. **OpenAI API Error**
   ```
   ❌ OpenAI API error (chat): Invalid API key
   ```
   **Fix**: Update `OPENAI_API_KEY` in settings

2. **JSON Parsing Error**
   ```
   ⚠️ AI analysis JSON parsing failed: Expecting property name...
   ```
   **Fix**: AI returned malformed JSON. Check model/prompt compatibility

## Expected Output Structure

For **PCI DSS** documents, you should see:
- Framework Name: "PCI DSS v4.0" or similar
- Control IDs: "Requirement X.X.X" format
- Modified controls with specific requirement numbers
- New additions with clear scope and purpose

For **NIST** documents, you should see:
- Framework Name: "NIST SP 800-53 Release X.X.X"
- Control IDs: "AC-2", "SI-7", "SA-15(13)" format
- Control enhancements with specific updates
- Framework references to SP 800-53A, SP 800-53B

## Comparing Old vs New Output

### Old Output (Generic)
```json
{
  "ai_analysis": null,
  "modified_sections": [
    {
      "description": "Payment Card Industry standards updated",
      "section_name": "PCI DSS Requirements",
      "section_type": "policy",
      "modification_type": "update"
    }
  ]
}
```

### New Output (Structured)
```json
{
  "ai_analysis": {
    "framework_name": "PCI DSS v4.0",
    "confidence": 0.9,
    "summary": "Summary of changes from PCI DSS v3.2.1 to v4.0...",
    "modified_controls": [
      {
        "control_id": "Requirement 1.2.3",
        "control_name": "Network Security Controls",
        "change_type": "modified",
        "change_description": "Updated to include cloud environments",
        "enhancements": ["Added cloud-specific requirements"],
        "related_controls": ["Requirement 1.2.4"],
        "sub_policies": []
      }
    ],
    "new_additions": [...],
    "framework_references": [...]
  },
  "modified_sections": [
    {
      "control_id": "Requirement 1.2.3",
      "control_name": "Network Security Controls",
      "section_type": "control",
      "modification_type": "modified",
      "change_description": "Updated to include cloud environments",
      "enhancements": ["Added cloud-specific requirements"],
      "related_controls": ["Requirement 1.2.4"]
    }
  ]
}
```

## Troubleshooting

### Problem: AI analysis returns empty arrays

**Diagnosis Steps:**
1. Check the extracted text snippet:
   ```bash
   python grc/changeManagement/test_ai_analysis.py your-file.pdf
   ```
   Look at the "Text Extraction" section

2. Check if the text mentions specific requirements:
   - For PCI DSS: Look for "Requirement X.X.X"
   - For NIST: Look for control IDs like "AC-2"

3. If text looks good but AI returns empty:
   - Try increasing text extraction limits in `changemanagement.py` line 339:
     ```python
     max_pages: int = 15,  # Increase from 10
     max_chars: int = 15000  # Increase from 12000
     ```
   - Try a more powerful model (gpt-4 instead of gpt-4o-mini)

### Problem: JSON parsing fails

**Diagnosis:**
```bash
python grc/changeManagement/test_ai_analysis.py your-file.pdf
```

Look for the "Response preview" in error messages. This shows what the AI actually returned.

**Common Causes:**
1. AI returned markdown instead of pure JSON
   - The code handles this, but check for edge cases
2. AI included explanatory text before/after JSON
   - Update prompt to be even more explicit about "ONLY JSON"
3. Model incompatibility
   - Some older models don't follow instructions as well

### Problem: Framework not identified

**Diagnosis:**
1. Check AI analysis framework_name:
   ```bash
   python grc/changeManagement/test_ai_analysis.py your-file.pdf | grep "Framework Name"
   ```

2. Check if framework exists in database:
   ```bash
   python manage.py shell
   >>> from grc.models import Framework
   >>> Framework.objects.filter(FrameworkName__icontains='PCI').values_list('FrameworkName', flat=True)
   ```

**Solution:**
- Add framework to database if missing
- Update `identify_framework()` patterns in `changemanagement.py` line 597
- Check fuzzy matching threshold (currently 0.7)

## Performance Notes

- **Text Extraction**: ~1-2 seconds per PDF
- **AI Analysis**: ~5-15 seconds depending on model and text size
- **S3 Upload**: ~2-5 seconds depending on file size
- **Total Processing**: ~10-25 seconds per PDF

## Cost Considerations

- **gpt-4o-mini**: ~$0.01-0.03 per PDF (recommended)
- **gpt-4**: ~$0.10-0.30 per PDF (more accurate but expensive)

For batch processing 100 PDFs:
- gpt-4o-mini: ~$1-3
- gpt-4: ~$10-30

## Next Steps

After testing:
1. Review the extracted data quality
2. Adjust prompt if needed for your specific frameworks
3. Test with various framework documents
4. Consider implementing caching to avoid re-processing
5. Set up automated testing in CI/CD

