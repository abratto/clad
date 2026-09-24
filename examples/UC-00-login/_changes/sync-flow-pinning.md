# Artefact impact matrix — `sync-flow-pinning`

> Iterative change to UC-00-login, **behavioural (narrowing)**: every
> non-bootstrap sync gains its flow root as its LAST `when` conjunct, with the
> route matcher, so it can only fire in its own flow. Same rules, same routes,
> same outcomes — a rule can only fire *less*.
> See `maintenance/sync-flow-pinning.md`.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `behavioural`
- **Earliest re-entry stage:** `03`
- **Status:** `closed`
- **Change summary:** each non-bootstrap sync spec's `when` block and contract
  matrix gain the pinned flow root; the Java rule gains the matching conjunct.

| Artefact | Touched? | How |
|---|---|---|
| Use case | no | — |
| Concept(s) | no | — |
| Sync(s) | yes | the flow pin added to every non-bootstrap rule |
| Data model | no | — |
| Contract slices | no | — |
| Flow tests | no | — |
| Concept tests | no | — |
| Sync tests | no | behaviour narrows to the rule's own flow |
| Production code | yes | the pinned conjunct on each `SyncRule` |
| Verification trace | no | — |

## Re-derivation order

1. `03` — pin the specs.
2. Re-present and re-approve **Gate 2** (02–03b is its block).
3. The Java follows the spec (parity), and the features' downstream stages re-run.

## Notes

- The change makes two use cases that share a completion stop firing each
  other's rules. That is a *narrowing*, which is why the category is behavioural
  rather than presentation: a rule that used to fire now does not.
