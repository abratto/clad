# Stage 04e — Sync TDD (UC-00-login)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../03_syncs/output/` | 4 | Sync specs |
| `../04b_spec/output/` | 4 | SPECs for the actions involved |
| `../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../methodology/implementation/RULES.md` | 3 | R3 |

## Process

For each sync, write the test that asserts its `then` actions fire
when its `when` pattern matches. Implement the sync declaratively
(no branching). At the end, the flow tests from `04c` go green.

## Outputs

- `output/sync-test-derivation.md`
- (Side effect:) `<SyncName>Test.java` and `<SyncName>.java` under the Java profile

## Verify

- All sync tests green.
- All `04c` flow tests green.
- **Cross-stage check (back):** every sync in `03_syncs/output/` has at least one row in the sync test-intent map.

## Gate

Default. This is the gate before `05_verify/`.
