# Stage 04e — Sync TDD (inner red → green; outer goes green)

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
| `../04b_spec/output/` | 4 | SPEC slices for the actions involved |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command for red/green evidence |
| `../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings for this feature |
| `../../../../../templates/test-intent-derivation-map.md` | 3 | Coverage template |
| `../../../../../methodology/implementation/RULES.md` | 3 | Hard rule R3 |
| `../../../../../reference-impl/java-micronaut-jena/README.md` and `../../../../../reference-impl/java-micronaut-jena/CODE_STYLE.md` (only when this profile is selected) | 3 | SPARQL sync-fragment conventions used by the reference engine |

## Process

For each sync, write the test that asserts its `then` actions fire
when its `when` pattern matches; then implement the sync (declarative
form, no branching). Build up the test-intent derivation map for
syncs. **At the end of this stage, the flow tests from `04c` go
green.**

Implementations in this stage must correspond 1:1 with the approved
Stage 03 sync specs. Do not invent extra executable convenience syncs,
aggregate handlers, or imperative coordinator classes that have no
matching Stage 03 sync contract. If the profile uses a declarative sync
fragment style, follow that style rather than inventing an ad hoc API.

If the selected profile is Java/Jena, keep sync logic in SPARQL
fragments (`whereClause()` and `thenBindings()`), preserve engine-owned
variables (`?_when_1`, `?_flow`, `?_then_1`, `?_then_input`), and emit
exactly one downstream invocation per sync firing.

Generated sync implementation files must live under
`APP_SOURCE_ROOT`/`APP_PACKAGE_ROOT` from
`../../../_config/package-and-layout.md`, not under a copied
`com.example.app` path unless that is explicitly configured.

Generated sync test files must live under `APP_TEST_SOURCE_ROOT`, using
packages rooted at `APP_PACKAGE_ROOT`.

"Red" in this stage means executable failing sync tests before
implementation, not disabled placeholders and not compile-failing
suites.

## Outputs

- `output/sync-test-derivation.md` — the test-intent map for syncs
- (Side effect:) `<SyncName>Test.java` and `<SyncName>.java` (or profile equivalent) per sync

## Verify

- All sync tests green.
- All flow tests from `04c` now green.
- Executed command evidence shows: test compilation succeeds, sync tests are green, and flow tests are green.
- Every generated sync test/implementation pair corresponds to exactly
  one sync in `03_syncs/output/`; no extra executable syncs exist
  without an upstream sync spec.
- Sync implementation package/source path matches
  `../../../_config/package-and-layout.md` (`APP_PACKAGE_ROOT`,
  `APP_SOURCE_ROOT`, `APP_TEST_SOURCE_ROOT`).
- **Cross-stage check (back):** every sync in `03_syncs/output/` has at least one row in the sync test-intent map.

## Gate

Default human approval. This is the gate before `05_verify/`.

## Next stage

→ [`../../05_verify/CONTEXT.md`](../../05_verify/CONTEXT.md) — Verify + close

(Stage 04 router is satisfied when 04e is green; advance directly to Stage 05.)

To advance, the human says: **"Proceed to Stage 05."**
