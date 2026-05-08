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

- `<concept>-card.md` → 04a (Pattern D fields drive ORM column choices), 04b (per-concept SPEC author sees the full inbound contract), 04d (concept TDD knows its inbound surface), 04e (sync TDD knows which concepts it must double).
- `pattern-d-summary.md` → 04a (single cross-cutting checklist for ORM design).

**Agent stance for this stage:** this stage produces **no new design**.
If a card needs an action that doesn't exist yet, you are mid-violation
— go back to Stage 02 or 02b.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../03_syncs/output/` | 4 | The two UC-00 syncs (`LoginGrantsSession`, `LockoutOnFailedAttempts`) |
| `../02b_chain-table/output/` | 4 | The four scenarios' action chains |
| `../02a_responsibility-map/output/responsibility-map.md` | 4 | The four concepts: `User`, `PasswordAuth`, `Session`, `Web` |
| `../02_concepts/output/` | 4 | Action and field names |
| `../../../../methodology/architecture/SYNC_PATTERNS.md` | 3 | Patterns A/B/C/D |
| `../../../../templates/dependency-review-card.md` | 3 | Per-concept card |
| `../../../../templates/pattern-d-summary.md` | 3 | Cross-flow Pattern D summary |

## Process

Produce one card per concept (`User`, `PasswordAuth`, `Session`,
`Web`) and one consolidated `pattern-d-summary.md`. The inputs above
are the only reads needed.

## Outputs

- `output/User-card.md`
- `output/PasswordAuth-card.md`
- `output/Session-card.md`
- `output/Web-card.md`
- `output/pattern-d-summary.md`

## Verify

- Four cards, one per concept in 02a's map.
- Every action row exists in the matching `*.concept.md`.
- Every sync mentioned exists under `../03_syncs/output/`.
- The Pattern D summary is consistent with every card's Section 2.

## Gate

Default human approval.

**Do you agree with this step? Any corrections before I continue?**
