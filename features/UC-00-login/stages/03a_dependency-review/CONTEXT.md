# Stage 03a — Per-concept dependency review

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
