# Maintenance change — `corpus-status-command`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `proposed`
- **Affected profile(s):** all profiles (new read-only CLI command)
- **Feature-contract impact:** `none` (reads the corpus and feature
  snapshots; writes nothing)
- **Design gate:** `pending`
- **Evidence gate:** `pending`
- **Change summary:** `./clad corpus-status` reports the shape of the
  canonical concept corpus: per-concept history, stale proposal snapshots,
  dependence in-degree, and remodel candidates.

## Why

The corpus accumulates one promotion at a time, and its shape was invisible
without opening every file. Two signals matter for governance:

- **History depth.** A concept extended by many features is where
  first-proposer bias hurts most — the introducer's frozen cut is what every
  extender had to add around. Those are the concepts a `remodel`
  (`concept-remodel-class`) is worth spending on.
- **Dependence in-degree.** The reviewed app-level graph
  (`concept-dependence.md`) is the implementation scheduling graph; a
  high-fan-in concept is load-bearing, and changing it has the widest blast
  radius.

Both were computable from artefacts that already existed but had no single
place to look.

## Rule

None (no behaviour gate). The command is read-only and advisory; it never
blocks, never writes, and exits 0. A concept is flagged as a remodel
candidate when its promotion history depth exceeds `--remodel-depth`
(default 3).

## Mechanism

- `quality-gate/corpus_status.py` — reads canonical specs (provenance via
  the `promote_concepts` regexes), feature Stage-02 snapshots (a snapshot
  differing from canonical is stale — expected, but now visible), and the
  reviewed `concept-dependence.md` edges table (in-degree). Sorted by
  in-degree descending.
- `clad` — new `corpus-status` subcommand (read commands may use the
  auto-discovered features dir; this one needs no feature at all).
- `AGENTS.md` §9 pointer.

## Evidence

- `quality-gate/tests/test_corpus_status.py` — 6 tests: empty corpus
  reports cleanly; history / current source / in-degree rendered and
  sorted; stale snapshot named; deep history flags the remodel candidate;
  shallow history does not; the seed repo's empty corpus runs clean.
- `./clad corpus-status` smoke-tested against this repository.
