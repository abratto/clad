# Maintenance change — `plan-concept-order-check`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (advisory planning check + overlay docs)
- **Feature-contract impact:** `none` (not wired into the per-UC stage loop;
  invoked from the optional PLANNING overlay only)
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** the plan board is checked against concept origins so
  orderings that guarantee corpus friction are visible at planning time.

## Why

Which use case runs first shapes the canonical concept corpus: the
introducer's cut becomes the base every later feature extends (R22
provenance), and promotion order is enforced mechanically. Two bad
orderings are knowable at planning time but were only discovered at Gate 2:

1. a feature scheduled early carries `extends:UC-XX` / `remodel:UC-XX` for
   a concept whose introducer is scheduled later or absent — the extension
   has nothing to extend;
2. two features in the same active wave both propose the same concept as
   `new` — the second promotion hits the registry's one-introducer rule.

## Rule

Advisory only (always exit 0). When `plan-board.md` exists, warn on:

- **extension before introduction** — `extends:`/`remodel:` targeting a UC
  scheduled later (status rank `done` < `doing` < `next` < `later` <
  `blocked`, ties by ascending priority) or absent from the board;
- **duplicate introduction** — the same concept proposed `new` by two
  features whose status is `doing` or `next`.

The check SKIPs when the planning overlay is not in use (no board, or no
queue rows). Sequencing remains a human decision; the warnings make the
corpus consequence of the sequence explicit.

## Mechanism

- `quality-gate/check_plan_concept_order.py` — parses the plan-board
  feature queue and each listed feature's Stage-01a responsibility map via
  `artifact_parsers`; emits WARN lines.
- `methodology/overlays/PLANNING.md` — invocation documented in the
  overlay; no stage-loop wiring (the overlay is optional).

## Evidence

- `quality-gate/tests/test_plan_concept_order.py` — 5 tests: missing board
  SKIPs; extension-before-introduction warns naming the later introducer;
  an introducer absent from the board warns; a duplicate `new` in the same
  wave warns of the Gate-2 collision; a consistent board PASSes.
- Full `quality-gate/tests` suite green.
