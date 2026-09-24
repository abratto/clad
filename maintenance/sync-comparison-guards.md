# Maintenance change — `sync-comparison-guards`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md` §"Platform maintenance changes" and R20
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** `reference-impl/legible-engine` (proposed; **not implemented in this pass**)
- **Feature-contract impact:** `preserved`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** A **discussion record**, not an implementation. It frames whether CLAD should extend `Guard` to accept pure literal comparisons (`>`, `<`, `>=`, `<=`) over two bound variables — a recurring shape ConceptBox's `frames.filter($ => $[count] >= 10)` and SPARQL `FILTER` cover — against the cost to R3's bright line. Decide and close; no code changes in this pass.

## Why

ConceptBox and SPARQL cover a common shape — "fire only when at least N" — with a
comparison in `where`: `frames.filter($ => $[count] >= 10)`, or SPARQL `FILTER`.
CLAD deliberately routes that into a **concept action + outcome**: the concept
decides `Enough` / `NotEnough` and the sync matches the outcome. That choice is
defensible and keeps `where` free of computation, but it is a recurring tax on a
frequent case: every threshold becomes a concept action whose only job is to
compare two numbers.

A *minimal* extension would let `Guard` accept a pure literal comparison over two
bound variables:

```
where {
    bind ( ?count as ... )
    guard ( ?count >= ?minimum )    // proposed shape — NOT implemented
}
```

No arithmetic, no functions, no JSON — only a comparison operator over two
already-bound values. That stays declarative in the SPARQL sense.

## The tension (the decision)

### Side A — adopt minimal comparison guards

- The shape is frequent and mechanical; outcome-ifying it adds concept actions
  that exist only to compare, which is arguably its own kind of coupling.
- A comparison over two bound variables is pure and total: it reads no state,
  renders no payload, and is fully visible in the `where` block.
- SPARQL `FILTER` is the paper's own substrate for the *older* engine; a literal
  comparison is the narrowest slice of it and does not open the imperative door.

### Side B — keep outcome-ifying comparisons in concept actions (status quo)

- **The bright line is legibility.** Today's rule is crisp and auditable at review
  time: *no comparison a literal `when`-matcher cannot express, except `Guard` on
  non-literal operands* (itself a narrow, hand-audited case). The moment a
  comparison operator is legal in `where`, the line becomes "some comparisons are
  fine, some are not", and every review must re-derive which.
- **The slope is real, not rhetorical.** Once `>=` is declarative, `>`, `==`, `+`,
  `max()`, and "just one function" each look like the same kind of exception.
  ConceptBox's own imperative surface began as small conveniences.
- **Discrimination belongs in the concept.** "At least N" is a judgement about
  *the concept's* state and belongs to the concept that owns it; the outcome is
  also the more legible artefact — a reader sees `Enough` in the chain table,
  not `count >= 10` embedded in a coordination rule.
- **The recurring tax is small and bounded.** The outcome-ifying is one action
  per threshold shape, reused across flows; it is not per-sync boilerplate.

### Recommendation

**Keep the status quo (decline).** The comparison guard is narrow, but it erodes
the single sentence that makes `where` reviewable, and the concept-outcome route
is the more legible artefact. The tax is real but bounded and already paid.

**Decided: declined (2026-09-23).** The bright line holds — `where` accepts no
comparison a literal when-matcher cannot express, except `Guard` on non-literal
operands — and comparisons stay in concept outcomes (`Enough` / `NotEnough`). No
implementation in this pass, and none scheduled: the decision is that this
extension does not belong in CLAD's declarative `where`.

### Rationale for the decline

- The bright line is a sentence a reviewer can apply without re-deriving edge
  cases; adding an operator makes it a judgement call.
- The concept-outcome route is the more legible artefact: `Enough` appears in the
  chain table and the concept spec, where a reader can see it.
- "At least N" is a judgement about the concept's own state; the concept that owns
  the state is where the judgement belongs (R3).
- The recurring tax is one reusable concept action per threshold shape, not
  per-sync boilerplate — bounded and already paid.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | Discussion only — no change in this pass |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine or profile contract documentation | yes | `SYNCHRONIZATIONS.md` §"Input matching in the when clause" already states the divergence; this record frames the decision |
| Profile configuration or deployment files | no | — |
| Engine/runtime implementation | no | **Not implemented in this pass** |
| Profile tests | no | — |
| UC artefact chain | no | — |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| No code change in this pass | — | `git diff` shows docs/record only | pass | record + decision only; no engine change |
| Artefact gate stays green | integration | `python3 quality-gate/verify_artefacts.py` | pass | artefact pipeline intact, 0 WARNs |
| Gate suite stays green | unit | `python3 -m pytest quality-gate/tests -q` | pass | 231 passed |

## Gates

### Design gate

**Approved, decided to decline (2026-09-23).** The minimal comparison guard is
not adopted; comparisons stay in concept outcomes and `Guard` stays for
non-literal operands. No implementation in this pass.

### Evidence gate

Cleared: this is a discussion record, so its evidence is the recorded decision
above plus a green gate (`verify_artefacts.py` intact, 231 tests). No code change;
nothing to build.

## Notes

- **Out of scope:** arithmetic, functions, aggregate predicates, and any
  comparison over a computed operand — the extension, if ever adopted, is pure
  literal comparison over two bound variables only.
- **Boundary to the other batch items.** Item 3's record-form `collect` is
  grouping/projection and does not touch this line; the comparison guard is the
  one item that would, which is why it is isolated as discussion-only.
- The current answer is coherent: `Guard` on non-literal operands plus concept
  outcomes. Declining keeps R3's line a sentence, not a judgement call.
