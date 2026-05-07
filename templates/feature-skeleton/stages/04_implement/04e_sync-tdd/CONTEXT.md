# Stage 04e — Sync TDD (inner red → green; outer goes green)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../03_syncs/output/` | 4 | Sync specs |
| `../04b_spec/output/` | 4 | SPEC slices for the actions involved |
| `../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../methodology/implementation/RULES.md` | 3 | Hard rule R3 |

## Process

For each sync, write the test that asserts its `then` actions fire
when its `when` pattern matches; then implement the sync (declarative
form, no branching). Build up the test-intent derivation map for
syncs. **At the end of this stage, the flow tests from `04c` go
green.**

## Outputs

- `output/sync-test-derivation.md` — the test-intent map for syncs
- (Side effect:) `<SyncName>Test.java` and `<SyncName>.java` (or profile equivalent) per sync

## Verify

- All sync tests green.
- All flow tests from `04c` now green.
- **Cross-stage check (back):** every sync in `03_syncs/output/` has at least one row in the sync test-intent map.

## Gate

Default human approval. This is the gate before `05_verify/`.
