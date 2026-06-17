# Test framework (profile hook)

This file declares the outer-loop test framework for this feature.
It determines whether Stage 04c produces Gherkin `.feature` files
or native markdown + test stubs.

## Declaration

Set `TEST_FRAMEWORK` to one of:

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

## Used by CLAD stages

- **04c**: selects which Process / Outputs / Verify track to follow.
- **04e**: validates that the selected track's artefacts are present at green time.
- **05**: adds Gherkin cross-references to the verification trace.
