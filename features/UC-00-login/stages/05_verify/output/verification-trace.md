Resume point: next feature — registration or iterative change to login (add role-based routing).

# Verification trace — UC-00-login

> Stage 05 back-trace from runtime behaviour to use case scenarios.

## Methodology

Traces expected flow-token chains from Gherkin scenarios against the
logic in `02b_chain-table/output/` and `03_syncs/output/`. Runtime
evidence from the Micronaut/Jena reference-impl (Java 21) via
`mvn test` + manual API smoke test.

## Per-scenario trace

### successful-login

- **Trigger:** `POST /login { username: "ada", password: "lovelace" }`
- **Expected chain (from 02b):**
  1. `Web.handle[POST /login]` → `Routed`
  2. `User.lookupByUsername(username)` → `FOUND`
  3. `PasswordAuth.check(userId, password)` → `OK`
  4. `Session.grant(userId)` → `GRANTED`
  5. `Web.respond[200, { sessionToken }]`
- **Flow test:** `login.feature` Scenario `successful-login` — PASSES (Cucumber)
- **Manual smoke:** App boots, responds to login request. Response body returns `sessionToken` on valid credentials pre-seeded by the test fixture.
- **Verdict:** covered

### wrong-password

- **Trigger:** `POST /login { username: "ada", password: "wrong" }`
- **Expected chain:**
  1. `Web.handle[POST /login]` → `Routed`
  2. `User.lookupByUsername(username)` → `FOUND`
  3. `PasswordAuth.check(userId, password)` → `BAD_PASSWORD`
  4. `Web.respond[401, { message: "username or password didn't match" }]`
- **Flow test:** `login.feature` Scenario `wrong-password` — PASSES (Cucumber)
- **Manual smoke:** Returns 401 with error message
- **Verdict:** covered

### unknown-user

- **Trigger:** `POST /login { username: "nobody", password: "test" }`
- **Expected chain:**
  1. `Web.handle[POST /login]` → `Routed`
  2. `User.lookupByUsername(username)` → `NOT_FOUND`
  3. `Web.respond[401, { message: "username or password didn't match" }]`
- **Flow test:** `login.feature` Scenario `unknown-user` — PASSES (Cucumber)
- **Manual smoke:** Returns 401 with error message
- **Verdict:** covered

### lockout

- **Trigger:** `POST /login { username: "ada", password: "wrong" }` (× 5 failures)
- **Expected chain:**
  1. `Web.handle[POST /login]` → `Routed`
  2. `User.lookupByUsername(username)` → `FOUND`
  3. `PasswordAuth.check(userId, password)` → `LOCKED`
  4. `Web.respond[401, { message: "account locked — too many attempts" }]`
- **Flow test:** `login.feature` Scenario `lockout` — PASSES (Cucumber)
- **Verdict:** covered (test-only — lockout requires 5 rapid failures)

## Test evidence

```
mvn -f reference-impl/java-micronaut-jena/pom.xml test
→ BUILD SUCCESS
→ Tests run: 32, Failures: 0, Errors: 0, Skipped: 0
→ Cucumber: 4 scenarios, 4 passed
→ ArchUnit: 16 rules checks passed
```

## Coverage summary

| Scenario | Status |
|---|---|
| successful-login | covered |
| wrong-password | covered |
| unknown-user | covered |
| lockout | covered |

No scenarios at "missing" or "partial."
