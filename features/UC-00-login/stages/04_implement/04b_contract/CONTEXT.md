<!--
  WORKED EXAMPLE - contract synced from templates/feature-skeleton/.
  UC-00's output/ is historical/frozen (gate content hashes); it may
  contain legacy artefacts. See features/UC-00-login/README.md
  SS"Contract vs example".
-->

# Stage 04b — contract

## Why this stage exists

The contract is the **machine-checkable slice** of each concept spec —
action signatures, outcome enums, flow-token shape — with the prose
principle and edge-case discussion stripped out. 04d and 04e compile
against the concept contracts, not against the prose. Without 04b the inner-loop
tests would have to re-derive the contract from prose every time
the spec changes.

**Feeds:**

- `<Name>.contract.md` → 04c (flow tests assert contract-level signatures), 04d (concept TDD compiles against contract), 04e (sync TDD references contract action enums).

**Agent stance for this stage:** mechanical extraction only. If the
contract needs an action that isn't in the concept spec, the defect is
upstream (Stage 02), not here.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/concept-bindings.md` | 4 | Which canonical concepts this feature uses |
| `../../../../../features/_system/concepts/` | 4 | Canonical concept specs (`state`, actions) |
| `../../02_concepts/output/<Name>.concept.md` | 4 | NEW/EXTEND proposals (not yet promoted) |
| `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md` | 4 | Required when present; external adapter response-shape contract |
| Skill: `clad-spec-extraction` | 3 | contract extraction reference (see skills/ directory) |
| `../../../../../templates/contract.md` | 3 | Output template |

## Process

**Deterministic generation first.** The contract is mechanical extraction from
the concept specs + chain tables. First run:

Generated via:
```
python3 ../../../../../quality-gate/generate_contract.py --feature ../../../ --write
```

`generate_contract.py` emits one `<Name>.contract.md` per business concept with the
action list and outcome enums collected from the canonical chain tables. It
leaves `<TODO>` markers for input types and flow-token shape; transcribe those
from the concept spec — the canonical corpus spec, or this feature's NEW/EXTEND
proposal where one exists. Do not add actions, outcomes, or fields the concept
spec and chain tables did not declare.

Derive the concept contract contract slice **mechanically** from each concept
spec: action signatures, outcome enums, flow-token shape. No prose
principle, no edge-case discussion — those stay in the concept spec.
The implementation in `04d` and `04e` compiles against these contracts.

If `../../02_concepts/output/` contains a bootstrap concept file such
as `Web.concept.md` without an explicit feature-level deviation, stop
and reopen Stage 02 instead of deriving a contract from it. `04b` must not
normalize upstream bootstrap drift by continuing mechanically.

contract files must not include correction history, methodology
interpretation, remediation notes, design commentary, or implementation
guidance beyond what is mechanically present in the concept spec.

If `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md`
exists, add a separate **Response shapes** section to the relevant contract
output. Derive it from the port spec, not from local implementation
preference. It must name exact JSON paths, field types, wrappers, and
error envelope values required by the external contract.


## Progress checklist

- [ ] One `.contract.md` per concept
- [ ] Action signatures match concept spec exactly
- [ ] Outcome enums match chain table
- [ ] Flow-token shapes declared
- [ ] Response shapes present if port-spec.md exists
- [ ] Self-audit: `./clad verify` passes
## Outputs

- `output/<Name>.contract.md` per concept

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../../quality-gate/verify_contract_parity.py \
  --concept-dir ../../../../../features/_system/concepts \
  --concept-dir ../../02_concepts/output \
  --spec-dir output
python3 ../../../../../quality-gate/verify_outcome_alignment.py \
  --chain-dir ../../01b_chain-table/output --spec-dir output
python3 ../../../../../quality-gate/verify_action_chain.py \
  --resp-map ../../01a_responsibility-map/output/responsibility-map.md \
  --chain-dir ../../01b_chain-table/output \
  --concept-dir ../../../../../features/_system/concepts \
  --concept-dir ../../02_concepts/output \
  --sync-dir ../../03_syncs/output \
  --dep-dir ../../03a_dependency-review/output \
  --spec-dir output
python3 ../../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<Name>.contract.md,…"  # one per business concept
python3 ../../../../../quality-gate/verify_concept_additivity.py \
  --feature ../../../
python3 ../../../../../quality-gate/verify_port_spec_contract.py \
  --port-spec ../../../../../features/_system/stages/00_actor-goal/output/port-spec.md \
  --spec-dir output
```

- **verify_contract_parity.py:** every action name in every concept spec
  has a matching entry in the corresponding contract file, and vice versa.
- **verify_outcome_alignment.py:** every chain-table outcome token
  appears in the corresponding contract's outcome enum. This is the first
  stage where both sides exist, which is why it runs here rather than at
  Stage 02.
- **verify_action_chain.py:** every action flows consistently through
  the responsibility map, chain tables, concept specs, syncs,
  dependency cards, and contracts.
- **verify_file_manifest.py:** one `.contract.md` file per business concept.
- **verify_concept_additivity.py:** an extended corpus concept's contract is
  **additive only** — every canonical action, and every canonical outcome of a
  surviving action, must still be listed. Same escape hatch as Stage 03b:
  `_config/additivity-exceptions.md`, one authorised line per bullet.

- **verify_port_spec_contract.py:** skips when no `port-spec.md` exists;
  otherwise checks the port spec is concrete and at least one contract file
  contains response-shape assertions.

### Semantic checks (human)

- Every contract entry's flow-token shape matches the concept's spec.
- **Bootstrap drift stop rule:** if a bootstrap concept file appears in
  `02_concepts/output/` without an explicit deviation, `04b` must stop
  and send work back to Stage 02 rather than deriving a new spec.
- **Mechanical extraction only:** no contract file contains correction
  history, methodology interpretation, remediation notes, or
  implementation guidance not present in the concept spec.
- **Inbound port response shapes:** when `port-spec.md` has inbound entries,
  contract output includes exact response shape examples for each relevant inbound
  port: transport paths, field types, wrappers, and error envelope values.
  Outbound entries instead name their adapter-boundary evidence; they do not
  require an HTTP response shape.

## Gate

Auto-advances (next human gate: Stage 04c). The `verify_contract_parity.py`,
`verify_outcome_alignment.py`, and `verify_action_chain.py` scripts must
pass before advancing.

## Next stage

→ [`../04c_flow-tests/CONTEXT.md`](../04c_flow-tests/CONTEXT.md) — Outer red (flow tests)

The agent proceeds to Stage 04c without a human gate.
