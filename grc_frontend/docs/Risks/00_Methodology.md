# Risk docs — methodology & section index

Each page report in this folder follows the **same numbered checklist** derived from the enterprise Pinia audit prompt. Use this file to map section numbers to meaning.

| § | Title | What each page doc includes |
|---|--------|-------------------------------|
| 1 | Page / module summary | Subsections 1.1–1.8 (purpose, route, parent, children, reusable, layout, workflow, domain) |
| 2 | Files analysed | Explicit paths read for that page |
| 3 | Current Vue implementation | Subsections 2.1–2.14 (Composition/Options, ref/reactive/computed/watch, props/emits/inject, Pinia, API patterns, prop drilling, loading/error, RBAC) |
| 4 | Current data flow | 3.1–3.10 style narrative (source → API → storage → children → filters → refresh → stale) |
| 5 | Variable inventory | Table: name, file, component, declaration type, purpose, type classification, local vs Pinia, store/action, priority |
| 6 | Local state to keep | Category 5.1 + rationale |
| 7 | State to move to Pinia | Categories 5.2 / 5.3 |
| 8 | API call inventory | Per-endpoint table where applicable |
| 9 | Recommended store design | Store name(s), file path |
| 10 | Recommended state fields | Shape / what to omit |
| 11 | Recommended getters | Named getters |
| 12 | Recommended actions | Named actions |
| 13 | Cache-first plan | TTL, invalidate, refresh |
| 14 | Repeated API calls | Dedup list |
| 15 | Prop drilling | Cases + fix |
| 16 | Forms analysis | Per-form table or “N/A” |
| 17 | Tables / filters / pagination | Table or “N/A” |
| 18 | Dashboard / charts | Widget-level or “N/A” |
| 19 | RBAC / permissions | Variables + `permissionStore` plan |
| 20 | Async UI improvements | Skeleton, retry, empty, etc. |
| 21 | Optimistic UI | Action-by-action yes/no |
| 22 | Smart vs presentational | Component-level recommendations |
| 23 | State normalization | Nested data advice |
| 24 | What / where / why | Numbered improvements |
| 25 | File-by-file migration | Table |
| 26 | Priority matrix | P0/P1/P2 |
| 27 | Step-by-step implementation | Ordered steps |
| 28 | Testing checklist | bullets |
| 29 | Final developer guidelines | 27.1-style bullets for that page |

**Note:** For small pages, some sections are intentionally short (“N/A”) but the **heading is still present** for traceability to the master prompt.
