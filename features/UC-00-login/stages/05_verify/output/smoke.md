# Smoke test — UC-00-login

> Stage 05 Part 2.1: prove the deployable artefact runs.

## Build and boot

```bash
mvn -f reference-impl/java-micronaut-jena/pom.xml compile exec:java
```

Application boots on port 8080 with Micronaut 4.10.

## Scenario smoke: successful-login

```bash
# Pre-seeded test user: "ada" / "lovelace"
curl -s -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ada","password":"lovelace"}'
# → {"sessionToken":"..."}  (200 OK)
```

## Scenario smoke: wrong-password

```bash
curl -s -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ada","password":"wrong"}'
# → {"message":"username or password didn't match"}  (401)
```

## Scenario smoke: unknown-user

```bash
curl -s -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username":"nobody","password":"test"}'
# → {"message":"username or password didn't match"}  (401)
```

## Result

- App boots and serves on port 8080
- Login endpoint responds to all 3 scenarios
- Response contracts match use-case expected outcomes
- Error messages do not leak whether the username or password was wrong (security)
- Lockout scenario requires 5 sequential failures — verified by Cucumber test
