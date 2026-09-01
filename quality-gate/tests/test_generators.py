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
GEN_DATA = QG / "generate_data_model.py"
GEN_FEATURE = QG / "generate_feature_files.py"
VERIFY_MATRIX = QG / "verify_sync_matrix.py"
VERIFY_CYCLE = QG / "verify_sync_cycle_graph.py"
VERIFY_OVERLAP = QG / "verify_sync_overlap.py"
VERIFY_DATA_MODEL = QG / "verify_data_model.py"
VERIFY_SPEC_PARITY = QG / "verify_spec_parity.py"
VERIFY_OUTCOME_ALIGNMENT = QG / "verify_outcome_alignment.py"
VERIFY_ACTION_CHAIN = QG / "verify_action_chain.py"


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
        # Outcome enums must be SCREAMING_SNAKE_CASE (normalized), not naive .upper().
        pa = (spec_dir / "PasswordAuth.spec.md").read_text(encoding="utf-8")
        self.assertIn("`BAD_PASSWORD`", pa)
        self.assertNotIn("`BADPASSWORD`", pa)

    def test_generate_cards_cover_participating_concepts(self):
        dep_dir = self.feature / "stages" / "03a_dependency-review" / "output"
        r = run(GEN_CARDS, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cards = sorted(f.name.replace("-card.md", "") for f in dep_dir.glob("*-card.md"))
        # UC-00-login has cards for the 3 business concepts AND the Web bootstrap.
        self.assertEqual(cards, ["PasswordAuth", "Session", "UserNaming", "Web"])
        self.assertTrue((dep_dir / "pattern-d-summary.md").exists())

    def test_generate_data_model_passes_csdp_structure_check(self):
        data_dir = self.feature / "stages" / "03b_data-model" / "output"
        for f in data_dir.glob("*.data-model.md"):
            f.unlink()
        r = run(GEN_DATA, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        models = sorted(f.name.replace(".data-model.md", "") for f in data_dir.glob("*.data-model.md"))
        self.assertEqual(models, ["PasswordAuth", "Session", "UserNaming"])
        r = run(VERIFY_DATA_MODEL,
                "--data-dir", data_dir,
                "--concept-dir", self.feature / "stages" / "02_concepts" / "output")
        self.assertEqual(r.returncode, 0,
                         f"generated data models failed CSDP check:\n{r.stdout}{r.stderr}")

    def test_generate_feature_files_derives_scenarios_and_status(self):
        out_dir = self.feature / "stages" / "04_implement" / "04c_flow-tests" / "output"
        for f in out_dir.glob("*.feature"):
            f.unlink()
        r = run(GEN_FEATURE, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        features = list(out_dir.glob("*.feature"))
        self.assertEqual(len(features), 1, features)
        text = features[0].read_text(encoding="utf-8")
        # Four UC-00-login scenarios, each present as a Scenario stub.
        for sc in ("successful-login", "wrong-password", "unknown-user", "lockout"):
            self.assertIn(f"@{sc}", text)
        # Happy path asserts 200; failure paths assert 401.
        self.assertIn("Then the response status is 200", text)
        self.assertIn("Then the response status is 401", text)

    def test_end_to_end_downstream_chain_passes_all_cross_stage_checks(self):
        """Regenerate the full derivable chain (03→03a→03b→04b→04c) from the
        authored upstream (01/01a/02) and run every cross-stage verify_* over
        the result. This is the integration test that catches coherence bugs
        (e.g. outcome normalization drift) that per-file unit tests miss."""
        f = self.feature
        # Regenerate every downstream stage.
        for gen, kwargs in [
            (GEN_SYNCS, {}),
            (GEN_CARDS, {}),
            (GEN_DATA, {}),
            (GEN_SPEC, {}),
            (GEN_FEATURE, {}),
        ]:
            r = run(gen, "--feature", f, "--write")
            self.assertEqual(r.returncode, 0, f"{gen.name}:\n{r.stdout}{r.stderr}")

        checks = [
            (VERIFY_MATRIX, "--sync-dir", f / "stages/03_syncs/output"),
            (VERIFY_CYCLE, "--sync-dir", f / "stages/03_syncs/output"),
            (VERIFY_OVERLAP, "--sync-dir", f / "stages/03_syncs/output"),
            (VERIFY_DATA_MODEL, "--data-dir", f / "stages/03b_data-model/output",
             "--concept-dir", f / "stages/02_concepts/output"),
            (VERIFY_SPEC_PARITY, "--concept-dir", f / "stages/02_concepts/output",
             "--spec-dir", f / "stages/04_implement/04b_spec/output"),
            (VERIFY_OUTCOME_ALIGNMENT, "--chain-dir", f / "stages/01b_chain-table/output",
             "--spec-dir", f / "stages/04_implement/04b_spec/output"),
            (VERIFY_ACTION_CHAIN,
             "--resp-map", f / "stages/01a_responsibility-map/output/responsibility-map.md",
             "--chain-dir", f / "stages/01b_chain-table/output",
             "--concept-dir", f / "stages/02_concepts/output",
             "--sync-dir", f / "stages/03_syncs/output",
             "--dep-dir", f / "stages/03a_dependency-review/output",
             "--spec-dir", f / "stages/04_implement/04b_spec/output"),
        ]
        for script, *args in checks:
            r = run(script, *args)
            self.assertEqual(r.returncode, 0,
                             f"{script.name} failed on regenerated chain:\n{r.stdout}{r.stderr}")


if __name__ == "__main__":
    unittest.main()
