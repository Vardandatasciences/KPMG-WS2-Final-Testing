# Quick Start Guide - AI Analysis Pipeline

Get started with the AI Analysis Pipeline in 5 minutes!

## Prerequisites

1. **Python 3.8+** installed
2. **OpenAI API Key** 
3. **Django environment** configured

## Step 1: Install Dependencies

```bash
pip install django pandas openpyxl python-dotenv langchain-openai PyMuPDF pdfminer.six
```

## Step 2: Configure API Key

Add your OpenAI API key to Django settings:

**Option A: Environment variable**
```bash
# Windows
set OPENAI_API_KEY=your_api_key_here

# Linux/Mac
export OPENAI_API_KEY=your_api_key_here
```

**Option B: .env file**
Create a `.env` file in the backend directory:
```
OPENAI_API_KEY=your_api_key_here
```

## Step 3: Place Your PDF

Put your framework PDF in the `data/` folder:
```
changeManagement/
  └── data/
      └── your_framework.pdf
```

## Step 4: Run the Pipeline

**Windows:**
```batch
cd changeManagement
run_pipeline.bat
```

**Linux/Mac:**
```bash
cd changeManagement
python ai_analysis.py --pdf-path data/your_framework.pdf
```

**Python Script:**
```python
from ai_analysis import process_framework_pdf

result = process_framework_pdf("data/your_framework.pdf")
print(f"Success: {result['success']}")
print(f"Output: {result['output_file']}")
```

## Step 5: Check Results

Your results will be in:
```
changeManagement/output/{pdf_name}_{timestamp}/
```

The main output file is:
```
{pdf_name}_complete_hierarchy.json
```

## Example Output Structure

```json
{
  "metadata": {
    "total_sections": 50,
    "total_policies": 150,
    "total_subpolicies": 450,
    "total_compliances": 1350
  },
  "framework": {
    "framework_name": "...",
    "current_version": "..."
  },
  "sections": [
    {
      "section_title": "...",
      "policies": [
        {
          "policy_id": "...",
          "policy_title": "...",
          "subpolicies": [
            {
              "subpolicy_id": "...",
              "subpolicy_title": "...",
              "compliances": [...]
            }
          ]
        }
      ]
    }
  ]
}
```

## Troubleshooting

### "OPENAI_API_KEY not found"
- Set the API key in Django settings or .env file
- Restart Django server after adding the key

### "PDF file not found"
- Check the path to your PDF file
- Ensure the file is in the data/ folder
- Use forward slashes in paths (even on Windows)

### "Import errors"
- Run from the changeManagement directory
- Ensure Django is properly configured
- Install all required dependencies

### "No items in index"
- Your PDF may not have a table of contents
- Try a different PDF with a clear TOC/Index

## Processing Time

- **Small PDFs (< 50 pages)**: 5-15 minutes
- **Medium PDFs (50-200 pages)**: 15-60 minutes
- **Large PDFs (> 200 pages)**: 1-3 hours

## API Costs

Typical costs per document:
- **Small documents**: $0.50 - $2
- **Medium documents**: $2 - $5
- **Large documents**: $5 - $15

## Next Steps

1. Review the generated JSON file
2. Import into your GRC system
3. Process additional framework PDFs
4. Customize the pipeline for your needs

## Support

For detailed documentation, see `README.md`

For examples, see `example_usage.py`

