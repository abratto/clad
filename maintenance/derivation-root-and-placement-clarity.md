# Maintenance change — `derivation-root-and-placement-clarity`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (gate + config docs + stage contracts)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Remove two agent-facing ambiguities found while running the library-lending experiment through the inner TDD loop: (1) `test.source.root` had no stated meaning, so a package-inclusive value silently broke red-test continuity; (2) the Stage 04d-green contract claimed the canonical profile uses a "flat" package, contradicting the immutable red test's package.

## Why (experiment-found)

Both cost a red→green cycle on `UC-01-enrol-member` of the library-lending
experiment.

1. **`test.source.root` semantics.** Every consumer
   (`verify_test_continuity`, `verify_concept_field_assertions`,
   `verify_concept_test_derivation`, `verify_test_naming`,
   `verify_close_evidence`) treats the value as the **test source root** — the
   directory that *contains* package directories. `verify_test_continuity`
   joins the derivation map's relative path onto it, so a value that already
   includes the package (`…/src/test/java/dev/library/lending`) makes every row
   resolve to a non-existent path and the stage reports the file "missing". The
   shipped `clad.properties` example and default both included a package
   (`…/src/test/java/dev/legible`), teaching the wrong shape.

2. **Concept placement.** The 04d-green contract said the canonical
   `java-legible` profile "uses a flat `<APP_PACKAGE_ROOT>` package". But the
   red test is immutable (T2) and its package is fixed when the red stage
   writes it; the green stage cannot move it. The contract must say that the
   feature's `_config/package-and-layout.md` directs placement and that, where
   the profile's habit and the frozen red test disagree, **the approved red
   test's package is authoritative**.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No behaviour change; a config default and contract wording only |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | no | — |
| Profile configuration or deployment files | yes | `clad.properties` — `test.source.root` default/example corrected to the source root, with the meaning documented inline |
| Gate scripts | yes | `verify_test_continuity.py` — the "missing" failure now names the resolved absolute path and the root it searched |
| Gate tests | yes | regression test for the root semantics |
| Stage contracts | yes | `04d_red-tests/CONTEXT.md` (states the continuity path base), `04d_green-impl/CONTEXT.md` (placement authority) |
| UC artefact chain | no | UC-00's `test.source.root` still resolves; its checks walk the tree |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Continuity resolves rows against the test source root | unit | `test_test_continuity.py::test_pass_when_files_unchanged` | pass | 1 file unchanged |
| A wrong (package-inclusive) root fails naming the resolved path | unit | `test_test_continuity.py::test_package_inclusive_root_fails_and_names_the_resolved_path` | pass | `missing:` + `resolved to` + root meaning |
| Drift still fails and routes to R17 | unit | `test_test_continuity.py::test_fail_on_drift_lists_files_and_routing` | pass | — |
| UC-00 pipeline unaffected by the default change | integration | `verify_artefacts.py`; `verify_stage_sequence --through 05` | pass | pipeline intact; sequence intact |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | 137 passed |
| Reactor intact | integration | `mvn -q test -f reference-impl/pom.xml -pl java-legible -am` | pass | exit 0 |

## Gates

### Design gate

Approved in-conversation: adopt the test-source-root meaning for
`test.source.root`, and make the feature's `_config` + the frozen red test
authoritative for package placement.

### Evidence gate

To be recorded before commit.

## Notes

- This is a clarity/correctness fix, not a semantic change: consumers already
  behaved this way; only the documented default and the failure message were
  wrong.
