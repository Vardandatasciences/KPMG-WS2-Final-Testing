# Postman API Testing Guide

## Quick Setup

### 1. Environment Variables
Set these in your Postman environment:
- `base_url`: Your API base URL (e.g., `http://localhost:8000`)
- `access_token`: JWT token from login endpoint
- `framework_id`: Valid framework ID (e.g., `2`)
- `user_id`: Valid user ID (e.g., `1`)

### 2. Get Access Token First
1. Go to **"Authentication & Authorization"** section
2. Find **"POST Login"** or **"POST JWT"** endpoint
3. Send request with your credentials
4. Copy `access_token` from response
5. Set it in environment variables

---

## Testing Fixed Endpoints

### ✅ 1. Create Framework Version (POST)
**Endpoint:** `{{base_url}}/api/frameworks/{{framework_id}}/create-version`

**Body (JSON):**
```json
{
  "FrameworkName": "Updated Framework Name",
  "version_type": "minor"
}
```

**Expected Response:** 200/201 with framework version details

---

### ✅ 2. Export Framework Policies (POST)
**Endpoint:** `{{base_url}}/api/frameworks/{{framework_id}}/export`

**Body (JSON):**
```json
{
  "format": "xlsx"
}
```

**Expected Response:** 200 with file download or file URL

---

### ✅ 3. Export All Frameworks (POST)
**Endpoint:** `{{base_url}}/api/frameworks/export-all`

**Body (JSON):**
```json
{
  "format": "xlsx"
}
```

**Expected Response:** 200 with file download

---

### ✅ 4. Activate/Deactivate Framework Version (PUT)
**Endpoint:** `{{base_url}}/api/frameworks/{{framework_id}}/toggle-active`

**Body (JSON):**
```json
{}
```

**Expected Response:** 200 with activation status

---

### ✅ 5. Get Rejected Framework Versions (GET)
**Endpoint:** `{{base_url}}/api/framework-versions/rejected?user_id={{user_id}}`

**Query Parameters:**
- `user_id`: Required (set in environment variables)

**Expected Response:** 200 with list of rejected framework versions

---

### ✅ 6. Resubmit Rejected Framework (POST)
**Endpoint:** `{{base_url}}/api/frameworks/{{framework_id}}/resubmit-version`

**Body (JSON):**
```json
{
  "FrameworkName": "Resubmitted Framework",
  "policies": []
}
```

**Expected Response:** 200/201 with resubmission confirmation

---

### ✅ 7. Resubmit Framework Approval (PUT)
**Endpoint:** `{{base_url}}/api/frameworks/{{framework_id}}/resubmit-approval`

**Body (JSON):**
```json
{
  "FrameworkName": "Resubmitted Framework",
  "policies": []
}
```

**Expected Response:** 200 with approval status

---

### ✅ 8. Set Selected Framework (POST)
**Endpoint:** `{{base_url}}/api/frameworks/set-selected`

**Body (JSON):**
```json
{
  "frameworkId": "{{framework_id}}",
  "userId": "{{user_id}}"
}
```

**Expected Response:** 200 with success message

---

## Response Status Codes

- **200/201**: ✅ Success
- **400**: ❌ Bad Request - Check request body format
- **401**: ❌ Unauthorized - Update access_token
- **403**: ❌ Forbidden - Check permissions
- **404**: ❌ Not Found - Verify IDs exist
- **405**: ❌ Method Not Allowed - Should NOT appear after fixes

---

## Troubleshooting

### Issue: 401 Unauthorized
**Solution:** 
1. Go to login endpoint
2. Get new access_token
3. Update environment variable

### Issue: 400 Bad Request
**Solution:**
1. Check request body format (must be valid JSON)
2. Verify all required fields are present
3. Check data types match API expectations

### Issue: 404 Not Found
**Solution:**
1. Verify `framework_id` exists in your database
2. Verify `user_id` exists in your database
3. Check `base_url` is correct

### Issue: 405 Method Not Allowed
**Solution:**
- This should NOT happen after fixes
- If it does, verify the HTTP method matches the endpoint (POST/PUT/GET)

---

## Testing Workflow

1. **Setup Environment Variables** (base_url, access_token, framework_id, user_id)
2. **Get Access Token** (from login endpoint)
3. **Test Each Endpoint** in order:
   - Start with GET endpoints (easier to test)
   - Then test POST endpoints
   - Finally test PUT endpoints
4. **Verify Responses** match expected status codes
5. **Check Response Body** for data or error messages

---

## Tips

- Use **Collection Runner** to test all endpoints at once
- Check **Test Results** tab for automated test results
- Use **Console** (View → Show Postman Console) to debug requests
- Save successful requests as examples for future reference
