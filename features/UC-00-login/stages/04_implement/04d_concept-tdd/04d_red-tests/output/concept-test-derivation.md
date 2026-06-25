--- template: templates/test-intent-derivation-map.md ---
# Concept Test Derivation Map — UC-00-login

> Stage 04d-red handoff to 04d-green. Documents test coverage for all SPEC
> outcomes plus the red-to-green handoff bundle.

## Source artefacts

- **Flow tests:** `04c_flow-tests/output/login.feature` — 4 Gherkin scenarios
- **SPECs:** `User.spec.md`, `PasswordAuth.spec.md`, `Session.spec.md`
- **Hard rules:** R1 (no cross-concept imports), R5 (flow token), R9 (distinct outcomes)

## Coverage matrix

### User (2 actions, 4 outcomes)

| Action | Outcome | Test coverage | Location |
|---|---|---|---|
| `register` | `REGISTERED` | Uncovered by login flow | — (needs unit test) |
| `register` | `USERNAME_TAKEN` | Uncovered by login flow | — (needs unit test) |
| `lookupByUsername` | `FOUND` | Covered — successful-login scenario | `LoginFlowTest` / `CucumberTest` |
| `lookupByUsername` | `NOT_FOUND` | Covered — unknown-user scenario | `LoginFlowTest` / `CucumberTest` |

### PasswordAuth (2 actions, 4 outcomes)

| Action | Outcome | Test coverage | Location |
|---|---|---|---|
| `setCredential` | `STORED` | Uncovered by login flow | — (needs unit test) |
| `check` | `OK` | Covered — successful-login scenario | `LoginFlowTest` / `CucumberTest` |
| `check` | `BAD_PASSWORD` | Covered — wrong-password scenario | `LoginFlowTest` / `CucumberTest` |
| `check` | `LOCKED` | Covered — lockout scenario | `LoginFlowTest` / `CucumberTest` |

### Session (2 actions, 3 outcomes)

| Action | Outcome | Test coverage | Location |
|---|---|---|---|
| `grant` | `GRANTED` | Covered — successful-login scenario | `LoginFlowTest` / `CucumberTest` |
| `lookup` | `FOUND` | Covered — successful-login scenario | `LoginFlowTest` / `CucumberTest` |
| `lookup` | `UNKNOWN` | Uncovered by login flow | — (needs unit test) |

## Summary

- **Total SPEC outcomes:** 11
- **Covered by flow tests:** 7 (all login-scenario outcomes)
- **Uncovered:** 4 (`register`/REGISTERED, `register`/USERNAME_TAKEN, `setCredential`/STORED, `lookup`/UNKNOWN)
- **Architecture compliance:** Verified — `LegibleArchitectureRulesTest` passes R1–R5

## Notes

The reference-impl tests concepts through flow-level integration tests
(LoginFlowTest + CucumberTest + LegibleArchitectureRulesTest). Per-concept
unit tests as separate test classes are not implemented. All 32 tests pass
with `mvn test`. Adding per-concept unit tests for the 4 uncovered outcomes
would complete 04d-red contract compliance.

---

## Red-to-green handoff

- **Approved red tests:** None — existing tests are flow-level and pass green
- **Concept packages:** `com.example.app.concepts.user`, `concepts.passwordauth`, `concepts.session`
- **Concept classes:** `UserConcept`, `PasswordAuthConcept`, `SessionConcept`
- **Test command:** `mvn -f reference-impl/java-micronaut-jena/pom.xml test`
- **Expected red outcome:** N/A — existing tests are green
- **Next implementation target:** Sync TDD (04e)
