# OCR App - Document Processing & SLA Data Extraction

## Overview

The OCR App provides intelligent document processing with AI-powered data extraction for SLA (Service Level Agreement) documents. It integrates with S3 for storage, uses Tesseract/PyMuPDF for OCR, and leverages LLaMA AI for intelligent data extraction.

## Architecture

```
Frontend (Vue.js) -> Backend API -> OCR Service -> S3 Storage
                                 -> LLaMA AI Extraction
```

### Components

1. **DocumentUploadView** - Handles file upload and orchestrates processing
2. **DocumentProcessingService** - Core OCR and AI extraction logic
3. **S3 Integration** - Secure document storage (via s3.py)
4. **LLaMA Integration** - AI-powered data extraction (via lamma.py)

## Features

- ✅ **Multi-format Support**: PDF, DOC, DOCX, TXT, PNG, JPG, JPEG
- ✅ **S3 Storage**: Automatic upload to S3 with MySQL tracking
- ✅ **OCR Processing**: Text extraction from documents and images
- ✅ **AI Extraction**: LLaMA-powered SLA data extraction
- ✅ **Structured Output**: Automatic mapping to database schema
- ✅ **Confidence Scoring**: Extraction confidence metrics
- ✅ **Error Handling**: Comprehensive error handling and logging

## API Endpoints

### 1. Document Upload & Processing
```
POST /api/ocr/upload/
Content-Type: multipart/form-data

FormData:
- file: <document file>
- title: <optional title>
- description: <optional description>
- category: <optional category>
- department: <optional department>
- doc_type: <optional document type>
- module_id: <optional module ID>

Response:
{
  "success": true,
  "message": "Document uploaded and processed successfully",
  "document": {
    "DocumentId": 123,
    "Title": "SLA Document",
    "OriginalFilename": "sla.pdf",
    "DocumentLink": "https://s3.amazonaws.com/...",
    ...
  },
  "ocr_result": {
    "OcrResultId": 456,
    "OcrText": "extracted text...",
    "OcrConfidence": 92.5,
    "OcrEngine": "PyMuPDF",
    ...
  },
  "extracted_data": {
    "ExtractedDataId": 789,
    "sla_name": "Database Service SLA",
    "vendor_id": "1",
    "contract_id": "1",
    "sla_type": "AVAILABILITY",
    "effective_date": "2024-01-01",
    "expiry_date": "2024-12-31",
    "business_service_impacted": "Database Services",
    "compliance_framework": "ISO 27001",
    "metrics": [
      {
        "metric_name": "Uptime",
        "threshold": 99.9,
        "measurement_unit": "%",
        "frequency": "MONTHLY",
        ...
      }
    ],
    ...
  },
  "upload_info": {
    "success": true,
    "file_info": {
      "url": "https://s3.amazonaws.com/...",
      "s3Key": "user_1/1234567890_sla.pdf",
      ...
    }
  },
  "processing_info": {
    "ocr_success": true,
    "extraction_success": true,
    "extraction_confidence": 0.85
  }
}
```

### 2. Health Check
```
GET /api/ocr/health/

Response:
{
  "status": "healthy",
  "service": "OCR Microservice",
  "version": "1.0.0",
  "components": {
    "database": "connected",
    "s3_service": "connected",
    "ai_service": "available"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Document List
```
GET /api/ocr/documents/

Response:
{
  "success": true,
  "documents": [...],
  "count": 10
}
```

### 4. Document Detail
```
GET /api/ocr/documents/<document_id>/

Response:
{
  "success": true,
  "document": {...},
  "ocr_results": [...],
  "extracted_data": [...]
}
```

## Database Schema

### Documents Table
```sql
- DocumentId (PK)
- Title
- Description
- OriginalFilename
- DocumentLink (S3 URL)
- Category
- Department
- DocType
- ModuleId
- Status
- CreatedBy
- CreatedAt
- UpdatedAt
```

### OCR Results Table
```sql
- OcrResultId (PK)
- DocumentId (FK)
- OcrText
- OcrLanguage
- OcrConfidence
- OcrEngine
- ocr_data (JSON)
- CreatedAt
- UpdatedAt
```

### Extracted Data Table
```sql
- ExtractedDataId (PK)
- DocumentId (FK)
- OcrResultId (FK)
- sla_name
- vendor_id
- contract_id
- sla_type
- effective_date
- expiry_date
- status
- business_service_impacted
- reporting_frequency
- baseline_period
- improvement_targets (JSON)
- penalty_threshold
- credit_threshold
- measurement_methodology
- exclusions
- force_majeure_clauses
- compliance_framework
- audit_requirements
- document_versioning
- compliance_score
- priority
- approval_status
- metrics (JSON)
- raw_extracted_data (JSON)
- extraction_confidence
- extraction_method
- CreatedAt
- UpdatedAt
```

## Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements_ocr.txt
```

Required packages:
- Django==4.2.7
- djangorestframework==3.14.0
- mysqlclient==2.2.0
- Pillow==10.0.1
- pytesseract==0.3.10
- PyMuPDF==1.23.8
- requests==2.31.0
- aiohttp==3.9.1

### 2. Configure Settings

In `vendor_guard_hub/settings.py`:

```python
# Add to INSTALLED_APPS
'ocr_app',

# OCR Configuration
OCR_ENABLED = True
OCR_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
OCR_ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg']
OCR_TESSERACT_CMD = 'tesseract'  # Path to tesseract executable
```

### 3. Configure URLs

In `vendor_guard_hub/urls.py`:

```python
# OCR APIs
path('api/ocr/', include('ocr_app.urls')),
```

### 4. Run Migrations

The OCR app uses the existing database. No additional migrations needed.

### 5. Start the Server

```bash
python manage.py runserver 8000
```

### 6. Test OCR Service

```bash
curl http://localhost:8000/api/ocr/health/
```

## Frontend Integration

### Vue.js Component Usage

```vue
<script setup>
async function handleDocumentUpload() {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('title', file.name)
  formData.append('category', 'SLA')
  
  const response = await fetch('http://localhost:8000/api/ocr/upload/', {
    method: 'POST',
    body: formData
  })
  
  const result = await response.json()
  
  if (result.success && result.extracted_data) {
    // Apply extracted data to form
    formData.sla_name = result.extracted_data.sla_name
    formData.vendor_id = result.extracted_data.vendor_id
    // ... map other fields
  }
}
</script>
```

## Processing Flow

1. **Upload**: User uploads document via frontend
2. **Validation**: Backend validates file size, type
3. **S3 Storage**: Document uploaded to S3, URL stored in database
4. **OCR**: Text extracted using PyMuPDF (PDF) or Tesseract (images)
5. **AI Extraction**: LLaMA processes OCR text and extracts structured data
6. **Database**: Results stored in documents, ocr_results, and extracted_data tables
7. **Response**: Extracted data returned to frontend for form population

## Troubleshooting

### Issue: OCR not working
**Solution**: Check if Tesseract is installed
```bash
# Windows
choco install tesseract

# Mac
brew install tesseract

# Linux
sudo apt-get install tesseract-ocr
```

### Issue: S3 upload failing
**Solution**: Check S3 microservice is running and database connection
```bash
# Test S3 connection
from s3 import create_direct_mysql_client
client = create_direct_mysql_client()
result = client.test_connection()
print(result)
```

### Issue: LLaMA extraction not working
**Solution**: Check Ollama is running
```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Or check EC2 instance
curl http://13.126.18.17:11434/api/tags
```

### Issue: Low extraction confidence
**Solution**: 
- Ensure document is clear and not scanned at low quality
- Check OCR confidence score
- Verify LLaMA model is loaded correctly
- Try with a different document format

## Configuration

### Environment Variables

```bash
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=tprm_integration
DB_PORT=3306

# S3 Microservice
S3_API_URL=http://13.233.147.73:3000

# LLaMA/Ollama
OLLAMA_URL=http://localhost:11434
LLAMA_MODEL_NAME=llama3.2:3b
```

## Performance Optimization

1. **Caching**: OCR results are cached in database
2. **Async Processing**: Uses aiohttp for concurrent operations
3. **Progress Tracking**: Real-time progress updates via frontend
4. **File Size Limits**: 50MB max to prevent memory issues
5. **Timeout Handling**: Adaptive timeouts based on file size

## Security

- ✅ File size validation (50MB max)
- ✅ File type validation
- ✅ Secure S3 storage with access controls
- ✅ CSRF protection disabled for API (uses token-based auth)
- ✅ SQL injection prevention via ORM
- ✅ Input sanitization

## Monitoring & Logging

All operations are logged with structured logging:

```python
logger.info(f"[INFO] Document uploaded: {file_name}")
logger.error(f"[ERROR] OCR failed: {error}")
logger.warning(f"[WARN] Low confidence extraction: {confidence}%")
```

Logs are stored in:
- `backend/logs/django.log`
- `backend/logs/vendor_tprm.log`

## API Testing

Use the included test scripts:

```bash
# Test upload
python -c "from ocr_app.services import document_service; print(document_service.s3_client.test_connection())"

# Test LLaMA
python lamma.py

# Test S3
python s3.py
```

## Maintenance

### Database Cleanup

```sql
-- Remove old OCR results (older than 90 days)
DELETE FROM ocr_results WHERE CreatedAt < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- Remove documents without extracted data
DELETE FROM documents WHERE Status = 'QUARANTINED' AND CreatedAt < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### Performance Monitoring

```sql
-- Check extraction success rate
SELECT 
  COUNT(*) as total_documents,
  SUM(CASE WHEN Status = 'ACTIVE' THEN 1 ELSE 0 END) as successful,
  AVG(ocr_confidence) as avg_confidence
FROM documents d
JOIN ocr_results o ON d.DocumentId = o.DocumentId
WHERE d.CreatedAt > DATE_SUB(NOW(), INTERVAL 7 DAY);
```

## Support

For issues or questions:
1. Check logs in `backend/logs/`
2. Test health endpoint: `/api/ocr/health/`
3. Verify S3 and LLaMA services are running
4. Check database connectivity

## Future Enhancements

- [ ] Multi-language OCR support
- [ ] Batch document processing
- [ ] Document versioning and comparison
- [ ] Enhanced AI extraction with custom models
- [ ] Real-time progress websockets
- [ ] Document annotation and markup
- [ ] Advanced search and filtering
- [ ] Export extracted data in multiple formats

