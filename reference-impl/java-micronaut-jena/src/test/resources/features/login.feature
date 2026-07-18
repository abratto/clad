# =============================================================================
# Derived from: features/UC-00-login/stages/01_usecase/output/usecase.md
# Derivation rules (see templates/feature.feature):
#   Feature name         ← usecase.md H1 "UC-00 — Login"
#   @UC-00               ← UC number from feature folder name
#   As a User            ← usecase.md ## Actors: primary actor
#   I want ...           ← usecase.md ## Operational principle, first sentence
#   So that ...          ← usecase.md ## Operational principle, remainder
#   Scenario:            ← one per usecase.md ### Scenario: <name>
#   Given                ← usecase.md Pre-conditions: bullets
#   When                 ← usecase.md Main flow step 1 (actor action)
#   Then / And           ← usecase.md Expected outcomes: + Postconditions
#   @no-state-change     ← Postconditions — Failure: "no state is modified"
#   @failure-path        ← Postconditions — Success: "Not applicable"
#   Scenario Outline     ← Extensions with shared trigger
# =============================================================================
# This file is a derived view — do not hand-edit. Regenerate from the use case.

@UC-00 @login
Feature: Login

  As a User
  I want to log in with my username and password
  So that the system can authenticate me and open a session

  Background:
    Given the system is running

  # Derived from usecase.md ### Scenario: successful-login
  # Expected token chain (from 02b_chain-table/output/successful-login-chain.md):
  #   Web/request[POST /login] → Web.handle → User.lookupByUsername[Found]
  #   → PasswordAuth.check[OK] → Session.grant[Granted] → Web.respond[200]
  @successful-login @happy-path
  Scenario: Successful login
    Given a registered user exists
    And the user has a password credential
    And the account is not locked
    When the user submits POST /login with "ada" and "correct-horse-battery-staple"
    Then the response status is 200
    And the response body contains "sessionToken"
    And the response carries a flow-token header

  # Derived from usecase.md ### Scenario: wrong-password
  # Expected token chain (from 02b_chain-table/output/wrong-password-chain.md):
  #   Web/request[POST /login] → Web.handle → User.lookupByUsername[Found]
  #   → PasswordAuth.check[BadPassword] → Web.respond[401]
  # Response literal from 03_syncs/output/WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.sync.md:
  #   body={ message: "username or password didn't match" }
  @wrong-password @failure-path
  Scenario: Wrong password
    Given a registered user exists
    And the account is below the lockout threshold
    When the user submits POST /login with "ada" and "wrong"
    Then the response status is 401
    And the response body contains "username or password didn't match"

  # Derived from usecase.md ### Scenario: unknown-user
  # Expected token chain (from 02b_chain-table/output/unknown-user-chain.md):
  #   Web/request[POST /login] → Web.handle → User.lookupByUsername[Refused]
  #   → Web.respond[401]
  # Response literal from 03_syncs/output/WhenUserLookupByUsernameRefusedThenWebRespondForLogin.sync.md:
  #   body={ message: "username or password didn't match" }
  # Postconditions — Failure: "No state is modified in any concept."
  @unknown-user @failure-path @no-state-change
  Scenario: Unknown user
    Given no registered user exists with that username
    When the user submits POST /login with "nobody" and "anything"
    Then the response status is 401
    And the response body contains "username or password didn't match"
    And no state is modified in any concept

  # Derived from usecase.md ### Scenario: lockout
  # Expected token chain (from 02b_chain-table/output/lockout-chain.md):
  #   Web/request[POST /login] → Web.handle → User.lookupByUsername[Found]
  #   → PasswordAuth.check[Locked] → Web.respond[401]
  # Response literal from 03_syncs/output/WhenPasswordAuthCheckLockedThenWebRespondForLogin.sync.md:
  #   body={ message: "Too many attempts. Try again in 15 minutes." }
  @lockout @failure-path
  Scenario: Account is locked
    Given a registered user exists
    And the account has reached the lockout threshold
    When the user submits POST /login with "ada" and "any"
    Then the response status is 401
    And the response body contains "Too many attempts. Try again in 15 minutes."
