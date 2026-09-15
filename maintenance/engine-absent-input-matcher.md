# Maintenance change — `engine-absent-input-matcher`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/legible-engine` (DSL extension + matcher semantics), all profiles through inheritance (`java-legible`, `java-plain`, `java-micronaut-postgres`)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved` (human in-conversation: "Go with A")
- **Evidence gate:** `approved` (test matrix below)
- **Change summary:** The `when`-clause input matcher gains an **absent** semantic: `Dsl.ABSENT` as a matcher value requires the matched trigger-input key to be ABSENT, the negation of the R15 value matcher (key present, equal value). Invocation-presence gating for partial-update fan-outs (conduit rebuild experiment UC-03, first feature to need it) is thereby expressible declaratively — the `OPTIONAL` where clause expresses positive presence only, and literal maps cannot carry a null sentinel (`Map.copyOf` rejects nulls), so no existing surface expressed it.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Engine change only; no stocked-example flow, outcome, or response contract touched (regression: reactor `mvn test` green) |
| Action ordering and sync deduplication | `preserved` | Matcher evaluated at fire time in the trigger check; rule identity unchanged |
| Flow-token lineage | `preserved` | Matcher inside `matchingRules`; `causedBySync` unchanged |
| Storage/retention semantics | `preserved` | `Region`/`FactStore` untouched |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `SyncEngine` javadoc + `Dsl.ABSENT` doc — matcher semantics extended |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `legible-engine` `Dsl` (sentinel), `SyncEngine.patternMatches` (absent branch; visibility widened to package for the engine unit test) |
| Profile tests | yes | `legible-engine/src/test/.../WhenInputPatternTest.java` (new unit test) |
| UC artefact chain | no | features re-derive only when they need the new matcher (conduit rebuild UC-03 does; no retrofit) |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Absent matcher matches only when key absent; value matcher unchanged | unit | `mvn -f reference-impl/pom.xml test` (WhenInputPatternTest) | pass | reactor BUILD SUCCESS, 2 new cases |
| Existing engine + profile suites unaffected | unit | reactor | pass | all modules green |
| Quality-gate suites unaffected | unit | `python3 -m unittest discover -s quality-gate/tests -t quality-gate/tests` | pass | OK |
| Gate pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact |

## Gates

### Design gate

Approved in-conversation by the human ("Go with A") before implementation.

### Evidence gate

Evidence recorded from the executed reactor run; Status set `closed` with the change commit.

## Notes

- `patternMatches` made package-visible static so the engine test exercises the matcher directly; behavioural surface unchanged.
- Semantics: sentinel-first check (`e.getValue() == Dsl.ABSENT → !containsKey`), eliminating the old null-ambiguity branch (`expected == null`); a matcher map cannot contain a true null value since `Map.of`/`Map.copyOf` reject nulls — the old branch was unreachable and is removed.
- Downstream: conduit rebuild experiment's `app/` (fork copy of `legible-engine`) inherits via file sync.
