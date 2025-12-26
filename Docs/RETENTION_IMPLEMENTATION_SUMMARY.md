# Retention Expiry Signal Handlers - Implementation Summary

## ✅ Successfully Implemented

### 1. **Document Uploads Module** (`document_handling`)

#### a) AuditDocument Model Handler
- **Location:** Line 1901-1905
- **Model:** `AuditDocument`
- **Page Keys:**
  - `document_upload` (when created)
  - `document_save` (when updated)
- **Module:** `document_handling`
- **Status:** ✅ Implemented

#### b) S3File Model Handler
- **Location:** Line 1908-1912
- **Model:** `S3File`
- **Page Key:** `document_upload` (when created)
- **Module:** `document_handling`
- **Status:** ✅ Implemented

#### c) FileOperations Model Handler
- **Location:** Line 2264-2268
- **Model:** `FileOperations`
- **Page Key:** `document_upload` (only for upload operations when created)
- **Module:** `document_handling`
- **Status:** ✅ Implemented

---

### 2. **Event Handling Module** (`event_handling`)

#### Event Model Handler
- **Location:** Line 2121-2125
- **Model:** `Event`
- **Page Keys:**
  - `event_create` (when created)
  - `event_log` (when updated)
- **Module:** `event_handling`
- **Status:** ✅ Implemented

---

### 3. **Change Management Module** (`change_management`)

#### ChangeRequest Model Handler
- **Location:** Line 1915-1928 (commented out with instructions)
- **Model:** `ChangeRequest` (does not exist yet)
- **Page Keys:**
  - `change_create` (when created)
  - `change_update` (when updated)
- **Module:** `change_management`
- **Status:** ⚠️ **Pending - Model Not Found**

**Note:** The `ChangeRequest` model does not exist in the codebase. The signal handler code is documented as a comment with instructions for when the model is created.

---

## How It Works

All signal handlers follow this pattern:

```python
@receiver(post_save, sender=ModelName)
def set_model_retention_expiry(sender, instance, created, **kwargs):
    page_key = 'create_key' if created else 'update_key'
    _set_retention_expiry(instance, 'module_key', page_key)
```

The `_set_retention_expiry()` function:
1. Looks up the `RetentionModulePageConfig` table for the module/page combination
2. Gets the `retention_days` value (default: 210 days if not configured)
3. Calculates `retentionExpiry = current_date + retention_days`
4. Updates the model instance's `retentionExpiry` field

---

## Coverage Summary

| Module | Models Covered | Status |
|--------|---------------|--------|
| **Document Handling** | AuditDocument, S3File, FileOperations | ✅ Complete |
| **Event Handling** | Event | ✅ Complete |
| **Change Management** | ChangeRequest | ⚠️ Pending Model Creation |

---

## Next Steps for Change Management

When the `ChangeRequest` model is created, uncomment and activate the signal handler at line 1921:

```python
@receiver(post_save, sender=ChangeRequest)
def set_change_request_retention_expiry(sender, instance, created, **kwargs):
    """Set retention expiry for change requests"""
    page_key = 'change_create' if created else 'change_update'
    _set_retention_expiry(instance, 'change_management', page_key)
```

---

## Testing Recommendations

1. **Document Uploads:**
   - Test creating an AuditDocument → should set `retentionExpiry`
   - Test uploading via S3File → should set `retentionExpiry`
   - Test FileOperations with `operation_type='upload'` → should set `retentionExpiry`

2. **Events:**
   - Test creating an Event → should set `retentionExpiry` with `event_create` page key
   - Test updating an Event → should set `retentionExpiry` with `event_log` page key

3. **Change Management:**
   - Wait until ChangeRequest model is created, then test

---

## Configuration Required

Make sure the following module/page combinations are configured in the `retention_module_page_config` table:

- `module='document_handling'`, `sub_page='document_upload'`
- `module='document_handling'`, `sub_page='document_save'`
- `module='event_handling'`, `sub_page='event_create'`
- `module='event_handling'`, `sub_page='event_log'`
- `module='change_management'`, `sub_page='change_create'` (when model exists)
- `module='change_management'`, `sub_page='change_update'` (when model exists)

Each configuration should have:
- `checklist_status=True` (enabled)
- `retention_days=<number>` (e.g., 210 days)

---

## Files Modified

- `grc_backend/grc/models.py` - Added 4 new signal handlers








