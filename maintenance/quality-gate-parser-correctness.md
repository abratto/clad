# Maintenance change — `quality-gate-parser-correctness`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles`
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Repair generic quality-gate parsing without weakening parity or executable-spec enforcement.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Gates parse approved artefacts; no feature artefact or application code changes. |
| Action ordering and sync deduplication | preserved | Parser changes do not execute or alter action chains. |
| Flow-token lineage | preserved | Parser changes do not interpret or change runtime flow data. |
| Storage/retention semantics | n/a | No storage implementation or configuration changes. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | no | Quality-gate grammar documentation remains local to script help and regression fixtures. |
| Profile configuration or deployment files | no | No profile configuration changes. |
| Engine/runtime implementation | no | No application or reference-engine changes. |
| Profile tests | no | Add deterministic Python subprocess fixtures for gate behavior. |
| UC artefact chain | no | Valid existing artefacts must remain untouched. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Sync Contract Matrix arrow signatures lower to their declared sync classes | fixture | `python3 -m unittest quality-gate/tests/test_parser_regressions.py` | pass | Matrix contract fixture passed. |
| Rule-block completion notation and compact matrix outcomes parse strictly | fixture | `python3 -m unittest quality-gate/tests/test_parser_regressions.py` | pass | Rule-block and compact `Routed(...)` fixtures passed. |
| Java SPI interfaces are excluded but concept agents require specs | fixture | `python3 -m unittest quality-gate/tests/test_parser_regressions.py` | pass | SPI interface is ignored; missing direct ConceptAgent spec still fails. |
| CucumberTest Surefire cases count pass, failure, skipped, and zero scenarios correctly | fixture | `python3 -m unittest quality-gate/tests/test_parser_regressions.py` | pass | Pass, failure, skipped, and zero-scenario fixtures passed. |
| Existing CLAD artefact and Java profile tests remain green | regression | canonical `test.command` | pass | Artefact gate and Maven suite passed: 73 tests, 0 failures/errors/skips. |

## Gates

### Design gate

Use the Sync Contract Matrix as the authoritative structured source when it is
present; retain support for the legacy arrow-form Rule block. Parse compact
completion notation only when it is syntactically a `Concept/action:
[Outcome(...)]` signature. Classify a concept implementation from its declared
base class or annotation rather than its directory name, while recursively
discovering genuine concept agents. Count every testcase in a Cucumber suite,
including a JUnit Platform `CucumberTest` suite, and fail when no scenarios are
executed. Missing specs, malformed signatures, filename/header mismatches,
failing scenarios, and skipped scenarios remain failures.

### Evidence gate

Review focused fixture coverage for accepted current formats and retained
failure cases, plus the canonical profile regression command.

## Notes

- No downstream feature artefacts or application code are part of this change.
- Rollback restores the prior parser behavior; the fixture suite guards the
  compatibility boundary.