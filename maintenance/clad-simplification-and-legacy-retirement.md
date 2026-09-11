<!-- Maintenance-route planning record for the 0.5.0 simplification work. -->
# Maintenance change — `clad-simplification-and-legacy-retirement`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles` (canonical `reference-impl/java-legible` retained; legacy `java-micronaut-jena`/`clad-engine` retired)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** remove dead code, collapse duplicated stage documentation, unify artefact parsing, and retire the legacy RDF/SPARQL profile (preserved at tag `v0.4.0`).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | No stage artefact or sync spec changes; S5 (outcome-casing unification) explicitly deferred. |
| Action ordering and sync deduplication | preserved | No engine or canonical-profile change. |
| Flow-token lineage | preserved | No canonical-profile change. |
| Storage/retention semantics | preserved | Canonical in-memory `FactStore` retained; legacy RDF/SPARQL profile removed, not re-lowered. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `STAGES.md` absorbs the stage manifest; legacy references removed across `methodology/`. |
| Profile configuration or deployment files | yes | `reference-impl/pom.xml` modules reduced (legacy modules removed). |
| Engine/runtime implementation | yes | Legacy `clad-engine`/`java-micronaut-jena` deleted; canonical `legible-engine` untouched. |
| Profile tests | yes | Legacy check branches removed; canonical tests retained. |
| UC artefact chain | no | No feature artefact changes; UC-00 gate hashes stay valid. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Canonical pipeline intact | unit | `python3 quality-gate/verify_artefacts.py` | pass | pipeline intact, 0 defects |
| Doc cross-references intact | unit | `python3 quality-gate/verify_links.py` | pass | 298 links / 104 docs |
| Quality-gate regression suite | unit | `python3 -m pytest quality-gate/tests -q` | pass | 85 tests |
| Canonical profile green | integration | `mvn test -f reference-impl/pom.xml -pl java-legible -am` | pass | BUILD SUCCESS |

## Gates

### Design gate

Approved: human authorized the no-loss simplifications (dead code, manifest
dedupe, stage-lifecycle trim, single artefact grammar) and the legacy-stack
retirement with `v0.4.0` as the preserved last snapshot. Outcome-casing
unification (S5) was deferred.

### Evidence gate

Approved: test matrix green (artefacts, links, 85 tests, canonical module build) and the deletion verified.

## Notes

- Legacy preservation: deleted from the working tree; the last version that
  contains it is tag `v0.4.0` (recorded in `reference-impl/LEGACY.md`).
- Rollback: revert this change's commits; the canonical profile is unaffected.
