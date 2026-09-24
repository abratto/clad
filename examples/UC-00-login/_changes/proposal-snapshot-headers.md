# Artefact impact matrix — `proposal-snapshot-headers`

> Iterative change to UC-00-login, **presentation only**: the Stage 03b model
> and Stage 04b contract artefacts are re-headed so a feature copy cannot be
> mistaken for the canonical corpus entry. Nothing below the header changes.
> See `maintenance/concept-provenance-and-additivity.md`.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `presentation`
- **Earliest re-entry stage:** `03b`
- **Status:** `closed`
- **Change summary:** each model/contract artefact gains
  `<!-- proposal snapshot — …; canonical <kind>: features/_system/concepts/<Name>.<kind> -->`
  in place of its old generator comment.

| Artefact | Touched? | How |
|---|---|---|
| Use case | no | — |
| Concept(s) | no | — |
| Sync(s) | no | — |
| Data model | yes | leading comment only (3 artefacts) |
| Contract slices | yes | leading comment only (3 artefacts) |
| Flow tests | no | — |
| Concept tests | no | — |
| Sync tests | no | — |
| Production code | no | — |
| Verification trace | no | — |

## Re-derivation order

1. `03b` — three models re-headed.
2. `04b` — three contracts re-headed.
3. Re-present and re-approve **Gate 2** (02–03b) and **Gate 3** (04a–04c):
   both blocks' outputs changed.

## Notes

- Gate approval is content-hash bound, so both gates must be re-approved.
- Do not hand-edit the RESUME `## Gate snapshot` hashes — `approve_gate.py`
  owns them.
