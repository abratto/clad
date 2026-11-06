#!/usr/bin/env python3
"""Regression coverage for `promote-concepts --maintenance` (finding 31 / the R20
additive-concept-extension route).

A behavioural change that adds an outcome or field to a shared concept has two
halves with different owners: the canonical concept and the feature flow that
consumes it. The flow-owning feature is necessarily NOT the concept's
*current source* (that is the last extender), so a normal `--feature` promotion
refuses it by design (R22 order rule). The maintenance route lets an approved
maintenance record authorise the additive append instead — without relaxing R22
(a drop/restate is still refused).
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QG))

PROMOTE = QG / "promote_concepts.py"

# Canonical Session: introduced by UC-01, extended by UC-03 (current source).
CANONICAL_VERSION = """concept Session [UserId]
introduced-by UC-01-login
extended-by UC-03-something
purpose
    to maintain a session for a verified user

## State

```
token: UserId -> String   -- mandatory
```

## Actions

```
grant [ userId: UserId ] => [ sessionId: String ]
    flow token: { action: "Session.grant", userId, outcome: "GRANTED" }
```

## Operational principle

```
after  Session/grant: [ userId: u ] => [ sessionId: s ]
```
"""

# UC-02 (a flow owner, NOT the current source) adds an additive `createdAt` fact.
ADDITIVE_PROPOSAL = """<!-- proposal snapshot — canonical spec: features/_system/concepts/Session.concept.md -->

concept Session [UserId]
introduced-by UC-01-login
purpose
    to maintain a session for a verified user

## State

```
token: UserId -> String   -- mandatory
createdAt: UserId -> Timestamp   -- mandatory
```

## Actions

```
grant [ userId: UserId ] => [ sessionId: String ]
    flow token: { action: "Session.grant", userId, outcome: "GRANTED" }
```

## Operational principle

```
after  Session/grant: [ userId: u ] => [ sessionId: s ]
```
"""

# A drop of `token` — non-additive; the maintenance route must refuse it.
DROP_PROPOSAL = ADDITIVE_PROPOSAL.replace(
    "token: UserId -> String   -- mandatory\n", "")

RESP_MAP = """# Responsibility map — UC-02-x

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `Session` | `extends:UC-01-login` | `token` | `grant` | x |
"""


def run(*args, cwd):
    return subprocess.run([sys.executable, str(PROMOTE), *args],
                          cwd=cwd, capture_output=True, text=True)


def make_world(tmp, proposal_text, design_gate="approved", proposals=True):
    """A repo with canonical Session, flow feature UC-02-x, and a maintenance
    record whose `## Concept proposals` names UC-02-x's Session proposal."""
    root = Path(tmp)
    (root / "clad.properties").write_text(
        "concepts.dir=features/_system/concepts\n", encoding="utf-8")
    corpus = root / "features" / "_system" / "concepts"
    corpus.mkdir(parents=True)
    (corpus / "Session.concept.md").write_text(CANONICAL_VERSION, encoding="utf-8")

    feature = root / "features" / "UC-02-x"
    resp_dir = feature / "stages" / "01a_responsibility-map" / "output"
    resp_dir.mkdir(parents=True)
    (resp_dir / "responsibility-map.md").write_text(RESP_MAP, encoding="utf-8")
    cdir = feature / "stages" / "02_concepts" / "output"
    cdir.mkdir(parents=True)
    (cdir / "Session.concept.md").write_text(proposal_text, encoding="utf-8")

    maint = root / "maintenance"
    maint.mkdir()
    proposal_line = ("- `Session: features/UC-02-x/stages/02_concepts/output/"
                     "Session.concept.md`\n" if proposals else "")
    (maint / "add-session-field.md").write_text(
        "# Maintenance change — `add-session-field`\n\n"
        f"- **Design gate:** `{design_gate}`\n"
        "- **Feature-contract impact:** `re-entered`\n\n"
        "## Concept proposals\n\n" + proposal_line + "\n",
        encoding="utf-8")
    return root, corpus


class MaintenancePromotionTests(unittest.TestCase):

    def test_maintenance_promote_appends_and_receipts(self):
        """An additive extension from a non-current-source feature publishes,
        appends it to `extended-by`, and writes a receipt."""
        with tempfile.TemporaryDirectory() as tmp:
            root, corpus = make_world(tmp, ADDITIVE_PROPOSAL)
            result = run("--maintenance", "add-session-field", cwd=str(root))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            canonical = (corpus / "Session.concept.md").read_text()
            self.assertIn("createdAt: UserId -> Timestamp", canonical)
            self.assertIn("UC-02-x", canonical)  # appended to extended-by
            self.assertTrue(
                (corpus / "_promotions" / "UC-02-x.md").is_file(),
                "promotion receipt must be written")

    def test_maintenance_promote_refuses_a_drop(self):
        """A non-additive removal is refused by the same additivity rules."""
        with tempfile.TemporaryDirectory() as tmp:
            root, corpus = make_world(tmp, DROP_PROPOSAL)
            result = run("--maintenance", "add-session-field", cwd=str(root))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dropped", result.stdout.lower())
            # The canonical is unchanged.
            self.assertIn("token: UserId -> String",
                          (corpus / "Session.concept.md").read_text())

    def test_maintenance_promote_requires_approved_design_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _corpus = make_world(tmp, ADDITIVE_PROPOSAL,
                                       design_gate="pending")
            result = run("--maintenance", "add-session-field", cwd=str(root))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("design gate is not approved", result.stdout)

    def test_maintenance_promote_requires_proposals_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _corpus = make_world(tmp, ADDITIVE_PROPOSAL, proposals=False)
            result = run("--maintenance", "add-session-field", cwd=str(root))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no `## Concept proposals`", result.stdout)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, corpus = make_world(tmp, ADDITIVE_PROPOSAL)
            before = (corpus / "Session.concept.md").read_text()
            result = run("--maintenance", "add-session-field", "--dry-run",
                         cwd=str(root))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("WOULD promote", result.stdout)
            self.assertEqual((corpus / "Session.concept.md").read_text(), before)
            self.assertFalse((corpus / "_promotions" / "UC-02-x.md").exists())


if __name__ == "__main__":
    unittest.main()
