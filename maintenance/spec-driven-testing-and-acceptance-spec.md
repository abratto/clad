<!-- Maintenance-route planning record for the spec-driven testing migration. -->
# Maintenance change — `spec-driven-testing-and-acceptance-spec`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles` (gate machinery + methodology +
  root `clad.properties`; canonical `reference-impl/java-legible` gains
  mutation tooling)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** replace Stage 04's in-loop TDD ceremony with
  native flow tests plus a generated, frozen Acceptance Spec, mutate-gate
  the unit suites, and delete the Cucumber/step-definition track. See
  `docs/decisions/0001-spec-driven-testing.md`.

## Mechanism

No engine/runtime behaviour changes; the change is gate machinery,
methodology prose, templates, skills, and root configuration.

- Stage registry that must reflect the collapsed 04 tree —
  `quality-gate/clad_stages.py:779` (the `Stage("04c"…)` / `Stage("04d"…)` /
  `Stage("04e"…)` block) is the single source of truth for the stage graph.
- Gate scripts deleted: `verify_gherkin_derivation.py`,
  `verify_step_definition_parity.py`, `verify_step_definition_derivation.py`,
  `verify_cucumber_green.py`, `verify_feature_file_presence.py`,
  `verify_test_continuity.py` and `generate_feature_files.py` are gone; no
  checker path still references them (`quality-gate/` is clean).
- New gate scripts: `quality-gate/verify_mutation_score.py`,
  `quality-gate/verify_acceptance_binding.py`.
- Root configuration: `clad.properties` gains `mutation.command`,
  `mutation.threshold` and `mutation.require`.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No concept/sync spec or engine change; 04b contract stays the design freeze |
| Action ordering and sync deduplication | `preserved` | No engine or sync-spec change |
| Flow-token lineage | `preserved` | Stage 05 trace unchanged; native flow tests assert the same token chain |
| Storage/retention semantics | `preserved` | 04a storage mapping unchanged |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `methodology/implementation/STAGES.md`, `QUALITY_GATE.md`, `TDD.md`→`TESTING.md`, `RULES.md`, `AGENTS.md`, architecture docs |
| Profile configuration or deployment files | yes | root `clad.properties` (mutation keys); `reference-impl` poms (mutation plugin) |
| Engine/runtime implementation | no | No `legible-engine` change |
| Profile tests | yes | canonical flow test already native (`LoginFlowTest`); mutation plugin added |
| UC artefact chain | yes (contract only) | `templates/feature-skeleton/stages/04_implement/**`, `templates/acceptance-spec.md`, worked example `examples/UC-00-login`; no live `features/UC-*` to migrate |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Quality-gate regression suite green | unit | `python3 -m pytest quality-gate/tests -q` | pass | 285 passed |
| Artefact pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | pipeline intact, 0 defects |
| Doc cross-references intact | unit | `python3 quality-gate/verify_links.py` | pass | 302 links / 102 docs |
| Canonical profile green | flow-regression | `mvn test -f reference-impl/pom.xml -pl java-legible -am` | pass | BUILD SUCCESS; 41 engine + 40 example tests |
| Mutation gate is three-valued (PASS/FAIL/SKIP) with a strict mode | unit | `python3 -m pytest quality-gate/tests/test_mutation_score.py -q` | pass | score below threshold FAILs; `MUTATION_SKIP` SKIPs by default and FAILs under `--require` |
| Mutation tooling present and wired | integration | `python3 quality-gate/verify_mutation_score.py --feature-root examples/UC-00-login --scope concepts --require` | pass | wrapper configured; PIT pinned at 1.19.1 at the time of this record made the check SKIP on the sandbox's JDK 25. Superseded by `maintenance/pit-1.30-java25-support.md`, which pins PIT 1.30.0; the strict check now PASSes on JDK 25 (84.6% >= 80%). CI's `mutation-gate` job runs it with `--require` on JDK 21. |
| Deleted scripts unreferenced | unit | `grep -r` for deleted script names across gates/docs | pass | only the maintenance record names them, as plain text |
| No legacy Stage 04/Gherkin terms in live docs/templates/skills | unit | `grep -rniE "04c_flow\|04d-red\|04e-green\|gherkin\|cucumber\|Executable spec"` | pass | AGENTS.md/methodology/skills/templates clean |

## Gates

### Design gate

Approved in-conversation by the human on 2026-09-28 ("1 - rename,
2 - drop, 3 - reject. Go ahead and proceed."), on the strength of the
plan presented after reading Böckeler's article. Recorded as `approved`
here by the implementing agent; no `approve-maintenance` ceremony was
available in the conversation channel.

### Evidence gate

Approved by the human in-conversation on 2026-09-28 ("Yes" to committing the
block) after reviewing the green test matrix. Status set to `closed` and the
record committed with the change.

## Notes

- Rejected: migrate legacy `04d_red-tests`/`04e_green-impl` trees (D3 —
  reject), and preserve a multi-model red/green handoff (D2 — drop).
  There are no live `features/UC-*` in this repo, so rejection affects
  only downstream Gherkin-era clones, which the CHANGELOG migration note
  addresses.
- Rollback: revert this change's commits; no engine or feature artefact
  is touched, so the canonical profile and UC-00 hashes are unaffected.
- Mutation threshold defaults to 80%; calibrate against real features
  before tightening.
