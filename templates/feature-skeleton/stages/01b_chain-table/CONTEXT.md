# Stage 01b — Chain table (per scenario)

## Why this stage exists

The **choreography review surface** — one scenario per file, easier to
read than six declarative syncs at once. 01b is also the **canonical
resolver for action-name disputes**: if a sync spec (Stage 03)
disagrees with a chain table, the table wins. That rule keeps Stage 03
from silently inventing names that nothing else will recognise.

**Feeds:**

- `<scenario>-chain.md` → 02 (every action used must be declared in the matching concept spec with the same outcome enum), 03 (each row formalises into a sync `when`/`then` link), 03a (the chain is the dependency graph 03a audits), 04c (the flow test asserts the token sequence the chain predicts).

**Agent stance for this stage:** every row is an explicit `When -> Then`
edge with a named outcome. If you cannot name the outcome or the
trigger, the concept set is wrong — go back to 01a, do not invent.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios to choreograph |
| `../01a_responsibility-map/output/responsibility-map.md` | 4 | Available concepts and their actions |
| Skill: `clad-chain-table` | 3 | Chain table reference (see skills/ directory) |
| `../../../../methodology/architecture/SYNCHRONIZATIONS.md` | 3 | What syncs are (so the chain table can be lifted into them later) |
| `../../../../templates/chain-table.md` | 3 | Output template |

## Process

For each named scenario in `01_usecase/output/usecase.md`, produce one
file `output/<scenario-name>-chain.md`. The chain is the ordered
sequence of explicit `When -> Then` steps that fulfils the scenario,
with the downstream action's `Inputs`, resulting `Outcome`, and one-line
justification. Use the actions and concepts already named in the
responsibility map — do not invent new ones.

This mapping is deterministic: one top-level Stage 01 scenario becomes
one Stage 01b chain file. Keep that scenario's extensions in the same
file as additional branch rows when they share the same trigger and user
goal. Do not split ordinary failure extensions into separate chain files.

Each row is one transition branch. If one action can complete with
multiple outcomes that lead to different `Web.respond[...]` contracts or
different next actions, split those branches into separate rows instead
of collapsing them into one line.

A row may also be a **join**: its `When` cell lists several conjuncts
separated by `∧` (U+2227), each optionally named `name:
Concept/action[Outcome]`. Such a row fires once when every conjunct has
completed in the same flow, and still carries exactly one `Then` and one
`Outcome` token. Single-conjunct rows keep the classic form. See
`../../../../methodology/architecture/SYNCHRONIZATIONS.md`.

If a downstream action needs request-originated data, the approved 01b
row must name those carried fields on the trigger contract itself
(for example `Web.request[Routed(email, password)]`). Stage 03 may bind
Pattern A values only from names that 01b has already declared.

Optionally include a Mermaid `stateDiagram-v2` as a derived view. Do not
use `sequenceDiagram`. The diagram must be mechanically derivable from
the canonical table: one table row, one arrow.

This stage exists to give the human a single, scenario-shaped review
surface **before** Stage 03 commits the choreography to declarative
sync rules. Reviewing a full sync pack at once is harder than reviewing
one chain table per scenario.


## Progress checklist

- [ ] One chain file per use-case scenario
- [ ] First row is bootstrap entry action (Web/request[routed])
- [ ] Last row is respond action with status code
- [ ] Outcome values match those in the responsibility map
- [ ] Self-audit: `./clad verify` passes
## Outputs

- `output/<scenario-name>-chain.md` — one per scenario in the use case

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_chain_grammar.py \
  --chain-dir output
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<scenario-name>-chain.md"  # one per scenario
```

- **verify_chain_grammar.py:** every row carries exactly one backticked
  outcome token (no pipe unions, no multi-token cells).
- **verify_file_manifest.py:** `output/` contains exactly one
  `<scenario-name>-chain.md` per use-case scenario.

### Semantic checks (human)

- Every scenario in `01_usecase/output/usecase.md` has exactly one
  chain file.
- The rows in each chain file cover the top-level scenario's main flow
  plus its extensions, not some narrower happy-path-only subset unless
  the Stage 01 scenario itself truly has no extensions.
- Every concept and action that appears in a chain table is listed in
  `01a_responsibility-map/output/responsibility-map.md`.
- The first row of every chain is `Web/request[...] -> Web.request` (R4);
  the last row of every chain is `... -> Web.respond[...]`.
- **One branch per row; one outcome token per row.** An action invoked
  once may complete with several outcomes. Model each outcome as its own
  row: the same source action appears in the `When` cell with a different
  completion token (`Health.check[Healthy]`, `Health.check[Unhealthy]`),
  and each row resolves to its own `Then`/status. That is a branch, not a
  repeated invocation.
- **No duplicate branches.** The same `<Concept>.<action>` must not
  appear twice as a `Then` with the same outcome and target, and two rows
  must not describe the same branch. If two rows are genuinely the same
  branch, merge them; if they are different outcomes of one invocation,
  keep them as separate rows. Do not collapse distinct `Web.respond[...]`
  contracts into a single outcome cell — `verify_chain_grammar.py` requires
  exactly one backticked outcome token per row.
- **Cross-stage check (back):** the chain's trigger and final response
  match the scenario's *Trigger* and *Expected outcomes* in the use
  case.
- **Trigger contract completeness:** if a non-root row's `Then` action
  needs request-originated values, those values are named explicitly on
  the approved trigger token instead of being left implicit for Stage 03
  to recover later.
- **No collapsed branch rows:** if one state would need multiple arrows
  in the derived diagram, the table already contains multiple rows.
  Do not combine distinct `Web.respond[...]` contracts or distinct next
  actions into one canonical row.

## Gate instruction — this stage ends a human gate

Run:

```
./clad advance
```

(Long form: `python3 quality-gate/advance.py --feature features/UC-XX-<slug>`.)

`advance.py` owns the gate: it runs `verify_chain_grammar.py` and
`verify_file_manifest.py`, writes the stage receipt, prints the artefact
summary and the `approve_gate.py --gate 1` command, and stops (exit 10).
Present its summary to the human and **wait**. Do NOT run `present_gate.py`
yourself and do NOT edit `RESUME.md`.

Only after the human explicitly says "approved", run the approval command
`advance.py` printed, then re-run `./clad advance` to cross the gate. Gate 1
is the **Requirements** gate; Stages 02 and 03 auto-advance, and the next
human gate is **Gate 2 (Architecture)** at Stage 03b.

## Next stage

→ [`../02_concepts/CONTEXT.md`](../02_concepts/CONTEXT.md) — Concept specs (full anatomy)

Do NOT open this file until `advance.py` prints it as the NEXT STAGE, which
happens only after the human approves Gate 1.
