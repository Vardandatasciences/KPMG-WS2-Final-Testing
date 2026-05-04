# HomeView State Management: Current State vs Needed Work

## Goal
Provide a practical, detailed list of:
- what exists today in the homepage flow,
- what problems remain,
- what exactly needs to be done next (step-by-step).

Target scope:
- `grc_frontend/src/components/Login/HomeView.vue`
- Supporting stores/services used by homepage data flow.

---

## 1) What We Currently Have

## A. State Management Architecture (Current)
- **Pinia is active** in app bootstrap and used in homepage flow.
  - `grc_frontend/src/main.js`
  - `grc_frontend/src/stores/framework.js`
  - `grc_frontend/src/stores/homepage.js`
  - `grc_frontend/src/stores/appData.js`
  - `grc_frontend/src/stores/dashboards.js`
- **Vuex is still active** (legacy coexistence with Pinia).
  - `grc_frontend/src/main.js`
  - `grc_frontend/src/store/index.js`
- **HomeView uses both centralized and local state together**, with many `ref/computed` blocks.
  - `grc_frontend/src/components/Login/HomeView.vue`

## B. Data Fetching and Caching (Current)
- `HomeView` uses:
  - Pinia stores (`useAppDataStore`, `useFrameworkStore`, `useHomepageStore`)
  - `homepageDataService`
  - direct `axios`/`axiosInstance` calls in component
- Existing cache behavior:
  - framework-keyed cache in `homepage` Pinia store
  - persisted cache in `localStorage`
  - service-level caching patterns
- This is useful, but still mixed and not fully standardized.

## C. Framework Selection (Current)
- Selected framework is managed through `frameworkStore`.
- `HomeView` also keeps local framework-related state and watchers.
- Framework selection triggers data reload logic in multiple places.

## D. UI State (Current)
- `HomeView` properly keeps many view-only concerns local:
  - popup visibility/data
  - chart options
  - layout/display behavior

## E. Cross-App Patterns (Current)
- Browser storage (`localStorage/sessionStorage`) is heavily used for auth/session/context.
- Event coordination exists (`CustomEvent` and event bus patterns in app).

---

## 2) What Problems We Still Have

## A. Too Many Sources of Truth
- Same homepage/domain data can come from:
  - component local refs,
  - Pinia,
  - Vuex,
  - service cache,
  - storage.
- This increases debugging and regression risk.

## B. Duplicate API and Transformation Logic
- Repeated endpoint usage across components for shared datasets (framework, notifications, risks, business units).
- Similar transformations are reimplemented in multiple dashboards/components.

## C. HomeView Is Too Heavy
- `HomeView.vue` is very large and handles:
  - data fetching orchestration,
  - data normalization,
  - view-model shaping,
  - UI rendering logic.
- This hurts maintainability and onboarding speed.

## D. Mixed Transport Layer Usage
- Component-level calls use mixed access patterns (`axios`, wrapper services, store actions), making behavior inconsistent.

---

## 3) What We Need To Do (Detailed Action Plan)

## Phase 1: Define Boundaries (No Behavior Change)
1. **Classify each HomeView state variable** into:
   - global shared state (belongs in Pinia),
   - local UI-only state (stays in component).
2. **Write canonical ownership map**:
   - framework selection -> `frameworkStore`
   - homepage payload/cache -> `homepageStore` (or dedicated `homeStore`)
   - UI toggles -> `HomeView` local state

Deliverable:
- One clear state ownership section in docs/comments for team reference.

## Phase 2: Centralize Homepage Fetch Orchestration
3. **Move all homepage fetch orchestration to store actions**.
   - `HomeView` should not orchestrate fallback chains directly.
4. **Use one transport path** for homepage domain:
   - store action -> service (`homepageDataService` / `apiService`) -> endpoint.
   - avoid scattered raw `axios` calls in component for the same domain.
5. **Keep cache strategy in one place**:
   - cache key: `all` or framework id
   - TTL freshness rules
   - stale-while-revalidate behavior (serve cache, refresh quietly)

Deliverable:
- Thin component, thick store/service pattern for homepage data.

## Phase 3: Simplify HomeView Consumption Layer
6. **Refactor HomeView to consume store state only** for shared data:
   - framework context
   - module metrics
   - loading/error/freshness
7. **Keep only local presentation state in HomeView**:
   - popup open/close and selected popup payload
   - chart options and view-only toggles
   - local interaction flags not needed elsewhere

Deliverable:
- `HomeView` becomes primarily rendering + interaction layer.

## Phase 4: Remove Duplication and Legacy Coupling
8. **Audit and remove duplicate homepage-related API calls** left in component.
9. **Stop dual reliance on Vuex for homepage concerns** where Pinia already owns data.
10. **Reduce event-based coupling** where store subscriptions/actions can replace custom events.

Deliverable:
- deterministic data flow with fewer hidden side-effects.

## Phase 5: Verification and Guardrails
11. Validate no behavior regression:
   - `all` frameworks view works,
   - specific framework view works,
   - switching frameworks updates all cards/charts correctly,
   - reload restores expected state/cache behavior,
   - no duplicate network bursts on mount.
12. Add lightweight instrumentation/logs around:
   - fetch start/end
   - cache hit/miss
   - framework-change refresh

Deliverable:
- measurable confidence before moving to next modules.

---

## 4) Exact “Keep Local” vs “Move to Pinia” Checklist

## Keep Local in `HomeView`
- popup visibility and popup presentation payload
- chart options and display preferences
- per-section temporary UI loading toggles
- transient selection states used only by this page

## Move/Keep Central in Pinia
- selected framework id/name and resolved context
- homepage canonical payload by framework
- module metrics (policy/compliance/risk/incident/audit)
- shared fetch/loading/error/freshness state
- shared dashboard summary data reused by other screens

---

## 5) File-by-File Work Queue (Home First)

## Primary
1. `grc_frontend/src/components/Login/HomeView.vue`
   - remove orchestration duplication
   - consume centralized store actions/state
2. `grc_frontend/src/stores/homepage.js`
   - strengthen canonical cache/fetch API
3. `grc_frontend/src/stores/framework.js`
   - keep framework selection as single source of truth
4. `grc_frontend/src/services/homepageService` (if present in project)
   - keep endpoint + normalization details centralized

## Secondary
5. `grc_frontend/src/stores/appData.js`
   - align shared summary ownership boundaries
6. `grc_frontend/src/stores/dashboards.js`
   - align TTL/freshness rules with homepage flow
7. `grc_frontend/src/main.js`
   - long-term: complete migration path away from homepage-related Vuex reliance

---

## 6) Definition of Done for Home Page Migration

Homepage migration is complete when:
- `HomeView` no longer directly orchestrates multi-step shared-data fetch chains.
- Shared homepage data has one clear owner in Pinia/store actions.
- Component only manages local UI state.
- Framework switch updates are deterministic and deduplicated.
- No duplicate homepage API calls during standard mount/switch flow.
- Existing UI output remains unchanged.

---

## 7) Next After Home Page

After homepage is stable, follow this sequence:
1. Auth
2. Framework selection consistency cleanup
3. Global filters
4. Risks
5. Policies
6. Compliance
7. Audit
8. Notifications

This keeps foundational dependencies stable before domain-by-domain migration.
