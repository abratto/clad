#!/usr/bin/env python3
"""Regression coverage for verify_collection_coverage.py.

Guards the forward-only cardinality gate: a collection-shaped feature must
declare empty / multi-item / repeated-key fixtures at Stage 04c; closed
features are grandfathered (no retrofit); non-collection features skip.
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


def feature(root, *, chain, spec="", coverage=None, closed=False):
    write(root / "stages/01b_chain-table/output/x-chain.md", chain)
    write(root / "stages/04_implement/04b_contract/output/X.contract.md", spec)
    write(root / "stages/04_implement/04c_flow-tests/output/stubs.md",
          coverage if coverage is not None else "# stubs\n")
    if closed:
        write(root / "stages/05_verify/output/trace.md", "Resume point: closed\n")
    return root


COLLECTION_CHAIN = (
    "# Chain\n| 9 | `Catalog.lookupBySlug[Found]` | `Web.respond[200]` | "
    "`{\"articles\": [...], \"articlesCount\": N}` | `Sent` |\n"
)

GOOD_COVERAGE = (
    "# Flow-test stubs\n\n## Collection coverage\n\n"
    "- Binding: `articles` (page) + `following` (parallel flags)\n"
    "- empty: zero followed authors -> `{\"articles\": [], \"articlesCount\": 0}`\n"
    "- multi-item: 3 articles, newest-first\n"
    "- repeated-key: art-1/art-3 share author `mina` (positional alignment)\n"
)


class CollectionCoverageTests(unittest.TestCase):
    def test_non_collection_feature_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = feature(Path(temporary) / "UC-90-x",
                           chain="# Chain\n| 2 | `Session.validate[Validated]` | "
                                 "`Web.respond[200]` | `{\"user\": {...}}` | `Sent` |\n")
            result = run(str(QG / "verify_collection_coverage.py"), "--feature", str(root))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP", result.stdout)

    def test_closed_collection_feature_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = feature(Path(temporary) / "UC-91-x", chain=COLLECTION_CHAIN, closed=True)
            result = run(str(QG / "verify_collection_coverage.py"), "--feature", str(root))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP", result.stdout)

    def test_collection_feature_with_declaration_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = feature(Path(temporary) / "UC-92-x", chain=COLLECTION_CHAIN,
                           coverage=GOOD_COVERAGE)
            result = run(str(QG / "verify_collection_coverage.py"), "--feature", str(root))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_collection_feature_missing_section_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = feature(Path(temporary) / "UC-93-x", chain=COLLECTION_CHAIN,
                           coverage="# stubs\nno coverage section here\n")
            result = run(str(QG / "verify_collection_coverage.py"), "--feature", str(root))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Collection coverage", result.stdout)

    def test_collection_feature_missing_multi_item_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = feature(Path(temporary) / "UC-94-x", chain=COLLECTION_CHAIN,
                           coverage="## Collection coverage\n"
                                    "- empty: no articles\n"
                                    "- repeated-key: n/a\n")
            result = run(str(QG / "verify_collection_coverage.py"), "--feature", str(root))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("multi-item", result.stdout)

    def test_advisory_downgrades_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = feature(Path(temporary) / "UC-95-x", chain=COLLECTION_CHAIN,
                           coverage="# stubs\n")
            result = run(str(QG / "verify_collection_coverage.py"), "--feature", str(root),
                         "--advisory")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("WARN", result.stdout)

    def test_list_field_spec_is_collection_shaped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = feature(Path(temporary) / "UC-96-x",
                           chain="# Chain\n| 2 | `A.b[C]` | `Web.respond[200]` | ok | `Sent` |\n",
                           spec="### `list()`\n\n- **Flow token:** `X.list { action, items: List<Item>, outcome }`\n")
            result = run(str(QG / "verify_collection_coverage.py"), "--feature", str(root))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FAIL", result.stdout)


    def test_feature_only_output_is_not_silently_skipped(self):
        """A `.feature`-only 04c output must still be checked.

        The `## Collection coverage` carrier is optional in the stage contract,
        so keying "did 04c run?" on markdown made this check a no-op for the
        common case — the cardinality edges it exists for never ran."""
        with tempfile.TemporaryDirectory() as temporary:
            root = feature(Path(temporary) / "UC-97-x", chain=COLLECTION_CHAIN)
            flow_dir = root / "stages/04_implement/04c_flow-tests/output"
            (flow_dir / "stubs.md").unlink()
            write(flow_dir / "x.feature", "@x\nFeature: X\n")
            result = run(str(QG / "verify_collection_coverage.py"), "--feature", str(root))
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Collection coverage", result.stdout)


if __name__ == "__main__":
    unittest.main()
