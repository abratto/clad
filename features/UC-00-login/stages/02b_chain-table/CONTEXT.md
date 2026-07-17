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

**Agent stance for this stage:** every row is an explicit `When -> Then`
edge with a named outcome. If you cannot name the outcome or trigger,
the concept set is wrong — go back to 02a, do not invent.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | UC-00-login scenarios |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | Available concepts and actions |
| `../../../../methodology/architecture/SYNCHRONIZATIONS.md` | 3 | Forward link to Stage 03 |
| Skill: `clad-chain-table` | 3 | Chain-table authoring reference |
| `../../../../templates/chain-table.md` | 3 | Output template |

## Process

For each named scenario in `01_usecase/output/usecase.md`, produce
`output/<scenario-name>-chain.md` using only concepts and actions
from `02a_responsibility-map/output/responsibility-map.md`. The
chain is the ordered list of explicit `When -> Then` edges that
fulfils the scenario; the last row is always a `... -> Web.respond`
terminal response.

If the use case has 2+ scenarios: also produce
`output/login-all-scenarios-chain.md` (consolidated view). This
non-canonical artefact merges all scenario chains into one
branching table and combined FSM diagram. It uses the same concrete
Stage 02b shape as the per-scenario chains
(`Scenario(s) | When | Then | Inputs | Outcome | Why this path`)
and keeps the WYSIWID `When -> Then` causality explicit in the table
itself.
Stages 03–04 will use it
to verify complete outcome coverage and prevent implementation gaps.
`Inputs` in this artefact are action arguments only; join provenance
still belongs exclusively to Stage 03 sync `where` clauses.
Template: `../../../../templates/consolidated-chain.md`.

## Outputs

- `output/successful-login-chain.md` — canonical
- `output/wrong-password-chain.md` — canonical
- `output/unknown-user-chain.md` — canonical
- `output/lockout-chain.md` — canonical
- `output/login-all-scenarios-chain.md` — consolidated (non-canonical, implementation aid)

## Verify

### Automated checks

```
python3 ../../../../quality-gate/verify_file_manifest.py --dir output --expected "successful-login-chain.md,wrong-password-chain.md,unknown-user-chain.md,lockout-chain.md,login-all-scenarios-chain.md"
```

- **verify_file_manifest.py:** `output/` contains exactly the expected chain files.

### Semantic checks (human)

- Every scenario has exactly one chain file (canonical).
- Consolidated chain (non-canonical):
  - Every row in the consolidated table traces back to a specific scenario chain.
  - Every non-root row already states one explicit `When -> Then` transition for Stage 03.
  - Every error outcome from the four scenarios appears in the consolidated branching table.
  - Concept outcome enums match across all per-scenario files (e.g., PasswordAuth.check: [Ok, BadPassword, Locked] appears in all files that use it).
  - `Inputs` expose downstream action arguments only; no `Where`/join provenance appears in Stage 02b.
- The first row of each scenario chain is `Web/request[...] -> Web.handle`; the last is `... -> Web.respond[...]`.
- Every action used appears in the responsibility map.
- Mermaid `stateDiagram-v2` diagrams render at [mermaid.live](https://mermaid.live) with no errors.

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
