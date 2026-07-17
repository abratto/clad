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
| `../03_syncs/output/` | 4 | The UC-00 per-transition sync pack |
| `../02b_chain-table/output/` | 4 | The four scenarios' action chains |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | The four concepts: `User`, `PasswordAuth`, `Session`, `Web` |
| `../02_concepts/output/` | 4 | Action and field names |
| `../../../../methodology/architecture/SYNC_PATTERNS.md` | 3 | Patterns A/B/C/D |
| Skill: `clad-dependency-review` | 3 | Dependency review reference |
| `../../../../templates/dependency-review-card.md` | 3 | Per-concept card |
| `../../../../templates/pattern-d-summary.md` | 3 | Cross-flow Pattern D summary |

## Process

Produce one card per concept (`User`, `PasswordAuth`, `Session`,
`Web`) and one consolidated `pattern-d-summary.md`. The inputs above
are the only reads needed.

Treat the approved Stage 03 sync files as token-locked input. Copy
action names, argument names, field names, pattern labels, keys, status
codes, and literals exactly. This stage is an audit, not a repair step.

Pattern D detection scans each sync's "Where clause patterns" table
(see [`../../../../templates/sync.md`](../../../../templates/sync.md))
for rows with pattern label D (`Concept: { ... }`). These rows
represent cross-concept state reads and must be flagged in the card's
Section 2. Patterns A, B, and C do not cross concept boundaries.

For every sync, identify its trigger action. If that trigger action is
produced by more than one named route, the sync must carry a route
filter or carry a documented justification for route-agnostic firing.
Record the finding in the relevant `*-card.md`. A sync that fires on a
shared trigger without either a route filter or a justification is a
defect.

If a card or summary would need to rename, re-case, re-type, or otherwise
normalize a token from Stage 03, stop and reopen Stage 03 instead. If
the approved Stage 03 syncs disagree with Stage 02b or Stage 02, reopen
that earlier stage rather than fixing the mismatch inside 03a.

## Outputs

- `output/User-card.md`
- `output/PasswordAuth-card.md`
- `output/Session-card.md`
- `output/Web-card.md`
- `output/pattern-d-summary.md`

## Verify

### Automated checks

```
python3 ../../../../quality-gate/verify_file_manifest.py --dir output --expected "User-card.md,PasswordAuth-card.md,Session-card.md,Web-card.md,pattern-d-summary.md"
```

- **verify_file_manifest.py:** `output/` contains exactly the expected review files.

### Semantic checks (human)

- Four cards, one per concept in 02a's map.
- Every action row exists in the matching `*.concept.md`.
- Every sync mentioned exists under `../03_syncs/output/`.
- The Pattern D summary is consistent with every card's Section 2.
- Every action name, argument name, field name, pattern label, key,
	status code, and literal matches the approved Stage 03 sync file
	exactly.
- Every sync whose trigger action is produced by more than one named
	route records the routes, the route filter status, and any
	route-agnostic justification in a dependency card.
- Any mismatch is surfaced as a Stage 03 or earlier-stage defect rather
	than being normalized in the dependency review output.

## Gate

Auto-advances (next human gate: Stage 03b). The `verify_file_manifest.py`
script must pass before advancing.

## Next stage

→ [`../03b_data-model/CONTEXT.md`](../03b_data-model/CONTEXT.md) — Data model

The agent proceeds to Stage 03b without a human gate.
