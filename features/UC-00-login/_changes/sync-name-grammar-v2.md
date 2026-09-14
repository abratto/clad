# Artefact impact matrix — `sync-name-grammar-v2`

> Iterative change to the UC-00-login worked example, mechanical only: the
> sync *name grammar* inverts from condition-first (`When…Then…`) to
> effect-first (`<Target>[For<Scope>]When<Trigger>…`) — see
> `maintenance/sync-dsl-legibility.md`. Triggers, targets, outcomes,
> literals, route filters, and observable action order are unchanged.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `presentation`
- **Earliest re-entry stage:** `03`
- **Status:** `closed`
- **Change summary:** Mechanical v1 → v2 name inversion across the seven
  UC-00 syncs and every derived artefact that cites them (03a cards,
  pattern-d-summary, 04e derivation/green evidence, Stage 05 trace,
  worked-example README). No sync content changes; Java records migrated
  in the same batch (see the maintenance record's impact matrix).

| Artefact | Touched? | How |
|---|---|---|
| Use case | no (cites unchanged; sync names are not modelled) |
| Concept(s) | no |
| Sync(s) | yes | file stems + `sync <Name>` headers + Willy body unchanged otherwise |
| SPEC slices | no | SPEC names are concept actions (unchanged) |
| Flow tests | no |
| Concept tests | no |
| Sync tests | yes | derivation-map sync names re-derived |
| Production code | no (java-legible code migrated in the same maintenance record) |
| Verification trace | yes | trace/`causedBySync` names mechanically renamed |

## Re-derivation order

1. `03` sync outputs — 7 file renames + `sync <Name>` headers
2. `03a` dependency cards + pattern-d-summary — mechanical rename
3. `04e` sync test derivation + green `_IMPL` — mechanical rename
4. Stage 05 verification-trace — mechanical rename
5. Worked-example README — deviation-note pointer to this record

## Notes

- Gate 2 (Architecture, 01→03b) must be re-presented and re-approved after
  the mechanical rename: approval hashes are bound to stage content, and
  the 03 outputs changed. `verify_stage_sequence` gates re-approval until
  then (see current `RESUME.md`).
- The concept/action token vocabulary is unchanged; only the grammar order
  flipped. No sync spec content was rewritten.
