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
  2. `User.lookupByUsername { outcome: NOT_FOUND }`
- **Expected response:** `401 Unauthorized` with the **same message** as `wrong-password` (no enumeration leak).

## Scenario `lockout`

- **Trigger:** `POST /login { username: "ada", password: "<any>" }` when the account is already locked.
- **Expected token chain:**
  1. `Web.handle`
  2. `User.lookupByUsername { outcome: FOUND }`
  3. `PasswordAuth.check { outcome: LOCKED }`
- **Expected response:** `401 Unauthorized { message: "Too many attempts. Try again in 15 minutes." }`
