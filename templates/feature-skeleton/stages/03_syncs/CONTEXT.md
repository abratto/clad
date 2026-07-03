# Stage 03 — Synchronizations

## Why this stage exists

Coordination is **declarative** so that **no concept imports another**
(hard rule R1) and so each cross-concept link is reviewable as a small
`when … where … then` rule rather than being buried in imperative
code. Each sync also commits to one of the four legal data-flow
patterns (A/B/C/D), which makes Stage 03a's audit and Stage 04e's TDD
mechanical.

**Feeds:**

- `<name>.sync.md` → 03a (every `then` call and every `where` clause is tabulated; Pattern D reads are flagged), 04c (the sync chain is what the outer flow test asserts), 04e (one inner red→green TDD loop per sync).

**Agent stance for this stage:** if you reach for an `if`, you are in
the wrong file. Branching belongs inside a concept action's outcomes;
the sync just says *"when outcome X fires → then call Y."*

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios to satisfy |
| `../02_concepts/output/` | 4 | Concepts available to coordinate |
| `../02b_chain-table/output/` | 4 | The action chain each sync formalises |
| Skill: `clad-sync-design` | 3 | Sync design reference (see skills/ directory) |
| `../../../../methodology/architecture/SYNCHRONIZATIONS.md` | 3 | Sync semantics |
| `../../../../methodology/architecture/SYNC_PATTERNS.md` | 3 | The four legal `where` patterns (A/B/C/D) |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rule R3 |
| `../../../../templates/sync.md` | 3 | Output template |

## Process

Count the transitions in every approved chain table in
`02b_chain-table/output/` for this feature. Each transition (row N →
row N+1) becomes exactly one sync file. Do not collapse multiple
transitions into one sync.

Before writing any sync prose, build a per-sync **Sync Contract Matrix**
from the approved chain table and concept files. For each transition,
capture exactly these tokens: source row id, target row id, `when`
signature, `then` signature, and allowed literals. Copy them verbatim.
This is a preflight check, not a place to reinterpret names.

If any action signature, outcome name, argument name, or literal differs
between 02b and 02, stop and reopen Stage 02 before writing any sync
file. Stage 03 derives coordination from approved contracts; it does not
repair contract drift.

For each transition, write one rule-shaped
`When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>].sync.md`:
- `when:` the outcome that fires (e.g. `Account.validate(...) -> Valid`)
- `where:` data-routing only — field-path references and sync constants.
  No function calls, no arithmetic, no I/O. If you need a computation,
  it belongs inside the concept action, not here. Label every line with
  its pattern: `A:` / `B:` / `C:` / `D:` per `SYNC_PATTERNS.md`.
- Pattern A binds only from names already declared by the approved
  `when` token. It may not read `body.*`, `request.*`, or other raw
  transport structure. If a needed Pattern A name is missing, reopen
  Stage 02b and fix the trigger contract before continuing.
- `where:` is binding-only. No JSON assembly, no ad hoc projection
  extraction, and no payload reshaping. If a downstream action needs a
  different shape, the upstream concept action must emit it explicitly.
- `where:` is also under a **literal lock**. Status codes remain numeric,
  not quoted strings. Status values keep their exact casing and
  hyphenation. Action argument names must match the Stage 02 signatures
  exactly.
- `where:` may not invent convenience fields. A response sync may use
  only constants from the target chain row, or fields explicitly emitted
  by the triggering/prior action outcomes and declared in `where:`.
- `then:` the next concept action to invoke.

The sync file stem and `sync <Name>` header must match the naming rule
from `SYNCHRONIZATIONS.md`: prefix with `When`, use `Then` between the
trigger and target sides, and append `For<Scope>` when the same edge can
occur in multiple routes, flows, or use cases.

Syncs are declarative — no imperative branching, no state, no I/O.
Every sync's `Cites` section names the use-case scenario it satisfies.
Optionally also emit `output/<scenario-name>.sync-summary.md` as a
derived, non-canonical review table that summarizes one scenario's syncs
as `Step | Sync | When | Then | Where summary | Key`. If present, it
must be mechanically derivable from the canonical per-sync files and may
not introduce new logic.

## Outputs

- `output/<name>.sync.md` — one per coordination rule

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_sync_matrix.py \
  --sync-dir output --chain-dir ../02b_chain-table/output
python3 ../../../../quality-gate/verify_scenario_coverage.py \
  --goals ../00_actor-goal/output/goals.md \
  --usecase ../01_usecase/output/usecase.md \
  --chain-dir ../02b_chain-table/output \
  --sync-dir output
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<name>.sync.md,…"  # one per coordination rule
```

- **verify_sync_matrix.py:** every sync has a complete Sync Contract Matrix
  with valid row IDs, `when`/`then` signatures, and allowed literals.
- **verify_scenario_coverage.py:** every use-case scenario is cited by at
  least one sync.
- **verify_file_manifest.py:** `output/` matches the expected sync list.

### Semantic checks (human)

- No sync contains imperative branching or persists state.
- **Sync count:** the number of sync files in `output/` equals the
  number of transitions in the chain table(s) for this feature (each
  chain-table row-to-row arrow = one sync).
- **Sync naming:** every filename stem and `sync <Name>` header follows
  `When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>]`.
- **Where-clause discipline:** no `where` line contains a function call,
  arithmetic expression, or I/O operation. Every line is a field-path
  reference (`when.field`, `result_of(<#N>).field`) or a sync constant
  (exact approved literal). Pattern labels (`A:` / `B:` / `C:` / `D:`) are
  present on every `where` line.
- **Pattern A discipline:** every Pattern A binding reads only from a
  name declared by the approved `when` token. No `body.*`, `request.*`,
  or other raw transport paths are permitted in Stage 03.
- **Sync Contract Matrix:** each sync can be traced back to one source
  row and one target row from 02b, with `when`/`then` signatures copied
  exactly from the approved contracts.
- **Literal lock:** exact literal identity is preserved across stages.
  Numeric transport status codes stay numeric, string literals keep their
  exact casing and hyphenation, and action argument names match the 02
  concept signatures exactly.
- **No invented payload fields:** every field referenced in `then`,
  including `Web.respond(...)` bodies, is either a Stage 03 constant from
  the chain row or a field explicitly emitted by an earlier approved
  action outcome and declared in `where:`.
- **Declare before use:** every variable referenced in a `then` line
  is either carried directly from the `when` outcome's flow token or
  explicitly declared in a `where` clause with a pattern label. No
  undeclared variable references permitted.
- **Cross-stage signature lock:** if any 03 `when`/`then` signature does
  not exactly match the corresponding 02b row or the 02 concept action
  signature, stop and reopen Stage 02 instead of guessing.
- **Cross-stage check (back):** every named scenario in
  `01_usecase/output/usecase.md` is satisfied by at least one sync, or
  is a `Web`-only failure path (call this out explicitly in the sync
  pack's notes).
- **Cross-stage check (back to 02b) — repeated action backstop:** scan
  the full sync set for any `<Concept>.<action>` that appears as the
  `then` target of one sync and also as the `when` source of another,
  where both share the same concept action name. If the same
  `<Concept>.<action>` appears more than once across the `then` lines
  of the sync set, this indicates that the chain table contained a
  repeated action invocation that was not caught at the 02b gate. Stop,
  do not proceed to 03a, and surface the finding to the human: name the
  duplicated action and the chain table rows that produced it. The chain
  table must be corrected and re-approved before the syncs can be
  re-derived.

## Gate

Auto-advances (next human gate: Stage 03b). The `verify_sync_matrix.py` and
`verify_scenario_coverage.py` scripts must pass before advancing.

## Next stage

→ [`../03a_dependency-review/CONTEXT.md`](../03a_dependency-review/CONTEXT.md) — Dependency review

The agent proceeds to Stage 03a without a human gate.
