<!-- derived from templates/test-intent-derivation-map.md -->
# Sync test-intent derivation — UC-00-login

| Sync | When-pattern | Expected `then` action | Test name | Status |
|---|---|---|---|---|
| LookupUserForLogin | `Web.handle { outcome: ROUTED }` | `User.lookupByUsername(username)` | `routed_login_invokes_user_lookup` | stub |
| CheckCredentialForLogin | `User.lookupByUsername { outcome: FOUND }` | `PasswordAuth.check(userId, password)` | `found_user_invokes_password_check` | stub |
| RespondUnknownUser | `User.lookupByUsername { outcome: NOT_FOUND }` | `Web.respond(401, opaqueMessage)` | `unknown_user_returns_opaque_401` | stub |
| GrantSessionForLogin | `PasswordAuth.check { outcome: OK }` | `Session.grant(userId)` | `ok_check_grants_session` | stub |
| RespondWrongPassword | `PasswordAuth.check { outcome: BAD_PASSWORD }` | `Web.respond(401, opaqueMessage)` | `bad_password_returns_opaque_401` | stub |
| RespondLocked | `PasswordAuth.check { outcome: LOCKED }` | `Web.respond(401, lockoutMessage)` | `locked_account_returns_lockout_401` | stub |
| RespondLoginSuccess | `Session.grant { outcome: GRANTED }` | `Web.respond(200, sessionToken)` | `granted_session_returns_token` | stub |

## Status

All rows currently `stub`. The success-path stubs already line up with
the disabled `LoginFlowTest.successful_login_grants_session_and_returns_token`
in the outside loop; an inner-loop unit test under
`com.example.app.syncs` will be added in the next iteration.
