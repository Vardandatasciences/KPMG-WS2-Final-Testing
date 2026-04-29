# Tailoring Risk — Pinia & state audit

**Component:** [`src/components/Risk/TailoringRisk.vue`](../../src/components/Risk/TailoringRisk.vue)  
**Route:** `/risk/tailoring`  
**Parent:** `App.vue` → `router-view`.

---

## 1. Page / module summary

| # | Item | Detail |
|---|------|--------|
| 1.1 | Purpose | Create a new risk using an **optional existing risk** as template (`selectedRiskId`); hybrid **Composition API** (`setup`) + template; category dropdown UX; POST new risk. |
| 1.2 | Route | `/risk/tailoring` |
| 1.3 | Parent | `App.vue` |
| 1.4 | Children | `PopupModal` (global) |
| 1.5 | Reusable | Popup service |
| 1.6 | Layout | Global shell |
| 1.7 | Workflow | **Risk** templating / creation variant |
| 1.8 | Domain | **Risk** |

---

## 2. Files analysed

- [`src/components/Risk/TailoringRisk.vue`](../../src/components/Risk/TailoringRisk.vue)

---

## 3. Current Vue implementation summary

| # | Topic | Finding |
|---|--------|---------|
| 2.1 | API | **Hybrid** — `setup()` with `ref`, `computed`, `watch` + large template |
| 2.9 | Pinia | **Not used** |
| 2.10–2.11 | API | `axios` shim; same master endpoints as `CreateRisk` |

---

## 4. Current data flow

1. `GET` `RISKS_FOR_DROPDOWN` → `allRisks`.  
2. On select existing risk, load fields into `risk` reactive object.  
3. Masters: `BUSINESS_IMPACTS`, `RISK_CATEGORIES`, add endpoints.  
4. `POST` `RISKS` with `riskData`.  
5. `PUSH_NOTIFICATION`.

---

## 5. Variable inventory (key)

| Variable | Declared | Local? | Pinia? |
|----------|----------|--------|--------|
| `risk` | `reactive` | Yes | No |
| `selectedRiskId`, `showCategoryDropdown`, `categorySearch` | `ref` | Yes | No |
| `allRisks` | loaded | No | Use `risk.risks` from store |

---

## 6–7. Local vs Pinia

- **Local:** form + category UX.  
- **Pinia:** `fetchRisks` for dropdown; `createRisk` / invalidate after POST.

---

## 8. API inventory

Same cluster as CreateRisk: `RISKS_FOR_DROPDOWN`, `BUSINESS_IMPACTS`, `ADD_BUSINESS_IMPACT`, `RISK_CATEGORIES`, `ADD_RISK_CATEGORY`, `RISKS`, `PUSH_NOTIFICATION`.

---

## 9–13. Store / cache

- Reuse **`risk.fetchRisks`** instead of local `allRisks` fetch.  
- TTL on register list.

---

## 14–29. Summary

- **Repeated:** duplicate of CreateRisk master fetches.  
- **Forms:** stay local.  
- **Migration:** `storeToRefs` for `risks`; keep `setup()` pattern.  
- **Testing:** template from existing risk; new category modal; submit success invalidates register.
