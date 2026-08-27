# Artefact impact matrix — `fire-after-commit-engine`

> Iterative change to the UC-00-login worked example. The engine is re-architected
> (maintenance route, `maintenance/fire-after-commit-engine.md`); this matrix
> records the feature-side re-lowering under R17.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `presentation`
- **Earliest re-entry stage:** `01a`
- **Status:** `closed`
- **Change summary:** Reconcile the bootstrap entry action from `Web/handle` to
  `Web/request` (the paper's name, collapsing the old "bootstrap handoff
  exception"), and re-lower the UC-00-login implementation from the RDF/SPARQL
  `ConceptAgent`/`SyncAgent` engine to the fire-after-commit engine (`Concept`
  map→map + declarative `SyncRule` `when/where/then`). Outcomes, action order,
  response contracts, and the business-concept set are **unchanged**.

| Artefact | Touched? | How |
|---|---|---|
| Use case | no | scenarios + postconditions unchanged |
| Concept(s) | no | same business concepts (`UserNaming`, `PasswordAuth`, `Session`), same state/actions/outcomes |
| Sync(s) | yes | `WhenWebHandleRouted…` → `WhenWebRequestRouted…`; `when`/`then` trigger renamed `Web/handle` → `Web/request` |
| SPEC slices | no | same action signatures + outcome enums |
| Flow tests | yes | `login.feature` + `login-flow-test.md` Web bootstrap references renamed |
| Concept tests | no | same R14/R16 field-value assertions (outcomes/fields unchanged) |
| Sync tests | yes | `sync-test-derivation.md` sync names re-derived |
| Production code | yes | `*Concept extends ConceptAgent` → `*Concept implements Concept`; 7 `SyncAgent` SPARQL classes → declarative `SyncRule`s in `LoginSyncs`; `concept:*` graphs → `FactStore` regions |
| Verification trace | yes | runtime-evidence surface changes from `/api/dev/*` SPARQL to the new `DebugApi`; chain-table ↔ runtime assertions re-recorded |

## Re-derivation order

1. 01a — responsibility map: `Web` actions `handle` → `request`
2. 01b — chain tables: `Web.handle` → `Web.request` (rows 1–2)
3. 03 — syncs: `WhenWebHandleRouted…` → `WhenWebRequestRouted…`
4. 03a — dependency cards: `Web-card.md`, `UserNaming-card.md`, `PasswordAuth-card.md` trigger refs
5. 04a — storage mapping: note `FactStore` relation regions (in-memory)
6. 04c — flow tests: `login.feature` bootstrap references
7. 04d-green — concept implementation: `ConceptAgent` → `Concept` (map→map, own `Region`)
8. 04e-green — sync implementation: `SyncAgent` (SPARQL) → declarative `SyncRule`; `sync-test-derivation.md`
9. 05 — verification trace: re-record runtime evidence from the new debug surface

## Notes

- The scratch prototype (`scratch/legible-engine-prototype/`, 53 tests) is the
  reference for the re-lowered code; parity, sync semantics, concurrency, and the
  flow-token back-trace are already proven there and re-run in
  `reference-impl/java-legible/`.
- Spec stages 01a–03 change only in the `Web` bootstrap action *name*; the
  business concepts, outcomes, and chains are untouched.
