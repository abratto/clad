#!/usr/bin/env python3
"""Regression coverage for corpus_status.py (maintenance change
`corpus-status-command`): read-only corpus health report — history, stale
snapshots, dependence in-degree, remodel-candidate flags."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "quality-gate" / "corpus_status.py"

SPEC = """concept {name} [UserId]
introduced-by {introducer}
{extended}purpose
    to {lower}

## State

```
{lower}At: UserId -> Timestamp   -- mandatory
```
"""

DEPENDENCE = """# Concept dependence — test

## Edges

| Concept | requires | Why (extrinsic, app-specific) |
|---|---|---|
| `PasswordAuth` | `UserNaming` | needs the user id |
| `Session` | `UserNaming` | needs the user id |
| `Profile` | `UserNaming` | needs the user id |
"""


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          cwd=REPO_ROOT, capture_output=True, text=True)


def spec(name, introducer, extenders=()):
    extended = ("extended-by " + ", ".join(extenders) + "\n") if extenders else ""
    return SPEC.format(name=name, introducer=introducer,
                       extended=extended, lower=name.lower())


def make_corpus(tmp):
    root = Path(tmp)
    corpus = root / "features" / "_system" / "concepts"
    corpus.mkdir(parents=True)
    (corpus / "UserNaming.concept.md").write_text(
        spec("UserNaming", "UC-00-login"), encoding="utf-8")
    (corpus / "Session.concept.md").write_text(
        spec("Session", "UC-00-login", ["UC-01-a", "UC-02-b", "UC-03-c"]),
        encoding="utf-8")
    (root / "features" / "_system" / "concept-dependence.md").write_text(
        DEPENDENCE, encoding="utf-8")
    # UC-00-login holds a stale snapshot of Session (diverged from canonical).
    snap = root / "features" / "UC-00-login" / "stages" / "02_concepts" / "output"
    snap.mkdir(parents=True)
    (snap / "Session.concept.md").write_text(
        spec("Session", "UC-00-login"), encoding="utf-8")
    return str(root / "features")


class CorpusStatusTests(unittest.TestCase):

    def test_empty_corpus_reports_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("--features-dir", tmp)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Corpus is empty", result.stdout)

    def test_reports_history_indegree_and_current_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("--features-dir", make_corpus(tmp))
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            self.assertIn("UserNaming", result.stdout)
            self.assertIn("in-degree      : 3", result.stdout)
            self.assertIn("current source : UC-03-c", result.stdout)
            # Sorted by in-degree descending: UserNaming before Session.
            self.assertLess(result.stdout.index("UserNaming"),
                            result.stdout.index("  Session"))

    def test_stale_snapshot_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("--features-dir", make_corpus(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertIn("stale snapshot(s): UC-00-login", result.stdout)

    def test_deep_history_flags_remodel_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("--features-dir", make_corpus(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertIn("REMODEL CANDIDATE", result.stdout)
            self.assertIn("Remodel candidates: Session", result.stdout)

    def test_shallow_history_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            corpus = root / "features" / "_system" / "concepts"
            corpus.mkdir(parents=True)
            (corpus / "Session.concept.md").write_text(
                spec("Session", "UC-00-login", ["UC-01-a"]), encoding="utf-8")
            result = run("--features-dir", str(root / "features"))
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("REMODEL CANDIDATE", result.stdout)

    def test_real_seed_repo_corpus_runs_clean(self):
        # The seed corpus is empty; the command must not crash on it.
        result = run("--features-dir", str(REPO_ROOT / "features"))
        self.assertEqual(result.returncode, 0,
                         result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
