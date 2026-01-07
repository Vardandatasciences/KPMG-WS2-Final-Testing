# Current Document Upload Flow

## What Happens When You Upload a Document (Current Implementation)

### Current Status: **LOCAL STORAGE** (NOT S3)

When you upload a document to the Risk AI Document Upload:

1. **File is compressed** (if > 100KB) ✅ NEW
   - Client compresses file using gzip
   - Saves bandwidth during upload

2. **File is saved to LOCAL DISK** 📁
   - Location: `MEDIA_ROOT/ai_uploads/risk/`
   - Example: `grc_backend/MEDIA_ROOT/ai_uploads/risk/20260105_004039_risk_register_export.pdf.gz`
   - **NOT uploaded to S3** - saved directly to server's local filesystem

3. **File is decompressed** (if it was compressed) ✅ NEW
   - Backend automatically decompresses .gz files
   - Original file is restored

4. **Document is processed**
   - Text is extracted from PDF/DOCX/etc.
   - AI processes the text
   - Risks are extracted

5. **File stays on LOCAL DISK**
   - File remains in `MEDIA_ROOT/ai_uploads/risk/`
   - Not moved to S3
   - Not deleted after processing

---

## Current Implementation Details

**File Storage:**
- ✅ Local filesystem (`MEDIA_ROOT/ai_uploads/risk/`)
- ❌ NOT using S3
- ❌ NOT using cloud storage

**Processing:**
- ✅ Synchronous (waits for processing to complete)
- ✅ Returns results immediately
- ❌ NOT async/background processing

---

## What the Async Architecture Would Do (Future)

According to the PDF document, the **async architecture** (which we haven't implemented yet) would:

1. **Upload to S3** ☁️
   - File uploaded to AWS S3
   - Gets a public/private URL

2. **Create Job Record** 📝
   - Database record with `job_id`
   - Status: "processing"

3. **Return Immediately** ⚡
   - Frontend gets `job_id` immediately
   - Doesn't wait for processing

4. **Background Processing** 🔄
   - AI processes in background (separate service/thread)
   - Updates job status when complete

5. **Frontend Polls Status** 🔍
   - Frontend polls `/api/risk-ai-doc/status/<job_id>`
   - Gets results when ready

---

## Summary

| Feature | Current | Future (Async) |
|---------|---------|----------------|
| **Storage** | Local disk | S3 ☁️ |
| **Processing** | Synchronous | Async/Background |
| **Response** | Wait for results | Immediate job_id |
| **Status** | ✅ Implemented | 🚧 Not implemented yet |

---

## Check Your Upload Location

To see where files are being saved, check:

1. **Backend logs** - Look for:
   ```
   ✅ File saved to: /path/to/MEDIA_ROOT/ai_uploads/risk/...
   ```

2. **File system** - Check:
   ```
   grc_backend/MEDIA_ROOT/ai_uploads/risk/
   ```

3. **Django settings** - Check `MEDIA_ROOT` setting in:
   ```
   grc_backend/grc_backend/settings.py
   ```

---

## To Enable S3 Upload (Future)

When we implement async architecture, we would:
1. Upload file to S3 using `create_direct_mysql_client()`
2. Get S3 URL
3. Store URL in database
4. Process asynchronously
5. Update status when complete

**This is part of the async architecture optimization that we haven't implemented yet.**


