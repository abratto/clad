#!/usr/bin/env python3
"""Regression coverage for the Stage 03b `## Machine model` block parser."""

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import artifact_parsers as ap  # noqa: E402
import generate_data_model as gdm  # noqa: E402


def _wrap(body: str) -> str:
    return (
        "# Example — conceptual data model\n\n"
        "## Step 2 — Draft fact model\n\n- prose\n\n"
        "## Machine model\n\n```\n" + body + "```\n"
    )


class MachineModelParserTests(unittest.TestCase):

    def test_conceptual_model_heading_is_accepted(self):
        text = (
            "# Example\n\n## Conceptual model\n\n```\n"
            "object-type UserId identified-by UserId\n"
            "fact name : UserId -> Name -- mandatory\n"
            "```\n")
        m = ap.parse_machine_model(text)
        self.assertTrue(m.present)
        self.assertEqual([f.field for f in m.facts], ["name"])

    def test_absent_block_reports_not_present(self):
        m = ap.parse_machine_model("# Example\n\n## Step 2\n\n- prose\n")
        self.assertFalse(m.present)
        self.assertEqual(m.facts, [])

    def test_parses_object_types_and_facts(self):
        m = ap.parse_machine_model(_wrap(
            "object-type UserId identified-by UserId\n"
            "fact passwordHash : UserId -> PasswordHash -- mandatory\n"
            "fact lockedUntil : UserId -> Timestamp -- optional\n"))
        self.assertTrue(m.present)
        self.assertEqual(m.object_types, {"UserId": "UserId"})
        self.assertEqual([f.field for f in m.facts], ["passwordHash", "lockedUntil"])
        self.assertEqual(m.facts[0].multiplicity, "mandatory")
        self.assertEqual(m.facts[1].multiplicity, "optional")

    def test_unique_annotation_sets_flag(self):
        m = ap.parse_machine_model(_wrap(
            "fact username : UserId -> String -- mandatory, unique across all users\n"))
        self.assertTrue(m.facts[0].unique)

    def test_state_relations_accept_compound_subjects(self):
        """A `(Category, Currency)` subject survives the shared state parser.

        Regression (expense-app UC-02): the parser's character class excluded
        parentheses, so SpendBudget parsed as stateless and 03b would drop its
        facts (and Rmap would create no budget table).
        """
        relations = ap.parse_state_relations([
            "budgetAmount: (Category, Currency) -> Int -- mandatory",
            "budgetCommitted: (Category, Currency) -> Int -- mandatory",
        ])
        self.assertEqual([r.field for r in relations],
                         ["budgetAmount", "budgetCommitted"])
        self.assertEqual(relations[0].subject_type, "(Category, Currency)")
        self.assertEqual(relations[0].value_type, "Int")
        self.assertEqual(relations[0].multiplicity, "mandatory")

    def test_parses_compound_multi_subtype_independent(self):
        m = ap.parse_machine_model(_wrap(
            "object-type FirmUri identified-by FirmUri\n"
            "fact provides : FirmUri -> { Service } -- zero or more\n"
            "fact serviceJurisdiction : ( FirmUri, Service ) -> Jurisdiction -- optional\n"
            "Manager is a Staff -- mapping: absorb\n"
            "independent AuditRef\n"))
        self.assertEqual(m.facts[0].subject_type, "FirmUri")
        self.assertTrue(m.facts[1].subject_type.startswith("( FirmUri"))
        self.assertEqual(m.subtypes, [("Manager", "Staff", "absorb")])
        self.assertEqual(m.independent, ["AuditRef"])

    def test_subtype_defaults_to_separate(self):
        m = ap.parse_machine_model(_wrap("Manager is a Staff\n"))
        self.assertEqual(m.subtypes, [("Manager", "Staff", "separate")])

    def test_unknown_clause_is_reported_not_dropped(self):
        m = ap.parse_machine_model(_wrap(
            "fact ok : UserId -> String -- mandatory\n"
            "facts typo : UserId -> String\n"))
        self.assertEqual(len(m.facts), 1)
        self.assertEqual(len(m.errors), 1)
        self.assertIn("unrecognized", m.errors[0])

    def test_duplicate_object_type_is_reported(self):
        m = ap.parse_machine_model(_wrap(
            "object-type UserId identified-by UserId\n"
            "object-type UserId identified-by UserId\n"))
        self.assertTrue(any("duplicate" in error for error in m.errors),
                        m.errors)

    def test_comments_and_blank_lines_ignored(self):
        m = ap.parse_machine_model(_wrap(
            "# a comment\n\nfact domain : ClientId -> Domain -- mandatory\n"))
        self.assertEqual(len(m.facts), 1)


class MachineSemanticsTests(unittest.TestCase):

    def test_snake_case_column_collision_is_rejected(self):
        import verify_data_model as vdm
        machine = ap.parse_machine_model(_wrap(
            "object-type UserId identified-by UserId\n"
            "fact userName : UserId -> String -- mandatory\n"
            "fact user_name : UserId -> String -- mandatory\n"))
        failures = vdm.check_machine_semantics(machine)
        self.assertTrue(any("both map to column" in f for f in failures), failures)

    def test_subtype_cycle_is_rejected(self):
        import verify_data_model as vdm
        machine = ap.parse_machine_model(_wrap(
            "object-type A identified-by A\n"
            "A is a B\n"
            "B is a A\n"))
        failures = vdm.check_machine_semantics(machine)
        self.assertTrue(any("subtype cycle" in f for f in failures), failures)

    def test_unknown_subtype_mapping_is_rejected(self):
        import verify_data_model as vdm
        machine = ap.parse_machine_model(_wrap(
            "object-type A identified-by A\n"
            "object-type B identified-by B\n"
            "A is a B -- mapping: table\n"))
        failures = vdm.check_machine_semantics(machine)
        self.assertTrue(any("unknown mapping" in f for f in failures), failures)


class FidelityTests(unittest.TestCase):

    def test_edited_machine_block_fails_fidelity(self):
        import tempfile
        import verify_data_model as vdm
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            concept_dir = root / "concepts"
            data_dir = root / "data"
            concept_dir.mkdir()
            data_dir.mkdir()
            concept = ap.ConceptSpec(
                name="Thing", purpose="",
                state_lines=["label: ThingId -> String -- mandatory"], actions=[])
            (concept_dir / "Thing.concept.md").write_text(
                "concept Thing [ThingId]\n\n## State\n\n```\n"
                "label: ThingId -> String -- mandatory\n```\n",
                encoding="utf-8")
            text = gdm.render(concept)
            (data_dir / "Thing.data-model.md").write_text(
                text.replace("fact label: ThingId -> String -- mandatory",
                             "fact label: ThingId -> String -- optional"),
                encoding="utf-8")
            failures = vdm.check_machine_model_fidelity(
                str(data_dir / "Thing.data-model.md"), [str(concept_dir)])
            self.assertTrue(failures)
            self.assertIn("diverges", failures[0])


class GeneratorMachineModelTests(unittest.TestCase):

    def test_generated_block_round_trips_through_the_parser(self):
        # The generator emits a block the parser must read back identically.
        concept = ap.ConceptSpec(
            name="PasswordAuth", purpose="",
            state_lines=[
                "passwordHash: UserId -> PasswordHash     -- mandatory",
                "failedAttempts: UserId -> Int            -- mandatory, default 0",
                "lockedUntil: UserId -> Timestamp         -- optional",
            ],
            actions=[])
        text = gdm.render(concept)
        m = ap.parse_machine_model(text)
        self.assertTrue(m.present)
        self.assertIn("UserId", m.object_types)
        self.assertEqual(
            [f.field for f in m.facts],
            ["passwordHash", "failedAttempts", "lockedUntil"])

    def test_stateless_concept_emits_an_empty_present_block(self):
        concept = ap.ConceptSpec(name="Web", purpose="", state_lines=[], actions=[])
        text = gdm.render(concept)
        m = ap.parse_machine_model(text)
        self.assertTrue(m.present)
        self.assertEqual(m.facts, [])


if __name__ == "__main__":
    unittest.main()
