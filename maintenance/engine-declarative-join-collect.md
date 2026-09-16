# Maintenance change — `engine-declarative-join-collect`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/legible-engine` (DSL + `where`/`when` semantics), all profiles via inheritance
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved` (human in-conversation: "go with your recommendations")
- **Evidence gate:** `approved`
- **Change summary:** Close the two expressiveness gaps the conduit rebuild experiment surfaced (UC-03/UC-04) **declaratively**: (1) a synchronised (multi-`when`) **join** — a rule with several named conjuncts fires once when every conjunct has completed in the same flow; (2) declarative **collect** — `collect`/`distinct`/`scan` sources and a `collectBy` clause gather values into one `List` binding. Both are code-free (R3 preserved); they are **not** conceptbox's imperative `frames.query/filter/collectAs` (see below).

## Why not `frames.query/filter/collectAs`

`SYNCHRONIZATIONS.md` §"How syncs fan out" and `SYNC_ENGINE_EVOLUTION.md` §3 record CLAD's deliberate divergence: `where` is a declarative bind/filter phase, not imperative code; in-`where` filters/JSON assembly are declined (R3), and concept query actions as `where` sources are a deferred non-goal. This change adds **no** filters, query DSL, or JSON assembly — only:
- a multi-action `when` **join** (the paper's own model: "a multi-action join selecting which completed actions in the flow match", all sharing one flow token);
- **aggregation** as a value-producing source (`collect`, the declarative analogue of `collectAs`), not a query/filter surface.

Both are parseable, gate-checkable, and keep the `when`/`where`/`then` records mechanically auditable.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Single-trigger rules behave exactly as before; reactor `mvn test` green |
| Action ordering and sync deduplication | `preserved` | Dedup keyed on the primary matched action id + rule name (single-trigger unchanged); join fires once per matched set |
| Flow-token lineage | `preserved` | Joined emission's `parentActionId` = primary conjunct's action id; `causedBySync` = rule name |
| Storage/retention semantics | `preserved` | `collectBy`/`scan` read via the existing `Region`/`FactStore` SPI |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `SyncRule`/`WhereEvaluator`/`Source`/`Clause` javadoc; `SYNCHRONIZATIONS.md`, `SYNC_ENGINE_EVOLUTION.md`, `SYNC_PATTERNS.md`; templates |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `SyncRule` (Trigger list), `SyncEngine` (per-conjunct index + completeness + conjunct context), `WhereEvaluator` (Conjuncts, collect/distinct/scan/collectBy), `Source`/`Clause`/`Dsl`, new `Conjuncts` |
| Profile tests | yes | `JoinEngineTest`, `CollectClausesTest` |
| UC artefact chain | no (additive) | Future chains may use joined `When` rows / collect; no retrofit |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Join fires once when all conjuncts complete; order-independent; not while a conjunct missing | unit | `mvn -f reference-impl/pom.xml -pl legible-engine test` (`JoinEngineTest`) | pass | 3 cases |
| `collect` gathers into one List value; `distinct` dedups+orders; `scan` reads a predicate; `collectBy` groups frames | unit | same (`CollectClausesTest`) | pass | 4 cases |
| Single-trigger rules + stocked profiles unaffected | unit | `mvn -f reference-impl/pom.xml test` | pass | reactor BUILD SUCCESS |
| Gate suites unaffected | unit | `python3 -m unittest discover -s quality-gate/tests -t quality-gate/tests` | pass | OK (101 tests) |
| Gate pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact (UC-00-login stage 05) |
| Templates/verifiers support joined `When` + collect syntax | unit | `python3 -m unittest discover -s quality-gate/tests -t quality-gate/tests` (`test_join_collect_grammar`) | pass | 12 cases: chain join parse, composite-`When` grammar, join stem, collect forms, matrix + cycle graph, Java emitter `conj` chain |
| Docs/links updated | integration | `python3 quality-gate/verify_links.py` | pass | 306 links, 105 docs |
| Backward compat: UC-00 chain/syncs unchanged | integration | stage 01b/03 `verify_chain_grammar` / `verify_sync_matrix` / `verify_sync_cycle_graph` / `verify_sync_overlap` | pass | 16 rows, 7 syncs |

## Gates

### Design gate

Approved in-conversation by the human ("go with your recommendations") before implementation.

### Evidence gate

Approved: parity/verifier/template plumbing landed; the four validation commands (unittest, verify_artefacts, verify_links, reactor) are green and UC-00-login re-verifies (byte-for-byte backward compatible).

## Notes

- Join semantics: `SyncRule.Trigger` (named); the engine files the rule under **every** conjunct and checks all triggers have a matching committed completion in the flow; the latest matching invocation wins per conjunct (deterministic by flow order).
- Determinism: `collect` sorts its gathered values and `distinct`/`scan` de-duplicate + sort; `collectBy` emits one group per distinct `groupKey` in **frame order** and gathers each group's values in source-read order — because `region.read` returns an unordered set, the within-group value order is not part of the contract and is deliberately left unsorted so parallel `collectBy` clauses stay positionally aligned (see `engine-empty-safe-aggregate.md`).
- Downstream: the conduit rebuild fork inherits the engine files.
- **Experiment-found follow-ups (UC-05):** (a) the join stem joined *every* conjunct payload, exceeding `NAME_MAX` (255) for a 6-conjunct join — fixed to use payload-free conjunct completions; (b) Stage 03 could pass with a missing sync — added `verify_sync_transition_coverage.py` (derives the expected stems and fails on a shortfall; tolerates pre-v0.6 legacy names when counts agree).
