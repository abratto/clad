<!-- derived from templates/test-intent-derivation-map.md -->
# Sync test-intent derivation — UC-00-login

| Sync | When-pattern | Expected `then` action | Test name | Status |
|---|---|---|---|---|
| LoginGrantsSession | `PasswordAuth.check { outcome: OK }` | `Session.grant(userId)` then `Web.respond(200, sessionId)` | `ok_check_grants_session_and_responds_200` | stub |
| LoginGrantsSession | `PasswordAuth.check { outcome: BAD_PASSWORD }` | (no `then` — `Web` handles failure response directly) | `bad_password_does_not_grant_session` | stub |
| LockoutOnFailedAttempts | `PasswordAuth.check { outcome: BAD_PASSWORD }` ×N | `PasswordAuth.lock(userId)` (action TBD when lockout is added) | `nth_bad_password_locks_account` | stub (sync spec only; concept action pending) |

## Status

All rows currently `stub`. The first row's stub Java test exists as
the disabled `LoginFlowTest.successful_login_grants_session_and_returns_token`
in the outside loop; an inner-loop unit test under
`com.example.app.syncs` will be added in the next iteration.
