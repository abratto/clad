# Stage 05 — Verify and close (UC-00-login)

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../01_usecase/output/usecase.md` | 4 | Scenarios |
| `../03_syncs/output/` | 4 | Authorising sync rules |
| `../04_implement/output/implementation-manifest.md` | 4 | What was built |
| (a flow-token log from a representative test run) | 4 | Runtime evidence |
| `../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics |

## Process

### Part 1 — Verify

Walk the flow-token tree for each scenario; check every token
back-traces to a sync or use-case scenario. Write
`output/verification-trace.md`. (UC-00 also keeps the older
`trace.md` filename around as the canonical name; this seed uses
`verification-trace.md` historically — both are acceptable.)

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
- `smoke.md` records a real (not predicted) curl/response per scenario.
- `tracking.md` exists.
- Trace file begins with `Resume point:`.
- **Cross-stage check (back):** every observed flow token back-traces
  to a use-case scenario.

## Gate

- Findings → loop back to owning stage.
- No further gate after closure.
