<!-- Maintenance-route planning record for the plan focus: trimmed gap closure. -->
# Maintenance change — `clad-test-command-scope`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles` (canonical `reference-impl/java-legible` default)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** scope the canonical `test.command` to the `java-legible` module so the R19 gate runs without Docker, and document the full-reactor CI command.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | n/a | No stage artefact or sync spec changed. |
| Action ordering and sync deduplication | n/a | No engine change. |
| Flow-token lineage | n/a | No engine change. |
| Storage/retention semantics | n/a | No storage change. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `clad.properties` comment names the full-reactor CI command. |
| Profile configuration or deployment files | yes | `test.command` now targets `-pl java-legible -am`. |
| Engine/runtime implementation | no | — |
| Profile tests | no | — |
| UC artefact chain | no | No feature artefact changed; UC-00 gates remain valid. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Canonical profile stays green under the scoped command | integration | `mvn test -f reference-impl/pom.xml -pl java-legible -am` | pass | 44 tests, 0 failures |
| Artefact pipeline gate unchanged | unit | `python3 quality-gate/verify_artefacts.py` | pass | pipeline intact |

## Gates

### Design gate

Approved: the human accepted scoping `test.command` to the canonical module and
documenting the full Docker-backed command for CI.

### Evidence gate

Approved: the scoped command is green and the artefact gate is intact.

## Notes

- The full-reactor command (`mvn test -f reference-impl/pom.xml`) still runs the
  durable profiles whose tests need Testcontainers/Docker; it remains the CI gate.
- Rollback: restore the previous `test.command` line.
