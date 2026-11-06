# Maintenance change — `sync-where-grammar`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Parse the documented `where { }` sync grammar and compare it clause-by-clause to the Java `.where(...)`, so binding provenance is machine-checked instead of prose.
- **Dependent re-entry:** `none`

## Why

The `where` grammar was documented (`templates/sync.md`, `SYNCHRONIZATIONS.md`)
but never parsed, so implementation parity compared only the trigger, targets,
route and argument names — not which source a binding reads. A rule could change
a binding from `triggerField("userId")` to `triggerInput("userId")` and pass
(experiment finding 3, "strict parity checks only a slice of behavior").
Reviewing the paper authors' ConceptBox engine confirms the frames model
(`frames.query` / `filter` / `collectAs`); CLAD already documents the equivalent
declarative grammar, so the fix is to parse and enforce that grammar, not invent
a parallel one.

## Mechanism

`quality-gate/sync_where.py` parses the documented forms (`bind ( <source> as
?var )`, `Concept: { ?id field: ?var }`, `OPTIONAL { … }`, `BIND ( ?x AS ?y )`,
`fanOut ( … )`, `absent ( … )`, `collect [distinct|by ?k] ( … )`) into a
normalized `Clause` list, and parses the Java `.where(...)` DSL into the same
list (`sync_where.py:parse_spec_where`, `:parse_java_where`). Stage 03
(`verify_sync_matrix.py`) fails a `where` block it cannot parse; the strict
parity check compares `clause_signatures(spec) == clause_signatures(java)`, and a
spec with no `where` block whose implementation has `.where(...)` is
*unresolved* (fail), not a silent pass.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Checks only; no runtime change |
| Action ordering and sync deduplication | `preserved` | Unchanged |
| Flow-token lineage | `preserved` | Unchanged |
| Storage/retention semantics | `preserved` | Unchanged |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `templates/sync.md`, `SYNCHRONIZATIONS.md`, 03 CONTEXT |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | — |
| Profile tests | yes | `test_sync_where_grammar.py`, `test_sync_gate_soundness.py` |
| UC artefact chain | no | Stage checks tightened; completed features are not re-checked |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| documented grammar parses | unit | `test_sync_where_grammar.py::SpecGrammarTests` | pass | suite green |
| spec and Java normalize equal | unit | `test_sync_where_grammar.py::SpecJavaParityTests` | pass | suite green |
| malformed where block fails Stage 03 | unit | `test_sync_gate_soundness.py::SyncMatrixSoundnessTests::test_malformed_where_block_fails` | pass | suite green |
| changed binding source fails parity | unit | `...::test_where_binding_source_mismatch_fails` | pass | suite green |
| impl where without spec block is unresolved | unit | `...::test_impl_where_without_spec_block_is_unresolved` | pass | suite green |
| full gate | unit | `python3 -m pytest quality-gate/tests -q` | pass | 580 passed |

## Gates

Design and evidence gates approved; record closed.

## Notes

- Backward-compatible: a spec with only a prose "Where clause patterns" table
  (no `where { }` block) is grandfathered; the generator's `bind ( <source> as
  ?var )` placeholder is accepted.
- Rollback: remove the parity comparison; the parser is additive.
