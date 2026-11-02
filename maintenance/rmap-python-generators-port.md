# Maintenance change — `rmap-python-generators-port`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `mixed`
- **Status:** `active` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** `reference-impl/legible-storage`,
  `reference-impl/legible-engine`, `reference-impl/java-micronaut`,
  `reference-impl/java-plain`, `clad.properties`, `quality-gate`
- **Feature-contract impact:** `preserved` (no example-UC action outcome,
  response contract, or flow-token change)
- **Design gate:** `approved` (the Rmap Python rewrite, generators, archive
  debug surface, and `httpStatus` rule were designed and proven on the
  experiment branch; this record governs their selective port onto the
  current `main` architecture)
- **Evidence gate:** `approved`
- **Change summary:** Port the additive work that does not depend on the
  superseded gate rewrite: the Python Rmap derivation/check tool
  (`rmap.py`, `verify_rmap_descriptor.py`, `verify_model_current.py`), the
  per-branch acceptance/trace generators (`chain_paths.py`,
  `generate_acceptance_spec.py`, `generate_trace.py`,
  `capture_observations.py`, `verify_trace_complete.py`), the archive debug
  surface, and the `httpStatus` verification rule. Do **not** port the
  parallel typed-model/gate rewrite (`artifact_model.py`, grouped rule
  families, `state.py`, `change.py`, gate deferral/reconciliation); remote
  `main` keeps its newer iterative/gate architecture.

## Mechanism

- **Rmap is one derivation implementation.** `quality-gate/rmap.py` reads the
  approved Stage 03b conceptual block and emits both the migration and the
  runtime descriptor. `RmapSchemaLoader` loads the descriptor at runtime;
  `RmapDeriver`/`RmapMigration` are removed. Stage 04a runs `rmap.py --check`
  and `verify_rmap_descriptor.py` when an Rmap migration is configured.
- **Incremental/baseline support.** `rmap.py --alter` discovers a deployed
  baseline (`rmap.baseline`, `_generated/rmap-baselines/`,
  `_system/rmap-baselines/`) and emits additive DDL; `--record-baseline`
  writes one.
- **Generators are per-branch.** `chain_paths.py` computes acceptance paths
  from the feature's frozen use case/chain; `generate_acceptance_spec.py`
  and `generate_trace.py` render the 04c acceptance spec and 05 trace;
  `capture_observations.py` reads the archive debug surface;
  `verify_trace_complete.py` blocks Stage 05 when a scenario has no trace
  entry.
- **Archive surface.** `DebugApi`/`FlowArchiveBuffer`/`DebugController`
  expose runtime observations without requiring a live app.
- **`httpStatus`.** Sync `then` blocks reject transport-frame fields; the
  HTTP status remains an adapter concern.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No sync/use-case contract edits; generators consume existing contracts. |
| Action ordering and sync deduplication | `preserved` | No sync-engine semantics change. |
| Flow-token lineage | `preserved` (extended) | Archive capture reads existing flow tokens; trace generator asserts scenario coverage. |
| Storage/retention semantics | `preserved` | Login schema/migration stay byte-identical; Rmap emits the same table set from the same model. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `RELATIONAL_RMAP.md`, `RELATIONAL_LOWERING.md`, `QUALITY_GATE.md`, `SYNCHRONIZATIONS.md`, stage contexts. |
| Profile configuration or deployment files | yes | `clad.properties` gains `storage.persistent` and `rmap.*`; login migration remains the runtime schema. |
| Engine/runtime implementation | yes | `legible-storage` Rmap loader/store; `legible-engine` archive buffer; `java-micronaut` debug endpoint. |
| Profile tests | yes | Python Rmap/generator suites; Java Postgres and archive suites; existing 501-test baseline extended. |
| UC artefact chain | no | Frozen examples only gain the derived descriptor. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Rmap derivation matches the conceptual model | unit | `quality-gate/tests/test_rmap.py` | pass | 28 tests green after porting the parser fix |
| Rmap rejects stale migrations/descriptors | unit | `test_rmap.py`, `test_model_current.py` | pass | login descriptor current; stale fixture detected |
| Generators produce stable paths/acceptance/trace | unit | `test_chain_paths.py`, `test_acceptance_generation.py`, `test_trace_generation.py` | pass | deterministic output assertions |
| Trace completeness blocks a missing scenario | unit | `test_trace_complete.py` | pass | missing-scenario failure path |
| `httpStatus` rule rejects transport frames | unit | `test_sync_then_shape.py` | pass | rule suite green |
| Python gate baseline | gate | `python3 -m pytest -q quality-gate/tests` | pass | 506 passed |
| Artefact pipeline | gate | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact; `model_current` checks the login descriptor |
| Java/Postgres Rmap and archive | integration | `mvn test -f reference-impl/pom.xml` | pass | 140 tests, 0 failures/errors/skips with `-Dclad.storage=postgres` |

## Gates

### Design gate

Approved by the selective-port decision: port only the additive Rmap,
generator, archive, and `httpStatus` work; keep remote `main`'s newer
iterative/gate architecture and do not import the parallel typed-model
rewrite. The port reuses the already-approved experiment designs; no new
design decision is introduced.

### Evidence gate

Pending. Requires the Java/Postgres reactor, the artefact gate, and the full
Python suite green on this branch.

## Notes

- Rollback: revert the branch; remote `main` remains the release baseline.
- The experiment report at `docs/experiments/expense-approvals.md` is
  historical evidence, not a shipped gate.
