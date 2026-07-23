# Iterative changes — re-entry workflow

When an already-approved stage artefact needs to change, you cannot
just edit it and commit. CLAD R17 requires re-entering the stage pipeline
at the earliest affected stage and walking forward.

## How to use this directory

1. Copy `templates/iterative-change/artefact-impact-matrix.md` into
   `features/UC-XX-<slug>/_changes/<change-name>.md`.
2. Fill in the change category, earliest re-entry stage, artefact-impact
   matrix, and re-derivation order.
3. Re-enter the pipeline at the specified earliest stage and walk forward,
   updating stage outputs and implementation in the **same commit batch**.
4. The pre-commit hook runs `verify_iterative_change_readiness.py` to
   confirm the `_changes/` artefact exists before allowing the commit.

## What happens if I skip this

The pre-commit hook will block the commit. If you bypass it, the
`verify_iterative_change_coupling.py` check catches implementation
changes without corresponding spec changes — but it won't catch a
spec-only change made without gate review. Both guards together form
the R17 enforcement surface.
