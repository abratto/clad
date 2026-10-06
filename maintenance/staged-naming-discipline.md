# Maintenance change — `staged-naming-discipline`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `proposed`
- **Affected profile(s):** all profiles (gate + templates + docs)
- **Feature-contract impact:** `additive` (two new Gate-1 checks; no
  existing artefact shape changes)
- **Design gate:** `pending`
- **Evidence gate:** `pending`
- **Change summary:** two rules that were social ("01a declares names
  only"; "the chain table may not invent names the map never declared")
  become mechanical Gate-1 checks.

## Why

Stage 01a fixes the concept SET and the action VOCABULARY; Stage 01b locks
the choreography, and the chain table is the canonical name source for
everything downstream ("if a Stage 03 sync spec disagrees with a chain
table on an action name, the chain table wins"). Both rules existed only
as prose:

1. The walkthrough's Stage-01a agent stance ("if you find yourself writing
   `lookupByUsername(username) -> Found(userId) | NotFound`, you are doing
   Stage 02 work in Stage 01a. Names only.") was not enforced. Signatures
   written at 01a lock a half-agreed design into the artefact the chain
   tables and concept specs are derived from.
2. `verify_action_chain.py` already fails when a chained action is missing
   from the responsibility map — but it runs at 04b, long after the name
   has propagated into concept specs, syncs, cards, and contracts. A name
   invented in a chain table at 01b was discovered three stages too late.

## Rule

- **01a names only.** The Concepts table's `Owned actions` column carries
  bare backticked action names. A cell containing `(`, `)`, `->`, `[`, or
  `]` is a Stage-01a defect: signatures and outcome enums are authored at
  Stage 01b/02.
- **01b resolves against 01a.** Every `Concept.action` invoked by a chain
  table must appear in the responsibility map's `Owned actions` column for
  that concept. `Web` actions are exempt (the bootstrap concept's
  request/respond surface belongs to the transport profile).

## Mechanism

- `quality-gate/verify_responsibility_map_shape.py` — blocking at Stage
  01a. Reads the raw `Owned actions` cell via the new
  `artifact_parsers.parse_resp_map_action_cells` (the name-extracting
  parser silently drops the syntax this check rejects). One diagnostic per
  offending row, naming the token and the stage that owns it.
- `quality-gate/verify_chain_map_names.py` — blocking at Stage 01b
  (before Gate 1). The name-level, design-time slice of
  `verify_action_chain.py`: compares `parse_chain_table_actions` against
  `parse_resp_map_actions` and fails with the add-to-map fix per
  undeclared action. A standalone script rather than a mode of
  `verify_action_chain.py` because the full check's remaining inputs
  (sync specs, cards, contracts) do not exist at Gate 1.
- Both are wired into `quality-gate/clad_stages.py` (Stage 01a and 01b
  check lists) so `advance` and `verify_artefacts.py` run them; both are
  named in the skeleton stage contracts
  (`templates/feature-skeleton/stages/01a_responsibility-map/CONTEXT.md`,
  `…/01b_chain-table/CONTEXT.md`).

## Evidence

- `quality-gate/tests/test_staged_naming.py` — 9 tests: a signature or
  outcome enum in the actions cell fails and names the concept; the typed
  `Owned state` column (`username: UserId -> String`) is not flagged; an
  undeclared chain action fails with the add-to-map fix; Web actions are
  exempt; missing inputs SKIP (exit 0).
- Full `quality-gate/tests` suite green; `verify_artefacts.py` intact.
