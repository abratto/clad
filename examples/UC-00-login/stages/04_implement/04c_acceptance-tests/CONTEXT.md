<!--
  WORKED EXAMPLE - contract synced from templates/feature-skeleton/.
  UC-00's output/ is historical/frozen (gate content hashes); it may
  contain legacy artefacts. See examples/UC-00-login/README.md
  SS"Contract vs example".
-->

# Stage 04c — Acceptance tests (worked example)

The authoritative stage contract is
[`../../../../../templates/feature-skeleton/stages/04_implement/04c_acceptance-tests/CONTEXT.md`](../../../../../templates/feature-skeleton/stages/04_implement/04c_acceptance-tests/CONTEXT.md).

This stage's output is the frozen **Acceptance Spec**
[`output/acceptance-spec.md`](output/acceptance-spec.md): one section per
UC-00 scenario (`successful-login`, `wrong-password`, `unknown-user`,
`lockout`), each bound to a method of the native outer loop
`LoginFlowTest`. It is the Gate-3 human artifact; editing it after
approval stales Gate 3.

## Advancing

> Do not open the next stage's `CONTEXT.md` yourself. After this stage's
> `output/` is written, end your turn by running the gate-driven advance
> command (`./clad advance`). See AGENTS.md §2 principle 12 and
> `methodology/implementation/STAGES.md` §"Gate-driven advance".
