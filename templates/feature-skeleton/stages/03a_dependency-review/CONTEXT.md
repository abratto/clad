# Stage 03a — Per-concept dependency review

## Why this stage exists

The **last cross-concept sanity check before code**. 03a makes every
inbound call and every Pattern D read visible per concept on a single
card, so the human can catch coupling defects (action-name mismatches,
the same field reconstructed two different ways across flows, an
orphan Pattern D read with no owner) before they ossify into Java
imports at Stage 04. Pattern D is the **only legal cross-concept read**
per [`SYNC_PATTERNS.md`](../../../../methodology/architecture/SYNC_PATTERNS.md);
03a is where that legality is audited.

**Feeds:**

- `<concept>-card.md` → 03b (Pattern D fields drive conceptual data-model coverage), 04b (per-concept SPEC author sees the full inbound contract), 04d (concept TDD knows its inbound surface), 04e (sync TDD knows which concepts it must double).
- `pattern-d-summary.md` → 03b (single cross-cutting checklist for conceptual data-model design).

**Agent stance for this stage:** this stage produces **no new design**.
If a card needs an action that doesn't exist yet, you are mid-violation
— go back to Stage 02 or 02b.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../03_syncs/output/` | 4 | Every `then` invocation and every `where` clause to be tabulated |
| `../02b_chain-table/output/` | 4 | The flows the syncs implement |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | The set of concepts to produce a card for |
| `../02_concepts/output/` | 4 | Action and field names to cite |
| Skill: `clad-dependency-review` | 3 | Dependency review reference (see skills/ directory) |
| `../../../../methodology/architecture/SYNC_PATTERNS.md` | 3 | The four patterns (A/B/C/D) and the rule that D is the only legal cross-concept read |
| `../../../../templates/dependency-review-card.md` | 3 | Per-concept card template |
| `../../../../templates/pattern-d-summary.md` | 3 | Cross-flow Pattern D summary template |

## Process

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
reopen Stage 03. If the Stage 03 file itself disagrees with 02b or 02,
stop and reopen the earlier stage instead of patching the review card.

Then produce `output/pattern-d-summary.md` from
[`../../../../templates/pattern-d-summary.md`](../../../../templates/pattern-d-summary.md):
one row per Pattern D read in the entire feature.

The point of this stage is **not** new design. It is making the
existing cross-concept coupling visible so the human can spot it
before Stage 04 turns it into code.

## Outputs

- `output/<concept>-card.md` — one per concept named in 02a's map.
- `output/pattern-d-summary.md` — single consolidated cross-flow view.

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<concept>-card.md,…"  # one per concept + pattern-d-summary.md
```

- **verify_file_manifest.py:** `output/` contains exactly one card
  per concept in the responsibility map plus `pattern-d-summary.md`.

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
   filter status, and any route-agnostic justification in a dependency
   card.
- **Escalation discipline:** any mismatch found in 03a is surfaced as a
   defect in Stage 03 or earlier; 03a does not repair or reinterpret it.

## Gate

Auto-advances (next human gate: Stage 03b). The `verify_file_manifest.py` script
must pass before advancing.

## Next stage

→ [`../03b_data-model/CONTEXT.md`](../03b_data-model/CONTEXT.md) — Data model

The agent proceeds to Stage 03b without a human gate.
