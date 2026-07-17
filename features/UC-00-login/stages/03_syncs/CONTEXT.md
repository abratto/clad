# Stage 03 — Synchronizations

## Why this stage exists

Coordination is **declarative** so that **no concept imports another**
(hard rule R1) and so each cross-concept link is reviewable as a small
`when … where … then` rule rather than being buried in imperative
code. Each sync also commits to one of the four legal data-flow
patterns (A/B/C/D), which makes Stage 03a's audit and Stage 04e's TDD
mechanical.

**Feeds:**

- `<name>.sync.md` → 03a (every `then` call and every `where` clause is tabulated; Pattern D reads are flagged), 04c (the sync chain is what the outer flow test asserts), 04e (one inner red→green TDD pass per sync), 05 (the verifier checks that every observed call is authorised by a sync or a use-case scenario).

**Agent stance for this stage:** if you reach for an `if`, you are in
the wrong file. Branching belongs inside a concept action's outcomes;
the sync just says *"when outcome X fires → then call Y."*

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios to satisfy |
| `../02_concepts/output/` | 4 | Concepts available to coordinate |
| `../02b_chain-table/output/` | 4 | The action chain each sync formalises |
| `../../../../methodology/architecture/SYNCHRONIZATIONS.md` | 3 | Sync semantics |
| `../../../../methodology/architecture/SYNC_PATTERNS.md` | 3 | The four `where` patterns (A/B/C/D) |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules (R3) |
| Skill: `clad-sync-design` | 3 | Sync design reference |
| `../../../../templates/sync.md` | 3 | Output template |

## Process

For each scenario in the use case, identify the chain of concept actions
that fulfils it. Each coordination link becomes one sync.

Before writing sync prose, build a per-sync **Sync Contract Matrix** from
the approved chain table and concept files. For each transition, record
the source row id, target row id, exact `when` signature, exact `then`
signature, and any allowed literals. Copy tokens verbatim.

If any action signature, outcome name, argument name, or literal differs
between `../02b_chain-table/output/` and `../02_concepts/output/`, stop
and reopen Stage 02. Stage 03 does not normalize earlier-stage drift.

Syncs use paper-style block syntax: `sync <Name>`, `when { }` / `where { }` /
`then { }`, with `Concept/action:` namespace qualifiers (slash separator,
colon after action), `?variable` bindings, and `=> [ outcome ]` for
outcome matching. The sync name and file stem follow the compressed rule
grammar from `SYNCHRONIZATIONS.md`:
`When<TriggerConcept><TriggerAction><TriggerCompletion>Then<TargetConcept><TargetAction>[For<Scope>]`.
All `?variable`s are scoped across the entire sync.

The `where` clause is a **declarative query language** supporting:

| Construct | Purpose | Example |
|---|---|---|
| `bind ( uuid() as ?x )` | Identifier minting | `bind ( uuid() as ?user )` |
| `Concept: { ... }` | State query (Pattern D) | `User: { ?user email: ?email }` |
| `OPTIONAL { ... }` | Conditional read | `OPTIONAL { Tag: { ?a tag: ?t } }` |
| `BIND ( ?x AS ?_eachthen )` | GROUP BY aggregation | `BIND ( ?article AS ?_eachthen )` |

What `where` still must NOT do:
- **Branch on business conditions** — `if ?role = "admin"` belongs in a concept's outcomes
- **Perform I/O or side effects** — reads are for binding; writes belong in `then`
- **Mutate state** — `where` is read-only
- **Execute custom computation** — hashing, signing, arithmetic, JSON assembly all belong in concept actions

Response bodies may use only constants from the target chain row or
fields explicitly emitted by an earlier approved outcome and declared in
`where`. Exact literals are locked: numeric status codes stay numeric,
and string/status values keep their approved casing and hyphenation.

Each sync's `Cites` section names the use-case scenarios it satisfies.
Each sync also includes a "Where clause patterns" table mapping every
binding to its Pattern (A/B/C/D) for Stage 03a's audit.

An optional `output/<scenario-name>.sync-summary.md` may be emitted as a
derived, non-canonical per-scenario review table (`Step | Sync | When |
Then | Where summary | Key`) if it is copied mechanically from the
canonical sync files and introduces no new logic.

## Outputs

- `output/WhenWebHandleRoutedThenUserLookupByUsernameForLogin.sync.md`
- `output/WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin.sync.md`
- `output/WhenUserLookupByUsernameRefusedThenWebRespondForLogin.sync.md`
- `output/WhenPasswordAuthCheckOkThenSessionGrantForLogin.sync.md`
- `output/WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.sync.md`
- `output/WhenPasswordAuthCheckLockedThenWebRespondForLogin.sync.md`
- `output/WhenSessionGrantGrantedThenWebRespondForLogin.sync.md`

## Verify

### Automated checks

```
python3 ../../../../quality-gate/verify_sync_matrix.py --sync-dir output --chain-dir ../02b_chain-table/output
python3 ../../../../quality-gate/verify_scenario_coverage.py \
  --goals ../../../_system/stages/00_actor-goal/output/goals.md \
  --usecase ../01_usecase/output/usecase.md \
  --chain-dir ../02b_chain-table/output \
  --sync-dir output
python3 ../../../../quality-gate/verify_file_manifest.py --dir output --expected "WhenWebHandleRoutedThenUserLookupByUsernameForLogin.sync.md,WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin.sync.md,WhenUserLookupByUsernameRefusedThenWebRespondForLogin.sync.md,WhenPasswordAuthCheckOkThenSessionGrantForLogin.sync.md,WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.sync.md,WhenPasswordAuthCheckLockedThenWebRespondForLogin.sync.md,WhenSessionGrantGrantedThenWebRespondForLogin.sync.md"
```

- **verify_sync_matrix.py:** every sync has a valid Sync Contract Matrix.
- **verify_scenario_coverage.py:** every scenario is satisfied by at least one sync.
- **verify_file_manifest.py:** `output/` contains exactly the expected sync files.

### Semantic checks (human)

- No sync contains `if`/`else` over business state.
- No sync persists state.
- Every sync has a one-row Sync Contract Matrix that names the exact
  source row, target row, `when`, `then`, and allowed literals it was
  derived from.
- Numeric transport status codes remain numeric, not quoted strings.
- String literals and status values preserve their exact approved casing
  and hyphenation.
- Response payloads contain only chain-row constants or fields explicitly
  emitted by earlier approved outcomes and declared in `where:`.
- If any 03 signature differs from 02b or 02, stop and reopen Stage 02
  instead of resolving the mismatch inside a sync.
- **Cross-stage check (back):** every named scenario in
  `../01_usecase/output/usecase.md` is satisfied by at least one sync.
- **Cross-stage check (forward):** every sync contract written here must
  later lower to one Stage 04e `SyncAgent` implementation; Stage 04e-green
  verifies this with `quality-gate/verify_sync_implementation_parity.py`.
- **Filename contract:** the files in `output/` match the `Outputs`
  section exactly, with no extras and no omissions.
- **Sync naming:** every filename stem and `sync <Name>` header follows
  the compressed `When<Trigger>Then<Target>` rule grammar.

## Gate

Auto-advances (next human gate: Stage 03b). The quality-gate scripts
(`verify_sync_matrix.py`, `verify_scenario_coverage.py`,
`verify_file_manifest.py`) must all pass before advancing.

## Next stage

→ [`../03a_dependency-review/CONTEXT.md`](../03a_dependency-review/CONTEXT.md) — Dependency review

The agent proceeds to Stage 03a without a human gate.
