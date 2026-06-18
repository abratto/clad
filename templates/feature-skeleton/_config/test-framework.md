# Test framework (profile hook)

This file declares the outer-loop test framework for this feature.
It determines whether Stage 04c produces Gherkin `.feature` files
or native markdown + test stubs.

## Global default

The project-wide default is set in `../../../../clad.properties` under
`test.framework`. This file overrides that default for this feature.

## Values

| Value | Meaning | 04c output |
|---|---|---|
| `CUCUMBER` | Profile supports Cucumber/Gherkin | `<feature>.feature` + step-definition skeletons |
| `NATIVE` | No Cucumber support, or opted out | `<scenario>-flow-test.md` + native test stub |

```
TEST_FRAMEWORK=CUCUMBER
```

## When to set this

Set it once when the feature skeleton is first copied. The choice is a
profile capability, not a per-scenario decision. Do not change it mid-
feature — the `04c` outputs will not match the profile's actual runner,
causing compilation failures at Stage 04e.

If your project's global default in `clad.properties` is already correct,
delete this file and the agent will use the global default.

## Resolution order

1. `clad.properties` (repo root) — global default
2. `features/UC-XX/_config/test-framework.md` — per-feature override

## Used by CLAD stages

- **04c**: selects which Process / Outputs / Verify track to follow.
- **04e**: validates that the selected track's artefacts are present at green time.
- **05**: adds Gherkin cross-references to the verification trace.
