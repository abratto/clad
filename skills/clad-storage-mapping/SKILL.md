---
name: clad-storage-mapping
description: Map conceptual data models to a specific storage profile during CLAD Stage 04a. Use when producing storage mapping files for a selected persistence technology (RDF, relational, document), or marking as not applicable for in-memory profiles.
---

# CLAD Storage Mapping (Stage 04a)

## What this skill covers

Producing profile-specific storage mappings from the Stage 03b conceptual
data models. For profiles that use a persistent store, produce one
`<Name>.storage.md` per concept. For in-memory profiles, produce a
`_NOT_APPLICABLE.md` note and skip.

## Quick reference

Load these files:

1. `methodology/implementation/STORAGE_MAPPING.md` — storage mapping
   contract and rules
2. `templates/storage.md` — output shape (for persistent profiles)
3. `templates/storage-rdf-example.md` — RDF profile example
4. `features/UC-XX-<slug>/stages/03b_data-model/output/` —
   approved conceptual data models
5. `clad.properties` — `storage.layer` key
6. The current stage `CONTEXT.md` for exact Inputs/Outputs/Process

## Process

1. Read `storage.layer` from `clad.properties`.
2. If in-memory: write `_NOT_APPLICABLE.md` and stop.
3. Otherwise: for each concept, produce a storage mapping that declares
   how each state field maps to the profile's persistence primitive.
4. Auto-advance to Stage 04b.

## Hard constraints

- Storage mapping is profile-specific — do not re-derive the data model.
- Follow the technology declared in `clad.properties`, not a substitute.
- **Copy the engine; do not reimplement it.** If your project root does
  not yet contain the CLAD engine/runtime, copy it verbatim from the
  reference profile's `engine/` package (`ConceptAgent`, `SyncAgent`,
  `ActionLog`, `SyncDispatcher`, `FlowManager`, plus the ArchUnit rule
  test), changing only the package declaration to match
  `APP_PACKAGE_ROOT`. This is reusable infrastructure and the only
  execution profile shipped today — never author engine classes from
  scratch. See
  `features/UC-XX-<slug>/_config/package-and-layout.md` rule 6 and the
  reference profile README's copy-out command.
