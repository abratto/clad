# UC-00 — Login (the canonical worked example)

This feature is the worked example for the whole repository. It is
the simplest thing CLAD can be applied to that is still meaningfully
more than a "hello world": authenticate a user with a username and a
password, and on success establish a session token they can present
on subsequent requests.

Read this folder as the canonical example first. The Java reference
profile is also runnable now, and `mvn test` exercises the active outer-loop
login flow tests end-to-end.

> **Do not copy this folder as a starter template.** UC-00 still contains a
> seed-time `stages/00_actor-goal/` folder for historical/example reasons.
> New work must run Stage 00 only in `features/_system/stages/00_actor-goal/`
> and then copy `templates/feature-skeleton/` for each per-UC feature.

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
| 03 | [`stages/03_syncs/CONTEXT.md`](stages/03_syncs/CONTEXT.md) | [`WhenWebHandleRoutedThenUserLookupByUsernameForLogin.sync.md`](stages/03_syncs/output/WhenWebHandleRoutedThenUserLookupByUsernameForLogin.sync.md), [`WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin.sync.md`](stages/03_syncs/output/WhenUserLookupByUsernameFoundThenPasswordAuthCheckForLogin.sync.md), [`WhenUserLookupByUsernameRefusedThenWebRespondForLogin.sync.md`](stages/03_syncs/output/WhenUserLookupByUsernameRefusedThenWebRespondForLogin.sync.md), [`WhenPasswordAuthCheckOkThenSessionGrantForLogin.sync.md`](stages/03_syncs/output/WhenPasswordAuthCheckOkThenSessionGrantForLogin.sync.md), [`WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.sync.md`](stages/03_syncs/output/WhenPasswordAuthCheckBadPasswordThenWebRespondForLogin.sync.md), [`WhenPasswordAuthCheckLockedThenWebRespondForLogin.sync.md`](stages/03_syncs/output/WhenPasswordAuthCheckLockedThenWebRespondForLogin.sync.md), [`WhenSessionGrantGrantedThenWebRespondForLogin.sync.md`](stages/03_syncs/output/WhenSessionGrantGrantedThenWebRespondForLogin.sync.md) | UC-00 now shows the canonical one-sync-per-transition shape. `WhenSessionGrantGrantedThenWebRespondForLogin` is the worked example's Pattern B join; the 401 branches are syncs too, so Stage 03 remains the single declarative coordination surface. |
| 03a | [`stages/03a_dependency-review/CONTEXT.md`](stages/03a_dependency-review/CONTEXT.md) | [`User-card.md`](stages/03a_dependency-review/output/User-card.md), [`PasswordAuth-card.md`](stages/03a_dependency-review/output/PasswordAuth-card.md), [`Session-card.md`](stages/03a_dependency-review/output/Session-card.md), [`Web-card.md`](stages/03a_dependency-review/output/Web-card.md), [`pattern-d-summary.md`](stages/03a_dependency-review/output/pattern-d-summary.md) | UC-00 has **no Pattern D reads** — the cards prove it. The first review iteration of these cards is what surfaced the action-name discrepancy that PR #6 reconciled. |
| 03b | [`stages/03b_data-model/CONTEXT.md`](stages/03b_data-model/CONTEXT.md) | [`User.data-model.md`](stages/03b_data-model/output/User.data-model.md), [`PasswordAuth.data-model.md`](stages/03b_data-model/output/PasswordAuth.data-model.md), [`Session.data-model.md`](stages/03b_data-model/output/Session.data-model.md) | The feature's conceptual state model is made explicit before any storage mapping. Because UC-00 has no Pattern D reads, these files are concept-local and profile-neutral. |
| 04 (router) | [`stages/04_implement/CONTEXT.md`](stages/04_implement/CONTEXT.md) | (sub-stages own all artefacts) | The five top-level sub-stages below are the outside-in TDD double-loop; `04d` and `04e` are routers with structural red/green child stages. |
| 04a | [`stages/04_implement/04a_storage-mapping/CONTEXT.md`](stages/04_implement/04a_storage-mapping/CONTEXT.md) | [`_NOT_APPLICABLE.md`](stages/04_implement/04a_storage-mapping/output/_NOT_APPLICABLE.md) | The reference profile is in-memory; a persistent profile would map the approved `*.data-model.md` files into profile-specific storage here. |
| 04b | [`stages/04_implement/04b_spec/CONTEXT.md`](stages/04_implement/04b_spec/CONTEXT.md) | [`User.spec.md`](stages/04_implement/04b_spec/output/User.spec.md), [`PasswordAuth.spec.md`](stages/04_implement/04b_spec/output/PasswordAuth.spec.md), [`Session.spec.md`](stages/04_implement/04b_spec/output/Session.spec.md) | Mechanically-extracted SPEC slices the test code compiles against. |
| 04c | [`stages/04_implement/04c_flow-tests/CONTEXT.md`](stages/04_implement/04c_flow-tests/CONTEXT.md) | [`login.feature`](stages/04_implement/04c_flow-tests/output/login.feature) | The outer-red flow test (Gherkin), now green in the Java reference profile. A historical native-track markdown spec is preserved at `output/login-flow-test.md`. |
| 04d (router) | [`stages/04_implement/04d_concept-tdd/CONTEXT.md`](stages/04_implement/04d_concept-tdd/CONTEXT.md) | (child stages own artefacts) | Structural boundary between concept test derivation and concept implementation. |
| 04d-red | [`stages/04_implement/04d_concept-tdd/04d_red-tests/CONTEXT.md`](stages/04_implement/04d_concept-tdd/04d_red-tests/CONTEXT.md) | concept test derivation artefact + per-concept test files | Derive and approve red concept tests from `04c` + `04b`; no implementation code. |
| 04d-green | [`stages/04_implement/04d_concept-tdd/04d_green-impl/CONTEXT.md`](stages/04_implement/04d_concept-tdd/04d_green-impl/CONTEXT.md) | per-concept Java + green concept tests | Implement only against the approved `04d-red` tests; no cross-concept imports (R1); every action emits a flow token (R5). |
| 04e (router) | [`stages/04_implement/04e_sync-tdd/CONTEXT.md`](stages/04_implement/04e_sync-tdd/CONTEXT.md) | (child stages own artefacts) | Structural boundary between sync test derivation and sync implementation. |
| 04e-red | [`stages/04_implement/04e_sync-tdd/04e_red-tests/CONTEXT.md`](stages/04_implement/04e_sync-tdd/04e_red-tests/CONTEXT.md) | sync test derivation artefact + per-sync test files | Derive and approve red sync tests from Stage 03 + `04c`; no implementation code. |
| 04e-green | [`stages/04_implement/04e_sync-tdd/04e_green-impl/CONTEXT.md`](stages/04_implement/04e_sync-tdd/04e_green-impl/CONTEXT.md) | per-sync Java + green sync tests + green flow tests | Implement only against the approved `04e-red` tests; when the last sync goes green, `04c`'s flow tests do too. |
| 05 | [`stages/05_verify/CONTEXT.md`](stages/05_verify/CONTEXT.md) | [`verification-trace.md`](stages/05_verify/output/verification-trace.md) (+ smoke / tracking when shipped) | Runtime-backed token-tree walk per scenario, checked by the Java reference profile tests and smoke evidence. |

## Cross-cutting reads

These don't live in any single stage's `output/` but are part of how
to navigate the feature:

- [`../../methodology/WALKTHROUGH.md`](../../methodology/WALKTHROUGH.md) — turn-by-turn replay of producing UC-00.
- [`../../methodology/architecture/ARTEFACT_MAP.md`](../../methodology/architecture/ARTEFACT_MAP.md) — diagram + per-artefact table mapping every artefact above to its consumers.
- [`../../methodology/architecture/MENTAL_MODEL.md`](../../methodology/architecture/MENTAL_MODEL.md) — OO ↔ WYSIWID intuition; useful before reading the concept specs.
- [`../../methodology/architecture/SYNC_PATTERNS.md`](../../methodology/architecture/SYNC_PATTERNS.md) — the four legal `where` patterns; needed for `WhenSessionGrantGrantedThenWebRespondForLogin`'s Pattern B `where:` clause and for reading the 03a cards.
- [`_config/voice.md`](_config/voice.md) — feature-scoped reference for the tone of the no-enumerating error message.
- [`../../reference-impl/java-micronaut-jena/`](../../reference-impl/java-micronaut-jena/) — minimal Java stubs honouring R1–R5 (ArchUnit-checked).

## Status

Spec-complete with a runnable Java reference profile. The Java profile
compiles and `mvn test` runs the ArchUnit suite, the OpenAPI docs tests,
and Cucumber scenarios end-to-end.
