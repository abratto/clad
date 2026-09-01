#!/usr/bin/env python3
"""Property tests: deterministic generators produce artefacts their sibling
verify_* checks accept — generator output must satisfy the gate by construction.

The core assertion types:

  1. `generate_syncs` over a fixture feature reproduces the canonical sync-name
     set (stem equality) and the emitted *.sync.md files pass
     verify_sync_matrix / verify_sync_cycle_graph / verify_sync_overlap.
  2. `generate_spec` excludes the bootstrap Web concept and emits one SPEC per
     business concept.
  3. `generate_sync_cards` emits one card per participating concept and a
     pattern-d-summary.
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
GEN_SYNCS = QG / "generate_syncs.py"
GEN_SPEC = QG / "generate_spec.py"
GEN_CARDS = QG / "generate_sync_cards.py"
VERIFY_MATRIX = QG / "verify_sync_matrix.py"
VERIFY_CYCLE = QG / "verify_sync_cycle_graph.py"
VERIFY_OVERLAP = QG / "verify_sync_overlap.py"


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )


class GeneratorPropertyTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Copy the worked example so generators write into an isolated tree.
        cls.tmp = tempfile.TemporaryDirectory()
        cls.platform = Path(cls.tmp.name)
        # Feature must sit under a `features/` dir for scope derivation.
        cls.features = cls.platform / "features"
        cls.features.mkdir()
        src = REPO_ROOT / "features" / "UC-00-login"
        cls.feature = cls.features / "UC-00-login"
        shutil.copytree(src, cls.feature)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def sync_dir(self):
        return self.feature / "stages" / "03_syncs" / "output"

    def test_generate_syncs_reproduces_canonical_names(self):
        # Wipe and regenerate.
        d = self.sync_dir()
        for f in d.glob("*.sync.md"):
            f.unlink()

        r = run(GEN_SYNCS, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        stems = sorted(f.name.replace(".sync.md", "") for f in d.glob("*.sync.md"))
        # UC-00-login has exactly seven syncs.
        self.assertEqual(len(stems), 7, stems)
        self.assertIn("WhenPasswordAuthCheckOkThenSessionGrantForLogin", stems)
        self.assertIn("WhenWebRequestRoutedThenUserNamingLookupByUsernameForLogin", stems)
        self.assertIn("WhenPasswordAuthCheckLockedThenWebRespondForLogin", stems)
        self.assertIn("WhenUserNamingLookupByUsernameRefusedThenWebRespondForLogin", stems)

    def test_generated_syncs_pass_sync_checks(self):
        d = self.sync_dir()
        for f in d.glob("*.sync.md"):
            f.unlink()
        run(GEN_SYNCS, "--feature", self.feature, "--write")

        for script in (VERIFY_MATRIX, VERIFY_CYCLE, VERIFY_OVERLAP):
            r = run(script, "--sync-dir", d)
            self.assertEqual(
                r.returncode, 0,
                f"{script.name} failed post-generation:\n{r.stdout}{r.stderr}")

    def test_generate_spec_excludes_bootstrap_and_covers_concepts(self):
        spec_dir = self.feature / "stages" / "04_implement" / "04b_spec" / "output"
        for f in spec_dir.glob("*.spec.md"):
            f.unlink()
        r = run(GEN_SPEC, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        specs = sorted(f.name.replace(".spec.md", "") for f in spec_dir.glob("*.spec.md"))
        self.assertEqual(specs, ["PasswordAuth", "Session", "UserNaming"])
        self.assertNotIn("Web", specs)

    def test_generate_cards_cover_participating_concepts(self):
        dep_dir = self.feature / "stages" / "03a_dependency-review" / "output"
        r = run(GEN_CARDS, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cards = sorted(f.name.replace("-card.md", "") for f in dep_dir.glob("*-card.md"))
        # UC-00-login has cards for the 3 business concepts AND the Web bootstrap.
        self.assertEqual(cards, ["PasswordAuth", "Session", "UserNaming", "Web"])
        self.assertTrue((dep_dir / "pattern-d-summary.md").exists())


if __name__ == "__main__":
    unittest.main()
