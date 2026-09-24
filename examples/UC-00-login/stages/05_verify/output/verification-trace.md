Resume point: next feature — registration or iterative change to login (add role-based routing).

# Verification trace — UC-00-login

> Stage 05 back-trace from runtime behaviour to use case scenarios.

## Methodology

Traces the runtime flow-token chains against the chain table
(`01b_chain-table/output/`) and the syncs (`03_syncs/output/`). The
canonical runtime evidence is the fire-after-commit engine's flow-token
back-trace: `FlowTraceTest` (in `reference-impl/java-legible/`) asserts the
ordered `Concept/action` chain + outcomes recorded on the action log match
the chain table, and that every non-root action carries the sync that
authorised it (`causedBySync`). The legacy Jena profile's Cucumber flow
tests (`login.feature`) remain the HTTP-level regression oracle.

## Per-scenario trace

### successful-login

- **Trigger:** `POST /login { username: "ada", password: "lovelace" }`
- **Expected chain (from 01b):**
  1. `Web/request[POST /login]` => `Routed`
  2. `UserNaming/lookupByUsername(username)` => `Found`
  3. `PasswordAuth/check(userId, password)` => `Ok`
  4. `Session/grant(userId)` => `Granted`
  5. `Web/respond[200, { sessionToken }]`
- **Runtime trace:** `FlowTraceTest.successfulLoginRuntimeChainMatchesChainTable` — PASSES
- **Flow test:** `login.feature` Scenario `successful-login` — PASSES (Cucumber)
- **Verdict:** covered

### wrong-password

- **Trigger:** `POST /login { username: "ada", password: "wrong" }`
- **Expected chain:**
  1. `Web/request[POST /login]` => `Routed`
  2. `UserNaming/lookupByUsername(username)` => `Found`
  3. `PasswordAuth/check(userId, password)` => `BadPassword`
  4. `Web/respond[401, { message: "username or password didn't match" }]`
- **Runtime trace:** `FlowTraceTest.wrongPasswordRuntimeChainMatchesChainTable` — PASSES
- **Flow test:** `login.feature` Scenario `wrong-password` — PASSES (Cucumber)
- **Verdict:** covered

### unknown-user

- **Trigger:** `POST /login { username: "nobody", password: "test" }`
- **Expected chain:**
  1. `Web/request[POST /login]` => `Routed`
  2. `UserNaming/lookupByUsername(username)` => `Refused`
  3. `Web/respond[401, { message: "username or password didn't match" }]`
- **Runtime trace:** `FlowTraceTest.unknownUserRuntimeChainMatchesChainTable` — PASSES
- **Flow test:** `login.feature` Scenario `unknown-user` — PASSES (Cucumber)
- **Verdict:** covered

### lockout

- **Trigger:** `POST /login { username: "ada", password: "wrong" }` (x 5 failures)
- **Expected chain:**
  1. `Web/request[POST /login]` => `Routed`
  2. `UserNaming/lookupByUsername(username)` => `Found`
  3. `PasswordAuth/check(userId, password)` => `Locked`
  4. `Web/respond[401, { message: "Too many attempts. Try again in 15 minutes." }]`
- **Runtime trace:** `FlowTraceTest.lockoutRuntimeChainMatchesChainTable` — PASSES
- **Flow test:** `login.feature` Scenario `lockout` — PASSES (Cucumber)
- **Verdict:** covered

## Test evidence

```
mvn test -f reference-impl/pom.xml
=> BUILD SUCCESS (5 modules)
=> legible-engine + java-legible: 53 tests, 0 failures (fire-after-commit engine,
   including FlowTraceTest, ConcurrencyTest, matcher/semantics/debug suites)
=> java-micronaut-jena: 67 tests, 0 failures (legacy transactional engine)
=> Cucumber: 4 scenarios, 4 passed
```

## Coverage summary

| Scenario | Status |
|---|---|
| successful-login | covered |
| wrong-password | covered |
| unknown-user | covered |
| lockout | covered |

No scenarios at "missing" or "partial."
