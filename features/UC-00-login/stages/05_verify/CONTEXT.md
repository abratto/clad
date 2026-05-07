# Stage 05 — Verify

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios to verify against |
| `../03_syncs/output/` | 4 | Authorising sync rules |
| `../04_implement/output/implementation-manifest.md` | 4 | What was built |
| (a flow-token log from a representative test run) | 4 | Runtime evidence |
| `../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics |

## Process

For each named scenario in the use case:

1. Find the root flow token (the `Web.handle` call matching the
   scenario's trigger).
2. Walk the parent-linked tree of children.
3. Check that the chain matches the syncs in `03_syncs/output/`.
4. Check that no action appears in the chain that is not authorised
   by either a use-case scenario or a sync.

Write a per-scenario walk to `trace.md`. If anything failed step 3 or
4, add an entry to `findings.md` and mark which earlier stage owns the
defect.

## Outputs

- `output/trace.md` — per-scenario walk
- `output/findings.md` — only if violations were found

## Verify

- Every scenario has an entry in `trace.md`.
- `findings.md`, if present, names the owning stage for each finding.

## Status in this seed

`output/` is intentionally empty. This stage runs against a live test
execution; without an implementation in `04_implement/`, there is
nothing to walk yet.
