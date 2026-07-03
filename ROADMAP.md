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

- _(none yet — add `UC-XX-<slug> — <one-line summary>` lines as ideas land)_

## Resume point

> Updated at the end of every working session.

- **Last gate passed:** `UC-00-login` Stage 05 (worked example shipped)
- **Next stage:** start `UC-01-<slug>` Stage 00 (actor/goal)
- **Blockers:** none
- **Last updated:** 2026-07-03 — methodology maintenance: added canonical `When<Trigger>Then<Target>` sync naming and extended `verify_implementation_parity.py` to validate sync spec/header/class/runtime names mechanically. UC-00 sync specs and Java sync classes migrated to the rule-shaped names.
