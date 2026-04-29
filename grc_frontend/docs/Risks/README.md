# Risk module — per-page Pinia / state audits

This folder contains **one markdown report per routed Risk screen** under [`src/components/Risk`](../../src/components/Risk). Each report follows the same enterprise checklist: purpose, routes, Vue patterns, data flow, variable inventory, Pinia recommendations, API inventory, cache/RBAC/async UI, migration steps, and testing.

**Section index (maps to the master audit prompt):** [00_Methodology.md](./00_Methodology.md).

## Reports (route → component)

| Report | Route(s) | Component |
|--------|----------|-----------|
| [CreateRisk.md](./CreateRisk.md) | `/risk/create`, `/risk/create-risk` | `CreateRisk.vue` |
| [RiskRegisterList.md](./RiskRegisterList.md) | `/risk/riskregister-list` | `RiskRegisterList.vue` |
| [RiskDashboard.md](./RiskDashboard.md) | `/risk/riskdashboard` | `RiskDashboard.vue` |
| [RiskInstances.md](./RiskInstances.md) | `/risk/riskinstances-list` | `RiskInstances.vue` |
| [CreateRiskInstance.md](./CreateRiskInstance.md) | `/risk/create-instance` | `CreateRiskInstance.vue` |
| [RiskResolution.md](./RiskResolution.md) | `/risk/resolution` | `RiskResolution.vue` |
| [RiskWorkflow.md](./RiskWorkflow.md) | `/risk/workflow` | `RiskWorkflow.vue` |
| [RiskScoring.md](./RiskScoring.md) | `/risk/scoring` | `RiskScoring.vue` |
| [ScoringDetails.md](./ScoringDetails.md) | `/risk/scoring-details/:riskId` | `ScoringDetails.vue` |
| [TailoringRisk.md](./TailoringRisk.md) | `/risk/tailoring` | `TailoringRisk.vue` |
| [RiskKPI.md](./RiskKPI.md) | `/risk/riskkpi` | `RiskKPI.vue` |
| [BaselKPIs.md](./BaselKPIs.md) | `/risk/baselkpis` | `baselkpi.vue` |
| [RiskAIDocumentUpload.md](./RiskAIDocumentUpload.md) | `/risk/ai-document-upload` | `risk_ai.vue` |
| [RiskInstanceAIUpload.md](./RiskInstanceAIUpload.md) | `/risk/ai-instance-upload` | `risk_ai_instance.vue` |
| [SystemIdentifiedRisks.md](./SystemIdentifiedRisks.md) | `/risk/system-identified-risks` | `SystemIdentifiedRisks.vue` (+ `SystemRiskWorkflowModal.vue`) |
| [RiskThreshold.md](./RiskThreshold.md) | `/risk/threshold` | `RiskThreshold.vue` |
| [ViewRisk.md](./ViewRisk.md) | `/view-risk/:id` | `ViewRisk.vue` |
| [ViewInstance.md](./ViewInstance.md) | `/view-instance/:id` | `ViewInstance.vue` |

## Shared context

- **Router:** [`src/router/index.js`](../../src/router/index.js) (risk paths).
- **Shell:** [`src/App.vue`](../../src/App.vue) — `Sidebar`, `GlobalNavbar`, `keep-alive` (excludes `CreateRisk`, `CreateRiskInstance`).
- **Existing Pinia:** [`src/stores/risk.js`](../../src/stores/risk.js) (partial; used heavily only by some screens).
- **Singleton cache:** [`src/services/riskService.js`](../../src/services/riskService.js) — overlaps with Pinia for risks / instances.
- **Cross-module note:** [`src/components/Policy/Sidebar.vue`](../../src/components/Policy/Sidebar.vue) calls `SYSTEM_RISKS_STATS` for badge count; align with Pinia after `SystemIdentifiedRisks` store slice is implemented.

## Conventions used in each report

- **Pinia only** for shared/API state recommendations (no Vuex/React/RTK/Zustand/Vue Query).
- **Local** = `ref` / `reactive` / Options `data` for UI-only concerns.
- **Priority:** High / Medium / Low for migration items.
