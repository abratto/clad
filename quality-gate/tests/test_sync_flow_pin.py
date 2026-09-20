#!/usr/bin/env python3
"""Regression coverage for verify_sync_flow_pin.py.

A flow token scopes a match to one flow, but within a flow any rule whose `when`
matches fires — so two use cases sharing a completion fire each other's rules
unless every non-bootstrap rule names its flow root last, with its route
(maintenance/sync-flow-pinning.md). The pin is last, not first: the engine binds
`triggerField`/`triggerInput` to the primary (first) conjunct, so a pin before
the domain trigger blanks the rule's arguments. The pin's route is also checked
against the feature's Stage 01b chains, which are where the generator derives it
from."""

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


def write_chain(features, feature, scenario, root_when):
    path = features / feature / "stages/01b_chain-table/output" / f"{scenario}-chain.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Chain table\n\n"
        "| # | When | Then | Inputs | Outcome | Why this step |\n"
        "|---|---|---|---|---|---|\n"
        f"| 1 | `{root_when}` | `Web.request` | `x` | `Routed` | entry |\n"
        "| 2 | `Web.request[Routed]` | `Lending.close` | `x` | `Returned` | step |\n",
        encoding="utf-8")


PINNED = """when {
    Lending/close: [ ... ] => [ Returned ; ... ]
    requested: Web/request: [ route: "returns" ] => [ Routed ; ... ]
}"""

BOOTSTRAP = """when {
    Web/request: [ route: "returns" ] => [ Routed ; ... ]
}"""

UNPINNED = """when {
    Lending/close: [ ... ] => [ Returned ; ... ]
}"""

NO_ROUTE = """when {
    Lending/close: [ ... ] => [ Returned ; ... ]
    requested: Web/request: [ ... ] => [ Routed ; ... ]
}"""

PIN_FIRST = """when {
    requested: Web/request: [ route: "returns" ] => [ Routed ; ... ]
    Lending/close: [ ... ] => [ Returned ; ... ]
}"""

PIN_MIDDLE = """when {
    closed: Lending/close: [ ... ] => [ Returned ; ... ]
    requested: Web/request: [ route: "returns" ] => [ Routed ; ... ]
    shelved: Stocking/shelve: [ ... ] => [ Shelved ; ... ]
}"""

TWO_ROOTS = """when {
    closed: Lending/close: [ ... ] => [ Returned ; ... ]
    requested: Web/request: [ route: "returns" ] => [ Routed ; ... ]
    requested: Web/request: [ route: "returns" ] => [ Routed ; ... ]
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

    def test_pin_before_the_domain_trigger_fails(self):
        """The pin must be last: the engine binds trigger fields to the primary.

        A pin first passes a naive "route present" check but blanks
        `triggerField`/`triggerInput`, which is exactly the defect the position
        rule guards (see maintenance/sync-flow-pinning.md §Review finding)."""
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            write_sync(features, "UC-01-x", "CloseWhenVerifyVerified", PIN_FIRST)
            result = run("--features-dir", str(features))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not the LAST conjunct", result.stdout)

    def test_pin_in_the_middle_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            write_sync(features, "UC-01-x", "RespondWhenJoinReturned", PIN_MIDDLE)
            result = run("--features-dir", str(features))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not the LAST conjunct", result.stdout)

    def test_two_flow_roots_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            write_sync(features, "UC-01-x", "RespondWhenJoinReturned", TWO_ROOTS)
            result = run("--features-dir", str(features))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("more than one flow root", result.stdout)

    def test_pin_matching_the_chain_route_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            write_chain(features, "UC-01-x", "return-copy", "Web/request[POST /returns]")
            write_sync(features, "UC-01-x", "RespondWhenCloseReturned", PINNED)
            result = run("--features-dir", str(features))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pin_drifted_from_the_chain_route_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            write_chain(features, "UC-01-x", "return-copy", "Web/request[POST /returns]")
            write_sync(features, "UC-01-x", "RespondWhenCloseReturned",
                       PINNED.replace('"returns"', '"loans"'))
            result = run("--features-dir", str(features))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("drifted from its chain", result.stdout)


if __name__ == "__main__":
    unittest.main()
