# Stage 04c — Acceptance tests

## Why this stage exists

This stage freezes **what "done" means** for the use case, in a form a
human can read and a machine can run:

- `output/acceptance-spec.md` — the **Acceptance Spec**: one section per
  use-case scenario naming the trigger, the expected response, the
  expected flow-token chain, the postconditions, and the native test
  method that enforces it. This is the human-facing Gate-3 artifact and
  it is **frozen**: changing it after approval stales Gate 3 and forces
  re-approval (the gate content-hash mechanism).
- the **native per-scenario flow tests** (one method per scenario or
  sub-case) under the configured test source root. These execute the
  scenario end-to-end (transport request → bootstrap → concepts/syncs →
  response) and assert the flow-token chain. There is **no Gherkin /
  Cucumber track**: the native test is the executable form.

The Acceptance Spec is a derived view — every row traces to the use
case, a chain table, a contract, or a sync spec. It invents nothing.
`verify_acceptance_binding.py` blocks the stage unless every use-case
scenario has a spec section, every spec row binds to a real test method,
and every flow-test method is documented.

> **Completed example.** A worked instance is at
> [`../../../../../examples/UC-00-login/stages/04_implement/04c_acceptance-tests/output/`](../../../../../examples/UC-00-login/stages/04_implement/04c_acceptance-tests/output/).

**Feeds:**

- `acceptance-spec.md` → 04d/04e (the tests they must turn green), 05
  (trace cross-reference).
- native flow tests (side effect) → run green by the end of 04e.

**Agent stance:** the spec must read like the use case. If it reads like
a unit test, you are at the wrong layer. Read
`methodology/implementation/TESTING.md` before writing anything.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../01_usecase/output/usecase.md` | 4 | Scenarios, triggers, preconditions, postconditions |
| `../../01b_chain-table/output/` | 4 | Expected action/outcome chain per scenario |
| `../../03_syncs/output/` | 4 | Response literals (`then` clauses) |
| `../04b_contract/output/` | 4 | Action signatures and outcome enums |
| `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md` | 4 | Required when present; inbound `@contract` scenarios |
| `../../../_config/build-and-test.md` | 3 | Canonical build/test command |
| `../../../_config/package-and-layout.md` | 3 | Test-source root and package layout |
| `../../../../../methodology/architecture/FLOW_TOKENS.md` | 3 | Token semantics, casing rules, payload rules |
| `../../../../../methodology/implementation/TESTING.md` | 3 | Spec-driven verification discipline |
| `../../../../../templates/acceptance-spec.md` | 3 | Acceptance Spec output template |
| `../../../../../templates/http-integration-test.java` | 3 | Profile-specific end-to-end adapter test |
| Skill: `clad-flow-testing` | 3 | Acceptance-spec and flow-test reference |

## Process

1. **Derive `output/acceptance-spec.md`** from the inputs using
   `../../../../../templates/acceptance-spec.md`. One `## Scenario:`
   section per top-level `### Scenario:` in `usecase.md`, using the
   **exact scenario name**. For each scenario record:
   - the trigger (verb + route) from the use case,
   - the expected response (status + body literals) copied from the sync
     spec's `then` clause,
   - the expected token chain from the chain table (action + outcome per
     row, SCREAMING_SNAKE_CASE outcomes copied from the contract),
   - the postconditions from the use case,
   - one or more `- **Test:** \`Class.method\`` bindings naming the
     native test method that enforces it.
2. **Write the native flow tests** under the configured
   `test.source.root`, in the feature's package. One method per spec
   binding. Each asserts the transport response and the runtime
   flow-token chain. Do not introduce steps, scenarios, or outcomes the
   use case does not define.
3. **If the feature exposes an adapter surface** (HTTP, CLI, GraphQL,
   pub/sub — `port-spec.md` inbound, or a `Web` bootstrap in a chain/use
   case), derive a profile-specific end-to-end integration test
   alongside the flow tests. Derive it from
   `../../../../../templates/http-integration-test.java`. It may be
   `@Disabled` until the implementation lands; Stage 05 re-runs it with
   `--require-enabled`.
4. **If `port-spec.md` has inbound entries**, add at least one
   `@contract` block to the Acceptance Spec per inbound port, asserting
   exact paths, field types (JSON path), and the primary failure
   envelope. Outbound entries are covered by their adapter-boundary
   tests.
5. **Collection coverage (only when the response carries a
   collection).** Add a `## Collection coverage` section to
   `acceptance-spec.md` naming an **empty**, a **multi-item**, and
   (where two lists are positionally aligned) a **repeated-key** fixture;
   write `repeated-key: n/a — <reason>` when no alignment exists. Design
   gates verify structure, not cardinality.
6. **Confirm the tests compile / run** with the canonical command from
   `../../../_config/build-and-test.md`. The tests may be `@Disabled` at
   this stage; they must exist and compile.

**Token-chain rules (read `FLOW_TOKENS.md` first):**
- Outcome values MUST be SCREAMING_SNAKE_CASE, copied from the contract.
- Token count = number of rows in the chain table — no phantom tokens.
- Passwords and secrets MUST NOT appear in any token payload.

**Boundary scaffold.** A compiling app is required even though this is a
test-authoring stage: write the bootstrap adapter/controller and DTOs if
the feature is greenfield. Do not implement business concepts or syncs —
that is 04d/04e.

## Outputs

- `output/acceptance-spec.md` — the frozen, human-facing Acceptance Spec
- (Side effect:) native per-scenario flow-test methods under
  `test.source.root`
- (Side effect:) a profile-specific end-to-end adapter integration test
  when the feature exposes an adapter surface

## Verify

### Automated checks

```
python3 ../../../../../quality-gate/verify_profile_paths.py \
  --feature ../../../
python3 ../../../../../quality-gate/verify_acceptance_binding.py \
  --spec output/acceptance-spec.md \
  --usecase ../../01_usecase/output/usecase.md \
  --chain-dir ../../01b_chain-table/output \
  --test-source-root <APP_TEST_SOURCE_ROOT>
python3 ../../../../../quality-gate/verify_collection_coverage.py \
  --feature ../../../
python3 ../../../../../quality-gate/verify_port_spec_contract.py \
  --port-spec ../../../../../features/_system/stages/00_actor-goal/output/port-spec.md \
  --contract-dir ../04b_contract/output \
  --feature-dir output
python3 ../../../../../quality-gate/verify_adapter_test.py \
  --feature-root ../../.. \
  --test-source-root <APP_TEST_SOURCE_ROOT>
python3 ../../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected acceptance-spec.md
```

- **verify_profile_paths.py:** the effective `test.source.root` /
  `concept.impl.dir` / `sync.impl.dir` resolve inside the feature's
  declared `_config/package-and-layout.md` roots.
- **verify_acceptance_binding.py:** every use-case scenario has an
  Acceptance Spec section; every `Test:` binding resolves to a real test
  method; every `*FlowTest` method is documented.
- **verify_collection_coverage.py:** a collection-shaped feature declares
  the empty / multi-item / repeated-key fixtures. Forward-only.
- **verify_port_spec_contract.py:** skips when no `port-spec.md`; else
  checks response shapes and `@contract` assertions.
- **verify_adapter_test.py:** an adapter surface requires a
  profile-specific end-to-end test to exist (may be `@Disabled` here).

### Semantic checks

- Every Acceptance Spec section traces to a use-case scenario; no
  invented scenario, outcome, or status code.
- Every `Test:` binding names the method that actually asserts that
  scenario's response and token chain.
- The expected token chain matches the corresponding chain table.
- Outcome values are SCREAMING_SNAKE_CASE, copied from the contract.
- No password or secret appears in any token payload.
- An executed build-and-test command proves the tests compile.

## Gate instruction — this stage ends a human gate

Run:

```
./clad advance
```

`advance.py` owns the gate: it runs this stage's checks, writes the
stage receipt, prints the artefact summary and the `approve_gate.py
--gate 3` command, and stops (exit 10). Present its summary to the
human and **wait**. Do NOT run `present_gate.py` yourself and do NOT
edit `RESUME.md`.

The human reviews `usecase.md` + `output/acceptance-spec.md` (the frozen
scenarios). Only after the human explicitly says "approved", run the
approval command `advance.py` printed, then re-run `./clad advance`.
Gate 3 is the **Acceptance spec** gate; Stages 04d, 04e, and 05 then
auto-advance with no further human gates. After Gate 3 is approved,
`advance.py` directs the agent to `04d_concept-impl/CONTEXT.md`; do not
select the stage manually.

## Advancing

> Do not open the next stage's `CONTEXT.md` yourself. After this stage's
> `output/` is written, end your turn by running the gate-driven advance
> command, which runs this stage's checks, enforces stage ordering, and
> tells you the next step:
>
> ```
> ./clad advance
> ```
>
> (Long form: `python3 quality-gate/advance.py --feature features/UC-XX-<slug>`.)
> The CLI wrapper auto-discovers the feature from `RESUME.md`.
>
> Treat its output as your next instruction. It advances you, stops you
> at a human gate, or returns you to this stage with the defects to fix.
> See AGENTS.md §2 principle 12 and
> `methodology/implementation/STAGES.md` §"Gate-driven advance".
