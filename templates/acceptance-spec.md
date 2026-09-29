<!-- Template for Stage 04c (04c_acceptance-tests). The Acceptance Spec is the
human-facing, frozen Gate-3 artifact (DR-0001). One `## Scenario:` section per
top-level `### Scenario:` in ../01_usecase/output/usecase.md, using the exact
scenario name. Every section binds to native test method(s) via `**Test:**`.
Delete this comment before committing. -->

# Acceptance spec — `<feature name>`

> Derived from `../01_usecase/output/usecase.md`, `../01b_chain-table/output/`,
> `../03_syncs/output/`, and `../04b_contract/output/`. It invents nothing.
> Frozen at Gate 3: editing this file after approval stales the gate and
> requires human re-approval (`verify_stage_sequence.py` gate content-hash).
> `verify_acceptance_binding.py` blocks the stage unless every use-case
> scenario has a section and every `Test:` binding resolves.

## Scenario: `<scenario-name>`

- **Trigger:** `<HTTP verb + route, or event>`
- **Expected response:** `<status + body literals copied from the sync spec 'then'>`
- **Expected token chain:** `<A.action[OUTCOME]> -> <B.action[OUTCOME]> -> <Web.respond[Sent]>`
- **Postconditions:** `<what is true after the scenario>`
- **Test:** `<TestClass>.<testMethod>`

> Repeat `## Scenario:` once per top-level use-case scenario. Add one
> `**Test:**` bullet per sub-case the scenario needs (for example a happy path
> and its failure envelope), each naming the native test method that enforces
> it. A method may be named by more than one bullet; a bullet must name a real
> method.

## Response contracts

> Only when `features/_system/stages/00_actor-goal/output/port-spec.md` has
> inbound entries. Tag each block `@contract` and assert the exact transport
> path, field type (JSON path), and primary failure envelope.

- `@contract` — `<method + path>`: JSON path `<$.field>` has type `<type>`;
  error envelope `<shape>`.

## Collection coverage

> Only when the response carries a collection (a plural envelope key or a
> `List<...>` completion field). Name the empty, multi-item, and (where two
> lists are positionally aligned) repeated-key fixtures, or write
> `repeated-key: n/a — <reason>`.

- empty: `<fixture / test method>`
- multi-item: `<fixture / test method>`
- repeated-key: `<fixture / test method>` | `n/a — <reason>`
