#!/usr/bin/env python3
"""Regression coverage for verify_mechanism_citations.py.

An active platform change must cite the code path its mechanism rests on; a
closed record is grandfathered. The load-bearing SYNCHRONIZATIONS sections
(§Naming, §Flow pinning) must cite code too."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"

RECORD = """# Maintenance change — `x`

- **Change class:** `platform`
- **Status:** `{status}`
- **Change summary:** x

{mechanism}
"""

MECHANISM_CITED = """## Mechanism

The engine binds fields to the primary conjunct — `SyncEngine.java:270`.
"""

MECHANISM_UNCITED = """## Mechanism

The engine never re-evaluates.
"""

SYNC_DOC = """# Syncs

## Naming

Action-first. {cite}

### Flow pinning

The pin goes last. {cite}
"""


def run(*args):
    return subprocess.run(
        [sys.executable, str(QG / "verify_mechanism_citations.py"), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class MechanismCitationTests(unittest.TestCase):

    def _run(self, root):
        return run("--maintenance-dir", str(root / "maintenance"),
                   "--sync-doc", str(root / "sync.md"))

    def test_active_platform_record_without_citation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "maintenance/x.md",
                  RECORD.format(status="active", mechanism=MECHANISM_UNCITED))
            write(root / "sync.md", SYNC_DOC.format(cite="`F.java:1`"))
            result = self._run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no `## Mechanism`", result.stdout)

    def test_active_platform_record_with_citation_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "maintenance/x.md",
                  RECORD.format(status="active", mechanism=MECHANISM_CITED))
            write(root / "sync.md", SYNC_DOC.format(cite="`F.java:1`"))
            result = self._run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_closed_record_is_not_checked(self):
        """Forward-only: a closed record predates the rule and is ignored."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "maintenance/x.md",
                  RECORD.format(status="closed", mechanism=MECHANISM_UNCITED))
            write(root / "sync.md", SYNC_DOC.format(cite="`F.java:1`"))
            result = self._run(root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("WARN", result.stdout)

    def test_sync_doc_section_without_citation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root / "maintenance/x.md",
                  RECORD.format(status="closed", mechanism=MECHANISM_CITED))
            write(root / "sync.md", SYNC_DOC.format(cite="no code here"))
            result = self._run(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no code-path citation", result.stdout)


if __name__ == "__main__":
    unittest.main()
