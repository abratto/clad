# Artefact impact matrix — `rename-user-to-usernaming`

> Iterative change to the UC-00-login worked example. For each artefact
> category, mark touched/not-touched. Touched artefacts re-derive from their
> predecessor stage; do not edit late-stage artefacts in isolation.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `presentation`
- **Earliest re-entry stage:** `01a`
- **Status:** `closed`
- **Change summary:** Rename the `User` concept to `UserNaming` (purpose-oriented
  name per `CONCEPTS.md` §1); outcomes, state, action order, and the concept set
  are unchanged — only the concept qualifier (`User/…` → `UserNaming/…`) and its
  IRI/graph/table/class names change.

| Artefact | Touched? | How |
|---|---|---|
| Concept(s) | yes | `User.concept.md` → `UserNaming.concept.md`; `concept User` → `concept UserNaming`; action qualifiers re-derived |
| Sync(s) | yes | three `WhenUserLookupByUsername…` syncs renamed + `triggeredBy`/`then` re-derived to `UserNaming/lookupByUsername` |
| SPEC slices | yes | `User.spec.md` → `UserNaming.spec.md`; flow-token names re-derived |
| Flow tests | yes | `login-flow-test.md` concept references updated |
| Concept tests | yes | `UserLookupByUsernameTest` → `UserNamingLookupByUsernameTest` |
| Sync tests | yes | sync-test-derivation references updated |
| Production code | yes | `UserConcept` → `UserNamingConcept` (both profiles); `concept:user` → `concept:usernaming`; table `user_accounts` → `usernames` |

## Re-derivation order

1. 01a — responsibility map: rename concept `User` → `UserNaming`
2. 01b — chain tables: re-derive `UserNaming/lookupByUsername` qualifier
3. 02 — concept spec: rename file + header
4. 03 — syncs: re-derive trigger/fires names
5. 03a — dependency cards: rename `UserNaming-card.md`
6. 03b — data model: rename file + header
7. 04a — storage mapping: rename region/table
8. 04b — SPEC slices: rename file + header
9. 04c — flow tests: update references
10. 04d/04e — concept/sync tests: rename classes
11. 05 — verification trace: update references

## Notes

- Naming-only change: no outcome, state, action-order, or concept-set change.
  The individual `User` and its identity `UserId` are unchanged; only the
  concept's name (and its derived IRI/graph/table/class) changes.
