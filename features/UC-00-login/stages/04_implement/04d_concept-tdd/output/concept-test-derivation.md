<!-- derived from templates/test-intent-derivation-map.md -->
# Concept test-intent derivation — UC-00-login

For each public action × outcome, exactly one test row.

| Concept | Action | Outcome | Test name | Status |
|---|---|---|---|---|
| User | `register` | `REGISTERED` | `register_returns_REGISTERED_for_fresh_username` | stub |
| User | `register` | `USERNAME_TAKEN` | `register_returns_USERNAME_TAKEN_when_username_exists` | stub |
| User | `lookupByUsername` | `FOUND` | `lookupByUsername_returns_FOUND_for_registered_username` | green — `UserLookupByUsernameTest` |
| User | `lookupByUsername` | `NOT_FOUND` | `lookupByUsername_returns_NOT_FOUND_for_unregistered_username` | green — `UserLookupByUsernameTest` |
| PasswordAuth | `setCredential` | `STORED` | `setCredential_stores_verifier` | stub |
| PasswordAuth | `check` | `OK` | `check_returns_OK_for_matching_password` | green — `PasswordAuthCheckTest` |
| PasswordAuth | `check` | `BAD_PASSWORD` | `check_returns_BAD_PASSWORD_for_mismatched_password` | green — `PasswordAuthCheckTest` |
| PasswordAuth | `check` | `LOCKED` | `check_returns_LOCKED_for_locked_account` | green — `PasswordAuthCheckTest` |
| Session | `grant` | `GRANTED` | `grant_mints_new_sessionId_for_userId` | green — flow/sync coverage |
| Session | `lookup` | `FOUND` | `lookup_returns_userId_for_active_session` | stub |
| Session | `lookup` | `UNKNOWN` | `lookup_returns_empty_for_unknown_session` | stub |

## Status

The Java reference profile now has dedicated concept tests for
`User.lookupByUsername` and `PasswordAuth.check`; `Session.grant` is
covered through sync and flow tests. `register`, `setCredential`, and
`Session.lookup` remain outside the UC-00 login flow and need dedicated
unit tests when a feature depends on them. The current verification
baseline is `mvn verify` with 46 tests and 0 failures.
