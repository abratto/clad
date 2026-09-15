#!/usr/bin/env python3
"""Coverage for the cross-feature shared-concept contract drift guard."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "quality-gate" / "verify_shared_action_contracts.py"


def write_spec(features, feature, concept, body):
    d = features / feature / "stages/02_concepts/output"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{concept}.concept.md").write_text(body, encoding="utf-8")


def run(features):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--features-dir", str(features)],
        cwd=REPO_ROOT, capture_output=True, text=True)


def spec(action_line, outcome):
    return (f"concept C\n\n## Actions\n\n"
            f"```\n{action_line}\n    flow token: {{ outcome: \"{outcome}\" }}\n```\n")


class SharedActionContractTests(unittest.TestCase):

    def test_disjoint_outcome_vocabularies_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp)
            write_spec(f, "UC-01-a", "C", spec("count [ articleIds ] => [ Counts ]", "Counts"))
            write_spec(f, "UC-02-b", "C", spec("count [ articleIds ] => [ Counted ]", "Counted"))
            r = run(f)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("disjoint outcome vocabularies", r.stdout)

    def test_subset_outcomes_and_same_inputs_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp)
            write_spec(f, "UC-01-a", "C", spec("send [ token ] => [ Sent ]", "Sent\n    outcome: \"Refused\""))
            write_spec(f, "UC-02-b", "C", spec("send [ token ] => [ Sent ]", "Sent"))
            r = run(f)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)

    def test_incompatible_input_shapes_warn_not_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp)
            write_spec(f, "UC-01-a", "C", spec("view [ userId ] => [ Seen ]", "Seen"))
            write_spec(f, "UC-02-b", "C", spec("view [ authorRefs ] => [ Seen ]", "Seen"))
            r = run(f)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("WARN", r.stdout)


if __name__ == "__main__":
    unittest.main()
