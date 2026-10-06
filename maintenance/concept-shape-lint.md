# Maintenance change — `concept-shape-lint`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (gate + config + docs)
- **Feature-contract impact:** `additive` (new advisory warnings only; no
  blocking behaviour changes, no artefact shape changes)
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** the judgment subset of the concept criteria gains
  heuristic warnings that surface granularity smells at Stage 02 review
  without pretending to decide them.

## Why

`verify_concept_criteria.py` mechanized the checkable subset of the concept
criteria and left the rest to "a human checklist in the Stage 02 contract".
But several judgment calls have mechanically detectable *smells*:

- the Jackson naming trap has a second form CONCEPTS.md already names —
  machinery suffixes (`UserService`: "the `Service` suffix is incidental
  machinery, not a purpose") — which the existing anti-pattern name list
  does not catch;
- "purposive — one purpose, nameable in a short verb phrase" has a smell:
  a purpose stanza that needs a paragraph;
- "end-to-end — the operational principle must exercise the concept alone"
  has a smell CONCEPTS.md names outright: a principle that degenerates to
  "when this action happens, the state updates so" (cites at most one of
  the concept's own actions);
- "one purpose" has a smell: a state block or action surface wide enough
  to be two capabilities sharing a noun.

Warnings, not failures: granularity is exactly the call a script should not
make. The lint moves each call from undocumented to visible-at-review.

## Rule

Advisory only (always folded into the existing WARN stream; exit code
unchanged). A concept spec warns when:

- its name ends in a machinery suffix (`Service`, `Manager`, `Handler`,
  `Helper`, `Util`, `Controller`);
- its purpose exceeds `concept.purpose.max-words` (default 12);
- its state block exceeds `concept.state.max-fields` (default 8) or its
  action list exceeds `concept.actions.max-count` (default 10);
- its operational principle cites at most one of its declared actions.

Entity-noun naming remains covered by the pre-existing `ANTI_PATTERN_NAMES`
warning in the same script (Jackson's `Session` deliberately unflagged);
this change does not alter it.

## Mechanism

- `quality-gate/verify_concept_criteria.py` — new advisory checks in
  `check_one`; thresholds read from repo-root `clad.properties` via
  `_shape_limits()` with defaults on unset/invalid. No CLI change; no new
  wiring (the script is already a Stage 02 check).
- `clad.properties` — three documented keys.

## Evidence

- `quality-gate/tests/test_concept_shape_lint.py` — 7 tests: one fixture
  per warning; a clean spec produces zero warnings; the canonical
  UC-00-login specs (`UserNaming`, `PasswordAuth`, `Session`) produce zero
  warnings — a warning on those is a linter bug.
- Full `quality-gate/tests` suite green.
