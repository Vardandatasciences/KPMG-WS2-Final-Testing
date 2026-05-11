# AI-Powered KPI Generator

Automated KPI generation system for GRC frameworks using database analysis, S3 evidence processing, and Ollama LLM.

## 📁 Module Structure

```
grc/AiKpis/
├── __init__.py              # Package initialization
├── generateFrameworkKpi.py           # Main entry point (CLI)
├── config.py                # Configuration and settings
├── database.py              # Database operations (MySQL)
├── s3_handler.py            # S3 document handling and text extraction
├── evidence.py              # Evidence indexing and S3 attachment
├── module_summaries.py      # Module summary creation and chunking
├── ollama_client.py         # Ollama API client for KPI generation
├── kpi_validation.py        # KPI validation, alignment, and deduplication
├── formula_evaluator.py     # Formula evaluation against dataframes
├── synthetic_data.py        # Synthetic dataset generation
├── kpi_generator.py         # Main KPI generation pipeline
└── README.md                # This file
```

## 🚀 Quick Start

### Installation

```bash
# Install required dependencies
pip install -r backend/grc/AiKpis/requirements.txt
```

### Basic Usage

```bash
# Generate KPIs for default framework (ID: 336)
python -m backend.grc.AiKpis.generateFrameworkKpi

# Generate KPIs for specific framework
python -m backend.grc.AiKpis.generateFrameworkKpi --framework-id 340

# Generate KPIs for specific modules only
python -m backend.grc.AiKpis.generateFrameworkKpi --modules audit,policies

# Limit S3 document processing
python -m backend.grc.AiKpis.generateFrameworkKpi --max-s3-docs 10
```

## 📋 Module Descriptions

### 1. **config.py**
- Central configuration file
- Database credentials
- S3 configuration
- Ollama settings
- Feature flags for optional dependencies

### 2. **database.py**
- Database connection management
- Framework metadata retrieval
- Schema information extraction
- Data fetching from all tables
- KPI persistence to database

### 3. **s3_handler.py**
- S3 document retrieval and caching
- Text extraction from PDF, TXT, DOC, DOCX, Excel
- Dataframe loading from CSV/Excel
- Document metadata management

### 4. **evidence.py**
- Evidence indexing for tables and S3 documents
- S3 evidence attachment to module summaries
- Keyword extraction and semantic matching
- Chunk caching for performance

### 5. **module_summaries.py**
- Per-module JSON summary creation
- Intelligent data chunking for LLM context
- Module-specific table grouping

### 6. **ollama_client.py**
- Ollama API communication
- JSON extraction and repair
- Prompt engineering for KPI generation
- Response validation

### 7. **kpi_validation.py**
- Formula validation against schemas
- KPI alignment with evidence
- Duplicate detection and removal
- Schema enforcement

### 8. **formula_evaluator.py**
- Pandas-style formula evaluation
- Dataframe-based computation
- Type inference and conversion
- Value population for KPIs

### 9. **synthetic_data.py**
- LLM-based synthetic dataset generation
- PDF evidence document creation
- S3 upload via microservice
- Dataframe caching

### 10. **kpi_generator.py**
- Main orchestration pipeline
- Module summary processing
- KPI generation workflow
- Single KPI refresh functionality

### 11. **generateFrameworkKpi.py**
- CLI entry point
- Argument parsing
- Error handling and reporting

## 🔄 Workflow

```
1. Connect to Database
   ↓
2. Fetch Framework Info
   ↓
3. Retrieve S3 Documents (with caching)
   ↓
4. Extract Framework Data (policies, risks, etc.)
   ↓
5. Get Database Schema
   ↓
6. Fetch Other Tables Data
   ↓
7. Create Module Summaries (JSON files)
   ↓
8. Test Ollama Connection
   ↓
9. Generate KPIs per Module
   ├─ Attach S3 Evidence
   ├─ Chunk Large Data
   ├─ Call Ollama API
   ├─ Validate Formulas
   └─ Generate Synthetic Data (if needed)
   ↓
10. Deduplicate KPIs
    ↓
11. Populate KPI Values
    ↓
12. Write to Database
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Database
DB_CONFIG = {
    'host': 'localhost',
    'database': 'grc2',
    'user': 'root',
    'password': 'your_password'
}

# Ollama
OLLAMA_BASE_URL = "http://13.126.18.17:11434/api"
OLLAMA_MODEL = "llama3.1:8b"

# S3
S3_CONFIG = {
    'aws_access_key_id': 'YOUR_KEY',
    'aws_secret_access_key': 'YOUR_SECRET',
    'region_name': 'ap-south-1'
}

# Framework
FRAMEWORK_ID = 336  # Default framework to process
```

## 📊 Output

- **Database**: KPIs written to `kpis` table
- **JSON Files**: Module summaries in `excel_output_enhanced_NEW/`
- **Cache Files**: S3 document cache, chunk cache
- **Schema Metadata**: Schema metadata JSON files

## 🔧 Dependencies

### Required
- `mysql-connector-python` - Database connectivity
- `pandas` - Data manipulation
- `requests` - HTTP requests to Ollama
- `python-dotenv` - Environment variable management
- `boto3` - AWS S3 access

### Optional
- `PyPDF2` - PDF text extraction
- `openpyxl` - Excel file handling
- `keybert` - Keyword extraction
- `sentence-transformers` - Semantic similarity
- `langchain` - Text splitting
- `fpdf` - PDF generation
- `json-repair` - JSON repair

## 🎯 Key Features

1. **Intelligent Evidence Matching**: Uses KeyBERT and sentence transformers for semantic evidence selection
2. **Caching**: Aggressive caching of S3 documents and chunks for performance
3. **Chunking**: Automatic data chunking to fit LLM context windows
4. **Synthetic Data**: Generates synthetic datasets when real data is missing
5. **Formula Validation**: Validates formulas against actual database schemas
6. **Deduplication**: Removes duplicate KPIs across modules
7. **Modular Design**: Clean separation of concerns for maintainability

## 🐛 Troubleshooting

### Ollama Connection Issues
```bash
# Test Ollama connectivity
curl http://13.126.18.17:11434/api/tags
```

### Database Connection Issues
- Verify credentials in `config.py`
- Check MySQL server is running
- Ensure database exists

### S3 Access Issues
- Verify AWS credentials
- Check bucket permissions
- Ensure bucket exists

### Missing Dependencies
```bash
# Install all optional dependencies
pip install PyPDF2 openpyxl keybert sentence-transformers langchain fpdf json-repair
```

## 📝 Notes

- The system processes one framework at a time
- Module summaries are cached and reused
- S3 documents are cached to avoid re-downloading
- Synthetic data is generated only when needed
- All KPIs are validated before database insertion

## 🔐 Security

- Database credentials should be stored in `.env` file
- AWS credentials should use IAM roles in production
- S3 buckets should have appropriate access policies

## 📄 License

Internal use only - Part of GRC system

