<!--
  WORKED EXAMPLE - contract synced from templates/feature-skeleton/.
  UC-00's output/ is historical/frozen (gate content hashes); it may
  contain legacy artefacts. See examples/UC-00-login/README.md
  SS"Contract vs example".
-->

# Stage 04 — Implement (worked example)

This is a reference container for the implementation sub-stages. The
authoritative stage contract is
[`../../../../../templates/feature-skeleton/stages/04_implement/CONTEXT.md`](../../../../../templates/feature-skeleton/stages/04_implement/CONTEXT.md).

Stage 04 is spec-driven and test-verified: `04c` authors the frozen
Acceptance Spec and native flow tests (Gate 3); `04d`/`04e` produce unit
tests and implementation together, gated by mutation score. See
[`../../../../../methodology/implementation/TESTING.md`](../../../../../methodology/implementation/TESTING.md).

In this worked feature the native outer loop is `LoginFlowTest`
(`reference-impl/java-legible/src/test/java/dev/legible/example/login/`).

## Advancing

> Do not open the next stage's `CONTEXT.md` yourself. After a stage's
> `output/` is written, end your turn by running the gate-driven advance
> command (`./clad advance`). See AGENTS.md §2 principle 12 and
> `methodology/implementation/STAGES.md` §"Gate-driven advance".
