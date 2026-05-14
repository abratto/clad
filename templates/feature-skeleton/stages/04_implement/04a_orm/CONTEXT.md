# Stage 04a — ORM (optional state model)

## Why this stage exists

For profiles with a persistent store, this is where each concept's
`state` section becomes a concrete schema in **its own named region**
(hard rule R2 — no concept reads another's region directly). Drafting
the schema **before** writing tests catches "this field needs to be
there because flow X reads it via Pattern D" defects in 30 seconds
rather than later inside a failing test.

**Feeds:**

- `<Name>.orm.md` → 04d (the test fixture builds against this schema), and the runtime data layer in the profile.
- `_NOT_APPLICABLE.md` → a record that this stage was consciously skipped (e.g. for an in-memory profile).

**Agent stance for this stage:** if a Pattern D field from
`pattern-d-summary.md` is missing from the owning concept's region, do
not "add it to make the column exist" — go back to Stage 02 and add it
to `state` first.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs (state sections) |
| `../../03a_dependency-review/output/pattern-d-summary.md` | 4 | Every cross-concept field that must be exposed in this concept's region |
| `../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings for this feature |
| `../../../../../methodology/implementation/RULES.md` | 3 | Hard rule R2 |
| `../../../../../methodology/architecture/ORM_NOTES.md` | 3 | Seven-step drafting procedure (CLAD adaptation of Jarrar CSDP) |
| Profile reference docs (e.g. `reference-impl/<profile>/README.md`) | 3 | Storage conventions |

## Process

If the chosen profile uses a relational/RDF/document store, draft the
state schema for each concept by walking the seven-step procedure in
`ORM_NOTES.md` — one named region per concept (R2). Otherwise write
`_NOT_APPLICABLE.md` explaining why and skip.

Before writing any implementation-adjacent artefact, read
`../../../_config/package-and-layout.md` and confirm this feature's
`APP_PACKAGE_ROOT` and `APP_SOURCE_ROOT`. Treat reference-profile
package names as examples only.

## Outputs

- `output/<Name>.orm.md` per concept — the **profile-neutral conceptual
  model**: fact types with uniqueness and mandatory constraints from the
  CSDP walk (steps 1–6). Profile mapping notes go in `## CSDP Notes`.
  Do **not** write a relational `Field / Type / Constraints` table
  unless the profile is explicitly relational. **or**
- `output/_NOT_APPLICABLE.md` if the profile does not use a persistent store

## Verify

- Each concept's schema lives in exactly one named region.
- No region is shared across concepts.
- Every field listed in `03a_dependency-review/output/pattern-d-summary.md`
  is present in the owner concept's region.
- The `.orm.md` body describes fact types and constraints in
  profile-neutral terms. A relational schema table (`Field / Type /
  Constraints`) is only present if the profile is relational.
- Package/source-root decisions used by later implementation stages are
  sourced from `../../../_config/package-and-layout.md`, not inferred from
  `reference-impl/` paths.

## Gate

Default human approval.

## Next stage

→ [`../04b_spec/CONTEXT.md`](../04b_spec/CONTEXT.md) — Per-concept SPEC slice

To advance, the human says: **"Proceed to Stage 04b."**
