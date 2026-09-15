# Maintenance change — `engine-subjects-inverse-read`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/legible-engine` (DSL + `where` source), all profiles via inheritance
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved` (human in-conversation: "go with b")
- **Evidence gate:** `approved` (test matrix below)
- **Change summary:** Add a declarative **inverse-index read** to the `where` clause: `Source.Subjects(concept, predicate, object)` / `Dsl.subjects(...)` collects the subjects `s` for which `predicate(s) = object` into **one List value**, the dual of the existing forward `StateRead` (`predicate(subject)` → values) and backed by the already-present `Region.subjects(predicate, value)` SPI. It lets a sync hand a resolved membership set to a downstream action (the conduit rebuild experiment's UC-04 `tag`/`favorited` article filters: `Catalog.list` must receive the article ids that carry a tag / were favorited by a user, owned by `Tagging`/`Favoriting`).

## Why not `frames.query/filter/collectAs`

CLAD **deliberately declines** conceptbox's imperative `frames.query/filter/collectAs` — `SYNCHRONIZATIONS.md` §"How syncs fan out — the Frames model" (the `where` clause is a declarative bind/filter phase only; rich lookups go through `FanOut` + state reads) and `SYNC_ENGINE_EVOLUTION.md` §3 + standing comparison (in-`where` imperative filters / JSON assembly = *deliberate divergence, R3*; concept query actions as `where` sources = *deferred non-goal*). This change is **not** that: it adds no filters, no aggregation expressions, and no imperative query surface — only a code-free index lookup that returns a collection where `StateRead` returns scalars. It is the natural dual of a source already in the model, and mirrors the storage SPI method `Region.subjects` that `Clause.FanOut` already uses (where `FanOut` yields one frame per subject; `Subjects` yields the set itself when a single downstream invocation needs the membership as a whole). The declined imperative behaviour remains declined.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No stocked-example flow/outcome changed; reactor `mvn test` green |
| Action ordering and sync deduplication | `preserved` | New read only; rule identity unchanged |
| Flow-token lineage | `preserved` | Read evaluated inside `where`; lineage unchanged |
| Storage/retention semantics | `preserved` | Uses existing `Region.subjects`; storage SPI unchanged |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `Source`/`WhereEvaluator` javadoc; this record + the `SYNCHRONIZATIONS.md`/`SYNC_ENGINE_EVOLUTION.md` distinction |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `legible-engine` `Source.Subjects`, `Dsl.subjects`, `WhereEvaluator.resolve` case |
| Profile tests | yes | `SubjectsInverseReadTest` (new) |
| UC artefact chain | no (feature-less) | Features use it when needed; no retrofit |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Collects all subjects for an object as one List value | unit | `mvn -f reference-impl/pom.xml -pl legible-engine test` (`SubjectsInverseReadTest`) | pass | `Tests run: 3, Failures: 0` |
| Empty object → no value (so `optional` can drop); known object with no matches → empty collection | unit | same | pass | covered in the same test |
| Existing engine + profile suites unaffected | unit | `mvn -f reference-impl/pom.xml test` | pass | all modules green |
| Gate suites unaffected | unit | `python3 -m unittest discover -s quality-gate/tests -t quality-gate/tests` | pass | OK |
| Gate pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact |

## Gates

### Design gate

Approved in-conversation by the human ("go with b") before implementation.

### Evidence gate

Evidence recorded from the executed test runs; Status set `closed` with the change commit.

## Notes

- Semantics: the collected subjects are de-duplicated and deterministically ordered (`TreeSet`).
- `WhereEvaluator.resolve` returns the collection as a **single** element so one `Bind` yields one frame carrying the whole set — a downstream `then` invocation receives it whole (contrast `FanOut`, which yields one frame per subject).
- Downstream: the conduit rebuild fork's `app/` engine copy inherits via file sync.
