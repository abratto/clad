# Smoke test — UC-00-login

> Stage 05 Part 2.1: prove the deployable artefact runs.

The canonical profile is `reference-impl/java-legible/` (fire-after-commit
engine, in-memory `FactStore`). Its deployable artefact is the engine
invoked through `SyncEngine.run`; the flow-token back-trace
(`FlowTraceTest`) and the flow tests (`LoginFlowTest`) are the executable
proof that it runs. The legacy Micronaut/Jena profile (`java-micronaut-jena`)
still boots an HTTP server for the Cucumber flow tests.

## Canonical profile: run the engine + flow tests

```bash
mvn test -f reference-impl/pom.xml -pl java-legible -am
# => legible-engine (13) + java-legible (40) tests, 0 failures
# => FlowTraceTest: the runtime chain matches the chain table for all 4 scenarios
```

## Legacy HTTP profile: boot and smoke

```bash
mvn -f reference-impl/java-micronaut-jena/pom.xml compile exec:java
# boots on port 8080 (Micronaut)
```

- `POST /login` `{"username":"ada","password":"lovelace"}` → `{"sessionToken":...}` (200)
- `POST /login` `{"username":"ada","password":"wrong"}` → `{"message":"username or password didn't match"}` (401)
- `POST /login` `{"username":"nobody","password":"test"}` → `{"message":"username or password didn't match"}` (401)

## Result

- The canonical engine runs the full login flow with behavioural parity
  (identical status codes and field values).
- The flow-token back-trace proves transport entry and exit were reached
  through the authorised action/sync chain.
- Error messages do not leak whether the username or password was wrong.
- Lockout (5 sequential failures) is covered by `FlowTraceTest` and Cucumber.
