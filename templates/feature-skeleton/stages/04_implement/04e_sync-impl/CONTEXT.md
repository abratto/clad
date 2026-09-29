# Stage 04e — Sync implementation

## Why this stage exists

Implement the syncs that coordinate the concepts, and the sync unit
tests that constrain them. Like 04d this is a **single stage** — no
red/green split. The sync tests are derived from the approved Stage 03
sync specs; they assert that the correct downstream action is *scheduled*
for a given trigger outcome (interaction verification), not the
downstream action's own behaviour.

This is where the acceptance tests from 04c finally go green: concept
code exists (04d) and the syncs now wire it together. Sync test
effectiveness is measured by **mutation score**.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../03_syncs/output/` | 4 | Approved sync specs (the contract) |
| `../../03a_dependency-review/output/` | 4 | Route scope / coordination cards |
| `../04b_contract/output/` | 4 | Trigger + then-action signatures |
| `../04c_acceptance-tests/output/acceptance-spec.md` | 4 | The scenarios that must go green |
| `../04d_concept-impl/output/verification-evidence.md` | 4 | Concept tests green before syncs |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command |
| `../../../../../templates/test-intent-derivation-map.md` | 3 | Derivation-map template |
| `../../../../../methodology/implementation/TESTING.md` | 3 | Spec-driven verification discipline |
| `../../../../../methodology/implementation/RULES.md` | 3 | R3/R11/R12/R15 and the rest |
| Skill: `clad-sync-impl` | 3 | Sync test + implementation reference |

## Process

1. **Derive `output/sync-test-derivation.md`** from the sync specs using
   `../../../../../templates/test-intent-derivation-map.md`. One row per
   sync: trigger pattern → the exact then-actions it must schedule.
2. **Write the sync unit tests** under the configured `test.source.root`.
   Assert the downstream action was scheduled; do not assert its own
   behaviour.
3. **Implement each sync** as a declarative rule so the tests pass. A
   sync is `when … where … then …` — no imperative branching (R3). Every
   action writes an `outcome` field (R12). Shared-trigger syncs declare
   route scope (R11/R15).
4. **Write `output/verification-evidence.md`** recording: the executed
   build-and-test command and result, the acceptance tests now green,
   and the mutation score (when configured).
5. Run the canonical build-and-test command from
   `../../../_config/build-and-test.md`. The 04c acceptance tests must
   all pass.

## Outputs

- `output/sync-test-derivation.md` — sync → expected scheduled actions
- `output/verification-evidence.md` — test run + acceptance result + mutation score
- (Side effect:) sync unit tests and declarative sync implementation

## Verify

### Automated checks

```
python3 ../../../../../quality-gate/verify_profile_paths.py \
  --feature ../../../
python3 ../../../../../quality-gate/verify_implementation_parity.py \
  --sync-impl-dir <SYNC_IMPL_DIR> --concept-impl-dir <CONCEPT_IMPL_DIR> \
  --features-dir ../../../
python3 ../../../../../quality-gate/verify_sync_implementation_parity.py \
  --sync-impl-dir <SYNC_IMPL_DIR> --sync-dir ../../03_syncs/output --strict-trigger
python3 ../../../../../quality-gate/verify_sync_route_filters.py \
  --sync-impl-dir <SYNC_IMPL_DIR>
python3 ../../../../../quality-gate/verify_sync_declarative.py \
  --sync-impl-dir <SYNC_IMPL_DIR>
python3 ../../../../../quality-gate/verify_action_log_isolation.py \
  --app-source-root <APP_SOURCE_ROOT>
python3 ../../../../../quality-gate/verify_mutation_score.py \
  --feature-root ../../.. --scope syncs
python3 ../../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected sync-test-derivation.md,verification-evidence.md
```

- **verify_implementation_parity.py / verify_sync_implementation_parity.py:**
  every sync spec has a matching implementation and vice versa; names
  follow the derived grammar.
- **verify_sync_route_filters.py:** shared-trigger syncs declare route
  scope (R11/R15).
- **verify_sync_declarative.py:** sync implementations carry no
  imperative branching (R3).
- **verify_action_log_isolation.py:** the action log is isolated from
  durable concept regions.
- **verify_mutation_score.py:** the sync suite meets
  `mutation.threshold` (skips when `mutation.command` is unset).

### Semantic checks

- The 04c acceptance tests all pass.
- Every sync's trigger and then-actions match its spec.
- No sync contains business branching, state, or I/O (R3).

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
