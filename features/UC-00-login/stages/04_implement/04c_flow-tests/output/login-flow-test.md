<!-- derived from templates/flow.md -->
# Login flow tests

## Scenario `successful-login`

- **Trigger:** `POST /login { username: "ada", password: "<correct>" }`
- **Expected token chain (parent → child):**
  1. `Web.handle { requestId }`
  2. `User.lookupByUsername { username: "ada", userId: U, outcome: FOUND }`
  3. `PasswordAuth.check { userId: U, outcome: OK }`
  4. `Session.grant { userId: U, sessionId: S, outcome: GRANTED }`
- **Expected response:** `200 OK { sessionToken: S }`

## Scenario `wrong-password`

- **Trigger:** `POST /login { username: "ada", password: "<wrong>" }`
- **Expected token chain:**
  1. `Web.handle`
  2. `User.lookupByUsername { outcome: FOUND }`
  3. `PasswordAuth.check { outcome: BAD_PASSWORD }`
- **Expected response:** `401 Unauthorized { message: "username or password didn't match" }`

## Scenario `unknown-user`

- **Trigger:** `POST /login { username: "nobody", password: "anything" }`
- **Expected token chain:**
  1. `Web.handle`
  2. `User.lookupByUsername { outcome: UNKNOWN }`
- **Expected response:** `401 Unauthorized` with the **same message** as `wrong-password` (no enumeration leak).

## Scenario `lockout`

- **Status:** spec-only in this iteration. Requires the `LockoutOnFailedAttempts` sync; the flow test will be added when that sync's tests land in `04e`.
