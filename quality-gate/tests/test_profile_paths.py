#!/usr/bin/env python3
"""Regression coverage for profile-path integrity:

  1. Feature-local `_config/<key>.md` overrides (AGENTS.md §4a resolution
     order item 1) take effect in `clad_stages._read_config` — a derived
     repo can re-bind impl/test paths per feature without touching root
     clad.properties.
  2. Non-key files in `_config/` (README, voice, package-and-layout,
     build-and-test) never become phantom keys; empty/comment-only key
     files leave the root default in force.
  3. `verify_profile_paths.py` blocks (exit 1) when a configured path
     resolves outside the feature's declared package-and-layout roots,
     warns (exit 0) about seed `reference-impl/` pointers while layout
     declares elsewhere, passes quietly for seed-style agreement, and
     skips when no layout is declared.
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
SCRIPT = QG / "verify_profile_paths.py"


def run(script, *args, cwd=None):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        cwd=cwd or REPO_ROOT, capture_output=True, text=True,
    )


def make_repo(with_layout=True, layout_style="app", configure=True):
    """Build an isolated repo-root fixture and return (root, feature)."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    feature = root / "features" / "UC-01-app"
    (feature / "_config").mkdir(parents=True)
    ref_test = root / "reference-impl" / "java-legible" / "src" / "test" / "java" \
        / "dev" / "legible"
    ref_main = root / "reference-impl" / "java-legible" / "src" / "main" / "java" \
        / "dev" / "legible" / "example" / "login"
    ref_test.mkdir(parents=True)
    ref_main.mkdir(parents=True)
    app_test = root / "app" / "src" / "test" / "java" / "dev" / "foodsaver" / "steps"
    app_main = root / "app" / "src" / "main" / "java" / "dev" / "foodsaver"
    app_test.mkdir(parents=True)
    app_main.mkdir(parents=True)
    if configure:
        (root / "clad.properties").write_text(
            "test.source.root=reference-impl/java-legible/src/test/java/dev/legible\n"
            "sync.impl.dir=reference-impl/java-legible/src/main/java/dev/legible/example/login\n"
            "concept.impl.dir=reference-impl/java-legible/src/main/java/dev/legible/example/login\n")
    if with_layout:
        if layout_style == "app":
            body = ("- `APP_PACKAGE_ROOT`: `dev.foodsaver`\n"
                    "- `APP_SOURCE_ROOT`: `app/src/main/java`\n"
                    "- `APP_TEST_SOURCE_ROOT`: `app/src/test/java`\n")
        else:  # seed-style: layout agrees with the reference-impl paths
            body = ("- `APP_PACKAGE_ROOT`: `com.example.app`\n"
                    "- `APP_SOURCE_ROOT`: `reference-impl/java-legible/src/main/java`\n"
                    "- `APP_TEST_SOURCE_ROOT`: `reference-impl/java-legible/src/test/java`\n")
        (feature / "_config" / "package-and-layout.md").write_text(body)
    return tmp, root, feature


class ConfigOverrideTests(unittest.TestCase):
    """Layer 1: key-file overrides layered over root clad.properties."""

    def test_feature_override_wins_over_root_default(self):
        tmp, root, feature = make_repo(with_layout=True)
        try:
            (feature / "_config" / "test.source.root.md").write_text(
                "app/src/test/java/dev/foodsaver\n")
            sys.path.insert(0, str(QG))
            import clad_stages as cs
            cfg = cs._read_config(str(feature))
            self.assertEqual(
                cfg["test.source.root"], "app/src/test/java/dev/foodsaver")
            self.assertEqual(
                cs._prop_path(str(feature), "test.source.root"),
                str(root / "app/src/test/java/dev/foodsaver"))
        finally:
            sys.path.pop(0)
            tmp.cleanup()

    def test_root_default_wins_when_override_file_empty(self):
        tmp, root, feature = make_repo(with_layout=False)
        try:
            (feature / "_config" / "test.source.root.md").write_text(
                "  <!-- not set -->\n")
            sys.path.insert(0, str(QG))
            import clad_stages as cs
            self.assertEqual(
                cs._read_config(str(feature)).get("test.source.root"),
                "reference-impl/java-legible/src/test/java/dev/legible")
        finally:
            sys.path.pop(0)
            tmp.cleanup()

    def test_feature_reference_docs_never_become_keys(self):
        tmp, root, feature = make_repo(with_layout=False)
        try:
            for name in ("README.md", "voice.md", "build-and-test.md",
                         "package-and-layout.md"):
                (feature / "_config" / name).write_text("irrelevant body\n")
            sys.path.insert(0, str(QG))
            import clad_stages as cs
            cfg = cs._read_config(str(feature))
            for leak in ("README", "voice", "build-and-test",
                         "package-and-layout"):
                self.assertNotIn(leak, cfg)
        finally:
            sys.path.pop(0)
            tmp.cleanup()


class ProfilePathsCheckTests(unittest.TestCase):
    """Layer 2: the blocking/warn/skip semantics of verify_profile_paths.py."""

    def test_tbd_layout_fails_once_the_feature_reaches_stage_04(self):
        """A still-TBD layout silently skipped the wrong-tree guard; it must
        fail once the feature has produced Stage-04a output, but stay skippable
        earlier. The skeleton pre-creates every stage output dir with a
        `.gitkeep`, which must NOT count as reaching Stage 04 (it would fire
        the guard at Stage 01 on a fresh feature)."""
        tmp, root, feature = make_repo(with_layout=False)
        try:
            (feature / "_config" / "package-and-layout.md").write_text(
                "- `APP_PACKAGE_ROOT`: `TBD`\n"
                "- `APP_SOURCE_ROOT`: `TBD`\n"
                "- `APP_TEST_SOURCE_ROOT`: `TBD`\n")
            proc = run(SCRIPT, "--feature", feature)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            out = feature / "stages/04_implement/04a_storage-mapping/output"
            out.mkdir(parents=True)
            (out / ".gitkeep").write_text("")
            proc = run(SCRIPT, "--feature", feature)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            (out / "_NOT_APPLICABLE.md").write_text("in-memory profile\n")
            proc = run(SCRIPT, "--feature", feature)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("TBD", proc.stdout)
        finally:
            tmp.cleanup()

    def test_mismatch_blocks_and_names_the_escape_hatch(self):
        tmp, root, feature = make_repo(with_layout=True, layout_style="app")
        try:
            proc = run(SCRIPT, "--feature", feature)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("FAIL", proc.stdout)
            self.assertIn("outside the declared APP_TEST_SOURCE_ROOT", proc.stdout)
            self.assertIn("_config", proc.stdout)
            self.assertIn("test.source.root.md", proc.stdout)
        finally:
            tmp.cleanup()

    def test_feature_override_resolves_the_mismatch(self):
        tmp, root, feature = make_repo(with_layout=True, layout_style="app")
        try:
            (feature / "_config" / "test.source.root.md").write_text(
                "app/src/test/java/dev/foodsaver\n")
            (feature / "_config" / "sync.impl.dir.md").write_text(
                "app/src/main/java/dev/foodsaver\n")
            (feature / "_config" / "concept.impl.dir.md").write_text(
                "app/src/main/java/dev/foodsaver\n")
            proc = run(SCRIPT, "--feature", feature)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("PASS", proc.stdout)
            self.assertNotIn("WARN", proc.stdout)
        finally:
            tmp.cleanup()

    def test_seed_style_agreement_passes_without_warning(self):
        tmp, root, feature = make_repo(with_layout=True, layout_style="seed")
        try:
            proc = run(SCRIPT, "--feature", feature)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("PASS", proc.stdout)
            self.assertNotIn("WARN", proc.stdout)
        finally:
            tmp.cleanup()

    def test_missing_layout_skips_cleanly(self):
        tmp, root, feature = make_repo(with_layout=False)
        try:
            proc = run(SCRIPT, "--feature", feature)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("SKIP", proc.stdout)
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
