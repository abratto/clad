# Feature-scoped reference (_config)

This folder holds **Layer-3, feature-scoped reference** material: conventions that apply inside this feature and should not be re-decided during Stages 02–05.

## Files

- `voice.md` — wording/tone and domain glossary for user-visible text.
- `build-and-test.md` — the canonical command(s) to build and run tests for this repo/profile.
  - Used to support Stage 04c/04d/04e requirements that “red” and “green” claims include executed evidence.
- `package-and-layout.md` — canonical source-root and package-root settings.
  - Used by Stage 04 implementation work to avoid copying reference-profile
    package names (for example `com.example.app`) into downstream projects.
- `test-framework.md` — declares whether the outer loop uses Cucumber/Gherkin
  or the profile-native test framework.
  - Used by Stage 04c to select the outer-red test format (`.feature` vs markdown spec).
