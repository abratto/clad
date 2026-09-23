#!/usr/bin/env python3
"""Drift guard: the executable stage model must agree with the contracts.

`clad_stages.py` is the machine projection of the per-UC workflow. The
authored contract for each stage is its `CONTEXT.md` (see AGENTS.md §4a).
This test fails when the two drift apart: a check wired
into `advance.py` that the stage contract never names, a stage with no
contract file, a missing script, or a gate/label mismatch.
"""

import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
SKELETON = REPO_ROOT / "templates" / "feature-skeleton"
sys.path.insert(0, str(QUALITY_GATE))

import clad_stages as cs  # noqa: E402


class StageContractConsistencyTests(unittest.TestCase):

    def context_text(self, stage):
        path = SKELETON / "stages" / stage.context_dir / "CONTEXT.md"
        self.assertTrue(path.is_file(), f"missing stage contract: {path}")
        return path.read_text(encoding="utf-8")

    def test_every_stage_has_a_context_contract(self):
        for stage in cs.STAGES:
            self.context_text(stage)

    def test_canonical_stage00_outputs_resolve_at_system_scope(self):
        """Stage-00 actors/goals are canonical system-scope assets.

        They live at `features/_system/stages/00_actor-goal/output/`, never
        inside a UC folder. When they are misplaced, the `scenario_coverage`
        and `port_spec_contract` checks resolve no input and silently skip —
        UC-00 shipped that way once. Guard the resolver's target, not just the
        presence of a file."""
        feature = REPO_ROOT / "features" / "UC-00-login"
        expected = (REPO_ROOT / "features" / "_system" / "stages"
                    / "00_actor-goal" / "output")
        goals = Path(cs._goals(str(feature)))
        self.assertEqual(goals.parent, expected)
        self.assertTrue((goals.parent / "actors.md").is_file(),
                        f"missing system-scope actors.md under {goals.parent}")
        self.assertTrue(goals.is_file(),
                        f"missing system-scope goals.md: {goals}")
        self.assertEqual(Path(cs._port_spec(str(feature))).parent, expected)

    def test_stage_contracts_advance_through_the_cli_not_by_walking_on(self):
        """A stage contract must never instruct the agent to open the next
        stage's `CONTEXT.md` itself: transitions are gate-driven
        (`./clad advance`, AGENTS.md §2 principles 12-13). The old
        `## Next stage` link-and-proceed phrasing contradicted that rule and
        was the most agent-confusing drift in the repo."""
        roots = [SKELETON, REPO_ROOT / "features" / "UC-00-login"]
        offenders = []
        for root in roots:
            for cf in sorted(root.rglob("stages/**/CONTEXT.md")):
                text = cf.read_text(encoding="utf-8")
                rel = cf.relative_to(REPO_ROOT)
                if "## Advancing" not in text:
                    offenders.append(f"{rel}: missing '## Advancing'")
                for bad in ("## Next stage", "proceeds to Stage",
                            "proceeds without a human gate"):
                    if bad in text:
                        offenders.append(
                            f"{rel}: contains walk-on phrasing '{bad}'")
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_profile_paths_is_wired_at_04a(self):
        """The layout guard runs when a feature enters implementation.

        `verify_profile_paths` advises "fill `_config` at Stage 04a before
        advancing", but it was wired only at 04c/04d, so `advance` passed 04a
        with a TBD layout and every later path check audited the seed's tree
        instead of the app's (UC-03 and UC-04 both shipped a TBD layout past
        04a)."""
        checks = {check.name for check in cs.stage_by_id("04a").checks}
        self.assertIn("profile_paths", checks)

    def test_wired_checks_are_named_in_the_stage_contract(self):
        missing = []
        for stage in cs.STAGES:
            text = self.context_text(stage)
            for check in stage.checks:
                if check.script not in text:
                    missing.append(f"Stage {stage.id}: {check.script} "
                                   f"(check '{check.name}') is wired into "
                                   f"clad_stages.py but not named in "
                                   f"{stage.context_dir}/CONTEXT.md")
        self.assertEqual(missing, [], "\n".join(missing))

    def _automated_commands(self, text):
        """Script names inside the stage contract's Automated-checks code
        blocks (the runnable commands, not the prose that explains them)."""
        match = re.search(r"### Automated checks(.*?)(?=^###|^## |\Z)",
                          text, re.S | re.M)
        if not match:
            return set()
        scripts = set()
        for block in re.findall(r"```(.*?)```", match.group(1), re.S):
            scripts |= set(re.findall(r"verify_\w+\.py", block))
        return scripts

    def _project_level_scripts(self):
        """Checks run project-wide (verify_artefacts.py / the pre-commit hook),
        which any stage contract may legitimately name."""
        scripts = set(re.findall(
            r"verify_\w+\.py", (QUALITY_GATE / "verify_artefacts.py").read_text()))
        hook = REPO_ROOT / ".githooks" / "pre-commit"
        if hook.is_file():
            scripts |= set(re.findall(r"verify_\w+\.py", hook.read_text()))
        scripts.add("verify_stage_sequence.py")
        return scripts

    def test_contracts_do_not_claim_unwired_automated_checks(self):
        """The reverse direction: a contract's Automated-checks command block
        must name only checks this stage runs (or project-level checks).

        This is the drift that let `verify_test_naming.py` and
        `verify_file_manifest.py` sit in stage contracts as "automated" while
        `clad_stages.py` never ran them."""
        project = self._project_level_scripts()
        missing = []
        for stage in cs.STAGES:
            wired = {check.script for check in stage.checks}
            for script in sorted(self._automated_commands(self.context_text(stage))):
                if script not in wired and script not in project:
                    missing.append(
                        f"Stage {stage.id}: contract runs {script} but "
                        f"clad_stages.py does not wire it for this stage")
        self.assertEqual(missing, [], "\n".join(missing))

    def test_every_check_script_exists(self):
        for stage in cs.STAGES:
            for check in stage.checks:
                script = QUALITY_GATE / check.script
                self.assertTrue(script.is_file(),
                                f"Stage {stage.id} wires missing script "
                                f"{check.script}")

    def test_gate_labels_match_resume_template(self):
        resume = (SKELETON / "RESUME.md").read_text(encoding="utf-8")
        for gate, label in cs.GATE_LABELS.items():
            self.assertIn(f"Gate {gate} ({label})", resume,
                          f"Gate {gate} label '{label}' not found in the "
                          f"RESUME.md template")

    def test_gate_stage_blocks_match_gate_after_markers(self):
        """GATE_STAGES[g] is exactly the contiguous block ending at the
        stage whose gate_after == g."""
        for gate, block in cs.GATE_STAGES.items():
            marker = [s.id for s in cs.STAGES if s.gate_after == gate]
            self.assertEqual(len(marker), 1,
                             f"gate {gate} must have exactly one marker stage")
            self.assertEqual(block[-1], marker[0],
                             f"GATE_STAGES[{gate}] must end at {marker[0]}")
            ids = [s.id for s in cs.STAGES]
            start = ids.index(block[0])
            end = ids.index(block[-1])
            self.assertEqual(block, ids[start:end + 1],
                             f"GATE_STAGES[{gate}] is not the contiguous "
                             f"stage block ending at {marker[0]}")

    def test_stage_map_doc_lists_every_stage(self):
        stages_md = (REPO_ROOT / "methodology" / "implementation" /
                     "STAGES.md").read_text(encoding="utf-8")
        for stage in cs.STAGES:
            self.assertIn(f"| {stage.id} |", stages_md,
                          f"STAGES.md stage table is missing '{stage.id}'")

    def test_stage_verify_relative_paths_have_correct_depth(self):
        """`../../..` breadcrumbs in the Verify commands must resolve from the
        stage directory to the repo root (and `--feature` to the feature root).
        A wrong depth makes the contract's commands unrunnable verbatim."""
        import re
        offenders = []
        for cf in SKELETON.rglob("stages/**/CONTEXT.md"):
            rel = cf.parent.relative_to(SKELETON)
            feature_depth = len(rel.parts)        # ups to the feature root
            repo_depth = feature_depth + 2        # + templates/feature-skeleton
            for lineno, line in enumerate(
                    cf.read_text(encoding="utf-8").splitlines(), 1):
                for m in re.finditer(
                        r"((?:\.\./)+)(quality-gate|methodology|templates|"
                        r"reference-impl|features|clad\.properties)", line):
                    if m.group(1).count("../") != repo_depth:
                        offenders.append(
                            f"{cf.relative_to(SKELETON)}:{lineno}: "
                            f"expected {repo_depth} ups, found "
                            f"{m.group(1).count('../')}")
                m = re.search(r"--feature\s+((?:\.\./?)+)", line)
                if m:
                    ups = m.group(1).count("..")
                    if ups != feature_depth:
                        offenders.append(
                            f"{cf.relative_to(SKELETON)}:{lineno}: --feature "
                            f"expected {feature_depth} ups, found {ups}")
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_present_gate_does_not_hardcode_a_divergent_label(self):
        """present_gate.py must derive gate labels from clad_stages, not
        restate them (the source of the old 'Executable specification'
        vs 'Executable spec' drift)."""
        present = (QUALITY_GATE / "present_gate.py").read_text(encoding="utf-8")
        self.assertIn("cs.GATE_LABELS", present,
                      "present_gate.py must import gate labels from clad_stages")
        self.assertNotIn("Executable specification", present,
                         "present_gate.py must not hardcode a gate label")


if __name__ == "__main__":
    unittest.main()
