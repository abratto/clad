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
| `lookupByUsername` | `FOUND` | Covered — successful-login scenario | `CucumberTest` |
| `lookupByUsername` | `NOT_FOUND` | Covered — unknown-user scenario | `CucumberTest` |

### PasswordAuth (2 actions, 4 outcomes)

| Action | Outcome | Test coverage | Location |
|---|---|---|---|
| `setCredential` | `STORED` | Uncovered by login flow | — (needs unit test) |
| `check` | `OK` | Covered — successful-login scenario | `CucumberTest` |
| `check` | `BAD_PASSWORD` | Covered — wrong-password scenario | `CucumberTest` |
| `check` | `LOCKED` | Covered — lockout scenario | `CucumberTest` |

### Session (2 actions, 3 outcomes)

| Action | Outcome | Test coverage | Location |
|---|---|---|---|
| `grant` | `GRANTED` | Covered — successful-login scenario | `CucumberTest` |
| `lookup` | `FOUND` | Uncovered by login flow | — (needs unit test) |
| `lookup` | `UNKNOWN` | Uncovered by login flow | — (needs unit test) |

## Summary

- **Total SPEC outcomes:** 11
- **Covered by flow tests:** 6 (all login-scenario outcomes)
- **Uncovered:** 5 (`register`/REGISTERED, `register`/USERNAME_TAKEN, `setCredential`/STORED, `lookup`/FOUND, `lookup`/UNKNOWN)
- **Architecture compliance:** Verified — `LegibleArchitectureRulesTest` passes R1–R5

## Notes

The reference implementation tests login-critical concept behavior through
`UserLookupByUsernameTest`, `PasswordAuthCheckTest`, CucumberTest,
CucumberTest, and LegibleArchitectureRulesTest. Dedicated concept tests for
the 5 uncovered non-login outcomes would complete 04d-red contract coverage.
The current baseline is `mvn verify` with 46 tests and 0 failures.

---

## Red-to-green handoff

- **Approved red tests:** None — existing tests are flow-level and pass green
- **Concept packages:** `com.example.app.concepts.user`, `concepts.passwordauth`, `concepts.session`
- **Concept classes:** `UserConcept`, `PasswordAuthConcept`, `SessionConcept`
- **Test command:** `mvn -f reference-impl/java-micronaut-jena/pom.xml test`
- **Expected red outcome:** N/A — existing tests are green
- **Next implementation target:** Sync TDD (04e)
