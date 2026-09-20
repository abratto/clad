#!/usr/bin/env python3
"""Regression coverage for verify_sync_flow_pin.py.

A flow token scopes a match to one flow, but within a flow any rule whose `when`
matches fires — so two use cases sharing a completion fire each other's rules
unless every non-bootstrap rule names its flow root with its route
(maintenance/sync-flow-pinning.md)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run([sys.executable, str(QG / "verify_sync_flow_pin.py"), *args],
                          cwd=REPO_ROOT, capture_output=True, text=True)


def write_sync(features, feature, name, when):
    path = features / feature / "stages/03_syncs/output" / f"{name}.sync.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"sync {name}\n\n## Sync Contract Matrix\n\n"
        "| Source row | Target row | `when` signature | `then` signature | Allowed literals |\n"
        "|---|---|---|---|---|\n| `1` | `2` | x | y | `<none>` |\n\n"
        "## Rule\n\n```\n" + when + "\n```\n", encoding="utf-8")


PINNED = """when {
    requested: Web/request: [ route: "returns" ] => [ Routed ; ... ]
    Lending/close: [ ... ] => [ Returned ; ... ]
}"""

BOOTSTRAP = """when {
    Web/request: [ route: "returns" ] => [ Routed ; ... ]
}"""

UNPINNED = """when {
    Lending/close: [ ... ] => [ Returned ; ... ]
}"""

NO_ROUTE = """when {
    requested: Web/request: [ ... ] => [ Routed ; ... ]
    Lending/close: [ ... ] => [ Returned ; ... ]
}"""


class FlowPinTests(unittest.TestCase):

    def test_pinned_rule_passes_and_bootstrap_is_exempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            write_sync(features, "UC-01-x", "RespondWhenCloseReturned", PINNED)
            write_sync(features, "UC-01-x", "VerifyWhenRequestRouted", BOOTSTRAP)
            result = run("--features-dir", str(features))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_unpinned_rule_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            write_sync(features, "UC-01-x", "CloseWhenVerifyVerified", UNPINNED)
            result = run("--features-dir", str(features))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("never names the flow root", result.stdout)

    def test_pin_without_a_route_fails(self):
        """A route is required: without it two routes look like one flow."""
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            write_sync(features, "UC-01-x", "CloseWhenVerifyVerified", NO_ROUTE)
            result = run("--features-dir", str(features))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("without its route", result.stdout)


if __name__ == "__main__":
    unittest.main()
