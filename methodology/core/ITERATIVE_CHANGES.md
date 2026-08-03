# Iterative changes — when not to re-run 00→05

CLAD's stage pipeline is designed for *new* features. Once a feature
is green, most subsequent work is **iterative**: small changes that
re-enter the pipeline at one stage instead of starting from zero.

This file is the workflow doc for those changes. It answers three
questions an agent should be able to answer **before** touching a
file: *what kind of change is this?*, *which stages does it
re-enter?*, *what is the smallest set of artefacts that must change?*

The artefact-impact-matrix template
([`../../templates/artefact-impact-matrix.md`](../../templates/artefact-impact-matrix.md))
is the worksheet for this conversation; this file is the rulebook.

---

## 1. Classify the change

Before editing anything, decide which of three categories the change
belongs to. The category determines which stages re-enter.

### Presentation change

A change to **what the user sees or hears** that does **not** alter
which actions fire, in which order, with which outcomes.

Examples:
- Reword a `Web.respond` body.
- Change the colour of a button (front-end only).
- Add a translation.
- Tighten a regex on input validation that still produces the same
  outcomes.

### Behavioural change

A change to **what the system does** for the same input — different
outcomes, different action chains, different state transitions —
that does **not** introduce a new concept or remove an existing one.

Examples:
- Add a "remember me" toggle that extends `Session.grant` with a
  `ttl` argument.
- Change the lockout threshold from 5 to 3 attempts.
- Add a new outcome (`PendingTwoFactor`) to an existing action.
- Replace one sync's `then` clause with a different action on the
  same concept.

### Structural change

A change to **the concept set** itself — adding a new concept,
removing one, splitting one in two, merging two.

Examples:
- Extract `LoginAttemptHistory` from `PasswordAuth`.
- Add a `Mailer` concept for password-reset emails.
- Replace `PasswordAuth` with `WebAuthn`.

---

## 2. Pick the re-entry stage

| Change category | Earliest stage that re-enters | Why |
|---|---|---|
| Presentation | Stage 04 sub-stage(s) only | The use case, concepts, and syncs are unchanged; only test text and code text move |
| Behavioural | Stage 02 (concepts) **or** Stage 03 (syncs), whichever owns the change | If outcomes change → Stage 02; if only the chain of actions changes → Stage 03 |
| Structural | Stage 01a (responsibility map) | The concept set itself is changing, so the map is no longer accurate |

**Rule of thumb.** Find the *earliest* stage whose `output/` is no
longer accurate after the change. Re-enter there. Re-running an
earlier stage when its output is still accurate is over-production
and should be avoided.

You **never** re-enter Stage 00 (actors/goals) for an iterative
change. If you would, the change is a new feature: create
`features/UC-XY-<slug>/` and start fresh.

---

## 3. Fill in the impact matrix

Open
[`../../templates/artefact-impact-matrix.md`](../../templates/artefact-impact-matrix.md)
and copy it into a working location (e.g. a PR description, a session
note, or `features/UC-XX/_change-<slug>.md` if you want it on disk).

For every artefact category, mark **touched / not touched** and a
one-line *how*. Anything marked *touched* must be re-derived from its
predecessor stage — not edited in isolation. This is what preserves
ICM's reversibility property: a downstream stage cannot silently
drift from upstream.

The matrix's *Re-derivation order* section is the agent's plan. List
the stages in execution order; gate after each.

When records are kept under a feature's `_changes/` directory, exactly one
record for in-progress work must have `**Status:** active`. Mark historical
records `closed` or `superseded`; quality gates select the active record and
do not treat historical records as competing matrices.

---

## 4. Run the re-entry loop

For each stage in the re-derivation order, in order:

1. Open that stage's `CONTEXT.md`.
2. Re-read its `Inputs`. *Treat any human edits to upstream output as
   authoritative.*
3. Produce the new `output/` — overwrite where the change applies,
   leave the rest untouched.
4. Stop at the gate. **Do you agree with this step? Any corrections
   before I continue?**

The standard rejection protocol applies (see
[`../../AGENTS.md`](../../AGENTS.md) §"Rejection protocol"):
acknowledge what was rejected, ask one targeted clarifying question,
re-run the same stage. Never silently advance.

---

## 5. Anti-patterns

Things agents tend to do on iterative changes that they should not:

- **Re-run the whole pipeline for a one-line tweak.** A
  presentation-only change does not require a new responsibility map.
- **Edit late-stage artefacts in isolation.** If a sync changes,
  Stage 03's output changes. Editing only the Java sync class drifts
  the spec from the code.
- **Quietly add a new concept inside Stage 03 or 04.** A new concept
  is a structural change; it must re-enter at Stage 01a so the human
  can review the new concept set before any sync depends on it.
- **Skip the impact matrix because the change "feels small".** The
  matrix is a few minutes; it is also where the human catches things
  the agent missed.

---

## 6. When in doubt

If you cannot decide between two categories, take the **larger** one.
Doing one extra stage of review is cheaper than discovering, three
stages downstream, that the change was structural after all.

---

## 7. Platform maintenance changes

The feature pipeline governs the domain contract: actors, use cases,
concepts, syncs, and their observable action chains. Engine, scheduler,
storage, deployment, and profile-configuration changes may preserve that
contract while changing how it is realised. They use the maintenance route,
not a fabricated UC pipeline.

### Route the change

| Change | Route |
|---|---|
| Changes outcomes, response shape, concept boundaries, sync rules, or observable action order | Existing iterative route: re-enter the earliest owning feature stage |
| Changes an engine/profile/deployment implementation while preserving those properties | Maintenance route |
| Changes a primary or secondary adapter implementation while preserving its declared port contract and observable semantics | Maintenance route plus adapter-boundary tests |
| Changes a port contract, timeout interpretation, retry/idempotency, ordering, delivery guarantee, or other observable adapter semantics | Existing iterative route: re-enter at the earliest owning concept or sync stage |
| Changes both | Split the work where possible; otherwise run the maintenance route and re-enter the earliest affected feature stage |

### Maintenance route

1. Copy `templates/maintenance-change.md` to `maintenance/<change-name>.md`.
2. Record the runtime invariant, feature-contract impact, affected surfaces,
  rollback boundary, and test matrix. Leave its status as `draft` while the
  design gate is pending.
3. Present the **design gate** for human approval. Do not modify an
  engine/profile/configuration/deployment implementation until the design
  gate is approved with `./clad approve-maintenance <change-name> design`.
4. After approval, set the record status to `active`. Write focused tests before
  implementation. Preserve existing flow tests as
  the regression oracle for the feature contract.
5. Implement the smallest change that satisfies the approved invariants.
6. Run the profile gate, the completed test matrix, and applicable smoke
  evidence. Present the **evidence gate** for human approval.
7. Record the evidence approval, set the record status to `closed`, and commit
  the record with the implementation.

`verify_maintenance_change_readiness.py` enforces the design gate before
tests run and both gates at commit time. It covers engine sources,
profile configuration/resources, Docker files, Compose files, and root
`clad.properties`; profiles may extend its scope.

For the boundary definitions and test ownership behind these rows, see the
optional [`../overlays/PORTS_AND_ADAPTERS.md`](../overlays/PORTS_AND_ADAPTERS.md).
