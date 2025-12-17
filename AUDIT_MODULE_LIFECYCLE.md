# Audit Module - Complete Lifecycle Documentation

## Table of Contents
1. [Quick Start: How Audits Work](#quick-start-how-audits-work)
2. [Regular Audit vs AI Audit: Key Differences](#regular-audit-vs-ai-audit-key-differences)
3. [Overview](#overview)
4. [Database Tables and Models](#database-tables-and-models)
5. [Complete Lifecycle Stages](#complete-lifecycle-stages)
6. [Status Transitions](#status-transitions)
7. [Key Functionalities](#key-functionalities)
8. [Data Flow and Storage](#data-flow-and-storage)
9. [API Endpoints](#api-endpoints)
10. [Related Modules](#related-modules)

---

## Quick Start: How Audits Work

### Simple Step-by-Step Process

#### **Step 1: Create & Assign Audit**
- Admin creates an audit with:
  - Title, scope, objective
  - Framework/Policy/SubPolicy selection
  - Assigns auditors (team members)
  - Assigns reviewer
  - Sets due date
- System automatically:
  - Creates audit record(s) in database
  - Finds all compliances based on selection
  - Creates audit findings (one per compliance)
  - Sets status: **"Yet to Start"**

#### **Step 2: Auditor Works on Audit**
- Auditor sees assigned audit in "My Audits"
- Auditor updates each finding:
  - Adds evidence (documents, screenshots, links)
  - Sets compliance status (Compliant/Not Compliant/Partially Compliant)
  - Adds comments and details
  - Sets criticality (Major/Minor)
- System updates:
  - Status changes to **"Work In Progress"**
  - Auditor can save versions (A1, A2, A3...) as they work

#### **Step 3: Submit for Review**
- Auditor completes all findings
- Clicks "Submit for Review"
- System updates:
  - Status changes to **"Under review"**
  - ReviewStartDate is set
  - Reviewer gets notification

#### **Step 4: Reviewer Reviews**
- Reviewer sees audit in "My Reviews"
- Reviewer examines each finding:
  - Reviews evidence
  - Checks compliance status
  - Can approve or reject individual findings
  - Adds review comments
- Reviewer makes decision:
  - **Approve**: Audit is accepted
  - **Reject**: Audit sent back to auditor for revision

#### **Step 5A: If Approved**
- System automatically:
  1. Updates status to **"Completed"**
  2. Updates all findings with review data
  3. Generates audit report (Word document)
  4. Uploads report to S3
  5. Creates incidents for non-compliant findings
  6. Updates `lastchecklistitemverified` table (tracks compliance history)
  7. Sends notifications to auditor and assignee

#### **Step 5B: If Rejected**
- System automatically:
  1. Changes status back to **"Work In Progress"**
  2. Resets review status
  3. Adds rejection comments
  4. Sends notification to auditor
- Process returns to **Step 2** (Auditor revises and resubmits)

---

## Regular Audit vs AI Audit: Key Differences

### **Regular Audit (Manual Audit)**

**How It Works:**
1. **Assignment**: Admin assigns audit to specific auditors (team members)
2. **Manual Work**: Auditor manually:
   - Reviews each compliance requirement
   - Collects evidence manually
   - Fills out findings form
   - Determines compliance status
   - Writes comments and recommendations
3. **Review**: Reviewer manually reviews all findings
4. **Completion**: Standard approval/rejection process

**Characteristics:**
- ✅ Human-driven process
- ✅ Requires auditor expertise
- ✅ Time-intensive (manual data entry)
- ✅ Full control over findings
- ✅ Suitable for complex, nuanced audits

**Use Cases:**
- Detailed compliance reviews
- Process audits
- Security audits requiring human judgment
- Custom audit requirements

---

### **AI Audit (AI-Powered Audit)**

**How It Works:**
1. **Assignment**: Admin creates AI audit (no specific auditor needed)
2. **Document Upload**: User uploads documents (PDFs, Word, Excel, etc.)
3. **AI Processing**: System automatically:
   - Extracts text from documents
   - Uses AI (OpenAI) to analyze content
   - Compares against compliance requirements
   - Identifies gaps and non-compliance
   - Generates compliance matrix
   - Creates findings automatically
4. **Review**: Auditor/Reviewer reviews AI-generated findings
5. **Completion**: Standard approval/rejection process

**Characteristics:**
- ✅ AI-driven analysis
- ✅ Fast processing (automated)
- ✅ Consistent analysis
- ✅ Handles large volumes of documents
- ✅ Reduces manual work
- ⚠️ Requires quality documents
- ⚠️ May need human verification

**Use Cases:**
- Document-based compliance checks
- Policy document reviews
- Contract compliance analysis
- Large-scale document audits
- Quick compliance assessments

---

### **Side-by-Side Comparison**

| Aspect | Regular Audit | AI Audit |
|--------|--------------|----------|
| **Assignment** | Multiple auditors (one audit per person) | Single audit (no specific auditor) |
| **Initial Setup** | Creates findings immediately | Creates findings immediately |
| **Work Process** | Manual data entry by auditor | Document upload + AI processing |
| **Evidence Collection** | Manual (auditor collects) | Automated (from uploaded documents) |
| **Compliance Analysis** | Human judgment | AI analysis (OpenAI) |
| **Finding Creation** | Manual (auditor fills forms) | Automated (AI generates) |
| **Time Required** | Days/weeks (depending on scope) | Hours (after document upload) |
| **Human Involvement** | High (throughout process) | Medium (review AI results) |
| **Accuracy** | Depends on auditor expertise | Depends on document quality & AI |
| **Scalability** | Limited by auditor capacity | High (can process many documents) |
| **Cost** | Higher (human resources) | Lower (automated processing) |
| **Best For** | Complex, nuanced audits | Document-heavy, standardized audits |

---

### **When to Use Each Type**

**Use Regular Audit when:**
- You need human expertise and judgment
- Audit requires on-site inspection
- Compliance is complex and context-dependent
- You need detailed interviews or observations
- Audit scope is small and manageable manually

**Use AI Audit when:**
- You have documents to analyze (policies, contracts, reports)
- You need to process many documents quickly
- Compliance requirements are well-defined
- You want consistent, automated analysis
- You need to scale audit operations

---

### **Workflow Comparison**

**Regular Audit Flow:**
```
Create Audit → Assign to Auditors → 
Auditors Work Manually → Submit for Review → 
Reviewer Reviews → Approve/Reject → Complete
```

**AI Audit Flow:**
```
Create AI Audit → Upload Documents → 
AI Processes Documents → AI Generates Findings → 
Reviewer Reviews AI Results → Approve/Reject → Complete
```

---

### **Key Technical Differences**

1. **Audit Creation:**
   - **Regular**: `team_members = [user1, user2, user3]` → Creates 3 separate audits
   - **AI**: `team_members = [None]` → Creates 1 audit

2. **Audit Type Field:**
   - **Regular**: `AuditType = 'R'` (Regular), `'I'` (Internal), `'E'` (External), `'S'` (Self)
   - **AI**: `AuditType = 'A'` (AI)

3. **Finding Population:**
   - **Regular**: Findings created empty, auditor fills manually
   - **AI**: Findings populated automatically by AI after document processing

4. **Evidence:**
   - **Regular**: Auditor manually adds evidence URLs/text
   - **AI**: Evidence extracted from documents automatically

5. **Processing:**
   - **Regular**: No special processing needed
   - **AI**: Requires document upload → text extraction → AI analysis → finding updates

---

## Overview

The Audit Module is a comprehensive system for managing compliance audits within the GRC (Governance, Risk, and Compliance) framework. It supports the complete lifecycle from audit creation through assignment, execution, review, approval/rejection, and completion.

### Key Features
- **Multiple Audit Types**: Regular (R), AI (A), Internal (I), External (E), Self-Audit (S)
- **Version Management**: Tracks audit versions with Auditor (A) and Reviewer (R) versions
- **Compliance-Based Findings**: Automatically creates findings based on compliance requirements
- **Review Workflow**: Supports review, approval, and rejection workflows
- **Incident Generation**: Automatically creates incidents for non-compliant findings
- **Report Generation**: Generates audit reports and stores them in S3

---

## Database Tables and Models

### 1. **audit** Table
Primary table storing audit records.

**Key Fields:**
- `AuditId` (Primary Key): Auto-incrementing ID
- `Title`: Audit title
- `Scope`: Audit scope description
- `Objective`: Audit objective
- `BusinessUnit`: Business unit associated with audit
- `Role`: Role associated with audit
- `Responsibility`: Responsibility description
- `Assignee`: Foreign key to `users` table (assigned user)
- `Auditor`: Foreign key to `users` table (auditor user)
- `Reviewer`: Foreign key to `users` table (reviewer user, nullable)
- `FrameworkId`: Foreign key to `frameworks` table
- `PolicyId`: Foreign key to `policies` table (nullable)
- `SubPolicyId`: Foreign key to `subpolicies` table (nullable)
- `DueDate`: Due date for audit completion
- `Frequency`: Frequency of audit (integer)
- `Status`: Current status (e.g., "Yet to Start", "Work In Progress", "Under review", "Completed")
- `CompletionDate`: Date when audit was completed
- `ReviewStatus`: Review status (0=Yet to Start, 1=In Review, 2=Accept, 3=Reject)
- `ReviewerComments`: Comments from reviewer
- `AuditType`: Type of audit (R/A/I/E/S)
- `Evidence`: Evidence text/URLs
- `Comments`: General comments
- `AssignedDate`: Date when audit was assigned
- `Reports`: JSON field storing report information
- `ReviewStartDate`: Date when review started
- `ReviewDate`: Date when review was completed
- `data_inventory`: JSON field mapping field labels to data types
- `retentionExpiry`: Data retention expiry date

**Database Table Name:** `audit`

---

### 2. **audit_findings** Table
Stores individual compliance findings for each audit.

**Key Fields:**
- `AuditFindingsId` (Primary Key): Auto-incrementing ID
- `AuditId`: Foreign key to `audit` table
- `ComplianceId`: Foreign key to `compliance` table
- `UserId`: Foreign key to `users` table (user who created/updated finding)
- `Evidence`: Evidence text/URLs
- `Check`: Compliance status ('0'=Not Started/Not Compliant, '1'=In Progress/Partially Compliant, '2'=Completed/Compliant, '3'=Not Applicable)
- `MajorMinor`: Criticality ('0'=Minor, '1'=Major, '2'=Not Applicable)
- `HowToVerify`: How to verify compliance
- `Impact`: Impact description
- `Recommendation`: Recommendations
- `DetailsOfFinding`: Details of the finding
- `Comments`: Comments on the finding
- `CheckedDate`: Date when finding was checked
- `AssignedDate`: Date when finding was assigned
- `FrameworkId`: Foreign key to `frameworks` table
- `ReviewStatus`: Review status for the finding
- `ReviewComments`: Reviewer comments
- `ReviewRejected`: Boolean indicating if review was rejected
- `ReviewDate`: Date when finding was reviewed
- `PredictiveRisks`: JSON field storing selected risks
- `CorrectiveActions`: JSON field storing selected mitigations
- `SeverityRating`: Severity rating
- `UnderlyingCause`: Underlying cause of non-compliance
- `WhyToVerify`: Why verification is needed
- `WhatToVerify`: What needs to be verified
- `SuggestedActionPlan`: Suggested action plan
- `MitigationDate`: Date for mitigation
- `ResponsibleForPlan`: Person responsible for action plan
- `ReAudit`: Boolean indicating if re-audit is required
- `ReAuditDate`: Date for re-audit
- `retentionExpiry`: Data retention expiry date

**Database Table Name:** `audit_findings`

---

### 3. **audit_version** Table
Stores version history of audits (both Auditor and Reviewer versions).

**Key Fields:**
- `AuditId`: Foreign key to `audit` table
- `Version`: Version identifier (A1, A2, R1, R2, etc.)
  - **A prefix**: Auditor versions (A1, A2, A3...)
  - **R prefix**: Reviewer versions (R1, R2, R3...)
- `ExtractedInfo`: JSON field containing complete audit findings data
- `UserId`: Foreign key to `users` table (user who created version)
- `Date`: Date when version was created
- `ApproverId`: Foreign key to `users` table (approver, nullable)
- `ApprovedRejected`: Approval status ('Approved', 'Rejected', NULL)
- `ActiveInactive`: Status of version ('A'=Active, 'R'=Review, 'I'=Inactive)
- `FrameworkId`: Foreign key to `frameworks` table

**Database Table Name:** `audit_version`

**Version Structure:**
- **Auditor Versions (A1, A2, ...)**: Created when auditor saves/submits audit findings
- **Reviewer Versions (R1, R2, ...)**: Created when reviewer reviews/approves/rejects audit

---

### 4. **audit_report** Table
Stores generated audit reports.

**Key Fields:**
- `ReportId` (Primary Key): Auto-incrementing ID
- `AuditId`: Foreign key to `audit` table
- `Report`: URL/path to the report file (stored in S3)
- `PolicyId`: Foreign key to `policies` table
- `SubPolicyId`: Foreign key to `subpolicies` table
- `FrameworkId`: Foreign key to `frameworks` table

**Database Table Name:** `audit_report`

---

### 5. **audit_documents** Table
Stores documents uploaded for AI audits.

**Key Fields:**
- `DocumentId` (Primary Key): Auto-incrementing ID
- `AuditId`: Foreign key to `audit` table
- `DocumentName`: Name of the document
- `DocumentPath`: Path/URL to document
- `UploadedBy`: Foreign key to `users` table
- `UploadedDate`: Date when document was uploaded
- `UploadStatus`: Status of upload
- `ProcessingStatus`: AI processing status
- `ProcessingResults`: JSON field with AI analysis results
- `ComplianceMapping`: JSON field mapping document sections to compliance
- `ExtractedText`: Extracted text from document
- `DocumentSummary`: AI-generated summary
- `FrameworkId`: Foreign key to `frameworks` table

**Database Table Name:** `audit_documents`

---

### 6. **lastchecklistitemverified** Table
**Critical table for tracking compliance verification history and audit completion status.**

**Purpose:**
- Tracks the last verification status of each compliance item
- Maintains a count of how many times a compliance has been verified (non-compliant or partially compliant)
- Links audit findings to compliance verification records
- Used for reporting, analytics, and compliance tracking

**Key Fields:**
- `ComplianceId` (Primary Key): Foreign key to `compliance` table
- `SubPolicyId`: Foreign key to `subpolicies` table
- `PolicyId`: Foreign key to `policies` table
- `FrameworkId`: Foreign key to `frameworks` table
- `Date`: Date when compliance was last verified
- `Time`: Time when compliance was last verified
- `User`: User ID who performed the verification
- `Complied`: Compliance status ('0'=Not Compliant, '1'=Partially Compliant/In Progress, '2'=Compliant, '3'=Not Applicable)
- `Comments`: Comments from the verification
- `Count`: Number of times this compliance has been verified (incremented for non-compliant/partially compliant findings)
- `AuditFindingsId`: Foreign key to `audit_findings` table (links to specific finding)
- `retentionExpiry`: Data retention expiry date

**Unique Constraint:**
- `(ComplianceId, SubPolicyId, PolicyId, FrameworkId)` - Ensures one record per compliance in a specific context

**Database Table Name:** `lastchecklistitemverified`

**When Updated:**
- Updated when an audit is **approved** (after review completion)
- Function: `update_lastchecklistitem_verified()` in `checklist_utils.py`
- Called from: `reviewing.py` after audit approval

**Update Logic:**
1. For each audit finding in the approved audit:
   - If record exists for ComplianceId: **UPDATE** with new verification data
   - If record doesn't exist: **INSERT** new record
   - If `Check` value is '0' (Not Compliant) or '1' (Partially Compliant): Increment `Count` field
   - Update all fields: Date, Time, User, Complied, Comments, AuditFindingsId

**Usage:**
- Used in compliance reports to show last verification status
- Used in analytics to track compliance trends
- Used in incident module to show audit findings
- Used in KPI calculations for compliance metrics

---

## Complete Lifecycle Stages

### Stage 1: Audit Creation and Assignment

**Location:** `grc_backend/grc/routes/Audit/assign_audit.py` - `create_audit()`

**Endpoint:** `POST /api/audit/create-audit/`

**Detailed Process:**

#### Step 1: User Input and Form Submission
Admin/Audit Assigner fills out the audit creation form with:
- **Basic Information:**
  - Title: Audit title/name
  - Scope: What areas/processes are being audited
  - Objective: Purpose of the audit
  - Business Unit: Associated business unit
  - Role: Role associated with audit
  - Responsibility: Responsibility description

- **Scope Selection:**
  - Framework: Select framework (required)
  - Policy: Optional - specific policy within framework
  - SubPolicy: Optional - specific subpolicy within policy

- **Audit Configuration:**
  - Due Date: When audit must be completed
  - Frequency: How often audit should be performed (integer)
  - Audit Type: 
    - **Regular (R)**: Standard manual audit
    - **AI (A)**: AI-powered audit using document analysis
    - **Internal (I)**: Internal audit
    - **External (E)**: External audit
    - **Self-Audit (S)**: Self-assessment audit

- **Assignment:**
  - Team Members: List of user IDs to assign as auditors (for non-AI audits)
  - Reviewer: User ID who will review the audit (required)
  - For AI audits: No team members needed (single audit created)

- **Optional Fields:**
  - Reports: JSON field for report selection
  - Data Inventory: JSON mapping field labels to data types (personal, confidential, regular)

#### Step 2: Request Validation
1. **Authentication Check:**
   - Verifies user has `AuditAssignPermission`
   - Checks consent for 'create_audit' action
   - Validates session/JWT token

2. **Data Validation:**
   - Validates all required fields are present
   - Checks framework exists in database
   - Validates policy exists (if provided)
   - Validates subpolicy exists (if provided)
   - Validates reviewer user exists
   - Validates auditor users exist (for non-AI audits)
   - Validates date format (YYYY-MM-DD)
   - Validates frequency is a valid integer

3. **Framework Filter:**
   - Checks if framework filter is active in session
   - Uses framework from request data or session
   - Ensures framework exists before proceeding

#### Step 3: User Object Resolution
1. **Reviewer Resolution:**
   - If reviewer ID provided: Fetches user from database
   - If reviewer empty/invalid: Uses current user as reviewer
   - If current user not found: Falls back to 'admin.grc' user

2. **Auditor Resolution (for non-AI audits):**
   - For each team member ID:
     - Fetches user object from database
     - Validates user exists
     - Creates separate audit for each auditor

3. **AI Audit Special Handling:**
   - If `audit_type == 'AI'`:
     - Sets `team_members_to_process = [None]` (single entry)
     - Uses reviewer as both assignee and auditor
     - Creates single audit record

#### Step 4: Audit Type Normalization
Maps audit type strings to single-letter database codes:
- 'AI' or 'A' → 'A'
- 'INTERNAL' or 'I' → 'I'
- 'EXTERNAL' or 'E' → 'E'
- 'SELF' or 'SELF-AUDIT' or 'S' → 'S'
- 'REGULAR' or 'R' → 'R'
- Default: 'I' (Internal)

#### Step 5: Audit Record Creation
For each team member (or single AI audit):

1. **Build Audit Fields:**
   ```python
   audit_fields = {
       'Title': validated_data['title'],
       'Scope': validated_data['scope'],
       'Objective': validated_data['objective'],
       'BusinessUnit': validated_data.get('business_unit', ''),
       'Role': validated_data['role'],
       'Responsibility': validated_data['responsibility'],
       'Assignee': auditor_obj,  # Same as auditor for most cases
       'Auditor': auditor_obj,
       'Reviewer': reviewer_obj,
       'FrameworkId': framework_obj,
       'PolicyId': policy_obj,  # Can be None
       'SubPolicyId': subpolicy_obj,  # Can be None
       'DueDate': due_date,
       'Frequency': frequency_integer,
       'Status': 'Yet to Start',  # Initial status
       'AuditType': db_audit_type,  # 'A', 'I', 'E', 'S', 'R'
       'AssignedDate': timezone.now(),
       'ReviewStatus': None,
       'ReviewerComments': None,
       'Evidence': '',
       'Comments': '',
       'Reports': data.get('reports', ''),
       'ReviewStartDate': None,
       'ReviewDate': None,
       'CompletionDate': None,
       'data_inventory': data_inventory  # JSON field
   }
   ```

2. **Create Audit Record:**
   - Uses `Audit.objects.create(**audit_fields)`
   - Generates auto-incrementing `AuditId`
   - Stores in `audit` table

3. **AI Audit Special Logging:**
   - If `AuditType == 'A'`:
     - Logs AI audit creation
     - Sets flag indicating document upload needed

#### Step 6: Compliance Retrieval
Based on the scope selection level:

1. **SubPolicy Level** (if SubPolicyId provided):
   ```sql
   SELECT c.* 
   FROM compliance c
   WHERE c.SubPolicyId = %s
   AND c.PermanentTemporary = 'Permanent'
   AND c.Status = 'Approved'
   AND c.ActiveInactive = 'Active'
   ```

2. **Policy Level** (if PolicyId provided, no SubPolicyId):
   ```sql
   SELECT c.* 
   FROM compliance c
   INNER JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
   WHERE sp.PolicyId = %s
   AND c.PermanentTemporary = 'Permanent'
   AND c.Status = 'Approved'
   AND c.ActiveInactive = 'Active'
   ```

3. **Framework Level** (if only FrameworkId provided):
   ```sql
   SELECT c.* 
   FROM compliance c
   INNER JOIN subpolicies sp ON c.SubPolicyId = sp.SubPolicyId
   INNER JOIN policies p ON sp.PolicyId = p.PolicyId
   WHERE p.FrameworkId = %s
   AND c.PermanentTemporary = 'Permanent'
   AND c.Status = 'Approved'
   AND c.ActiveInactive = 'Active'
   ```

**Filter Criteria:**
- `PermanentTemporary = 'Permanent'`: Only permanent compliances (not temporary)
- `Status = 'Approved'`: Only approved compliances
- `ActiveInactive = 'Active'`: Only active compliances

#### Step 7: Audit Findings Creation
For each compliance found:

1. **Create Finding Record:**
   ```sql
   INSERT INTO audit_findings (
       AuditId, ComplianceId, UserId, Evidence, 
       Check, Comments, MajorMinor, AssignedDate, FrameworkId, ReviewRejected
   ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
   ```

2. **Initial Values:**
   - `AuditId`: The newly created audit ID
   - `ComplianceId`: The compliance ID from query
   - `UserId`: Auditor's user ID
   - `Evidence`: Empty string ''
   - `Check`: '0' (Not Started / Not Compliant)
   - `Comments`: Empty string ''
   - `MajorMinor`: NULL
   - `AssignedDate`: Same as audit's AssignedDate
   - `FrameworkId`: From parent audit
   - `ReviewRejected`: 0 (not rejected)

3. **Result:**
   - One `audit_findings` record per compliance
   - All findings linked to the audit
   - Ready for auditor to start work

#### Step 8: Error Handling and Cleanup
- If audit creation fails: Logs error, continues to next team member
- If findings creation fails: Deletes audit record, logs error
- If all audits fail: Returns error response
- If some succeed: Returns success with list of created audit IDs

#### Step 9: Response and Logging
1. **Success Response:**
   ```json
   {
       "message": "Audits created successfully",
       "audits_created": 3,
       "audit_ids": [101, 102, 103],
       "findings_created_per_audit": 25
   }
   ```

2. **Logging:**
   - Logs audit creation attempt
   - Logs successful creation for each audit
   - Logs findings count
   - Logs AI audit special handling (if applicable)
   - Logs any errors encountered

**Tables Updated:**
- `audit`: New audit record(s) created
  - One record per team member (or single for AI audit)
  - Status: 'Yet to Start'
  - AssignedDate: Current timestamp
  
- `audit_findings`: New finding records created
  - One record per compliance found
  - Check: '0' (Not Started)
  - All linked to their respective audits

**Key Differences: AI vs Regular Audits**

| Aspect | Regular Audit | AI Audit |
|--------|--------------|----------|
| Team Members | Multiple auditors (one audit per auditor) | Single audit (no specific auditor) |
| Auditor Assignment | Each team member gets separate audit | Reviewer used as auditor |
| Initial Findings | Created immediately from compliances | Created immediately (same as regular) |
| Next Step | Auditor starts working on findings | Upload documents for AI processing |
| Document Upload | Not required | Required for AI analysis |

---

### Stage 2: Audit Execution (Work In Progress)

**Location:** `grc_backend/grc/routes/Audit/audit_views.py`

**Process:**
1. **Auditor Access**: Auditor views assigned audits via "My Audits"
   - Endpoint: `GET /api/audits/my-audits/`
   - Filters audits where `Auditor = current_user_id`

2. **Status Update**: When auditor starts working:
   - Updates `Status = 'Work In Progress'`
   - Endpoint: `POST /api/audits/{audit_id}/status/`

3. **Finding Updates**: Auditor updates each finding:
   - Updates `Evidence` field
   - Updates `Check` status (0/1/2/3)
   - Updates `Comments`
   - Updates `MajorMinor` (criticality)
   - Updates `HowToVerify`
   - Updates `Impact`, `Recommendation`, `DetailsOfFinding`
   - Endpoint: `POST /api/audit-findings/{compliance_id}/`

4. **Version Creation**: When auditor saves progress:
   - Creates Auditor version (A1, A2, A3...)
   - Stores complete findings data in `ExtractedInfo` JSON field
   - Endpoint: `POST /api/audits/{audit_id}/save-version/`
   - Function: `create_audit_version()` in `audit_views.py`

5. **Version Data Structure**:
   ```json
   {
     "compliance_id_1": {
       "description": "...",
       "status": "0",
       "compliance_status": "Not Compliant",
       "comments": "...",
       "evidence": "...",
       "how_to_verify": "...",
       "impact": "...",
       "details_of_finding": "...",
       "major_minor": "0",
       "selected_risks": [...],
       "selected_mitigations": [...],
       ...
     },
     "__metadata__": {
       "version_date": "...",
       "auditor_id": ...,
       "version_type": "Auditor",
       ...
     }
   }
   ```

**Tables Updated:**
- `audit`: Status updated to "Work In Progress"
- `audit_findings`: Individual findings updated
- `audit_version`: New Auditor version (A1, A2, etc.) created

---

### Stage 3: Submission for Review

**Location:** `grc_backend/grc/routes/Audit/audit_views.py` - `send_audit_for_review()`

**Process:**
1. **Final Save**: Auditor saves final version before submission
   - Creates final Auditor version (e.g., A3)
   - Ensures all findings are updated

2. **Submission**:
   - Updates `Status = 'Under review'`
   - Sets `ReviewStartDate = timezone.now()`
   - Sets `ReviewStatus = 1` (In Review)
   - Endpoint: `POST /api/audits/{audit_id}/send-for-review/`

3. **Notification**:
   - Sends notification to reviewer
   - Notification includes audit details and link

**Tables Updated:**
- `audit`: Status changed to "Under review", ReviewStartDate set, ReviewStatus = 1

---

### Stage 4: Review Process

**Location:** `grc_backend/grc/routes/Audit/reviewing.py` - `update_audit_review_status()`

**Process:**
1. **Reviewer Access**: Reviewer views audits pending review
   - Endpoint: `GET /api/audits/my-reviews/`
   - Filters audits where `Reviewer = current_user_id` AND `Status = 'Under review'`

2. **Review Data Loading**:
   - Loads latest version data from `audit_version` table
   - Endpoint: `GET /api/audits/{audit_id}/review-data/`
   - Function: `load_latest_review_data()`

3. **Review Actions**:
   - Reviewer can review each compliance finding
   - Can add review comments
   - Can approve or reject individual findings
   - Can add overall review comments

4. **Review Version Creation**:
   - When reviewer saves review, creates Reviewer version (R1, R2, etc.)
   - Stores review data in `ExtractedInfo` JSON field
   - Updates `ReviewStatus` in audit_findings

**Tables Updated:**
- `audit_version`: New Reviewer version (R1, R2, etc.) created
- `audit_findings`: ReviewStatus, ReviewComments updated

---

### Stage 5: Approval/Rejection Decision

**Location:** `grc_backend/grc/routes/Audit/reviewing.py` - `update_audit_review_status()`

#### 5A. Approval Flow

**Process:**
1. **Reviewer Approves**:
   - Sets `ReviewStatus = 2` (Accept)
   - Sets `Status = 'Completed'`
   - Sets `ReviewDate = timezone.now()`
   - Sets `CompletionDate = timezone.now()`
   - Updates `ReviewerComments`

2. **Findings Update**:
   - Updates all `audit_findings` records:
     - Sets `ReviewStatus = 'Accept'`
     - Sets `ReviewRejected = 0`
     - Sets `ReviewDate = current_time`
     - Sets `CheckedDate = current_time`
     - Updates all finding fields (Evidence, Comments, etc.)
     - Stores `PredictiveRisks` and `CorrectiveActions` (JSON)

3. **Version Update**:
   - Updates latest Reviewer version:
     - Sets `ApprovedRejected = 'Approved'`
     - Updates `ExtractedInfo` with review data

4. **Report Generation**:
   - Generates audit report (Word document)
   - Uploads to S3
   - Saves report URL to `audit_report` table
   - Function: `generate_report_file()` in `report_views.py`

5. **Incident Creation**:
   - For findings with `Check = '0'` (Not Compliant) or `Check = '1'` (Partially Compliant):
     - Creates `Incident` record
     - Links to audit and compliance
     - Sets `Origin = 'Audit Finding'`
     - Function: `create_incidents_for_findings()` in `reviewing.py`

6. **Checklist Update**:
   - Updates `lastchecklistitemverified` table
   - Function: `update_lastchecklistitem_verified()`

7. **Notification**:
   - Sends approval notification to auditor and assignee

**Tables Updated:**
- `audit`: Status = "Completed", ReviewStatus = 2, ReviewDate, CompletionDate set
- `audit_findings`: All findings updated with review data
- `audit_version`: ApprovedRejected = "Approved"
- `audit_report`: New report record created
- `incidents`: New incident records created for non-compliant findings
- `lastchecklistitemverified`: Updated

#### 5B. Rejection Flow

**Process:**
1. **Reviewer Rejects**:
   - Sets `ReviewStatus = 3` (Reject)
   - Sets `Status = 'Work In Progress'` (returns to auditor)
   - Sets `ReviewStatus = 0` (resets review status)
   - Sets `ReviewDate = timezone.now()`
   - Updates `ReviewerComments`

2. **Findings Update**:
   - Updates `audit_findings` records:
     - Sets `ReviewStatus = 'Reject'`
     - Sets `ReviewRejected = 1`
     - Sets `ReviewDate = current_time`
     - Updates `ReviewComments`

3. **Version Update**:
   - Updates latest Reviewer version:
     - Sets `ApprovedRejected = 'Rejected'`
     - Updates `ExtractedInfo` with rejection data

4. **Notification**:
   - Sends rejection notification to auditor and assignee
   - Includes rejection comments

**Tables Updated:**
- `audit`: Status = "Work In Progress", ReviewStatus = 0, ReviewDate set
- `audit_findings`: ReviewStatus = "Reject", ReviewRejected = 1
- `audit_version`: ApprovedRejected = "Rejected"

**Next Steps After Rejection:**
- Auditor receives notification
- Auditor can revise findings
- Process returns to Stage 2 (Audit Execution)
- New Auditor version created (A4, A5, etc.)
- Can resubmit for review

---

### Stage 6: Completion and Reporting

**Process:**
1. **Audit Completed**:
   - Status remains "Completed"
   - All findings reviewed and approved
   - Report generated and stored

2. **Report Access**:
   - Reports accessible via `audit_report` table
   - Report URL points to S3 storage

3. **Incident Tracking**:
   - Incidents created from non-compliant findings
   - Tracked in `incidents` table
   - Linked to audit via `AuditId`

4. **Data Retention**:
   - `retentionExpiry` field tracks data retention
   - Used for compliance and archival purposes

**Tables Accessed:**
- `audit`: Final audit record
- `audit_findings`: All findings with review data
- `audit_version`: Complete version history
- `audit_report`: Generated reports
- `incidents`: Related incidents

---

### Stage 1A: AI Audit Document Upload Process

**Location:** `grc_backend/grc/routes/Audit/ai_audit_api.py` - `AIAuditDocumentUploadView`

**Endpoint:** `POST /api/ai-audit/{audit_id}/upload/`

**Purpose:** Upload documents for AI-powered audit analysis. Documents are analyzed using AI/ML to extract compliance information, identify gaps, and generate findings.

**Detailed Process:**

#### Step 1: Authentication and Validation
1. **Authentication:**
   - Checks JWT token or session authentication
   - Validates user has permission to upload documents
   - Gets user ID from request

2. **Audit Validation:**
   - Verifies audit exists in `audit` table
   - Checks `AuditType = 'A'` (AI audit)
   - Retrieves `FrameworkId` from audit record
   - Validates audit is in correct state for document upload

#### Step 2: File Upload Handling
Two modes supported:

**Mode A: New File Upload**
1. **File Reception:**
   - Receives file from `request.FILES['file']`
   - Validates file exists and is not empty
   - Gets file metadata: name, size, content type

2. **File Processing:**
   - Generates unique file ID using UUID: `file_id = str(uuid.uuid4())`
   - Extracts file extension: `.pdf`, `.docx`, `.xlsx`, etc.
   - Creates unique filename: `{file_id}{extension}`
   - Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf`

3. **File Storage:**
   - Saves to: `MEDIA_ROOT/ai_audit_documents/{unique_filename}`
   - Creates directory if it doesn't exist
   - Writes file in chunks for large files
   - Stores local file path for processing

**Mode B: Already Uploaded File (Metadata Only)**
- Used when file already uploaded to S3
- Receives metadata: `file_name`, `file_size`, `aws_file_link`, `s3_key`, `stored_name`
- Creates database record without re-uploading file
- Links to existing S3 file

#### Step 3: Document Metadata Extraction
1. **File Information:**
   - Document name: Original filename
   - File size: In bytes
   - MIME type: `application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, etc.
   - File extension: `.pdf`, `.docx`, `.xlsx`, etc.

2. **Optional Mapping:**
   - `policy_id`: Optional - links document to specific policy
   - `subpolicy_id`: Optional - links document to specific subpolicy
   - `upload_type`: Default 'evidence', can be 'evidence', 'supporting', etc.

#### Step 4: Database Record Creation
Creates record in `audit_documents` table:

```sql
INSERT INTO audit_documents (
    AuditId, DocumentName, DocumentPath, UploadedBy, 
    UploadedDate, UploadStatus, ProcessingStatus, 
    DocumentType, FileSize, MimeType, FrameworkId,
    PolicyId, SubPolicyId, ExternalSource
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
```

**Field Values:**
- `AuditId`: The audit ID
- `DocumentName`: Original filename
- `DocumentPath`: Local file path or S3 key
- `UploadedBy`: User ID (can be NULL)
- `UploadedDate`: Current timestamp
- `UploadStatus`: 'uploading' → 'completed' or 'failed'
- `ProcessingStatus`: 'pending' (will be updated after AI processing)
- `DocumentType`: Derived from file extension
- `FileSize`: File size in bytes
- `MimeType`: Content type
- `FrameworkId`: From audit record
- `PolicyId`: Optional, from request
- `SubPolicyId`: Optional, from request
- `ExternalSource`: 'manual' for new uploads, 'evidence_attachment' for already uploaded

#### Step 5: S3 Upload (Optional)
If S3 is configured:
1. Uploads file to S3 bucket
2. Stores S3 key and URL
3. Updates `DocumentPath` with S3 URL
4. Can keep local copy or remove after S3 upload

#### Step 6: Response
Returns success response:
```json
{
    "success": true,
    "document_id": 123,
    "message": "Document uploaded successfully",
    "document": {
        "document_id": 123,
        "document_name": "policy_document.pdf",
        "file_size": 1024000,
        "upload_status": "completed",
        "processing_status": "pending"
    }
}
```

**Tables Updated:**
- `audit_documents`: New document record created
  - `UploadStatus`: 'completed'
  - `ProcessingStatus`: 'pending' (ready for AI processing)

---

### Stage 1B: AI Audit Processing

**Location:** `grc_backend/grc/routes/Audit/ai_audit_api.py` - `start_ai_audit_processing_api()`

**Endpoint:** `POST /api/ai-audit/{audit_id}/start-processing/`

**Purpose:** Process uploaded documents using AI/ML to extract compliance information and generate audit findings.

**Detailed Process:**

#### Step 1: Get Pending Documents
1. **Query Documents:**
   ```sql
   SELECT document_id, document_name, document_path, document_type, 
          file_size, mime_type
   FROM audit_documents
   WHERE AuditId = %s 
   AND ProcessingStatus = 'pending'
   AND UploadStatus = 'completed'
   ```

2. **Update Status:**
   - Sets `ProcessingStatus = 'processing'` for all pending documents
   - Prevents duplicate processing

#### Step 2: Process Each Document
For each document:

1. **Text Extraction:**
   - **PDF Files:** Uses PDF parsing library
   - **Word Documents (.docx):** Uses python-docx library
   - **Excel Files (.xlsx):** Uses openpyxl library
   - **Other Formats:** Uses appropriate extraction method
   - Extracts full text content from document

2. **AI Analysis:**
   - **Compliance Checking:**
     - Uses structured compliance checker
     - Compares document content against compliance requirements
     - Identifies gaps and non-compliance areas
   
   - **AI Processing:**
     - Calls OpenAI API (GPT-4 or configured model)
     - Sends document text with compliance requirements
     - Gets AI analysis of compliance status
     - Extracts compliance matrix (which requirements are met/not met)

3. **Compliance Mapping:**
   - Maps document sections to compliance requirements
   - Identifies which compliances are addressed in document
   - Flags missing or incomplete compliance coverage
   - Generates compliance matrix (JSON structure)

4. **Metadata Extraction:**
   - Extracts document metadata (title, author, dates, etc.)
   - Identifies key sections and topics
   - Generates document summary

5. **Risk Assessment:**
   - Identifies potential risks from document content
   - Assesses risk levels
   - Links risks to compliance gaps

6. **Recommendations Generation:**
   - AI generates recommendations for compliance improvements
   - Suggests action items
   - Provides best practices

#### Step 3: Update Audit Findings
For each compliance identified:

1. **Check Existing Finding:**
   - Checks if `audit_findings` record exists for this compliance
   - If exists: Updates with AI analysis
   - If not exists: Creates new finding

2. **Update Finding:**
   ```sql
   UPDATE audit_findings
   SET Evidence = %s,  -- Document reference
       Comments = %s,  -- AI analysis summary
       HowToVerify = %s,  -- AI-generated verification steps
       Impact = %s,  -- AI-identified impact
       Recommendation = %s,  -- AI recommendations
       DetailsOfFinding = %s,  -- Detailed AI analysis
       Check = %s  -- Compliance status from AI
   WHERE AuditId = %s AND ComplianceId = %s
   ```

3. **Compliance Status Mapping:**
   - AI determines compliance status
   - Maps to `Check` field:
     - '0': Not Compliant (gaps identified)
     - '1': Partially Compliant (some requirements met)
     - '2': Compliant (all requirements met)
     - '3': Not Applicable

#### Step 4: Update Document Record
```sql
UPDATE audit_documents
SET ProcessingStatus = 'completed',
    ProcessingResults = %s,  -- JSON with AI analysis
    ComplianceMapping = %s,  -- JSON mapping to compliances
    ExtractedText = %s,  -- Full extracted text
    DocumentSummary = %s,  -- AI-generated summary
    ProcessedDate = %s
WHERE document_id = %s
```

**ProcessingResults JSON Structure:**
```json
{
    "ai_analysis": {
        "compliance_status": "partially_compliant",
        "gaps_identified": [...],
        "strengths": [...],
        "recommendations": [...]
    },
    "compliance_matrix": {
        "compliance_id_1": {
            "status": "compliant",
            "evidence": "Section 3.2",
            "notes": "..."
        },
        "compliance_id_2": {
            "status": "non_compliant",
            "gaps": [...],
            "recommendations": [...]
        }
    },
    "risks": [...],
    "metadata": {...}
}
```

#### Step 5: Error Handling
- If processing fails for a document:
  - Sets `ProcessingStatus = 'failed'`
  - Stores error in `ProcessingError` field
  - Continues with other documents
  - Logs error for debugging

#### Step 6: Completion
1. **Status Update:**
   - All documents processed (success or failure)
   - Audit findings updated with AI analysis
   - Ready for auditor review

2. **Response:**
   ```json
   {
       "success": true,
       "documents_processed": 3,
       "findings_updated": 25,
       "processing_results": [
           {
               "document_id": 123,
               "status": "completed",
               "findings_count": 10
           }
       ]
   }
   ```

**Tables Updated:**
- `audit_documents`: 
  - `ProcessingStatus`: 'completed' or 'failed'
  - `ProcessingResults`: JSON with AI analysis
  - `ComplianceMapping`: JSON mapping to compliances
  - `ExtractedText`: Full document text
  - `DocumentSummary`: AI summary
  - `ProcessedDate`: Timestamp

- `audit_findings`:
  - Updated with AI analysis results
  - Evidence, Comments, HowToVerify, Impact, Recommendation, DetailsOfFinding
  - Check status based on AI compliance assessment

**AI Processing Flow Summary:**
```
Document Upload
    ↓
Text Extraction
    ↓
AI Analysis (OpenAI API)
    ├─→ Compliance Checking
    ├─→ Gap Identification
    ├─→ Risk Assessment
    └─→ Recommendations Generation
    ↓
Update Audit Findings
    ↓
Store Processing Results
    ↓
Ready for Auditor Review
```

---

## Status Transitions

### Audit Status Flow

```
Yet to Start
    ↓
Work In Progress
    ↓
Under review
    ↓
    ├─→ Completed (if approved)
    └─→ Work In Progress (if rejected)
```

### Review Status Flow

```
None (0)
    ↓
In Review (1)
    ↓
    ├─→ Accept (2) → Completed
    └─→ Reject (3) → Work In Progress
```

### Finding Check Status

- `'0'`: Not Started / Not Compliant
- `'1'`: In Progress / Partially Compliant
- `'2'`: Completed / Compliant
- `'3'`: Not Applicable

### MajorMinor (Criticality)

- `'0'`: Minor
- `'1'`: Major
- `'2'`: Not Applicable

---

## Key Functionalities

### 1. Audit Assignment
- **File**: `grc_backend/grc/routes/Audit/assign_audit.py`
- **Function**: `create_audit()`
- **Purpose**: Creates audits and assigns to team members
- **Creates**: Audit records, Audit findings

### 2. Audit Execution
- **File**: `grc_backend/grc/routes/Audit/audit_views.py`
- **Functions**: 
  - `update_audit_status()`: Updates audit status
  - `update_audit_finding()`: Updates individual findings
  - `save_audit_version()`: Creates auditor versions
- **Purpose**: Allows auditor to update findings and save progress

### 3. Submission for Review
- **File**: `grc_backend/grc/routes/Audit/audit_views.py`
- **Function**: `send_audit_for_review()`
- **Purpose**: Submits audit for reviewer approval

### 4. Review Process
- **File**: `grc_backend/grc/routes/Audit/reviewing.py`
- **Function**: `update_audit_review_status()`
- **Purpose**: Handles review, approval, and rejection

### 5. Version Management
- **File**: `grc_backend/grc/routes/Audit/audit_views.py`
- **Functions**:
  - `create_audit_version()`: Creates auditor versions (A1, A2...)
  - `create_review_version()`: Creates reviewer versions (R1, R2...)
  - `get_next_version_number()`: Gets next version number
- **Purpose**: Maintains version history

### 6. Report Generation
- **File**: `grc_backend/grc/routes/Audit/report_views.py`
- **Function**: `generate_report_file()`
- **Purpose**: Generates Word document reports and uploads to S3

### 7. Incident Creation
- **File**: `grc_backend/grc/routes/Audit/reviewing.py`
- **Function**: `create_incidents_for_findings()`
- **Purpose**: Creates incidents for non-compliant findings

### 8. Compliance Addition
- **File**: `grc_backend/grc/routes/Audit/assign_audit.py`
- **Function**: `add_compliance_to_audit()`
- **Purpose**: Adds new compliance items to existing audit

### 9. Checklist Verification Update
- **File**: `grc_backend/grc/routes/Audit/checklist_utils.py`
- **Function**: `update_lastchecklistitem_verified()`
- **Purpose**: Updates `lastchecklistitemverified` table when audit is approved
- **When Called**: After audit approval in `reviewing.py`
- **Process**:
  1. Retrieves all audit findings for the approved audit
  2. For each finding:
     - Checks if record exists in `lastchecklistitemverified`
     - Updates or inserts record with latest verification data
     - Increments `Count` for non-compliant/partially compliant findings
  3. Sends notifications about audit completion
  4. Logs all updates for audit trail

### 10. AI Audit Document Processing
- **File**: `grc_backend/grc/routes/Audit/ai_audit_api.py`
- **Functions**: 
  - `AIAuditDocumentUploadView.post()`: Handles document upload
  - `start_ai_audit_processing_api()`: Starts AI processing
  - `process_document_with_ai()`: Processes individual documents
- **Purpose**: Uploads and processes documents for AI-powered audits
- **Process**:
  1. Uploads documents to server/S3
  2. Extracts text from documents
  3. Uses AI (OpenAI) to analyze compliance
  4. Updates audit findings with AI analysis
  5. Generates compliance matrix and recommendations

---

## Data Flow and Storage

### When Audit is Assigned

1. **audit Table**:
   - New record created with:
     - `Status = 'Yet to Start'`
     - `AssignedDate = current_timestamp`
     - `ReviewStatus = NULL`
     - All audit metadata (Title, Scope, Objective, etc.)

2. **audit_findings Table**:
   - Multiple records created (one per compliance):
     - `Check = '0'` (Not Started)
     - `Evidence = ''`
     - `Comments = ''`
     - `AssignedDate = audit.AssignedDate`
     - Links to AuditId, ComplianceId, UserId, FrameworkId

3. **audit_version Table**:
   - No version created yet (created when auditor saves)

### When Auditor Saves Progress

1. **audit_findings Table**:
   - Individual findings updated with:
     - Evidence, Comments, Check status
     - MajorMinor, HowToVerify, Impact, etc.

2. **audit_version Table**:
   - New Auditor version created (A1, A2, etc.):
     - `Version = 'A1'` (or next number)
     - `ExtractedInfo = JSON` (complete findings data)
     - `UserId = auditor_id`
     - `Date = current_timestamp`

3. **audit Table**:
   - `Status` may update to "Work In Progress"

### When Submitted for Review

1. **audit Table**:
   - `Status = 'Under review'`
   - `ReviewStartDate = current_timestamp`
   - `ReviewStatus = 1` (In Review)

2. **audit_version Table**:
   - Latest Auditor version remains (e.g., A3)

### When Reviewer Reviews

1. **audit_version Table**:
   - New Reviewer version created (R1, R2, etc.):
     - `Version = 'R1'` (or next number)
     - `ExtractedInfo = JSON` (review data)
     - `UserId = reviewer_id`
     - `Date = current_timestamp`

2. **audit_findings Table**:
   - `ReviewStatus`, `ReviewComments` updated

### When Approved

1. **audit Table**:
   - `Status = 'Completed'`
   - `ReviewStatus = 2` (Accept)
   - `ReviewDate = current_timestamp`
   - `CompletionDate = current_timestamp`
   - `ReviewerComments` updated

2. **audit_findings Table**:
   - All findings updated:
     - `ReviewStatus = 'Accept'`
     - `ReviewRejected = 0`
     - `ReviewDate = current_timestamp`
     - `CheckedDate = current_timestamp`
     - All finding fields updated
     - `PredictiveRisks`, `CorrectiveActions` stored (JSON)

3. **audit_version Table**:
   - Latest Reviewer version:
     - `ApprovedRejected = 'Approved'`
     - `ExtractedInfo` updated with final data

4. **audit_report Table**:
   - New record:
     - `Report = S3_URL`
     - Links to AuditId, PolicyId, SubPolicyId, FrameworkId

6. **lastchecklistitemverified Table**:
   - **CRITICAL UPDATE** - Called via `update_lastchecklistitem_verified(audit_id)`
   - For each audit finding:
     - **If record exists for ComplianceId:**
       - UPDATE with new verification data
       - Increment `Count` if `Check = '0'` or `'1'`
     - **If record doesn't exist:**
       - INSERT new record
       - Set `Count = 1` if `Check = '0'` or `'1'`
     - Fields updated:
       - `Date`: Current date
       - `Time`: Current time
       - `User`: Auditor/Reviewer user ID
       - `Complied`: Check value ('0', '1', '2', '3')
       - `Comments`: Finding comments
       - `Count`: Incremented for non-compliant/partially compliant
       - `AuditFindingsId`: Links to specific finding
       - `SubPolicyId`, `PolicyId`, `FrameworkId`: From compliance hierarchy

7. **incidents Table**:
   - New records for non-compliant findings:
     - `Origin = 'Audit Finding'`
     - Links to AuditId, ComplianceId

### When Rejected

1. **audit Table**:
   - `Status = 'Work In Progress'`
   - `ReviewStatus = 0` (reset)
   - `ReviewDate = current_timestamp`
   - `ReviewerComments` updated

2. **audit_findings Table**:
   - `ReviewStatus = 'Reject'`
   - `ReviewRejected = 1`
   - `ReviewDate = current_timestamp`
   - `ReviewComments` updated

3. **audit_version Table**:
   - Latest Reviewer version:
     - `ApprovedRejected = 'Rejected'`
     - `ExtractedInfo` updated with rejection data

---

## API Endpoints

### Audit Assignment
- `GET /api/audit/assign-data/`: Get frameworks, policies, subpolicies, users
- `POST /api/audit/create-audit/`: Create new audit(s)
- `POST /api/audits/{audit_id}/add-compliance/`: Add compliance to audit

### Audit Management
- `GET /api/audits/`: Get all audits
- `GET /api/audits/my-audits/`: Get audits assigned to current user
- `GET /api/audits/my-reviews/`: Get audits pending review
- `GET /api/audits/{audit_id}/`: Get audit details
- `POST /api/audits/{audit_id}/status/`: Update audit status
- `GET /api/audits/{audit_id}/get-status/`: Get audit status

### Audit Findings
- `GET /api/audits/{audit_id}/compliances/`: Get audit compliances/findings
- `POST /api/audit-findings/{compliance_id}/`: Update audit finding
- `POST /api/upload-evidence/{compliance_id}/`: Upload evidence
- `GET /api/audit-findings-details/{audit_findings_id}/`: Get finding details

### Version Management
- `GET /api/audits/{audit_id}/versions/`: Get all versions
- `GET /api/audits/{audit_id}/versions/{version}/`: Get version details
- `POST /api/audits/{audit_id}/save-version/`: Save auditor version
- `POST /api/audits/{audit_id}/save-audit-version/`: Save audit version (JSON)
- `GET /api/audits/{audit_id}/check-version/`: Check version

### Review Process
- `POST /api/audits/{audit_id}/send-for-review/`: Submit for review
- `POST /api/audits/{audit_id}/update-audit-review-status/`: Update review status
- `GET /api/audits/{audit_id}/review-data/`: Load review data

### Reports
- `GET /api/audits/{audit_id}/reports/`: Get audit reports
- `POST /api/export/audit-compliances/{format}/{item_type}/{item_id}/`: Export findings

---

## Related Modules

### 1. Compliance Module
- **Relationship**: Audits are based on compliance requirements
- **Tables**: `compliance`, `subpolicies`, `policies`, `frameworks`
- **Usage**: When audit is created, compliances are retrieved and findings created

### 2. Incident Module
- **Relationship**: Non-compliant findings create incidents
- **Table**: `incidents`
- **Usage**: When audit is approved, incidents are created for non-compliant findings

### 3. User Management
- **Relationship**: Users are assigned as auditors, reviewers, assignees
- **Table**: `users`
- **Usage**: All audit assignments reference users

### 4. Framework/Policy Management
- **Relationship**: Audits are scoped to frameworks, policies, subpolicies
- **Tables**: `frameworks`, `policies`, `subpolicies`
- **Usage**: Determines which compliances are included in audit

### 5. Notification Service
- **Relationship**: Sends notifications for audit events
- **Usage**: 
  - Audit assignment notifications
  - Review request notifications
  - Approval/rejection notifications

### 6. Logging Service
- **Relationship**: Logs all audit actions
- **Usage**: Tracks audit lifecycle events for audit trail

---

## Summary

The Audit Module follows a comprehensive lifecycle:

1. **Creation**: Audit created and assigned to auditors
2. **Execution**: Auditors update findings and save versions
3. **Submission**: Audit submitted for review
4. **Review**: Reviewer reviews and makes decision
5. **Approval/Rejection**: 
   - **Approved**: Audit completed, report generated, incidents created
   - **Rejected**: Returns to auditor for revision
6. **Completion**: Final state with all data stored

**Key Tables:**
- `audit`: Main audit records
- `audit_findings`: Individual compliance findings
- `audit_version`: Version history (A1, A2, R1, R2...)
- `audit_report`: Generated reports
- `audit_documents`: Documents for AI audits
- `lastchecklistitemverified`: **Critical** - Tracks compliance verification history and completion status

**Data Persistence:**
- All audit data stored in database tables
- Version history maintained in `audit_version` table
- Reports stored in S3 and referenced in `audit_report` table
- Complete audit trail available through version history

---

*Document Generated: Comprehensive Audit Module Lifecycle Documentation*
*Last Updated: Based on codebase analysis*

