# UC-00 — Login (the canonical worked example)

This feature is the worked example for the whole repository. It is
the simplest thing CLAD can be applied to that is still meaningfully
more than a "hello world": authenticate a user with a username and a
password, and on success establish a session token they can present
on subsequent requests.

It exists to be **read**, not run. The Java reference profile compiles
and the ArchUnit suite passes, but `LoginFlowTest` is `@Disabled`
until the inner-loop tests in `04d` and `04e` ship — see *Status* at
the bottom.

## How to read this folder

Three reading modes are supported:

1. **Linear walkthrough** — read the methodology-level annotated
   transcript first ([`../../methodology/WALKTHROUGH.md`](../../methodology/WALKTHROUGH.md)),
   then walk this folder stage-by-stage in the order below. Best for
   first-time readers.
2. **Single-stage deep-dive** — open one stage's `CONTEXT.md` and its
   `output/`. Each `CONTEXT.md` now opens with a `## Why this stage
   exists` block that names what feeds *out* of it and where each
   output is consumed downstream.
3. **Artefact-graph navigation** — open
   [`../../methodology/architecture/ARTEFACT_MAP.md`](../../methodology/architecture/ARTEFACT_MAP.md)
   and use the per-artefact table to jump between producer and
   consumer. Best when you are about to touch one artefact and need to
   know what else has to be redone.

## Stage-by-stage index, with rationale

Each row links the stage's `CONTEXT.md` (which now carries the *why*
in its first section) and the stage's `output/`. The "Why this stage
matters in UC-00" column is the *feature-specific* rationale on top
of the generic *Why this stage exists* block in each CONTEXT.

| Stage | CONTEXT (with rationale) | Output(s) | Why this stage matters in UC-00 |
|---|---|---|---|
| 00 | [`stages/00_actor-goal/CONTEXT.md`](stages/00_actor-goal/CONTEXT.md) | [`actors.md`](stages/00_actor-goal/output/actors.md), [`goals.md`](stages/00_actor-goal/output/goals.md) | The brief mentions registration, password reset, MFA, SSO, logout. Stage 00 is where each of those gets explicitly marked **out of scope** so the use case can't drift. |
| 01 | [`stages/01_usecase/CONTEXT.md`](stages/01_usecase/CONTEXT.md) | [`usecase.md`](stages/01_usecase/output/usecase.md) | The four scenarios (`successful-login`, `wrong-password`, `unknown-user`, `lockout`) and especially the *Postconditions—Failure* assertion *"no state is modified"* are what make the no-enumeration property mechanically checkable at Stage 04c. |
| 02a | [`stages/02a_responsibility-map/CONTEXT.md`](stages/02a_responsibility-map/CONTEXT.md) | [`responsibility-map.md`](stages/02a_responsibility-map/output/responsibility-map.md) | Three concepts (`User`, `PasswordAuth`, `Session`) plus `Web` (R4 bootstrap). The *Out of scope* note records why `LoginAttemptHistory` and `Account` were rejected as concepts — keeping that visible prevents reinvention later. |
| 02b | [`stages/02b_chain-table/CONTEXT.md`](stages/02b_chain-table/CONTEXT.md) | [`successful-login-chain.md`](stages/02b_chain-table/output/successful-login-chain.md), [`wrong-password-chain.md`](stages/02b_chain-table/output/wrong-password-chain.md), [`unknown-user-chain.md`](stages/02b_chain-table/output/unknown-user-chain.md), [`lockout-chain.md`](stages/02b_chain-table/output/lockout-chain.md), [`login-all-scenarios-chain.md`](stages/02b_chain-table/output/login-all-scenarios-chain.md) | Four canonical scenario chains plus one derived consolidated chain. The canonical tables fix the action names; the consolidated chain makes the full Stage 02b `When -> Then` branching surface explicit for Stage 03 sync derivation without smuggling `where` provenance down from Stage 03. |
| 02 | [`stages/02_concepts/CONTEXT.md`](stages/02_concepts/CONTEXT.md) | [`User.concept.md`](stages/02_concepts/output/User.concept.md), [`PasswordAuth.concept.md`](stages/02_concepts/output/PasswordAuth.concept.md), [`Session.concept.md`](stages/02_concepts/output/Session.concept.md) | R1 in action: `Session.concept.md` works with opaque `UserId` and never names anything from `User`'s state. `Web` deliberately has no concept spec — see [`../../methodology/architecture/WEB_CONCEPT.md`](../../methodology/architecture/WEB_CONCEPT.md). |
| 03 | [`stages/03_syncs/CONTEXT.md`](stages/03_syncs/CONTEXT.md) | [`LoginGrantsSession.sync.md`](stages/03_syncs/output/LoginGrantsSession.sync.md), [`LockoutOnFailedAttempts.sync.md`](stages/03_syncs/output/LockoutOnFailedAttempts.sync.md) | Only the *successful* path needs a sync; the *wrong-password* and *unknown-user* paths are `Web`-only failure responses. `LoginGrantsSession` is the canonical example of a **Pattern B** join (see its `where:` clause and [`../../methodology/architecture/SYNC_PATTERNS.md`](../../methodology/architecture/SYNC_PATTERNS.md)). |
| 03a | [`stages/03a_dependency-review/CONTEXT.md`](stages/03a_dependency-review/CONTEXT.md) | [`User-card.md`](stages/03a_dependency-review/output/User-card.md), [`PasswordAuth-card.md`](stages/03a_dependency-review/output/PasswordAuth-card.md), [`Session-card.md`](stages/03a_dependency-review/output/Session-card.md), [`Web-card.md`](stages/03a_dependency-review/output/Web-card.md), [`pattern-d-summary.md`](stages/03a_dependency-review/output/pattern-d-summary.md) | UC-00 has **no Pattern D reads** — the cards prove it. The first review iteration of these cards is what surfaced the action-name discrepancy that PR #6 reconciled. |
| 04 (router) | [`stages/04_implement/CONTEXT.md`](stages/04_implement/CONTEXT.md) | (sub-stages own all artefacts) | The five sub-stages below are the outside-in TDD double-loop. |
| 04a | [`stages/04_implement/04a_orm/CONTEXT.md`](stages/04_implement/04a_orm/CONTEXT.md) | [`_NOT_APPLICABLE.md`](stages/04_implement/04a_orm/output/_NOT_APPLICABLE.md) | The reference profile is in-memory; a persistent profile would derive `<Name>.orm.md` per concept here from the `state` sections. |
| 04b | [`stages/04_implement/04b_spec/CONTEXT.md`](stages/04_implement/04b_spec/CONTEXT.md) | [`User.spec.md`](stages/04_implement/04b_spec/output/User.spec.md), [`PasswordAuth.spec.md`](stages/04_implement/04b_spec/output/PasswordAuth.spec.md), [`Session.spec.md`](stages/04_implement/04b_spec/output/Session.spec.md) | Mechanically-extracted SPEC slices the test code compiles against. |
| 04c | [`stages/04_implement/04c_flow-tests/CONTEXT.md`](stages/04_implement/04c_flow-tests/CONTEXT.md) | [`login-flow-test.md`](stages/04_implement/04c_flow-tests/output/login-flow-test.md) | The outer-red flow test. Stays red until 04e finishes. |
| 04d | [`stages/04_implement/04d_concept-tdd/CONTEXT.md`](stages/04_implement/04d_concept-tdd/CONTEXT.md) | [`concept-test-derivation.md`](stages/04_implement/04d_concept-tdd/output/concept-test-derivation.md) + per-concept Java | Per-concept inner red→green; no cross-concept imports (R1); every action emits a flow token (R5). |
| 04e | [`stages/04_implement/04e_sync-tdd/CONTEXT.md`](stages/04_implement/04e_sync-tdd/CONTEXT.md) | [`sync-test-derivation.md`](stages/04_implement/04e_sync-tdd/output/sync-test-derivation.md) + per-sync Java | Per-sync inner red→green; the moment the last sync goes green, `04c`'s flow tests do too. |
| 05 | [`stages/05_verify/CONTEXT.md`](stages/05_verify/CONTEXT.md) | [`verification-trace.md`](stages/05_verify/output/verification-trace.md) (+ smoke / tracking when shipped) | Predicted token-tree walk per scenario. Will become a real walk once the inner-loop tests ship and produce flow-token logs. |

## Cross-cutting reads

These don't live in any single stage's `output/` but are part of how
to navigate the feature:

- [`../../methodology/WALKTHROUGH.md`](../../methodology/WALKTHROUGH.md) — turn-by-turn replay of producing UC-00.
- [`../../methodology/architecture/ARTEFACT_MAP.md`](../../methodology/architecture/ARTEFACT_MAP.md) — diagram + per-artefact table mapping every artefact above to its consumers.
- [`../../methodology/architecture/MENTAL_MODEL.md`](../../methodology/architecture/MENTAL_MODEL.md) — OO ↔ WYSIWID intuition; useful before reading the concept specs.
- [`../../methodology/architecture/SYNC_PATTERNS.md`](../../methodology/architecture/SYNC_PATTERNS.md) — the four legal `where` patterns; needed for `LoginGrantsSession`'s Pattern B `where:` clause and for reading the 03a cards.
- [`_config/voice.md`](_config/voice.md) — feature-scoped reference for the tone of the no-enumerating error message.
- [`../../reference-impl/java-micronaut-jena/`](../../reference-impl/java-micronaut-jena/) — minimal Java stubs honouring R1–R5 (ArchUnit-checked).

## Status

Spec-complete; implementation is scaffolding. The Java profile compiles
and `mvn test` runs the ArchUnit suite, but the `LoginFlowTest` is
`@Disabled` until the inner-loop tests in `04d` and `04e` ship.
