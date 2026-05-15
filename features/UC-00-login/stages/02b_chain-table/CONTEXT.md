# Stage 02b — Chain table (UC-00-login)

## Why this stage exists

The **choreography review surface** — one scenario per file, easier to
read than four declarative syncs at once. 02b is also the **canonical
resolver for action-name disputes**: if a sync spec (Stage 03)
disagrees with a chain table, the table wins. That rule is what
reconciled `Session.open` → `Session.grant` and `PasswordAuth.verify` →
`PasswordAuth.check` in this feature — see PR #6.

**Feeds:**

- `<scenario>-chain.md` → 02 (every action used must be declared in the matching concept spec with the same outcome enum), 03 (each row formalises into a sync `when`/`then` link), 03a (the chain is the source of truth for inbound calls per concept), 04c (flow tests assert the chain end-to-end at runtime).

**Agent stance for this stage:** every row is `<Concept>.<action> -> <outcome>`. If you cannot name the outcome, the concept set is wrong — go back to 02a, do not invent.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | UC-00-login scenarios |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | Available concepts and actions |
| `../../../../methodology/architecture/SYNCHRONIZATIONS.md` | 3 | Forward link to Stage 03 |
| `../../../../templates/chain-table.md` | 3 | Output template |

## Process

For each named scenario in `01_usecase/output/usecase.md`, produce
`output/<scenario-name>-chain.md` using only concepts and actions
from `02a_responsibility-map/output/responsibility-map.md`. The
chain is the ordered list of concept actions that fulfils the
scenario; the last row is `Web.respond`.

If the use case has 2+ scenarios: also produce
`output/login-all-scenarios-chain.md` (consolidated view). This
non-canonical artefact merges all scenario chains into one
breatching table and combined FSM diagram. Stages 03–04 will use it
to verify complete outcome coverage and prevent implementation gaps.
Template: `../../../../templates/consolidated-chain.md`.

## Outputs

- `output/successful-login-chain.md` — canonical
- `output/wrong-password-chain.md` — canonical
- `output/unknown-user-chain.md` — canonical
- `output/lockout-chain.md` — canonical
- `output/login-all-scenarios-chain.md` — consolidated (non-canonical, implementation aid)

## Verify

- Every scenario has exactly one chain file (canonical).
- Consolidated chain (non-canonical):
  - Every row in the consolidated table traces back to a specific scenario chain.
  - Every error outcome from the four scenarios appears in the consolidated "When → Then" table.
  - Concept outcome enums match across all per-scenario files (e.g., PasswordAuth.check: [Ok, BadPassword, Locked] appears in all files that use it).
- The first row of each scenario chain is `Web.handle`; the last is `Web.respond`.
- Every action used appears in the responsibility map.
- Mermaid `stateDiagram-v2` diagrams render at [mermaid.live](https://mermaid.live) with no errors.

## Gate

Default human approval. Review all five chain files (four per-scenario + one consolidated). Verify:
- Per-scenario chains are consistent with the use case scenarios.
- Consolidated chain correctly merges all outcomes; no outcome is missing or duplicated.
- All diagrams render correctly.

**Do you agree with this step? Any corrections before I continue?**

## Next stage

→ [`../02_concepts/CONTEXT.md`](../02_concepts/CONTEXT.md) — Concept specs (full anatomy)

To advance, the human says: **"Proceed to Stage 02."**
