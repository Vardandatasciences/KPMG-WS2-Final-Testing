# Risk Register AI Document Upload — Pinia & state audit

**Component:** [`src/components/Risk/risk_ai.vue`](../../src/components/Risk/risk_ai.vue)  
**Route:** `/risk/ai-document-upload`  
**Parent:** `App.vue` (keep-alive applies unless excluded — name check: component `name: 'RiskRegisterAIDocumentUpload'` vs `keep-alive` exclude list uses `'CreateRisk'` etc.; **this page may be kept alive**).

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | AI-assisted **risk register** upload: steps (upload → processing → review → success), file upload, progress, extracted risks review/save, optional analysis generation. |
| 1.2 | Route | `/risk/ai-document-upload` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | — |
| 1.5 | Reusable | — |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk** bulk intake via AI |
| 1.8 | Domain | **Risk**; file processing |

---

## 2. Files analysed

- [`src/components/Risk/risk_ai.vue`](../../src/components/Risk/risk_ai.vue)
- [`src/stores/risk.js`](../../src/stores/risk.js) (`aiState`, `setAiState`, `resetAiState`)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Hybrid:** `setup()` returns `{ riskStore }` + **Options** `data()` / `methods` |
| 2.9 | Pinia | **`useRiskStore`** for **AI wizard persistence** |
| 2.10–2.11 | API | `axios` shim → `POST` `RISK_AI_UPLOAD`, `RISK_AI_SAVE`, `RISK_GENERATE_ANALYSIS` |

---

## 4. Current data flow

1. Local `data()` holds `currentStep`, `selectedFile`, progress, `extractedRisks`, etc.  
2. `saveProcessingState()` copies much of this into **`riskStore.aiState`** (including serialized file metadata).  
3. `loadProcessingState()` reads store; discards if older than 24h.  
4. Upload/analysis/save hit AI endpoints.

**Duplication risk:** same concepts in **`data()`** and **`riskStore.aiState`**.

---

## 5. Variable inventory

| Variable | Location | Local? | Pinia? |
|----------|----------|--------|--------|
| `currentStep`, `isProcessing`, `processingProgress` | `data` + `aiState` | Pick **one** source | If resume across nav: **Pinia only** + component sync |
| `selectedFile` | `data` | File object **local only** | Store **metadata** `{ name, size }` only |
| `extractedRisks` | `data` / store | Large — prefer **local** during session | Persist only if product requires |

---

## 6. Local state to keep

- **`File` object**, streaming controllers, timers, DOM progress UI.  
- Ephemeral validation.

---

## 7. State to move / consolidate in Pinia

- **Either** remove duplicate `data()` fields and drive wizard from **`riskStore.aiState`** only, **or** stop persisting to store and keep entirely local until submit.  
- On successful save: **`invalidateRisks()`** so register list picks up AI-created risks.

---

## 8. API inventory

| Endpoint | Method | Notes |
|----------|--------|-------|
| `API_ENDPOINTS.RISK_AI_UPLOAD` | POST | multipart |
| `API_ENDPOINTS.RISK_AI_SAVE` | POST | fallback string replace in code |
| `API_ENDPOINTS.RISK_GENERATE_ANALYSIS` | POST | fallback string replace |

---

## 9–12. Store

- Clarify **`aiState`** schema; add `aiWizardStatus`, `aiWizardError`.  
- **Action:** `uploadRiskAiDocument(formData)`, `saveExtractedRisks(payload)`, `generateRiskAnalysis(payload)` — each updates progress fields in store **or** returns to component for local-only progress.

---

## 13. Cache-first

- Not for upload stream.  
- After save: invalidate risks list cache.

---

## 14. Repeated API calls

- None obvious; risk is **duplicate state** not duplicate network.

---

## 15–29. Summary

- **Prop drilling:** none.  
- **Forms:** wizard — simplify state ownership.  
- **Optimistic:** no for regulatory save.  
- **Testing:** resume after refresh (if Pinia persist), 24h expiry, large file abort, invalidate register.

---

## 29. Guidelines

- **Never** put `File` in persisted localStorage.  
- **Choose** single wizard state owner (component vs Pinia) to reduce bugs.
