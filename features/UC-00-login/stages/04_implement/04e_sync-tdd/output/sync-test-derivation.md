<!-- derived from templates/test-intent-derivation-map.md -->
# Sync test-intent derivation — UC-00-login

| Sync | When-pattern | Expected `then` action | Test name | Status |
|---|---|---|---|---|
| UserNamingLookupByUsernameForLoginWhenWebRequestRouted | `Web.request { outcome: ROUTED }` | `UserNaming.lookupByUsername(username)` | `routed_login_invokes_user_lookup` | green — flow coverage |
| PasswordAuthCheckForLoginWhenUserNamingLookupByUsernameFound | `UserNaming.lookupByUsername { outcome: FOUND }` | `PasswordAuth.check(userId, password)` | `found_user_invokes_password_check` | green — flow coverage |
| WhenUserNamingLookupByUsernameNotFoundThenWebRespondForLogin | `UserNaming.lookupByUsername { outcome: NOT_FOUND }` | `Web.respond(401, opaqueMessage)` | `unknown_user_returns_opaque_401` | green — flow coverage |
| SessionGrantForLoginWhenPasswordAuthCheckOk | `PasswordAuth.check { outcome: OK }` | `Session.grant(userId)` | `ok_check_grants_session` | green — unit + flow coverage |
| WebRespondForLoginWhenPasswordAuthCheckBadPassword | `PasswordAuth.check { outcome: BAD_PASSWORD }` | `Web.respond(401, opaqueMessage)` | `bad_password_returns_opaque_401` | green — flow coverage |
| WebRespondForLoginWhenPasswordAuthCheckLocked | `PasswordAuth.check { outcome: LOCKED }` | `Web.respond(401, lockoutMessage)` | `locked_account_returns_lockout_401` | green — flow coverage |
| WebRespondForLoginWhenSessionGrantGranted | `Session.grant { outcome: GRANTED }` | `Web.respond(200, sessionToken)` | `granted_session_returns_token` | green — flow coverage |

## Status

All seven sync implementation classes exist. `SessionGrantForLoginWhenPasswordAuthCheckOk`
has a dedicated sync unit test; the remaining syncs are covered by the
green Cucumber scenarios.
