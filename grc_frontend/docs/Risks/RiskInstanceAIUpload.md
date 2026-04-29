# Risk Instance AI Upload — Pinia & state audit

**Component:** [`src/components/Risk/risk_ai_instance.vue`](../../src/components/Risk/risk_ai_instance.vue)  
**Route:** `/risk/ai-instance-upload`  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | AI-assisted **risk instance** creation from documents: **streaming** upload (`fetch` + `ReadableStream`), non-stream upload fallback, save pipeline, test endpoints; large wizard similar to register AI. |
| 1.2 | Route | `/risk/ai-instance-upload` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | — |
| 1.5 | Reusable | — |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk instance** intake |
| 1.8 | Domain | **Risk** instances |

---

## 2. Files analysed

- [`src/components/Risk/risk_ai_instance.vue`](../../src/components/Risk/risk_ai_instance.vue)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Options API** |
| 2.9 | Pinia | **Not used** (unlike `risk_ai.vue`) |
| 2.10–2.11 | API | **`fetch`** for `RISK_INSTANCE_AI_UPLOAD_STREAM`; `axios.post` for `RISK_INSTANCE_AI_UPLOAD`, `RISK_INSTANCE_AI_SAVE` |

---

## 4. Current data flow

1. Streaming `fetch` to `API_ENDPOINTS.RISK_INSTANCE_AI_UPLOAD_STREAM` with reader loop.  
2. Fallback `axios.post` `RISK_INSTANCE_AI_UPLOAD`.  
3. Save via `RISK_INSTANCE_AI_SAVE`.  
4. Field mapping / summary logs for computed vs extracted fields (console diagnostics).

---

## 5. Variable inventory

| Class | Local? | Pinia? |
|-------|--------|--------|
| Stream readers, chunk buffers, progress | **Yes** | No |
| Parsed instance candidates | Yes until save | Optional mirror `risk_ai` `aiState` pattern |
| Reviewer placeholder text | Yes | No |

---

## 6–7. Local vs Pinia

- **Local:** streaming + File + timers.  
- **Pinia (optional):** align with register AI — `risk.instanceAiWizard` slice OR shared `risk.aiWizard` with `mode: 'instance'|'register'`.  
- **After save:** `invalidateInstances()`.

---

## 8. API inventory

| Endpoint | Method |
|----------|--------|
| `API_ENDPOINTS.RISK_INSTANCE_AI_UPLOAD_STREAM` | `fetch` (stream) |
| `API_ENDPOINTS.RISK_INSTANCE_AI_UPLOAD` | POST |
| `API_ENDPOINTS.RISK_INSTANCE_AI_SAVE` | POST |

---

## 9–13. Store

**Actions:** `streamRiskInstanceAiUpload`, `saveRiskInstanceAi` — return progress via callback or `ref` in store **only if** you need cross-component progress (usually keep in component).

---

## 14. Repeated API calls

Stream vs non-stream paths should be **mutually exclusive** UI-wise; avoid double submit.

---

## 15. Prop drilling

None.

## 16. Forms analysis

Wizard-style steps (file pick, mapping, review): **keep all field state local**; on successful save call `invalidateInstances()` from store action wrapper.

## 17. Tables / filters / pagination

**N/A** or minimal (extracted rows preview only).

## 18. Dashboard / charts

**N/A**.

## 19. RBAC / permissions

API-enforced; optional gated route if module requires elevated role.

## 20. Async UI improvements

Stream progress UI; cancel/abort controller; timeout messaging; error retry on non-stream fallback.

## 21. Optimistic UI

**No** for save to instance register.

## 22. Smart vs presentational

Keep streaming orchestration in one smart component; extract row preview list as dumb child if it grows.

## 23. State normalization

**N/A** until extracted entities are reused across routes.

## 24. What / where / why

| # | What | Where | Why | Pri |
|---|------|-------|-----|-----|
| 1 | Align wizard state with `risk_ai` | `risk_ai_instance.vue` + store | One pattern for AI wizards | Medium |
| 2 | `invalidateInstances` | after save | Fresh instances list | High |

## 25. File-by-file migration

| File | Change |
|------|--------|
| `risk_ai_instance.vue` | optional store hooks; always invalidate via store |
| `stores/risk.js` | `saveRiskInstanceAi` + invalidate |

## 26. Priority matrix

- **P0:** invalidation after successful save.  
- **P1:** unified wizard state model with register AI.  
- **P2:** extract presentational subcomponents.

## 27. Step-by-step implementation

1. Add save action + invalidate.  
2. Refactor duplicate local vs store state.  
3. Test stream + fallback + large file.

## 28. Testing checklist

Stream completion; abort mid-stream; save failure; instances list after navigation.

## 29. Final developer guidelines

- Keep **streams** in component; Pinia holds **outcomes** and invalidation triggers.  
- **Do not** serialize `File` in Pinia/localStorage.
