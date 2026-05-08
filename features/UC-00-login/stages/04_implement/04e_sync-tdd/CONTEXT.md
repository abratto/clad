# Stage 04e — Sync TDD (UC-00-login)

## Why this stage exists

The **inner red→green for syncs** — and the moment the **outer flow
tests from 04c finally go green**. Each sync gets its own TDD pass:
assert the `then` actions fire when the `when` pattern matches, with
the `where` clause's join semantics honoured (Pattern A/B/C/D per
`SYNC_PATTERNS.md`). When the last sync goes green, the corresponding
flow test goes green too — closing the outer loop.

**Feeds:**

- `sync-test-derivation.md` → 05 (which syncs are covered by tests, which only by flow tests).
- `<SyncName>Test.java` + `<SyncName>.java` → the running coordination layer; this is the artefact 05 back-traces against.

**Agent stance for this stage:** if you find a sync needs imperative
branching to make a test pass, the defect is in Stage 03 — push the
branching down into a concept action's outcomes and re-derive the sync.

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
