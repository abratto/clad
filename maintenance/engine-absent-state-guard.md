# Maintenance change — `engine-absent-state-guard`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `reference-impl/legible-engine` (new `where` clause), `reference-impl/java-legible` (inherits), `reference-impl/java-micronaut-postgres` (inherits), `reference-impl/java-plain` (inherits)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** No existing sync's `when`, `then`, outcomes, order or response changes; this adds a clause a new sync may use. `where` gains a **negative state pattern**, `absent ( Concept ; ?subject ; predicate )`, so a declarative rule can say *"the ones that do not have X"*. It is the binding-set transformation `WHERE` already performs (§6.5 of the pattern paper), expressed as an operator rather than as code.

## Why

Demonstrated need, found by UC-04-return-copy in the library-lending experiment. Its response must report the member's **remaining open** loans:

```
chain row 11/12 input:  { loanId, dueAt, returnedAt, overdue, openLoans }
```

A loan is open exactly when it has no `returnedAt`. Every `where` source CLAD
has — `Bind`, `FanOut`, `StateRead`, `subjects(...)`, `scan(...)`, and the
`collect`/`distinct`/`collectBy` wrappers — *enumerates* state. None can
express an absence, and `collect` takes no filter. So the flow can gather the
member's loans and cannot exclude the closed ones, and the field the approved
chain table (and the use case) promised is not derivable.

This is not a one-off shape. "The ones that don't have X" is ordinary: unread
notifications, unshipped orders, uncatalogued copies, users without a profile.

### What the sources say

- **The pattern paper** (Meng & Jackson, *What You See Is What It Does*,
  Onward! 2025, §5–6) gives `where` a uniform semantics as a function from a
  binding to a **set of bindings**, with conjunctive multi-property state blocks
  (§5.5) and queries that map one binding to many (§6.5). A negative pattern is
  a binding-set transformation in exactly that sense.
- **The paper authors' reference implementation** (conceptbox, MIT 61040)
  filters freely — `where` is an `async` function over `Frames`, an `Array`
  subclass, so `filter`/`map`/`query`/`collectAs` are all available
  (`design/background/implementing-synchronizations.md`).
- **CLAD recorded both halves of this** in
  [`engine-when-input-matching.md`](engine-when-input-matching.md)
  §"Deliberate non-adoptions": (1) **imperative/computed** `where` — declined,
  because hidden logic in the declarative binding phase breaks
  readable-at-a-glance and the Stage 03a–05 machinery built on Pattern A/B/C/D;
  (2) parametrized concept **query actions** as `where` sources — deferred,
  "revisit only with **demonstrated need** recorded in a new maintenance
  record". That trigger has now fired.

This record takes neither deferred path. It does **not** reverse (1): an
operator is not hidden logic — it is legible, has no computation, and stays
auditable. It does **not** take (2), because a query action would move the
filter into the concept, which is the design the paper's own rationale pushes
away from ("discrimination belongs in concept outcomes" applies to
discrimination the concept owns, not to a rule selecting among that concept's
state).

## Rule

- **Clause.** `absent ( <concept> ; <subject> ; <predicate> )` — keep the frame
  only if `<subject>` has **no** value for `<predicate>` in `<concept>`. An
  optional fourth operand narrows it to a value:
  `absent ( <concept> ; <subject> ; <predicate> ; <source> )` — keep the frame
  only if no value equals the source's.
- **Position.** `absent` is a clause like any other: it appears in the `where`
  block in order, operates on the frames the clauses above it produced, and
  composes with `collect`/`distinct`/`collectBy` and with `optional`.
- **Pattern label.** A state read is Pattern D. An `absent` clause is a **D⁻**
  read: it consults concept state and produces no binding. It is audited the
  same way — same card row, same summary, same review.
- **Fail-closed.** If the subject variable is **not bound**, the clause drops
  the frame. It never asserts an absence it could not check. The consequence is
  the documented aggregate trap: a `where` that yields no frames means the sync
  never fires, so the flow stops rather than responding with wrong data. That is
  deliberate: returning closed loans as "remaining open" is the worse failure,
  and `/api/dev/stuck` surfaces the stopped flow.
- No arithmetic, no JSON assembly, no arbitrary code — R3 is unchanged.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | New clause only; no existing sync in any profile uses it |
| Action ordering and sync deduplication | `preserved` | Clause position, not rule ordering, is unaffected |
| Flow-token lineage | `preserved` | `absent` reads concept state; it neither emits nor consumes tokens |
| Storage/retention semantics | `preserved` | Read-only over `Region.read`; no new facts |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | yes | `Clause.Absent`; `Dsl.absent(...)`; `WhereEvaluator` case; `DebugApi` where-clause rendering |
| Profile tests | yes | new `AbsentClauseTest` in `legible-engine`; the four profiles inherit |
| Gate scripts | yes | `artifact_parsers` recognises `absent(...)` as a D⁻ read for the 03a cards and the pattern summary |
| Templates | yes | `templates/sync.md` §"Negative state pattern"; the 03 stage contract names it |
| Methodology docs | yes | `SYNC_PATTERNS.md` (D⁻ alongside A/B/C/D), `SYNCHRONIZATIONS.md` §"Absence" |
| UC artefact chain | yes | UC-04's join responses gain `openLoans` (the reason for the change) — an R17 re-entry on that feature, not a contract change |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Absence keeps the frame; presence drops it | unit | `AbsentClauseTest.shouldKeepTheFrameWhenThePropertyIsAbsent` | pass | — |
| The value form drops only on the matching value | unit | `AbsentClauseTest.shouldDropOnlyWhenTheValueMatches` | pass | — |
| An unbound subject drops the frame (fail-closed) | unit | `AbsentClauseTest.shouldFailClosedWhenTheSubjectIsUnbound` | pass | — |
| A later clause still sees the frame's bindings | unit | `AbsentClauseTest.shouldPreserveEarlierBindings` | pass | — |
| Composes with `collect` for "the ones that don't have X" | unit | `AbsentClauseTest.shouldCollectTheSubjectsWithoutTheProperty` | pass | — |
| Engine suite | unit | `mvn -q test -f reference-impl/pom.xml -pl legible-engine` | pass | 37 tests |
| Whole reactor unaffected | integration | `mvn test -f reference-impl/pom.xml` | pass | 37+19+40+24+16, BUILD SUCCESS |
| 03a audits the read | unit | `test_join_collect_grammar.py::…test_absent_state_pattern_is_detected_as_a_concept_read` | pass | — |
| UC-04's `openLoans` becomes derivable | acceptance | UC-04's join syncs bind `collect` over an `absent`-filtered fan-out | pending | first consumer — the experiment's next step |

## Gates

### Design gate

Approved in-conversation: the absent-state guard is the fix for the
demonstrated need, taking the declarative-operator route rather than
conceptbox's imperative filter or the deferred query-action path.

### Evidence gate

To be recorded before commit.

## Notes

- The name is `absent`, not `filter`: the operator cannot compute, cannot
  assemble, and can only negate a state pattern. Keeping the name narrow keeps
  R3's line visible.
- `verify_maintenance_change_readiness.py` requires exactly one **active** record while
  maintenance-scoped changes are unmerged (its base is `origin/main`), so this record stays
  `active` on the branch and is closed when the change lands.
- This record does **not** retire the deferred query-action item; a rule that
  needs a *parameterised lookup* (rather than an exclusion) still has no
  declarative source, and that remains the documented gap.
