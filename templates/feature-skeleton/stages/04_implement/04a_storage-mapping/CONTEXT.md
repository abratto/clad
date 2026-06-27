# Stage 04a — Storage mapping (optional)

## Pre-condition (agent must verify before starting)

Run the following **before** writing any artefacts for this stage:

```
python3 ../../../../../quality-gate/verify_gate_approval.py \
  --feature ../../../ \
  --required-gates 2
```

If this script exits with a non-zero status, stop immediately.
Gate 2 has not been approved — do not proceed.

## Why this stage exists

For profiles with a persistent store, this is where each concept's
approved conceptual data model becomes a **profile-specific storage
mapping** in its own named region (hard rule R2 — no concept reads
another's region directly). This stage no longer decides the fact model;
it only realizes the approved one in RDF, SQL, document storage, or an
equivalent profile mechanism.

**Feeds:**

- `<Name>.storage.md` → 04d (the test fixture builds against this mapping), and the runtime data layer in the profile.
- `_NOT_APPLICABLE.md` → a record that this stage was consciously skipped (e.g. for an in-memory profile).

**Agent stance for this stage:** if a required fact is missing from the
approved data model, do not add it here "to make the storage work" — go
back to Stage 03b and repair the conceptual model first.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../03b_data-model/output/` | 4 | Approved conceptual data models |
| `../../../_config/package-and-layout.md` | 3 | Canonical package/source-root settings for this feature |
| Skill: `clad-storage-mapping` | 3 | Storage mapping reference (see skills/ directory) |
| `../../../../../methodology/implementation/RULES.md` | 3 | Hard rule R2 |
| `../../../../../methodology/implementation/STORAGE_MAPPING.md` | 3 | Profile mapping procedure |
| `../../../../../templates/storage.md` | 3 | Default storage-mapping output shape |
| Profile reference docs (e.g. `reference-impl/<profile>/README.md`) | 3 | Storage conventions |

## Process

If the chosen profile uses a relational/RDF/document store, map each
approved conceptual data model into the selected profile's storage
primitives by following `STORAGE_MAPPING.md` — one named region per
concept (R2). Otherwise write `_NOT_APPLICABLE.md` explaining why and
skip.

Every storage field, property, or region-level structure must trace 1:1
to an approved fact or constraint in `../../03b_data-model/output/`. Do
not add helper fields, indexes-as-design, lifecycle concepts, or
commentary that is not present upstream.

For RDF / named-graph profiles, the `.storage.md` output must name:

- the concept's graph URI
- the subject-IRI rule for each entity type
- the literal/datatype rule for each value type
- the predicate used for each approved fact type
- whether each approved constraint is enforced by SHACL, code/tests, or
  explicitly not enforced in the storage layer

Do not treat `rdfs:domain`, `rdfs:range`, or OWL axioms as required
outputs unless the selected profile explicitly carries ontology
metadata. They are optional metadata, not the default storage contract.

Before writing any implementation-adjacent artefact, read
`../../../_config/package-and-layout.md` and confirm this feature's
`APP_PACKAGE_ROOT` and `APP_SOURCE_ROOT`. Treat reference-profile
package names as examples only.

## Outputs

- `output/<Name>.storage.md` per concept — the profile-specific storage
  realization of the approved conceptual data model. **or**
- `output/_NOT_APPLICABLE.md` if the profile does not use a persistent store

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<Name>.storage.md,…"  # one per concept, or _NOT_APPLICABLE.md
```

- **verify_file_manifest.py:** `output/` contains exactly one
  `.storage.md` per concept or a single `_NOT_APPLICABLE.md`.

### Semantic checks (human)

- Each concept's storage mapping lives in exactly one named region.
- No region is shared across concepts.
- Every mapped fact or constraint in a `.storage.md` file traces back to
  an approved `.data-model.md` file.
- No new fact type, status, default, or region structure is introduced
  during mapping.
- For RDF mappings, entity IRIs, literal typing, predicate choice, and
  constraint-enforcement surface are all stated explicitly.
- Package/source-root decisions used by later implementation stages are
  sourced from `../../../_config/package-and-layout.md`, not inferred from
  `reference-impl/` paths.

## Gate

Auto-advances (next human gate: Stage 04c). The `verify_file_manifest.py` script
must pass before advancing.

## Next stage

→ [`../04b_spec/CONTEXT.md`](../04b_spec/CONTEXT.md) — Per-concept SPEC slice

The agent proceeds to Stage 04b without a human gate.
