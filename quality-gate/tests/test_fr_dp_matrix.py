#!/usr/bin/env python3
"""Regression coverage for the Axiomatic Design deepening (maintenance change
`ad-design-deepening`): the FR×DP matrix builders and the Stage-03 advisory
wiring."""

import os
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import clad_stages as cs  # noqa: E402
import verify_concept_matrix as vcm  # noqa: E402


def write_chain(dirpath, slug, rows):
    chain = dirpath / f"{slug}-chain.md"
    lines = ["# Chain — " + slug, "", "| # | When | Then |", "|---|---|---|"]
    for i, (when, then) in enumerate(rows):
        lines.append(f"| {i+1} | `{when}` | `{then}` |")
    chain.write_text("\n".join(lines) + "\n")


def resp_map(names):
    lines = ["# Responsibility map — test", "", "## Concepts", "",
             "| Concept | reserved words | blocked words |", "|---|---|---|"]
    for n in names:
        lines.append(f"| `{n}` | `x` | `y` |")
    return "\n".join(lines) + "\n"


def usecase(scenarios):
    lines = ["# Use case — test", ""]
    for s in scenarios:
        lines += ["### Scenario: " + s, "", "- does the thing", ""]
    return "\n".join(lines)


class MatrixBuilderTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.chain = self.root / "chain"
        self.chain.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def scenario_run(self, scenarios, per_scenario_rows):
        for slug, rows in per_scenario_rows.items():
            write_chain(self.chain, slug, rows)
        self.paths = dict(
            usecase=usecase(scenarios),
            concepts=resp_map(sorted(
                {c for rows in per_scenario_rows.values()
                 for w, _ in rows for c in [w.split("/")[0]]}
            )),
            chain_dir=self.chain,
        )

    def test_near_diagonal_matrix_flags_nothing(self):
        # Each concept covers a distinct pair in a band — every set unique,
        # nothing at 75%+, no two shapes identical, no pair sharing 2+.
        scenarios = ["S1", "S2", "S3", "S4", "S5"]
        rows = {
            "s1": [("Alpha/action", "Beta/act")],
            "s2": [("Beta/act", "Gamma/act")],
            "s3": [("Gamma/act", "Delta/act")],
            "s4": [("Delta/act", "Epsilon/act")],
            "s5": [("Epsilon/act", "Alpha/act")],
        }
        for slug, r in rows.items():
            write_chain(self.chain, slug, r)
        m, cov = vcm.build_matrix(scenarios,
                                  {"Alpha", "Beta", "Gamma", "Delta", "Epsilon"},
                                  str(self.chain))
        self.assertEqual({"Alpha", "Beta", "Gamma", "Delta", "Epsilon"},
                         {c for c, n in cov.items() if n == 2},
                         "each concept has its own distinct two-scenario band")
        self.assertEqual([], vcm.detect_god_objects(cov, 5))
        self.assertEqual([], vcm.detect_duplication(m, scenarios))
        self.assertEqual([], vcm.detect_entanglement(m, scenarios))

    def test_god_object_and_duplication_detected(self):
        # Alpha appears in every scenario (solid column); Beta and Gamma
        # cover exactly the same scenarios (identical columns).
        # Alpha: solid column — every scenario (a God Object at 75%+).
        rows = {
            "s1": [("Alpha/act", "Beta/act1")],
            "s2": [("Alpha/act", "Gamma/act")],
            "s3": [("Alpha/act", "Beta/act2"), ("Alpha/act", "Gamma/act")],
            "s4": [("Alpha/act", "Delta/act")],
            "s5": [("Alpha/act", "Delta/act")],
        }
        for slug, r in rows.items():
            write_chain(self.chain, slug, r)
        scenarios = ["S1", "S2", "S3", "S4", "S5"]
        concepts = {"Alpha", "Beta", "Gamma", "Delta"}
        m, cov = vcm.build_matrix(scenarios, concepts, str(self.chain))
        self.assertIn("Alpha", cov)
        self.assertEqual(5, cov.get("Alpha", 0), "Alpha is a solid column")
        self.assertEqual({"Alpha"},
                         {c for c, *_ in vcm.detect_god_objects(cov, 5)},
                         "only Alpha crosses the 75% threshold")
        dups = vcm.detect_duplication(m, scenarios)
        self.assertEqual([], dups,
                         "no two concepts share identical coverage")
        ent = vcm.detect_entanglement(m, scenarios)
        # The God Object is maximally entangled: every flagged pair must
        # include Alpha (the non-god concepts share at most one scenario).
        self.assertTrue(ent, "Alpha is entangled with its co-appearing concepts")
        self.assertTrue(all("Alpha" in {c1, c2} for c1, c2, _ in ent))


    def test_duplication_on_identical_coverage(self):
        rows = {
            "s1": [("Alpha/act", "Beta/act")],
            "s2": [("Alpha/act", "Beta/act")],
            "s3": [("Alpha/act", "Beta/act")],
            "s4": [("Alpha/act", "Beta/act")],
        }
        for slug, r in rows.items():
            write_chain(self.chain, slug, r)
        m, _ = vcm.build_matrix(["S1", "S2", "S3", "S4"], {"Alpha", "Beta"},
                                str(self.chain))
        dups = vcm.detect_duplication(m, ["S1", "S2", "S3", "S4"])
        self.assertEqual([("Alpha", "Beta", {"S1", "S2", "S3", "S4"})], dups,
                         "identical columns are redundant DPs (duplication)")
        ent = vcm.detect_entanglement(m, ["S1", "S2", "S3", "S4"])
        self.assertEqual([], ent, "equal sets are duplicates, not entangled")

    def test_god_object_skipped_for_small_features(self):
        cov = {"Alpha": 3}
        self.assertEqual([], vcm.detect_god_objects(cov, 3),
                         "3 scenarios naturally touch most concepts")


class Stage03WiringTests(unittest.TestCase):
    """The advisory check is wired at Stage 03 and the stage contract names
    it (the consistency tests enforce the direction too; these pin the
    intent)."""

    def test_stage03_carries_the_fr_dp_matrix_check(self):
        stage = next(s for s in cs.STAGES if s.id == "03")
        checks = {c.name for c in stage.checks}
        self.assertIn("fr_dp_matrix", checks)

    def test_stage01b_carries_the_fr_dp_matrix_check_too(self):
        # Gate 1 is where God-Object/duplication defects are a one-line map
        # edit; the matrix runs advisively there as well (ad-review-evidence).
        stage = next(s for s in cs.STAGES if s.id == "01b")
        checks = {c.name for c in stage.checks}
        self.assertIn("fr_dp_matrix", checks)

    def test_matrix_check_builds_feature_relative_args(self):
        stage = next(s for s in cs.STAGES if s.id == "03")
        check = next(c for c in stage.checks if c.name == "fr_dp_matrix")
        args = check.build_args("features/UC-00-login")
        self.assertIn("verify_concept_matrix.py", check.script)
        self.assertLess(args.index("--usecase"), args.index("--chain-dir"))
        self.assertIn("01_usecase/output/usecase.md", args[1])
        self.assertTrue(check.script.endswith("verify_concept_matrix.py"))

    def test_script_always_advisory(self):
        script = QUALITY_GATE / "verify_concept_matrix.py"
        self.assertIn("exit(0", script.read_text(),
                      "the FR×DP verdict must never block a stage")

    def test_matrix_check_skips_without_chain_tables(self):
        stage = next(s for s in cs.STAGES if s.id == "03")
        check = next(c for c in stage.checks if c.name == "fr_dp_matrix")
        with tempfile.TemporaryDirectory() as tmp:
            requires = check.requires(tmp)
            self.assertFalse(all(os.path.exists(p) for p in requires),
                             "pristine feature root lacks the inputs")


if __name__ == "__main__":
    unittest.main()
