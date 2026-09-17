# Artefact impact matrix — `sync-name-grammar-v3`

> Iterative change to the UC-00-login worked example, mechanical only: the
> sync *name grammar* moves from v2 (effect-first, concept-full) to v3
> (action-first, concept-free) — see `maintenance/sync-name-grammar-v3.md`.
> Triggers, targets, outcomes, literals, route filters, and observable action
> order are unchanged; no sync rule body was rewritten.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change category:** `presentation`
- **Earliest re-entry stage:** `01b`
- **Status:** `closed`
- **Change summary:** the seven UC-00 syncs are renamed and every derived
  artefact that cites them is mechanically updated: the two chain-table
  citations, the four 03a cards, `pattern-d-summary.md`, the 04e derivation and
  `_IMPL`, the 04c `.feature` comments, the worked-example README, and the
  sync names declared in the `java-legible`, `java-plain`, and
  `java-micronaut-postgres` implementations.

| Artefact | Touched? | How |
|---|---|---|
| Use case | yes (names only) | `usecase.md` cites sync names in its notes |
| Concept(s) | no | — |
| Sync(s) | yes | seven file renames + `sync <Name>` headers; rule bodies unchanged |
| SPEC slices | no | SPEC names are concept actions (unchanged) |
| Flow tests | yes | `login.feature` comments cite the sync files |
| Concept tests | no | — |
| Sync tests | yes | 04e derivation / `_IMPL` sync names |
| Production code | yes | `LoginSyncs.java` (java-legible), `java-plain` `LoginSyncs.java`, `java-micronaut-postgres` sync classes + rules, `Dsl.java` doc reference |
| Verification trace | no | Stage 05 trace does not cite sync names |
| Stage 01b chain tables | yes | `lockout-chain.md`, `login-all-scenarios-chain.md` cite sync names |

## Re-derivation order

1. `03` sync outputs — seven renames + `sync <Name>` headers.
2. `01b` chain tables — mechanical name update in the two citation lists.
3. `03a` cards + `pattern-d-summary.md` — mechanical rename of audited syncs.
4. `04c` `.feature` comments, `04e` derivation + `_IMPL` — mechanical rename.
5. Implementation — `java-legible`, `java-plain`, `java-micronaut-postgres`.
6. Re-present and re-approve **Gate 1** (01b), **Gate 2** (03/03a), **Gate 3**
   (04c).

## Notes

- Gate approvals are content-hash bound: 01b is in Gate 1's block, 03/03a in
  Gate 2's, 04c in Gate 3's, so all three must be re-approved.
- The concept/action/outcome vocabulary is unchanged; only the name grammar
  moved. No rule body, `where` binding, or response literal was rewritten.
- Supersedes the naming introduced by `sync-name-grammar-v2`.
- Do not hand-edit the RESUME `## Gate snapshot` hashes — `approve_gate.py`
  owns them.
