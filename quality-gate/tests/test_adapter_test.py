#!/usr/bin/env python3
"""Regression coverage for the blocking adapter end-to-end test check."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
SCRIPT = QG / "verify_adapter_test.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          cwd=REPO_ROOT, capture_output=True, text=True)


def make_feature(tmp, *, chain=True, tests=None, test_root=True):
    feature = Path(tmp) / "features/UC-01-x"
    chain_dir = feature / "stages/01b_chain-table/output"
    chain_dir.mkdir(parents=True)
    if chain:
        (chain_dir / "x-chain.md").write_text(
            "# Chain table\n\n"
            "| # | When | Then | Inputs | Outcome | Why |\n"
            "|---|---|---|---|---|---|\n"
            "| 1 | `Web/request[POST /x]` | `Web.request` | `x` | `ROUTED` | entry |\n",
            encoding="utf-8")
    root = Path(tmp) / "app/src/test/java"
    if test_root:
        root.mkdir(parents=True)
    for name, text in (tests or {}).items():
        (root / name).write_text(text, encoding="utf-8")
    return feature, root


class AdapterTestCheckTests(unittest.TestCase):

    def test_enabled_adapter_test_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, root = make_feature(tmp, tests={"FooFlowTest.java": "class FooFlowTest {}"})
            r = run("--feature-root", feature, "--test-source-root", root)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_missing_adapter_test_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, root = make_feature(tmp)
            r = run("--feature-root", feature, "--test-source-root", root)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_disabled_present_at_04c_but_fails_when_enabled_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, root = make_feature(
                tmp, tests={"FooIntegrationTest.java": "@Disabled\nclass FooIntegrationTest {}"})
            at_04c = run("--feature-root", feature, "--test-source-root", root)
            self.assertEqual(at_04c.returncode, 0, at_04c.stdout + at_04c.stderr)
            at_05 = run("--feature-root", feature, "--test-source-root", root,
                        "--require-enabled")
            self.assertEqual(at_05.returncode, 1, at_05.stdout + at_05.stderr)

    def test_no_adapter_surface_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, root = make_feature(tmp, chain=False, tests={"FooFlowTest.java": "class FooFlowTest {}"})
            r = run("--feature-root", feature, "--test-source-root", root)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("no adapter surface", r.stdout)

    def test_no_test_root_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, _root = make_feature(tmp, test_root=False)
            r = run("--feature-root", feature, "--test-source-root", "")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("no test source root", r.stdout)

    def test_foreign_enabled_test_does_not_satisfy_the_gate(self):
        """The feature's own e2e test is @Disabled; another feature's enabled
        test sits in the same root and must not make the gate PASS."""
        with tempfile.TemporaryDirectory() as tmp:
            feature, root = make_feature(tmp, tests={
                "ForeignFlowTest.java": "class ForeignFlowTest {}",
                "OwnHttpIntegrationTest.java":
                    "@Disabled\nclass OwnHttpIntegrationTest {}",
            })
            spec = (feature / "stages/04_implement/04c_acceptance-tests/"
                    "output/acceptance-spec.md")
            spec.parent.mkdir(parents=True)
            spec.write_text(
                "# Acceptance spec\n\n## Scenario: x\n\n"
                "- **Test:** `OwnHttpIntegrationTest.someCase`\n",
                encoding="utf-8")
            at_04c = run("--feature-root", feature, "--test-source-root", root)
            self.assertEqual(at_04c.returncode, 0, at_04c.stdout + at_04c.stderr)
            at_05 = run("--feature-root", feature, "--test-source-root", root,
                        "--require-enabled")
            self.assertEqual(at_05.returncode, 1, at_05.stdout + at_05.stderr)


if __name__ == "__main__":
    unittest.main()
