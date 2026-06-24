## Historical artefact — superseded by Cucumber/BDD

This native-track flow-test markdown spec is preserved for reference.

**Superseded per CUCUMBER-only standard (2026-06-23).** The active flow
tests for this feature are at `output/login.feature` as a Gherkin
`.feature` file, exercised by the Cucumber runner at
`src/test/java/.../steps/CucumberTest.java`.

The step definitions in `LoginStepDefinitions.java` cover all four
UC-00 scenarios (successful login, wrong password, unknown user, lockout).
