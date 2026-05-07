# CLAD — Contract-Led, Artefact-Driven Development

CLAD is a way of working with AI coding agents that keeps a human firmly in
the loop without slowing the agent down. It rests on two claims:

1. **A change is only real once it has a contract.** A contract is a small,
   reviewable specification — a use case, a concept spec, a sync spec, an
   API schema. If there is no contract, there is nothing to review and
   nothing to verify against.
2. **A contract is only real once it has an artefact.** An artefact is a
   file on disk: a markdown spec, a type definition, a unit of code, a
   test, a trace. If there is no artefact, there is nothing to diff and
   nothing to revert.

Together these mean: **every meaningful change leaves two trails behind it
— a contract that says what was supposed to happen, and an artefact that
says what did happen.**

## Principles

### P1. Contracts before code

No code is written before its driving contract exists. The contract may be
small (a one-paragraph use case is a valid contract) but it must exist as
a file before the work that fulfils it.

### P2. Artefacts on every step

Every step of every workflow produces a file in a known location. If a
step's outcome is a thought, the thought is written down. If a step's
outcome is a transformation, the transformation is committed. Nothing
that matters lives only in chat history.

### P3. One stage, one job

A stage (in the ICM sense — see
[`../implementation/STAGES.md`](../implementation/STAGES.md)) does
exactly one thing. Drafting concepts is a stage. Writing syncs is a
stage. Implementing them is a different stage. Mixing concerns inside a
single stage is the most common way agents drift.

### P4. The human is a reviewer, not an integrator

The human's job is to read each artefact, edit it if necessary, and
either approve the move to the next stage or send the agent back. The
human does not reconcile inconsistencies the agent introduced; the agent
does, after the human points them out by editing.

### P5. Source-level fixes for repeating patterns

If the same correction appears in three runs, the fix belongs in a
`CONTEXT.md`, a reference file, or a template — not in the latest output.
Output edits are diagnostic information; they should be lifted into the
source.

### P6. Trace back to the use case

Every running effect must be traceable, through flow tokens
([`../architecture/FLOW_TOKENS.md`](../architecture/FLOW_TOKENS.md)),
back to the use case that authorised it. If you cannot draw that line,
you have an unauthorised behaviour.

## The contract loop

```
  +----------+    +----------+    +-------+    +----------------+    +--------------+
  | use case | -> | concepts | -> | syncs | -> | implementation | -> | verification |
  +----------+    +----------+    +-------+    +----------------+    +--------------+
        ^                                                                    |
        +----------------------- back-trace from flow tokens ----------------+
```

This loop is the spine of the methodology. It is:

- **Sequential.** You do not write a sync before you have concepts to
  coordinate. You do not implement before syncs exist.
- **Reviewable at every arrow.** Every arrow is a folder boundary in the
  ICM scaffold; the human reviews what landed in `output/` before the
  next stage runs.
- **Reversible.** Every stage's output is a file. If stage 3 produced
  the wrong syncs, you re-run stage 3 with edited inputs.

## Why this discipline at all

Modern coding agents can produce a working system from a one-line
prompt. They cannot, on their own, produce a system that a human
reviewer can still understand a week later, modify safely, and trust to
behave only the way the contracts authorised. CLAD is the structure that
recovers that property.

The architecture that CLAD targets — Legible architecture, the WYSIWID
pattern — exists for the same reason at the runtime level: a system
whose runtime behaviour you can read directly from its concept specs.
See [`../architecture/LEGIBLE.md`](../architecture/LEGIBLE.md).
