# Compliance Mapping Update API Guide

## Overview
This guide explains how to update compliance mappings using the PUT and PATCH endpoints.

## Endpoints

### PUT - Full Update
**URL:** `PUT {{base_url}}/api/tprm/v1/compliance/compliance-mappings/{{compliance_mapping_id}}/`

**Description:** Updates all fields of a compliance mapping. You should provide all fields (or at least all required fields).

### PATCH - Partial Update
**URL:** `PATCH {{base_url}}/api/tprm/v1/compliance/compliance-mappings/{{compliance_mapping_id}}/`

**Description:** Updates only the fields you provide. Other fields remain unchanged.

## Authentication

**Required Headers:**
```
Content-Type: application/json
Authorization: Bearer {{access_token}}
```

## Request Body Fields

### Required Fields (for PUT - full update)
- `sla_id` (integer) - SLA ID
- `framework_id` (integer) - Framework ID
- `compliance_version` (string) - Version of compliance (e.g., "v1.0")

### Optional Fields
- `compliance_status` (string) - Status: "Compliant", "Non-Compliant", "Partially Compliant", etc.
- `compliance_score` (decimal/float) - Score from 0.00 to 100.00
- `compliance_description` (string) - Description of the compliance mapping
- `last_audited` (date string) - Last audit date in format "YYYY-MM-DD"
- `next_audit_due` (date string) - Next audit due date in format "YYYY-MM-DD"
- `assigned_auditor` (string) - Name or email of assigned auditor
- `audit_frequency` (string) - One of: "DAILY", "WEEKLY", "MONTHLY", "QUARTERLY"

### Read-Only Fields (will be ignored if sent)
- `mapping_id` - Primary key, cannot be changed
- `framework_name` - Automatically derived from framework
- `framework_category` - Automatically derived from framework
- `framework_version` - Automatically derived from framework
- `sla_name` - Automatically generated
- `vendor_name` - Automatically generated

## Important Constraints

⚠️ **Unique Constraint:** The combination of `sla_id` + `framework_id` must be unique. If you try to update these to values that already exist in another record, the update will fail.

## Example Requests

### Example 1: PUT - Full Update

**Request:**
```json
PUT {{base_url}}/api/tprm/v1/compliance/compliance-mappings/7/

Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body:
{
  "sla_id": 1,
  "framework_id": 1,
  "compliance_status": "Compliant",
  "compliance_score": 90.0,
  "compliance_description": "Updated compliance mapping description",
  "compliance_version": "v1.0",
  "audit_frequency": "MONTHLY",
  "assigned_auditor": "john.doe@example.com",
  "last_audited": "2025-01-10",
  "next_audit_due": "2025-04-10"
}
```

**Response (200 OK):**
```json
{
  "mapping_id": 7,
  "sla_id": 1,
  "framework_id": 1,
  "compliance_status": "Compliant",
  "compliance_score": "90.00",
  "compliance_description": "Updated compliance mapping description",
  "compliance_version": "v1.0",
  "audit_frequency": "MONTHLY",
  "assigned_auditor": "john.doe@example.com",
  "last_audited": "2025-01-10",
  "next_audit_due": "2025-04-10",
  "framework_name": "ISO 27001",
  "framework_category": "Information Security",
  "framework_version": 1.0,
  "sla_name": "SLA-1",
  "vendor_name": "Unknown Vendor"
}
```

### Example 2: PATCH - Partial Update (Update Only Score and Status)

**Request:**
```json
PATCH {{base_url}}/api/tprm/v1/compliance/compliance-mappings/7/

Headers:
Content-Type: application/json
Authorization: Bearer {{access_token}}

Body:
{
  "compliance_status": "Non-Compliant",
  "compliance_score": 65.0
}
```

**Response (200 OK):**
```json
{
  "mapping_id": 7,
  "sla_id": 1,
  "framework_id": 1,
  "compliance_status": "Non-Compliant",
  "compliance_score": "65.00",
  "compliance_description": "Oracle Database SLA compliance to ISO 27001 standards with a 95% compliance rate",
  "compliance_version": "v1.0",
  "audit_frequency": "MONTHLY",
  "assigned_auditor": "John Doe",
  "last_audited": "2025-01-10",
  "next_audit_due": "2025-04-10",
  "framework_name": "ISO 27001",
  "framework_category": "Information Security",
  "framework_version": 1.0,
  "sla_name": "SLA-1",
  "vendor_name": "Unknown Vendor"
}
```

## How to Use in Postman

### Step 1: Set Environment Variables
1. Create or select an environment in Postman
2. Set these variables:
   - `base_url`: Your API base URL (e.g., `http://localhost:8000`)
   - `access_token`: Your JWT authentication token
   - `compliance_mapping_id`: The ID of the compliance mapping to update (e.g., `7`)

### Step 2: Create PUT Request
1. Method: **PUT**
2. URL: `{{base_url}}/api/tprm/v1/compliance/compliance-mappings/{{compliance_mapping_id}}/`
3. Headers:
   - `Content-Type`: `application/json`
   - `Authorization`: `Bearer {{access_token}}`
4. Body (raw JSON):
   ```json
   {
     "sla_id": 1,
     "framework_id": 1,
     "compliance_status": "Compliant",
     "compliance_score": 90.0,
     "compliance_description": "Updated description",
     "compliance_version": "v1.0"
   }
   ```

### Step 3: Create PATCH Request
1. Method: **PATCH**
2. URL: `{{base_url}}/api/tprm/v1/compliance/compliance-mappings/{{compliance_mapping_id}}/`
3. Headers: Same as PUT
4. Body (raw JSON) - Only include fields you want to update:
   ```json
   {
     "compliance_status": "Non-Compliant",
     "compliance_score": 65.0
   }
   ```

## Common Issues and Solutions

### Issue 1: Update Not Reflecting in Response
**Symptom:** You send an update but the response shows old values.

**Solution:** The endpoint now refreshes the instance from the database after saving. Make sure you're using the latest code.

### Issue 2: Unique Constraint Error
**Symptom:** Error about duplicate `sla_id` and `framework_id` combination.

**Solution:** 
- Don't change `sla_id` or `framework_id` to values that already exist
- Or delete/update the existing record first
- Or use a different combination

### Issue 3: Missing Required Fields (PUT only)
**Symptom:** Validation error about missing required fields.

**Solution:** 
- For PUT requests, include all required fields: `sla_id`, `framework_id`, `compliance_version`
- For PATCH requests, you only need to include fields you want to update

### Issue 4: Invalid Field Values
**Symptom:** Validation error about field values.

**Solutions:**
- `compliance_score`: Must be between 0.00 and 100.00
- `audit_frequency`: Must be one of: "DAILY", "WEEKLY", "MONTHLY", "QUARTERLY"
- `last_audited` and `next_audit_due`: Must be valid date strings in "YYYY-MM-DD" format

## Testing Checklist

- [ ] Set correct `compliance_mapping_id` in environment variable
- [ ] Set valid `access_token` in environment variable
- [ ] Use correct HTTP method (PUT for full, PATCH for partial)
- [ ] Include required headers (Content-Type and Authorization)
- [ ] For PUT: Include all required fields
- [ ] For PATCH: Include only fields to update
- [ ] Check response status is 200 OK
- [ ] Verify response contains updated values
- [ ] Query the record again to confirm changes persisted

## Response Codes

- **200 OK**: Update successful
- **400 Bad Request**: Validation error or invalid data
- **401 Unauthorized**: Missing or invalid authentication token
- **403 Forbidden**: Not authorized to update this record
- **404 Not Found**: Compliance mapping with given ID not found
- **500 Internal Server Error**: Server error (check logs)
