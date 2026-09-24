# Stage 03b — Data model

## Why this stage exists

This stage separates **conceptual data modeling** from implementation.
It turns each concept's approved `state` section plus any approved
Pattern D exposure from 03a into a **profile-neutral** fact model
before Stage 04 starts talking about RDF, SQL, document fields, or
other storage primitives.

> **Completed example.** A worked instance of this stage's output is at
> [`../../../../examples/UC-00-login/stages/03b_data-model/output/`](../../../../examples/UC-00-login/stages/03b_data-model/output/) — read it if useful; it is illustrative, not a template.

**Feeds:**

- `<Name>.data-model.md` → 04a (profile-specific storage mapping), 04d (state invariants remain visible when implementation starts).

**Agent stance for this stage:** this stage models facts and
constraints, not databases. If you find yourself naming a table,
property IRI, migration, or schema library, you are too far downstream.

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../../../../features/_system/concepts/` | 4 | Canonical concept state sections |
| `../02_concepts/output/<Name>.concept.md` | 4 | NEW/EXTEND proposals (not yet promoted) — same anatomy |
| `../03a_dependency-review/output/pattern-d-summary.md` | 4 | Approved cross-concept fields that must be exposed conceptually |
| Skill: `clad-data-modeling` | 3 | Data modeling reference (see skills/ directory) |
| `../../../../methodology/architecture/DATA_MODEL_NOTES.md` | 3 | Conceptual data-model procedure |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R2 |
| `../../../../templates/data-model.md` | 3 | Output template |

## Process

**Deterministic generation first.** The CSDP is judgement-laden, so the
generator emits the full seven-step skeleton and auto-fills only the parts that
are mechanical from the concept `## State` annotations. First run:

Generated via:
```
python3 ../../../../quality-gate/generate_data_model.py --feature ../../ --write
```

`generate_data_model.py` emits one `<Name>.data-model.md` per business concept
with Object types, Fact types, and (where the state line carries a
`-- mandatory` / `-- optional` / `-- unique` annotation) uniqueness + mandatory
roles derived automatically. It leaves `<TODO: judgment>` markers on steps that
are genuine modelling decisions (familiar examples/elementary facts, combination
checks, value/subtype constraints, final checks). Resolve those markers;
the derived Object/Fact/constraint rows must stay as the generator produced them
unless you can point to an error in the upstream state section.

For each approved concept spec, derive a profile-neutral conceptual data
model by following the seven CSDP steps in `DATA_MODEL_NOTES.md`.
The output must make those steps inspectable in text form: familiar
examples, elementary facts, draft fact model, combination/derivation
checks, uniqueness and arity, mandatory/logical derivations, value/set/
subtype constraints, and final checks. If a concept truly has no state,
still produce a `<Name>.data-model.md` file recording that fact rather
than skipping the concept silently.

Every fact and constraint must trace 1:1 to approved Stage 02 state or
approved Pattern D exposure from 03a. Do not add foreign keys,
cross-concept joins, storage-specific indexes, or implementation-only
helper fields.


## Progress checklist

- [ ] One `.data-model.md` per concept
- [ ] All 7 CSDP steps present
- [ ] Fact types derived from concept `state` section
- [ ] Constraints derived from concept `actions` pre/post
- [ ] No concept-state read fields missed (from 03a)
- [ ] Self-audit: `./clad verify` passes
## Outputs

- `output/<Name>.data-model.md` per concept — profile-neutral conceptual data model following the seven-step CSDP structure

## Verify

### Automated checks

Run the following before requesting the human gate:

```
python3 ../../../../quality-gate/verify_data_model.py \
  --data-dir output \
  --concept-dir ../../../../features/_system/concepts \
  --concept-dir ../02_concepts/output   # proposals shadow canonical by name
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "<Name>.data-model.md,…"  # one per concept
python3 ../../../../quality-gate/verify_concept_additivity.py \
  --feature ../..
```

- **verify_data_model.py:** validates all 7 CSDP steps present, all
  sub-sections present, constraint sections have content or "None",
  no storage-leakage patterns, and no cross-concept entity type
  references.
- **verify_file_manifest.py:** one `.data-model.md` file per concept.
- **verify_concept_additivity.py:** an extended corpus concept is
  **additive only** — every canonical `## State` line must survive in this
  feature's proposal. A lost or restated line fails unless it is listed, with a
  reason, in `_config/additivity-exceptions.md`. Closes the only guarantee the
  promotion machinery does not give you: `_state_changed` is a *difference*
  test, so a removal and an addition look alike, and promotion copies either
  over the canonical entry.


### Semantic checks (human)

- Every fact type traces back to approved Stage 02 state or approved
  Pattern D exposure from 03a.
- Elementary facts are explicit and remain concept-local.
- No cross-concept foreign key or direct region-sharing relationship is
  introduced.
- **Cross-stage check (back):** every Pattern D field in
  `pattern-d-summary.md` appears in the owner concept's data model.

## Gate instruction — this stage ends a human gate

Run:

```
./clad advance
```

(Long form: `python3 quality-gate/advance.py --feature features/UC-XX-<slug>`.)

`advance.py` owns the gate: it runs `verify_data_model.py` and
`verify_file_manifest.py`, writes the stage receipt, prints the artefact
summary and the `approve_gate.py --gate 2` command, and stops (exit 10).
Present its summary to the human and **wait**. Do NOT run `present_gate.py`
yourself and do NOT edit `RESUME.md`.

Only after the human explicitly says "approved", run the approval command
`advance.py` printed, then re-run `./clad advance` to cross the gate. Gate 2
is the **Architecture** gate; Stages 04a and 04b auto-advance, and the next
human gate is **Gate 3 (Executable spec)** at Stage 04c.

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
