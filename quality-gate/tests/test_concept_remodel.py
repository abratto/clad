#!/usr/bin/env python3
"""Regression coverage for the `remodel` proposal class (maintenance change
`concept-remodel-class`, R22 amendment).

A `remodel:UC-XX` proposal may drop canonical lines only when every dropped
line is listed in the proposal's `## Migration notes` AND every feature on
the concept's canonical history (minus the proposer) has a consent receipt.
An `extends` is never rescued by remodel mechanics.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"

ADDITIVITY = QG / "verify_concept_additivity.py"
PROMOTE = QG / "promote_concepts.py"
PROPOSALS = QG / "verify_concept_proposals.py"

CANONICAL_SESSION = """concept Session [UserId]
introduced-by UC-00-login
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

# Remodel: drops `createdAt`, keeps `token`, adds `expiresAt`.
REMODEL_PROPOSAL = """<!-- proposal snapshot — derived from templates/concept.md; canonical spec: features/_system/concepts/Session.concept.md -->

concept Session [UserId]
introduced-by UC-00-login
purpose
    to maintain a session for a verified user

## State

```
token: UserId -> String   -- mandatory
expiresAt: UserId -> Timestamp   -- mandatory
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

## Migration notes

- drops `createdAt: UserId -> Timestamp   -- mandatory` — creation time is
  superseded by `expiresAt`; no consumer reads `createdAt`.
"""

REMODEL_NO_NOTES = REMODEL_PROPOSAL.split("## Migration notes")[0].rstrip() + "\n"

EXTEND_PROPOSAL = REMODEL_PROPOSAL  # same drop, but authored as an extend

RESP_MAP_REMODEL = """# Responsibility map — UC-02-x

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `Session` | `remodel:UC-00-login` | `token: UserId -> String` | `grant` | x |
"""

RESP_MAP_EXTEND = RESP_MAP_REMODEL.replace("remodel:UC-00-login",
                                           "extends:UC-00-login")


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          cwd=REPO_ROOT, capture_output=True, text=True)


def make_world(tmp, resp_text, proposal_text, with_consent=False,
               gate2="approved"):
    """A corpus holding canonical Session (introduced by UC-00-login) and a
    feature UC-02-x proposing against it."""
    root = Path(tmp)
    corpus = root / "features" / "_system" / "concepts"
    corpus.mkdir(parents=True)
    (corpus / "Session.concept.md").write_text(CANONICAL_SESSION,
                                               encoding="utf-8")
    feature = root / "features" / "UC-02-x"
    out = feature / "stages" / "01a_responsibility-map" / "output"
    out.mkdir(parents=True)
    (out / "responsibility-map.md").write_text(resp_text, encoding="utf-8")
    cdir = feature / "stages" / "02_concepts" / "output"
    cdir.mkdir(parents=True)
    (cdir / "Session.concept.md").write_text(proposal_text, encoding="utf-8")
    if gate2:
        (feature / "RESUME.md").write_text(
            "# RESUME\n\n- **Gate 2 (Architecture):** `%s`\n"
            "- **Gate 2 content hash:** `%s`\n" % (gate2, "b" * 64),
            encoding="utf-8")
    if with_consent:
        consent = corpus / "_remodel-consent"
        consent.mkdir()
        (consent / "Session-UC-00-login.md").write_text(
            "# Consent — Session remodel\n\nUC-00-login consents: createdAt "
            "is unused.\n", encoding="utf-8")
    return str(feature), str(corpus)


class RemodelAdditivityTests(unittest.TestCase):

    def test_remodel_with_notes_and_consent_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, corpus = make_world(tmp, RESP_MAP_REMODEL,
                                         REMODEL_PROPOSAL, with_consent=True)
            result = run(ADDITIVITY, "--feature", feature, "--corpus", corpus)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            self.assertIn("remodel", result.stdout)

    def test_remodel_without_notes_fails_naming_the_dropped_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, corpus = make_world(tmp, RESP_MAP_REMODEL,
                                         REMODEL_NO_NOTES, with_consent=True)
            result = run(ADDITIVITY, "--feature", feature, "--corpus", corpus)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Migration notes", result.stdout)
            self.assertIn("createdAt", result.stdout)

    def test_remodel_without_consent_fails_naming_the_feature(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, corpus = make_world(tmp, RESP_MAP_REMODEL,
                                         REMODEL_PROPOSAL, with_consent=False)
            result = run(ADDITIVITY, "--feature", feature, "--corpus", corpus)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("UC-00-login", result.stdout)
            self.assertIn("consent", result.stdout)

    def test_extends_is_never_rescued_by_remodel_mechanics(self):
        # Same drop, but authored as `extends` — even WITH a migration-notes
        # section and a consent receipt on disk, additivity must fail.
        with tempfile.TemporaryDirectory() as tmp:
            feature, corpus = make_world(tmp, RESP_MAP_EXTEND,
                                         EXTEND_PROPOSAL, with_consent=True)
            result = run(ADDITIVITY, "--feature", feature, "--corpus", corpus)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not additive", result.stdout)


class RemodelPromotionTests(unittest.TestCase):

    def test_promotion_refuses_without_consent(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, corpus = make_world(tmp, RESP_MAP_REMODEL,
                                         REMODEL_PROPOSAL, with_consent=False)
            result = run(PROMOTE, "--feature", feature)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)  # refused ≠ crashed
            self.assertIn("remodel refused", result.stdout)
            self.assertIn("UC-00-login", result.stdout)
            # The corpus is untouched.
            self.assertEqual(
                (Path(corpus) / "Session.concept.md").read_text(),
                CANONICAL_SESSION)

    def test_promotion_with_notes_and_consent_promotes(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature, corpus = make_world(tmp, RESP_MAP_REMODEL,
                                         REMODEL_PROPOSAL, with_consent=True)
            result = run(PROMOTE, "--feature", feature)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            self.assertIn("promoted", result.stdout)
            promoted = (Path(corpus) / "Session.concept.md").read_text()
            self.assertIn("expiresAt", promoted)
            state_block = promoted.split("## State")[1].split("##")[0]
            self.assertNotIn("createdAt", state_block)
            # The migration notes ride along as the permanent audit trail of
            # the non-additive change.
            self.assertIn("## Migration notes", promoted)
            # History is append-only: UC-02-x joins as extender.
            self.assertIn("extended-by UC-02-x", promoted)


class RemodelProposalShapeTests(unittest.TestCase):

    def test_remodel_origin_requires_a_proposal_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            feature = root / "features" / "UC-02-x"
            out = feature / "stages" / "01a_responsibility-map" / "output"
            out.mkdir(parents=True)
            (out / "responsibility-map.md").write_text(RESP_MAP_REMODEL,
                                                       encoding="utf-8")
            (feature / "stages" / "02_concepts" / "output").mkdir(parents=True)
            result = run(PROPOSALS, "--feature", str(feature))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Session", result.stdout)


if __name__ == "__main__":
    unittest.main()
