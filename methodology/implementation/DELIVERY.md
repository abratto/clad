# Delivery — trunk-based, continuously deliverable

CLAD governs **what changes** and **what shape they take**. This file
governs **how those changes land** — the merge-gate counterpart to
[`QUALITY_GATE.md`](QUALITY_GATE.md), which governs the local
pre-commit gate.

The two together implement the Continuous Delivery posture: every
commit on `main` is releasable, every PR is small enough to review in
one sitting, and the methodology's hard rules are enforced by
machines, not memory.

---

## 1. Posture

1. **Trunk-based development.** `main` is the only long-lived branch.
   Every change lands on `main` via a short-lived branch (≤ 1–2 days
   of work).
2. **One PR, one change.** A PR is either *one new feature*
   (one `features/UC-XX-<slug>/` folder taken from Stage 00 to Stage
   05) or *one iterative change* (per
   [`../core/ITERATIVE_CHANGES.md`](../core/ITERATIVE_CHANGES.md))
   or *one focused methodology edit*. Do not bundle.
3. **Every commit on `main` is releasable.** Tests green, hard rules
   enforced, smoke artefact (where applicable) passes.
4. **CI is the gate, not a hint.** A red check blocks merge. Local
   `QUALITY_GATE.md` checks are the developer's mirror of CI; CI is
   authoritative.
5. **Squash-merge.** One PR collapses to one commit on `main`. The
   per-stage history of a feature lives in the *artefacts* (the
   `stages/NN_*/output/` files), not in the git log.

## 2. Branch naming

| Kind | Pattern | Example |
|---|---|---|
| New feature | `feat/UC-XX-<slug>` | `feat/UC-03-password-reset` |
| Iterative change | `change/UC-XX-<slug>` | `change/UC-00-lockout-threshold` |
| Methodology / docs | `docs/<topic>` | `docs/sync-patterns-clarify-d` |
| Reference-impl only | `impl/<profile>-<topic>` | `impl/java-arch-rule-r2` |
| Repo hygiene | `chore/<topic>` | `chore/upgrade-spotless` |

A branch lives until its PR merges or is closed — typically hours,
not weeks. If a branch lasts longer than two days, split the work or
rebase frequently.

## 3. Branch lifecycle

Create the feature branch **before** writing any Stage 01 output to the
repo — the branch must exist before the first `git add` of feature
artefacts. Do not commit artefacts directly to `main`.

**Commit cadence:** one commit per gate approval on the branch. After the
human approves a stage's output, commit all that stage's output files in
a single commit using the message convention:

```
feat(UC-XX): Stage NN — <artefact name>
```

Example commit sequence for a feature (one commit per gate):

```
feat(UC-01): Gate 1 — requirements (stages 01–02b)
feat(UC-01): Gate 2 — architecture (stages 02–03b)
feat(UC-01): Gate 3 — executable (stages 04a–04c)
```

The branch squash-merges to `main` as a single commit at the end of
Stage 05. The per-stage history lives on the branch, not on `main`. If a
stage produces multiple output files (e.g. Stage 02 concepts + catalog
entry), include them all in one commit for that gate.

`RESUME.md` is a required per-gate artefact for feature branches and
is included in each gate-approved commit alongside the stage outputs
(see [HANDOVER.md](HANDOVER.md) for the read protocol).

## 4. The CI surface (what `main` requires)

The repository's GitHub Actions workflow
[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) runs the
following on every PR. Each maps to a CLAD invariant.

| Check | Enforces | Where |
|---|---|---|
| Markdown link check | No broken cross-stage links | `methodology/`, `features/`, root `*.md` |
| Concept-import grep (R1) | No `import` across `concepts.<X>.<Y>` packages | `reference-impl/**/src/main/java/**` |
| Tracking hygiene (overlay) | At most one `doing` phase + fresh resume point | `ROADMAP.md` (skipped if absent) |
| `mvn verify` (when Java profile changed) | Format, lint, unit + integration tests, ArchUnit hard-rule tests | `reference-impl/java-micronaut-jena/` |
| Stage-output edit guard (advisory) | Edits to `stages/NN_*/output/` come from re-running the stage, not freelance edits | warning only — humans judge in review |

CI is intentionally short. Add a check only when the *cost* of a
violation reaching `main` is higher than the *cost* of the check
running on every PR.

### Contract tests

When `port-spec.md` exists, CI must include a contract test stage that:

1. Starts the assembled application (same as the smoke test stage).
2. Runs the external contract test suite (e.g. Hurl files, Postman
   collection, or custom HTTP client tests) against the live HTTP
   surface.
3. Fails the build if any contract assertion fails.

Contract tests run **after** unit and flow tests and **after** the smoke
stage confirms the application starts. They are the outermost ring of
the test pyramid.

A contract test failure indicates an adapter problem (wrong
serialization, missing field, wrong error envelope). A flow test failure
indicates a behaviour problem (wrong outcome, wrong state transition).
These failures have different owners and different fixes; keeping the
tiers separate preserves that distinction.

## 5. Branch protection (`main`)

Settings to enable on the GitHub repo (one-time, repo admin):

- **Require a pull request before merging.**
  - Require **1** approving review.
  - Dismiss stale reviews on new commits.
- **Require status checks to pass before merging.**
  - Required: every job in `ci.yml`.
  - Require branches to be up-to-date before merging (forces rebase /
    update branch when `main` advances).
- **Require linear history.** (Pairs with squash-merge.)
- **Disallow force-pushes** to `main`.
- **Disallow deletions** of `main`.

The exact toggles live under *Settings → Rules → Rulesets* on the
GitHub repo. They are not in this file because git itself does not
host them; the file is the spec, the GitHub UI is the implementation.

## 6. PR review checklist

A reviewer reads the PR against these:

1. **Is this one change?** A new feature, an iterative change, or a
   methodology/docs edit — not a mix.
2. **For features:** does each stage's `output/` derive from the
   inputs declared in its `CONTEXT.md`? Is the `Verify` block in each
   stage actually verified?
3. **For iterative changes:** does the PR include the artefact-impact
   matrix (or its equivalent), and does the re-derivation order match
   the change category (per `ITERATIVE_CHANGES.md` §2)? Do
   `verify_iterative_change_readiness.py` and
   `verify_iterative_change_coupling.py` pass for the diff?
4. **Hard rules.** No cross-concept imports, no imperative branching
   in syncs, no second bootstrap concept. CI catches the first; the
   reviewer catches the rest.
5. **Diff hygiene.** No noise: no formatter-only churn outside the
   stated scope, no IDE files, no committed `target/`.

A green CI is necessary, not sufficient. Approval is the human
half of the gate.

## 7. Anti-patterns

- **Long-lived feature branches** that accumulate two or three
  features. Always split.
- **Merging your own PR without review.** The methodology depends on
  a second pair of eyes at the gate.
- **Bypassing CI** with `--no-verify`, admin merge, or
  branch-protection overrides. If a check is wrong, fix the check or
  open an issue to remove it; do not route around it.
- **"Just one tiny fix" follow-up commits to `main`.** They go
  through the same loop: branch → PR → CI → review → merge.

## 8. Pointers

- Local pre-commit gate: [`QUALITY_GATE.md`](QUALITY_GATE.md)
- Hard rules CI enforces: [`RULES.md`](RULES.md)
- Iterative-change workflow: [`../core/ITERATIVE_CHANGES.md`](../core/ITERATIVE_CHANGES.md)
- Branch & PR conventions in this repo: [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md)
