#!/usr/bin/env python3
"""Regression coverage for the process-domain Axiomatic Design work
(maintenance change `ad-process-domain`): `sync_information.py`'s binding
profile and its advisory wiring at Stage 03."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "quality-gate" / "sync_information.py"
UC00 = REPO_ROOT / "examples" / "UC-00-login" / "stages" / "03_syncs" / "output"

sys.path.insert(0, str(REPO_ROOT / "quality-gate"))
import clad_stages as cs  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          cwd=REPO_ROOT, capture_output=True, text=True)


SYNC_WITH_D_AND_WIDE_JOIN = """sync LoanAlertWhenBorrowAndHeld

## Rule

when {
    borrow: Lending/borrow: [ loan: ?loan ] => [ Borrowed ]
    held: Hold/place: [ loan: ?loan ] => [ Placed ]
    requested: Web/request: [ route: "loans" ] => [ Routed ]
}
where {
    absent ( "Lending" ; ?loan ; "returnedAt" )
}

## Where clause patterns (for Stage 03a audit)

| Binding | Pattern | Source |
|---|---|---|
| `?loan` | A | Trigger token (`Lending/borrow` input) |
| `?returnedAt` | B | Flow-sibling output — `Hold/place` completion |
| `"open"` | C | Sync constant |
| `absent("Lending", ?loan, "returnedAt")` | D | Concept-state read — `Lending` region |

## Cites

- `../01_usecase/output/usecase.md` — scenario `loan-alert`
"""


class ProfileParsingTests(unittest.TestCase):

    def test_real_worked_example_profile_is_exact(self):
        proc = run("--sync-dir", str(UC00))
        self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
        self.assertIn("Aggregate: A=3 B=3 C=7 D=0  (13 bindings)", proc.stdout)
        self.assertIn("LookupByUsernameForLoginWhenRequestRouted: "
                      "A=2 B=0 C=0 D=0 join=1", proc.stdout)
        self.assertIn("GrantForLoginWhenCheckOk: A=0 B=1 C=0 D=0 join=2",
                      proc.stdout)
        # No D reads, no arity-3 joins: no findings on the worked example.
        self.assertIn("PASS  no advisory findings", proc.stdout)

    def test_d_read_and_wide_join_produce_findings_but_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "LoanAlertWhenBorrowAndHeld.sync.md").write_text(
                SYNC_WITH_D_AND_WIDE_JOIN)
            proc = run("--sync-dir", tmp)
        self.assertEqual(0, proc.returncode,
                         "the profile is advisory — findings never block")
        self.assertIn("A=1 B=1 C=1 D=1 join=3", proc.stdout)
        self.assertIn("outcome instead of read?", proc.stdout)
        self.assertIn("concepts decide, syncs route", proc.stdout)
        self.assertIn("join arity 3", proc.stdout)

    def test_missing_table_and_empty_dir_are_skipped_not_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = run("--sync-dir", tmp)
            self.assertEqual(0, empty.returncode)
            self.assertIn("SKIP", empty.stdout)
            (Path(tmp) / "Skeleton.sync.md").write_text(
                "sync Skeleton\n\n## Rule\n\nwhen {\n    Web/request: "
                "[ route: \"x\" ] => [ Routed ]\n}\n")
            skeleton = run("--sync-dir", tmp)
            self.assertEqual(0, skeleton.returncode)
            self.assertIn("no where-pattern table", skeleton.stdout)


class Stage03WiringTests(unittest.TestCase):

    def test_stage03_carries_the_sync_information_check(self):
        stage = next(s for s in cs.STAGES if s.id == "03")
        checks = {c.name for c in stage.checks}
        self.assertIn("sync_information", checks)

    def test_check_passes_the_sync_dir(self):
        stage = next(s for s in cs.STAGES if s.id == "03")
        check = next(c for c in stage.checks if c.name == "sync_information")
        args = check.build_args("features/UC-00-login")
        self.assertEqual(["--sync-dir", os.path.join(
            "features", "UC-00-login", "stages", "03_syncs", "output")], args)

    def test_script_always_advisory(self):
        text = SCRIPT.read_text()
        self.assertIn("return 0", text,
                      "the profile's findings must never change the exit code")


if __name__ == "__main__":
    unittest.main()
