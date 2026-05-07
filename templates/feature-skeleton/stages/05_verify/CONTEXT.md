# Stage 05 — Verify and close

This stage has two parts. **Verify** is the back-trace from runtime
flow tokens to the use case (this is what Stage 05 has always been).
**Close** is the deliberate hand-off — smoke the running instance,
update tracking, leave a resume-point — that prevents the feature
from going "done" implicitly the moment the PR merges.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios to verify against |
| `../03_syncs/output/` | 4 | Authorising sync rules |
| (a flow-token log from a representative test run) | 4 | Runtime evidence |
| `../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics |
| `../../../../methodology/overlays/TRACKING.md` | 3 | Optional — only if the TRACKING overlay is in use |

## Process

### Part 1 — Verify (back-trace)

For each named scenario in the use case:

1. Find the root flow token (the `Web.handle` matching the
   scenario's trigger).
2. Walk the parent-linked tree of children.
3. Check that the chain matches the syncs in `03_syncs/output/`.
4. Check that no action appears in the chain that is not authorised
   by either a use-case scenario or a sync.

Write a per-scenario walk to `output/trace.md`. If anything failed
step 3 or 4, add an entry to `output/findings.md` and mark which
earlier stage owns the defect — **do not proceed to closure** until
findings are resolved.

### Part 2 — Close

Once `trace.md` is clean and `findings.md` is empty (or absent), do
**all three** of the following:

1. **Smoke test the running instance.** Boot the profile (e.g.
   `mvn exec:java` for the Java profile), exercise each scenario's
   trigger by hand or with a small script, and confirm the response
   matches the use case. Capture the commands and observed responses
   in `output/smoke.md`. This is the only step that proves the
   *deployable* artefact, not just the test suite, behaves.
2. **Update tracking** (if the TRACKING overlay is in use). Move the
   roadmap entry from `doing` to `done`; relabel the issue/PR
   `clad:done`; close the issue if appropriate. If the TRACKING
   overlay is not in use, write `output/tracking.md` containing the
   single line `Not applicable — TRACKING overlay not in use.`
3. **Leave a resume-point.** Append a one-line `Resume point:` entry
   to the top of `output/trace.md` describing the next reasonable
   piece of work (typically the next feature, the next iterative
   change, or "no follow-up planned"). The next session's first read
   should land on it.

## Outputs

- `output/trace.md` — per-scenario verification walk; **also**
  carries the resume-point line at the top
- `output/findings.md` — only if Part 1 found violations
- `output/smoke.md` — recorded smoke run (Part 2.1)
- `output/tracking.md` — closure note (Part 2.2)

## Verify

- Every scenario has an entry in `trace.md`.
- `findings.md`, if present, names the owning stage for each finding.
- `smoke.md` exists and contains a real (not predicted) command +
  response per scenario.
- `tracking.md` exists, even if only to record that no overlay is in
  use.
- `trace.md` begins with a `Resume point:` line.
- **Cross-stage check (back):** every flow token observed at runtime
  back-traces to a use-case scenario.

## Gate

- Any verify-stage finding sends the loop back to whichever stage
  owns the defect; closure does not run until findings are clear.
- Closure has no further gate — once smoke, tracking, and resume-
  point are written, the feature is done.
