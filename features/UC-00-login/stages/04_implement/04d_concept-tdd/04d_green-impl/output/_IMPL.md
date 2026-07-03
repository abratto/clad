--- stage: 04d-green ---
# Concept Implementation — UC-00-login

Implementation classes exist under `reference-impl/java-micronaut-jena/src/main/java/com/example/app/concepts/`:

- `user/UserConcept.java` — `register()`, `lookupByUsername()`
- `passwordauth/PasswordAuthConcept.java` — `setCredential()`, `check()`
- `session/SessionConcept.java` — `grant()`, `lookup()`

## Verification

```
mvn -f reference-impl/java-micronaut-jena/pom.xml test
→ BUILD SUCCESS (46 tests, 0 failures)
```

All concept actions emit flow tokens (R5). No cross-concept imports (R1).
Architecture rules verified by `LegibleArchitectureRulesTest` (16 checks pass).
