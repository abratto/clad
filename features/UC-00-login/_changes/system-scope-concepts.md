# Artefact impact matrix — `system-scope-concepts`

> Iterative change to the UC-00-login worked example: concepts become
> system-scope, reusable assets (maintenance change
> `system-scope-concept-vocabulary`, rule R22). The three concept specs move to
> the canonical corpus and UC-00 gains a `concept-bindings.md`; the concept
> *set*, all syncs, SPECs, tests, and runtime behaviour are unchanged. This is
> the worked example's migration to Model B so it teaches the current model.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `structural`
- **Earliest re-entry stage:** `01a`
- **Status:** `closed`
- **Change summary:** UC-00 introduced `UserNaming`, `PasswordAuth`, and
  `Session`; under Model B it records them as `Origin: new` proposals that are
  promoted into `features/_system/concepts/` (provenance "introduced by
  UC-00-login"), and emits `02_concepts/output/concept-bindings.md` alongside
  the proposals. Every reference to the per-UC concept location is re-pointed
  at the corpus (shadowed by the feature's own proposals).

| Artefact | Touched? | How |
|---|---|---|
| Use case | no | scenarios unchanged |
| Concept(s) | yes | three specs gain `introduced-by UC-00-login`; promoted copies live in `features/_system/concepts/` |
| Sync(s) | no | sync content unchanged |
| SPEC slices | no | still one per concept |
| Flow tests | no | |
| Concept tests | no | |
| Sync tests | no | |
| Production code | no | `reference-impl/java-legible` unchanged |
| Stage 01a map | yes | gains the `Origin` column (all `new`) and a *Proposals* section |
| Stage 02 output | yes | new `concept-bindings.md`; concept dir references re-pointed |
| Downstream stage contracts | yes | 03 / 03a / 03b / 04 / 04b / 04d Inputs resolve the corpus (via `CONCEPT_DIR` union) |
| Verification trace | no | Stage 05 outcomes unchanged |

## Re-derivation order

1. `01a` — add the `Origin` column (`new` for `UserNaming`, `PasswordAuth`,
   `Session`, `Web`) and the *Proposals* section.
2. `02` — add `concept-bindings.md`; add `introduced-by UC-00-login` to the
   three proposals; re-point the stage contract's concept references at the
   corpus + proposals.
3. `03` / `03a` / `03b` / `04` / `04b` / `04d` — re-point the stage contracts'
   concept Inputs. Outputs are unchanged, so no downstream stage output is
   re-derived.
4. Re-present and re-approve **Gate 1** (01a) and **Gate 2** (02).

## Notes

- Gate approvals are content-hash bound (`verify_stage_sequence.py`): the 01a
  and 02 outputs change, so Gate 1 and Gate 2 must be re-approved. Gate 3
  (04a–04c) is unaffected — no stage in its block changes.
- The corpus was seeded from these very specs (`maintenance/
  system-scope-concept-vocabulary.md`, Phase 1); promotion is therefore already
  reflected, and re-running `./clad promote-concepts` is a no-op.
- No behavioural change: the same state, actions, outcomes, and syncs. This is
  a location/ownership migration only.
- Do not hand-edit the RESUME `## Gate snapshot` hashes —
  `approve_gate.py` owns them.
