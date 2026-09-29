<!-- Acceptance Spec — the frozen Gate-3 artifact (DR-0001). See
templates/acceptance-spec.md. Native tests: LoginFlowTest (java-legible profile). -->
# Acceptance spec — UC-00 login

## Scenario: successful-login

- **Trigger:** `POST /login { username: "ada", password: "<correct>" }`
- **Expected response:** `200 OK { sessionToken: <S> }`
- **Expected token chain:** `Web.request[ROUTED]` -> `UserNaming.lookupByUsername[FOUND]` -> `PasswordAuth.check[OK]` -> `Session.grant[GRANTED]` -> `Web.respond[SENT]`
- **Postconditions:** a session exists for the user; the response carries a non-empty token.
- **Test:** `LoginFlowTest.successfulLoginReturns200WithSessionToken`
- **Test:** `LoginFlowTest.successfulFlowRecordsExpectedConcepts`

## Scenario: wrong-password

- **Trigger:** `POST /login { username: "ada", password: "<wrong>" }`
- **Expected response:** `401 Unauthorized { message: "username or password didn't match" }`
- **Expected token chain:** `Web.request[ROUTED]` -> `UserNaming.lookupByUsername[FOUND]` -> `PasswordAuth.check[BAD_PASSWORD]` -> `Web.respond[SENT]`
- **Postconditions:** no session is minted.
- **Test:** `LoginFlowTest.wrongPasswordReturns401WithOpaqueMessage`

## Scenario: unknown-user

- **Trigger:** `POST /login { username: "nobody", password: "anything" }`
- **Expected response:** `401 Unauthorized { message: "username or password didn't match" }` (same message as `wrong-password`; no enumeration leak)
- **Expected token chain:** `Web.request[ROUTED]` -> `UserNaming.lookupByUsername[NOT_FOUND]` -> `Web.respond[SENT]`
- **Postconditions:** no session is minted; no state changes.
- **Test:** `LoginFlowTest.unknownUserReturns401WithOpaqueMessage`

## Scenario: lockout

- **Trigger:** `POST /login { username: "ada", password: "<any>" }` when the account is locked
- **Expected response:** `401 Unauthorized { message: "Too many attempts. Try again in 15 minutes." }`
- **Expected token chain:** `Web.request[ROUTED]` -> `UserNaming.lookupByUsername[FOUND]` -> `PasswordAuth.check[LOCKED]` -> `Web.respond[SENT]`
- **Postconditions:** the account remains locked for the window; no session is minted.
- **Test:** `LoginFlowTest.lockoutReturns401WithVisibleMessage`
- **Test:** `LoginFlowTest.lockoutIsNotPermanentAfterWindow`
