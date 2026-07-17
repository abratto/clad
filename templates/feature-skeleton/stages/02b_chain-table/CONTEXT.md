# Stage 02b — Chain table (per scenario)

## Why this stage exists

The **choreography review surface** — one scenario per file, easier to
read than six declarative syncs at once. 02b is also the **canonical
resolver for action-name disputes**: if a sync spec (Stage 03)
disagrees with a chain table, the table wins. That rule keeps Stage 03
from silently inventing names that nothing else will recognise.

**Feeds:**

- `<scenario>-chain.md` → 02 (every action used must be declared in the matching concept spec with the same outcome enum), 03 (each row formalises into a sync `when`/`then` link), 03a (the chain is the dependency graph 03a audits), 04c (the flow test asserts the token sequence the chain predicts).

**Agent stance for this stage:** every row is an explicit `When -> Then`
edge with a named outcome. If you cannot name the outcome or the
trigger, the concept set is wrong — go back to 02a, do not invent.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios to choreograph |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | Available concepts and their actions |
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
one Stage 02b chain file. Keep that scenario's extensions in the same
file as additional branch rows when they share the same trigger and user
goal. Do not split ordinary failure extensions into separate chain files.

Each row is one transition branch. If one action can complete with
multiple outcomes that lead to different `Web.respond[...]` contracts or
different next actions, split those branches into separate rows instead
of collapsing them into one line.

If a downstream action needs request-originated data, the approved 02b
row must name those carried fields on the trigger contract itself
(for example `Web.handle[Routed(email, password)]`). Stage 03 may bind
Pattern A values only from names that 02b has already declared.

Optionally include a Mermaid `stateDiagram-v2` as a derived view. Do not
use `sequenceDiagram`. The diagram must be mechanically derivable from
the canonical table: one table row, one arrow.

This stage exists to give the human a single, scenario-shaped review
surface **before** Stage 03 commits the choreography to declarative
sync rules. Reviewing a full sync pack at once is harder than reviewing
one chain table per scenario.

## Outputs

- `output/<scenario-name>-chain.md` — one per scenario in the use case

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<scenario-name>-chain.md"  # one per scenario
```

- **verify_file_manifest.py:** `output/` contains exactly one
  `<scenario-name>-chain.md` per use-case scenario.

### Semantic checks (human)

- Every scenario in `01_usecase/output/usecase.md` has exactly one
  chain file.
- The rows in each chain file cover the top-level scenario's main flow
  plus its extensions, not some narrower happy-path-only subset unless
  the Stage 01 scenario itself truly has no extensions.
- Every concept and action that appears in a chain table is listed in
  `02a_responsibility-map/output/responsibility-map.md`.
- The first row of every chain is `Web/request[...] -> Web.handle` (R4);
  the last row of every chain is `... -> Web.respond[...]`.
- **No repeated action invocations.** Each `<Concept>.<action>` pair
  may appear at most once per chain. If the same action appears in two
  rows, those rows must be merged: a single action invocation produces
  one outcome per execution path, and all reachable outcomes are listed
  in the `Outcome` column of that single row. Two rows for the same
  action means outcomes are being split that belong together — that is
  a defect in the chain table, not a valid choreography choice.
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

## Gate instruction — STOP AND PRESENT

### Step 1 — Present artefacts

Run:

```
python3 ../../../quality-gate/present_gate.py \
  --feature ../../ \
  --gate 1
```

Present the output to the human. **Do NOT proceed past this point.**

### Step 2 — Wait for human approval

Wait for the human to say "approved" (or "Gate 1 approved").
Do NOT update RESUME.md yourself.

### Step 3 — Record approval

Only after the human explicitly approves, run:

```
python3 ../../../quality-gate/approve_gate.py \
  --feature ../../ \
  --gate 1
```

This updates RESUME.md to mark Gate 1 as approved.

### Step 4 — Proceed

After `approve_gate.py` exits successfully, proceed to Stage 02
(concept specs). Stages 02, 03 auto-advance. The next human gate is
**Gate 2 (Architecture)** at Stage 03b.

The `verify_file_manifest.py` script must pass before requesting the gate.

## Next stage

→ [`../02_concepts/CONTEXT.md`](../02_concepts/CONTEXT.md) — Concept specs (full anatomy)

Do NOT open this file until the human approves Gate 1. After
`approve_gate.py` exits successfully, open the next CONTEXT.md.
