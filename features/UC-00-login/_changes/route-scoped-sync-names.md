# Artefact impact matrix — `route-scoped-sync-names`

> Iterative change to UC-00-login, **name only**: a route-scoped bootstrap sync
> carries its route (`VerifyForReturnsWhenRequestRouted`). No outcome, route,
> status, body or ordering changes — `maintenance/route-scoped-sync-names.md`.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `presentation`
- **Earliest re-entry stage:** `01b`
- **Status:** `active`
- **Change summary:** the bootstrap sync is renamed (the chain's notes name it, hence the 01b re-entry) and its spec gains the route
  matcher; references follow (card, derivation map, chain note, Java rule name,
  test class and its file).

| Artefact | Touched? | How |
|---|---|---|
| Use case | no | — |
| Concept(s) | no | — |
| Sync(s) | yes | `LookupByUsernameWhenRequestRouted` → `LookupByUsernameForLoginWhenRequestRouted`, route matcher added |
| Data model | no | — |
| Contract slices | no | — |
| Flow tests | no | — |
| Concept tests | no | — |
| Sync tests | yes | test class and file renamed; continuity hash refreshed |
| Production code | yes | `LibrarySyncs` rule name (same rule, same matcher) |
| Verification trace | no | — |

## Re-derivation order

1. `01b` — the chain's notes name the renamed sync.
2. `03` — rename the spec and add the route matcher.
3. Re-present and re-approve **Gate 1** (01–01b) and **Gate 2** (02–03b).
3. Downstream references follow mechanically.

## Notes

- Behaviour is preserved: the rule fires on the same route with the same `then`.
  The gate re-approval exists because a gated stage's output changed.
