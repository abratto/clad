# Feature-scoped reference (_config)

This folder holds **Layer-3, feature-scoped reference** material: conventions that apply inside this feature and should not be re-decided during Stages 02–05.

## Files

- `voice.md` — wording/tone and domain glossary for user-visible text.
- `build-and-test.md` — the canonical command(s) to build and run tests for this repo/profile.
  - Used to support Stage 04c/04d/04e requirements that "red" and "green" claims include executed evidence.
- `package-and-layout.md` — canonical source-root and package-root settings.
  - Used by Stage 04 implementation work to avoid copying reference-profile
    package names (for example `com.example.app`) into downstream projects.

Stage 04c uses Cucumber/BDD (Gherkin `.feature` files + step definitions)
for outer-red flow tests — see `methodology/architecture/GHERKIN_INTEGRATION.md`.

If `features/_system/stages/00_actor-goal/output/port-spec.md` exists,
every Stage 04b and Stage 04c `CONTEXT.md` Inputs table must list it as
a required Layer-4 input. Stage 04b uses it for exact response shapes;
Stage 04c uses it for `@contract` scenarios.
