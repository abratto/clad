#!/usr/bin/env python3
"""Regression coverage for verify_concept_corpus_current.py.

The invariant this guards is about ORDER, not file equality: the canonical
entry names its promotion history, and every use case that has been through
Gate 2 appears on it. A parity check across the copies would be the wrong
invariant — from the second extending use case onward the earlier copy is
*supposed* to differ, because it is a frozen proposal snapshot.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


def run(*args):
    return subprocess.run([sys.executable, *args], cwd=REPO_ROOT,
                          capture_output=True, text=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def spec(history_lines):
    body = "\n".join(history_lines)
    return (f"concept MemberEnrolment [MemberId]\n{body}\n"
            "purpose\n    to enrol a person\n")


CANONICAL_HEADER = ("<!-- canonical — derived from concept MemberEnrolment: "
                    "introduced-by UC-01-a, current source UC-02-b -->\n")


class CorpusCurrentTests(unittest.TestCase):

    def build(self, tmp, *, history, feature_status="approved",
              companion_header=CANONICAL_HEADER, receipt=True, proposer="UC-02-b"):
        features = Path(tmp) / "features"
        write(features / "UC-02-b/stages/01a_responsibility-map/output/"
              "responsibility-map.md",
              "| Concept | Origin | Owned state (one line) | Owned actions | Notes |\n"
              "|---|---|---|---|---|\n"
              f"| `MemberEnrolment` | `extends:UC-01-a` | *(canonical)* | `enrol` | — |\n")
        write(features / "UC-02-b/RESUME.md",
              f"# RESUME\n\n- **Gate 2 (Architecture):** `{feature_status}`\n")

        corpus = features / "_system" / "concepts"
        write(corpus / "MemberEnrolment.concept.md", spec(history))
        for suffix in ("data-model.md", "contract.md"):
            write(corpus / f"MemberEnrolment.{suffix}", companion_header + "# x\n")
        if receipt:
            names = [line.split()[-1] for line in history
                     if line.startswith(("introduced-by", "extended-by"))]
            if "extended-by" in " ".join(history) and proposer not in names:
                names.append(proposer)
            for slug in names:
                write(corpus / f"_promotions/{slug}.md",
                      f"# Promotion receipt — `{slug}`\n\n"
                      "- promoted concepts: `MemberEnrolment`\n")
        return features

    def test_current_corpus_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            features = self.build(tmp, history=["introduced-by UC-01-a",
                                                "extended-by UC-02-b"])
            result = run(str(QG / "verify_concept_corpus_current.py"),
                         "--features-dir", str(features))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_approved_proposal_missing_from_history_fails(self):
        """The corpus is behind — promotion never ran for this feature."""
        with tempfile.TemporaryDirectory() as tmp:
            features = self.build(tmp, history=["introduced-by UC-01-a"])
            result = run(str(QG / "verify_concept_corpus_current.py"),
                         "--features-dir", str(features))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("corpus is behind", result.stdout)

    def test_companion_without_canonical_header_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            features = self.build(
                tmp,
                history=["introduced-by UC-01-a", "extended-by UC-02-b"],
                companion_header="<!-- proposal snapshot — generated -->\n")
            result = run(str(QG / "verify_concept_corpus_current.py"),
                         "--features-dir", str(features))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no 'canonical —", result.stdout)

    def test_companion_naming_a_stale_promoter_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            features = self.build(
                tmp,
                history=["introduced-by UC-01-a", "extended-by UC-02-b"],
                companion_header=("<!-- canonical — derived from concept "
                                  "MemberEnrolment: introduced-by UC-01-a, "
                                  "current source UC-01-a -->\n"))
            result = run(str(QG / "verify_concept_corpus_current.py"),
                         "--features-dir", str(features))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("companions have drifted", result.stdout)

    def test_missing_receipt_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            features = self.build(tmp, history=["introduced-by UC-01-a",
                                                "extended-by UC-02-b"],
                                  receipt=False)
            result = run(str(QG / "verify_concept_corpus_current.py"),
                         "--features-dir", str(features))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no _promotions/UC-02-b.md receipt", result.stdout)

    def test_in_flight_feature_is_skipped(self):
        """A feature before Gate 2 has legitimately not promoted yet."""
        with tempfile.TemporaryDirectory() as tmp:
            features = self.build(
                tmp, history=["introduced-by UC-01-a"], feature_status="pending",
                companion_header=("<!-- canonical — derived from concept "
                                  "MemberEnrolment: introduced-by UC-01-a, "
                                  "current source UC-01-a -->\n"))
            result = run(str(QG / "verify_concept_corpus_current.py"),
                         "--features-dir", str(features))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
