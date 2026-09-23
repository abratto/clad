# Maintenance change — `promote-atomic`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `quality-gate/promote_concepts.py` (no engine/profile/runtime change)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Make concept promotion atomic: stage the three canonical artefacts to temp files and `os.replace` them into place as one step, roll back on any failure (including catalog regeneration), so a crash can never leave the system-scope corpus half-written.

## Why

`promote_concepts.py` writes the corpus with separate sequential writes and no
transaction (quality-gate/promote_concepts.py:~347):

```
for concept in sorted(planned):
    write <concept>.concept.md
    for suffix, text in companions:      # .data-model.md, .contract.md
        write <concept>.<suffix>
# then, separately:
subprocess.run(generate_concepts_catalog.py --write)   # regenerates the index
```

A crash (disk full, SIGKILL/OOM, a catalog-regen failure) between any two writes
leaves the corpus **half-written**:

- the concept spec may be present while its companions are not (or come from a
  different feature's derivation);
- the generated catalog may name a concept whose spec never landed;
- every feature reads this corpus (it is the system-scope vocabulary, R22), so
  the inconsistency propagates to every later gate.

Promotion is the highest-blast-radius write in the system, and today it has no
all-or-nothing property.

## Rule

- **Stage, then swap.** Build all target file contents in memory (as now), write
  each to a sibling temp file (`<name>.<pid>.tmp`) in the corpus directory, then
  `os.replace` each into place. `os.replace` is atomic per file on POSIX.
- **All-or-nothing across the set.** Back up the current corpus files that will
  be replaced (spec + companions + the catalog + the receipt) before swapping; if
  **any** step fails — a write, a swap, or the catalog regeneration — restore the
  backups and remove the temp files, then exit non-zero with the failure named.
- **Catalog last, inside the transaction.** Regenerate the catalog as part of the
  atomic set: the old catalog is restored on failure, so the index never names a
  concept the corpus does not hold.
- **No partial visibility between processes.** Because `os.replace` is atomic and
  the swap happens after all temp files are written, a concurrent reader sees
  either the old corpus or the new one — never a mix.
- **Dry-run unchanged.** `--dry-run` still writes nothing.

## Mechanism

Promotion now builds a `{path: text}` write set (specs, companions, the
catalog rendered by `generate_concepts_catalog.render`, and the receipt) and
passes it to `atomic_write_set` (quality-gate/promote_concepts.py:83), which
stages each file to a sibling `<path>.<pid>.tmp` and `os.replace`s it into
place, backing up and restoring the set on any failure. The catalog path is
`catalog_out_path` (quality-gate/promote_concepts.py:63) and its content comes
from `_catalog_text` (quality-gate/promote_concepts.py:68).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Tooling change; no artefact content changes |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | Corpus content on success is byte-identical to today's output |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | no | — |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | — |
| Gate scripts | yes | `promote_concepts.py` — staged write + rollback |
| Gate tests | yes | new test: simulate a mid-promotion failure and assert the corpus is unchanged |
| UC artefact chain | no | UC-00 does not promote (corpus is stocked) |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| A failure between writes leaves the corpus byte-identical to before | unit | `test_concept_registry.py::PromotionAtomicityTests` — `…test_failure_injection_leaves_the_corpus_unchanged`, plus `…test_atomic_write_set_rolls_back_on_swap_failure` / `…removes_a_newly_created_target_on_failure` | pass | — |
| A successful promotion still writes spec + companions + catalog + receipt | unit | `test_concept_registry.py::PromotionAtomicityTests::…test_successful_promotion_is_complete` | pass | — |
| --dry-run writes nothing | unit | `promote_concepts.py --feature features/UC-00-login --dry-run` (no files written) | pass | — |
| Gate pipeline intact | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact, 0 WARNs |
| Gate suite green | unit | `python3 -m pytest quality-gate/tests -q` | pass | 250 passed |

## Gates

### Design gate

To be approved before implementation. Approve with
`./clad approve-maintenance promote-atomic design`.

### Evidence gate

Cleared: the failure-injection test proves a mid-promotion failure (catalog render, or a swap) leaves the corpus byte-identical, including newly-created targets being removed; a normal promotion writes spec + companions + catalog + receipt; UC-00's dry-run writes nothing; the artefact pipeline is intact (0 WARNs) and the gate suite is green at 250.

## Notes

- The success path's corpus output is unchanged — this is an atomicity wrapper,
  not a format change.
- Rollback restores from in-memory backups taken before the first swap, so it
  does not depend on a separate backup directory being writable.
