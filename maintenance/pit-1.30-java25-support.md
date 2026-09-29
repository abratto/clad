<!-- Maintenance-route planning record for the PIT 1.30.0 upgrade. -->
# Maintenance change — `pit-1.30-java25-support`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/java-legible` (canonical); derived profiles get the version properties
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** pin PIT (pitest-maven) at 1.30.0 and pitest-junit5-plugin
  at 1.2.3 so the mutation gate runs on current JDKs (including Java 25),
  replacing the 1.19.1 pin whose coverage minion aborts on Java 25.

## Mechanism

The mutation gate (`scripts/mutation-score.sh`) runs the PIT Maven plugin
over the java-legible tests and parses its report. The plugin version is
declared once in the reactor pom and referenced by the module:

- `reference-impl/pom.xml:35` — `<pitest.version>1.30.0</pitest.version>`.
- `reference-impl/java-legible/pom.xml:53` — `pitest-maven` uses `${pitest.version}`.
- `reference-impl/java-legible/pom.xml:70` — `pitest-junit5-plugin` uses
  `${pitest.junit5.plugin.version}` (1.2.3).

PIT 1.25.8 introduced the Java 25 compatibility fixes (BigDecimal/BigInteger
mutators); 1.30.0 is the current release. No engine, concept, sync, or
artefact behaviour changes — the gate measures the same suites, it can now
launch on Java 25.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No concept/sync/engine change |
| Action ordering and sync deduplication | `preserved` | No engine change |
| Flow-token lineage | `preserved` | No engine change |
| Storage/retention semantics | `preserved` | No storage change |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `methodology/implementation/TESTING.md`, `clad.properties`, `.github/workflows/ci.yml` comments; this record |
| Profile configuration or deployment files | yes | `reference-impl/pom.xml` (pitest version properties); `reference-impl/java-legible/pom.xml` |
| Engine/runtime implementation | no | — |
| Profile tests | yes | `login/ConceptTest.java` — added R14/R16 field-value and uncovered-action tests so the login suite clears the 80% mutation threshold |
| UC artefact chain | no | No stage artefact change |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| PIT runs on Java 25 and reports a score | integration | `./scripts/mutation-score.sh` | pass | `MUTATION_SCORE: 84.1` (JDK 25) |
| Strict mutation gate passes at threshold 80 | integration | `python3 quality-gate/verify_mutation_score.py --feature-root examples/UC-00-login --scope concepts --require` | pass | `84.6% >= 80.0%` |
| Quality-gate regression suite green | unit | `python3 -m pytest quality-gate/tests -q` | pass | 288 passed |
| Canonical profile green | flow-regression | `mvn -B -ntp verify -f reference-impl/pom.xml -pl java-legible -am` | pass | BUILD SUCCESS |

## Gates

### Design gate

Approved by the human in-conversation on 2026-09-28 ("Go ahead") — upgrade
PIT to 1.30.0, keep the 80% threshold, improve tests if below it.

### Evidence gate

Approved by the human in-conversation after the matrix ran green; Status set
to `closed` and the record committed with the change.

## Notes

- The `MUTATION_SKIP` path in `verify_mutation_score.py` is retained: it still
  guards a future/unsupported JVM or a missing toolchain, and CI runs the gate
  with `--require` so a SKIP cannot pass there.
- Supersedes the "sandbox JDK 25 cannot host PIT" note in
  `maintenance/spec-driven-testing-and-acceptance-spec.md` (corrected there).
- Derived projects should adopt `pitest.version` ≥ 1.25.8; the LegalCare
  experiment app should move its PIT pin to 1.30.0 likewise.
