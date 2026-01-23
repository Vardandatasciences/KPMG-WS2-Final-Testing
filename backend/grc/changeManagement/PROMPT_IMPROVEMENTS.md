# AI Prompt Improvements for Change Management

## Overview
This document describes the improvements made to the AI analysis prompt and parsing logic in the Change Management system to ensure structured JSON extraction from framework PDFs.

## Changes Made

### 1. Enhanced Text Extraction (Lines 339-366)
- **Increased text extraction**: Changed from 5 pages / 6000 chars to **10 pages / 12000 chars**
- **Reason**: PCI DSS and similar documents often have detailed change information spread across multiple pages
- More text = better AI analysis and more accurate control extraction

### 2. Improved AI Prompt (Lines 380-468)
The prompt was completely rewritten to be more comprehensive and framework-agnostic:

#### Key Improvements:
- **Clearer Instructions**: Added specific guidelines for different framework types
  - PCI DSS: Look for "Requirement X.X.X" patterns
  - NIST: Look for control IDs like "AC-2", "SI-7"
  - ISO: Look for "A.X.X" or clause numbers

- **More Specific Extraction Requirements**:
  - Extract EACH modified requirement/control individually
  - Include identifiers, names, and detailed change descriptions
  - Capture sub-requirements and sub-policies
  - Extract new additions with scope and purpose
  - Identify deprecated/removed items
  - Capture cross-framework references

- **Emphasized Detail Extraction**:
  ```
  "Extract SPECIFIC details, not generic summaries"
  "If a document says 'Requirement 1.2.3 was updated to clarify X', extract that as a modified control"
  "If it says '15 requirements were added', try to list them individually"
  ```

- **Stricter Output Requirements**:
  - Respond ONLY with valid JSON (no markdown, no explanations)
  - Do NOT return empty arrays if changes are mentioned
  - Extract as much detail as possible

### 3. Enhanced Error Handling (Lines 498-555)
- **Better API Error Handling**: Individual try-catch blocks for each OpenAI API method
- **Detailed Error Messages**: Print and log specific error types
- **Request Tracking**: Log when requests are sent to OpenAI
- **Debug Information**: Keep original response for debugging failed JSON parsing

### 4. Improved Response Validation (Lines 555-591)
- **Comprehensive Structure Validation**: Ensure all expected fields exist
  - `modified_controls`: Array of modified controls
  - `new_additions`: Array of new controls/requirements
  - `framework_references`: Array of framework cross-references
  - `summary`: Summary text
  - `confidence`: Confidence score

- **Type Checking**: Ensure all fields have the correct types
- **Default Values**: Provide sensible defaults for missing fields
- **Extraction Summary**: Log what was extracted (counts of controls, additions, references)

### 5. Better Process Logging (Lines 807-813)
- **Status Messages**: Clear indication of AI analysis status
  - When AI is enabled vs disabled
  - When analysis succeeds vs fails
  - Framework identification from AI
  - Fallback to filename-based detection

## Expected JSON Structure

### Input: PCI DSS Summary of Changes PDF
The improved prompt should now extract:

```json
{
  "framework_name": "PCI DSS v4.0",
  "probable_aliases": ["Payment Card Industry Data Security Standard", "PCI-DSS"],
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
  "new_additions": [
    {
      "control_id": "Requirement 6.4.3",
      "control_name": "Secure Software Development",
      "scope": "Applies to all custom software",
      "purpose": "Enhance application security",
      "requirements": ["Code review", "Security testing"]
    }
  ],
  "framework_references": [
    {
      "referenced_framework": "NIST Cybersecurity Framework",
      "reference_type": "alignment",
      "description": "Aligned with NIST CSF categories"
    }
  ]
}
```

### Input: NIST SP 800-53 Changes PDF
Similar structure but with NIST-specific control IDs:

```json
{
  "framework_name": "NIST SP 800-53 Release 5.2.0",
  "probable_aliases": ["NIST Special Publication 800-53"],
  "confidence": 0.95,
  "summary": "NIST SP 800-53 Release 5.2.0 introduces new controls...",
  "modified_controls": [
    {
      "control_id": "SI-02",
      "control_name": "Flaw Remediation",
      "change_type": "modified",
      "change_description": "Updated discussion to address flaw remediation testing",
      "enhancements": [],
      "related_controls": ["SI-02(05)", "SI-02(07)"],
      "sub_policies": []
    }
  ],
  "new_additions": [
    {
      "control_id": "SA-24",
      "control_name": "Design for Cyber Resiliency",
      "scope": "System design processes",
      "purpose": "Enhance resilience against cyber threats",
      "requirements": []
    }
  ],
  "framework_references": [
    {
      "referenced_framework": "NIST SP 800-53A",
      "reference_type": "alignment",
      "description": "Includes updated assessment procedures"
    }
  ]
}
```

## Testing the Changes

### 1. Test with Existing PDFs
```bash
cd backend
python grc/changeManagement/test_system.py
```

This will run all tests including PDF processing with AI analysis.

### 2. Test Specific File
```bash
cd backend
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.changeManagement.changemanagement import process_specific_file

# Process a specific PDF
result = process_specific_file('PCI-DSS-v3-2-1-to-v4-0-Summary-of-Changes-r1.pdf')
print('AI Analysis:', result.get('ai_analysis'))
print('Modified Sections:', result.get('amendment_info', {}).get('modified_sections'))
"
```

### 3. Check Logs
Watch for these messages in the output:
- ✅ `AI analysis successful - extracted structured data`
- 📊 `AI extracted: X modified controls, Y new additions, Z framework references`
- ✅ `AI analysis completed - Framework: <name>`

### 4. Check for Issues
Watch for these warning messages:
- ⚠️ `AI analysis disabled - using fallback detection`
- ⚠️ `AI analysis returned no results - using filename-based detection`
- ❌ `OpenAI API error: <details>`
- ⚠️ `AI analysis JSON parsing failed: <error>`

## Troubleshooting

### Problem: AI analysis returns null
**Possible causes:**
1. OpenAI API key not configured in settings
2. OpenAI API call failing (check error messages)
3. PDF text extraction failing (check PDF readability)
4. JSON parsing error (check response preview in logs)

**Solution:**
- Check `OPENAI_API_KEY` in Django settings
- Check OpenAI service status
- Test PDF text extraction manually
- Review OpenAI response format

### Problem: Empty arrays in AI response
**Possible causes:**
1. PDF doesn't contain clear change information
2. Text extraction captured wrong pages
3. AI model couldn't parse the document structure

**Solution:**
- Increase `max_pages` in `_extract_pdf_text_snippet` (currently 10)
- Increase `max_chars` (currently 12000)
- Try a different OpenAI model (e.g., gpt-4 instead of gpt-4o-mini)
- Check if PDF is text-based (not scanned image)

### Problem: Generic fallback data instead of structured data
**Possible causes:**
1. AI analysis failed or returned null
2. Framework not identified from AI analysis

**Solution:**
- Check AI analysis logs for errors
- Verify AI is extracting framework_name correctly
- Check framework matching logic in `identify_framework()`

## Benefits

1. **More Structured Data**: Detailed control-level information instead of generic "framework updated"
2. **Better Framework Detection**: AI-assisted framework identification with fuzzy matching
3. **Richer Metadata**: Includes control IDs, change types, enhancements, and cross-references
4. **Better Debugging**: Comprehensive logging and error messages
5. **Framework Agnostic**: Works with NIST, PCI DSS, ISO, HIPAA, GDPR, SOX, Basel III, etc.

## Next Steps

1. Test with real PCI DSS v3.2.1 to v4.0 PDF
2. Test with other framework documents (ISO, HIPAA, etc.)
3. Fine-tune prompt if needed based on results
4. Consider adding support for image-based PDFs (OCR)
5. Consider caching AI analysis results to save API costs

