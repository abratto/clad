# Maintenance change — `concept-remodel-class`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (gate + promotion + templates + R22)
- **Feature-contract impact:** `additive` (new Origin value `remodel:UC-XX`;
  `bind`/`extends`/`new` semantics unchanged)
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** R22 gains a fourth proposal class — `remodel` — the
  deliberate, reviewable path for a non-additive change to a canonical
  concept, gated by migration notes and historical consent.

## Why

R22 gave a use case three moves: `bind`, `extends` (additive), `new`.
Anything else — retiring a fact type, correcting a value type, restating an
action's outcomes — had to route through the R20 maintenance route, which is
deliberately heavyweight (a maintenance record, design gate, evidence gate).
That made the FIRST definer's cut effectively frozen: the introducing use
case's mistakes could be carried indefinitely because fixing them was
disproportionately expensive. First-proposer bias is the observed cost; the
`concept-provenance-and-additivity` change record shows how much machinery
the alternative required just to make replacement visible.

## Rule (R22 amendment)

- A responsibility-map row may carry `Origin: remodel:UC-XX` — a
  deliberately NON-additive proposal against an existing canonical concept.
  Stage 02 authors it as a full proposal snapshot carrying a
  `## Migration notes` section: one bullet per dropped or restated
  canonical line (state lines and contract terms), exact line backticked,
  with reason and consumer impact.
- `verify_concept_additivity.py` waives the additive-only failure for a
  remodel ONLY for noted lines; an unnoted drop fails. Consent receipts and
  migration notes never rescue an `extends` row.
- `promote-concepts` refuses a remodel unless every feature on the
  concept's canonical history (`introduced-by` / `extended-by`, minus the
  proposer) has a consent receipt at
  `features/_system/concepts/_remodel-consent/<Concept>-<feature>.md`.
- Provenance, order, and corpus-currency rules apply unchanged: only the
  concept's current source may promote, and the promotion is recorded in
  the append-only history.

## Mechanism

- `quality-gate/concept_remodel.py` — shared mechanics: migration-note
  extraction, canonical-history reading, consent-receipt resolution, and
  unauthorised-drop computation (reusing
  `verify_concept_additivity.dropped_state_lines` /
  `dropped_contract_terms`, so a remodel and an extend compute "dropped"
  identically).
- `verify_concept_additivity.py` — remodel branch (notes + consent).
- `promote_concepts.py` — remodel proposals are promotable; per-concept
  refusal when notes or consent are incomplete.
- Origin vocabulary extended in `verify_concept_proposals.py`,
  `artifact_parsers.py` (`feature_model_concepts`,
  `feature_contract_concepts`, `expected_stage_outputs`),
  `verify_concept_registry.py`, `verify_concept_corpus_current.py`.
- Templates (`concept.md`, `responsibility-map.md`), RULES.md R22, and
  CONCEPTS.md updated.

## Evidence

- `quality-gate/tests/test_concept_remodel.py` — remodel with notes +
  consent passes the additivity gate and promotes; missing notes fail
  naming the dropped line; missing consent fails naming the historical
  feature; an `extends` carrying a consent receipt still fails additivity
  (consent is remodel-only); promotion refuses without consent and names
  the missing receipt.
- Full `quality-gate/tests` suite green; `verify_artefacts.py` intact.
