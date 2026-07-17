# Stage 03b — Data model (UC-00-login)

## Why this stage exists

This stage makes UC-00's conceptual state model explicit **before** any
profile mapping or test implementation starts. The feature has no
Pattern D reads, so the data model is driven almost entirely by each
concept's own `state` section.

**Feeds:**

- `User.data-model.md`, `PasswordAuth.data-model.md`, `Session.data-model.md` → 04a storage mapping when a persistent profile exists

## Inputs

| Path | Layer | Why |
|---|---|---|
| `../02_concepts/output/` | 4 | Approved concept state sections |
| `../03a_dependency-review/output/pattern-d-summary.md` | 4 | Confirms UC-00 has no Pattern D field exposure |
| `../../../../methodology/architecture/DATA_MODEL_NOTES.md` | 3 | Conceptual data-model procedure |
| `../../../../methodology/implementation/RULES.md` | 3 | Hard rules R1, R2 |
| Skill: `clad-data-modeling` | 3 | Data modeling reference |
| `../../../../templates/data-model.md` | 3 | Output template |

## Process

Produce one profile-neutral conceptual data-model file per business
concept: `User`, `PasswordAuth`, and `Session`. Follow the seven CSDP
steps explicitly, not a compressed summary. Use the approved state
sections exactly; do not introduce profile-specific field types or
runtime-only helper structures.

## Outputs

- `output/User.data-model.md`
- `output/PasswordAuth.data-model.md`
- `output/Session.data-model.md`

## Verify

### Automated checks

```
python3 ../../../../quality-gate/verify_data_model.py \
  --data-dir output --concept-dir ../02_concepts/output
python3 ../../../../quality-gate/verify_file_manifest.py \
  --dir output --expected "User.data-model.md,PasswordAuth.data-model.md,Session.data-model.md"
```

- **verify_data_model.py:** validates CSDP steps, constraints, no
  storage leakage, no cross-concept references.
- **verify_file_manifest.py:** `output/` contains exactly one `.data-model.md`
  per business concept.

### Semantic checks (human)

- Three data-model files exist, one per business concept in UC-00.
- Each file exposes the seven CSDP steps in text form.
- Every fact type traces directly to the concept's approved `state`
  section.
- No Pattern D exposure is invented, because `pattern-d-summary.md`
  states there are none.
- Uniqueness, mandatory, derivation, and value/set/subtype sections are
  explicit, even when they conclude `None`.
- No RDF, SQL, or document-store mapping detail appears in the files.

## Gate instruction — STOP AND PRESENT

### Step 1 — Present artefacts

Run:

```
python3 ../../../../quality-gate/present_gate.py \
  --feature ../../../ \
  --gate 2
```

Present the output to the human. **Do NOT proceed past this point.**

### Step 2 — Wait for human approval

Wait for the human to say "approved" (or "Gate 2 approved").
Do NOT update RESUME.md yourself.

### Step 3 — Record approval

Only after the human explicitly approves, run:

```
python3 ../../../../quality-gate/approve_gate.py \
  --feature ../../../ \
  --gate 2
```

This updates RESUME.md to mark Gate 2 as approved.

### Step 4 — Proceed

After `approve_gate.py` exits successfully, proceed to Stage 04a
(storage mapping). Stages 04a–04b auto-advance. The next human gate is
**Gate 3 (Executable specification)** at Stage 04c.

The `verify_data_model.py` and `verify_file_manifest.py` scripts must
pass before requesting the gate.

## Next stage

→ [`../04_implement/CONTEXT.md`](../04_implement/CONTEXT.md) — Implement (router)

Do NOT open this file until the human approves Gate 2. After
`approve_gate.py` exits successfully, open the next CONTEXT.md.