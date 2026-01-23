# Files with Approval Buttons - Complete List

This document lists all files across the application that contain approval/rejection buttons, organized by module.

## 📋 Policy Module

1. **`frontend/src/components/Policy/PolicyDetails.vue`**
   - Approve/Reject buttons for policies
   - Approve/Reject buttons for subpolicies
   - Final approval button for entire policy
   - Rejection confirmation modal

2. **`frontend/src/components/Policy/PolicyApprover.vue`**
   - Approve/Reject buttons for policy compliance
   - Approve/Reject buttons for subpolicies
   - Modal approval/rejection actions
   - Rejection confirmation modal

3. **`frontend/src/components/Policy/StatusChangeDetails.vue`**
   - Approve/Reject buttons for status change requests

4. **`frontend/src/components/Policy/StatusChangeRequests.vue`**
   - Approve/Reject buttons for status change requests

---

## ✅ Compliance Module

5. **`frontend/src/components/Compliance/ComplianceDetails.vue`**
   - Final approval button for compliance
   - Reject button for compliance
   - Submit review button
   - Rejection confirmation modal

6. **`frontend/src/components/Compliance/ComplianceApprover.vue`**
   - Approve/Reject buttons for compliance items
   - Rejection confirmation modal
   - Resubmission handling

---

## 🏗️ Framework Module

7. **`frontend/src/components/Framework/FrameworkDetails.vue`**
   - Final approval button for entire framework
   - Approve framework button
   - Reject framework button
   - Approve/Reject buttons for policies within framework
   - Approve/Reject buttons for subpolicies
   - Submit review button
   - Rejection confirmation modal

8. **`frontend/src/components/Framework/FrameworkApprover.vue`**
   - Rejection confirmation modal
   - Framework approval workflow

---

## ⚠️ Risk Module

9. **`frontend/src/components/Risk/RiskWorkflow.vue`**
   - Approve/Reject buttons for risk mitigations
   - Approve/Reject buttons for questionnaires
   - Change decision buttons
   - Feedback/remarks functionality

10. **`frontend/src/components/Risk/RiskScoring.vue`**
    - Reject action for risk instances

---

## 🚨 Incident Module

11. **`frontend/src/components/Incident/IncidentUserTasks.vue`**
    - Approve/Reject buttons for assessments
    - Approve/Reject buttons for mitigations
    - Approve/Reject incident buttons
    - Feedback/remarks functionality

12. **`frontend/src/components/Incident/Incident.vue`**
    - Confirm reject button
    - Confirm close button

13. **`frontend/src/components/Incident/IncidentDetails.vue`**
    - Approval/rejection functionality (referenced in search results)

14. **`frontend/src/components/Incident/AuditFindings.vue`**
    - Filter by rejected status (approval-related UI)

15. **`frontend/src/components/Incident/AuditFindingDetails.vue`**
    - Approval/rejection functionality (referenced in search results)

---

## 📅 Event Handling Module

16. **`frontend/src/components/EventHandling/EventsApproval.vue`**
    - Approve/Reject action buttons for events
    - Event approval workflow

17. **`frontend/src/components/EventHandling/EventDetails.vue`**
    - Approve button
    - Reject button

18. **`frontend/src/components/EventHandling/EventsQueue.vue`**
    - Approve action buttons

19. **`frontend/src/components/EventHandling/ApprovalModal.vue`**
    - Generic approval modal component
    - Approve/Reject/Archive buttons
    - Used across multiple modules

20. **`frontend/src/components/EventHandling/EventViewPopup.vue`**
    - Approve/Reject emit actions

21. **`frontend/src/components/EventHandling/EventsList.vue`**
    - Approval status filtering (approved/rejected groups)

22. **`frontend/src/components/EventHandling/EventsCalendar.vue`**
    - Approval-related functionality (referenced in search results)

---

## 👨‍💼 Auditor Module

23. **`frontend/src/components/Auditor/ReviewTaskView.vue`**
    - Confirm reject button
    - Review acceptance/rejection workflow
    - Rejection confirmation modal

24. **`frontend/src/components/Auditor/Reviewer.vue`**
    - Review status management (approval-related)

---

## 📊 Summary by Module

| Module | Number of Files | Files |
|--------|----------------|-------|
| **Policy** | 4 | PolicyDetails, PolicyApprover, StatusChangeDetails, StatusChangeRequests |
| **Compliance** | 2 | ComplianceDetails, ComplianceApprover |
| **Framework** | 2 | FrameworkDetails, FrameworkApprover |
| **Risk** | 2 | RiskWorkflow, RiskScoring |
| **Incident** | 5 | IncidentUserTasks, Incident, IncidentDetails, AuditFindings, AuditFindingDetails |
| **Event Handling** | 7 | EventsApproval, EventDetails, EventsQueue, ApprovalModal, EventViewPopup, EventsList, EventsCalendar |
| **Auditor** | 2 | ReviewTaskView, Reviewer |
| **TOTAL** | **24** | |

---

## 🔍 Common Approval Button Patterns

The following CSS classes and patterns are commonly used for approval buttons:

- **Approve buttons**: `approve-btn`, `btn-approve`, `approve-button`, `final-approve-btn`
- **Reject buttons**: `reject-btn`, `btn-reject`, `reject-button`
- **Common methods**: `approveCompliance()`, `rejectCompliance()`, `approvePolicy()`, `rejectPolicy()`, `approveFramework()`, `rejectFramework()`, `approveMitigation()`, `approveQuestionnaire()`, `handleApprove()`, `handleReject()`

---

## 📝 Notes

- Some files may contain approval buttons that are conditionally rendered based on user permissions
- The `ApprovalModal.vue` component is a reusable modal used across multiple modules
- Many components include rejection confirmation modals to prevent accidental rejections
- Approval workflows often include feedback/remarks functionality for rejections

