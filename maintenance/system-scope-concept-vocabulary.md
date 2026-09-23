# Maintenance change — `system-scope-concept-vocabulary`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (methodology + gate + templates + a new system-scope artefact tree)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Make the concept a first-class, system-scope, reusable asset — one canonical corpus at `features/_system/concepts/<Name>.concept.md`, a generated catalog, a reviewed app-level dependence graph, and a criteria gate — with use cases composing concepts (REUSE / EXTEND / NEW) instead of re-deriving them per feature.

## Why (experiment-found)

The 13-use-case Conduit rebuild re-derived the **same** concept in every use case and it drifted: `Session.concept.md` appeared in 6 UC folders with 6 different hashes, `User.concept.md` 5, `Article.concept.md` 4; even a same-named sync file differed across two UCs. Implementation is single-instance (one `SessionConcept` class), so the contradiction only surfaced at Stage 04. Per-feature gates bind only their own outputs, giving false isolation.

The rebuild already shipped a **detection** band-aid, not a fix:

- `quality-gate/verify_shared_action_contracts.py` (commit `719a816`, wired into `verify_artefacts.py`) compares each `Concept.action` declared by ≥2 features and fails on disjoint outcome vocabularies. It is a **post-hoc cross-feature comparison** that only works because the drift is allowed to exist.
- `templates/feature-skeleton/stages/02_concepts/CONTEXT.md` gained a "Shared concepts (cross-feature contract)" directive — a manual reuse rule with no canonical store to reuse *from*.
- `templates/concepts-catalog.md` already states the correct rule ("one owning feature per concept; later features add *Used by*; do not redefine") but **no stage reads, writes, or checks it** (verified: zero consumers in `quality-gate/`, `methodology/`, `templates/`, `AGENTS.md`).

This change makes the rule structural: with one canonical corpus, cross-feature concept drift is impossible by construction, and the drift guard is repurposed (see "Reconciliation").

## Decisions locked (do not re-litigate)

D1 Model B (system-scope vocabulary; use cases compose). D2 the corpus IS the canonical spec (full anatomy: name + type params, purpose, state, user/system actions, operational principle). D3 the catalog index is generated (`Concept | Purpose | Type params | Actions | Introduced by | Used by | Notes`) and carries action *names*. D4 a reviewed app-level **extrinsic** dependence graph + valid subsets (`features/_system/concept-dependence.md`), the implementation scheduling graph. D5 ownership = introduction provenance; REUSE binds and never re-authors; EXTEND is a reviewed proposal (`used-by ∪ dependence-neighbour` impact); NEW otherwise; promotion on gate approval. D6 criteria gate = mechanical subset + human checklist. D7 parallel unit is the concept; schedule by topological levels (document only). D8 adopted-unchanged concepts allowed. D9 cross-app ontology is a non-goal. D10 Stage 03a is **re-described** (not renamed) as the per-UC coordination review; the term "concept dependence" is reserved for D4; 03a cards are *evidence* for dependence edges.

Resolved sub-decisions: S1 dependence graph is a separate system-scope artefact reviewed with the catalog (no new numbered stage). S2 promotion via an explicit `./clad promote-concepts` after gate approval. S3 corpus seeded from `UC-00-login` (provenance "introduced by UC-00-login"). S4 **revised** — Stage 02's file manifest stays static; the NEW/EXTEND proposal set is validated by a new `verify_concept_proposals.py` (do not implement the original dynamic-manifest design). S5 the running experiment fork is out of scope; a new smaller-scope experiment follows later.

## Structural risk and mitigations (M1–M5, part of this design)

- **M1 — one resolution chokepoint.** `quality-gate/clad_stages.py:87` `CONCEPT_DIR = _dir("02_concepts")` is the concept-spec source for five readers: `_CONCEPT_STATE_RELATIONAL`, `_DATA_MODEL`, `_SPEC_PARITY`, `_ACTION_CHAIN` (via `--concept-dir`) and `generate_spec.py:76` (calls `cs.CONCEPT_DIR` directly).
  **Resolution is a UNION, not a swap (found while writing the Phase 3 contracts).** Between Stage 02 and Gate-2 promotion a NEW/EXTEND concept exists **only** as a proposal in the feature's `02_concepts/output/`; the canonical corpus holds only already-promoted concepts. D5 ("reusing UCs emit bindings, never copies") therefore requires the effective concept source to be the **ordered union** `[<feature>/02_concepts/output, <corpus>]`, with a proposal shadowing the canonical spec of the same name. Introduce `cs.concept_source_dirs(feature_root) -> list[str]` and a `concepts.dir` config key (default `features/_system/concepts`), plus a **legacy fallback** (a feature with no corpus and no bindings resolves to its own `02_concepts/output` exactly as today). The four consumer checks take a repeatable `--concept-dir`; `generate_spec.py` iterates the same ordered list. This supersedes the earlier "one resolver returning one dir" phrasing. Reassign `_CONCEPT_STATE_RELATIONAL` from Stage 02 to a corpus check.
  **M1 completeness (found during Phase 0 recon).** Six further readers hardcode `02_concepts/output` and must be routed through the same resolver or explicitly repointed: `_CONCEPT_MANIFEST` (`clad_stages.py:442`, built by `_manifest_check`) and `artifact_parsers.expected_stage_outputs` (`out["02"]`) — these become bindings + proposals under M2; `generate_sync_cards.py:99,102` (emitted card text); `verify_implementation_parity.py:328` (`collect_spec_stems`); `verify_iterative_change_coupling.py:29` and `verify_iterative_change_readiness.py:32` (R17 triggers).
- **M2 — static manifest + proposal verifier.** Stage 02 always emits `concept-bindings.md`; keep `_CONCEPT_MANIFEST`'s expectation static; add `verify_concept_proposals.py` (NEW/EXTEND rows in 01a ⇔ present proposal specs; REUSE rows have none).
- **M3 — promotion is a gated transaction.** `quality-gate/promote_concepts.py` + a `promote-concepts` arm in the `clad` wrapper; refuses unless Gate 2 is approved; idempotent; writes a promotion receipt; refuses frozen features; regenerates catalog + applies reviewed dependence edits; must not change other subcommands.
- **M4 — backward compatibility proven.** Fallback resolution + fixtures (reuse-only / mixed / new-only) + invariants (no-corpus feature behaves as today; manifest semantics unchanged; advance/approve unchanged). Live oracle: `UC-00-login` before Phase 6b.
- **M5 — sequence by blast radius.** Additive phases (1–3) first; the mutating surfaces (Phase 4) as their own checkpoint, one surface per commit; docs last.

## Reconciliation with the 0.7.x experiment fixes (must be resolved in this change)

1. **`verify_shared_action_contracts.py` becomes vacuous under Model B** — its premise (one concept authored in ≥2 per-feature spec dirs) is structurally prevented, and it already excludes `UC-00`. **Proposed:** repurpose it as a **corpus-vs-proposal consistency check** (a UC's Stage-02 proposal for an existing `<Name>` must extend the canonical corpus signature/outcomes additively, never redeclare a disjoint vocabulary), reusing its existing machinery and regression tests; keep the multi-UC comparison only for legacy-fallback features. Alternative considered: retire it entirely and let `verify_concept_registry.py` absorb the guarantee. **Decision (human, design gate): repurpose it** — keep the script and its regression tests as the corpus-vs-proposal consistency check; do not retire.
2. **Stage-02 "Shared concepts" directive** (`719a816`) is superseded/extended by the bindings + proposals design; it must not survive as a duplicate rule pointing at per-feature specs.
3. **`templates/concepts-catalog.md` currently contradicts D2/D4** — it says the *owning feature* holds `<Name>.concept.md`, and lists concept dependencies as "Out of scope (R1)". Both must be amended (corpus holds the spec; distinguish intrinsic dependence — none, R1 — from extrinsic dependence, `concept-dependence.md`).
4. **RESUME `## Gate snapshot` is machine-owned** (`8f04cbd`): Phase 6b must re-approve via `approve-iter` (change record) **and** `approve <N>` (gate status + new content hash), never by hand-editing hash lines. The hash covers a gate block's `output/` dirs only (`verify_stage_sequence.py:211`), so re-approve only gates whose outputs actually moved.
5. **R17 trigger coverage:** `verify_iterative_change_readiness.py` `ITERATIVE_PATTERNS` match only `features/UC-*/stages/02_concepts/output/*.concept.md`; the corpus path must be added (or corpus writes explicitly routed through the gated `promote-concepts`) so canonical-concept edits cannot bypass the guard.

## Mechanism

`clad_stages.concept_source_dirs` returns the feature's proposals first, then the
canonical corpus, so a proposal shadows the corpus
(`quality-gate/clad_stages.py#concept_source_dirs`).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Concept anatomy/outcomes unchanged; only their storage location moves. UC-00 re-entered at Gate 1/2 (Phase 6b) |
| Action ordering and sync deduplication | `preserved` | Syncs unchanged; only their concept references resolve through M1 |
| Flow-token lineage | `preserved` | No engine or grammar change in this maintenance record |
| Storage/retention semantics | `preserved` | No profile or FactStore change |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | no | — (this is a methodology/gate change) |
| Engine or profile contract documentation | no | — |
| Profile configuration or deployment files | no | — |
| Gate scripts | yes | new `generate_concepts_catalog.py`, `verify_concept_criteria.py`, `verify_concept_proposals.py`, `verify_concept_registry.py`, `promote_concepts.py`; amended `clad_stages.py` (M1 resolver + check reassignment), `verify_artefacts.py`, `verify_iterative_change_readiness.py`, repurposed `verify_shared_action_contracts.py` |
| Gate tests | yes | new fixtures for reuse-only / mixed / new-only; M1 fallback; M2 proposal matrix; M3 gate-refusal + idempotency; R17 corpus-trigger |
| Stage contracts | yes | skeleton `01a`, `02`, `03`, `03a`; Stage 03b/04b/04d Inputs point at the corpus |
| Templates | yes | `concept.md`, `responsibility-map.md`, `concepts-catalog.md`, `dependency-review-card.md` |
| System-scope artefacts | yes | new `features/_system/concepts/`, `concepts-catalog.md`, `concept-dependence.md`; `_system/README.md` rider |
| Methodology docs | yes | `CONCEPTS.md`, `STAGES.md`, `ARTEFACT_MAP.md`, `TRACEABILITY.md`, `CONTEXT_MANIFEST.md`, `RULES.md` (only if required), `AGENTS.md`, `CONTEXT.md`, `CHANGELOG.md` |
| UC artefact chain | yes (one) | `UC-00-login` re-entered at Gate 1 (01a Origin column) and Gate 2 (02 bindings) via Phase 6b; all other features untouched |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Existing features with no corpus behave exactly as today | unit | `test_concept_registry.py` ResolverTests | pass | 2 cases: no corpus → feature dir only; corpus appended |
| `verify_file_manifest.py` semantics unchanged (S4/M2) | integration | `verify_artefacts.py` (UC-00 legacy expected outputs) | pass | legacy map → one spec per concept, no bindings |
| NEW/EXTEND ⇔ proposal specs; REUSE ⇔ no spec | unit | `test_concept_registry.py` ProposalMatrixTests | pass | 3 cases (new w/o proposal fails; reuse w/ spec fails; new w/ proposal passes) |
| Promotion refuses without approved Gate 2 | unit | `test_concept_registry.py::PromotionTests::test_refuses_without_gate2_approval` | pass | refused; corpus untouched |
| Promotion is idempotent at the same gate hash | unit | `PromotionTests::test_promotes_then_is_idempotent` | pass | second run → `no-op`; provenance stamped; catalog regenerated |
| Canonical-concept edits hit the R17 guard | unit | `test_iterative_change_readiness.py::test_canonical_corpus_concept_is_iterative_scope` | pass | corpus path in scope; catalog/index not |
| Catalog regeneration is deterministic | unit | `test_concept_registry.py` CatalogTests + dry-run `diff` | pass | byte-identical across runs |
| Registry: one introducer; no redefinition; promoted-on-approval | unit | `test_concept_registry.py` RegistryTests | pass | 2 cases |
| Drift guard: proposal vs corpus | unit | `test_shared_action_contracts.py` (2 new cases) | pass | disjoint outcome fails; additive extension passes |
| Criteria mechanical subset | integration | `verify_concept_criteria.py` on the corpus | pass | 3 concepts, 0 warnings |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | **134 passed** |
| Pipeline + doc links | integration | `verify_artefacts.py`; `verify_links.py` | pass | pipeline intact; 310 links |
| Reference reactor intact | integration | `mvn -q test -f reference-impl/pom.xml -pl java-legible -am` | pass | exit 0 |

## Gates

### Design gate

The design was approved in-conversation (Model B locked: D1–D10, S1–S5, M1–M5). This record is presented for confirmation, including the item-1 disposition (`verify_shared_action_contracts.py` repurpose vs retire). Approve with `./clad approve-maintenance system-scope-concept-vocabulary design`, then Status becomes `active`.

### Evidence gate

Reviewed after the executed test matrix and `verify_artefacts.py` + reactor evidence, and after Phase 6b's UC-00 re-approvals. Approve with `./clad approve-maintenance system-scope-concept-vocabulary evidence`; then Status `closed` and the record commits with the change.

## Notes

- **Feature-contract impact detail:** `preserved` for every feature; the worked
  example `UC-00-login` is deliberately re-entered at Gate 1 + Gate 2 in Phase 6b
  via R17 (the sole exception, recorded in `_changes/system-scope-concepts.md`).
- **Only in scope:** the upstream `clad` repository. The running experiment fork is not read, merged into, or modified; a new smaller-scope experiment follows after this lands.
- **Frozen boundaries:** no edits to frozen feature outputs except Phase 6b's gated UC-00 re-entry.
- **Version:** a minor bump (not a patch). Release/tag only on explicit human authorization.
- **Resolved at the design gate:** the shared-action drift guard (`verify_shared_action_contracts.py`) is **repurposed** as a corpus-vs-proposal consistency check (item 1). No open questions remain.
