# Maintenance change — `concept-novelty-gate`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (gate + templates + config + docs)
- **Feature-contract impact:** `additive` (one new blocking Gate-1 check,
  one new advisory lint; the `## Why not existing` template section is
  required only when the check finds a near-match)
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** consulting the canonical concept catalog before
  writing `new` in the Origin column becomes an auditable Gate-1
  obligation instead of a prose instruction.

## Why

"Reuse is roughly 90% of design" (`CONCEPTS.md`) and the responsibility-map
template's "Consult the system vocabulary BEFORE deriving" were
aspirational: nothing forced the lookup, and per-feature re-derivation of
an existing concept is exactly the drift R22 exists to prevent (six
divergent `Session.concept.md` files across six use cases in the Conduit
rebuild, surfaced only at Stage 04). The generated `concepts-catalog.md`
already answered "does the action I need already exist?" — but a question
nobody is obliged to ask is answered only by the conscientious.

## Rule

- **Justified novelty.** A responsibility-map row with `Origin: new` whose
  name + declared-action token set overlaps a catalog concept's token set
  at or above `concept.novelty.threshold` (default 0.5) must address every
  such near-match in the map's `## Why not existing` section — one bullet
  per near-match naming the existing concept and why it does not fit.
- **Visible close calls.** Every overlap above threshold — justified or
  not — is surfaced to the Gate-1 reviewer by an advisory lint.

Novelty is not banned; it is made deliberate. The check SKIPs (exit 0)
when the map is absent, when there is no Origin column (pre-Model-B), or
when the catalog is absent/empty (a project's first feature).

## Mechanism

- `quality-gate/concept_novelty.py` — shared tokenisation
  (PascalCase/camelCase word split), catalog parsing, Jaccard scoring,
  threshold parsing. Single source for both entry points so the gate and
  the lint can never disagree on what a near-match is.
- `quality-gate/verify_concept_novelty.py` — blocking, wired into Stage
  01b's checks in `clad_stages.py` (runs before Gate 1 alongside
  `chain_map_names`).
- `quality-gate/lint_concept_overlap.py` — advisory twin, wired beside it;
  always exits 0.
- `templates/responsibility-map.md` — new `## Why not existing` section
  with authoring guidance.
- `clad.properties` — new documented key `concept.novelty.threshold`.

## Evidence

- `quality-gate/tests/test_concept_novelty.py` — 7 tests: an unjustified
  collision fails and names both concepts; the same map with a
  `## Why not existing` bullet passes; a genuinely novel concept needs no
  section; missing catalog and missing Origin column SKIP; the linter
  warns and exits 0.
- Full `quality-gate/tests` suite green; `verify_artefacts.py` intact.
