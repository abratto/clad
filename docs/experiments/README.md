# Experiments

Worked, end-to-end trials of CLAD on a real app, kept as evidence. An
experiment is not a tutorial (those live under `examples/`) and not a
methodology spec (that lives under `methodology/`); it is a record of what
happened when the methodology met a non-trivial problem, including the defects
it exposed and the platform fixes that followed.

## Index

| Report | What it exercises | Status |
|---|---|---|
| [`expense-approvals.md`](expense-approvals.md) | Full loop (stages 00–05) on a multi-actor HTTP service, then an iterative change; one sub-agent per stage, a human reviewing every gate | Complete; the experimental app was removed from the seed, the platform fixes remain |
| [`bookings-friction.md`](bookings-friction.md) | Full loop (stages 00–05) on a 3-UC room-booking app (Java/Micronaut/Postgres) plus two iterative changes (a state-field extension and a behaviour refusal); one sub-agent per stage, the orchestrator reviewing every gate | Complete; fixes ported as v0.30.0 |

## Retention policy

- **Keep the finding, drop the scaffolding.** When an experiment finishes, its
  throwaway app (`features/UC-*`, `reference-impl/<app>`) is removed from the
  seed; the report stays as the durable record of what broke and what changed.
- **The report is historical.** Paths and commands in a report describe the tree
  *at the time of the experiment*. They are not maintained against later renames;
  the `## Disposition` note at the top of each report says so.
- **Fix-forward.** A defect an experiment exposes is fixed in the platform (a
  rule, a checker, a stage contract), not just noted here. The report links the
  fix; the fix is proven by the test suite, not by the report.
- **No silent edits.** Do not rewrite a past experiment's findings to match a
  later architecture. Add a dated addendum instead.
