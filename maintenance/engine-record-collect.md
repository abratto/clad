# Maintenance change — `engine-record-collect`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/legible-engine` (new `where` clause), `reference-impl/java-legible`, `reference-impl/java-micronaut-postgres`, `reference-impl/java-plain` (inherit)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Add a **record-form `collect`** — `collect ( ?a ?b as ?rows )` / `collect by ?key ( ?a ?b as ?rows )` — that gathers a **binding subset per frame** into a list of records. This is the one genuine expressiveness gap against ConceptBox's `collectAs([a, b], results)`; it is grouping/projection, not assembly, so it stays on the declarative side of R3.

## Why

CLAD's `collect` gathers a **single variable's** values per list:
`collect ( ?loanId as ?openLoans )`. ConceptBox's
`collectAs([user, username, total], results)` gathers **correlated records** —
one entry per frame carrying several bindings. CLAD has no declarative form for
that, and both workarounds are bad:

- **Parallel `collect`s** produce two lists (`?copies` / `?dueDates`) that cannot
  be zipped without losing the copy↔dueDate correlation — the position of a copy
  in one list is not guaranteed to line up with its due date in the other
  (`collect` sorts its values; `collectBy`'s within-group order is deliberately
  unsorted and unspecified).
- **Pushing row-shaping into a concept action** moves a binding concern out of
  the sync, where it belongs, into a concept that owns no such concern.

Demonstrated shape: a response that must report a member's open loans, each row
carrying `{ copy, dueAt }`. The chain-table row's input names `openLoans`; the
only correct source is one record per open loan.

## Rule

### Syntax (proposed)

```
collect ( ?copy ?dueDate as ?rows )            # one List of records per group
collect by ?key ( ?copy ?dueDate as ?rows )    # one List of records per key group
```

Two or more variables before `as` is the **record form**; one variable keeps the
existing value-collect form. No new keyword. (`distinct` is **not** defined for
the record form — record equality is ambiguous, and the surface stays bounded.)

### Semantics

- Each record is the ordered projection of the selected variables from a frame
  (`{ copy: ?, dueDate: ? }`).
- **Ungrouped** `collect ( ?a ?b as ?rows )` groups frames by the tuple of the
  **non-collected bindings**, so the surviving frame keeps its other fields and
  `?rows` lists the collected subset for that group.
- **Grouped** `collect by ?key ( ?a ?b as ?rows )` groups by `?key` instead.
- Ordering is **frame order**, not sorted — the whole point is to preserve
  copy↔dueDate correlation by position, exactly as `collectBy` preserves it for
  parallel clauses (`maintenance/engine-empty-safe-aggregate.md`).
- Empty-safe like `collectBy`: a group with no frames still emits one frame with
  `?rows = []` (a zero-item collection is a value, not an absence).

### Why this is R3-clean

Gathering a binding subset is **grouping and projection**, not assembly: it reads
no new state, computes nothing, filters nothing, and constructs no payload. It is
the same category as the already-accepted `collect by ?key`, generalised from one
value to a tuple of already-bound values. It is explicitly **not** ConceptBox's
declined surface:

- `frames.filter($ => $[count] >= 10)` — a computation in `where`; still declined
  (see the separate `sync-comparison-guards` discussion).
- JSON payload assembly — still the primary adapter's job
  (`verify_sync_then_shape`).

### Open design sub-decisions (for the gate)

1. **Arity-based syntax vs. a `collect record ( … )` keyword.** Proposed:
   arity-based (no new keyword; the grammar already distinguishes one vs. several
   variables). The keyword form is the alternative if arity is judged too subtle.
2. **Grouping key.** Proposed: non-collected bindings (keeps the frame's other
   fields; matches the demonstrated `openLoans` shape). Alternative: collapse all
   frames into one list regardless of other bindings (simpler, but discards the
   surviving frame's fields).

## Mechanism

The record form mirrors the existing frame-set aggregate `Clause.CollectBy`,
applied in `WhereEvaluator` (`reference-impl/legible-engine/src/main/java/dev/legible/engine/WhereEvaluator.java:182`),
with the same empty-safe path (`WhereEvaluator.java:51`). It adds a sibling
`Clause.RecordCollect` handled in `WhereEvaluator.apply`; the engine's
fire-after-commit and exactly-once properties are untouched (a `where` clause
does not emit, consume, or reorder tokens).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | New clause only; no existing sync uses it |
| Action ordering and sync deduplication | `preserved` | Clause position, not rule ordering, is unaffected; no new emission |
| Flow-token lineage | `preserved` | `collect` neither emits nor consumes tokens |
| Storage/retention semantics | `preserved` | Reads only via the existing `Region`/`FactStore` SPI |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `SYNCHRONIZATIONS.md` §"Collect"; `SYNC_PATTERNS.md` §"Collect / aggregate bindings" |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `Clause.RecordCollect`; `WhereEvaluator` (`apply` + record-collect method + empty-safe path); `Dsl` factories |
| Gate scripts | yes | `artifact_parsers.py` recognises/parses the multi-variable collect form for the grammar + Pattern-D audit |
| Profile tests | yes | new `WhereEvaluator`/`CollectClausesTest` cases; grammar property test in `quality-gate/tests/` |
| UC artefact chain | no (additive) | Future chains may use record-form collect; no retrofit |

> **Note:** `generate_syncs_java.py` emits only `when`/`then` and leaves `where`
> to the author (a `// TODO` marker for Pattern D). The Java lowering surface for
> `where` clauses is the `Dsl` factories, so record-form collect adds a `Dsl`
> factory rather than an emitter branch. If the gate prefers, the emitter can also
> gain a TODO hint naming the record form.

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Ungrouped record collect binds one list of per-frame records | unit | `CollectClausesTest.recordCollectGathersABindingSubsetPerFrame` | pass | 2 records, copy/dueAt paired |
| Grouped record collect binds one list per key group | unit | `CollectClausesTest.recordCollectGroupsByTheNamedKey` | pass | 2 groups |
| Correlation preserved — the record is the projection, not the raw value | unit | `CollectClausesTest.recordCollectGathersABindingSubsetPerFrame` | pass | per-record map keyed by `?loanId` carries its own `?copy`/`?dueAt` |
| Empty group emits one frame with `[]` (empty-safe) | unit | `CollectClausesTest.recordCollectEmitsEmptyListWhenNoFrameCarriesTheBindings` | pass | one frame, `?rows = []` |
| Grammar detects the multi-variable form; single-var stays value form | unit | `test_join_collect_grammar.py::…test_record_collect_forms_are_detected` | pass | — |
| Engine suite (isolated-module compile) | unit | `mvn -q test -f reference-impl/pom.xml -pl legible-engine` | pass | 41 tests |
| Canonical profile build | integration | `mvn test -f reference-impl/pom.xml -pl legible-engine,java-legible -am` | pass | BUILD SUCCESS (engine 41, java-legible 40) |
| Gate pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact, 0 WARNs |
| Gate suite green | unit | `python3 -m pytest quality-gate/tests -q` | pass | 231 passed |
| Engine maintenance contract holds (fire-after-commit, exactly-once) | integration | `ENGINE.md` §"Maintenance contract" | pass | new clause is read-only in `where`; emits/consumes no token; no emission or ordering change |

## Gates

### Design gate

To be approved **before** implementation (this record touches the engine).
The two sub-decisions above are the gate's subject. Approve with
`./clad approve-maintenance engine-record-collect design`.

### Evidence gate

Cleared: the engine suite (41) and the canonical profile build (`legible-engine,java-legible -am`) are BUILD SUCCESS; the new evaluator and grammar tests pass; the gate pipeline is intact (0 WARNs) and the gate suite is green at 231. The engine maintenance contract holds: the clause is read-only in `where`, emits and consumes no flow token, and changes no emission or ordering, so fire-after-commit and exactly-once are untouched.

## Notes

- **R3 boundary.** Grouping/projection only — no filter, no arithmetic, no JSON
  assembly. The declined ConceptBox surface is untouched.
- **Ordering is the feature.** Frame order (not sorted) is what makes the
  correlation usable; sorting would silently break the copy↔dueDate pairing.
- **Not a query surface.** It gathers bindings the frame already has; it does not
  read new state beyond whatever an earlier clause already read.
- **Out of scope:** record-form `distinct` (record equality is ambiguous) and any
  per-record computed field (that is assembly, and belongs in a concept action).
