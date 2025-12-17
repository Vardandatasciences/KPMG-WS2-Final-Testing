# Mandatory and Optional Fields for Policy and Framework Creation

## Framework Creation Fields

### Mandatory Fields (marked with *)
1. **Framework Name** - Required, cannot be empty
2. **Description** - Required, cannot be empty
3. **Internal/External** - Required, must select either Internal or External
4. **Identifier** - Required, cannot be empty (auto-generated for Internal, manual for External)
5. **Category** - Required, cannot be empty
6. **Effective Start Date** - Required, must provide a date

### Optional Fields (no asterisk)
1. **Effective End Date** - Optional, can be left empty
2. **Upload Document** - Optional, can be skipped

---

## Policy Creation Fields

### Mandatory Fields (marked with *)
1. **Policy Name** - Required, cannot be empty
2. **Policy Identifier** - Required, cannot be empty (auto-generated for Internal frameworks, manual for External)
3. **Description** - Required, cannot be empty
4. **Scope** - Required, cannot be empty
5. **Department** - Required, must select at least one department
6. **Objective** - Required, cannot be empty
7. **Coverage Rate (%)** - Required, must provide a numeric value (0-100)
8. **Applicability** - Required, cannot be empty
9. **Policy Type** - Required, must select a policy type
10. **Policy Category** - Required, must select a category
11. **Policy Sub Category** - Required, must select a subcategory
12. **Start Date** - Required, must provide a date

### Optional Fields (no asterisk)
1. **Applicable Entities** - Optional, defaults to empty list (can select "All Locations" or specific entities)
2. **End Date** - Optional, can be left empty
3. **Upload Document** - Optional, can be skipped

---

## Subpolicy Creation Fields

### Mandatory Fields (marked with *)
1. **Sub Policy Name** - Required, cannot be empty

### Optional Fields (no asterisk)
- All other subpolicy fields are optional

---

## Event Creation Fields

### Mandatory Fields (marked with *)
1. **Framework** - Required, must select a compliance framework
2. **Event Type** - Required, must select an event type (depends on selected framework)
3. **Event Title** - Required, cannot be empty
4. **Reviewer** - Required, must select a reviewer for approval

### Optional Fields (no asterisk)
1. **Module** - Optional, can be left empty or select/create a module
2. **Specific Record** - Optional, can link to a specific record (Policy, Compliance, Audit, Risk, Incident, SubPolicy, or Jira Issue)
3. **Sub-Event Type** - Optional, specific sub-category of the selected event type
4. **Description** - Optional, detailed event description
5. **Owner** - Optional, auto-filled with current user (can be changed)
6. **Recurrence Type** - Optional, defaults to "Non-Recurring"
7. **Frequency** - Optional, required only if Recurrence Type is "Recurring"
8. **Start Date** - Optional, for recurring events
9. **End Date** - Optional, for recurring events
10. **Dynamic Fields** - Optional, additional fields specific to the selected framework and event type (some dynamic fields may be required based on configuration)
11. **Evidence/Attachments** - Optional, can upload or link evidence files
12. **Additional Records** - Optional, can add multiple linked records (only framework is required for additional records)

---

## Risk Creation Fields

### Mandatory Fields (marked with *)
1. **Risk Title** - Required, cannot be empty
2. **Risk Description** - Required, cannot be empty
3. **Risk Mitigation** - Required, at least one mitigation action must be provided

### Optional Fields (no asterisk)
1. **Compliance ID** - Optional, can link to a compliance requirement
2. **Criticality** - Optional, can select severity level (Critical, High, Medium, Low)
3. **Category** - Optional, can categorize the risk
4. **Risk Priority** - Optional, can set priority level (High, Medium, Low)
5. **Risk Likelihood** - Optional, numeric value from 1-10 (defaults to 1)
6. **Risk Impact** - Optional, numeric value from 1-10 (defaults to 1)
7. **Impact Multiplier (X)** - Optional, numeric value from 1-10 (defaults to 1)
8. **Likelihood Multiplier (Y)** - Optional, numeric value from 1-10 (defaults to 1)
9. **Risk Exposure Rating** - Optional, automatically calculated
10. **Risk Type** - Optional, defaults to "Current"
11. **Business Impact** - Optional, can select multiple business impacts
12. **Possible Damage** - Optional, can describe potential consequences

---

## Risk Instance Creation Fields

### Mandatory Fields (marked with *)
1. **Risk ID** - Required, must select a base risk template (optional if creating from incident)
2. **Criticality** - Required, must select severity level (Critical, High, Medium, Low)
3. **Risk Priority** - Required, must select priority level (High, Medium, Low)
4. **Origin** - Required, must select origin (Manual, SIEM, AuditFindings)
5. **Risk Type** - Required, must select risk type (Current, Residual, Inherent, Emerging, Accept)
6. **Appetite** - Required, must indicate if organization accepts this risk level (Yes, No)
7. **Response Type** - Required, must select response type (Mitigate, Avoid, Accept, Transfer)
8. **Risk Likelihood** - Required, must provide numeric value from 1-10
9. **Risk Impact** - Required, must provide numeric value from 1-10
10. **Risk Title** - Required, cannot be empty
11. **Risk Description** - Required, cannot be empty

### Optional Fields (no asterisk)
1. **Category** - Optional, can categorize the risk instance
2. **Impact Multiplier (X)** - Optional, numeric value from 1-10 (defaults to 1)
3. **Likelihood Multiplier (Y)** - Optional, numeric value from 1-10 (defaults to 1)
4. **Risk Exposure Rating** - Optional, automatically calculated
5. **Risk Owner** - Optional, can assign an owner
6. **Business Impact** - Optional, can select multiple business impacts
7. **Risk Status** - Optional, defaults to "Not Assigned"
8. **Mitigation Status** - Optional, defaults to "Pending"
9. **Possible Damage** - Optional, can describe potential consequences
10. **Risk Response Description** - Optional, can describe the response strategy
11. **Risk Mitigation** - Optional, can provide mitigation actions
12. **Compliance ID** - Optional, can link to a compliance requirement
13. **Incident ID** - Optional, can link to an incident

---

## Incident Creation Fields

### Mandatory Fields (marked with *)
1. **Incident Title** - Required, cannot be empty (minimum 3 characters, maximum 255 characters)
2. **Description** - Required, cannot be empty (minimum 10 characters, maximum 2000 characters)
3. **Origin** - Required, must select how incident was discovered (Manual, System Generated)
4. **Date** - Required, must provide the date when the incident occurred or was discovered
5. **Time** - Required, must provide the time when the incident occurred or was discovered
6. **Risk Priority** - Required, must select priority level (High, Medium, Low)
7. **Risk Category** - Required, must select at least one category

### Optional Fields (no asterisk)
3. **Criticality** - Optional, can rate criticality level (Critical, High, Medium, Low)
4. **Cost of Incident** - Optional, can provide monetary cost
5. **Possible Damage** - Optional, can describe potential damage
6. **Affected Business Unit** - Optional, can select multiple business units
7. **Geographic Location** - Optional, can specify location
8. **Systems/Assets Involved** - Optional, can list affected systems
9. **Incident Classification** - Optional, can classify the incident
10. **Incident Category** - Optional, can select or add multiple categories
11. **Initial Impact Assessment** - Optional, can provide impact assessment
12. **Mitigation** - Optional, can describe mitigation steps taken
13. **Comments** - Optional, can add additional comments
14. **Internal Contacts** - Optional, can list internal contacts involved
15. **External Parties Involved** - Optional, can list external parties
16. **Regulatory Bodies** - Optional, can list regulatory bodies notified
17. **Relevant Policies/Procedures Violated** - Optional, can list violated policies
18. **Control Failures** - Optional, can describe control failures
19. **Lessons Learned** - Optional, can document lessons learned
20. **Compliance ID** - Optional, can link to a compliance requirement
21. **Timeline of Events** - Optional, can provide detailed timeline

---

## Compliance Creation Fields

### Mandatory Fields (marked with *)
1. **Framework** - Required, must select a framework
2. **Policy** - Required, must select a policy from the selected framework
3. **Sub Policy** - Required, must select a sub policy from the selected framework and policy
4. **Compliance Title** - Required, cannot be empty (minimum 3 characters, maximum 145 characters)
5. **Compliance Type** - Required, cannot be empty (maximum 100 characters)
6. **Compliance Description** - Required, cannot be empty (minimum 10 characters)
7. **Scope** - Required, cannot be empty (minimum 15 characters)
8. **Objective** - Required, cannot be empty
9. **Business Units Covered** - Required, must select or add at least one business unit
10. **Criticality** - Required, must select criticality level (High, Medium, Low)
11. **Assign Reviewer** - Required, must select a reviewer for approval

### Optional Fields (no asterisk)
1. **Identifier** - Optional, auto-generated if left empty
2. **Is Risk** - Optional, checkbox to indicate if compliance item represents a risk
3. **Impact (Severity Rating)** - Optional, numeric value from 1-10 (defaults to 5.0 if not provided)
4. **Probability** - Optional, numeric value from 1-10 (defaults to 5.0 if not provided)
4. **Possible Impact** - Optional, can describe potential damage
5. **Mitigation Steps** - Optional, can add multiple mitigation steps (if provided, each step must have at least 10 characters)
6. **Potential Risk Scenarios** - Optional, can describe risk scenarios
7. **Risk Type** - Optional, can select risk type (Current, Residual, Inherent, Emerging, Accepted)
8. **Risk Category** - Optional, can select or add risk categories
9. **Risk Business Impact** - Optional, can select or add business impacts
10. **Mandatory/Optional** - Optional, defaults to "Mandatory"
11. **Manual/Automatic** - Optional, defaults to "Manual"
12. **Maturity Level** - Optional, defaults to "Initial", can select maturity level (Initial, Developing, Defined, Managed, Optimizing)
13. **Applicability** - Optional, can provide applicability information

---

## Notes

- Fields marked with `*` (asterisk) are mandatory and must be filled before submission
- Optional fields can be left empty without causing validation errors
- The backend validation enforces these requirements and will return errors if mandatory fields are missing
- Some fields like "Identifier" are auto-generated for Internal frameworks but require manual entry for External frameworks
- For Event Creation, the Owner field is auto-filled with the current user but can be changed if needed
- Dynamic fields in Event Creation may have their own required/optional status based on the framework and event type configuration

