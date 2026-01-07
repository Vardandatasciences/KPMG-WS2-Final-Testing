# S3 Upload Missing Analysis

## Summary
This document identifies file upload, download, and export endpoints that are **NOT using S3** and are saving files locally to `MEDIA_ROOT` instead.

---

## ❌ Endpoints NOT Using S3 (Saving Locally)

### 1. **Risk AI Document Upload**
- **File**: `grc_backend/grc/routes/Risk/risk_ai_doc.py`
- **Function**: `upload_and_process_risk_document()`
- **Current Storage**: `MEDIA_ROOT/ai_uploads/risk/`
- **Line**: ~1218-1229
- **Status**: ❌ Local storage only

### 2. **Risk Instance AI Upload**
- **File**: `grc_backend/grc/routes/Risk/risk_instance_ai.py`
- **Function**: `upload_and_process_risk_instance_document()`
- **Current Storage**: `MEDIA_ROOT/ai_uploads/risk_instance/`
- **Line**: ~959-972
- **Status**: ❌ Local storage only

### 3. **Incident AI Import**
- **File**: `grc_backend/grc/routes/Incident/incident_ai_import.py`
- **Function**: `upload_and_process_incident_document()`
- **Current Storage**: `MEDIA_ROOT/ai_uploads/incident/`
- **Line**: ~886-896
- **Status**: ❌ Local storage only

### 4. **AI Audit Document Upload**
- **File**: `grc_backend/grc/routes/Audit/ai_audit_api.py`
- **Function**: `AIAuditDocumentUploadView.post()`
- **Current Storage**: `MEDIA_ROOT/ai_audit_documents/`
- **Line**: ~679-689
- **Status**: ❌ Local storage only

### 5. **Incident File Upload (General)**
- **File**: `grc_backend/grc/routes/Incident/incident_views.py`
- **Function**: `FileUploadView.post()`
- **Current Storage**: `SecureFileUploadHandler.UPLOAD_DIR` (local secure directory)
- **Line**: ~7355-7363
- **Status**: ❌ Local storage only

### 6. **Incident Evidence File Upload**
- **File**: `grc_backend/grc/routes/Incident/incident_views.py`
- **Function**: `upload_evidence_file()`
- **Current Storage**: Temporary file → S3 (but saves temp locally first)
- **Line**: ~7575-7615
- **Status**: ⚠️ Uses S3 but saves temp file locally first

### 7. **Risk Evidence File Upload**
- **File**: `grc_backend/grc/routes/Risk/risk_views.py`
- **Function**: `upload_risk_evidence_file()`
- **Current Storage**: Temporary file → S3 (but saves temp locally first)
- **Line**: ~5075-5086
- **Status**: ⚠️ Uses S3 but saves temp file locally first

### 8. **Upload Framework**
- **File**: `grc_backend/grc/routes/UploadFramework/new_upload_framework.py`
- **Function**: `upload_framework_file()`
- **Current Storage**: `MEDIA_ROOT/uploaded_frameworks/{userid}/`
- **Line**: ~123-148
- **Status**: ❌ Local storage only

### 9. **Policy Document Upload**
- **File**: `grc_backend/grc/routes/Policy/policy.py`
- **Function**: `upload_policy_document()`
- **Current Storage**: Temporary file → **S3** ✅
- **Line**: ~11196-11220
- **Status**: ✅ **USES S3**

### 10. **Audit Evidence Upload**
- **File**: `grc_backend/grc/routes/Audit/auditing.py`
- **Function**: `upload_evidence_to_s3()`
- **Current Storage**: Temporary file → **S3** ✅
- **Line**: ~992-1015
- **Status**: ✅ **USES S3**

### 11. **Event S3 Upload**
- **File**: `grc_backend/grc/routes/EventHandling/event_views.py`
- **Function**: `s3_upload_file()`
- **Current Storage**: Temporary file → **S3** ✅
- **Line**: ~4175-4195
- **Status**: ✅ **USES S3**

---

## ✅ Endpoints Already Using S3

1. **Audit Evidence Upload** - `upload_evidence_to_s3()` ✅
2. **Policy Document Upload** - `upload_policy_document()` ✅
3. **Event File Upload** - `s3_upload_file()` ✅
4. **Risk Evidence Upload** - `upload_risk_evidence_file()` ✅ (via temp file)
5. **Incident Evidence Upload** - `upload_evidence_file()` ✅ (via temp file)

---

## 📊 Statistics

- **Total Upload Endpoints**: 11
- **Using S3**: 5 (45%)
- **Local Storage Only**: 6 (55%)

---

## 🔧 Recommended Actions

### High Priority (AI Document Processing)
These endpoints process large documents and would benefit significantly from S3:

1. **Risk AI Document Upload** (`risk_ai_doc.py`)
   - Currently: `MEDIA_ROOT/ai_uploads/risk/`
   - Should: Upload to S3, then download for processing if needed

2. **Risk Instance AI Upload** (`risk_instance_ai.py`)
   - Currently: `MEDIA_ROOT/ai_uploads/risk_instance/`
   - Should: Upload to S3, then download for processing if needed

3. **Incident AI Import** (`incident_ai_import.py`)
   - Currently: `MEDIA_ROOT/ai_uploads/incident/`
   - Should: Upload to S3, then download for processing if needed

4. **AI Audit Document Upload** (`ai_audit_api.py`)
   - Currently: `MEDIA_ROOT/ai_audit_documents/`
   - Should: Upload to S3, then download for processing if needed

### Medium Priority (General File Uploads)

5. **Incident File Upload** (`incident_views.py` - `FileUploadView`)
   - Currently: Local secure directory
   - Should: Upload to S3 after security validation

6. **Upload Framework** (`new_upload_framework.py`)
   - Currently: `MEDIA_ROOT/uploaded_frameworks/`
   - Should: Upload to S3

---

## 💡 Implementation Pattern

For endpoints that need to process files (AI extraction, etc.), use this pattern:

```python
# 1. Save temporarily (for decompression if needed)
temp_file_path = save_temp_file(uploaded_file)

# 2. Decompress if needed
temp_file_path = decompress_if_needed(temp_file_path)

# 3. Upload to S3
s3_client = create_direct_mysql_client()
upload_result = s3_client.upload(
    file_path=temp_file_path,
    user_id=user_id,
    custom_file_name=filename,
    module='ModuleName'
)

# 4. Get S3 URL
s3_url = upload_result['file_info']['url']
s3_key = upload_result['file_info']['s3Key']

# 5. Download from S3 for processing (if needed)
# OR process directly from temp file, then upload result to S3

# 6. Clean up temp file
os.remove(temp_file_path)
```

---

## 📝 Notes

- All endpoints now have **compression support** ✅
- Some endpoints use temp files → S3 (good pattern)
- AI processing endpoints should upload to S3 first, then download for processing
- This ensures files are backed up in S3 even if processing fails


