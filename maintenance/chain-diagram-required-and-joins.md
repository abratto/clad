# Maintenance change — `chain-diagram-required-and-joins`

- **Rulebook:** `methodology/core/ITERATIVE_CHANGES.md`
- **Change class:** `platform`
- **Status:** `closed`
- **Affected profile(s):** all profiles (stage contract + template + gate check)
- **Feature-contract impact:** `re-entered`
- **Design gate:** `approved`
- **Evidence gate:** `approved`
- **Change summary:** the Stage 01b diagram is **required** rather than "optional but encouraged", and its derivation rules now say how rows that share a `When` and a `Then` map, and how a join row maps. `verify_chain_grammar.py` fails a chain file with no `stateDiagram-v2`.

## Why

A chain table was committed with no diagram in the experiment (UC-04). Three
things were wrong in the methodology, not just in the author's judgement:

1. **The template contradicted itself.** The heading said "Diagram (optional but
   encouraged)" while the same-turn surfacing rule said "One scenario = one
   chain-table file = one table + one diagram" and "the gate at Stage 01b covers
   both artefacts together, and a gate cannot be opened over an incomplete
   picture". Reading the heading rather than the rule is a reasonable mistake.
2. **The derivation rules did not cover per-outcome rows.** The rule said "each
   table row becomes exactly one arrow", but rows that share a `When` label and a
   `Then` action (`Ok` / `BadPassword` / `Locked` on one trigger invoking one
   action) cannot produce distinct arrows — they enter the same node. The rule
   neither stated the collapse nor explained that the distinguishing outcomes
   reappear as that node's outgoing arrows. Counting arrows and expecting one per
   row is the obvious (wrong) reading.
3. **The derivation rules did not cover joins.** The template documents join
   rows (`∧`) in the table but said nothing about drawing them, and a Mermaid
   arrow has exactly one source.

Nothing was enforced mechanically either: no checker referenced `stateDiagram`,
so the requirement lived only in prose.

## Rule

- The diagram is **required**: the 01b artefact is the table *and* its
  `stateDiagram-v2`, and the gate covers them together.
- **Terminal responses** are one node per response contract (`Web_respond201`,
  `Web_respond409`) — two responses that assert different things are two
  observable results (R9), not one state.
- **Rows that share a `When` label and a `Then` action collapse into one
  arrow.** The invariant is that every arrow has a row — not that every row has
  its own arrow.
- **A join row is drawn from the conjunct that completes last**, with every
  other conjunct named in the label
  (`Stocking_shelve --> Web_respond200 : [Shelved after a Returned close]`). No
  `<<join>>` pseudo-state: it would add arrows the table does not have.
- `verify_chain_grammar.py` fails a chain file with no ```mermaid
  `stateDiagram-v2` block, and rejects a `sequenceDiagram`.

## Contract impact

| Invariant | Status | Evidence or re-entry |
|---|---|---|
| Action outcomes and response contracts | `preserved` | The table is unchanged in kind; the rules only say how to draw it |
| Action ordering and sync deduplication | `preserved` | — |
| Flow-token lineage | `preserved` | — |
| Storage/retention semantics | `preserved` | — |

## Impact matrix

| Surface | Touched? | How |
|---|---|---|
| Engine/runtime implementation | no | — |
| Gate scripts | yes | `verify_chain_grammar.py` requires the diagram; docstring records why |
| Gate tests | yes | `test_join_collect_grammar.py` (missing diagram, sequence diagram) and the 01b fixture in `test_stage_workflow.py` |
| Templates | yes | `templates/chain-table.md` §"Diagram (required)" and its derivation rules; the 01b stage contract in the skeleton and in every feature |
| Methodology docs | yes | `STAGES.md` 01b row names the table **and** its diagram |
| Corpus | no | — |
| Feature artefacts | no | Every existing chain file already carried a diagram (13 of 13), so nothing is retrofitted |

## Test matrix

| Invariant | Test level | Command or test | Status | Evidence |
|---|---|---|---|---|
| A chain file with no diagram fails | unit | `test_join_collect_grammar.py::…test_grammar_verifier_requires_the_state_diagram` | pass | — |
| A `sequenceDiagram` does not satisfy it | unit | `…test_grammar_verifier_rejects_a_sequence_diagram` | pass | — |
| Join rows still parse and pass | unit | `…test_grammar_verifier_accepts_composite_when` | pass | — |
| Stage advance past 01b needs a complete artefact | integration | `test_stage_workflow.py::…test_autonomous_advance_records_auto_approved_and_unblocks_precondition` | pass | — |
| Whole gate suite | unit | `pytest quality-gate/tests -q` | pass | 170 passed |
| Existing chain files unaffected | integration | `verify_chain_grammar.py` over both repos' 01b outputs | pass | clad 16 rows; experiment 12 rows |

## Gates

### Design gate

Approved in-conversation: close the two derivation gaps and the
optional/required contradiction that let a diagram be omitted.

### Evidence gate

To be recorded before commit.

## Notes

- The change is enforcement of an existing *practice*, not a new practice:
  every chain file in the seed and in the experiment already had a diagram. The
  heading and the missing rules were the defect.
- `methodology/architecture/SYNCHRONIZATIONS.md` §"Aggregation"/"Collect" already
  describes the join semantics; the gap was only their depiction.
