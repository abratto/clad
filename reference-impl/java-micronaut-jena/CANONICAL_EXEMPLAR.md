# Canonical Declarative Exemplar — Java/Jena/Micronaut

This file names the **canonical implementation shape** to copy when a
feature chooses the Java/Jena/Micronaut reference profile.

It is a **profile realization pattern**, not a source of business truth.
The authoritative inputs for implementation remain the feature's own
approved upstream artefacts:

- Stage 02 concept specs
- Stage 03 sync specs
- Stage 04b SPEC slices
- Stage 04c expected authored action chains
- approved red tests from Stage 04d / 04e

If this exemplar appears to conflict with those upstream artefacts, the
upstream artefacts win and implementation must stop rather than copying
the profile example blindly.

For the deterministic lowering rules that connect a Stage 03 sync spec
to a `SyncAgent` SPARQL implementation, read
[`SYNC_LOWERING.md`](SYNC_LOWERING.md) alongside this exemplar. The
exemplar shows one canonical slice; the lowering doc names the stepwise
translation contract.

## The canonical slice

For this profile, the canonical declarative slice is the UC-00 login
flow implemented by:

- `infrastructure/WebController.java` — transport-only bootstrap entry
- `engine/FlowManager.java` — root action + flow token minting
- `engine/SyncDispatcher.java` — sync scheduling loop
- `engine/ConceptAgent.java` — per-concept polling/action boundary
- `engine/SyncAgent.java` — declarative `whereClause()` /
  `thenBindings()` sync shape plus shared SPARQL parameterization hook
- `concepts/user/UserConcept.java`
- `concepts/passwordauth/PasswordAuthConcept.java`
- `concepts/session/SessionConcept.java`
- `syncs/WhenWebHandleRoutedThenUserLookupByUsernameForLogin.java`
- `syncs/WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin.java`
- `syncs/WhenUserLookupByUsernameRefusedThenWebRespondForLogin.java`
- `syncs/WhenPasswordAuthCheckOkThenSessionGrantForLogin.java`
- `syncs/WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.java`
- `syncs/WhenPasswordAuthCheckLockedThenWebRespondForLogin.java`
- `syncs/WhenSessionGrantGrantedThenWebRespondForLogin.java`
- `src/test/java/com/example/app/steps/LoginStepDefinitions.java`
- `features/UC-00-login/stages/04_implement/04c_flow-tests/output/login.feature`

## What to copy from this exemplar

- one transport-only `WebController`
- one `*Concept` class per concept package, extending `ConceptAgent`
- one declarative `SyncAgent` subclass per approved sync
- sync SPARQL fragments written as Java text blocks with `.formatted()`
  for IRI constants
- non-outcome discriminator literals centralized as Java constants and
  bound through `SyncAgent.parameterizeSparql(...)`
- the package split itself: `api`, `infrastructure`, `engine`,
  `concepts.<name>`, `syncs`, and `flows` tests
- no coordinator / orchestrator class that sequences domain calls
- flow completion through `Web/respond`, not inline controller branching
- flow tests and runtime debug evidence aligned to the expected authored
  action chain

## What not to copy from this exemplar

- package names or source roots as if they were mandatory defaults
- specific domain names like `User`, `PasswordAuth`, `Session`, or
  `login`
- any implementation detail not justified by the current feature's own
  approved upstream artefacts

For the concrete code pattern, read the login sync classes together with
[`SYNC_LOWERING.md`](SYNC_LOWERING.md): they are the working exemplar
for text-block SPARQL fragments, explicit outcome literals, and
parameterized route/message literals in this profile.

## Legacy-code rule for derived repositories

In a CLAD-derived repository, **working code is not automatically
canonical code**. If a repository still contains imperative
coordinators, mixed architectural styles, or transitional code, that
code must be treated as non-authoritative precedent unless it is
explicitly marked as the canonical exemplar.

When in doubt, copy the declarative login slice above, not a richer but
architecturally mixed flow elsewhere in the repository.