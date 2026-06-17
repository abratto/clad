// Template for Stage 04c step-definition skeletons (outer-red).
// Derived from: ../02b_chain-table/output/<scenario>-chain.md
//               ../02_concepts/output/<Name>.concept.md
//               ../04b_spec/output/<Name>.spec.md
//
// Each Gherkin Given/When/Then step derives from a use-case precondition, trigger,
// or postcondition. The method body invokes concept actions via the sync engine.
//
// Derivation rules (cross-reference with 02b chain-table rows):
//   Given precondition fixture    ← chain-table row whose action seeds concept state
//   When trigger method           ← chain-table row 1 (Web/request → Web.handle)
//   Then response assertion       ← chain-table last row (Session.grant → Web.respond)
//   Then token chain assertion    ← every non-root row's When/Then/Outcome copied verbatim
//
// Derivation rules (cross-reference with 02 concept specs):
//   Method parameter types   ← concept spec action argument types
//   Assertion enum values    ← concept spec outcome enum variants (SCREAMING_SNAKE_CASE)
//
// Profile adaptation: this skeleton targets Java + Cucumber. For other profiles,
// replace the annotation syntax and assertion helpers while keeping the step text.

package <APP_PACKAGE_ROOT>.steps;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.When;
import io.cucumber.java.en.Then;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Step definitions for UC-XX — <feature name>.
 *
 * Derived from:
 *   ../01_usecase/output/usecase.md  — scenario structure
 *   ../02b_chain-table/output/       — action chain per scenario
 *   ../04b_spec/output/              — SPEC action signatures and outcome enums
 *
 * One step-definition method per chain-table row. The method body
 * invokes the target concept action via the sync engine (not directly)
 * to preserve the declarative coordination boundary (R3).
 *
 * Do not add imperative branching or domain logic in step definitions.
 * If a step needs conditional behavior, it must be expressed through
 * distinct concept outcomes and sync triggers — not step-definition if/else.
 */
public class <FeatureName>StepDefinitions {

    // -----------------------------------------------------------------------
    // Helpers — derived from 04b_spec/output/<Name>.spec.md outcome enums
    // -----------------------------------------------------------------------

    // Outcome enum constants (SCREAMING_SNAKE_CASE)
    // Copied verbatim from 04b_spec/output/ — do not rename or recase.

    // -----------------------------------------------------------------------
    // Background
    // -----------------------------------------------------------------------

    @Given("the system is running")
    public void the_system_is_running() {
        // Boot the test context — typically a no-op if the Cucumber runner
        // starts the application. In profiles without auto-start, start here.
    }

    // -----------------------------------------------------------------------
    // Scenarios — one block per use-case scenario
    // Derived from usecase.md ### Scenario: <name>
    // -----------------------------------------------------------------------

    @Given("a registered user exists")
    public void a_registered_user_exists() {
        // Seed: User.lookupByUsername must return FOUND for the test user.
        // Maps to chain-table row in the registration UC (not this one).
        // In a unit-test environment, inject state directly into the
        // User concept's named region. In an integration-test environment,
        // invoke the registration flow.
    }

    @When("the user submits POST /login with {string} and {string}")
    public void login(String username, String password) {
        // Invoke the flow root via HTTP test client.
        // Maps to chain-table row 1: Web/request[POST /login] → Web.handle
        // Expected token chain from chain-table rows 2–5:
        //   User.lookupByUsername → PasswordAuth.check[OK]
        //   → Session.grant → Web.respond[200]
    }

    @Then("the response status is {int}")
    public void response_status_is(int expectedStatus) {
        // Assert HTTP response status code.
    }

    @Then("the response body matches {string}")
    public void response_body_matches(String expectedBody) {
        // Assert HTTP response body matches the sync spec's then-clause body.
        // For JSON responses, parse and compare field by field.
    }

    @Then("the runtime token chain matches:")
    public void runtime_token_chain_matches(String expectedChain) {
        // Assert the emitted flow tokens match the chain-table row sequence.
        // Reads tokens from the profile's debug surface (e.g., /api/dev/flow/{token})
        // or from the test's captured ActionLog.
        // Each token's action name and outcome must match a chain-table row.
    }

    @Then("no state is modified in any concept")
    public void no_state_modified_in_any_concept() {
        // Assert that no concept's named region changed across the request.
        // Captures concept state snapshots before and after the When step.
    }

    @Then("no state is modified in {string}")
    public void no_state_modified_in_concept(String conceptName) {
        // Assert that a specific concept's named region did not change.
    }

    @Then("the response body matches")
    public void response_body_matches_multiline(String expectedBody) {
        // For multiline response body assertions (e.g., JSON blocks).
    }

    // -----------------------------------------------------------------------
    // Scenario Outlines — step definitions shared across failure branches
    // Derived from usecase.md Extensions: and 02b chain-table branch rows
    // -----------------------------------------------------------------------

    // Scenario Outlines reuse existing step definitions (login, response_status_is, etc.).
    // Additional step definitions for outline-specific parameters go here.

    @Given("the account is locked")
    public void the_account_is_locked() {
        // Seed: PasswordAuth.check must return LOCKED.
        // Sets PasswordAuth.lockedUntil[userId] to a future timestamp.
    }

    @Given("no user exists with that username")
    public void no_user_exists_with_that_username() {
        // Seed: User.lookupByUsername must return NOT_FOUND.
        // Ensures the test username is not registered.
    }

    // -----------------------------------------------------------------------
    // Derivation completeness marker
    // -----------------------------------------------------------------------

    // All step-definition methods above are currently stubs (red).
    // They go green when 04e (sync TDD) completes.
    // Each method corresponds to one row in the chain table for its scenario.
    // No step-definition method exists without a matching chain-table row.
}
