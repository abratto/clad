#!/usr/bin/env python3
"""Regression coverage for verify_concept_additivity.py.

Guards Model B's additive-only convention mechanically: a feature that extends
a canonical corpus concept may add fact types, constraints, actions and
outcomes, but must not quietly drop or restate them. Without this the
convention is social — `_state_changed` is a *difference* test, so a removal
looks like an addition and promotion copies it over the canonical entry.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run([sys.executable, *args], cwd=REPO_ROOT,
                          capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def response_table(origin):
    return (
        "| Concept | Origin | Owned state (one line) | Owned actions | Notes |\n"
        "|---|---|---|---|---|\n"
        f"| `MemberEnrolment` | `{origin}` | *(canonical)* | `enrol`, `verify` | — |\n"
    )


def spec(state_lines, actions=""):
    body = "\n".join(state_lines)
    return (
        "concept MemberEnrolment [MemberId]\n"
        "introduced-by UC-01-x\n"
        "purpose\n"
        "    to enrol a person\n"
        "\n"
        "## State\n"
        "\n"
        "```\n"
        f"{body}\n"
        "```\n"
        "\n"
        "## Actions\n"
        "\n"
        "```\n"
        f"{actions}"
        "```\n"
    )


ENROL_ACTION = (
    "enrol [ ref: String ; name: String ] => [ memberId: MemberId ]\n"
    "    records the member\n"
)


def contract(outcomes="`ENROLLED`, `INVALID_NAME`, `DUPLICATE_REF`"):
    return (
        "<!-- derived from templates/contract.md -->\n"
        "# MemberEnrolment — contract\n"
        "\n"
        "## Actions\n"
        "\n"
        "### `enrol(ref, name) -> MemberId`\n"
        "\n"
        "- **Inputs:** `ref: String`, `name: String`\n"
        f"- **Outcomes (enum):** {outcomes}\n"
        "- **Flow token:** `MemberEnrolment.enrol { ref, name, memberId?, outcome }`\n"
    )


CANON_STATE = ["ref: MemberId -> String", "name: MemberId -> String"]


class AdditivityTests(unittest.TestCase):

    def feature(self, root, *, origin="extends:UC-01-x", proposal_state=None,
                proposal_contract=None, exception=None):
        write(root / "stages/01a_responsibility-map/output/responsibility-map.md",
              response_table(origin))
        if proposal_state is not None:
            write(root / "stages/02_concepts/output/MemberEnrolment.concept.md",
                  spec(proposal_state, ENROL_ACTION))
        if proposal_contract is not None:
            write(root / "stages/04_implement/04b_contract/output/"
                  "MemberEnrolment.contract.md", proposal_contract)
        if exception is not None:
            write(root / "_config/additivity-exceptions.md", exception)
        return root

    def corpus(self, temporary):
        root = Path(temporary) / "corpus"
        write(root / "MemberEnrolment.concept.md", spec(CANON_STATE, ENROL_ACTION))
        write(root / "MemberEnrolment.contract.md", contract())
        return root

    def test_reused_and_new_only_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.feature(Path(temporary) / "UC-90-x", origin="reused:UC-01-x")
            result = run(str(QG / "verify_concept_additivity.py"),
                         "--feature", str(root), "--corpus", str(self.corpus(temporary)))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP", result.stdout)

    def test_additive_extend_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.feature(
                Path(temporary) / "UC-91-x",
                proposal_state=CANON_STATE + ["lastSeen: MemberId -> Timestamp"],
                proposal_contract=contract())
            result = run(str(QG / "verify_concept_additivity.py"),
                         "--feature", str(root), "--corpus", str(self.corpus(temporary)))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_dropped_state_line_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.feature(Path(temporary) / "UC-92-x",
                                proposal_state=["ref: MemberId -> String"])
            result = run(str(QG / "verify_concept_additivity.py"),
                         "--feature", str(root), "--corpus", str(self.corpus(temporary)))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("name: MemberId -> String", result.stdout)
            self.assertIn("not additive", result.stdout)

    def test_restated_state_line_fails(self):
        """A changed value type reads as a removal — it needs authorisation."""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.feature(
                Path(temporary) / "UC-93-x",
                proposal_state=["ref: MemberId -> Int", "name: MemberId -> String"])
            result = run(str(QG / "verify_concept_additivity.py"),
                         "--feature", str(root), "--corpus", str(self.corpus(temporary)))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ref: MemberId -> String", result.stdout)

    def test_dropped_contract_outcome_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.feature(
                Path(temporary) / "UC-94-x",
                proposal_state=CANON_STATE,
                proposal_contract=contract(outcomes="`ENROLLED`, `INVALID_NAME`"))
            result = run(str(QG / "verify_concept_additivity.py"),
                         "--feature", str(root), "--corpus", str(self.corpus(temporary)))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("`DUPLICATE_REF`", result.stdout)

    def test_re_aligned_state_lines_are_not_a_restatement(self):
        """Adding a longer relation re-flows the comment column.

        Comparing raw text read a re-alignment as dropping every line above it;
        the column is presentation, not the fact type."""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.feature(
                Path(temporary) / "UC-98-x",
                proposal_state=["ref:    MemberId -> String",
                                "name:   MemberId -> String",
                                "lastSeen: MemberId -> Timestamp"],
                proposal_contract=contract())
            result = run(str(QG / "verify_concept_additivity.py"),
                         "--feature", str(root), "--corpus", str(self.corpus(temporary)))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_missing_proposal_contract_fails(self):
        """A canonical contract exists but the proposal produced none — a
        dropped contract is a defect, not a skip."""
        with tempfile.TemporaryDirectory() as temporary:
            root = self.feature(
                Path(temporary) / "UC-97-x",
                proposal_state=CANON_STATE)
            result = run(str(QG / "verify_concept_additivity.py"),
                         "--feature", str(root), "--corpus", str(self.corpus(temporary)))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dropped contract", result.stdout.lower())

    def test_authorised_exception_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = self.feature(
                Path(temporary) / "UC-95-x",
                proposal_state=["ref: MemberId -> String"],
                proposal_contract=contract(),
                exception="- `name: MemberId -> String` — retired in maintenance #12\n")
            result = run(str(QG / "verify_concept_additivity.py"),
                         "--feature", str(root), "--corpus", str(self.corpus(temporary)))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("authorised exception", result.stdout)


if __name__ == "__main__":
    unittest.main()
