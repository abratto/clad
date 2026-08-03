<!-- See methodology/overlays/TRACKING.md for the conventions this file follows. -->

# Roadmap

> One row per phase. **Exactly one** phase has status `doing` at any time;
> everything else is `done`, `next`, or `later`. The `doing` phase points
> at the active feature folder under `features/`.
>
> CI enforces: at most one `doing` row, and a current `Resume point` block.
> See [`.github/scripts/check-roadmap-hygiene.sh`](.github/scripts/check-roadmap-hygiene.sh).

## Phases

| # | Phase | Feature(s) | Status | Notes |
|---|---|---|---|---|
| 1 | Seed methodology | `UC-00-login` | done | Worked example, end-to-end through Stage 04. |
| 2 | First real feature | `UC-01-<slug>` | next | Replace this row when you start your first feature. |

## Backlog

> Use cases identified but not yet promoted into a phase. Promote a row
> by moving it into the phases table and setting status to `doing`
> (and demoting the previous `doing` row to `done`).

- Production workload characterization — benchmark the predicate engine with a durable backend, realistic graph sizes and action chains, mixed read/write traffic, and sustained concurrency. Publish throughput, p50/p95/p99 latency, error rate, and the tested hardware/configuration; use the results to establish production workload expectations rather than a generic RPS claim.
- Legacy polling-engine scheduler hardening — deferred. The transactional predicate engine is the preferred path because it performs better and matches the WYSIWID sync semantics; revisit bounded polling, claims, and lease recovery only for legacy-engine users.

## Resume point

> Updated at the end of every working session.

- **Last gate passed:** `UC-00-login` Stage 05 (worked example shipped)
- **Next stage:** start `UC-01-<slug>` Stage 00 (actor/goal)
- **Blockers:** none
- **Last updated:** 2026-08-02 — added production workload characterization to establish realistic capacity expectations for the transactional predicate engine; legacy polling-engine scheduler hardening remains deferred.
