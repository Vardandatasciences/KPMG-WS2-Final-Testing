# Compliance Deactivation Guide

## Overview

This document describes how compliance deactivation works in the GRC system, including what entities should be deactivated, the approval workflow, and cascading effects.

## Table of Contents

1. [Deactivation Prerequisites](#deactivation-prerequisites)
2. [What Gets Deactivated](#what-gets-deactivated)
3. [Deactivation Workflow](#deactivation-workflow)
4. [Cascade Options](#cascade-options)
5. [Related Entities Impact](#related-entities-impact)
6. [Version Management](#version-management)
7. [Approval Process](#approval-process)
8. [Reactivation](#reactivation)

---

## Deactivation Prerequisites

### Conditions for Deactivation

A compliance item can only be deactivated if:

1. **Status is "Approved"**: Only approved compliances can be deactivated
   - Compliances with status "Under Review" or "Rejected" cannot be deactivated
   - The system validates this before allowing deactivation

2. **ActiveInactive is "Active"**: Only currently active compliances can be deactivated
   - Inactive compliances are already deactivated and cannot be deactivated again
   - This prevents duplicate deactivation requests

3. **User Permissions**: User must have `ComplianceDeactivatePermission`
   - RBAC (Role-Based Access Control) must grant deactivation rights
   - Permission is checked via `compliance_deactivate_required` decorator

4. **Required Information**:
   - **Deactivation Reason**: Mandatory text field explaining why the compliance is being deactivated
   - **Reviewer ID**: Must select an approver who will review the deactivation request
   - **User ID**: The user requesting deactivation (typically from session/localStorage)

---

## What Gets Deactivated

### Primary Entity: Compliance

When a compliance is deactivated, the following changes occur:

1. **Compliance Record**:
   - `ActiveInactive` field changes from `'Active'` to `'Inactive'`
   - `Status` remains `'Approved'` (does not change)
   - All other compliance fields remain unchanged
   - Compliance history and version information is preserved

2. **Compliance Identifier**:
   - The compliance `Identifier` remains the same
   - Version history is maintained
   - Previous version relationships (`PreviousComplianceVersionId`) are preserved

### Related Entities (Cascade Effects)

When a compliance is deactivated, the following related entities should be considered:

#### 1. Risk Records

**Relationship**: `Risk.ComplianceId` → `Compliance.ComplianceId`

**Impact**:
- Risk records are automatically created when a compliance becomes "Approved" and "Active"
- When compliance is deactivated, related Risk records should be handled based on business rules:
  - **Option A (Recommended)**: Mark related risks as inactive or archive them
  - **Option B**: Keep risks active but flag them as "orphaned" or "compliance-deactivated"
  - **Option C**: Delete risk records (not recommended - loses audit trail)

**Current Behavior**:
- Risk records are created/updated when compliance is `Status='Approved'` AND `ActiveInactive='Active'`
- When compliance is deactivated, risk records are not automatically updated
- **Recommendation**: Implement logic to mark related risks as inactive when compliance is deactivated

#### 2. Audit Findings

**Relationship**: `AuditFinding.ComplianceId` → `Compliance.ComplianceId`

**Impact**:
- Audit findings linked to the compliance should be reviewed
- **Recommendation**: 
  - Mark audit findings as "Compliance Deactivated" or "Stale"
  - Prevent new audit findings from being created for inactive compliances
  - Keep historical audit findings for compliance purposes

#### 3. Audit Documents

**Relationship**: `AuditDocument.ComplianceId` → `Compliance.ComplianceId`

**Impact**:
- Documents linked to the compliance remain in the system
- **Recommendation**: 
  - Documents should remain accessible for audit purposes
  - Consider adding a flag or metadata indicating compliance is inactive
  - Do not delete documents (maintains audit trail)

#### 4. Baseline Configurations

**Relationship**: `BaselineConfiguration.ComplianceId` → `Compliance.ComplianceId`

**Impact**:
- Baseline settings for the compliance should be reviewed
- **Recommendation**:
  - Mark baseline configurations as inactive or archived
  - Prevent new baseline configurations for inactive compliances
  - Preserve historical baseline data

#### 5. Organization Controls

**Relationship**: `OrgControl.ComplianceId` → `Compliance.ComplianceId`

**Impact**:
- Organization controls linked to the compliance should be handled
- **Recommendation**:
  - Review and potentially deactivate related org controls
  - Maintain historical relationships for reporting

#### 6. Policies and SubPolicies (Cascade Option)

**Relationship**: `Compliance.SubPolicy` → `SubPolicy.SubPolicyId` → `Policy.PolicyId`

**Impact** (when `cascade_to_policies` is enabled):
- If the compliance is the only active compliance for a SubPolicy, consider deactivating the SubPolicy
- If the SubPolicy is the only active sub-policy for a Policy, consider deactivating the Policy
- **Recommendation**: 
  - This should be an optional cascade (user choice)
  - Only deactivate parent entities if no other active compliances/sub-policies exist
  - Provide warnings before cascading to parent entities

---

## Deactivation Workflow

### Step 1: User Initiates Deactivation

1. User navigates to Compliance Versioning page
2. User clicks the toggle switch for an active compliance
3. System validates:
   - Compliance status is "Approved"
   - Compliance is currently "Active"
   - User has deactivation permissions

### Step 2: Deactivation Dialog

The system displays a deactivation dialog requiring:

1. **Deactivation Reason** (Required):
   - Text input field
   - Minimum length validation
   - Should capture business justification

2. **Cascade to Policies** (Optional checkbox):
   - Default: `true` (checked)
   - When enabled: Also deactivates related SubPolicies/Policies if appropriate
   - When disabled: Only deactivates the compliance

3. **Reviewer Selection** (Required):
   - Dropdown or search field to select approver
   - Must be a user with `ComplianceApprovePermission`

### Step 3: Create Deactivation Request

When user submits the deactivation request:

1. **Create ComplianceApproval Record**:
   - `Identifier`: `"COMP-DEACTIVATE-{compliance.Identifier}"`
   - `Version`: Auto-incremented user version (e.g., "u1", "u2", ...)
   - `UserId`: User requesting deactivation
   - `ReviewerId`: Selected reviewer
   - `ApprovedNot`: `None` (pending approval)
   - `ExtractedData`: Contains deactivation metadata:
     ```json
     {
       "type": "compliance_deactivation",
       "compliance_id": <compliance_id>,
       "identifier": <compliance_identifier>,
       "version": <compliance_version>,
       "reason": "<deactivation_reason>",
       "current_status": "Active",
       "requested_status": "Inactive",
       "RequestType": "Change Status to Inactive",
       "cascade_to_policies": "Yes" | "No",
       "affected_policies_count": <count>
     }
     ```

2. **Send Notification**:
   - Email notification sent to reviewer
   - In-app notification created
   - Notification includes compliance details and deactivation reason

3. **Response to User**:
   - Success message: "Deactivation request submitted successfully. Awaiting approval."
   - Approval ID returned for tracking

### Step 4: Reviewer Approval Process

1. **Reviewer Receives Notification**:
   - Email and in-app notification about pending deactivation request
   - Reviewer can view compliance details and reason

2. **Reviewer Reviews Request**:
   - Access Compliance Approval page
   - View deactivation request details
   - Review affected entities and cascade options

3. **Reviewer Decision**:

   **If Approved**:
   - Call `approve_compliance_deactivation(approval_id)`
   - System updates compliance:
     - `ActiveInactive = 'Inactive'`
     - Compliance saved
   - Create reviewer version (e.g., "r1", "r2", ...)
   - Update `ComplianceApproval` record:
     - `ApprovedNot = True`
     - `Version` updated to reviewer version
   - Send notification to requester: "Your request to deactivate this compliance item has been approved."
   - **Cascade Effects** (if enabled):
     - Process related entities as per cascade rules
     - Update Risk records
     - Update Audit Findings
     - Update Baseline Configurations
     - Potentially deactivate SubPolicies/Policies

   **If Rejected**:
   - Call rejection endpoint with remarks
   - System updates `ComplianceApproval`:
     - `ApprovedNot = False`
     - Remarks stored
   - Compliance remains active
   - Send notification to requester: "Your request to deactivate this compliance item has been rejected. Reason: {remarks}"

---

## Cascade Options

### Cascade to Policies (`cascade_to_policies`)

When `cascade_to_policies` is enabled, the system should:

1. **Check SubPolicy Dependencies**:
   - Count active compliances for the SubPolicy
   - If count = 0 (this was the last active compliance):
     - Mark SubPolicy as inactive
     - Check Policy dependencies

2. **Check Policy Dependencies**:
   - Count active SubPolicies for the Policy
   - If count = 0 (this was the last active SubPolicy):
     - Mark Policy as inactive
     - Check Framework dependencies (optional)

3. **Warnings**:
   - Show user which entities will be affected
   - Display count of affected compliances, sub-policies, and policies
   - Require confirmation before proceeding

4. **Implementation Notes**:
   - Cascade should be reversible (can reactivate)
   - Maintain audit trail of cascade actions
   - Log all cascade operations for compliance purposes

### Cascade to Risk Records

**Recommended Behavior**:

1. **Find Related Risks**:
   ```python
   related_risks = Risk.objects.filter(ComplianceId=compliance_id)
   ```

2. **Update Risk Status**:
   - Option 1: Add `ActiveInactive` field to Risk model and set to 'Inactive'
   - Option 2: Add `ComplianceStatus` field to track compliance state
   - Option 3: Create a flag like `IsComplianceActive` in Risk model

3. **Preserve Risk Data**:
   - Do not delete risk records
   - Maintain historical risk data for reporting
   - Allow reactivation of risks when compliance is reactivated

---

## Related Entities Impact

### Entity Relationship Diagram

```
Framework
  └── Policy
       └── SubPolicy
            └── Compliance (being deactivated)
                 ├── Risk (ComplianceId)
                 ├── AuditFinding (ComplianceId)
                 ├── AuditDocument (ComplianceId)
                 ├── BaselineConfiguration (ComplianceId)
                 └── OrgControl (ComplianceId)
```

### Impact Matrix

| Entity | Relationship | Action on Deactivation | Reversible |
|--------|-------------|----------------------|------------|
| **Compliance** | Primary | Set `ActiveInactive = 'Inactive'` | Yes |
| **Risk** | `ComplianceId` FK | Mark as inactive/archived | Yes |
| **AuditFinding** | `ComplianceId` FK | Mark as stale, prevent new findings | Partial |
| **AuditDocument** | `ComplianceId` FK | Preserve, add metadata flag | N/A |
| **BaselineConfiguration** | `ComplianceId` FK | Mark as inactive | Yes |
| **OrgControl** | `ComplianceId` FK | Review and potentially deactivate | Yes |
| **SubPolicy** | `SubPolicy` FK (parent) | Optional cascade if no other active compliances | Yes |
| **Policy** | Via SubPolicy | Optional cascade if no other active sub-policies | Yes |

---

## Version Management

### Version Tracking

1. **Compliance Versions**:
   - Compliance version (e.g., "1.0", "1.1") remains unchanged
   - Version history is preserved
   - Previous version relationships maintained

2. **Approval Versions**:
   - User version: "u1", "u2", ... (created when user submits request)
   - Reviewer version: "r1", "r2", ... (created when reviewer approves/rejects)
   - Version sequence: u1 → r1 → u2 → r2 (if multiple iterations)

3. **Deactivation Identifier**:
   - Format: `"COMP-DEACTIVATE-{compliance.Identifier}"`
   - Unique per deactivation request
   - Allows multiple deactivation requests for same compliance (if reactivated)

### Version History

- All deactivation requests are tracked in `ComplianceApproval` table
- Can query deactivation history by identifier pattern
- Supports audit trail and compliance reporting

---

## Approval Process

### Approval States

1. **Pending**: `ApprovedNot = None`
   - Request submitted, awaiting reviewer action

2. **Approved**: `ApprovedNot = True`
   - Reviewer approved, compliance deactivated
   - Compliance `ActiveInactive = 'Inactive'`

3. **Rejected**: `ApprovedNot = False`
   - Reviewer rejected, compliance remains active
   - Remarks stored explaining rejection

### Approval Workflow Diagram

```
User Request
    ↓
Create ComplianceApproval (ApprovedNot = None)
    ↓
Notify Reviewer
    ↓
Reviewer Reviews
    ↓
    ├── Approve → Update Compliance (ActiveInactive = 'Inactive')
    │                ↓
    │            Notify User (Approved)
    │                ↓
    │            Process Cascade Effects (if enabled)
    │
    └── Reject → Update ComplianceApproval (ApprovedNot = False)
                     ↓
                 Notify User (Rejected)
```

---

## Reactivation

### Reactivation Process

A deactivated compliance can be reactivated:

1. **Prerequisites**:
   - Compliance must be in "Inactive" state
   - Status should be "Approved" (or may require re-approval)
   - User must have activation permissions

2. **Reactivation Methods**:
   - **Method 1**: Use toggle switch (if compliance is inactive)
   - **Method 2**: Create new version (recommended for version tracking)
   - **Method 3**: Direct activation via API (if permissions allow)

3. **Reactivation Effects**:
   - Set `ActiveInactive = 'Active'`
   - Reactivate related Risk records (if they were deactivated)
   - Update Audit Findings status
   - Restore Baseline Configurations
   - Notify relevant stakeholders

4. **Version Considerations**:
   - If reactivating same version: Simply toggle status
   - If creating new version: Follow normal versioning workflow
   - Previous version remains in history

---

## Implementation Recommendations

### 1. Risk Record Handling

**Current Gap**: Risk records are not automatically updated when compliance is deactivated.

**Recommendation**: 
- Add logic in `approve_compliance_deactivation` to update related Risk records
- Consider adding `ActiveInactive` or `ComplianceStatus` field to Risk model
- Preserve risk data for historical reporting

### 2. Cascade Implementation

**Current Gap**: Cascade to policies is mentioned but not fully implemented.

**Recommendation**:
- Implement cascade logic in `approve_compliance_deactivation`
- Add validation to check dependencies before cascading
- Show user preview of what will be affected
- Log all cascade operations

### 3. Audit Trail

**Recommendation**:
- Log all deactivation requests and approvals
- Track who requested, who approved, when, and why
- Maintain history for compliance reporting
- Export deactivation history for audits

### 4. Notifications

**Current**: Basic email notifications exist.

**Recommendation**:
- Enhance notifications with more details
- Include affected entity counts
- Provide direct links to approval page
- Support multiple notification channels

### 5. Validation Rules

**Recommendation**:
- Validate that deactivation won't break critical dependencies
- Check if compliance is referenced in active audits
- Warn if compliance is part of active risk assessments
- Prevent deactivation if compliance is required by framework

---

## Summary

### What Should Be Deactivated

1. **Primary**: Compliance record (`ActiveInactive = 'Inactive'`)
2. **Related Risks**: Mark as inactive (preserve data)
3. **Audit Findings**: Mark as stale, prevent new findings
4. **Baseline Configurations**: Mark as inactive
5. **Org Controls**: Review and potentially deactivate
6. **SubPolicies/Policies**: Optional cascade (if no other active dependencies)

### What Should NOT Be Deactivated

1. **Audit Documents**: Preserve for audit trail
2. **Compliance History**: Maintain version history
3. **Approval Records**: Keep all approval history
4. **Risk Historical Data**: Preserve for reporting

### Key Principles

1. **Preserve Audit Trail**: Never delete data, only mark as inactive
2. **Reversibility**: All deactivations should be reversible
3. **Transparency**: Clear visibility into what will be affected
4. **Approval Required**: All deactivations require approval workflow
5. **Cascade Control**: User should control cascade behavior
6. **Multi-tenancy**: Respect tenant isolation in all operations

---

## Questions for Business Stakeholders

1. Should Risk records be automatically deactivated when compliance is deactivated?
2. Should cascade to Policies be mandatory or optional?
3. What happens to active audits referencing the compliance?
4. Should there be a grace period before deactivation takes effect?
5. Can deactivated compliances be referenced in new compliance items?
6. Should there be different deactivation types (temporary vs. permanent)?

---

## Related Documentation

- Compliance Versioning: See `compliance_views.py` - `toggle_compliance_version`
- Approval Workflow: See `compliance_views.py` - `approve_compliance_deactivation`
- Risk Management: See `models.py` - `Risk` model and signal handlers
- Multi-tenancy: See `MULTITENANCY_DOCUMENTATION.md`

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-12  
**Author**: GRC Development Team
