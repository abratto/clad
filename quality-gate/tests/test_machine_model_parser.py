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

    def test_comments_and_blank_lines_ignored(self):
        m = ap.parse_machine_model(_wrap(
            "# a comment\n\nfact domain : ClientId -> Domain -- mandatory\n"))
        self.assertEqual(len(m.facts), 1)


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
