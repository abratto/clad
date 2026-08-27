# Maintenance change — `r13-serialization-and-auth-concurrency`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `active`
- **Affected profile(s):** `reference-impl/java-micronaut-jena` (R13), `reference-impl/java-micronaut-postgres` (auth concurrency)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Fix two contract-preserving loose ends — R13 null-serialization enforcement (a wrong package left the Jena `ObjectMapperCustomizer` undiscovered) and the PasswordAuth failed-attempt read-modify-write race (make it atomic in Postgres).

## Why

1. `reference-impl/java-micronaut-jena/.../infrastructure/ObjectMapperCustomizer.java`
   declares `package org.clad.conduit.infrastructure;` (a Conduit leftover), so
   Micronaut never discovers the bean and R13 ("Jackson must serialize null
   values") is silently not enforced in the Jena profile. Fixing the package to
   `com.example.app.infrastructure` activates it.
2. `PasswordAuthConcept.doCheck` (Postgres) does read → compute → write without
   a lock, so two concurrent checks for one user can lose a failed-attempt
   increment. It is currently masked by the single-writer dispatch loop, but the
   relational profile should not depend on that; the increment must be atomic.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Same `OK/BAD_PASSWORD/NO_CREDENTIAL/LOCKED`; same `Web/respond` bodies |
| Action ordering and sync deduplication | preserved | Syncs and the dispatch loop untouched |
| Flow-token lineage | preserved | Unchanged |
| Storage/retention semantics | preserved | Same tables; only the access pattern of `doCheck` changes |
| R13 null serialization (Jena) | changed (fixed) | The bean was never active; it now is. This is the intended behaviour — no domain re-entry |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `CODE_STYLE.md` (Postgres) note that `doCheck` is atomic |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `PasswordAuthConcept.doCheck` (Postgres) → `dsl.transaction` + `SELECT … FOR UPDATE`; `ObjectMapperCustomizer` package (Jena) |
| Profile tests | yes | strengthen `CladRulesComplianceTest.jacksonSerializesNullValues` to require `ALWAYS`; `PasswordAuthCheckTest` unchanged (behaviour oracle) |
| UC artefact chain | no | Concept spec (state/actions/outcomes) unchanged |

## Design

- **R13 (Jena):** change `ObjectMapperCustomizer` package to
  `com.example.app.infrastructure`; strengthen the R13 test to assert
  `JsonInclude.Include.ALWAYS` (not the lenient `ALWAYS || NON_EMPTY`).
- **Auth concurrency (Postgres):** wrap `doCheck`'s read-compute-write in
  `dsl.transactionResult(...)` with a `SELECT … FOR UPDATE` row lock on
  `passwordauth_credentials`, so the failed-attempt increment and lockout
  threshold are applied atomically. `writeCompletion` stays outside the
  transaction (the action log is a separate store).

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| R13 null serialization enforced (Jena) | unit | `CladRulesComplianceTest.jacksonSerializesNullValues` (assert `ALWAYS`) | pass | 2/2 green |
| Auth behaviour unchanged (Postgres) | unit/integration | `PasswordAuthCheckTest` (3, incl. 5-failure lockout) + `LoginFlowTest` (2) | pass | 5/5 green |
| Full regression | integration | `python3 quality-gate/verify_artefacts.py && mvn test -f reference-impl/pom.xml` | pass | 91 tests 0 failures (3 modules) |

## Gates

### Design gate

The human reviews contract impact, non-goals, and the test matrix before any
implementation. Approve with `./clad approve-maintenance r13-serialization-and-auth-concurrency design`,
then set Status to `active`.

### Evidence gate

The human reviews the completed test matrix and runtime evidence before commit.
After approval, set Status to `closed` and commit the record with the change.

## Notes

- **Non-goals:** no change to concept/sync specs, outcomes, response bodies, or
  the dispatch loop. The concurrency fix is defensive — the single-writer
  dispatch lock already serializes concept processing; this removes the latent
  hazard for a future parallel dispatcher.
- **Jena `PasswordAuth` is unchanged** — its read-modify-write is already
  protected by the single-writer dispatch lock and TxnMem transaction semantics;
  the relational fix targets the profile where parallel execution is plausible.
