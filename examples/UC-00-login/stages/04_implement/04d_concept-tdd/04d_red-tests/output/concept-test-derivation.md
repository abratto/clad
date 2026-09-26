<!-- template: templates/test-intent-derivation-map.md -->

# Test-intent derivation map — UC-00-login (concepts)

> Stage 04d-red handoff to 04d-green. Format A (`### \`Concept.action\` →
> test class` plus the `@Nested` table) is the grammar
> `verify_concept_test_derivation.py` consumes; this worked example was updated
> from a legacy coverage-matrix layout that the parser read as zero rows.

## Use-case scenarios → flow tests

| Scenario | Trigger | Flow test | Status |
|---|---|---|---|
| `successful-login` | `POST /login` | `CucumberTest` | green |
| `wrong-password` | `POST /login` | `CucumberTest` | green |
| `unknown-user` | `POST /login` | `CucumberTest` | green |
| `lockout` | `POST /login` | `CucumberTest` | green |

## Concept actions → concept tests

### `UserNaming.lookupByUsername` → test class: `UserNamingLookupByUsernameTest`

| # | @Nested | Test method | Outcome | Source | Preconditions |
|---|---|---|---|---|---|
| 1 | `WhenUserExists` | `shouldReturnUserIdWhenUsernameIsRegistered()` | `FOUND` | Flow: `successful-login` | none |
| 2 | `WhenUserUnknown` | `shouldRefuseWhenUsernameIsNotRegistered()` | `NOT_FOUND` | Flow: `unknown-user` | none |

### `UserNaming.register` → test class: `UserNamingRegisterTest`

| # | @Nested | Test method | Outcome | Source | Preconditions |
|---|---|---|---|---|---|
| 1 | `WhenUsernameIsFree` | `shouldRegisterWhenUsernameIsFree()` | `REGISTERED` | Spec: `02_concepts/output/UserNaming.concept.md` | none |
| 2 | `WhenUsernameIsTaken` | `shouldRefuseWhenUsernameIsTaken()` | `USERNAME_TAKEN` | Spec: `02_concepts/output/UserNaming.concept.md` | a user named `ada` exists |

### `PasswordAuth.check` → test class: `PasswordAuthCheckTest`

| # | @Nested | Test method | Outcome | Source | Preconditions |
|---|---|---|---|---|---|
| 1 | `WhenPasswordMatches` | `shouldReturnOkWhenPasswordMatches()` | `OK` | Flow: `successful-login` | a credential is stored |
| 2 | `WhenPasswordDiffers` | `shouldReturnBadPasswordWhenPasswordDiffers()` | `BAD_PASSWORD` | Flow: `wrong-password` | a credential is stored |
| 3 | `WhenAttemptsExhausted` | `shouldLockWhenAttemptsAreExhausted()` | `LOCKED` | Flow: `lockout` | a credential and a locked counter state exist |

### `PasswordAuth.setCredential` → test class: `PasswordAuthSetCredentialTest`

| # | @Nested | Test method | Outcome | Source | Preconditions |
|---|---|---|---|---|---|
| 1 | `WhenCredentialIsAbsent` | `shouldStoreWhenNoCredentialExists()` | `STORED` | Spec: `02_concepts/output/PasswordAuth.concept.md` | none |

### `Session.grant` → test class: `SessionGrantTest`

| # | @Nested | Test method | Outcome | Source | Preconditions |
|---|---|---|---|---|---|
| 1 | `WhenPasswordOk` | `shouldGrantWhenPasswordIsOk()` | `GRANTED` | Flow: `successful-login` | a stored credential matches |

### `Session.lookup` → test class: `SessionLookupTest`

| # | @Nested | Test method | Outcome | Source | Preconditions |
|---|---|---|---|---|---|
| 1 | `WhenSessionExists` | `shouldReturnSessionWhenItExists()` | `FOUND` | Spec: `02_concepts/output/Session.concept.md` | a granted session exists |
| 2 | `WhenSessionUnknown` | `shouldReturnUnknownWhenSessionIsAbsent()` | `UNKNOWN` | Spec: `02_concepts/output/Session.concept.md` | none |

## Sync rules → sync tests

> For Stage 04e. One test class per sync; interaction verification only.

| Sync | @Nested class | Test method | Trigger pattern | Resulting actions |
|---|---|---|---|---|
| `GrantForLoginWhenCheckOk` | `WhenCheckOk` | `shouldGrantWhenCheckOk()` | `PasswordAuth.check -> OK` | `Session.grant` |

## Red-To-Green Handoff Bundle

| Item | Value |
|---|---|
| Approved test files | `UserNamingLookupByUsernameTest`, `PasswordAuthCheckTest`, `SessionGrantTest` |
| Exact package names | `dev.legible.example.login` |
| Exact class names | as above |
| Exact method signatures under test | see the tables above |
| Red evidence command | `mvn -f reference-impl/pom.xml test -pl java-legible` |
| Expected red outcome | failing assertions / `@Disabled` stubs |
| Next implementation target | `SyncRules` + concept implementations |

## Test file continuity

| Test file (test-source-root-relative) | SHA-256 at red |
|---|---|
| `dev/legible/example/login/UserNamingLookupByUsernameTest.java` | `<64-hex-sha256>` |
| `dev/legible/example/login/PasswordAuthCheckTest.java` | `<64-hex-sha256>` |
| `dev/legible/example/login/SessionGrantTest.java` | `<64-hex-sha256>` |

## Notes

The non-login outcomes (`register`/`REGISTERED`, `register`/`USERNAME_TAKEN`,
`setCredential`/`STORED`, `lookup`/`FOUND`, `lookup`/`UNKNOWN`) are spec-defined
and covered by dedicated unit tests rather than the login flow — as the
coverage rule requires, each carries a `Spec:` source.
