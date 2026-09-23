#!/usr/bin/env python3
"""Regression coverage for verify_reference_integrity.py and rename_sync.py.

A sync/concept rename leaves a tail — cards, derivation maps, traces, the
README, the Java rule and test class cite the artefact by name. These lock the
tail-catcher and the one-step rename."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(script, *args):
    return subprocess.run([sys.executable, str(QG / script), *map(str, args)],
                          cwd=REPO_ROOT, capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ReferenceIntegrityTests(unittest.TestCase):

    def _feature(self, root, doc):
        feature = root / "features/UC-01-x"
        write(feature / "stages/03_syncs/output/Keep.sync.md", "sync Keep\n")
        write(feature / "stages/03a_dependency-review/output/card.md", doc)
        return feature

    def test_dangling_sync_reference_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._feature(Path(tmp), "see `Gone.sync.md`")
            result = run("verify_reference_integrity.py",
                         "--features-dir", Path(tmp) / "features")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Gone.sync.md", result.stdout)

    def test_resolving_sync_reference_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._feature(Path(tmp), "see `Keep.sync.md`")
            result = run("verify_reference_integrity.py",
                         "--features-dir", Path(tmp) / "features")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_corpus_concept_reference_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._feature(root, "see `Widget.concept.md`")
            write(root / "features/_system/concepts/Widget.concept.md", "concept Widget\n")
            result = run("verify_reference_integrity.py",
                         "--features-dir", root / "features")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_history_directory_is_exempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = self._feature(Path(tmp), "ok")
            write(feature / "_changes/old.md", "renamed `Gone.sync.md` -> `Keep.sync.md`")
            result = run("verify_reference_integrity.py",
                         "--features-dir", Path(tmp) / "features")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_orphan_java_rule_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._feature(root, "ok")
            impl = root / "impl"
            write(impl / "S.java", 'class S { void r() { rule("Orphan"); } }\n')
            result = run("verify_reference_integrity.py",
                         "--features-dir", root / "features",
                         "--sync-impl-dir", impl)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Orphan", result.stdout)


class RenameSyncTests(unittest.TestCase):

    def test_rename_moves_the_whole_tail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature = root / "features/UC-01-x"
            write(feature / "stages/03_syncs/output/Old.sync.md",
                  "sync Old\n\n## Rule\n\n```\nwhen { X/y: [ ... ] => [ Ok ] }\n```\n")
            write(feature / "stages/03a_dependency-review/output/card.md",
                  "cites `Old.sync.md`")
            impl = root / "impl"
            write(impl / "Old.java", "class Old { void r() { rule(\"Old\"); } }\n")
            tests = root / "tests"
            write(tests / "OldTest.java", "class OldTest { }\n")

            result = run("rename_sync.py", "--feature", feature,
                         "--from", "Old", "--to", "New",
                         "--sync-impl-dir", impl, "--test-source-root", tests,
                         "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            spec = feature / "stages/03_syncs/output/New.sync.md"
            self.assertTrue(spec.is_file())
            self.assertIn("sync New", spec.read_text())
            self.assertFalse((feature / "stages/03_syncs/output/Old.sync.md").exists())
            self.assertIn("New.sync.md",
                          (feature / "stages/03a_dependency-review/output/card.md").read_text())
            self.assertTrue((impl / "New.java").is_file())
            self.assertIn('rule("New")', (impl / "New.java").read_text())
            self.assertTrue((tests / "NewTest.java").is_file())

    def test_dry_run_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "features/UC-01-x"
            write(feature / "stages/03_syncs/output/Old.sync.md", "sync Old\n")
            run("rename_sync.py", "--feature", feature, "--from", "Old", "--to", "New")
            self.assertTrue((feature / "stages/03_syncs/output/Old.sync.md").is_file())
            self.assertFalse((feature / "stages/03_syncs/output/New.sync.md").exists())


if __name__ == "__main__":
    unittest.main()
