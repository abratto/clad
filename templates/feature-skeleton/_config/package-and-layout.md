# Package & layout (feature-scoped reference)

This file prevents agents from copying package/layout choices from the
reference implementation when they are not correct for this project.

## Required

- **APP_PACKAGE_ROOT:** `TBD`  
  Example: `org.acme.billing`
- **APP_SOURCE_ROOT:** `TBD`  
  Example: `src/main/java`
- **APP_TEST_SOURCE_ROOT:** `TBD`
  Example: `src/test/java`

## Optional

- **REFERENCE_PROFILE:** `TBD`  
  Example: `reference-impl/java-micronaut-jena`

## Rules

1. If `APP_PACKAGE_ROOT` is not `com.example.app`, do not generate code
   under `com.example.app`.
2. Place implementation files under `APP_SOURCE_ROOT` and package them
   under `APP_PACKAGE_ROOT`.
3. Place test files under `APP_TEST_SOURCE_ROOT` and package them under
  `APP_PACKAGE_ROOT`.
4. Use the reference profile for patterns and engine behavior, not for
   package names or source-root paths unless they match this file.
5. In a repository created from the CLAD template, do not use
  `reference-impl/<profile>/` as the long-term product code root.
  Copy starter code/patterns from the selected reference profile into
  your own app/runtime directory and point this file at those real
  package and source roots.
6. **Copy the engine; do not reimplement it.** The reference profile's
  `engine/` package (e.g. `ConceptAgent`, `SyncAgent`, `ActionLog`,
  `SyncDispatcher`, `FlowManager`) plus its ArchUnit rule test is
  reusable runtime infrastructure and the only execution profile shipped
  today. Copy those classes into `<APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/engine/`
  **verbatim**, changing only the package declaration to match
  `APP_PACKAGE_ROOT`. Never author engine/runtime classes from scratch
  when the reference profile already provides them. Only concepts, syncs,
  boundary DTOs, and the HTTP entry are written per feature.

## Java profile mapping hints

If using Java, typical paths are:

- API DTOs: `<APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/api/`
- Engine/runtime classes: `<APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/engine/`
- Concepts: `<APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/concepts/<name>/`
- Syncs: `<APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/syncs/`
- HTTP entry: `<APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/infrastructure/`
- Concept tests: `<APP_TEST_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/concepts/<name>/`
- Sync tests: `<APP_TEST_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/syncs/`
- Flow tests: `<APP_TEST_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/flows/`

Use those buckets as the default Java placement contract. If a class is
concept logic, it belongs under `concepts/<name>/`; if it is sync
coordination, it belongs under `syncs/`; if it is transport-only HTTP
code, it belongs under `infrastructure/`; if it is DTO-only boundary
shape, it belongs under `api/`; if it is shared runtime/dispatch
machinery, it belongs under `engine/`.

Replace dots with path separators when mapping `APP_PACKAGE_ROOT`.