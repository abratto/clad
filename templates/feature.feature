<!-- Template for Stage 04c outer-red flow tests when the profile supports Cucumber/Gherkin.
     Purpose: see methodology/implementation/STAGES.md §"Stage 04c — Flow tests" and
     the Gherkin integration proposal at methodology/architecture/GHERKIN_INTEGRATION.md.

     This file IS the outer-red test — it is the executable form of the use case.
     It is mechanically DERIVED from ../01_usecase/output/usecase.md, not hand-authored.

     Derivation rules (cross-reference with ../01_usecase/output/usecase.md):
       Feature name              ← usecase.md H1 element text
       @UC-XX tag                ← UC number from the feature folder name
       As a <actor>              ← usecase.md ## Actors, first primary actor listed
       I want <goal>             ← usecase.md ## Operational principle, first sentence
       So that <rationale>       ← usecase.md ## Operational principle, remainder
       Scenario: <name>          ← usecase.md ### Scenario: <name> (one per named scenario)
       @<scenario-name> tag      ← scenario name, hyphenated
       @happy-path / @failure-path ← inferred from Postconditions
       Given <precondition>      ← usecase.md Pre-conditions: bullet (one Given per bullet)
       When <trigger>            ← usecase.md Main flow step 1 (always a primary actor action)
       Then <response assertion> ← usecase.md Expected outcomes:
       Then <state assertion>    ← usecase.md Postconditions — Success: / Postconditions — Failure:
       Scenario Outline          ← usecase.md Extensions: (branching conditions)
       Examples: table           ← extension branches collapsed into rows

     Postconditions — Failure with "no state is modified" → @no-state-change tag + explicit Then assertion.

     Derivation rules (cross-reference with ../02b_chain-table/output/):
       step-definition method signature   ← chain-table Then column action name
       step-def method body (expected)    ← chain-table Inputs + Outcome columns
       token-chain assertion in Then step ← chain-table row sequence

     This template uses the Java profile's step-definition and token-assertion conventions.
     Adjust the step-definition regex and assertion helpers for other profiles.

     -->

@<UC-XX> @<feature-slug>
Feature: <Feature name>

  As a <primary actor>
  I want <goal from operational principle>
  So that <rationale from operational principle>

  Background:
    Given the system is running

  @<scenario-name> @happy-path
  Scenario: <scenario-name>
    Given <precondition 1>
    Given <precondition 2>
    When <trigger action from main-flow step 1>
    Then the response status is <expected HTTP status>
    And the response body matches <expected shape>
    And the runtime token chain matches:<expected token sequence>

  @<scenario-name> @failure-path
  Scenario: <scenario-name>
    Given <precondition 1>
    When <trigger action from main-flow step 1>
    Then the response status is <expected HTTP status>
    And the response body matches <expected shape>
    And no state is modified in <ConceptName>
    And the runtime token chain matches:<expected token sequence>

  @<scenario-name> @failure-path @no-state-change
  Scenario: <scenario-name>
    Given <precondition 1>
    When <trigger action from main-flow step 1>
    Then the response status is <expected HTTP status>
    And the response body matches <expected shape>
    And no state is modified in any concept
    And the runtime token chain matches:<expected token sequence>

  @<scenario-name> @failure-path
  Scenario Outline: <scenario-name> — <branch-condition>
    Given <shared precondition>
    When the user submits <route> with "<field1>" and "<field2>"
    Then the response status is <status>
    And the response body matches "<message>"
    And the runtime token chain matches:<expected token chain>

    Examples:
      | branch-condition | field1 | field2 | status | message | expected token chain |
      | <condition 1>    | <val>  | <val>  | <code> | <msg>   | <token seq>          |
      | <condition 2>    | <val>  | <val>  | <code> | <msg>   | <token seq>          |

  @contract @<endpoint-slug>
  Scenario: <METHOD> <path> matches the external contract
    When <trigger action from main-flow step 1>
    Then the response status is <expected HTTP status>
    And the response body has JSON path <json.path> with type <type>
    And the response body has JSON path <json.path> with value <value>
    And the primary error response body matches envelope <exact error envelope>
