# Stage 04b — SPEC

## Why this stage exists

The SPEC is the **machine-checkable slice** of each concept spec —
action signatures, outcome enums, flow-token shape — with the prose
principle and edge-case discussion stripped out. 04d and 04e compile
against the SPECs, not against the prose. Without 04b the inner-loop
tests would have to re-derive the contract from prose every time
the spec changes.

**Feeds:**

- `<Name>.spec.md` → 04c (flow tests assert SPEC-level signatures), 04d (concept TDD compiles against SPEC), 04e (sync TDD references SPEC action enums).

**Agent stance for this stage:** mechanical extraction only. If the
SPEC needs an action that isn't in the concept spec, the defect is
upstream (Stage 02), not here.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../02_concepts/output/` | 4 | Concept specs |
| `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md` | 4 | Required when present; external adapter response-shape contract |
| Skill: `clad-spec-extraction` | 3 | SPEC extraction reference (see skills/ directory) |
| `../../../../../templates/spec.md` | 3 | Output template |

## Process

Derive the SPEC contract slice **mechanically** from each concept
spec: action signatures, outcome enums, flow-token shape. No prose
principle, no edge-case discussion — those stay in the concept spec.
The implementation in `04d` and `04e` compiles against these SPECs.

If `../../02_concepts/output/` contains a bootstrap concept file such
as `Web.concept.md` without an explicit feature-level deviation, stop
and reopen Stage 02 instead of deriving a SPEC from it. `04b` must not
normalize upstream bootstrap drift by continuing mechanically.

SPEC files must not include correction history, methodology
interpretation, remediation notes, design commentary, or implementation
guidance beyond what is mechanically present in the concept spec.

If `../../../../../features/_system/stages/00_actor-goal/output/port-spec.md`
exists, add a separate **Response shapes** section to the relevant SPEC
output. Derive it from the port spec, not from local implementation
preference. It must name exact JSON paths, field types, wrappers, and
error envelope values required by the external contract.

## Outputs

- `output/<Name>.spec.md` per concept

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../../quality-gate/verify_spec_parity.py \
  --concept-dir ../../02_concepts/output --spec-dir output
python3 ../../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<Name>.spec.md,…"  # one per business concept
python3 ../../../../../quality-gate/verify_port_spec_contract.py \
  --port-spec ../../../../../features/_system/stages/00_actor-goal/output/port-spec.md \
  --spec-dir output
```

- **verify_spec_parity.py:** every action name in every concept spec
  has a matching entry in the corresponding SPEC file, and vice versa.
- **verify_file_manifest.py:** one `.spec.md` file per business concept.
- **verify_port_spec_contract.py:** skips when no `port-spec.md` exists;
  otherwise checks the port spec is concrete and at least one SPEC file
  contains response-shape assertions.

### Semantic checks (human)

- Every SPEC entry's flow-token shape matches the concept's spec.
- **Bootstrap drift stop rule:** if a bootstrap concept file appears in
  `02_concepts/output/` without an explicit deviation, `04b` must stop
  and send work back to Stage 02 rather than deriving a new spec.
- **Mechanical extraction only:** no SPEC file contains correction
  history, methodology interpretation, remediation notes, or
  implementation guidance not present in the concept spec.
- **Port-spec response shapes:** when `port-spec.md` exists, SPEC output
  includes exact response shape examples for each relevant HTTP endpoint:
  JSON paths, field types, wrappers, and error envelope values.

## Gate

Auto-advances (next human gate: Stage 04c). The `verify_spec_parity.py` script must
pass before advancing.

## Next stage

→ [`../04c_flow-tests/CONTEXT.md`](../04c_flow-tests/CONTEXT.md) — Outer red (flow tests)

The agent proceeds to Stage 04c without a human gate.
