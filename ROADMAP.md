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
| 1 | Seed methodology | `examples/UC-00-login` | done | Worked example, end-to-end; unbundled into `examples/` so `features/` is project workspace only. |
| 2 | First real feature | `UC-01-<slug>` | next | Replace this row when you start your first feature. |

## Backlog

> Use cases identified but not yet promoted into a phase. Promote a row
> by moving it into the phases table and setting status to `doing`
> (and demoting the previous `doing` row to `done`).

- Production workload characterization — benchmark the predicate engine with a durable backend, realistic graph sizes and action chains, mixed read/write traffic, and sustained concurrency. Publish throughput, p50/p95/p99 latency, error rate, and the tested hardware/configuration; use the results to establish production workload expectations rather than a generic RPS claim.
- Legacy polling-engine scheduler hardening — deferred. The transactional predicate engine is the preferred path because it performs better and matches the WYSIWID sync semantics; revisit bounded polling, claims, and lease recovery only for legacy-engine users.

## Done

- `java-micronaut` transport/storage split — Micronaut HTTP transport separated from the concept-state backend; `clad.storage=memory` (default) or `postgres` select the `FactStore` binding. See `maintenance/micronaut-transport-storage-split.md`.
- Jena backend demotion — removed the unshipped `JenaFactStore`; CLAD ships in-memory and Postgres, and RDF/SPARQL is a `FactStore` you implement. See `maintenance/jena-backend-demotion.md`.

## Resume point

> Updated at the end of every working session.

- **Last gate passed:** worked example shipped (`examples/UC-00-login` Stage 05)
- **Next stage:** start `UC-01-<slug>` Stage 00 (actor/goal)
- **Blockers:** none
- **Last updated:** 2026-09-24 — documented the ways of working (single session / one sub-agent per stage / session-per-stage) and reference-profile guidance; completed the `java-micronaut` transport/storage split and the Jena backend demotion.
