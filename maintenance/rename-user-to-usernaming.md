# Maintenance change — `rename-user-to-usernaming`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `mixed`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/java-micronaut-jena`, `reference-impl/java-micronaut-postgres`, and the `features/UC-00-login` worked example
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Rename the `User` concept to `UserNaming` (and its IRI, named graph, Java class, and Postgres table) so the exemplar follows CLAD's purpose-oriented naming guidance — a concept names the capability, not the entity.

## Why

`features/UC-00-login/stages/02_concepts/output/User.concept.md` declares
`concept User [UserId]` with purpose "associate usernames with opaque user
identifiers" — that is the *naming* capability. Naming the concept `User`
conflates the capability with the entity, the exact trap Daniel Jackson
describes in *Why concepts aren't objects* (`Post` rather than `Posting`).
`CONCEPTS.md` §1 now requires a purpose-oriented name; this change brings the
exemplar into line.

The mapping is unchanged: the individual identity (`UserId`) stays the RDF
subject / relational key; the concept's region is renamed for its purpose
(`concept:usernaming`, table `usernames`).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | preserved | Same outcomes (`REGISTERED`, `FOUND`, `refused`); only the concept qualifier changes |
| Action ordering and sync deduplication | preserved | Same chains; sync names re-derive mechanically from the renamed trigger |
| Flow-token lineage | preserved | Flow tokens still span the chain; `:concept` IRI changes to `…/usernaming` |
| Storage/retention semantics | preserved | Same relations; graph renamed `concept:usernaming`, table `user_accounts` → `usernames` |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `CANONICAL_EXEMPLAR.md`, `SYNC_LOWERING.md`, `README.md`, `CODE_STYLE.md`, `RELATIONAL_LOWERING.md` |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `UserConcept` → `UserNamingConcept` (both profiles); sync classes re-derive |
| Profile tests | yes | `UserLookupByUsernameTest` → `UserNamingLookupByUsernameTest` (both profiles) |
| UC artefact chain | yes | `01a` responsibility map, `01b` chain tables, `02` concept spec, `03` syncs, `03a` cards, `03b` data model, `04a` storage, `04b` spec, `05` trace — all rename the concept reference; no outcome/state/order change |

## Design

- **Concept name:** `User` → `UserNaming` (purpose-oriented; the individual is
  `User`, its identity `UserId`, both unchanged).
- **IRI:** `https://clad.dev/concept/user` → `https://clad.dev/concept/usernaming`.
- **Named graph (Jena):** `concept:user` → `concept:usernaming`.
- **Table (Postgres):** `user_accounts` → `usernames` (relation-named, not
  entity-named).
- **Java:** package `concepts.user` → `concepts.usernaming`, class
  `UserConcept` → `UserNamingConcept`; sync class names and
  `@SyncMetadata.triggeredBy` re-derive from the renamed trigger
  (`User/lookupByUsername` → `UserNaming/lookupByUsername`).

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Rename preserves behaviour | unit | concept/flow/ArchUnit tests in both profiles | pass | 91 tests 0 failures (3 modules) |
| No residual `concept:user` / `UserConcept` / `user_accounts` | unit | `grep -r` across src + features | pass | 0 matches |
| Full regression | integration | `python3 quality-gate/verify_artefacts.py && mvn test -f reference-impl/pom.xml` | pass | 91 tests 0 failures |

## Gates

### Design gate

Approve with `./clad approve-maintenance rename-user-to-usernaming design`, then set Status to `active`.

### Evidence gate

Approve with `./clad approve-maintenance rename-user-to-usernaming evidence` after the test matrix is green.

## Notes

- **Non-goals:** no change to `PasswordAuth`/`Session` names (already
  purpose-oriented enough); no change to actions, outcomes, state, or the
  dispatch loop.
- The rename is a naming change only — a mechanical re-derivation of the
  artefact chain, not a re-design.
