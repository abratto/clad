# Maintenance change — `sync-authoring-expressiveness`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `all profiles` (documentation only — no engine, generator, or contract change)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** Three documentation improvements to the sync-authoring surface: a paper/ConceptBox translation callout, a post-commit compensation pattern, and a progressive-disclosure restructure of `templates/sync.md` and the `clad-sync-design` skill. No DSL, engine, generator, or gate change.

## Why

A three-way comparison of CLAD's synchronization model against the Meng & Jackson
paper (arXiv:2508.14511, §5–§6) and the paper authors' ConceptBox engine found
that CLAD is expressively complete for the coordination rules it is designed to
hold, and exceeds both sources on flow pinning, route-scoped naming, and `absent`.
The residue worth closing is **authoring-surface information architecture**, not
language expressiveness. This record closes three documentation gaps.

### Item 1 — the pin-ordering portability hazard

CLAD's joined-rule dispatch evaluates a rule's `where` against its **primary
(first)** conjunct, so the flow pin goes **last**. The paper lists `Web/request`
first in its multi-`when` examples, and ConceptBox's `actions([...])` is
order-agnostic. An agent or human translating either verbatim puts the request
first and produces a rule that fires with blank arguments — the failure the
`sync-flow-pinning` change found the hard way (9 errors / 5 failures in the
experiment). The rule is documented in `SYNCHRONIZATIONS.md` §"Flow pinning" and
`maintenance/sync-flow-pinning.md`, but it is absent from the two places an author
actually reads: `templates/sync.md` and the `clad-sync-design` skill.

### Item 2 — no idiomatic home for compensation

The paper's *older* transactional scheme (§3) had suppression: a failed
downstream action aborts the trigger. The paper's final scheme drops
transactions, and CLAD follows (fire-after-commit). CLAD's R23 covers
request-level refusal, but there is no idiomatic home for **compensation** —
"X already committed, downstream Y failed, now mitigate X". Today an agent
hitting this will improvise an imperative coordinator or a half-rollback, which
is exactly the design smell R3 exists to prevent.

### Item 2b — flat union instead of progressive disclosure

The DSL is appropriately simple for simple cases and correctly expressive for
hard ones: the paper core (three clauses, `?var`, flow token) covers a bootstrap,
and every addition (named conjuncts, flow pinning, route-scoped naming, `collect`,
`absent`) traces to a real bug. The problem is information architecture: a
first-time author opening `templates/sync.md` meets naming grammar, joins,
pin-last, `absent`, and three `collect` variants before the basic three-clause
rule, and never learns which subset applies to the chain-table row in front of
them.

## Mechanism

This is a documentation change, but the one mechanism it relies on is the pin
position, so it cites the code: `SyncEngine.processInvocation` hands a rule's
**primary (first)** conjunct to `WhereEvaluator`
(reference-impl/legible-engine/src/main/java/dev/legible/engine/SyncEngine.java:270),
and `triggerField`/`triggerInput` resolve against it
(reference-impl/legible-engine/src/main/java/dev/legible/engine/WhereEvaluator.java:98).
The callout documents this; it changes nothing.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Documentation only; no artefact changes |
| Action ordering and sync deduplication | `preserved` | Documentation only; no engine change |
| Flow-token lineage | `preserved` | Documentation only |
| Storage/retention semantics | `preserved` | Documentation only |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `SYNC_PATTERNS.md` (compensation pattern); `templates/sync.md` and `skills/clad-sync-design/SKILL.md` (translation callout + progressive disclosure) |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | — |
| Profile tests | no | — |
| UC artefact chain | no | No spec, contract, outcome, or order change |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| Artefact gate stays green | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact, 0 WARNs |
| Gate suite stays green | unit | `python3 -m pytest quality-gate/tests -q` | pass | 230 passed |
| Doc cross-reference links resolve | integration | `python3 quality-gate/verify_links.py` | pass | 292 links, 106 docs |
| Mechanism citation resolves | integration | `python3 quality-gate/verify_mechanism_citations.py` | pass | `SyncEngine.java:270`, `WhereEvaluator.java:98` |

## Gates

### Design gate

Presented with the docs written (docs-only: the maintenance route's
implementation hold covers engine/profile/configuration/deployment, none of which
this touches). Approve with
`./clad approve-maintenance sync-authoring-expressiveness design`.

### Evidence gate

Cleared: the artefact gate is intact (0 WARNs), the gate suite is green at 230,
doc links resolve (292), and the record's mechanism citation resolves. Docs-only,
so no profile build is required.

## Notes

- Docs-only: no engine, generator, or contract change; feature-contract impact is
  `preserved`.
- The Item 1 callout corrects a translation hazard the sources' own ordering
  would otherwise reintroduce.
- The compensation pattern is the deliberate replacement for the paper's retired
  transactional rollback (§3), not a reintroduction of transactions.
- The restructure keeps the DSL unchanged — it is a readability pass, and R3's
  framing is intact.
