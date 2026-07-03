# Workflow overlay — DECISIONS

> **Status: optional.** Nothing in `methodology/core/`,
> `methodology/architecture/`, or `methodology/implementation/`
> requires this. Use it if you want a lightweight Architecture
> Decision Record (ADR) trail; ignore it if your team logs decisions
> elsewhere (PR descriptions, issue threads, an external wiki).

## Why an overlay

CLAD's stage gates capture **what** was decided each turn (the
`output/` of each stage *is* the decision). They do not capture
**why** — particularly for cross-cutting choices that span features:
"why Jena over Postgres for the reference profile?", "why one named
graph per concept rather than one schema?", "why no JWT?".

Without a place to write those down, the same questions get
re-litigated session after session. The DECISIONS overlay is that
place.

## When to write a record

Write one when, and only when, **all three** are true:

1. The decision is **cross-cutting** (touches more than one feature
   or more than one stage).
2. The decision was **non-obvious** at the time (a reasonable agent
   would have picked the other option).
3. The decision will be **annoying to reverse** (changing it later
   means coordinated edits across multiple files).

Decisions that are local to a feature belong in that feature's
stage `output/`. Decisions that are obvious do not need a record.

If you are tempted to write an ADR every day, you are over-using
this overlay; tighten the three criteria above.

## Where records live

```
docs/decisions/
  0001-<slug>.md
  0002-<slug>.md
  ...
```

(Or any folder your project prefers; the path is convention, not a
hard requirement.)

Records are **append-only**. Numbers do not get reused. A reversed
decision becomes a new record that **supersedes** the old one and
cross-links it; the old record stays in the tree, marked
`Superseded by 00NN`.

## The record format

Use the four-section short-ADR template at
[`../../templates/decision-record.md`](../../templates/decision-record.md):

- **Status** — `Proposed`, `Accepted`, `Superseded by 00NN`,
  `Deprecated`.
- **Context** — what forced the decision (one short paragraph; link
  to the relevant feature stage if applicable).
- **Decision** — what we chose, in one or two sentences.
- **Consequences** — what becomes easier and what becomes harder.

Aim for one screen of text. Long ADRs do not get re-read.

## How to cite a decision from a stage output

When a stage's output rests on a recorded decision, cite it:

```
> See DR-0003 (`docs/decisions/0003-jena-over-postgres.md`).
```

Citing a decision is what makes it load-bearing. An ADR that nothing
links to has no force; delete it or merge it into another.

## Relation to other overlays

The DECISIONS overlay is independent of TRACKING. You can use one,
both, or neither. They do not interact: TRACKING is *what feature is
active now*; DECISIONS is *what stable choices the project has
already made*.
