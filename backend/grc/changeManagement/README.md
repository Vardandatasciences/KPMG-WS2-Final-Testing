# Change Management System

## Overview
The Change Management System automatically monitors, processes, and tracks amendments to compliance framework documents. When new or updated framework PDFs are downloaded via Selenium, the system automatically:

1. **Detects** new PDF files in the `data/` directory
2. **Uploads** them to S3 bucket with the original filename
3. **Extracts** amendment information from the PDF
4. **Updates** the Framework's `Amendment` column in the database with structured JSON data

## Architecture

### Components

#### Backend (`changemanagement.py`)
- **ChangeManagementService**: Core service class handling all change management operations
- **API Endpoints**: REST API endpoints for frontend integration
- **S3 Integration**: Uploads framework documents to S3 using existing `s3_fucntions.py`
- **Database Updates**: Updates Framework table with amendment tracking data

#### Frontend
- **changeManagementService.js**: Frontend service for API calls
- **HomeView.vue Integration**: Automatic initialization on user login

#### Selenium Integration (`selimium.py`)
- Downloads framework PDFs when updates are detected
- Saves to `data/` directory with timestamped filenames

## How It Works

### 1. File Detection & Download
```
Selenium Script (selimium.py)
    ↓
Downloads PDF to data/
    ↓
Saves as: SP800-53_YYYYMMDD_HHMMSS.pdf
```

### 2. Automatic Processing on Login
```
User Logs In (HomeView.vue)
    ↓
changeManagementService.initializeOnLogin()
    ↓
Checks data/ directory for PDFs
    ↓
If PDFs found → scan_and_process_changes()
```

### 3. PDF Processing Flow
```
scan_and_process_changes()
    ↓
For each PDF:
    1. Calculate file hash (check if already processed)
    2. Identify framework (NIST, PCI, ISO, etc.)
    3. Upload to S3 with original filename
    4. Extract PDF metadata & content
    5. Generate amendment information
    6. Update Framework.Amendment column
    7. Mark as processed (save hash)
```

### 4. Framework Amendment JSON Structure
```json
{
  "amendment_id": 1,
  "amendment_name": "NIST SP 800-53 - Update 2024-11-12",
  "modified_sections": [
    {
      "section_type": "policy",
      "section_name": "NIST SP 800-53 Controls",
      "modification_type": "update",
      "description": "Framework controls updated"
    }
  ],
  "content_summary": "Document size: 5.8 MB | Total pages: 400 | Title: NIST SP 800-53",
  "s3_url": "https://s3.amazonaws.com/bucket/SP800-53_20241112_112130.pdf",
  "s3_key": "changemanagement/user/SP800-53_20241112_112130.pdf",
  "stored_name": "SP800-53_20241112_112130.pdf",
  "file_size": 6078463,
  "uploaded_date": "2024-11-12T11:21:30.123456",
  "file_metadata": {
    "num_pages": 400,
    "title": "NIST SP 800-53 Rev 5",
    "author": "NIST",
    "creation_date": "2024-11-12"
  }
}
```

## API Endpoints

### POST /api/change-management/scan/
Trigger a scan and process operation for PDFs in data/ directory

**Request:**
```json
{
  "user_id": "123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_time": "2024-11-12T11:21:30.123456",
    "files_found": 1,
    "files_processed": 1,
    "files_skipped": 0,
    "files_failed": 0,
    "processed_files": [...]
  },
  "message": "Scan completed. Processed: 1, Skipped: 0, Failed: 0"
}
```

### POST /api/change-management/process-file/{file_name}/
Process a specific PDF file

**Request:**
```json
{
  "user_id": "123"
}
```

### GET /api/change-management/framework-amendments/{framework_id}/
Get all amendments for a specific framework

**Response:**
```json
{
  "success": true,
  "data": {
    "framework_id": 1,
    "framework_name": "NIST SP 800-53",
    "amendments": [...]
  }
}
```

### GET /api/change-management/status/
Get change management system status

**Response:**
```json
{
  "success": true,
  "data": {
    "service_status": "operational",
    "data_directory": "/path/to/data",
    "pdf_files_count": 1,
    "processed_files_count": 5,
    "s3_configured": true
  }
}
```

## Database Schema

### Framework Table - Amendment Column
```sql
Amendment JSON NULL DEFAULT NULL
```

Type: `JSONField` - Array of amendment objects

## Configuration

### Settings (from settings.py)
- Database credentials: Automatically loaded from Django settings
- S3 configuration: Uses existing S3 service configuration

### Directories
- **Data Directory**: `backend/grc/changeManagement/data/`
  - Contains downloaded PDFs
  - `state.json` - Selenium tracking
  - `processed_files.json` - Processed file hashes

## File Naming Convention

### Downloaded Files (Selenium)
```
SP800-53_YYYYMMDD_HHMMSS.pdf
PCI_DSS_YYYYMMDD_HHMMSS.pdf
```

### S3 Storage
```
changemanagement/userid/original_filename_userid_module_timestamp.ext
```
Example: `changemanagement/123/SP800-53_123_changemanagement_20241112_112130.pdf`

## Framework Detection

The system automatically identifies frameworks based on filename patterns:

| Pattern | Framework |
|---------|-----------|
| sp800-53, nist, sp800 | NIST SP 800-53 |
| pci | PCI DSS |
| iso27001, iso | ISO 27001 |
| hipaa | HIPAA |
| gdpr | GDPR |
| sox | SOX |

## Security

- All API endpoints require authentication
- S3 uploads use secure credentials from settings
- File hash tracking prevents duplicate processing
- CSRF protection enabled

## Monitoring & Logging

All operations are logged with emoji indicators:
- 🔍 Scanning/Detection
- 📤 Upload operations
- ✅ Success
- ❌ Errors
- ⚠️ Warnings
- 📋 Information

## Troubleshooting

### PDFs Not Being Processed
1. Check if Selenium downloaded to correct directory
2. Verify data/ directory permissions
3. Check `processed_files.json` - may be already processed

### Framework Not Identified
1. Verify filename contains framework identifier (nist, pci, iso, etc.)
2. Ensure framework exists in database
3. Check framework name matches expected patterns

### S3 Upload Failures
1. Verify S3 credentials in settings.py
2. Check S3 microservice is running (http://15.207.1.40:3000)
3. Review S3 service logs

### Database Update Failures
1. Check database connection
2. Verify Framework model has Amendment column
3. Review Django logs for errors

## Development & Testing

### Manual Testing
```bash
cd backend/grc/changeManagement
python changemanagement.py
```

### Add Test PDF
1. Copy PDF to `data/` directory
2. Refresh homepage (will trigger scan)
3. Or call API directly: `POST /api/change-management/scan/`

### View Amendments
```python
from grc.models import Framework
framework = Framework.objects.get(FrameworkId=1)
print(framework.Amendment)
```

## Dependencies

Required Python packages:
- `PyPDF2` - PDF processing
- `django` - Web framework
- `requests` - HTTP client
- `selenium` - Web automation
- `mysql-connector-python` - Database

## Future Enhancements

1. **AI-Powered Change Detection**: Use NLP to compare PDFs and identify specific changes
2. **Email Notifications**: Send alerts when amendments are processed
3. **Scheduled Scans**: Run Selenium + processing on schedule
4. **Version Comparison**: Visual diff between framework versions
5. **Approval Workflow**: Require approval before publishing amendments

## Support

For issues or questions, contact the development team or refer to:
- Main application README
- Django documentation
- S3 service documentation
