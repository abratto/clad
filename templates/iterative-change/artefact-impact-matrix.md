<!-- Template for iterative-change artefacts. Copy this file into
     features/UC-XX-<slug>/_changes/<change-name>.md and fill in the fields.
     See methodology/core/ITERATIVE_CHANGES.md for the re-entry workflow. -->

# `<change-name>` — iterative change

- **Change category:** `presentation` | `behavioural` | `structural`
- **Earliest re-entry stage:** `01` | `01a` | `01b` | `02` | `03` | `03a` | `03b` | `04a` | `04b` | `04c` | `04d` | `04e`
- **Why:** <one sentence describing what changed and why>

This change is governed by `methodology/core/ITERATIVE_CHANGES.md`.

## Artefact-impact matrix

| Artefact | Touched? | How |
|---|---|---|
| Concept(s) | `yes` / `no` | <e.g. "added `hostFirm` field to `User.concept.md`"> |
| Sync(s) | `yes` / `no` | <e.g. "new `WhenUserLookupByUsernameFoundThenInterceptForSpillover.sync.md`"> |
| SPEC slices | `yes` / `no` | <e.g. "regenerated `User.spec.md`"> |
| Flow tests | `yes` / `no` | <e.g. "added `spillover.feature` scenario"> |
| Concept tests | `yes` / `no` | <e.g. "added `UserLookupTest.shouldReturnHostFirm`"> |
| Sync tests | `yes` / `no` | <e.g. "added `WhenUserLookup...InterceptTest`"> |
| Production code | `yes` / `no` | <e.g. "`UserConcept.java` updated; new `SpilloverSync.java`"> |

## Re-derivation order

1. <step — e.g. "Re-open Stage 02 and update `User.concept.md`">
2. <step — e.g. "Re-open Stage 03 and add new sync spec">
3. <step — e.g. "Re-open Stage 04b and regenerate SPECs">
4. <step — e.g. "Re-open Stage 04c and add flow test scenario">
5. <step — e.g. "Re-open Stage 04d and implement concept changes">
6. <step — e.g. "Re-open Stage 04e and implement sync + close flow tests">

---

*This file was produced by the CLAD iterative-change workflow.*
*All work to satisfy this change must be committed together with the*
*corresponding stage output and implementation changes.*
