# Concepts catalog — `<project name>`

> Project-level catalog of every concept used across features. Useful
> once you have **three or more** features. Below that, the per-
> feature responsibility maps in `02a_responsibility-map/output/` are
> sufficient and a project-level catalog is overhead.

## How to use this catalog

- Add one row per concept the *first time* a feature uses it.
- The owning feature column points at the feature where the concept
  was introduced — this is its canonical home, where the
  `<Name>.concept.md` lives.
- Subsequent features that reuse a concept add their UC-id to the
  *Used by* column rather than redefining the concept.
- If two features try to define the same concept differently, that
  is a structural conflict — resolve it before either feature merges
  by re-running Stage 02a on whichever feature is younger.

## Catalog

| Concept | One-line capability | Owning feature | Used by | Notes |
|---|---|---|---|---|
| `User` | Identify a person to the system | UC-00-login | UC-00-login | Username uniqueness |
| `PasswordAuth` | Verify a password against a stored credential | UC-00-login | UC-00-login | Includes lockout outcome |
| `Session` | Issue and look up authenticated sessions | UC-00-login | UC-00-login | TTL fixed at issue time |
| `Web` | HTTP entry point (bootstrap) | UC-00-login | (every feature) | See `methodology/architecture/WEB_CONCEPT.md` |
| ... | ... | ... | ... | ... |

## Cross-feature rules

- **R1 still holds.** The catalog does **not** authorise one
  concept to import another. If two features need to coordinate via
  a shared concept, they coordinate through syncs, the same as ever.
- **One owning feature per concept.** If you are about to add a
  concept whose owning feature is unclear, that is a sign the
  feature boundaries are wrong — surface it to the human before
  proceeding.
- **Splitting and merging.** Splitting one catalog row into two, or
  merging two rows, is a structural change in every feature that
  used the affected concepts. Re-enter Stage 02a in each.

## Out of scope for the catalog

- Concept *anatomy* (state, actions, outcomes) — that lives in the
  owning feature's `02_concepts/output/<Name>.concept.md`.
- Concept *dependencies* — there are none (R1).
- Concept *implementation paths* — they live under
  `reference-impl/<profile>/`.
