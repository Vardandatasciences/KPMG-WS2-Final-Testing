# External Screening – Improvements by Type & Adding New Methods

This document describes **improvements per screening type** and **how to add other external screening methods** so they run automatically when a temp vendor is created.

---

## 1. Standard integration pattern (for all types)

When a **temp vendor is created** (or when "Run screening now" / manual trigger is used), the backend:

1. Calls `_perform_automatic_screening(vendor)` in `apps/management/views.py`.
2. For each screening type:
   - Insert a row in `external_screening_results` (vendor_id, screening_type, status=UNDER_REVIEW, search_terms, etc.).
   - Call the provider (API or list).
   - For each match: insert into `screening_matches` (screening_id, match_type, match_score, match_details).
   - Update the screening row (total_matches, high_risk_matches, status).
3. The same tables and UI work for every type; only the **provider** and **search inputs** change.

To **add a new screening type** you must:

- Add the type to `ExternalScreeningResult.SCREENING_TYPES` in `apps/vendor_core/models.py` (if not already there).
- Implement a `_perform_<type>_screening(vendor)` method that follows the pattern below (or use the shared helper).
- Call it from `_perform_automatic_screening(vendor)` in `apps/management/views.py`.

**Shared pattern for one screening type:**

```text
1. Resolve tenant_id from vendor.
2. INSERT into external_screening_results (vendor_id, screening_type, search_terms, status='UNDER_REVIEW', ...).
3. Get search terms from vendor (e.g. company_name, legal_name, directors).
4. Call external API or local list → get list of matches.
5. For each match: INSERT into screening_matches (screening_id, match_type, match_score, match_details).
6. Compute status (CLEAR / UNDER_REVIEW / POTENTIAL_MATCH / CONFIRMED_MATCH) from match count and risk.
7. UPDATE external_screening_results SET total_matches, high_risk_matches, status, last_updated.
8. Return {'screening_type': '<TYPE>', 'status': ..., 'total_matches': ...}.
```

---

## 2. Improvements by screening type

### 2.1 OFAC

| Item | Current state | Improvement |
|------|----------------|-------------|
| **Provider** | `OFACService` in `apps/vendor_core/services.py`. Real API when `OFAC_API_KEY` set; else mock. | Use env `OFAC_API_KEY` and `OFAC_API_BASE_URL` in production. Validate API response format; if provider changes, adapt payload in `search_entity()` and response parsing in `_make_request()`. |
| **Inputs** | company_name, legal_name, tax_id (in search_terms). Search uses `company_name or legal_name`. | Optionally add: registration number, country, aliases. Pass threshold/sources via settings if needed. |
| **Match storage** | Match details (name, source, programs, risk_level, etc.) in `match_details` JSON. | Keep; ensure `extract_match_details()` and risk logic stay aligned with API response. Add any new fields to JSON only (no schema change). |
| **Status/risk** | HIGH/MEDIUM/LOW from score; status from high_risk_count and match count. | Document thresholds in this file or in code. Consider configurable thresholds per tenant later. |
| **Errors** | On API error, fallback to mock. | In production, consider: store API error in screening row (e.g. review_comments or dedicated column), set status to UNDER_REVIEW, and surface in UI so ops can re-run or fix key. |

**Steps to improve OFAC:**

1. Set `OFAC_API_KEY` (and optionally `OFAC_API_BASE_URL`) in env/settings.
2. Test with real API; fix payload/headers if provider docs differ.
3. Optionally add a small “last_error” or comment field so failed API runs are visible.
4. Add unit tests for OFACService (mock HTTP) and one integration test that runs _perform_ofac_screening with a test vendor.

---

### 2.2 PEP (Politically Exposed Person)

| Item | Current state | Improvement |
|------|----------------|-------------|
| **Provider** | None. Simulated: creates screening row, no API, matches=[], status=CLEAR. | Integrate a PEP provider (e.g. Refinitiv World-Check, ComplyAdvantage, Dow Jones, or internal list). |
| **Inputs** | company_name, legal_name (in search_terms). | Add: beneficial owners, directors, country; search both entity and associated persons. |
| **Match storage** | No matches today. | Same as OFAC: one row per match in `screening_matches` with match_type, match_score, match_details (JSON). |
| **Status/risk** | Always CLEAR. | Derive from match list and risk levels returned by provider. |

**Steps to improve PEP:**

1. Choose provider (API or file-based PEP list).
2. Add `PEPService` in `apps/vendor_core/services.py` (or a shared `screening_services` module): e.g. `search_entity_and_related_persons(vendor) -> list[match]`.
3. In `_perform_pep_screening(vendor)`:
   - Keep existing INSERT for `external_screening_results`.
   - Call the new service with vendor fields (and optionally beneficial owners/directors from DB).
   - For each match: INSERT into `screening_matches` (reuse same structure as OFAC).
   - Set total_matches, high_risk_matches, status from results.
4. Add settings (e.g. `PEP_API_KEY`, `PEP_API_URL`) and document in this file.

---

### 2.3 SANCTIONS

| Item | Current state | Improvement |
|------|----------------|-------------|
| **Provider** | None. Simulated: screening row only, no API, CLEAR. | Use sanctions list(s): OFAC SDN, EU, UN, or a consolidated API (e.g. same OFAC API with different list, or Refinitiv/ComplyAdvantage sanctions). |
| **Inputs** | company_name, legal_name. | Same as OFAC; can share search terms. Some providers support bulk or entity+address. |
| **Match storage** | None. | Same pattern: one row per match in `screening_matches`. |
| **Status/risk** | Always CLEAR. | From match count and severity (e.g. list type, score). |

**Steps to improve SANCTIONS:**

1. Decide source: extend OFAC service to “sanctions” list, or use a separate Sanctions API.
2. Implement `_perform_sanctions_screening(vendor)` with real search (reuse OFACService if same API, or add `SanctionsService`).
3. Reuse the same INSERT/UPDATE flow as OFAC: one screening row, N match rows, then update status.
4. If using same provider as OFAC, consider a single service with `search_ofac()` and `search_sanctions()` to avoid duplication.

---

### 2.4 ADVERSE_MEDIA

| Item | Current state | Improvement |
|------|----------------|-------------|
| **Provider** | None. Simulated: screening row only, CLEAR. | Use adverse media / negative news API (e.g. Refinitiv, LexisNexis, Dow Jones, or ComplyAdvantage). |
| **Inputs** | company_name, legal_name. | Add: jurisdiction, industry; optional date range for news. |
| **Match storage** | None. | Store each article/alert as a match: match_type e.g. "Adverse Media", match_details = { title, source, date, url, snippet, risk_level }. |
| **Status/risk** | Always CLEAR. | From number and severity of articles (e.g. high/critical = POTENTIAL_MATCH or CONFIRMED_MATCH). |

**Steps to improve ADVERSE_MEDIA:**

1. Choose adverse media provider (API).
2. Add `AdverseMediaService` (e.g. in `apps/vendor_core/services.py`): input vendor (and optional filters), return list of matches with score/details.
3. In `_perform_adverse_media_screening(vendor)`: INSERT screening row, call service, INSERT each match into `screening_matches`, UPDATE screening status.
4. Add settings (e.g. `ADVERSE_MEDIA_API_KEY`, `ADVERSE_MEDIA_API_URL`). Optionally make date range or severity configurable.

---

### 2.5 WORLDCHECK (and other “extra” types)

| Item | Current state | Improvement |
|------|----------------|-------------|
| **Provider** | Not run. Type exists in model only. | Integrate Refinitiv World-Check (or equivalent) if licensed. |
| **Inputs** | Same idea: entity name, related persons, country. | Align with provider’s required fields. |
| **Match storage** | N/A. | Same as others: screening row + match rows. |
| **Trigger** | Not in `_perform_automatic_screening`. | Add `_perform_worldcheck_screening(vendor)` and call it from `_perform_automatic_screening`. |

**Steps to add WORLDCHECK:**

1. Add `_perform_worldcheck_screening(vendor)` in `apps/management/views.py` (or call a `WorldCheckService`).
2. In `_perform_automatic_screening`, after ADVERSE_MEDIA, add:
   - `try: worldcheck_result = self._perform_worldcheck_screening(vendor); if worldcheck_result: screening_results.append(worldcheck_result)`
3. Use same DB pattern: INSERT screening, INSERT matches, UPDATE status. Add settings for API key/URL.

---

## 3. Other external screening methods – easy to add on temp vendor create

The following methods are straightforward to add so they run **when a temp vendor is created** (and on “Run screening now” / manual trigger), using the same tables and UI.

### 3.1 List of methods that fit the current design

| Method | What it does | Ease of integration | Typical provider / source |
|--------|----------------|----------------------|----------------------------|
| **OFAC** | Sanctions / SDN list | Done (service exists; add key) | OFAC API, or OFAC-style APIs |
| **PEP** | Politically exposed persons | Easy (same pattern as OFAC) | World-Check, ComplyAdvantage, Dow Jones, internal list |
| **Sanctions** | Consolidated sanctions lists | Easy (reuse or extend OFAC, or separate API) | OFAC, EU, UN, Refinitiv, ComplyAdvantage |
| **Adverse media** | Negative news / reputational risk | Easy (same pattern) | Refinitiv, LexisNexis, Dow Jones, ComplyAdvantage |
| **World-Check** | Consolidated risk (PEP + sanctions + adverse) | Easy (one more type in same flow) | Refinitiv World-Check |
| **Custom / internal list** | Your own CSV/DB of high-risk names | Easy | Internal DB or file, parsed in a small service |
| **FATF high-risk jurisdictions** | Country risk only | Easy | Static list; check vendor country vs list |
| **Denied party / internal DPL** | Internal “do not use” list | Easy | DB or file |
| **Entity resolution / KYC** | Verify entity identity and links | Medium (more data, maybe different UI) | Dedicated KYC provider |

### 3.2 How to add a new type so it runs on temp vendor create

**Step 1 – Model (if new type)**  
In `apps/vendor_core/models.py`, add the type to `ExternalScreeningResult.SCREENING_TYPES`:

```python
SCREENING_TYPES = [
    ('WORLDCHECK', 'WorldCheck'),
    ('OFAC', 'OFAC'),
    ('PEP', 'PEP Database'),
    ('SANCTIONS', 'Sanctions'),
    ('ADVERSE_MEDIA', 'Adverse Media'),
    ('INTERNAL_DPL', 'Internal Denied Party List'),  # example new type
]
```

**Step 2 – Service (optional but recommended)**  
In `apps/vendor_core/services.py` (or a new module e.g. `screening_providers.py`), add a small class or function that:

- Takes `vendor` (and optional config).
- Returns a list of matches, each with: type, score, details (dict for `match_details` JSON).

Example:

```python
class InternalDPLService:
    def search(self, entity_name: str, **kwargs) -> dict:
        # Query internal DB or file; return {'matches': [...], 'error': None or str}
        ...
```

**Step 3 – Perform method**  
In `apps/management/views.py`, add a method that follows the same pattern as `_perform_ofac_screening`:

- Get tenant_id from vendor.
- INSERT `external_screening_results` (vendor_id, screening_type='INTERNAL_DPL', status='UNDER_REVIEW', search_terms=...).
- Call your service (e.g. `InternalDPLService().search(vendor.company_name)`).
- For each match: INSERT `screening_matches` (screening_id, match_type, match_score, match_details).
- UPDATE the screening row (total_matches, high_risk_matches, status).
- Return `{'screening_type': 'INTERNAL_DPL', 'status': ..., 'total_matches': ...}`.

**Step 4 – Register in automatic screening**  
In `_perform_automatic_screening`, add:

```python
# 5. Internal DPL (example)
try:
    dpl_result = self._perform_internal_dpl_screening(vendor)
    if dpl_result:
        screening_results.append(dpl_result)
except Exception as e:
    logger.error(f"Internal DPL screening failed for vendor {vendor.id}: {str(e)}")
```

**Step 5 – Config**  
Add any API keys or URLs to `backend/settings.py` and env (e.g. `INTERNAL_DPL_API_URL`, or path to file). Document in this file.

No frontend change is required: the UI already shows any `screening_type` and its matches from the same tables.

### 3.3 Optional: screening provider registry (for many types)

If you add many providers, you can centralise configuration and make adding a new type “config-only”:

1. **Registry**  
   A dict or list in settings or a small module, e.g.:

   ```python
   # screening_registry.py
   SCREENING_PROVIDERS = [
       ('OFAC', ofac_service.search_entity),
       ('PEP', pep_service.search),
       ('SANCTIONS', sanctions_service.search),
       ('ADVERSE_MEDIA', adverse_media_service.search),
       ('INTERNAL_DPL', internal_dpl_service.search),
   ]
   ```

2. **Generic runner**  
   `_perform_automatic_screening` loops over `SCREENING_PROVIDERS`; for each `(type_name, search_fn)` it:
   - Inserts the screening row,
   - Calls `search_fn(vendor)` or `search_fn(**search_terms)`,
   - Writes matches and updates the row.

3. **Adding a new type**  
   Implement the search function, add one entry to `SCREENING_PROVIDERS`, and (if new) add the type to `SCREENING_TYPES` in the model. No change to `_perform_ofac_screening`-style methods beyond the one new entry.

This keeps “when temp vendor is created” behaviour in one place and makes new external screening methods easy to plug in.

---

## 4. Summary table – improvements per type

| Type | Current | Main improvement | Config / provider |
|------|---------|------------------|--------------------|
| **OFAC** | Service exists; mock or real by key | Use real API in prod; optional error storage | `OFAC_API_KEY`, `OFAC_API_BASE_URL` |
| **PEP** | Simulated | Add PEP API or list; same DB pattern | e.g. `PEP_API_KEY`, `PEP_API_URL` |
| **SANCTIONS** | Simulated | Add sanctions API or extend OFAC | e.g. `SANCTIONS_API_*` or reuse OFAC |
| **ADVERSE_MEDIA** | Simulated | Add adverse media API | e.g. `ADVERSE_MEDIA_API_KEY` |
| **WORLDCHECK** | Not run | Implement and call from _perform_automatic_screening | e.g. World-Check API keys |
| **Internal DPL / custom** | Not present | Add type + service + one block in _perform_automatic_screening | Internal DB or file path |

---

## 5. File reference (where to edit)

| Change | File |
|--------|------|
| Add or extend screening type enum | `apps/vendor_core/models.py` – `ExternalScreeningResult.SCREENING_TYPES` |
| Add or extend provider logic | `apps/vendor_core/services.py` (or new `screening_providers.py`) |
| Add perform method and call it on vendor create | `apps/management/views.py` – `_perform_automatic_screening`, `_perform_*_screening` |
| Add settings / env for new provider | `backend/settings.py` and `.env` |
| Optional registry for many types | New module e.g. `apps/vendor_core/screening_registry.py` and use in `_perform_automatic_screening` |

Once a new type is added and called from `_perform_automatic_screening`, it runs automatically when a temp vendor is created and when “Run screening now” or the manual external-screening API is used, and results appear in the same External Screening UI.
