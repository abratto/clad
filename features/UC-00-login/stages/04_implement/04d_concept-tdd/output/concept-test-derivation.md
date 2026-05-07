<!-- derived from templates/test-intent-derivation-map.md -->
# Concept test-intent derivation — UC-00-login

For each public action × outcome, exactly one test row.

| Concept | Action | Outcome | Test name | Status |
|---|---|---|---|---|
| User | `register` | `REGISTERED` | `register_returns_REGISTERED_for_fresh_username` | stub |
| User | `register` | `USERNAME_TAKEN` | `register_returns_USERNAME_TAKEN_when_username_exists` | stub |
| User | `lookupByUsername` | `FOUND` | `lookupByUsername_returns_FOUND_for_registered_username` | stub |
| User | `lookupByUsername` | `UNKNOWN` | `lookupByUsername_returns_UNKNOWN_for_unregistered_username` | stub |
| PasswordAuth | `setCredential` | `STORED` | `setCredential_stores_verifier` | stub |
| PasswordAuth | `check` | `OK` | `check_returns_OK_for_matching_password` | stub |
| PasswordAuth | `check` | `BAD_PASSWORD` | `check_returns_BAD_PASSWORD_for_mismatched_password` | stub |
| PasswordAuth | `check` | `NO_CREDENTIAL` | `check_returns_NO_CREDENTIAL_when_no_verifier_set` | stub |
| Session | `grant` | `GRANTED` | `grant_mints_new_sessionId_for_userId` | stub |
| Session | `lookup` | `ACTIVE` | `lookup_returns_userId_for_active_session` | stub |
| Session | `lookup` | `UNKNOWN` | `lookup_returns_empty_for_unknown_session` | stub |

## Status

All rows currently `stub`. They flip to `green` as the inner loop runs
under the chosen profile. The minimal Java stub classes
(`UserConcept`, `PasswordAuthConcept`, `SessionConcept`) already exist
under `reference-impl/java-micronaut-jena/` and emit the right flow
tokens, but the unit-test files themselves are not yet written;
adding them is the next iteration's first task.
