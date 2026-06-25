# Stage 04a — Storage mapping (UC-00-login)

## Why this stage exists

For profiles with a persistent store, this is where each concept's
approved conceptual data model becomes a concrete storage mapping in its
own named region (hard rule R2).

In this feature the chosen profile is in-memory — see
[`output/_NOT_APPLICABLE.md`](output/_NOT_APPLICABLE.md). The CONTEXT
is kept so that, if the feature later gains a persistence profile, the
contract is already in place.

**Feeds:**

- `<Name>.storage.md` (or `_NOT_APPLICABLE.md`) → 04d (the test fixture builds against this mapping), and the runtime data layer in the profile.

**Agent stance for this stage:** if storage mapping reveals a missing
fact, fix Stage 03b first instead of inventing it here.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../03b_data-model/output/` | 4 | Approved conceptual data models |
| `../../../../../methodology/implementation/STORAGE_MAPPING.md` | 3 | Storage mapping procedure |
| `../../../../../templates/storage.md` | 3 | Default storage-mapping output shape |
| `../../../../../reference-impl/java-micronaut-jena/README.md` | 3 | Profile storage status |

## Process

The Java profile is currently **in-memory only**. No persistent-store
mapping is needed, even though Stage 03b still models the concepts
conceptually. Document the decision in `output/_NOT_APPLICABLE.md` and
move on.

## Outputs

- `output/_NOT_APPLICABLE.md`

## Verify

- The note explains why storage mapping is skipped and how R2 is
	satisfied without it.

## Gate

Auto-advances (next human gate: Stage 04c).

## Next stage

→ [`../04b_spec/CONTEXT.md`](../04b_spec/CONTEXT.md) — Per-concept SPEC slice

To advance, the human says: **"Proceed to Stage 04b."**
