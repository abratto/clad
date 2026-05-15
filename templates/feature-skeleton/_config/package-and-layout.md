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

## Java profile mapping hints

If using Java, typical paths are:

- Concepts: `<APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/concepts/<name>/`
- Syncs: `<APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/syncs/`
- HTTP entry: `<APP_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/infrastructure/`
- Concept tests: `<APP_TEST_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/concepts/<name>/`
- Sync tests: `<APP_TEST_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/syncs/`
- Flow tests: `<APP_TEST_SOURCE_ROOT>/<APP_PACKAGE_ROOT>/flows/`

Replace dots with path separators when mapping `APP_PACKAGE_ROOT`.