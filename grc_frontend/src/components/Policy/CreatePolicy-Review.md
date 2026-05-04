# CreatePolicy.vue Review

File reviewed:
- `grc_frontend/src/components/Policy/CreatePolicy.vue`

Purpose:
- Provide a practical review in format: **Issue -> Why it matters -> Minimal fix approach**.

---

## 1) In-place form mutation during submit

### Issue
`Department` is converted from array/`'all'` into a string directly on `policiesForm` during submit preparation.

### Why it matters
- If submit fails, UI state is already transformed and no longer matches the editable form model.
- Retry/edit behavior can become inconsistent.
- Side-effects make debugging hard.

### Minimal fix approach
- Build a separate payload object (`const policiesPayload = policiesForm.value.map(...)`) and transform fields there.
- Do not mutate `policiesForm` source data inside submit workflow.

---

## 2) Expensive deep watcher on entire policies array

### Issue
A deep `watch` on `policiesForm` runs validation across all policies on every nested change.

### Why it matters
- Performance degradation on large forms.
- Typing lag risk as policy/subpolicy count grows.
- Hard to reason about validation triggers.

### Minimal fix approach
- Replace deep global watch with:
  - field-level validation on input/blur,
  - targeted watchers only for fields that need auto generation (`PolicyName`, `SubPolicyName`, etc.),
  - optional debouncing for expensive checks.

---

## 3) Timing-based framework sync guard

### Issue
`isLoadingFramework` is reset using `setTimeout(100)` after session/framework sync.

### Why it matters
- Timing-based guards are race-prone.
- Fast/slow devices or API variance can trigger unintended save/watch loops.

### Minimal fix approach
- Replace timeout with deterministic flow:
  - set flag before programmatic update,
  - `await nextTick()` after state application,
  - clear flag immediately after controlled update sequence ends.

---

## 4) Excessive debug logging including payloads

### Issue
Large internal objects and full payloads are logged (including form and mapped payload details).

### Why it matters
- Can expose sensitive business data in console logs.
- Adds noise and runtime overhead.
- Makes production troubleshooting harder.

### Minimal fix approach
- Remove high-volume logs or guard behind `if (import.meta.env.DEV)`.
- Keep only structured, low-noise operational logs for key milestones (fetch start/end, submit success/failure).

---

## 5) Single component handling too many responsibilities

### Issue
The component handles:
- framework loading/sync,
- users/categories/entities/departments fetch,
- uploads,
- consent gate,
- payload mapping,
- validation,
- submission,
- notifications.

### Why it matters
- High change risk (small edits can break unrelated parts).
- Harder testing and onboarding.
- Increased regression probability.

### Minimal fix approach
- Extract logic into focused units:
  - `policySubmissionService` (payload build + submit),
  - `policyReferenceDataService` (users/categories/entities/departments),
  - `useCreatePolicyStore` (state/orchestration),
  - keep `CreatePolicy.vue` mostly as view/controller.

---

## 6) Loading state is shared across unrelated async operations

### Issue
A single `loading` flag is reused for many independent operations.

### Why it matters
- UI can show misleading loading state.
- One operation can block or hide status of another.

### Minimal fix approach
- Split into scoped flags:
  - `isLoadingFrameworks`
  - `isLoadingUsers`
  - `isUploadingDocuments`
  - `isSubmitting`

---

## 7) Repeated notification-on-error boilerplate

### Issue
Many catch blocks repeat nearly identical `sendPushNotification` + popup error patterns.

### Why it matters
- Inconsistent error messaging.
- Difficult maintenance and localization.
- Copy-paste bug risk.

### Minimal fix approach
- Add helper utility like `handlePolicyError(context, err, userId)`.
- Centralize message formatting and notification payload defaults.

---

## 8) Data normalization patterns are duplicated

### Issue
Mapping of policy/subpolicy fields and data inventory labels is repeated in new-framework and existing-framework submit paths.

### Why it matters
- Divergence risk between two code paths.
- More maintenance cost.

### Minimal fix approach
- Extract shared mappers:
  - `buildPolicyDataInventory(policyFieldTypes)`
  - `buildSubPolicyDataInventory(subPolicyFieldTypes)`
  - `mapPolicyForSubmit(policy, context)`

---

## Real Page Examples (Create Policy)

These examples explain each issue in plain language using actual user behavior on the page.

### Example A: Department value changes after failed submit
- You select departments `[IT, HR]` for a policy.
- You click submit.
- Backend returns error.
- In current logic, department may already be converted to a string like `'1,2'`.
- Result: form state is no longer in original editable format, and retry can behave oddly.

What should happen instead:
- Form stays as array for UI.
- Only API payload gets converted to backend format.

### Example B: Page slows down while typing policy names
- You create 8-10 policies, each with subpolicies.
- You type one character in `PolicyName`.
- Deep watcher runs validation over many items every time.
- Result: typing lag and unnecessary CPU usage.

What should happen instead:
- Validate only changed field or only changed policy row.

### Example C: Framework auto-selection race
- You open page from Home where framework context is already selected.
- Page tries to sync framework and unlock watcher after `100ms`.
- On slower responses, watcher may re-enable too early.
- Result: extra framework save/sync calls may trigger unexpectedly.

What should happen instead:
- Re-enable watcher after state is definitely applied (`nextTick`/controlled sequence), not by timer.

### Example D: Debug logs expose too much data
- You fill creator/reviewer, entities, policies, subpolicies.
- Submit prints large payload in console (`JSON.stringify(payload, null, 2)`).
- Result: sensitive business/form data is visible in browser console and noisy for debugging.

What should happen instead:
- Keep only minimal logs (success/failure ids), and detailed logs only in dev mode.

### Example E: One bug fix impacts unrelated behavior
- You want to change only category mapping logic.
- Because submit, validation, upload, and notification logic live together, small edits risk side effects.
- Result: regression risk increases.

What should happen instead:
- Move payload/submit into service or store; keep component focused on UI interactions.

### Example F: Single loading flag gives wrong user feedback
- User opens reviewer dropdown (users loading), while frameworks refresh also starts.
- One shared `loading` flag controls multiple operations.
- Result: UI may show “busy” for wrong reason or block unrelated actions.

What should happen instead:
- Separate flags: `isLoadingUsers`, `isLoadingFrameworks`, `isSubmitting`, `isUploadingDocuments`.

---

## What is already good

- Uses `apiService` abstraction (not raw axios scatter).
- Has strong business validation coverage:
  - required fields,
  - creator/reviewer conflict,
  - duplicate policy/subpolicy checks.
- Framework context is integrated with Pinia (`useFrameworkStore`).

---

## Priority order for fixes (recommended)

1. Stop in-place form mutation during submit.
2. Remove deep global watcher and switch to targeted validation.
3. Replace timeout-based framework guard.
4. Reduce payload/debug logs.
5. Extract submit/reference logic into service/store modules.

---

## Quick Definition of Done

This file is considered stabilized when:
- submit never mutates source form state,
- validations are targeted and responsive,
- no timing-based race guards,
- production logs are minimal/safe,
- major submit/data-fetch logic is extracted from component.
