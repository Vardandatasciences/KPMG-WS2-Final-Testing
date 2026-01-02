# Testing Guide: File Upload Compression

## Prerequisites

1. **Install Dependencies**
   ```bash
   cd grc_frontend
   npm install
   ```
   This will install the `pako` library we added for compression.

2. **Verify Installation**
   ```bash
   npm list pako
   ```
   Should show `pako@^2.1.0` or similar version.

## Testing Steps

### Step 1: Start the Backend Server

Make sure your Django backend is running:
```bash
cd grc_backend
python manage.py runserver
```

### Step 2: Start the Frontend Server

In a separate terminal:
```bash
cd grc_frontend
npm run serve
```

### Step 3: Test File Compression

1. **Open the Application**
   - Navigate to the Risk AI Document Upload page
   - URL: `http://localhost:8080` (or your frontend port)

2. **Select a Large File**
   - Choose a PDF file that is **larger than 100KB**
   - Files smaller than 100KB will NOT be compressed (by design)
   - Recommended test file: A compliance document PDF (5-50MB works best)

3. **Upload the File**
   - Click "Choose File" and select your test PDF
   - Click "Process with AI"
   - **Watch the browser console** (F12 → Console tab)

### Step 4: Check Compression Logs

#### In Browser Console (Frontend)

You should see logs like:
```
✅ Compressed filename.pdf: 72.5% reduction
   Original: 5240.5 KB
   Compressed: 1435.2 KB
```

**What to look for:**
- ✅ Compression log appears (for files > 100KB)
- Compression ratio is typically 60-80% for PDFs
- Original and compressed sizes are logged

#### In Backend Console/Terminal

You should see logs like:
```
✅ Decompressed upload: 72.5% reduction
   Bandwidth saved: 3805.3 KB
📦 Decompressed file: 72.5% reduction, saved 3805.3 KB
```

**What to look for:**
- Decompression confirmation
- Compression ratio matches frontend
- Bandwidth saved amount

### Step 5: Verify Normal Processing

After compression/decompression:
- Document should process normally
- Risk extraction should work as before
- Response should include compression metadata

### Step 6: Test Response Metadata

Check the API response for compression metadata:
```json
{
  "status": "success",
  "risks": [...],
  "compression_metadata": {
    "original_size": 5240448,
    "compressed_size": 1435238,
    "ratio": 72.6,
    "bandwidth_saved_kb": 3805.2
  }
}
```

## Test Cases

### Test Case 1: Large PDF (Should Compress)
- **File**: PDF > 100KB
- **Expected**: Compression logs in console
- **Expected**: Compression ratio 60-80%
- **Expected**: Faster upload time

### Test Case 2: Small File (Should NOT Compress)
- **File**: PDF < 100KB (e.g., 50KB)
- **Expected**: No compression logs
- **Expected**: Original file uploaded
- **Expected**: Normal processing

### Test Case 3: Already Compressed File (Should NOT Compress)
- **File**: .zip, .jpg, .png file
- **Expected**: No compression logs
- **Expected**: Original file uploaded

### Test Case 4: Compressible File Types
- **Files**: .pdf, .docx, .txt, .csv, .xlsx
- **Expected**: All should compress if > 100KB

## Troubleshooting

### Issue: No Compression Logs

**Possible Causes:**
1. File is too small (< 100KB)
2. File type is not compressible (.jpg, .zip, etc.)
3. pako library not installed

**Solution:**
```bash
cd grc_frontend
npm install
# Verify installation
npm list pako
```

### Issue: "pako is not defined" Error

**Cause:** pako library not loaded

**Solution:**
- Check browser console for import errors
- Verify `npm install` completed successfully
- Check if pako is in `package.json`
- Restart frontend dev server

### Issue: Backend Not Decompressing

**Possible Causes:**
1. File doesn't have .gz extension
2. File wasn't actually compressed (too small)
3. Decompression utility not imported

**Solution:**
- Check backend logs for decompression messages
- Verify file has .gz extension when uploaded
- Check import in `risk_ai_doc.py`:
  ```python
  from ...utils.file_compression import decompress_if_needed
  ```

### Issue: Upload Fails After Compression

**Possible Causes:**
1. Compressed file corrupted
2. Backend can't decompress
3. Network error during upload

**Solution:**
- Check browser network tab for failed requests
- Check backend error logs
- Try with a different file
- Verify file compression completed successfully

## Performance Testing

### Measure Upload Time

1. **Without Compression:**
   - Upload large file (10MB PDF)
   - Note upload time in browser network tab
   - Example: 60 seconds

2. **With Compression:**
   - Upload same file
   - Note upload time
   - Example: 15 seconds

3. **Calculate Improvement:**
   - Expected: 70-80% reduction in upload time
   - Formula: `(Original - Compressed) / Original * 100`

### Measure Bandwidth Savings

Check the compression metadata in response:
```json
"compression_metadata": {
  "bandwidth_saved_kb": 3805.2
}
```

Multiply by number of uploads to estimate monthly savings.

## Expected Results

✅ **Success Indicators:**
- Compression logs appear in console for large files
- Upload time reduced significantly (70-80%)
- Backend successfully decompresses files
- Processing continues normally after decompression
- Compression metadata included in response
- No errors in console or backend logs

❌ **Failure Indicators:**
- No compression logs (check file size/type)
- Errors in browser console
- Backend errors during decompression
- Upload fails or times out
- Processing fails after compression

## Quick Test Checklist

- [ ] npm install completed successfully
- [ ] pako library installed (npm list pako)
- [ ] Backend server running
- [ ] Frontend server running
- [ ] Browser console open (F12)
- [ ] Test file selected (> 100KB PDF)
- [ ] Compression logs appear in browser console
- [ ] Decompression logs appear in backend console
- [ ] File processes successfully
- [ ] Compression metadata in API response
- [ ] Upload time significantly reduced

## Next Steps After Testing

If compression works correctly:
1. ✅ File compression implementation is complete
2. Consider adding compression to other upload endpoints
3. Monitor compression metrics in production
4. Proceed to next optimization (Async Processing or Streaming)

If issues found:
1. Check troubleshooting section
2. Verify all files are in place
3. Check browser/backend console for errors
4. Test with different file sizes/types

