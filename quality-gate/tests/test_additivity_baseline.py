#!/usr/bin/env python3
"""Regression coverage for finding 32: additivity must compare a re-entering
feature's proposal to its OWN last committed version, not the moving canonical.

A canonical concept grows as later features extend it. When an *earlier*
feature re-enters (its `_changes/` re-derives Stage 02), its frozen proposal
legitimately lacks the lines later features added — and the old check (canonical
minus proposal) called that a "drop". The fix reads the proposal's prior
committed version at `--base` and compares against that; first authoring still
compares to the canonical (unchanged behaviour).
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QG))

ADDITIVITY = QG / "verify_concept_additivity.py"

RESP_MAP = """# Responsibility map

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `S` | `extends:UC-01-a` | x | `g` | x |
"""

CANONICAL = """concept S [Id]
introduced-by UC-01-a
extended-by UC-03-c
## State

```
base: Id -> T   -- mandatory
addedByLater: Id -> T   -- mandatory
```
"""

# The earlier feature's proposal as it was committed (has `base`, not `addedByLater`).
PRIOR_PROPOSAL = """concept S [Id]
introduced-by UC-01-a
## State

```
base: Id -> T   -- mandatory
```
"""


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def make_repo(tmp, reentry_proposal):
    """A git repo whose `main` holds the earlier feature's prior proposal, then
    the working tree carries `reentry_proposal` (the re-derived version)."""
    root = Path(tmp)
    (root / "features" / "_system" / "concepts").mkdir(parents=True)
    (root / "features" / "_system" / "concepts" / "S.concept.md").write_text(
        CANONICAL, encoding="utf-8")
    feature = root / "features" / "UC-02-b"
    resp = feature / "stages" / "01a_responsibility-map" / "output"
    resp.mkdir(parents=True)
    (resp / "responsibility-map.md").write_text(RESP_MAP, encoding="utf-8")
    out = feature / "stages" / "02_concepts" / "output"
    out.mkdir(parents=True)
    (out / "S.concept.md").write_text(PRIOR_PROPOSAL, encoding="utf-8")

    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    git(root, "checkout", "-q", "-b", "main")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "prior")
    git(root, "tag", "main-base")

    # The re-entry rewrites the proposal in the working tree.
    (out / "S.concept.md").write_text(reentry_proposal, encoding="utf-8")
    return root, feature


class ReentryBaselineTests(unittest.TestCase):

    def test_reentry_lacking_a_later_canonical_line_passes(self):
        """UC-02 re-enters with its own proposal (has `base`, not the line a
        later feature added) — not a drop, because its own prior lacked it too."""
        with tempfile.TemporaryDirectory() as tmp:
            root, feature = make_repo(tmp, PRIOR_PROPOSAL)  # unchanged proposal
            r = subprocess.run(
                [sys.executable, str(ADDITIVITY), "--feature", str(feature),
                 "--base", "main-base"], cwd=root, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)

    def test_reentry_dropping_its_own_prior_line_fails(self):
        """If the re-entry removes `base` (which its own prior carried), that IS
        a drop and must fail even against the baseline."""
        with tempfile.TemporaryDirectory() as tmp:
            dropped = "concept S [Id]\nintroduced-by UC-01-a\n## State\n\n```\n```\n"
            root, feature = make_repo(tmp, dropped)
            r = subprocess.run(
                [sys.executable, str(ADDITIVITY), "--feature", str(feature),
                 "--base", "main-base"], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("base: Id -> T", r.stdout)

    def test_without_a_committed_baseline_falls_back_to_canonical(self):
        """No `--base` (or no committed proposal): first-authoring semantics —
        the canonical is the baseline, so missing canonical lines fail."""
        with tempfile.TemporaryDirectory() as tmp:
            root, feature = make_repo(tmp, PRIOR_PROPOSAL)
            r = subprocess.run(
                [sys.executable, str(ADDITIVITY), "--feature", str(feature),
                 "--base", ""], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("addedByLater", r.stdout)


class ReentryContractBaselineTests(unittest.TestCase):
    """The contract arm has the same ripple: a re-entry's contract must be
    compared to its own prior committed contract, not the canonical (finding 32's
    `listForDay` case)."""

    CANONICAL_CONTRACT = (
        "# S — contract\n\n## Actions\n\n"
        "### `g()` -> Bool\n\n- **Outcomes (enum):** `OK`, `ADDED_LATER`\n")
    PRIOR_CONTRACT = (
        "# S — contract\n\n## Actions\n\n"
        "### `g()` -> Bool\n\n- **Outcomes (enum):** `OK`\n")
    CANONICAL_WITH_ACTION = CANONICAL + (
        "\n## Actions\n\n```\n"
        "g [ ] => [ ok: Bool ]\n"
        "    flow token: { action: \"S.g\", outcome: \"OK\" }\n"
        "h [ ] => [ ok: Bool ]\n"
        "    flow token: { action: \"S.h\", outcome: \"OK\" }\n```\n")

    def _repo(self, tmp, reentry_contract):
        root = Path(tmp)
        corpus = root / "features" / "_system" / "concepts"
        corpus.mkdir(parents=True)
        (corpus / "S.concept.md").write_text(self.CANONICAL_WITH_ACTION,
                                             encoding="utf-8")
        (corpus / "S.contract.md").write_text(self.CANONICAL_CONTRACT,
                                              encoding="utf-8")
        feature = root / "features" / "UC-02-b"
        resp = feature / "stages" / "01a_responsibility-map" / "output"
        resp.mkdir(parents=True)
        (resp / "responsibility-map.md").write_text(RESP_MAP, encoding="utf-8")
        out = feature / "stages" / "02_concepts" / "output"
        out.mkdir(parents=True)
        (out / "S.concept.md").write_text(PRIOR_PROPOSAL, encoding="utf-8")
        cdir = feature / "stages" / "04_implement" / "04b_contract" / "output"
        cdir.mkdir(parents=True)
        (cdir / "S.contract.md").write_text(self.PRIOR_CONTRACT, encoding="utf-8")

        git(root, "init", "-q")
        git(root, "config", "user.email", "t@example.com")
        git(root, "config", "user.name", "t")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "prior")
        git(root, "tag", "main-base")
        (cdir / "S.contract.md").write_text(reentry_contract, encoding="utf-8")
        return root, feature

    def test_reentry_contract_lacking_a_later_action_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, feature = self._repo(tmp, self.PRIOR_CONTRACT)
            r = subprocess.run(
                [sys.executable, str(ADDITIVITY), "--feature", str(feature),
                 "--base", "main-base"], cwd=root, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_reentry_contract_dropping_own_outcome_fails(self):
        own_dropped = (
            "# S — contract\n\n## Actions\n\n"
            "### `g()` -> Bool\n\n- **Outcomes (enum):** `OTHER`\n")
        with tempfile.TemporaryDirectory() as tmp:
            root, feature = self._repo(tmp, own_dropped)
            r = subprocess.run(
                [sys.executable, str(ADDITIVITY), "--feature", str(feature),
                 "--base", "main-base"], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
