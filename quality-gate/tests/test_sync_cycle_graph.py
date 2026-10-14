#!/usr/bin/env python3
"""Regression coverage for verify_sync_cycle_graph.py.

A *repeated invocation* is the same `<Concept>.<action>` reachable twice on ONE
execution path (a design-time cycle). Mutually exclusive branches that share the
single bootstrap action (`Web.respond`, R4) are NOT a repeat: 01b models each
outcome of one invocation as its own branch, and the cycle graph excludes the
Web bootstrap from its node set. This locks in the branch-aware reading the
Stage 03 "repeated action backstop" prose now states.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(sync_dir):
    return subprocess.run(
        [sys.executable, str(QG / "verify_sync_cycle_graph.py"),
         "--sync-dir", str(sync_dir)],
        cwd=REPO_ROOT, capture_output=True, text=True)


def write_sync(sync_dir, name, when_body, then_body):
    sync_dir.mkdir(parents=True, exist_ok=True)
    (sync_dir / f"{name}.sync.md").write_text(
        f"sync {name}\n\n## Sync Contract Matrix\n\n"
        "| Source row | Target row | `when` signature | `then` signature | Allowed literals |\n"
        "|---|---|---|---|---|\n| `1` | `2` | x | y | `<none>` |\n\n"
        "## Rule\n\n```\n"
        "when {\n" + when_body + "\n}\n"
        "then {\n" + then_body + "\n}\n"
        "```\n", encoding="utf-8")


class SyncCycleGraphTests(unittest.TestCase):

    def test_mutually_exclusive_branches_sharing_web_respond_are_not_a_cycle(self):
        # The UC-08 shape: one request, two response branches (200 / 401) that
        # are mutually exclusive. Both `then Web/respond` — not a repeat.
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "03_syncs" / "output"
            write_sync(d, "RespondOk",
                       '    GuidelineRules/publishedLineages: [ ] => [ Ok ]\n'
                       '    requested: Web/request: [ route: "x" ] => [ Routed ]',
                       "    Web/respond: [ status: 200 ]")
            write_sync(d, "RespondRefused",
                       "    Session/validate: [ ] => [ Refused ]\n"
                       '    requested: Web/request: [ route: "x" ] => [ Routed ]',
                       "    Web/respond: [ status: 401 ]")

            r = run(d)

            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("no sync cycles", r.stdout)

    def test_a_true_repeated_invocation_is_a_cycle(self):
        # `A/x` completes → `B/y`; `B/y` completes → `A/x` again. The same
        # action is reachable twice on one path — a genuine repeat.
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "03_syncs" / "output"
            write_sync(d, "AtoB", "    A/x: [ ] => [ ]", "    B/y: [ ]")
            write_sync(d, "BtoA", "    B/y: [ ] => [ ]", "    A/x: [ ]")

            r = run(d)

            self.assertNotEqual(r.returncode, 0)
            self.assertIn("cycle", r.stdout.lower())


if __name__ == "__main__":
    unittest.main()
