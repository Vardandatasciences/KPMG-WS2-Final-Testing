# Export Framework Policies Error Solution

## Error
```
500 Internal Server Error
{
  "success": false,
  "error": "'export_id'"
}
```

## Root Cause
The backend code at `grc_backend/grc/routes/Policy/policy.py` line 4882 tries to access `result['export_id']`, but the `export_data()` function doesn't return an `export_id` field. This is a **backend bug**.

## Backend Code Issue
```python
# Line 4880-4886 in policy.py
return Response({
    'success': True,
    'export_id': result['export_id'],  # ❌ KeyError: 'export_id' doesn't exist
    'file_url': result['file_url'],
    'file_name': result['file_name'],
    'metadata': result['metadata']
})
```

The `export_data()` function returns:
```python
{
    'success': True,
    'file_url': '...',
    'file_name': '...',
    'metadata': {...}
    # ❌ Missing 'export_id'
}
```

## Solutions (Without Changing Backend)

### Option 1: Verify Framework Has Data
The export might fail if the framework has no policies to export:

1. **Test Framework Exists:**
   ```
   GET {{base_url}}/api/frameworks/{{framework_id}}
   ```

2. **Check if Framework has Policies:**
   ```
   GET {{base_url}}/api/frameworks/{{framework_id}}/policies-list
   ```

3. **If framework has no policies**, the export will fail. Add policies first or use a framework that has data.

### Option 2: Try Different Export Format
Try using a different format that might handle the error differently:

```json
{
  "format": "csv"
}
```

or

```json
{
  "format": "json"
}
```

### Option 3: Use Export All Frameworks Instead
If you need to export data, try the "Export All Frameworks" endpoint instead:

```
POST {{base_url}}/api/frameworks/export-all
Body: {}
```

### Option 4: Check Backend Logs
The backend should log detailed error messages. Check the server logs for:
- S3 connection errors
- Database connection issues
- Export function failures

## Required Backend Fix (For Developer)
The backend needs to be fixed to either:
1. Add `export_id` to the return value of `export_data()` function, OR
2. Make `export_id` optional in the response (use `result.get('export_id', None)`)

**File to fix:** `grc_backend/grc/routes/Policy/policy.py` line 4882

**Change from:**
```python
'export_id': result['export_id'],
```

**Change to:**
```python
'export_id': result.get('export_id', None),  # Make optional
```

## Workaround for Testing
Since this is a backend bug, the Postman request format is correct. The issue must be fixed in the backend code. Until then, you can:

1. Skip this endpoint for testing
2. Use "Export All Frameworks" if it works
3. Check backend logs for more details
4. Verify the framework has data before exporting
