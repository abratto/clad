# Stage 05 — Verify and close (UC-00-login)

## Why this stage exists

The **closing of the contract loop**. Stage 05 is the only place that
proves runtime behaviour matches the use case (Part 1, back-trace) and
that the deployable thing actually runs (Part 2, smoke). Without it,
*merged* is not *done* — and the next session has no resume-point.

**Feeds:**

- `trace.md` → the next feature's Stage 00 (the `Resume point:` line is the bridge between features).
- `findings.md` → upstream stage(s) — defects route **back**, never forward.
- `smoke.md` + `tracking.md` → the human (closure evidence).

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios |
| `../03_syncs/output/` | 4 | Authorising sync rules |
| `../04_implement/output/implementation-manifest.md` | 4 | What was built |
| (a flow-token log from a representative test run) | 4 | Runtime evidence |
| `../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics |
| `../../../../reference-impl/java-micronaut-jena/README.md` | 3 | Java runtime debug surface |

## Process

### Part 1 — Verify

Walk the flow-token tree for each scenario; check every token
back-traces to a sync or use-case scenario. Write
`output/verification-trace.md`. (UC-00 also keeps the older
`trace.md` filename around as the canonical name; this seed uses
`verification-trace.md` historically — both are acceptable.)

In this Java profile, the default runtime evidence surface is the debug
controller documented in the reference-impl README. Prefer
`/api/dev/flows` to confirm the registered sync plan,
`/api/dev/flow/{token}` to inspect one archived flow token,
`/api/dev/stuck` to rule out missing `:output`, and
`/api/dev/concept/{name}/triples` when concept state must be checked
alongside the trace.

### Part 2 — Close

1. Boot the Java profile, hit `POST /login` for each scenario,
   capture in `output/smoke.md`.
2. Update tracking (or note "not applicable") in `output/tracking.md`.
3. Add a `Resume point:` line at the top of the trace file.

## Outputs

- `output/verification-trace.md` (with `Resume point:` line at top)
- `output/findings.md` (only if violations found)
- `output/smoke.md`
- `output/tracking.md`

## Verify

- Every scenario has a trace entry.
- The trace is backed by captured runtime evidence from the Java debug
  endpoints or another executed runtime inspection command, not only by
  predicted test chains.
- `smoke.md` records a real (not predicted) curl/response per scenario.
- `tracking.md` exists.
- Trace file begins with `Resume point:`.
- **Cross-stage check (back):** every observed flow token back-traces
  to a use-case scenario.

## Gate

- Findings → loop back to owning stage.
- No further gate after closure.

## Next stage

**This is the final stage.** When the gate passes, the feature is complete.

To start the next feature, run system-scope Stage 00 at [`features/_system/stages/00_actor-goal/CONTEXT.md`](../../../../features/_system/stages/00_actor-goal/CONTEXT.md). After that gate passes, copy [`templates/feature-skeleton/`](../../../../templates/feature-skeleton/) to `features/UC-XX-<slug>/` and begin at `stages/01_usecase/CONTEXT.md`.
