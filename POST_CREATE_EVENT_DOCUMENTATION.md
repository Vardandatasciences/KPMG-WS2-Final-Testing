# POST Create Event Endpoint Documentation

## Overview
The POST Create Event endpoint allows you to create a new event in the GRC system. This document explains how it should work based on the actual implementation.

## Endpoint

**Correct URL:** `POST {{base_url}}/api/events/create/`

**Note:** The Postman collection currently uses `POST {{base_url}}/api/events/`, which is incorrect. That route maps to the GET events handler.

## Authentication & Authorization

- **Required:** Bearer token in Authorization header
- **Permission:** `EventCreatePermission` 
- **Consent:** Requires `create_event` consent
- **Multi-tenancy:** Tenant ID must be present in request headers

### Headers Required:
```
Content-Type: application/json
Authorization: Bearer {{access_token}}
X-Tenant-ID: <tenant_id>  (if not in JWT)
```

## Request Body

### Required Fields

1. **`title`** (string, required) - Event title/name
   - This is the main identifier for the event
   - Example: `"Test Event"`

2. **`user_id`** (integer, required) - ID of the user creating the event
   - Can be passed in request body or query parameter
   - Must exist in the users table

### Optional Fields

3. **`description`** (string, optional) - Event description
   - Example: `"Test event description"`

4. **`framework_id`** (integer, optional) - Framework ID to associate with the event
   - Must exist in frameworks table if provided

5. **`framework_name`** (string, optional) - Framework name
   - Example: `"ISO 27001"`

6. **`module`** (string, optional) - Module name
   - Example: `"Compliance"`

7. **`category`** (string, optional) - Event category
   - Example: `"compliance"` or `"Policy Management"`

8. **`event_type_id`** (integer, optional) - ID of the event type
   - Must exist in eventtype table if provided

9. **`sub_event_type_id`** (integer, optional) - Index of sub-event type
   - Used to select from the event type's subtypes

10. **`linked_record_type`** (string, optional) - Type of linked record
    - Example: `"Policy"`, `"Risk"`, `"Compliance"`

11. **`linked_record_id`** (integer, optional) - ID of linked record

12. **`linked_record_name`** (string, optional) - Name of linked record

13. **`owner_id`** (integer, optional) - User ID of event owner
    - Defaults to the logged-in user if not provided

14. **`reviewer_id`** (integer, optional) - User ID of event reviewer

15. **`status`** (string, optional) - Event status
    - Default: `"Under Review"`
    - Other values: `"Draft"`, `"Approved"`, `"Rejected"`, etc.

16. **`priority`** (string, optional) - Event priority
    - Default: `"Medium"`
    - Values: `"Low"`, `"Medium"`, `"High"`, `"Critical"`

17. **`recurrence_type`** (string, optional) - Recurrence pattern
    - Default: `"Non-Recurring"`
    - Values: `"Daily"`, `"Weekly"`, `"Monthly"`, `"Yearly"`, `"Non-Recurring"`

18. **`frequency`** (string, optional) - Frequency details (for recurring events)
    - Set to `null` if `recurrence_type` is `"Non-Recurring"`

19. **`start_date`** (date, optional) - Event start date
    - Format: `"YYYY-MM-DD"` or ISO date string
    - Empty strings are converted to `null`

20. **`end_date`** (date, optional) - Event end date
    - Format: `"YYYY-MM-DD"` or ISO date string
    - Empty strings are converted to `null`

21. **`is_template`** (boolean, optional) - Whether this is a template
    - Default: `false`

22. **`evidence`** (array or JSON string, optional) - Evidence files
    - Format: Array of objects with `s3_url` property
    - Example: `[{"s3_url": "https://s3.../file.pdf"}]`

23. **`dynamic_fields`** (object, optional) - Custom dynamic field data
    - JSON object with key-value pairs

24. **`data_inventory`** (object or JSON string, optional) - Data inventory mapping
    - Maps field labels to data types: `"personal"`, `"confidential"`, `"regular"`

25. **`additional_records`** (array, optional) - Additional linked records
    - Creates additional events for each record
    - Each item should have: `framework_id`, `framework_name`, `module`, `linked_record_type`, `linked_record_id`, `linked_record_name`

## Example Request Body

```json
{
  "title": "Test Event",
  "description": "Test event description",
  "user_id": 1,
  "category": "compliance",
  "framework_id": 1,
  "framework_name": "ISO 27001",
  "module": "Compliance",
  "priority": "High",
  "status": "Under Review",
  "recurrence_type": "Non-Recurring",
  "start_date": "2026-01-21",
  "end_date": "2026-01-31",
  "owner_id": 1,
  "reviewer_id": 2,
  "evidence": [
    {
      "s3_url": "https://s3.amazonaws.com/bucket/file.pdf"
    }
  ]
}
```

## Response Format

### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Event created successfully",
  "event_id": 15277,
  "event_id_generated": "EVT-2026-2042",
  "total_events_created": 1,
  "events": [
    {
      "EventId": 15277,
      "EventTitle": "Test Event",
      "Status": "Under Review",
      "RecurrenceType": "Non-Recurring",
      "StartDate": "2026-01-21",
      "EndDate": "2026-01-31",
      "LinkedRecordName": null,
      "FrameworkName": "ISO 27001",
      "Module": "Compliance"
    }
  ]
}
```

### Error Responses

#### 400 Bad Request - Missing Required Field
```json
{
  "success": false,
  "message": "User ID is required"
}
```

#### 400 Bad Request - Missing Title
```json
{
  "success": false,
  "message": "Event title is required"
}
```

#### 400 Bad Request - Framework Not Found
```json
{
  "success": false,
  "message": "Framework with ID {id} not found"
}
```

#### 500 Internal Server Error - Database Schema Issue
```json
{
  "success": false,
  "message": "Events table schema mismatch. Please run: python manage.py create_events_table",
  "error": "..."
}
```

#### 500 Internal Server Error - General Error
```json
{
  "success": false,
  "message": "Error creating event: {error details}"
}
```

## Key Behaviors

1. **Default Status**: All events are created with status `"Under Review"` unless explicitly set otherwise

2. **Owner Assignment**: If `owner_id` is not provided, it defaults to the logged-in user (from `user_id`)

3. **Evidence Storage**: Evidence files are stored as a semicolon-separated string of S3 URLs in the database

4. **Multiple Events**: If `additional_records` is provided, multiple events are created (one primary + one per additional record)

5. **Notifications**: 
   - Email notifications are sent to Owner, Reviewer, and Creator
   - In-app notifications are created for all recipients
   - Uses templates: `eventCreated` or `eventAssigned`

6. **Data Validation**:
   - Empty strings are converted to `null` for optional fields
   - Frequency is set to `null` for non-recurring events
   - Framework and User objects are validated before creation

## Issues with Current Postman Collection

1. **Wrong Endpoint**: Uses `/api/events/` instead of `/api/events/create/`
2. **Wrong Field Names**: 
   - Uses `name` instead of `title`
   - Missing required `user_id` field
   - Uses `type` which doesn't map to any field (should be `category`)
3. **Incomplete Request**: Missing many optional but commonly used fields

## Recommended Postman Request

Update your Postman collection to use:

**Method:** POST  
**URL:** `{{base_url}}/api/events/create/`  
**Headers:**
```
Content-Type: application/json
Authorization: Bearer {{access_token}}
```

**Body (raw JSON):**
```json
{
  "title": "Test Event",
  "description": "Test event description",
  "user_id": 1,
  "category": "compliance",
  "priority": "High"
}
```
