<!--
  WORKED EXAMPLE - contract synced from templates/feature-skeleton/.
  UC-00's output/ is historical/frozen (gate content hashes); it may
  contain legacy artefacts. See features/UC-00-login/README.md
  SS"Contract vs example".
-->

# Stage 03a — Coordination review (sync coupling)

## Why this stage exists

The **last cross-concept sanity check before code** — the per-UC
**coordination review**. 03a makes every inbound call and every Pattern D
read visible per concept on a single card, so the human can catch coupling
defects (action-name mismatches, the same field reconstructed two different
ways across flows, an orphan Pattern D read with no owner) before they ossify
into Java imports at Stage 04. Pattern D is the **only legal cross-concept
read** per [`SYNC_PATTERNS.md`](../../../../methodology/architecture/SYNC_PATTERNS.md);
03a is where that legality is audited.

**Naming (do not confuse the two).** This stage is a *coordination* review of
one feature's sync coupling. It is **not** the app-level concept-dependence
graph (`features/_system/concept-dependence.md`), which records *extrinsic*
dependence — which concepts this app requires together — and is a reviewed
system-scope artefact, not a per-UC audit. The term "concept dependence" is
reserved for that graph. **The 03a cards are EVIDENCE for a possible dependence
edge, never its source**: a strong cross-UC coordination pattern may justify an
edge, but the edge is a purpose judgment, made in the graph.

This stage does **not** emit the dependence graph.

**Feeds:**

- `<concept>-card.md` → 03b (Pattern D fields drive conceptual data-model coverage), 04b (per-concept contract author sees the full inbound contract), 04d (concept TDD knows its inbound surface), 04e (sync TDD knows which concepts it must double).
- `pattern-d-summary.md` → 03b (single cross-cutting checklist for conceptual data-model design).

**Agent stance for this stage:** this stage produces **no new design**.
If a card needs an action that doesn't exist yet, you are mid-violation
— go back to Stage 02 or 01b.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../03_syncs/output/` | 4 | Every `then` invocation and every `where` clause to be tabulated |
| `../../../../features/_system/shared-triggers.md` | 4 | Cross-UC shared-trigger view (advisory) — triggers other use cases already fire |
| `../01b_chain-table/output/` | 4 | The flows the syncs implement |
| `../01_usecase/output/usecase.md` | 4 | Scenario names for the concept coverage matrix |
| `../01a_responsibility-map/output/responsibility-map.md` | 4 | The set of concepts to produce a card for |
| `../02_concepts/output/concept-bindings.md` | 4 | Which canonical concepts this feature uses |
| `../../../../features/_system/concepts/` | 4 | Action and field names to cite (canonical specs) |
| `../02_concepts/output/<Name>.concept.md` | 4 | NEW/EXTEND proposals (not yet promoted) |
| Skill: `clad-dependency-review` | 3 | Coordination review reference (see skills/ directory) |
| `../../../../methodology/architecture/SYNC_PATTERNS.md` | 3 | The four patterns (A/B/C/D) and the rule that D is the only legal cross-concept read |
| `../../../../templates/dependency-review-card.md` | 3 | Per-concept card template |
| `../../../../templates/pattern-d-summary.md` | 3 | Cross-flow Pattern D summary template |

## Process

**Deterministic generation first.** This is a token-locked audit of the
approved sync pack — not new design. First run:

Generated via:
```
python3 ../../../../quality-gate/generate_sync_cards.py --feature ../../ --write
```

`generate_sync_cards.py` emits one `*-card.md` per concept (Section 1 inbound
`then` calls, Section 2 Pattern D reads) plus `pattern-d-summary.md`, copying
sync names, concepts, and actions exactly from `03_syncs/output/`. It leaves
`<args>`/`<source>`/`<field>`/`<id>`/`<scenario>` placeholders for the agent to
fill from the approved sync text. Fill ONLY those placeholders verbatim; do not
add or remove rows unless a defect is found — and if one is, reopen Stage 03 or
earlier rather than editing the card.

**Cross-UC shared triggers.** Consult `features/_system/shared-triggers.md`
(generated) before treating a trigger as feature-local: another use case may
already fire a sync on the same `Concept.action` completion. A shared trigger
with divergent routing is the cross-UC coordination defect to surface here. It
may also justify a concept-dependence edge — but that edge is recorded in the
reviewed graph, not on this card.

For each concept that appears in any chain table or sync:

1. Open
   [`../../../../templates/dependency-review-card.md`](../../../../templates/dependency-review-card.md)
   and produce `output/<concept>-card.md`.
2. Before tabulating anything, treat the approved Stage 03 sync pack as
   token-locked input. Copy action names, argument names, field names,
   pattern labels, keys, status codes, and literals exactly as written.
   03a is an audit stage; it does not normalize names.
2. Section 1 — for each sync in `../03_syncs/output/`, inspect its
   `then` clause only. If the `then` clause calls an action on this
   concept, add one row. Do **not** add a row for syncs where this
   concept's action appears in the `when` clause — a `when` clause is
   a trigger, not an invocation. One row per (sync × action called in `then`).
   Pattern B applies when the argument comes from a prior action's flow
   token (`result_of(...)`) rather than from the approved trigger token
   (Pattern A).
3. Section 2 — list every Pattern D read of this concept's named
   region by **other** concepts' syncs. If none, say so explicitly.
4. Note any inconsistency (same action invoked via different
   patterns across flows; same field read via D in one flow and
   reconstructed via A/B in another).
5. For every sync, identify its trigger action. If that trigger action
   is produced by more than one named route, the sync must carry a route
   filter or carry a documented justification for route-agnostic firing.
   Record the finding in the relevant `*-card.md`. A sync that fires on
   a shared trigger without either a route filter or a justification is
   a defect.

If a sync name, action signature, field name, key, pattern label, or
literal in 03a would differ from the approved Stage 03 file, stop and
reopen Stage 03. If the Stage 03 file itself disagrees with 01b or 02,
stop and reopen the earlier stage instead of patching the review card.

Then produce `output/pattern-d-summary.md` from
[`../../../../templates/pattern-d-summary.md`](../../../../templates/pattern-d-summary.md):
one row per Pattern D read in the entire feature.

The point of this stage is **not** new design. It is making the
existing cross-concept coupling visible so the human can spot it
before Stage 04 turns it into code.


## Progress checklist

- [ ] One `-card.md` per concept
- [ ] Section 1: inbound calls tabulated per concept
- [ ] Section 2: concept-state reads listed (usually empty)
- [ ] `pattern-d-summary.md` produced
- [ ] Concept coverage matrix produced
- [ ] Shared-trigger analysis complete
- [ ] Self-audit: `./clad verify` passes
## Outputs

- `output/<concept>-card.md` — one per concept named in 01a's map.
- `output/pattern-d-summary.md` — single consolidated cross-flow view.
- `output/concept-matrix.md` — FR×DP matrix mapping scenarios to
  concepts. Surfaces God Objects, duplication, and entanglement visually.
  Generated via:
  ```
  python3 ../../../../quality-gate/verify_concept_matrix.py \
    --usecase ../01_usecase/output/usecase.md \
    --chain-dir ../01b_chain-table/output \
    --resp-map ../01a_responsibility-map/output/responsibility-map.md \
    --output output/concept-matrix.md
  ```

### Reading the matrix

The matrix maps scenarios (rows) to concepts (columns). An `X` means the
concept appears in that scenario's chain table. The pattern tells you
whether your concept boundaries are clean.

**What good looks like — sparse, diagonal-ish:**

```
| Scenario | User | Triage | Matcher | Billing | Notify |
|---|:---:|:---:|:---:|:---:|:---:|
| Register | X | X | — | — | — |
| Triage   | X | X | — | — | — |
| Match    | X | X | X | — | — |
| Track    | X | X | X | — | — |
| Bill     | X | — | — | X | X |
| Notify   | X | — | — | — | X |
```

Triage and Matcher appear where they're needed. Billing and Notify
each appear in 1–2 scenarios. No concept touches everything.

**What needs attention:**

| Pattern | What it looks like | Why it matters |
|---|---|---|
| **God Object** | A solid vertical column of X's — one concept in every row | That concept holds too much (state, actions, logic). Split it. |
| **Duplication** | Two columns with identical X patterns | Two concepts are structurally the same — merge or differentiate. |
| **Entanglement** | Two concepts both touch a scenario where only one should | The boundary is fuzzy. Clarify which concept owns that concern. |
| **Orphan** | A concept with no X's in any scenario | It's listed in the responsibility map but never used. Remove or justify. |

For small features (≤3 scenarios), concepts naturally overlap —
this is expected. The matrix is most useful on features with
4+ scenarios where anti-patterns become visible.

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<concept>-card.md,…"  # one per concept + pattern-d-summary.md,concept-matrix.md
```

- **verify_file_manifest.py:** `output/` contains exactly one card
  per concept in the responsibility map plus `pattern-d-summary.md` and
  `concept-matrix.md`.
- Route-filter enforcement is a design audit here (every shared-trigger
  sync records its filter status or justification in a card) **and** is
  enforced mechanically on the implementation at Stage 04e-green by
  `verify_sync_route_filters.py`. It is not run on markdown sync specs.

### Semantic checks (human)

- One card per concept in the responsibility map (no missing, no extra).
- Every action in every card exists in the corresponding `*.concept.md`.
- Every sync named in any card exists under `../03_syncs/output/`.
- Every Pattern D row in any card appears in `pattern-d-summary.md`,
  and vice versa.
- Every Pattern D `Field` is declared in the owner concept's `state`
  section (and therefore will need to appear in 04a's ORM output).
- **`then`-only rule:** every row in every Section 1 table corresponds
  to a sync whose `then` clause calls that action. No row may correspond
  to a sync whose `when` clause merely triggers on that action's outcome.
- **Exact-token audit:** every action name, argument name, field name,
   pattern label, key, status code, and literal matches the approved
   Stage 03 sync file exactly.
- **Route-filter completeness:** every sync whose trigger action is
   produced by more than one named route records the routes, the route
   filter status, and any route-agnostic justification in a
   coordination-review card.
- **Escalation discipline:** any mismatch found in 03a is surfaced as a
   defect in Stage 03 or earlier; 03a does not repair or reinterpret it.

## Gate

Auto-advances (next human gate: Stage 03b). The `verify_file_manifest.py` script
must pass before advancing.

## Next stage

→ [`../03b_data-model/CONTEXT.md`](../03b_data-model/CONTEXT.md) — Data model

The agent proceeds to Stage 03b without a human gate.
