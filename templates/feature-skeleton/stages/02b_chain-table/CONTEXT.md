# Stage 02b — Chain table (per scenario)

## Why this stage exists

The **choreography review surface** — one scenario per file, easier to
read than six declarative syncs at once. 02b is also the **canonical
resolver for action-name disputes**: if a sync spec (Stage 03)
disagrees with a chain table, the table wins. That rule keeps Stage 03
from silently inventing names that nothing else will recognise.

**Feeds:**

- `<scenario>-chain.md` → 02 (every action used must be declared in the matching concept spec with the same outcome enum), 03 (each row formalises into a sync `when`/`then` link), 03a (the chain is the source of truth for inbound calls per concept), 04c (flow tests assert the chain end-to-end at runtime).

**Agent stance for this stage:** every row is `<Concept>.<action> -> <outcome>`. If you cannot name the outcome, the concept set is wrong — go back to 02a, do not invent.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios to choreograph |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | Available concepts and their actions |
| `../../../../methodology/architecture/SYNCHRONIZATIONS.md` | 3 | What syncs are (so the chain table can be lifted into them later) |
| `../../../../templates/chain-table.md` | 3 | Output template |

## Process

For each named scenario in `01_usecase/output/usecase.md`, produce one
file `output/<scenario-name>-chain.md`. The chain is the ordered
sequence of `<Concept>.<action> -> <outcome>` calls that fulfils the
scenario, justified one row at a time. Use the actions and concepts
already named in the responsibility map — do not invent new ones.

Optionally include a Mermaid sequence diagram (the template suggests
one). The diagram is for human review; it is not load-bearing.

This stage exists to give the human a single, scenario-shaped review
surface **before** Stage 03 commits the choreography to declarative
sync rules. Reviewing six syncs at once is harder than reviewing one
chain table per scenario.

## Outputs

- `output/<scenario-name>-chain.md` — one per scenario in the use case

## Verify

- Every scenario in `01_usecase/output/usecase.md` has exactly one
  chain file.
- Every concept and action that appears in a chain table is listed in
  `02a_responsibility-map/output/responsibility-map.md`.
- The first row of every chain is `Web.handle` (R4); the last row of
  every chain is `Web.respond`.
- **Cross-stage check (back):** the chain's trigger and final response
  match the scenario's *Trigger* and *Expected outcomes* in the use
  case.

## Gate

Default human approval. **Do you agree with this step? Any
corrections before I continue?**

## Next stage

→ [`../02_concepts/CONTEXT.md`](../02_concepts/CONTEXT.md) — Concept specs (full anatomy)

To advance, the human says: **"Proceed to Stage 02."**
