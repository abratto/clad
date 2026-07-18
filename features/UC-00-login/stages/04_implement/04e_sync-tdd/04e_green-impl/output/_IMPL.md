--- stage: 04e-green ---
# Sync Implementation — UC-00-login

Implementation classes exist under `reference-impl/java-micronaut-jena/src/main/java/com/example/app/syncs/`:

- `WhenWebHandleRoutedThenUserLookupByUsernameForLogin.java`
- `WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin.java`
- `WhenPasswordAuthCheckOkThenSessionGrantForLogin.java`
- `WhenSessionGrantGrantedThenWebRespondForLogin.java`
- `WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.java`
- `WhenPasswordAuthCheckLockedThenWebRespondForLogin.java`
- `WhenUserLookupByUsernameNotFoundThenWebRespondForLogin.java`

## Verification

```
mvn -f reference-impl/java-micronaut-jena/pom.xml test
→ BUILD SUCCESS (46 tests, 0 failures)
```

- All sync tests pass (Cucumber: 4 scenarios, 0 failed)
- Outer flow tests green (CucumberTest: 4 scenarios, 0 failures)
- All syncs are declarative (R3) — no imperative coordinator classes
- Sync count matches chain-table transitions (7)
