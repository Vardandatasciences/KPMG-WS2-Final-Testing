# HomeView Frontend State Management Audit

## Scope
This report audits state management in the Vue frontend with `HomeView` as the center, including how shared state, API calls, storage, and cross-component data flow currently work.

Primary focus file:
- `grc_frontend/src/components/Login/HomeView.vue`

Supporting files:
- `grc_frontend/src/main.js`
- `grc_frontend/src/store/index.js`
- `grc_frontend/src/stores/framework.js`
- `grc_frontend/src/stores/homepage.js`
- `grc_frontend/src/stores/appData.js`
- `grc_frontend/src/stores/dashboards.js`
- `grc_frontend/src/services/apiService.js`
- `grc_frontend/src/utils/eventBus.js`

---

## 1) Existing State Management Pattern

The frontend uses a **hybrid model**:

- **Pinia** is active (`createPinia`, `app.use(pinia)`), and multiple Pinia stores are already in production use.
- **Vuex** is also active (`createStore`, `app.use(store)`), with legacy modules still consumed by components/composables.
- **Local component state** (`ref`, `reactive`, `computed`) is heavy, especially in `HomeView.vue`.
- **Browser storage** (`localStorage`, `sessionStorage`) is heavily used for auth/session/cache.
- **Event mechanisms** exist both as a custom `eventBus` and browser `CustomEvent` (`framework-changed`, `authChanged` patterns).
- **provide/inject** was not found in `src` during scan.

Evidence:
- `grc_frontend/src/main.js`
- `grc_frontend/src/store/index.js`
- `grc_frontend/src/stores/*.js`
- `grc_frontend/src/components/Login/HomeView.vue`
- `grc_frontend/src/utils/eventBus.js`

---

## 2) Components with Duplicated API Calls

### Framework selection duplication
Common endpoints repeatedly called across many components:
- `FRAMEWORK_GET_SELECTED`
- `FRAMEWORK_SET_SELECTED`

Notable files:
- `grc_frontend/src/components/Policy/AllPolicies.vue`
- `grc_frontend/src/components/Policy/PolicyDashboard.vue`
- `grc_frontend/src/components/Compliance/ComplianceDashboard.vue`
- `grc_frontend/src/components/Compliance/AuditManagementView.vue`
- `grc_frontend/src/components/Incident/IncidentUserTasks.vue`
- `grc_frontend/src/components/Login/HomeView.vue`

### Notification duplication
Common endpoint repeatedly called:
- `GET_NOTIFICATIONS` (or `/api/get-notifications/`)

Notable files:
- `grc_frontend/src/components/GlobalNavbar.vue`
- `grc_frontend/src/components/Settings/Settings.vue`
- `grc_frontend/src/components/Policy/PendingAcknowledgements.vue`
- `grc_frontend/src/components/SessionTimeoutPopup.vue`
- `grc_frontend/src/views/Notifications.vue`

### Risk shared list duplication
Common endpoints:
- `RISKS_FOR_DROPDOWN`
- `RISK_INSTANCES`

Notable files:
- `grc_frontend/src/components/Risk/TailoringRisk.vue`
- `grc_frontend/src/components/Risk/ScoringDetails.vue`
- `grc_frontend/src/components/Risk/RiskRegisterList.vue`
- `grc_frontend/src/components/Risk/CreateRiskInstance.vue`
- `grc_frontend/src/components/Risk/RiskInstances.vue`
- `grc_frontend/src/components/Risk/RiskResolution.vue`

### Business unit duplication
Common endpoint:
- `BUSINESS_UNITS`

Notable files:
- `grc_frontend/src/components/Auditor/AuditorDashboard.vue`
- `grc_frontend/src/components/Auditor/Reviewer.vue`
- `grc_frontend/src/components/Auditor/AssignAudit.vue`
- `grc_frontend/src/components/Incident/CreateIncident.vue`
- `grc_frontend/src/components/Incident/Incident.vue`
- `grc_frontend/src/components/Incident/AuditFindings.vue`

---

## 3) Components Using Shared Data Locally

High-value shared datasets are often fetched centrally but transformed repeatedly in component-local computed/refs.

### Key example: `HomeView.vue`
- Pulls from Pinia (`useAppDataStore`, `useFrameworkStore`, `useHomepageStore`)
- Also uses direct API/service calls (`axios`, `axiosInstance`, `homepageDataService`)
- Builds many local computed projections:
  - hero statistics
  - preview metrics
  - policy/compliance/risk/incident/audit metric cards
  - chart datasets and popup state

Similar pattern in:
- `grc_frontend/src/components/Policy/PolicyDashboard.vue`
- `grc_frontend/src/components/Risk/RiskDashboard.vue`
- `grc_frontend/src/components/Auditor/UserDashboard.vue`

---

## 4) Prop Drilling Issues

Findings:
- No major deep prop drilling was observed in the Home route/dashboard flow.
- `HomeView` is route-mounted directly and not fed through long parent chains.
- Cross-feature data sharing primarily uses:
  - Pinia/Vuex
  - storage fallbacks
  - custom events
- Props/emits are mostly localized to reusable inputs/modals.

Files:
- `grc_frontend/src/router/index.js`
- `grc_frontend/src/components/inputs/*.vue`
- `grc_frontend/src/components/EventHandling/*.vue`

---

## 5) Data That Should Move to Pinia

For consistency and de-duplication, move these to centralized Pinia stores:

- Auth/session user snapshot and status flags
- Framework selection metadata and effective framework context
- Shared global filters (framework/date/business-unit/status filters)
- Notifications list, unread count, fetch status, refresh timestamps
- Shared reference datasets (business units, dropdown masters)
- Risk shared lists (`RISKS_FOR_DROPDOWN`, `RISK_INSTANCES`) and KPI summaries
- Policy/compliance/audit summaries reused by multiple pages
- Dashboard module metrics keyed by framework + freshness TTL

---

## 6) Data That Should Remain Local Component State

Keep these local to component state:

- Modal visibility and transient popup data
- Per-view table UI state (expand/collapse/sort menus)
- Draft form values before submit
- Local loading indicators for a subsection
- Chart rendering/view-only options

In `HomeView.vue`, local UI states like popup open/close and chart display options should remain local, while canonical data payloads and fetch status should be centralized.

---

## 7) Suggested Pinia Stores for This Product

Recommended target store architecture:

- `useAuthStore` (new)
  - auth flags, user profile, derived permission snapshot
- `useFrameworkStore` (extend existing)
  - selected framework, framework list, framework change side-effects
- `useFilterStore` (new)
  - shared cross-module filters
- `useReferenceDataStore` (new)
  - business units and common lookup lists
- `useNotificationStore` (new)
  - notifications, unread counters, refresh policy
- `useRiskStore` (new)
  - risk lists, instances, risk KPI summary cache
- `usePolicyStore` (new)
  - policy list/status summary and acknowledgements aggregate
- `useComplianceStore` (new)
  - compliance controls/progress summaries
- `useAuditStore` (new)
  - assignment/findings/dashboard summaries
- `useDashboardStore` (extend existing `dashboards.js`)
  - framework-keyed KPI slices with TTL freshness

---

## 8) Migration Priority

Recommended order:

1. **Auth**
2. **Framework selection**
3. **Filters**
4. **Risks**
5. **Policies**
6. **Compliance**
7. **Audit**
8. **Notifications**

Reasoning:
- Auth/framework/filter layers are foundational and affect all domain requests.
- Risks/policies/compliance/audit currently show significant duplicate fetching and local reshaping.
- Notifications can be centralized once core domain stores are stabilized.

---

## HomeView-Specific Summary

`HomeView.vue` is already partially aligned with centralized state (Pinia + service cache), but still mixes:
- multiple transport styles (`axios`, `axiosInstance`, service wrappers),
- local computation of cross-domain shared metrics,
- storage and event-based fallback behavior.

This file should be the pilot for:
- stricter source-of-truth boundaries,
- normalized fetch + cache actions in stores,
- thinner component-level transformation logic.

---

## Evidence Index

- `grc_frontend/src/components/Login/HomeView.vue`
- `grc_frontend/src/main.js`
- `grc_frontend/src/store/index.js`
- `grc_frontend/src/stores/framework.js`
- `grc_frontend/src/stores/homepage.js`
- `grc_frontend/src/stores/appData.js`
- `grc_frontend/src/stores/dashboards.js`
- `grc_frontend/src/components/Policy/AllPolicies.vue`
- `grc_frontend/src/components/Compliance/ComplianceDashboard.vue`
- `grc_frontend/src/components/Risk/RiskDashboard.vue`
- `grc_frontend/src/components/GlobalNavbar.vue`
- `grc_frontend/src/components/Settings/Settings.vue`
- `grc_frontend/src/components/Auditor/UserDashboard.vue`
- `grc_frontend/src/utils/eventBus.js`
