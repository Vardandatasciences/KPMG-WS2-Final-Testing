# Retention Expiry Coverage Analysis

## Summary
**❌ NO - Not every data operation will automatically set `retentionExpiry`**

Many pages/endpoints listed in the Vue components do NOT have corresponding signal handlers to set retention expiry dates.

---

## ✅ Modules/Pages WITH Signal Handlers (Will Set retentionExpiry)

### POLICY Module
| Page Key | Model | Signal Handler | Status |
|----------|-------|----------------|--------|
| `policy_create` | Policy | ✅ set_policy_retention_expiry | ✓ |
| `policy_update` | Policy | ✅ set_policy_retention_expiry | ✓ |
| `policy_version_create` | PolicyVersion | ✅ set_policy_version_retention_expiry | ✓ |
| `policy_approval` | PolicyApproval | ✅ set_policy_approval_retention_expiry | ✓ |
| `policy_subpolicy_add` | SubPolicy | ✅ set_subpolicy_retention_expiry | ✓ |
| `framework_create` | Framework | ✅ set_framework_retention_expiry | ✓ |
| `framework_update` | Framework | ✅ set_framework_retention_expiry | ✓ |
| `framework_version_create` | FrameworkVersion | ✅ set_framework_version_retention_expiry | ✓ |
| `framework_approval` | FrameworkApproval | ✅ set_framework_approval_retention_expiry | ✓ |
| `save_policy_category` | PolicyCategory | ✅ set_policy_category_retention_expiry | ✓ |

### COMPLIANCE Module
| Page Key | Model | Signal Handler | Status |
|----------|-------|----------------|--------|
| `compliance_create` | Compliance | ✅ set_compliance_retention_expiry | ✓ |
| `compliance_edit` | Compliance | ✅ set_compliance_retention_expiry | ✓ |
| `compliance_category_add` | Category | ✅ set_category_retention_expiry | ✓ |
| `compliance_category_bu_add` | CategoryBusinessUnit | ✅ set_category_bu_retention_expiry | ✓ |

### AUDIT Module
| Page Key | Model | Signal Handler | Status |
|----------|-------|----------------|--------|
| `audit_create` | Audit | ✅ set_audit_retention_expiry | ✓ |
| `audit_status_update` | Audit | ✅ set_audit_retention_expiry | ✓ |
| `audit_version_save` | AuditVersion | ✅ set_audit_version_retention_expiry | ✓ |
| `audit_finding_update` | AuditFinding | ✅ set_audit_finding_retention_expiry | ✓ |

### INCIDENT Module
| Page Key | Model | Signal Handler | Status |
|----------|-------|----------------|--------|
| `incident_create` | Incident | ✅ set_incident_retention_expiry | ✓ |
| `incident_update` | Incident | ✅ set_incident_retention_expiry | ✓ |
| `incident_workflow_create` | Workflow | ✅ set_workflow_retention_expiry | ✓ |

### RISK Module
| Page Key | Model | Signal Handler | Status |
|----------|-------|----------------|--------|
| `risk_create` | Risk | ✅ set_risk_retention_expiry | ✓ |
| `risk_update` | Risk | ✅ set_risk_retention_expiry | ✓ |
| `risk_instance_create` | RiskInstance | ✅ set_risk_instance_retention_expiry | ✓ |
| `risk_instance_update` | RiskInstance | ✅ set_risk_instance_retention_expiry | ✓ |

---

## ❌ Modules/Pages WITHOUT Signal Handlers (Will NOT Set retentionExpiry)

### POLICY Module - Missing Handlers
| Page Key | Expected Model | Status | Action Required |
|----------|---------------|--------|-----------------|
| `policy_acknowledgement` | PolicyAcknowledgementRequest | ❌ Missing | Add signal handler |
| `policy_templating` | Policy (tailored) | ❌ Missing | Add signal handler |
| `save_policy_details` | Policy | ❌ Missing | Uses existing handler (policy_create/update) |
| `save_framework_to_db` | Framework | ❌ Missing | Uses existing handler (framework_create) |
| `save_policies` | Policy (bulk) | ❌ Missing | May not trigger signals properly |
| `save_single_policy` | Policy | ❌ Missing | Uses existing handler (policy_create) |
| `create_framework_approval` | FrameworkApproval | ❌ Missing | Uses existing handler (framework_approval) |

### AUDIT Module - Missing Handlers
| Page Key | Expected Model | Status | Action Required |
|----------|---------------|--------|-----------------|
| `audit_add_compliance` | Audit (many-to-many) | ❌ Missing | May not trigger save |
| `audit_review_progress` | Audit | ❌ Missing | Should use audit_status_update handler |

### INCIDENT Module - Missing Handlers
| Page Key | Expected Model | Status | Action Required |
|----------|---------------|--------|-----------------|
| `incident_status_update` | Incident | ❌ Missing | Should use incident_update handler |
| `incident_from_audit` | Incident | ❌ Missing | Should use incident_create handler |
| `incident_category_add` | Category/IncidentCategory | ❌ Missing | Add signal handler |

### RISK Module - Missing Handlers
| Page Key | Expected Model | Status | Action Required |
|----------|---------------|--------|-----------------|
| `risk_status_update` | Risk/RiskInstance | ❌ Missing | Should use risk_update handler |
| `risk_mitigation_update` | Risk/RiskInstance | ❌ Missing | Should use risk_update handler |
| `risk_category_add` | Category | ❌ Missing | Add signal handler |

### DOCUMENT_HANDLING Module - Missing Handlers
| Page Key | Expected Model | Status | Action Required |
|----------|---------------|--------|-----------------|
| `document_upload` | AuditDocument/S3File | ❌ Missing | Add signal handler |
| `document_save` | AuditDocument | ❌ Missing | Add signal handler |

### CHANGE_MANAGEMENT Module - Missing Handlers
| Page Key | Expected Model | Status | Action Required |
|----------|---------------|--------|-----------------|
| `change_create` | ChangeRequest (Model?) | ❌ Missing | Model may not exist |
| `change_update` | ChangeRequest (Model?) | ❌ Missing | Model may not exist |

### EVENT_HANDLING Module - Missing Handlers
| Page Key | Expected Model | Status | Action Required |
|----------|---------------|--------|-----------------|
| `event_create` | Event | ❌ Missing | **Event model exists but NO signal handler** |
| `event_log` | Event | ❌ Missing | Should use event_create handler |

---

## ⚠️ Important Notes

### 1. Signal Handler Mismatch
- **Audit handler uses `create_audit`** but Vue component uses `audit_create`
- These may not match! Check if the page_key mapping is correct.

### 2. Missing Event Model Handler
The `Event` model (line 1896) has `retentionExpiry` field but **NO signal handler exists** to set it automatically.

### 3. How retentionExpiry is Set
The `_set_retention_expiry()` function:
1. Calls `compute_retention_expiry(module_key, page_key)`
2. Looks up `RetentionModulePageConfig` table for the module/page combination
3. Returns `current_date + retention_days` (default 210 days if not found)
4. Updates the model instance's `retentionExpiry` field

### 4. Models with retentionExpiry Field but No Handlers
These models have the field but no automatic handlers:
- Event (has field, no handler)
- AuditDocument (has field, no handler)
- S3File (has field, no handler)
- Many other models have the field but no handlers

---

## 🔧 Recommended Actions

### Immediate Fixes Needed:

1. **Add Event Model Signal Handler:**
```python
@receiver(post_save, sender=Event)
def set_event_retention_expiry(sender, instance, created, **kwargs):
    page_key = 'event_create' if created else 'event_update'
    _set_retention_expiry(instance, 'event_handling', page_key)
```

2. **Fix Audit page_key mismatch:**
```python
@receiver(post_save, sender=Audit)
def set_audit_retention_expiry(sender, instance, created, **kwargs):
    page_key = 'audit_create' if created else 'audit_status_update'  # Changed from 'create_audit'
    _set_retention_expiry(instance, 'audit', page_key)
```

3. **Add PolicyAcknowledgementRequest handler:**
```python
@receiver(post_save, sender=PolicyAcknowledgementRequest)
def set_policy_acknowledgement_retention_expiry(sender, instance, created, **kwargs):
    if created:
        _set_retention_expiry(instance, 'policy', 'policy_acknowledgement')
```

4. **Add AuditDocument handler:**
```python
@receiver(post_save, sender=AuditDocument)
def set_audit_document_retention_expiry(sender, instance, created, **kwargs):
    page_key = 'document_upload' if created else 'document_save'
    _set_retention_expiry(instance, 'document_handling', page_key)
```

---

## 📊 Coverage Statistics

- **Total Pages in Vue Components:** ~45 pages
- **Pages WITH Signal Handlers:** ~22 pages (49%)
- **Pages WITHOUT Signal Handlers:** ~23 pages (51%)
- **Coverage:** ❌ **INCOMPLETE**

---

## ✅ Conclusion

**No, not every data operation will automatically add a date to the `retentionExpiry` column.**

Only **about 49% of the pages** listed in the Vue components have corresponding signal handlers. You need to add signal handlers for the missing pages/models to ensure complete coverage.








