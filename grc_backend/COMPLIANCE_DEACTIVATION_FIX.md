# Compliance Deactivation Fix

## Issue Description

When a compliance deactivation request was approved through the general `submit_compliance_review` endpoint (instead of the specific `approve_compliance_deactivation` endpoint), the compliance record was incorrectly set to `ActiveInactive = 'Active'` instead of `'Inactive'`.

## Root Cause

The `submit_compliance_review` function in `compliance_views.py` was designed for regular compliance approvals and always set `ActiveInactive = 'Active'` when approving, regardless of whether the request was a deactivation request or a regular compliance approval.

## Fix Applied

Updated `submit_compliance_review` function to:

1. **Detect deactivation requests** by checking:
   - `extracted_data.get('type') == 'compliance_deactivation'`
   - `extracted_data.get('RequestType') == 'Change Status to Inactive'`
   - `'COMP-DEACTIVATE' in approval.Identifier`

2. **Fix compliance lookup for deactivation requests**:
   - **Problem**: For deactivation requests, approval `Identifier` is `COMP-DEACTIVATE-{compliance_identifier}`, but compliance `Identifier` is just `{compliance_identifier}`
   - **Solution**: For deactivation requests, use `compliance_id` from `ExtractedData` to find the compliance directly by `ComplianceId`
   - **Fallback**: If not found by `compliance_id`, try finding by the actual compliance identifier from `ExtractedData.identifier`

3. **Handle deactivation requests differently**:
   - If approved: Set `ActiveInactive = 'Inactive'` (instead of `'Active'`)
   - If rejected: Set `ActiveInactive = 'Inactive'` (same as before)

4. **Maintain regular approval behavior**:
   - For regular compliance approvals: Use `Identifier` to find compliance and set `ActiveInactive = 'Active'` (unchanged)

## Code Changes

### Location: `grc_backend/grc/routes/Compliance/compliance_views.py`

**Lines 2320-2342**: 
- Added deactivation request detection at the start
- Updated compliance lookup to use `compliance_id` from `ExtractedData` for deactivation requests
- Fallback to `Identifier` lookup for regular approvals

**Lines 2344-2378**: 
- Updated compliance status update logic to check for deactivation requests
- Set `ActiveInactive = 'Inactive'` for approved deactivation requests
- Set `ActiveInactive = 'Active'` for regular approvals

**Lines 2412-2450**: 
- Enhanced error handling with fallback lookup using actual compliance identifier
- Updated alternative compliance path to also check for deactivation requests

## Fixing Existing Data

For compliances that were already incorrectly approved (e.g., ComplianceId: 4337, 4338), you have options:

### Option 1: Manual Database Update

```sql
-- Fix specific compliance
UPDATE grc2.compliance 
SET ActiveInactive = 'Inactive' 
WHERE ComplianceId = 4338 
  AND ActiveInactive = 'Active';

-- Or fix all incorrectly approved deactivations
UPDATE grc2.compliance c
INNER JOIN grc2.complianceapproval ca ON c.ComplianceId = JSON_EXTRACT(ca.ExtractedData, '$.compliance_id')
SET c.ActiveInactive = 'Inactive'
WHERE ca.Identifier LIKE 'COMP-DEACTIVATE-%'
  AND ca.ApprovedNot = 1
  AND JSON_EXTRACT(ca.ExtractedData, '$.type') = 'compliance_deactivation'
  AND c.ActiveInactive = 'Active';
```

### Option 2: Re-approve the Deactivation

1. Reject the current approval (if possible)
2. Re-submit the deactivation request
3. Approve it - now both endpoints (`submit_compliance_review` and `approve_compliance_deactivation`) will work correctly

### Option 3: Create a Fix Script

Create a script to find and fix all incorrectly approved deactivation requests:

```python
# fix_deactivation_approvals.py
from grc.models import Compliance, ComplianceApproval
import json

# Find all approved deactivation requests
deactivation_approvals = ComplianceApproval.objects.filter(
    Identifier__startswith='COMP-DEACTIVATE',
    ApprovedNot=True
)

fixed_count = 0
not_found_count = 0
already_inactive_count = 0

for approval in deactivation_approvals:
    extracted_data = approval.ExtractedData
    compliance_id = extracted_data.get('compliance_id')
    
    if compliance_id:
        try:
            compliance = Compliance.objects.get(ComplianceId=compliance_id)
            if compliance.ActiveInactive == 'Active':
                print(f"Fixing compliance {compliance_id} ({compliance.Identifier}) - was Active, should be Inactive")
                compliance.ActiveInactive = 'Inactive'
                compliance.save()
                fixed_count += 1
                print(f"✅ Fixed compliance {compliance_id}")
            else:
                already_inactive_count += 1
                print(f"ℹ️ Compliance {compliance_id} already inactive")
        except Compliance.DoesNotExist:
            not_found_count += 1
            print(f"⚠️ Compliance {compliance_id} not found")
    else:
        print(f"⚠️ No compliance_id in approval {approval.ApprovalId}")

print(f"\n=== Summary ===")
print(f"Fixed: {fixed_count}")
print(f"Already inactive: {already_inactive_count}")
print(f"Not found: {not_found_count}")
```

## Testing

After applying the fix, test the following scenarios:

1. **Deactivation Request via General Endpoint**:
   - Submit deactivation request
   - Approve via `submit_compliance_review`
   - Verify: `ActiveInactive = 'Inactive'`

2. **Deactivation Request via Specific Endpoint**:
   - Submit deactivation request
   - Approve via `approve_compliance_deactivation`
   - Verify: `ActiveInactive = 'Inactive'`

3. **Regular Compliance Approval**:
   - Submit regular compliance approval
   - Approve via `submit_compliance_review`
   - Verify: `ActiveInactive = 'Active'`

## Prevention

To prevent this issue in the future:

1. **Frontend**: Ensure deactivation requests use the specific deactivation approval endpoint
2. **Backend**: The fix ensures both endpoints work correctly
3. **Validation**: Add validation to prevent deactivation requests from being processed as regular approvals

## Related Files

- `grc_backend/grc/routes/Compliance/compliance_views.py` - Main fix location
- `grc_backend/COMPLIANCE_DEACTIVATION_GUIDE.md` - Complete deactivation documentation

## Status

✅ **Fixed**: The code now correctly:
1. Detects deactivation requests
2. Finds compliance records using `compliance_id` for deactivation requests
3. Sets `ActiveInactive = 'Inactive'` when deactivation is approved
4. Works correctly in both `submit_compliance_review` and `approve_compliance_deactivation` endpoints

⚠️ **Action Required**: Fix existing incorrectly approved deactivations (e.g., ComplianceId: 4337, 4338) using one of the options above.
