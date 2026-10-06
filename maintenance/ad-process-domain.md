# Maintenance change — `ad-process-domain`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed` (`draft` until design approval, `active` while
  implementing, `closed` after evidence approval)
- **Affected profile(s):** all features (quality-gate scripts + the Stage 03
  stage contract in `templates/feature-skeleton`, mirrored in the worked
  example); `methodology/architecture/SYNC_PATTERNS.md`,
  `methodology/reference/CITATIONS.md`, `methodology/implementation/QUALITY_GATE.md`
- **Feature-contract impact:** `preserved` (advisory only — the profile never
  blocks; no derived-artefact or runtime contract changes)
- **Design gate:** `approved` (human, in-conversation: "Take both" — the
  process-domain framing and the sync information linter, with the devil's
  advocate conclusions adopted: profile vector not a weighted number; count
  departures from A; price D with the outcome-instead-of-read prompt; the
  labels are author-declared, so the profile is a self-report)
- **Evidence gate:** `approved`
- **Change summary:** Frame CLAD's layering onto Suh's domain pairs (scenarios
  = FRs, concepts = DPs, **syncs = the process domain**), making the shipped
  sync-cycle-graph and sync-overlap checks legible as the Independence Axiom
  at the DP↔PV pair — and add `sync_information.py`, an always-advisory
  linter that reports each sync's A/B/C/D binding profile (the Information
  Axiom read as a binding-complexity ladder) plus the feature aggregate, with
  findings only for concept-state reads (with the "outcome instead of read?"
  remediation prompt) and join arity ≥ 3.

## Mechanism

- **Framing (no behavior change).** The A/B/C/D ladder in
  `SYNC_PATTERNS.md` already ranks bindings by information content —
  A (trigger token) adds zero; B (flow-sibling output) adds chain-topology
  knowledge; C (sync constant) adds a copy point (≥3 copies exist of every
  literal: chain row, sync spec, implementation); D (concept-state read)
  crosses the concept boundary. The framing docs make the Suh mapping
  explicit: customer→goals (Stage 00), functional→scenarios (FRs),
  physical→concepts (DPs), process→syncs (PVs). Independence at FR↔DP is the
  FR×DP matrix (`ad-design-deepening`); independence at DP↔PV — no
  back-coupling between concepts through the orchestration — is the shipped
  cycle graph (A→B→A) and lock-order overlap check, previously unlabelled as
  AD. The Information Axiom is honestly noted as an adaptation: Suh's
  information content is probabilistic (design range vs. system range); the
  profile is a structural reading, the same kind of honest adaptation as the
  ORM-ML non-adoption note.
- **`sync_information.py`.** Parses each sync's existing
  `## Where clause patterns (for Stage 03a audit)` table (the only reliable
  pattern source — the labels are author-declared) and the `when` block's
  conjunct count. Reports per sync `A=a B=b C=c D=d join=k`, the feature
  aggregate, and advisory findings: every D read (with the
  "outcome instead of read?" prompt — concepts decide, syncs route) and any
  join of arity ≥ 3. No weighted score (devil's advocate: pseudo-quantitative
  and gameable); no findings on C or B counts alone (counted, priced, not
  flagged). Syncs without the pattern table (unresolved skeletons) are noted
  per file and skipped. Always exits 0.
- **Wiring.** `_SYNC_INFORMATION` runs advisively at Stage 03 beside
  `_FR_DP_MATRIX` and the cycle/overlap checks, with the contract lockstep
  edits (template + worked example) the consistency tests enforce.
  `quality-gate/INDEX.md` regenerated.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Advisory linter only; no runtime or derived-schema change. |
| Action ordering and sync deduplication | `preserved` | Stage-03 checks extended with one advisory entry; blocking checks unchanged. |
| Flow-token lineage | `preserved` | Untouched. |
| Storage/retention semantics | `n/a` | No storage surface. |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `CITATIONS.md` (domain-pair mapping), `QUALITY_GATE.md` (process-domain framing), `SYNC_PATTERNS.md` (profile pointer), Stage-03 contract (template + example). |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | quality-gate scripts only. |
| Profile tests | yes | New `quality-gate/tests/test_sync_information.py`. |
| UC artefact chain | no | The profile reads sync specs; it emits nothing into stage outputs. |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Profile parses the real worked example correctly | unit (subprocess) | `tests/test_sync_information.py` | pass | UC-00 aggregate A=3 B=3 C=7 D=0, 13 bindings, join arities 1×1/6×2, no findings, exit 0 (hand-counted before coding; linter matched) |
| D-read and wide-join findings fire (synthetic) | unit | `tests/test_sync_information.py` | pass | a D read + arity-3 join produce both prompts (outcome-instead-of-read + check-the-chain-table); still exit 0 |
| Always advisory | unit | `tests/test_sync_information.py` | pass | findings never change the exit code (asserted on the synthetic findings case + the script body) |
| Wiring + lockstep | unit + suite | `tests/test_sync_information.py` + contract-consistency suite | pass | Stage 03 carries `sync_information` (args = the sync dir); template + example contracts name it; consistency suite green in the 368 |
| Whole gate suite green | gate | `pytest quality-gate/tests`, `verify_artefacts.py` | pass | 368 passed (362→368); artefact gate intact; INDEX regenerated + `--check` PASS |

## Gates

### Design gate

Approved in-conversation (2026-10-05). Devil's-advocate conclusions adopted:
A is the uncounted baseline; B is priced as structural coupling (not free);
C is priced as a copy point (necessary evil, never neutral); D is priced
hardest and carries the outcome-instead-of-read prompt; the score is the
vector, never a weighted number; the labels are author-declared, so the
profile is a self-report — misclassification stays with the literal-lock and
03a checks. The FR×DP matrix itself stays concept-only (a scenarios×syncs
matrix is diagonal by construction — every sync cites exactly one scenario —
so the concept anti-patterns would misfire over syncs).

### Evidence gate

Approved — matrix above: the real worked example's profile matched the
hand-count exactly (A=3 B=3 C=7 D=0, 13 bindings, join arities 1×1/6×2),
the synthetic D-read and arity-3 findings fire with exit 0, the suite is
368 passed (362→368) with the contract-consistency lockstep green, the
artefact gate is intact, and INDEX.md regeneration is deterministic.

## Notes

- On the `feat/axiomatic-design-wiring` branch, continuing the
  `ad-design-deepening` theme (that record is closed; this is a separate
  increment with its own record).
- Deferred (gated decisions if demand shows): a per-feature coupling budget
  (threshold on D count); persisting the profile into 03a outputs.
- Rollback: remove `_SYNC_INFORMATION` from Stage 03's checks and the
  contract block; the framing docs are prose-only.
