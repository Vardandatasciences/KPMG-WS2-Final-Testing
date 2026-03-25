# External Screening – Documentation

## Overview

External screening runs compliance checks on vendors using multiple screening types. Results are stored and reviewed in the Vendor External Screening UI.

---

## How It Works

### End-to-end flow

1. **Trigger**
   - **Automatic:** When a temp vendor is created via Management (Add Vendor / bulk upload), a background thread runs `_perform_automatic_screening(vendor)`.
   - **Manual:** `POST /api/v1/management/vendors/<vendor_code>/external-screening/` runs the same screening for that vendor.

2. **Backend screening**
   - For the vendor, the backend runs four screening types in sequence: **OFAC**, **PEP**, **SANCTIONS**, **ADVERSE_MEDIA**.
   - Each type inserts a row in `external_screening_results` and, when there are matches, rows in `screening_matches`.
   - Status is set to CLEAR / UNDER_REVIEW / POTENTIAL_MATCH / CONFIRMED_MATCH based on match counts and risk.

3. **Storage**
   - **DB:** `tprm` (e.g. `tprm_integration`) – tables `external_screening_results`, `screening_matches`.
   - **Models:** `ExternalScreeningResult`, `ScreeningMatch` in `apps/vendor_core/models.py`.

4. **Frontend**
   - **Page:** Vendor External Screening at route `/vendor-verification` (router name: "Vendor External Screening").
   - **Files:** `VendorExternalScreening.vue`, `VendorExternalScreening.css`.
   - User selects a vendor (from temp vendors), sees list of screening results by type and date, then can open a result to see matches, resolve (False Positive / Escalated / Confirmed Match), add notes, and “Clear All” for that screening.

5. **APIs used by the UI**
   - Vendors: `GET /api/v1/vendor-core/temp-vendors/` (and optional `?search=`).
   - Results: `GET /api/v1/vendor-core/screening-results/vendor_screening_results/?vendor_id=<id>`.
   - Actions (all require auth and tenant):
     - `POST .../screening-results/<screening_id>/mark_as_cleared/` – mark that screening (and its matches) as cleared.
     - `POST .../screening-results/<screening_id>/update_match_status/` – body `{ match_id, status, notes }`.
     - `POST .../screening-results/<screening_id>/add_note/` – body `{ note }`.

---

## Screening Types (4 in use)

| Type           | Count | Implementation | Working condition |
|----------------|-------|----------------|-------------------|
| **OFAC**       | 1     | `OFACService` in `apps/vendor_core/services.py`; called from `apps/management/views.py` `_perform_ofac_screening()` | **Mock only.** Real OFAC API is commented out (was returning 400). Mock returns matches for names containing "test", "global", or "med". |
| **PEP**        | 1     | `_perform_pep_screening()` in `apps/management/views.py` | **Simulated.** Creates screening record; no external API; `matches = []`, status CLEAR. |
| **SANCTIONS**  | 1     | `_perform_sanctions_screening()` in `apps/management/views.py` | **Simulated.** Same as PEP – record only, no API, CLEAR. |
| **ADVERSE_MEDIA** | 1  | `_perform_adverse_media_screening()` in `apps/management/views.py` | **Simulated.** Same – record only, no API, CLEAR. |

**Note:** Model defines `WORLDCHECK` as a screening type but it is **not** run anywhere in the current code.

---

## Where It Is Implemented

| Step / area        | Location | Notes |
|--------------------|----------|--------|
| Trigger on vendor create | `apps/management/views.py` – `TempVendorManagementViewSet` create flow | Starts background thread that calls `_trigger_external_screening(vendor_id)` → `_perform_automatic_screening(vendor)`. |
| Manual trigger by vendor_code | `apps/management/views.py` – `ExternalScreeningView.post(request, vendor_code)` | Resolves temp_vendor by vendor_code, then calls same `_perform_automatic_screening(temp_vendor)`. |
| OFAC logic        | `apps/management/views.py` – `_perform_ofac_screening(vendor)` | Uses `OFACService` from `apps/vendor_core/services.py`. |
| PEP / Sanctions / Adverse media | `apps/management/views.py` – `_perform_pep_screening`, `_perform_sanctions_screening`, `_perform_adverse_media_screening` | Raw SQL to `external_screening_results` (and for OFAC, `screening_matches`). |
| Get results for UI | `apps/vendor_core/views.py` – `VendorScreeningViewSet.vendor_screening_results(request)` | `GET .../screening-results/vendor_screening_results/?vendor_id=<id>`. |
| Mark as cleared   | `apps/vendor_core/views.py` – `VendorScreeningViewSet.mark_as_cleared(request, pk)` | **pk = screening_id.** Should update only that screening and its matches (see Implementation plans). |
| Update match status | `apps/vendor_core/views.py` – `VendorScreeningViewSet.update_match_status(request, pk)` | pk = screening_id; body has match_id, status, notes. |
| Add note          | `apps/vendor_core/views.py` – `VendorScreeningViewSet.add_note(request, pk)` | pk = screening_id; should store note on screening (see Implementation plans). |
| Frontend page     | `VendorExternalScreening.vue` (route `/vendor-verification`) | Vendor dropdown (temp vendors), results list, match list, Clear All, per-match resolution, Schedule Screening modal. |
| Styles            | `VendorExternalScreening.css` | Layout, panels, dropdown, cards, status badges. |

---

## Working Condition Summary

- **OFAC:** Code path works; **data is mock only** (no live OFAC API). Enable real API when key/format are fixed.
- **PEP / SANCTIONS / ADVERSE_MEDIA:** Run and create records; **no external integrations** – always CLEAR, no matches.
- **UI:** Loads vendors and results, shows matches, resolution status, and notes. “Clear All” and “Update match status” call the backend; **mark_as_cleared/add_note** currently treat `pk` as vendor_id in code while the URL passes screening_id – **bug to fix** (see below).
- **Schedule Screening:** Modal and cron-like options exist in the frontend only; **no backend persistence or job** – “Schedule Screening” only shows a success message. Recurring schedule is not saved. To run screening on demand, use **“Run screening now”** (calls `POST .../management/vendors/<vendor_code>/external-screening/` and refreshes results).

---

## Improvements & Implementation Plans

**Detailed improvement plan per screening type, and how to add other external screening methods (so they run when a temp vendor is created):** see **[EXTERNAL_SCREENING_IMPROVEMENTS.md](./EXTERNAL_SCREENING_IMPROVEMENTS.md)**. It covers:
- Improvements for **OFAC, PEP, SANCTIONS, ADVERSE_MEDIA, WORLDCHECK** (current state + concrete steps).
- **Other methods** that are easy to plug in (World-Check, internal DPL, FATF jurisdictions, etc.).
- **Standard integration pattern**: same DB tables and UI; add one perform method and one call in `_perform_automatic_screening`.
- Optional **screening provider registry** when many types are used.

---

### 1. Fix `mark_as_cleared` and `add_note` (backend) — DONE

- **Issue:** URL is `screening-results/<screening_id>/mark_as_cleared/` (and same for `add_note`), but the view used `pk` as `vendor_id`, so the wrong screening could be updated or the call could fail.
- **Change applied:** Treat `pk` as `screening_id`. Use `self.get_object()` to load the screening (already tenant-filtered), get `vendor_id` from it, then:
  - **mark_as_cleared:** Update only that screening and its matches.
  - **add_note:** Update only that screening’s `review_comments`.

### 2. OFAC API key and real vs mock — DONE

- **Current:** API key is read from `settings.OFAC_API_KEY` (env `OFAC_API_KEY`). If set, the service calls the real OFAC API (v4: `apiKey`, `cases[]`); on error or if unset, it falls back to mock data. See `apps/vendor_core/services.py`. API errors are stored in the screening row’s `review_comments` for visibility.
- **Where to get the API key:** Sign up at **[OFAC-API.com](https://ofac-api.com)** (or see **[docs.ofac-api.com](https://docs.ofac-api.com)**). API key is in your account/settings; new accounts often get a trial. Set `OFAC_API_KEY=` in `.env` for production.

### 3. Schedule Screening – make it “happen”

- **Done (on-demand):** “Run screening now” button on the External Screening page calls `POST .../management/vendors/<vendor_code>/external-screening/` and refreshes results. Use it when a vendor is selected and has a vendor code.
- **Recurring schedule (not yet implemented):** The Schedule Screening modal is UI-only; no backend persistence or cron. To implement:
  - **Option A:** Add an API that saves a screening schedule (vendor_id/vendor_code, frequency/cron, next_run) and a management command or cron job that finds due schedules and triggers screening (e.g. same logic as `ExternalScreeningView`).
  - **Option B:** Reuse an existing scheduler (e.g. questionnaire assignment scheduler) and add “external screening” as a job type.
  - **Frontend:** Wire the Schedule submit to the new API and show errors if save fails.

### 4. PEP / Sanctions / Adverse media integrations

- **Plan:** When third-party APIs (e.g. World-Check, Refinitiv, or internal lists) are available, replace the “simulate only” logic in `_perform_pep_screening`, `_perform_sanctions_screening`, and `_perform_adverse_media_screening` with real search + match creation, reusing the same `external_screening_results` / `screening_matches` pattern as OFAC.

### 5. WORLDCHECK

- **Current:** In model only, not run.
- **Plan:** Either add `_perform_worldcheck_screening()` and call it from `_perform_automatic_screening`, or remove WORLDCHECK from the active list until a provider is chosen.

### 6. Tenant and security

- **Current:** JWT + tenant_id; vendor_core screening views filter by tenant where possible. EXTERNAL_SCREENING_FIX.md describes tenant handling and dev fallback.
- **Recommendation:** Keep tenant checks on all screening read/write paths; in production, do not fall back to “all vendors” when tenant_id is missing.

---

## Recommendations

1. **Fix mark_as_cleared and add_note** to use `screening_id` (pk) and scope updates to that screening (and document the contract in this file).
2. **Move OFAC API key** to configuration and document mock vs real in `services.py` and here.
3. **Implement Schedule Screening** with at least one of: new schedule table + job, or reuse of an existing scheduler; then wire the frontend to it.
4. **Add integration tests** for: trigger on create, manual trigger by vendor_code, get results by vendor_id, mark_as_cleared and update_match_status (and add_note once fixed).
5. **When adding real PEP/Sanctions/Adverse media:** Use the same “create screening row + matches” pattern as OFAC; keep status and risk logic consistent so the existing UI remains valid.

---

## File Reference

| Purpose | Path |
|--------|------|
| Screening logic (trigger + OFAC/PEP/Sanctions/Adverse) | `grc_backend/tprm_backend/apps/management/views.py` |
| OFAC service (mock + real API code) | `grc_backend/tprm_backend/apps/vendor_core/services.py` |
| Models | `grc_backend/tprm_backend/apps/vendor_core/models.py` (ExternalScreeningResult, ScreeningMatch) |
| Results + actions API | `grc_backend/tprm_backend/apps/vendor_core/views.py` (VendorScreeningViewSet) |
| Management trigger by vendor_code | `grc_backend/tprm_backend/apps/management/urls.py` (ExternalScreeningView) |
| Frontend page | `grc_frontend/tprm_frontend/src/pages/vendor/VendorExternalScreening.vue` |
| Frontend styles | `grc_frontend/tprm_frontend/src/pages/vendor/VendorExternalScreening.css` |
| Router (vendor verification) | `grc_frontend/tprm_frontend/src/router/index.js` (path `/vendor-verification`) |
| Tenant/auth fix notes | `grc_backend/tprm_backend/apps/vendor_core/EXTERNAL_SCREENING_FIX.md` |
| **Improvements by type + adding new methods** | `grc_backend/tprm_backend/EXTERNAL_SCREENING_IMPROVEMENTS.md` |
