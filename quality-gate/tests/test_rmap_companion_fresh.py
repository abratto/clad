#!/usr/bin/env python3
"""Regression coverage for verify_rmap_companion_fresh.py (finding 29).

Aggregate Rmap treats the canonical corpus as authoritative, so a feature that
re-derives its Stage-03b model but has not refreshed the canonical data-model
companion gets a migration generated from the STALE companion — silently wrong.
The check fails and tells the author to run `promote-concepts --companions-only`.
Only a concept's current source is checked (an earlier frozen feature's model
legitimately differs — finding 32).
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QG))

SCRIPT = QG / "verify_rmap_companion_fresh.py"

MODEL_WITH_TITLE = """# Reserving — data model

## Conceptual model

```
object-type Reservation identified-by ReservationId
fact room : ReservationId -> RoomId -- mandatory
fact title : ReservationId -> Text -- mandatory
```
"""

MODEL_WITHOUT_TITLE = """# Reserving — data model

## Conceptual model

```
object-type Reservation identified-by ReservationId
fact room : ReservationId -> RoomId -- mandatory
```
"""

CONCEPT = """concept Reserving [ReservationId]
introduced-by UC-01-a
extended-by UC-03-c
purpose
    p
"""


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args],
                          cwd=REPO_ROOT, capture_output=True, text=True)


def world(tmp, *, feature_model, companion_model, current_source="UC-03-c",
          feature_slug="UC-03-c"):
    root = Path(tmp)
    corpus = root / "features" / "_system" / "concepts"
    corpus.mkdir(parents=True)
    (corpus / "Reserving.concept.md").write_text(CONCEPT, encoding="utf-8")
    (corpus / "Reserving.data-model.md").write_text(companion_model,
                                                    encoding="utf-8")
    feature = root / "features" / feature_slug
    d = feature / "stages" / "03b-data-model" / "output"
    d.mkdir(parents=True)
    (d / "Reserving.data-model.md").write_text(feature_model, encoding="utf-8")
    return str(feature)


class CompanionFreshTests(unittest.TestCase):

    def test_stale_companion_fails(self):
        """Current source derived `title` but the companion lacks it → FAIL."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = world(tmp, feature_model=MODEL_WITH_TITLE,
                            companion_model=MODEL_WITHOUT_TITLE)
            r = run("--feature", feature)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("promote-concepts", r.stdout)
            self.assertIn("stale", r.stdout)

    def test_fresh_companion_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = world(tmp, feature_model=MODEL_WITH_TITLE,
                            companion_model=MODEL_WITH_TITLE)
            r = run("--feature", feature)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)

    def test_earlier_feature_is_skipped(self):
        """A feature that is NOT the current source is not flagged (its frozen
        model legitimately predates later additions — finding 32)."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = world(tmp, feature_model=MODEL_WITHOUT_TITLE,
                            companion_model=MODEL_WITH_TITLE,
                            feature_slug="UC-02-b")
            r = run("--feature", feature)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)

    def test_no_corpus_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "features" / "UC-03-c"
            (feature / "stages" / "03b-data-model" / "output").mkdir(parents=True)
            r = run("--feature", str(feature))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SKIP", r.stdout)


if __name__ == "__main__":
    unittest.main()
