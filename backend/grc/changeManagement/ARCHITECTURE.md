# AI Analysis Pipeline - Architecture Documentation

## Overview

The AI Analysis Pipeline is a comprehensive system for extracting and structuring compliance data from framework PDF documents. It uses a combination of PDF parsing, natural language processing, and AI-powered analysis to generate a complete hierarchy of frameworks, policies, subpolicies, and compliance records.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          INPUT: Framework PDF                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: INDEX EXTRACTION                                                │
│  Module: pdf_index_extractor.py                                          │
│  • Parse PDF table of contents                                           │
│  • Extract section titles and page numbers                               │
│  • Support multiple TOC formats (GRI, NIST, PCI-DSS, etc.)              │
│  Output: {pdf_name}_index.json                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: SECTION EXTRACTION                                              │
│  Module: index_content_extractor.py                                      │
│  • Map page numbers to PDF pages                                         │
│  • Extract text content for each section                                 │
│  • Create hierarchical folder structure                                  │
│  • Save section metadata and content                                     │
│  Output: sections/ directory with content.json files                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: POLICY EXTRACTION (AI-POWERED)                                 │
│  Module: policy_extractor_enhanced.py                                    │
│  • Analyze section content with OpenAI                                   │
│  • Generate policies with comprehensive metadata                         │
│  • Create subpolicies with detailed controls                             │
│  • Categorize and classify policies                                      │
│  Output: policies/all_policies.json                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 4: COMPLIANCE GENERATION (AI-POWERED)                             │
│  Module: compliance_generator.py                                         │
│  • Generate 1-3 compliance records per subpolicy                         │
│  • Create associated risk assessments                                    │
│  • Include mitigation strategies                                         │
│  • Calculate risk exposure ratings                                       │
│  Output: compliance/all_compliances.json                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 5: HIERARCHICAL JSON GENERATION                                    │
│  Module: ai_analysis.py (step5_generate_hierarchical_json)              │
│  • Combine all extracted data                                            │
│  • Build complete hierarchy                                              │
│  • Add metadata and statistics                                           │
│  Output: {pdf_name}_complete_hierarchy.json                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              OUTPUT: Complete Hierarchical JSON                          │
│  Framework → Sections → Policies → Subpolicies → Compliances           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. FrameworkProcessor Class

**Location**: `ai_analysis.py`

**Responsibilities**:
- Orchestrate the entire pipeline
- Manage state and progress tracking
- Handle errors and logging
- Coordinate between modules

**Key Methods**:
- `__init__()`: Initialize processor with configuration
- `step1_extract_index()`: Run index extraction
- `step2_extract_sections()`: Run section extraction
- `step3_extract_policies()`: Run policy extraction
- `step4_generate_compliance()`: Run compliance generation
- `step5_generate_hierarchical_json()`: Generate final output
- `process()`: Run complete pipeline

### 2. PDF Index Extractor

**Location**: `backend/grc/routes/uploadNist/pdf_index_extractor.py`

**Key Functions**:
- `extract_and_save_index()`: Main entry point
- `load_pages_with_positions_pymupdf()`: Parse PDF with PyMuPDF
- `find_toc_start_pages()`: Locate table of contents
- `parse_toc_from_pages()`: Extract TOC entries
- `infer_levels_from_indents()`: Determine hierarchy levels

**Supported Formats**:
- Standard TOC with dots: "Title .......... 123"
- Right-aligned page numbers: "Title           123"
- GRI format: "GRI 1: Foundation 2021    45"
- Roman numeral pages: "Preface    iv"

### 3. Index Content Extractor

**Location**: `backend/grc/routes/uploadNist/index_content_extractor.py`

**Key Functions**:
- `process_pdf_sections()`: Main entry point
- `detect_page_offset()`: Map printed pages to PDF pages
- `assign_start_pages()`: Determine section start pages
- `compute_ranges_hierarchical()`: Calculate section page ranges
- `extract_section_text()`: Extract text with smart cropping
- `extract_pdf_pages()`: Save section as separate PDF

**Features**:
- Automatic page offset detection
- Hierarchical section organization
- Smart text extraction (removes TOC content)
- PDF page extraction for each section

### 4. Policy Extractor Enhanced

**Location**: `backend/grc/routes/uploadNist/policy_extractor_enhanced.py`

**Key Class**: `EnhancedPolicyExtractor`

**Key Methods**:
- `detect_framework_info()`: Auto-detect framework type
- `analyze_content_for_policies_enhanced()`: AI analysis with OpenAI
- `categorize_policy_comprehensive()`: Multi-level categorization
- `generate_comprehensive_scope()`: Generate scope statements
- `generate_comprehensive_objective()`: Generate objectives
- `generate_structured_identifiers()`: Create policy IDs

**Policy Metadata Generated**:
- policy_id, policy_title, policy_description
- policy_text, scope, objective
- policy_type, policy_category, policy_subcategory
- subpolicies with controls

**AI Model**: GPT-4o-mini (configurable)

**Frameworks Detected**:
- NIST SP 800-53
- NIST Cybersecurity Framework (CSF)
- PCI DSS
- GRI Standards
- TCFD
- HIPAA
- Generic frameworks

### 5. Compliance Generator

**Location**: `backend/grc/routes/uploadNist/compliance_generator.py`

**Key Functions**:
- `generate_compliance_for_single_subpolicy()`: Generate compliance for one subpolicy
- `setup_llm_chain()`: Initialize LangChain with OpenAI
- `process_excel_data()`: Batch process subpolicies

**Compliance Fields Generated**:
- Identifier, ComplianceTitle, ComplianceItemDescription
- ComplianceType, Scope, Objective
- Criticality, Impact, Probability
- MaturityLevel, Status, Applicability
- Associated risk details

**Risk Fields Generated**:
- RiskTitle, RiskDescription
- RiskLikelihood, RiskImpact, RiskExposureRating
- RiskPriority, RiskMitigation
- Category, RiskType, BusinessImpact

**AI Model**: GPT-3.5-turbo (for cost efficiency)

## Data Flow

### Input Data
```
PDF File
└── Binary PDF content
    └── Table of contents
    └── Section content
```

### Intermediate Data

**Step 1 Output** (`_index.json`):
```json
{
  "source_pdf": "path/to/file.pdf",
  "extraction_method": "toc_text_with_positions",
  "items": [
    {
      "level": 1,
      "title": "Section Title",
      "page_label": "10",
      "page_number": 10,
      "source_page": 5
    }
  ]
}
```

**Step 2 Output** (`sections/*/content.json`):
```json
{
  "name": "Section Title",
  "level": 1,
  "start_page": 10,
  "end_page": 15,
  "printed_page": 10,
  "content": "Extracted text content..."
}
```

**Step 3 Output** (`policies/all_policies.json`):
```json
[
  {
    "section_info": {...},
    "analysis": {
      "framework_info": {...},
      "policies": [
        {
          "policy_id": "NIST-800-53-SEC-001",
          "policy_title": "...",
          "subpolicies": [...]
        }
      ]
    }
  }
]
```

**Step 4 Output** (`compliance/all_compliances.json`):
```json
[
  {
    "Identifier": "COMP-001",
    "ComplianceTitle": "...",
    "SubPolicyId": "NIST-800-53-SEC-001.01",
    "risk_details": {...},
    "section_info": {...},
    "policy_info": {...}
  }
]
```

### Final Output

**Hierarchical JSON** (`_complete_hierarchy.json`):
```json
{
  "metadata": {
    "source_pdf": "...",
    "processing_timestamp": "...",
    "total_sections": 50,
    "total_policies": 150,
    "total_subpolicies": 450,
    "total_compliances": 1350
  },
  "framework": {
    "framework_name": "...",
    "current_version": "...",
    "framework_description": "..."
  },
  "sections": [
    {
      "section_title": "...",
      "policies": [
        {
          "policy_id": "...",
          "subpolicies": [
            {
              "subpolicy_id": "...",
              "compliances": [...]
            }
          ]
        }
      ]
    }
  ]
}
```

## State Management

**State File**: `changeManagement/output/state.json`

**State Structure**:
```json
{
  "step1_extract_index": {
    "status": "completed",
    "timestamp": "2025-11-05T14:30:22",
    "data": {
      "index_file": "...",
      "items_count": 50
    }
  },
  "step2_extract_sections": {...},
  "step3_extract_policies": {...},
  "step4_generate_compliance": {...},
  "step5_generate_hierarchical_json": {...}
}
```

## Error Handling

### Error Propagation
1. Errors in any step stop the pipeline
2. Error details are logged to console
3. Error information saved to state file
4. Stack traces provided for debugging

### Recovery
- State file tracks completed steps
- Future enhancement: Resume from last successful step
- Intermediate results saved at checkpoints

## Performance Optimization

### API Rate Limiting
- Built-in delays between API calls
- Longer breaks every 10 calls (2 seconds)
- Extended breaks every 50 calls (10 seconds)
- Configurable in code

### Content Chunking
- Large sections split into 8000-character chunks
- Each chunk processed separately
- Results merged intelligently

### Caching
- Intermediate results saved to disk
- Temporary files every 5 processed sections
- Final results always saved

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # Optional, defaults in settings
```

### Django Settings
```python
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = 'gpt-4o-mini'
```

### Runtime Configuration
```python
processor = FrameworkProcessor(
    pdf_path="data/file.pdf",
    base_output_dir="output",
    verbose=True
)
```

## Extension Points

### Adding New Framework Types
Modify `detect_framework_info()` in `policy_extractor_enhanced.py`:
```python
elif "FRAMEWORK_NAME" in dir_name:
    return {
        "framework_name": "...",
        "current_version": "...",
        "identifier_prefix": "..."
    }
```

### Custom Policy Categorization
Modify `categorize_policy_comprehensive()` in `policy_extractor_enhanced.py`

### Custom Compliance Fields
Modify `generate_compliance_for_single_subpolicy()` in `compliance_generator.py`

### Custom Output Format
Modify `step5_generate_hierarchical_json()` in `ai_analysis.py`

## Testing

### Unit Tests
- Individual module functions
- PDF parsing accuracy
- JSON structure validation

### Integration Tests
- Full pipeline execution
- Error handling
- State management

### Validation
Run `test_setup.py` to validate:
- Python version
- Dependencies installed
- Django configured
- OpenAI API accessible
- Required modules present

## Deployment

### Local Development
```bash
python ai_analysis.py --pdf-path data/file.pdf
```

### Production Deployment
1. Install dependencies in virtual environment
2. Configure Django settings
3. Set up API keys securely
4. Run with appropriate resource limits
5. Monitor API usage and costs

## Monitoring

### Progress Tracking
- Console output shows current step
- Progress bars for batch operations
- Statistics at each step completion

### Logging
- All operations logged to console
- Error details with stack traces
- State file tracks all steps

### Cost Monitoring
- Track API calls made
- Estimate costs based on tokens used
- Typical: $1-10 per document

## Security Considerations

### API Key Management
- Never commit API keys to version control
- Use environment variables or .env files
- Rotate keys regularly

### PDF Processing
- Validate PDF file integrity
- Handle malformed PDFs gracefully
- Sanitize extracted text

### Data Privacy
- Be aware of sensitive data in PDFs
- Consider data residency for API calls
- Review OpenAI's data policies

## Future Enhancements

### Planned Features
1. Resume from checkpoint
2. Parallel processing
3. Custom AI prompts
4. Export to database
5. Web UI for monitoring
6. Batch processing optimization

### Under Consideration
- Support for non-English PDFs
- Custom policy templates
- Integration with GRC systems
- Real-time progress tracking
- Cost optimization strategies

## Support and Maintenance

### Updating Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Troubleshooting
1. Check `test_setup.py` results
2. Review state.json for errors
3. Check console output for details
4. Verify API key and credits

### Contributing
- Follow existing code style
- Add tests for new features
- Update documentation
- Test with multiple PDF types

