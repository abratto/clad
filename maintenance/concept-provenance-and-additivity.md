# Maintenance change — `concept-provenance-and-additivity`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (gate + generators + promotion + templates + docs)
- **Feature-contract impact:** `re-entered`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** a canonical concept's artefacts say that they are canonical and name their promotion history; a feature's copies say that they are proposal snapshots; promotion cannot move a concept backwards; and an extend may add to a concept but not quietly subtract from it.

## Why

A concept is written whole, so every promotion replaces the canonical entry. That
made three things invisible:

1. **Which copy is authoritative.** A feature that introduces or extends a
   concept keeps a copy under its own `stages/` (`02_concepts/`,
   `03b_data-model/`, `04_implement/04b_contract/`), and the corpus holds
   another. The two were byte-identical and carried the same generator comment,
   so nothing on either file said which one a reader should believe.
2. **Order.** Promotion is a replacement, so re-promoting an OLDER feature over
   a NEWER canonical entry silently rolls the corpus back. That is not
   hypothetical: `./clad promote-concepts` defaulted to a guessed active
   feature, targeted one whose RESUME still said `Stage 04c`, and replaced the
   canonical `MemberEnrolment` spec with a superseded proposal — dropping the
   `verify` action UC-03 had added.
3. **Additivity.** "An extend is additive" was a social convention.
   `feature_model_concepts` decides whether a feature derives a model with a
   *difference* test (`proposal.state_lines != canonical.state_lines`), so a
   proposal that REMOVES a state line is indistinguishable from one that adds
   one, and promotion copies either over the canonical entry.

## Rule

- **Provenance.** The canonical spec carries `introduced-by <UC>` plus
  `extended-by <UC>, …` — append-only, in promotion order. The canonical data
  model and contract carry
  `<!-- canonical — derived from concept <Name>: introduced-by <UC>, current
  source <UC> -->`. A feature's model and contract carry
  `<!-- proposal snapshot — …; canonical <kind>: features/_system/concepts/<Name>… -->`.
- **Order.** Only the concept's current source may promote it. Anyone already in
  the history who is not last is refused (per concept, with a warning — a
  feature may legitimately own some concepts and trail on others). Promotion no
  longer guesses its feature: `./clad promote-concepts <feature>` requires the
  feature, because it WRITES the corpus.
- **Additivity.** An `extends:*` proposal must keep every canonical `## State`
  line and every canonical contract action and outcome. A deliberate removal is
  authorised by listing the exact dropped line in the feature's
  `_config/additivity-exceptions.md` with a reason.
- **Currency.** Every feature whose Gate 2 is approved appears on the canonical
  history of every concept it proposed, with a `_promotions/<slug>.md` receipt;
  the canonical companions name the same current source as the spec.

## Mechanism

`promote_concepts.stamp_provenance` appends the promoter to the canonical
history and refuses a feature already on it
(`quality-gate/promote_concepts.py#stamp_provenance`).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | No action, outcome, or sync changes; provenance is metadata |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | no | — |
| Gate scripts | yes | new `verify_concept_additivity.py`, `verify_concept_corpus_current.py`; `promote_concepts.py` (history, canonical headers, per-concept roll-back refusal, re-stamp); `generate_data_model.py` / `generate_contract.py` (snapshot headers); `clad_stages.py` (wire additivity to 03b + 04b); `verify_artefacts.py` (wire the currency check project-level) |
| Gate tests | yes | `test_concept_additivity.py`, `test_concept_corpus_current.py`, promotion tests |
| Templates | yes | 03b and 04b stage contracts name the new check; `clad` requires the feature for `promote-concepts` |
| Methodology docs | yes | `CONCEPTS.md` (snapshot vs canonical, additivity, order), `RULES.md` (R22), `CONTEXT_MANIFEST.md` |
| Corpus | yes | history lines, canonical headers, receipts, `_config/additivity-exceptions.md` convention |
| Feature artefacts | yes | model + contract headers re-headed (UC-00 in both repos, UC-01/02/03 in the experiment) — Gate 2 and Gate 3 re-approved per feature |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| An extend may add state but not drop it | unit | `test_concept_additivity.py` | pass | — |
| A dropped or restated contract outcome fails | unit | `test_concept_additivity.py::…test_dropped_contract_outcome_fails` | pass | — |
| A bounded, authorised removal passes | unit | `…test_authorised_exception_passes` | pass | — |
| Promotion records the promoter and refuses to roll back | unit | `test_concept_registry.py::PromotionTests::test_second_promoter_is_appended_and_out_of_order_is_refused` | pass | — |
| The current promoter's re-run is a no-op | unit | `…test_re_promoting_the_current_promoter_is_idempotent` | pass | — |
| A companion gains the canonical header, not a copy of the snapshot | unit | `…test_promotion_carries_the_conceptual_data_model` | pass | — |
| An approved proposal missing from the history fails | unit | `test_concept_corpus_current.py::…test_approved_proposal_missing_from_history_fails` | pass | — |
| A stale companion header fails | unit | `…test_companion_naming_a_stale_promoter_fails` | pass | — |
| In-flight features are skipped | unit | `…test_in_flight_feature_is_skipped` | pass | — |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | 168 passed |
| Corpus current in both repos | integration | `verify_concept_corpus_current.py` | pass | clad 3 concepts; experiment 4 concepts / 3 features |
| Pipelines intact | integration | `verify_artefacts.py` in clad and the experiment | pass | — |
| Experiment app green | integration | `mvn -q test -f app/pom.xml` | pass | exit 0 |

## Gates

### Design gate

Approved in-conversation: the two-file model stays (a proposal snapshot is the
Gate 2 audit trail), but it must be labelled, ordered, and additive — covering
both the data model and the contract.

### Evidence gate

To be recorded before commit.

## Notes

- The wrong-invariant trap is written into both new scripts: file-equality
  across the copies is NOT the invariant (from the second extending use case
  onward an earlier snapshot is *supposed* to differ). The invariant is
  ordering, which the canonical entry now records itself.
- `UC-00-*` is skipped as the reserved worked example — in a derived repository
  its concepts belong to the seed's corpus, not to that app's — and the
  bootstrap concept `Web` is skipped because it is not a corpus concept.
- **Follow-up (post-0.8.0):** the *concept* proposal now carries a
  `<!-- proposal snapshot — … -->` header at authoring time
  (`templates/concept.md`), so a hand-authored proposal is labelled like the
  generated model and contract. `verify_concept_proposals.py` requires it while
  Gate 2 is open (approved features are grandfathered), and
  `promote_concepts.canonical_spec` drops it so the canonical spec never claims
  to be a proposal.
