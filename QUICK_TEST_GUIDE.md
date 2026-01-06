# Quick Testing Guide - File Compression

## ✅ Prerequisites Check
- [x] pako library installed (v2.1.0) ✓

## Quick Test Steps

### 1. Start Servers
```bash
# Terminal 1 - Backend
cd grc_backend
python manage.py runserver

# Terminal 2 - Frontend  
cd grc_frontend
npm run serve
```

### 2. Test Compression

1. **Open Browser**
   - Go to Risk AI Document Upload page
   - Open Developer Tools (F12) → Console tab

2. **Upload Large File**
   - Select a PDF file **> 100KB** (ideally 1-10MB)
   - Click "Process with AI"

3. **Check Console Logs**

   **Browser Console (Frontend):**
   ```
   ✅ Compressed filename.pdf: XX% reduction
      Original: XXX KB
      Compressed: XXX KB
   ```

   **Backend Terminal:**
   ```
   📦 Decompressed file: XX% reduction, saved XXX KB
   ✅ Decompressed upload: XX% reduction
   ```

### 3. Verify Success

✅ **Success if you see:**
- Compression logs in browser console
- Decompression logs in backend
- File processes successfully
- Upload completes faster than before

❌ **If no compression logs:**
- File might be < 100KB (compression skipped for small files)
- Check file type (PDF, DOCX, TXT compress well)
- Try with a larger file

### 4. Test Different Scenarios

| File Type | Size | Should Compress? |
|-----------|------|------------------|
| PDF | > 100KB | ✅ Yes |
| PDF | < 100KB | ❌ No (too small) |
| DOCX | > 100KB | ✅ Yes |
| JPG | Any size | ❌ No (already compressed) |
| ZIP | Any size | ❌ No (already compressed) |

## Expected Results

**For a 5MB PDF:**
- Compression ratio: 60-80%
- Upload time: ~60s → ~15s (75% faster)
- Bandwidth saved: ~3-4MB

## Quick Troubleshooting

**No compression logs?**
→ File is too small or wrong type. Use PDF > 100KB.

**Error in console?**
→ Check that pako is installed: `npm list pako`

**Upload fails?**
→ Check backend logs for errors

## Full Testing Guide

For detailed testing instructions, see: `TESTING_GUIDE_FILE_COMPRESSION.md`

