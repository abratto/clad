# Maintenance change — `config-and-dead-code`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (root `clad.properties`, engine doc comments, gate scripts)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Remove dead `clad.properties` keys and stale doc comments; consolidate duplicated gate-status parsing. No runtime behaviour changes.

## Why

A read-only audit found configuration and code that nothing reads or that
describes the retired `java-micronaut-jena` profile:

- `clad.properties` carried an unread legacy engine section (`engine.dataset.*`,
  `engine.dispatch.timeout.*`, `engine.archive.*`) and an unenforced,
  never-read `stages.usecase.require-sequence-diagram`; the canonical engine
  reads none of them.
- `FlowArchiveSink`/`FlowArchiveBuffer` doc comments referenced those removed
  keys.
- `promote_concepts.py` and `verify_concept_corpus_current.py` each carried
  their own Gate-2 status regex instead of the canonical parser in
  `verify_stage_sequence.py`.
- `verify_sync_route_filters.py`'s docstring described a retired
  `SyncTrigger`/SPARQL profile and was garbled.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No artefact or code behaviour changes |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | The canonical engine already ignored the removed keys; the durable profile hardcodes its sink/buffer |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | yes | `FlowArchiveSink`/`FlowArchiveBuffer` doc comments only |
| Gate scripts | yes | `promote_concepts.py`, `verify_concept_corpus_current.py` use `verify_stage_sequence.gate_status`; `verify_sync_route_filters.py` docstring |
| Gate tests | no | Existing coverage exercises the refactor |
| Templates | yes | 01_usecase contract: the interaction sketch is optional (the key is gone) |
| Methodology docs | no | — |
| Corpus | no | — |
| Feature artefacts | yes | UC-00 01_usecase contract mirrors the template |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Gate suite stays green | unit | `pytest quality-gate/tests -q` | pass | 211 |
| Promotion still requires a literal `approved` Gate 2 | unit | `test_concept_registry.py::PromotionTests` | pass | — |
| The reactor builds | integration | `mvn -B -ntp test -f reference-impl/pom.xml` | pass | BUILD SUCCESS (7 modules) |
| The pipeline is intact | integration | `verify_artefacts.py` | pass | — |

## Gates

### Design gate

Approved in-conversation: remove the dead keys, reword the stale comments, and
centralize gate-status parsing.

### Evidence gate

Cleared: gate suite 211 (macOS + Linux), reactor BUILD SUCCESS, pipeline intact.

## Notes

- `jackson.serialization-inclusion` is **kept** (R13 points at it as the
  canonical setting) but marked documentation-only in the file.
- `SyncRule.of` is *not* legacy — the durable `java-micronaut-postgres` profile
  still uses it — so only the stale docstring phrase was removed, not any
  parsing branch.
