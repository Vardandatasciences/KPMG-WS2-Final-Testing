# How PUT Requests Work - Activate/Deactivate Framework Version

## Endpoint
```
PUT {{base_url}}/api/frameworks/{{framework_id}}/toggle-active
```

## Request Body Options

### Option 1: Toggle (Default)
Automatically toggles between Active/Inactive based on current status:
```json
{
  "action": "toggle"
}
```
or simply:
```json
{}
```

**Behavior:**
- If currently `Inactive` → becomes `Active` (or `Scheduled` if StartDate is in future)
- If currently `Active` → becomes `Inactive`

### Option 2: Explicitly Activate
Force activation regardless of current status:
```json
{
  "action": "activate"
}
```

**Behavior:**
- Sets to `Active` (or `Scheduled` if StartDate > today)
- Uses date-based scheduling logic

### Option 3: Explicitly Deactivate
Force deactivation:
```json
{
  "action": "deactivate"
}
```

**Behavior:**
- Sets to `Inactive` regardless of current status

## Date-Based Scheduling Logic

When activating (`action: "activate"` or toggle to active):
- If `StartDate` > today → Status becomes `Scheduled`
- If `StartDate` <= today or None → Status becomes `Active`

## Headers Required

```
Content-Type: application/json
Authorization: Bearer {{access_token}}
```

## Expected Response (Success - 200)

```json
{
  "message": "Framework version updated to Active successfully",
  "FrameworkId": 2,
  "ActiveInactive": "Active",
  "Status": "Approved"
}
```

## Error Responses

### 404 Not Found
```json
{
  "error": "Framework not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Error message"
}
```

## Testing in Postman

1. **Set Environment Variables:**
   - `base_url`: Your API URL
   - `framework_id`: Valid framework ID (e.g., `2`)
   - `access_token`: Your JWT token

2. **Select Body Tab:**
   - Choose "raw"
   - Select "JSON" format

3. **Enter Request Body:**
   ```json
   {
     "action": "toggle"
   }
   ```

4. **Click Send**

5. **Check Response:**
   - Status: 200 OK
   - Body: Contains framework status information

## Example Use Cases

### Toggle Status
```json
{}
```
or
```json
{
  "action": "toggle"
}
```

### Force Activate
```json
{
  "action": "activate"
}
```

### Force Deactivate
```json
{
  "action": "deactivate"
}
```

## Notes

- The `action` parameter is **optional** - defaults to `"toggle"` if not provided
- Empty body `{}` works fine and will toggle the status
- The endpoint uses date-based scheduling when activating
- Framework must exist and belong to your tenant
