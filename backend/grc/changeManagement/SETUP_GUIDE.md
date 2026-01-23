# Change Management System - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd backend/grc/changeManagement
pip install -r requirements.txt
```

Required packages:
- PyPDF2 (PDF processing)
- Django (already installed)
- Selenium (for PDF downloads)

### 2. Database Setup

The `Amendment` column already exists in the Framework model as a JSONField. No migration needed.

To verify:
```python
from grc.models import Framework
# Should have Amendment field
```

### 3. Directory Structure

Ensure the following directory structure exists:

```
backend/grc/changeManagement/
├── __init__.py
├── changemanagement.py       # Main service code
├── selimium.py               # Selenium PDF downloader
├── requirements.txt
├── README.md
├── SETUP_GUIDE.md
└── data/                     # PDF download directory
    ├── state.json           # Selenium state tracking
    ├── processed_files.json # Processed files tracking
    └── *.pdf                # Downloaded framework PDFs
```

### 4. Configuration

All configuration is automatic:
- **Database**: Uses Django settings.py credentials
- **S3**: Uses existing S3 service (http://15.207.1.40:3000)
- **Data Directory**: Automatically created at `data/`

No additional configuration needed!

## Usage

### Automatic Mode (Recommended)

The system runs automatically when users log in:

1. **User logs in** → HomeView.vue loads
2. **System checks** `data/` directory for PDFs
3. **If PDFs found** → Automatically processes them in background
4. **Updates Framework** Amendment column
5. **User sees notification** if new amendments detected

**No manual intervention required!**

### Manual Mode (API)

#### Trigger Manual Scan

Using curl:
```bash
curl -X POST http://localhost:8000/api/change-management/scan/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"user_id": "123"}'
```

Using Python:
```python
import requests

response = requests.post(
    'http://localhost:8000/api/change-management/scan/',
    json={'user_id': '123'},
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)

print(response.json())
```

#### Process Specific File

```bash
curl -X POST http://localhost:8000/api/change-management/process-file/SP800-53_20241112_112130.pdf/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"user_id": "123"}'
```

#### Get Framework Amendments

```bash
curl -X GET http://localhost:8000/api/change-management/framework-amendments/1/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Check System Status

```bash
curl -X GET http://localhost:8000/api/change-management/status/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Command Line Testing

Test the service directly:

```bash
cd backend/grc/changeManagement
python changemanagement.py
```

This will:
1. Scan the `data/` directory
2. Process any PDFs found
3. Print detailed results

## Testing Workflow

### Complete Test Scenario

1. **Download a framework PDF using Selenium**

```bash
cd backend/grc/changeManagement
python selimium.py
```

This downloads NIST SP 800-53 PDF to `data/` directory.

2. **Verify PDF Downloaded**

```bash
ls -la data/*.pdf
```

You should see: `SP800-53_YYYYMMDD_HHMMSS.pdf`

3. **Test Processing**

Option A - Command line:
```bash
python changemanagement.py
```

Option B - API:
```bash
curl -X POST http://localhost:8000/api/change-management/scan/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "system"}'
```

Option C - Login to frontend:
- Just log in to the application
- System automatically checks and processes

4. **Verify Results**

Check database:
```python
from grc.models import Framework

# Find NIST framework
nist = Framework.objects.filter(FrameworkName__icontains='NIST').first()

# View amendments
import json
print(json.dumps(nist.Amendment, indent=2))
```

Expected output:
```json
[
  {
    "amendment_id": 1,
    "amendment_name": "NIST SP 800-53 - Update 2024-11-12",
    "modified_sections": [...],
    "s3_url": "https://...",
    "uploaded_date": "2024-11-12T11:21:30.123456",
    ...
  }
]
```

5. **Verify S3 Upload**

Check S3 bucket for uploaded file:
- File should be at: `changemanagement/[userid]/SP800-53_[timestamp].pdf`
- With original filename preserved

## Frontend Integration

### Viewing Amendments in UI

Add to your framework detail page:

```vue
<template>
  <div class="framework-amendments">
    <h3>Framework Amendments</h3>
    <div v-for="amendment in amendments" :key="amendment.amendment_id">
      <h4>{{ amendment.amendment_name }}</h4>
      <p>{{ amendment.content_summary }}</p>
      <a :href="amendment.s3_url" target="_blank">View Document</a>
      <p>Uploaded: {{ formatDate(amendment.uploaded_date) }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import changeManagementService from '@/services/changeManagementService';

const amendments = ref([]);
const frameworkId = ref(1); // Your framework ID

onMounted(async () => {
  const result = await changeManagementService.getFrameworkAmendments(frameworkId.value);
  if (result.success) {
    amendments.value = result.data.amendments || [];
  }
});

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString();
};
</script>
```

### Trigger Manual Scan from UI

```vue
<template>
  <button @click="scanForChanges">Check for Updates</button>
</template>

<script setup>
import changeManagementService from '@/services/changeManagementService';

const scanForChanges = async () => {
  const userId = localStorage.getItem('userId');
  const result = await changeManagementService.scanForChanges(userId);
  
  if (result.success) {
    alert(`Scan complete! Processed: ${result.data.files_processed}`);
  }
};
</script>
```

## Scheduled Automation

### Set up Cron Job (Linux/Mac)

Run Selenium + Processing daily:

```bash
# Edit crontab
crontab -e

# Add this line (runs at 2 AM daily)
0 2 * * * cd /path/to/backend/grc/changeManagement && python selimium.py && python changemanagement.py >> /var/log/change-management.log 2>&1
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Framework Change Management"
4. Trigger: Daily at 2:00 AM
5. Action: Start a program
6. Program: `python`
7. Arguments: `D:\UI_GRC\backend\grc\changeManagement\selimium.py && python D:\UI_GRC\backend\grc\changeManagement\changemanagement.py`

### Django Management Command (Recommended)

Create a management command for easy scheduling:

```bash
python manage.py scan_framework_changes
```

See the included management command file.

## Monitoring

### Check System Status

```bash
curl http://localhost:8000/api/change-management/status/
```

Response:
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

### View Logs

All operations are logged to console with emoji indicators:

```
🔍 [ChangeManagement] Scanning for framework changes...
📄 Processing file: SP800-53_20241112_112130.pdf
✅ Identified framework: NIST SP 800-53 (ID: 1)
📤 Uploading SP800-53_20241112_112130.pdf to S3...
✅ Successfully uploaded to S3
✅ Successfully updated framework NIST SP 800-53 with new amendment
✅ Successfully processed SP800-53_20241112_112130.pdf
```

### Check Processed Files

```bash
cat backend/grc/changeManagement/data/processed_files.json
```

Contains hashes of all processed files to prevent duplicates.

## Troubleshooting

### Issue: PDFs not being processed

**Check 1: Are PDFs in the correct directory?**
```bash
ls backend/grc/changeManagement/data/*.pdf
```

**Check 2: Is the framework in the database?**
```python
from grc.models import Framework
frameworks = Framework.objects.all()
for f in frameworks:
    print(f.FrameworkId, f.FrameworkName)
```

**Check 3: Already processed?**
```bash
cat backend/grc/changeManagement/data/processed_files.json
```

### Issue: S3 upload failing

**Check S3 microservice:**
```bash
curl http://15.207.1.40:3000/health
```

Should return service health status.

**Check S3 credentials in settings.py:**
- Verify AWS credentials are configured
- Check S3 microservice URL

### Issue: Framework not identified

**Solution: Update filename pattern matching**

Edit `changemanagement.py`, function `identify_framework()`:

```python
framework_patterns = {
    'your-custom-pattern': ['Framework Name in DB'],
    # Add more patterns as needed
}
```

### Issue: Database update failing

**Check Amendment column exists:**
```bash
python manage.py dbshell
DESCRIBE frameworks;
```

Should show `Amendment` column of type `JSON`.

## Security Considerations

1. **File Upload Security**: Only PDFs from trusted sources (Selenium) are processed
2. **S3 Access**: Uses secure credentials from settings.py
3. **API Authentication**: All endpoints require valid JWT token
4. **File Hash Verification**: Prevents duplicate processing
5. **SQL Injection**: Uses Django ORM (safe by default)

## Performance Optimization

### Large PDF Files

For PDFs > 50MB:
- Increase timeout in S3 upload: Edit `s3_fucntions.py`
- Increase Django upload limit in settings.py

### Many PDFs

For bulk processing:
- Process in batches
- Use background task queue (Celery)
- Schedule during off-peak hours

## Backup & Recovery

### Backup Processed Files State

```bash
cp backend/grc/changeManagement/data/processed_files.json \
   backend/grc/changeManagement/data/processed_files.backup.json
```

### Restore State

```bash
cp backend/grc/changeManagement/data/processed_files.backup.json \
   backend/grc/changeManagement/data/processed_files.json
```

### Reprocess All Files

Delete processed files state:
```bash
echo '{"processed": []}' > backend/grc/changeManagement/data/processed_files.json
```

Then run scan again.

## Support & Maintenance

### Regular Maintenance

- **Weekly**: Review processed files log
- **Monthly**: Clean up old PDFs from `data/` directory
- **Quarterly**: Audit S3 bucket for orphaned files

### Getting Help

1. Check logs for error messages
2. Review README.md for architecture
3. Check API endpoint responses
4. Contact development team

## Next Steps

After setup is complete:

1. ✅ Test with one PDF file
2. ✅ Verify S3 upload
3. ✅ Check database amendment
4. ✅ Test frontend display
5. ✅ Set up scheduled automation
6. ✅ Monitor for a week
7. ✅ Document any custom configurations

You're all set! 🎉

