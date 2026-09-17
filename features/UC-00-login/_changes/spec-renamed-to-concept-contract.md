# Artefact impact matrix — `spec-renamed-to-concept-contract`

> Iterative change to UC-00-login, **presentation only**: the Stage 04b artefact
> is renamed from SPEC to the **concept contract**
> (`<Name>.spec.md` → `<Name>.contract.md`, folder `04b_spec/` →
> `04b_contract/`). See `maintenance/spec-renamed-to-concept-contract.md`.
> No action, outcome, sync, or flow token changes.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `presentation`
- **Earliest re-entry stage:** `04b`
- **Status:** `closed`
- **Change summary:** the three contract artefacts and the stage folder are
  renamed; nothing inside them changes.

| Artefact | Touched? | How |
|---|---|---|
| Use case | no | — |
| Concept(s) | no | — |
| Sync(s) | no | — |
| Contract slices | yes | folder renamed; 3 artefacts renamed |
| Flow tests | no | their references to `04b_contract/` are in the contract, not the artefact |
| Concept tests | no | — |
| Sync tests | no | — |
| Production code | no | — |
| Verification trace | no | — |

## Re-derivation order

1. `04b` — folder renamed, three artefacts renamed.
2. Re-present and re-approve **Gate 3** (04a–04c is its block).

## Notes

- Gate approval is content-hash bound: 04b's `output/` changed, so Gate 3 must
  be re-approved. Gates 1 and 2 are unaffected.
- Do not hand-edit the RESUME `## Gate snapshot` hashes — `approve_gate.py`
  owns them.
