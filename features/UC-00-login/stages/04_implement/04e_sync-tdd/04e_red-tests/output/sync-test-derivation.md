--- template: templates/test-intent-derivation-map.md ---
# Sync Test Derivation Map — UC-00-login

> Stage 04e-red handoff to 04e-green. Documents test coverage for all
> approved syncs against chain-table transitions and outer flow expectations.

## Source artefacts

- **Sync specs:** `03_syncs/output/` — 7 sync files
- **Outer flow:** `04c_flow-tests/output/login.feature` — 4 Gherkin scenarios
- **contracts:** `UserNaming.contract.md`, `PasswordAuth.contract.md`, `Session.contract.md`

## Sync coverage matrix

| Sync | Chain table | Flow scenario | Tested by |
|---|---|---|---|
| `LookupByUsernameForLoginWhenRequestRouted` | Row 1→2 | successful-login, wrong-pw, lockout, unknown-user | `CucumberTest` |
| `CheckForLoginWhenLookupByUsernameFound` | Row 2→3 | successful-login, wrong-pw, lockout | `CucumberTest` |
| `GrantForLoginWhenCheckOk` | Row 3→4 | successful-login | `CucumberTest` |
| `RespondForLoginWhenGrantGranted` | Row 4→5 | successful-login | `CucumberTest` |
| `RespondForLoginWhenCheckBadPassword` | Row 3a | wrong-password | `CucumberTest` |
| `RespondForLoginWhenCheckLocked` | Row 3b | lockout | `CucumberTest` |
| `RespondForLoginWhenLookupByUsernameRefused` | Row 2a | unknown-user | `CucumberTest` |

## Gherkin scenario coverage

| Scenario | Syncs exercised |
|---|---|
| `successful-login` | LookupByUsernameForLoginWhenRequestRouted, CheckForLoginWhenLookupByUsernameFound, GrantForLoginWhenCheckOk, RespondForLoginWhenGrantGranted |
| `wrong-password` | LookupByUsernameForLoginWhenRequestRouted, CheckForLoginWhenLookupByUsernameFound, RespondForLoginWhenCheckBadPassword |
| `lockout` | LookupByUsernameForLoginWhenRequestRouted, CheckForLoginWhenLookupByUsernameFound, RespondForLoginWhenCheckLocked |
| `unknown-user` | LookupByUsernameForLoginWhenRequestRouted, RespondForLoginWhenLookupByUsernameRefused |

All 4 Cucumber scenarios pass (0 failures).

## Architecture compliance

- **R3 (declarative syncs):** Verified — all 7 sync classes extend `SyncAgent` with SPARQL text-block fragments, no imperative branching
- **R1 (no cross-concept imports):** Verified — `LegibleArchitectureRulesTest` passes
- **No coordinator/orchestrator classes:** Verified — all coordination is through syncs

## Summary

- **Total syncs:** 7 (matching chain-table transitions)
- **All syncs covered by flow tests:** Yes — 100%
- **Outer flow tests green:** Yes — all 4 Gherkin scenarios pass
- **All 46 tests pass:** Yes — `mvn verify` BUILD SUCCESS

## Notes

The reference implementation tests syncs through flow-level integration
tests (CucumberTest) and a dedicated unit test for
`GrantForLoginWhenCheckOk`. All sync implementations
exist under `com.example.app.syncs` with matching spec artefacts.

---

## Red-to-green handoff

- **Approved red tests:** None — existing tests are flow-level and pass green
- **Sync package:** `com.example.app.syncs`
- **Sync classes:** `LookupByUsernameForLoginWhenRequestRouted`, `CheckForLoginWhenLookupByUsernameFound`,
  `GrantForLoginWhenCheckOk`, `RespondForLoginWhenGrantGranted`, `RespondForLoginWhenCheckBadPassword`,
  `RespondForLoginWhenCheckLocked`, `RespondForLoginWhenLookupByUsernameRefused`
- **Test command:** `mvn -f reference-impl/java-micronaut-jena/pom.xml test`
- **Expected red outcome:** N/A — existing tests are green
- **Next implementation target:** Stage 05 verification
