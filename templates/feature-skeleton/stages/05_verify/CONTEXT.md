# Stage 05 — Verify and close

## Pre-condition

`advance.py` enforces stage order and upstream gate approval before this
stage runs — see `STAGES.md` §"Stage lifecycle (standard)". Do not start
until it has printed this stage as `NEXT STAGE`.

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
| `../01_usecase/output/usecase.md` | 4 | Scenarios to verify against |
| `../03_syncs/output/` | 4 | Authorising sync rules |
| `../04_implement/04c_flow-tests/output/` | 4 | Outer test specs for cross-reference (.feature or markdown) |
| (a flow-token log from a representative test run) | 4 | Runtime evidence |
| (Cucumber HTML/JSON report, Gherkin track only) | 4 | Supplementary scenario-pass evidence |
| Skill: `clad-verification` | 3 | Verification reference (see skills/ directory) |
| `../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics |
| `../../../../reference-impl/java-legible/README.md` (default profile) | 3 | Runtime evidence surface for the canonical fire-after-commit profile (`DebugApi`, archived flow records) |
| `../../../../methodology/overlays/TRACKING.md` | 3 | Optional — only if the TRACKING overlay is in use |

## Process

### Part 1 — Verify (back-trace)

For each named scenario in the use case:

1. Find the root flow token (the `Web.request` matching the
   scenario's trigger).
2. Walk the parent-linked tree of children.
3. Check that the chain matches the syncs in `03_syncs/output/`.
4. Check that no action appears in the chain that is not authorised
   by either a use-case scenario or a sync.
5. Check that the runtime chain actually crossed the bootstrap
   boundary the right way: transport entry -> authorised concept/sync
   chain -> transport exit, rather than being short-circuited inside the
   controller / route handler.

On the Gherkin track, additionally cross-reference:
   - Every Gherkin `Scenario` / `Scenario Outline` name in
     `../04_implement/04c_flow-tests/output/*.feature` matches a
     use-case scenario name in `../01_usecase/output/usecase.md`.
   - Every scenario's trace entry references its Gherkin scenario
     name and line number alongside the use-case heading.

When the selected profile exposes a read-oriented runtime debug surface,
use that surface as the default proof source for the walk before you
write `trace.md`. For the Java reference profile, prefer `/api/dev/flows`
to confirm the registered sync plan, `/api/dev/flow/{token}` to inspect
the archived action history for one flow token, `/api/dev/stuck` to rule
out missing `:output`, and `/api/dev/concept/{name}/triples` when you
need to verify concept state alongside the flow trace.

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
4. **Close the RESUME.** Set `RESUME.md`'s `Current stage` line to
   `None — feature complete` (and its status accordingly). The
   `./clad` active-feature heuristic treats a RESUME that names any
   stage as in progress, so a feature left at `Stage 04c — …` can
   outrank a genuinely live one — and a command that writes (promotion
   replaces corpus entries) can then target the stale feature and
   overwrite newer content with its older proposal.
   `verify_close_evidence.py` warns when a closed feature still
   advertises a live stage.


## Progress checklist

- [ ] Flow tokens back-traced to use-case scenarios
- [ ] Every scenario marked covered/partial/missing
- [ ] Deployable artefact smoke-tested
- [ ] `trace.md`, `findings.md`, `smoke.md`, `tracking.md` produced
- [ ] Self-audit: `./clad verify` passes
## Outputs

- `output/trace.md` — per-scenario verification walk; **also**
  carries the resume-point line at the top
- `output/findings.md` — only if Part 1 found violations
- `output/smoke.md` — recorded smoke run (Part 2.1)
- `output/tracking.md` — closure note (Part 2.2)

## Verify

Automated close-evidence self-audit (advisory — warnings, never blocks):

```
python3 ../../../../quality-gate/verify_close_evidence.py \
  --feature-root ../.. \
  --test-source-root <APP_TEST_SOURCE_ROOT>
```

- Confirms `trace.md` (the canonical name) is present and warns on the legacy
  `verification-trace.md`.
- Warns when an adapter surface is declared but no enabled flow/integration
  test exists. This makes the "required, not optional" integration test
  visible to `advance`/`./clad verify`; it is advisory because there is no
  reliable profile-agnostic definition of that test.

- Every scenario has an entry in `trace.md`.
- `findings.md`, if present, names the owning stage for each finding.
- `trace.md` is backed by captured runtime evidence from the profile's
  debug surface or equivalent executed inspection commands, not only by
  predicted test chains.
- The captured runtime evidence shows that transport entry and exit were
  reached through the authorised action/sync chain, not by imperative
  controller branching.
- `smoke.md` exists and contains a real (not predicted) command +
  response per scenario.
- `tracking.md` exists, even if only to record that no overlay is in
  use.
- `trace.md` begins with a `Resume point:` line.
- **Adapter-surface integration test:** features exposing any adapter
  surface (HTTP, CLI, GraphQL, pub/sub) **must** carry a profile-specific
  integration test that exercises that surface end-to-end (response shape
  + state round-tripping). Derived alongside the 04c flow tests. Required,
  not optional. Distinct from Gherkin flow tests (action token chain).
  A *failing* integration test blocks the build (`mvn test`); a *missing*
  one is surfaced as a warning by `verify_close_evidence.py` (above) and
  confirmed by this human checklist.
- **Cross-stage check (back):** every flow token observed at runtime
  back-traces to a use-case scenario.

### Gherkin/Cucumber coverage

- Every Gherkin scenario name in
  `../04_implement/04c_flow-tests/output/*.feature` appears as a
  heading or cross-reference in `trace.md`.
- The Cucumber report (if present) shows 0 failed scenarios for the
  scenarios exercised in `smoke.md`.
- The Gherkin scenarios provide no additional coverage beyond what the
  use case already defines — they are a derived view, not a new
  contract.

## Gate

Auto-closes. The agent runs verification scripts, records results
in trace.md, smoke.md, and tracking.md. No human gate required —
the human inspects the results at their convenience.

Any verify-stage finding in trace.md sends the loop back to whichever
stage owns the defect; closure does not run until findings are clear.

## Advancing

> **This is the final stage.** When verification passes, the feature is
> complete. `advance.py` auto-closes the loop; there is no next stage.
>
> To start the next feature, run system-scope Stage 00 at
> [`features/_system/stages/00_actor-goal/CONTEXT.md`](../../../../features/_system/stages/00_actor-goal/CONTEXT.md).
> After that gate passes, copy
> [`templates/feature-skeleton/`](../../../../templates/feature-skeleton/)
> to `features/UC-XX-<slug>/` and begin at
> `stages/01_usecase/CONTEXT.md`.
