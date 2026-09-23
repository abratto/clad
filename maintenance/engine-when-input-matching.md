<!-- Maintenance-route planning record. Copy to maintenance/<change-name>.md. -->
# Maintenance change — `engine-when-input-matching`

> Platform change under `methodology/core/ITERATIVE_CHANGES.md`
> §"Platform maintenance changes" and R20. Engine DSL/verification
> accommodation, not a feature-UC change: outcomes, response shape,
> concept boundaries, sync rules, and observable action order are
> **preserved** — the same flows with the same outcomes, only the
> declarative surface that expresses route discrimination moves.

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/legible-engine` (DSL extension), `reference-impl/java-legible` (migration), `reference-impl/java-micronaut-postgres` (inherits; no behaviour change), `reference-impl/java-plain` (inherits; no behaviour change)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Close the last meaningful parity delta with the paper-authors' own sync implementation (MIT 61040 conceptbox, `design/background/implementing-synchronizations.md`): `SyncRule` gains an optional **input-pattern matcher** on the `when` trigger — `when Web/request (route: "profile") : routed` — so route/value discrimination moves from hand-written `Guard` clauses in `where` into the trigger token itself. The 10 `?route` guards across the four stocked example features migrate to matchers. `Guard` remains legal (R15) for comparisons a when-matcher cannot express (non-literal operands). Deltas against the conceptbox model that CLAD **declines to adopt** are recorded below with rationale.

## Mechanism

A conjunct's input matcher is applied in `SyncEngine.candidateEntries` via
`patternMatches` (reference-impl/legible-engine/src/main/java/dev/legible/engine/SyncEngine.java:152).

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | migrated features' flows keep identical outcomes/status codes; java-legible's FlowTraceTest/LoginFlowTest are the regression oracle |
| Action ordering and sync deduplication | `preserved` | same rule set; one rule = one chain-table transition unchanged |
| Flow-token lineage | `preserved` | matcher is evaluated at fire time inside the trigger check; `causedBySync` lineage unchanged |
| Storage/retention semantics | `preserved` | engine's `Region`/`FactStore` semantics untouched |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `SYNCHRONIZATIONS.md` §"Input matching in the when clause"; `methodology/implementation/RULES.md` R15 restated |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | yes | `SyncRule` (+ matcher field + factory overloads), `SyncEngine` (trigger match filtering), `DebugApi` (`syncs()` matcher column) |
| Profile tests | yes | 10 Guards migrated in `java-legible/{login,tagging,social,token}`; existing flow/concept tests are the oracle |
| UC artefact chain | no | no stage artefact changes; Stage 03 `*.sync.md` grammar gains an optional when-matcher notation (docs/template only — no generator change needed: the generator already emits matcher-free skeletons and never emitted Guards) |

## Deliberate non-adoptions (parity deltas declined, with rationale)

1. **Imperative/computed `where` (conceptbox `frames.filter(count >= 10)`, JSON assembly in `where`).** Declined: re-introducing hidden logic into the declarative binding phase would break Legible's "readable-at-a-glance" property and the deterministic Stage 03a–05 machinery built on Pattern A/B/C/D. Discrimination belongs in concept outcomes (R3), and concept actions can return the discriminated outcome directly. Recorded as a designed divergence, not a gap.
2. **Parametrized concept query actions as `where` sources (`frames.query(Comment._getByTarget, {target: post}, {comment})`).** Deferred (non-goal for this record): requires a "queries" tier in the SPEC slices, Stage 02/04b artefact chains, and pattern-card machinery. Rich lookups today express via `FanOut` + binary `StateRead`; revisit only with demonstrated need recorded in a new maintenance record.

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Matcher fires for matching input, not for non-matching | unit | java-legible example flows re-run post-migration (publish/tag/subscribe/profile/list-tags routes only fire their own sync) | pass | reactor green; route-scoped flows unchanged |
| Guard semantics unchanged for in-where discrimination | unit | remaining `Guard`/`OptionalClause` examples re-run | pass | reactor green |
| Migration equivalence: guard-only route syncs produce identical outcomes with matcher | feature | `mvn -f reference-impl/pom.xml test` (post-migration) | pass | full reactor green (incl. tagged flows, concurrency, storage contracts) |
| Advisory detector recognizes matchers | gate | `verify_sync_route_filters.py --sync-impl-dir reference-impl/java-legible/src/main/java/dev/legible/example` | pass | 27 SyncRule(s) examined, no ambiguous shared-trigger respond sync |
| Docs links | gate | `quality-gate/verify_links.py` | pass | 299 links checked |
| Canonical gate | gate | `test.command` (verify_artefacts + reactor mvn test) | pass | artefact pipeline intact; reactor green |

## Gates

### Design gate

The human reviewed and approved the proposal in-conversation ("I agree
with your proposed changes and scope"): engine matcher + factory
overloads + DebugApi surface, paper-faithful when-matcher notation in the
Stage 03 `*.sync.md` template and `SYNCHRONIZATIONS.md`, R15 restatement,
Guard retained for non-literal comparisons, 10-guard migration across the
four example feature sets, the advisory detector recognizing matchers,
and the two recorded non-adoptions.

### Evidence gate

Approved by the human after the test matrix was presented (full reactor green
post-migration, matcher-aware advisory detector 27 rules examined, docs+
artefact gates green).

## Notes

- The when-matcher is a **routing/discrimination equality** on trigger
  *input values*, matching the reference implementation's
  `when Requesting.request (path: "/X")` shape. It does not introduce
  business branching into syncs: business discrimination remains the
  trigger *outcome* property (R3's reason for existing).
- Follow-up flagged for the record close: verify `verify_sync_matrix.py`
  docs (not a code change) mention that when-matcher tokens parse as part
  of when signatures but no new grammar is required since literals in the
  when-brackets were already accepted.
