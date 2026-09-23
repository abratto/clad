# Stage 02 — Concept specs

## Pre-condition

`advance.py` enforces stage order and upstream gate approval before this
stage runs — see `STAGES.md` §"Stage lifecycle (standard)". Do not start
until it has printed this stage as `NEXT STAGE`.

## Why this stage exists

Establishes the full anatomy of every concept this feature needs — state,
action signatures with outcomes, flow-token shape, operational principle —
so Stage 03 can name actions/outcomes precisely, Stage 03b can derive a
conceptual data model from `state`, and Stage 04d can TDD the concept against
a fixed contract.

Concepts are **system-scope, canonical assets** (the corpus at
`_system/concepts/`), not per-feature artefacts. This stage therefore does one
of two things per concept: **binds** to an existing canonical concept, or
**proposes** an addition to the vocabulary. Hard rule **R1** is enforced here:
no concept names another concept's state, actions, or types beyond opaque ids.

**Feeds:**

- `concept-bindings.md` → 03b/04b (which concepts to derive models/specs for),
  the catalog's *Used by* column, and `verify_concept_registry.py`.
- `<Name>.concept.md` **proposal** (NEW/EXTEND only) → promotion into
  `_system/concepts/` on gate approval, then 03a cards, 03b, 04b, 04d.

**Agent stance for this stage:** consult the catalog before authoring
anything. If the action you need already exists canonically, **bind** — do not
restate the spec. If you find yourself wanting to import another concept's
type, stop — that coordination belongs in a sync, not in this file.

> **Note:** the choreography review (which concepts exist; what they own; how
> they fan out per scenario) lives in `01a_responsibility-map/` and
> `01b_chain-table/`. This stage does **only** the anatomy.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Use case |
| `../01a_responsibility-map/output/responsibility-map.md` | 4 | The agreed concept set + each concept's `Origin` (reuse / extend / new) |
| `../01b_chain-table/output/` | 4 | The agreed action choreography (per scenario) — **read every file before naming any outcome** |
| `../../../../features/_system/concepts-catalog.md` | 4 | Canonical vocabulary index — reuse an existing concept/action before proposing |
| `../../../../features/_system/concept-dependence.md` | 4 | App-level extrinsic graph — for proposed dependence claims |
| `../../../../features/_system/concepts/<Name>.concept.md` | 4 | The canonical spec for every REUSE / EXTEND concept |
| `../../../_system/stages/00_actor-goal/output/actors.md` | 4 | For cross-stage check |
| Skill: `clad-concept-design` | 3 | Concept design reference (see skills/ directory) |
| `../../../../methodology/architecture/CONCEPTS.md` | 3 | Concept anatomy |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R2 |
| `../../../../templates/concept.md` | 3 | Proposal output template |
| `../../../../templates/concept-bindings.md` | 3 | Bindings output template |

> The catalog, dependence graph, and corpus are **conditional** inputs: a
> project's first feature has none, and every concept is `new`. Load them when
> they exist.

## Process

For each non-bootstrap concept in
`01a_responsibility-map/output/responsibility-map.md`, read its **Origin**
column and act accordingly:

1. **`reused:UC-XX`** — emit a binding row in `concept-bindings.md` only. Do
   **not** author `<Name>.concept.md`. The canonical spec is the corpus.
2. **`extends:UC-XX`** — emit a binding row AND author a proposal
   `<Name>.concept.md` that adds the needed actions/state to the existing
   concept. Keep it **additive and single-purpose**: never rename an existing
   outcome or parameter, and never redeclare an action with a different
   vocabulary. If the addition introduces a second purpose, split it into a
   `new` concept instead.
3. **`new`** — emit a binding row AND author a proposal `<Name>.concept.md`
   to full anatomy.

Always emit `output/concept-bindings.md`, even when every concept is reused —
a feature may reuse the whole vocabulary and propose nothing. Record any
proposed extrinsic dependence claim (`requires`) in the responsibility map's
*Proposals* section; it is reviewed here, and the app-level graph
(`concept-dependence.md`) is updated only through promotion.

**Outcome alignment is mandatory:** every action output name MUST exactly
match the outcome strings used in the approved chain tables in
`01b_chain-table/output/`. Open every chain table file before naming any
outcome. If you need an outcome the chain table did not name, return to
Stage 01b and amend the chain table first — do not invent outcomes here.

**State and input discipline:** do not add state fields or action inputs that
have no basis in the chain table or responsibility map. If a field is absent
from both, raise it as an open question in the concept's Notes section.

**Bootstrap concept exclusion:** bootstrap concepts such as `Web`, `Grpc`,
`Cli`, or `Stream` do not belong in `02_concepts/output/` unless the feature
has explicitly declared a methodology deviation. They are governed by the
shared bootstrap-concept docs and are not listed in `concept-bindings.md`.

R1 still applies: no concept names another concept's state, actions, or types
beyond opaque ids.

## Progress checklist

- [ ] Every non-bootstrap concept's `Origin` read from the responsibility map
- [ ] `concept-bindings.md` emitted with one row per concept used
- [ ] Proposals authored for exactly the NEW/EXTEND concepts
- [ ] Proposal state uses Alloy-like relational notation
- [ ] Proposal actions have case-split outcomes matching the chain table
- [ ] Proposal operational principle includes a witness trace
- [ ] No cross-concept references (R1)
- [ ] Self-audit: `./clad verify` passes
## Outputs

- `output/concept-bindings.md` — always (one row per concept used)
- `output/<Name>.concept.md` — one proposal per NEW/EXTEND concept only

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_concept_state_relational.py \
  --concept-dir output \
  --concept-dir ../../../../features/_system/concepts
python3 ../../../../quality-gate/verify_concept_criteria.py \
  --concept-dir output \
  --concept-dir ../../../../features/_system/concepts
python3 ../../../../quality-gate/verify_concept_proposals.py \
  --feature ../..
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output \
  --expected "concept-bindings.md,…"  # + one <Name>.concept.md per NEW/EXTEND concept
```

- **verify_concept_state_relational.py:** each proposal's (and canonical
  concept's) `## State` is a relation over a set of individuals, not a single
  instance's field list. Proposals shadow the corpus by concept name.
- **verify_concept_criteria.py:** every concept satisfies the mechanical
  criteria (operational principle present, no external types; warnings for type
  params / capability naming).
- **verify_concept_proposals.py:** the proposal set corresponds **exactly** to
  the NEW/EXTEND rows in the responsibility map; REUSE rows have no spec file.
- **verify_file_manifest.py:** `output/` contains exactly `concept-bindings.md`
  plus one `.concept.md` per NEW/EXTEND concept.
- **Cross-artefact action-name parity** (`verify_action_chain.py`) needs the
  syncs, dependency cards, and contracts, so it runs at Stage 04b, not here.

### Semantic checks (human)

- **Concept criteria checklist** (Jackson's criteria — see
  `methodology/architecture/CONCEPTS.md`):
  - *purposive* — one purpose per concept, nameable in one verb phrase;
  - *end-to-end* — the operational principle exercises the concept alone;
    if it degenerates to "when this action happens, the state updates so",
    something is missing;
  - *user-facing* — it serves an actor's goal, not an internal refactor;
  - *familiar / reusable* — novelty is rare and justified;
  - *state sufficiency and necessity* — every field is needed, and nothing
    needed is missing; no external types (use type parameters).
- **Input/state discipline:** no state field or action input without a basis
  in the chain table or responsibility map.
- **Action discipline:** no action declared that is not listed in
  `01a_responsibility-map/output/responsibility-map.md`.
- **Bootstrap exclusion:** no bootstrap concept file appears in `output/`.
- **Additive extension:** an `extends` proposal adds outcomes/parameters
  without renaming or removing an existing one.
- **Cross-stage check (back):** every actor in
  `features/_system/stages/00_actor-goal/output/actors.md` whose goal is
  in-scope appears in at least one concept's operational principle.

## Gate

Auto-advances (next human gate: Stage 03b). The quality-gate scripts
(`verify_concept_criteria.py`, `verify_concept_proposals.py`,
`verify_file_manifest.py`) must all pass before advancing.

**Promotion.** On **Gate 2** approval, the proposals in `output/` are
promoted into `_system/concepts/` by `./clad promote-concepts` (never by hand),
which also regenerates the catalog and applies the reviewed dependence claims.
A REUSE-only feature promotes nothing.

## Advancing

> Do not open the next stage's `CONTEXT.md` yourself. After this stage's
> `output/` is written, end your turn by running the gate-driven advance
> command, which runs this stage's checks, enforces stage ordering, and
> tells you the next step:
>
> ```
> ./clad advance
> ```
>
> (Long form: `python3 quality-gate/advance.py --feature features/UC-XX-<slug>`.)
> The CLI wrapper auto-discovers the feature from `RESUME.md`.
>
> Treat its output as your next instruction. It advances you, stops you
> at a human gate, or returns you to this stage with the defects to fix.
> See AGENTS.md §2 principle 12 and
> `methodology/implementation/STAGES.md` §"Gate-driven advance".
