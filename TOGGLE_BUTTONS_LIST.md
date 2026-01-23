# Toggle Buttons - Files by Module

This document lists all files that contain toggle buttons/switches organized by module.

## Risk Module

### 1. **RiskResolution.vue**
   - **Location:** `frontend/src/components/Risk/RiskResolution.vue`
   - **Toggle Type:** Toggle Buttons
   - **Purpose:** Toggle between "Risk Resolution" and "Risk Workflow" views
   - **Classes:** `risk-resolution-toggle-buttons`, `risk-resolution-toggle-button`

### 2. **RiskWorkflow.vue**
   - **Location:** `frontend/src/components/Risk/RiskWorkflow.vue`
   - **Toggle Type:** Toggle Buttons
   - **Purpose:** Toggle between "Risk Resolution" and "Risk Workflow" views
   - **Classes:** `risk-workflow-toggle-buttons`, `risk-workflow-toggle-button`

### 3. **CreateRisk.vue**
   - **Location:** `frontend/src/components/Risk/CreateRisk.vue`
   - **Toggle Type:** Toggle Buttons (3-way toggle)
   - **Purpose:** Toggle between creation modes: "Manual Creation", "AI Suggested", and "Tailoring Risk"
   - **Classes:** `risk-creation-mode-toggle`, `risk-toggle-container`, `risk-toggle-option`, `risk-toggle-slider`

---

## Compliance Module

### 4. **ComplianceVersioning.vue**
   - **Location:** `frontend/src/components/Compliance/ComplianceVersioning.vue`
   - **Toggle Type:** Toggle Switch
   - **Purpose:** Toggle active/inactive status of compliance items
   - **Classes:** `toggle-switch`

### 5. **Compliances.vue**
   - **Location:** `frontend/src/components/Compliance/Compliances.vue`
   - **Toggle Type:** View Toggle Button
   - **Purpose:** Toggle view mode
   - **Classes:** `compliance-view-toggle-btn`

---

## Policy Module

### 6. **FrameworkExplorer.vue**
   - **Location:** `frontend/src/components/Policy/FrameworkExplorer.vue`
   - **Toggle Type:** Toggle Switch
   - **Purpose:** Toggle framework status (Active/Inactive)
   - **Classes:** `switch`, `slider`, `switch-label`

### 7. **FrameworkPolicies.vue**
   - **Location:** `frontend/src/components/Policy/FrameworkPolicies.vue`
   - **Toggle Type:** View Toggle Buttons
   - **Purpose:** Toggle between "List View" and "Card View"
   - **Classes:** `view-toggle-controls`, `view-toggle-btn`

### 8. **StatusChangeRequests.vue**
   - **Location:** `frontend/src/components/Policy/StatusChangeRequests.vue`
   - **Toggle Type:** Status Toggle Switch
   - **Purpose:** Display status toggle (Active/Inactive/Pending)
   - **Classes:** `status-toggle`, `switch-label`

### 9. **TT.vue**
   - **Location:** `frontend/src/components/Policy/TT.vue`
   - **Toggle Type:** Toggle Buttons
   - **Purpose:** Toggle between "Framework" and "Policy" tabs
   - **Classes:** `TT-toggle-group`, `TT-toggle`, `TT-active`

---

## Event Handling Module

### 10. **EventsCalendar.vue**
   - **Location:** `frontend/src/components/EventHandling/EventsCalendar.vue`
   - **Toggle Type:** View Toggle Buttons
   - **Purpose:** Toggle between "Table View" and "Calendar View"
   - **Classes:** `events-calendar-view-toggle`, `events-calendar-view-btn`, `events-calendar-view-btn-active`, `events-calendar-view-btn-inactive`

---

## Performance Analysis Module

### 11. **KpiAnalysis.vue**
   - **Location:** `frontend/src/components/PerformanceAnalysis/KpiAnalysis.vue`
   - **Toggle Type:** Toggle Buttons
   - **Purpose:** Toggle between "Days" and "Percentage" view modes for Time to Close KPI
   - **Classes:** `audit-kpi-view-toggle-container`, `audit-kpi-view-toggle-button`

---

## Auditor Module

### 12. **Audits.vue**
   - **Location:** `frontend/src/components/Auditor/Audits.vue`
   - **Toggle Type:** View Toggle Buttons
   - **Purpose:** Toggle between "List View" and "Card View"
   - **Classes:** `view-toggle`, `view-btn`

---

## Framework Comparison (Vue Directory)

### 13. **FrameworkComparisonUpdated.vue**
   - **Location:** `frontend/vue/FrameworkComparisonUpdated.vue`
   - **Toggle Type:** Toggle Button
   - **Purpose:** Toggle AI Matching ON/OFF
   - **Classes:** `FC_ai-toggle-button`, `FC_ai-toggle-active`

---

## Summary

**Total Files with Toggle Buttons/Switches: 13**

### By Toggle Type:
- **Toggle Buttons (Multi-option):** 7 files
- **Toggle Switches (On/Off):** 3 files
- **View Toggle Buttons:** 3 files

### By Module:
- **Risk Module:** 3 files
- **Compliance Module:** 2 files
- **Policy Module:** 4 files
- **Event Handling Module:** 1 file
- **Performance Analysis Module:** 1 file
- **Auditor Module:** 1 file
- **Framework Comparison:** 1 file

