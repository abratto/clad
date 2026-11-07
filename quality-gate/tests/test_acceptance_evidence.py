#!/usr/bin/env python3
"""Regression coverage for acceptance evidence (finding: predicted vs produced).

`verify_acceptance_evidence.py` compares machine-produced runtime evidence to the
frozen Acceptance Spec: token chain, status, response fields, and (persistent) a
persisted read-back.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QG))

CHECK = QG / "verify_acceptance_evidence.py"

SPEC = """# Acceptance spec — demo

## Scenario: do-a-thing

- **Expected response:** `200 OK { id: <X> }`
- **Expected token chain:** `Web.request[ROUTED]` -> `Thing.create[CREATED]` -> `Web.respond[SENT]`
- **Test:** `ThingFlowTest.doAThing`
"""


def world(tmp, evidence=None, persistent=False, legacy_trace=False):
    root = Path(tmp)
    (root / "clad.properties").write_text(
        f"storage.persistent={'true' if persistent else 'false'}\n",
        encoding="utf-8")
    feature = root / "features" / "UC-01-x"
    spec_dir = feature / "stages" / "04_implement" / "04c_acceptance-tests" / "output"
    spec_dir.mkdir(parents=True)
    (spec_dir / "acceptance-spec.md").write_text(SPEC, encoding="utf-8")
    out = feature / "stages" / "05_verify" / "output"
    out.mkdir(parents=True)
    if evidence is not None:
        (out / "acceptance-evidence.json").write_text(
            json.dumps(evidence), encoding="utf-8")
    if legacy_trace:
        (out / "verification-trace.md").write_text("# legacy\n", encoding="utf-8")
    return str(feature)


GOOD = {"do-a-thing": {
    "runtime": ["Web/request[ROUTED]", "Thing/create[CREATED]", "Web/respond[SENT]"],
    "status": 200, "body": {"id": "x"}}}


def run(*args):
    return subprocess.run([sys.executable, str(CHECK), *args],
                          cwd=REPO_ROOT, capture_output=True, text=True)


class AcceptanceEvidenceTests(unittest.TestCase):

    def test_matching_evidence_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--feature-root", world(tmp, GOOD))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)

    def test_wrong_chain_fails(self):
        bad = {"do-a-thing": {**GOOD["do-a-thing"],
                              "runtime": ["Web/request[ROUTED]", "Web/respond[SENT]"]}}
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--feature-root", world(tmp, bad))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("runtime chain does not match", r.stdout)

    def test_wrong_status_fails(self):
        bad = {"do-a-thing": {**GOOD["do-a-thing"], "status": 500}}
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--feature-root", world(tmp, bad))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("status 500", r.stdout)

    def test_missing_body_field_fails(self):
        bad = {"do-a-thing": {**GOOD["do-a-thing"], "body": {}}}
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--feature-root", world(tmp, bad))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("missing field", r.stdout)

    def test_missing_evidence_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--feature-root", world(tmp, None))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("no acceptance evidence", r.stdout)

    def test_legacy_feature_is_grandfathered(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--feature-root", world(tmp, None, legacy_trace=True))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SKIP", r.stdout)

    def test_persistent_requires_readback(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--feature-root", world(tmp, GOOD, persistent=True))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("read-back", r.stdout)

    def test_persistent_with_readback_passes(self):
        good = {"do-a-thing": {**GOOD["do-a-thing"],
                               "readback": {"Thing": {"id": "x"}}}}
        with tempfile.TemporaryDirectory() as tmp:
            r = run("--feature-root", world(tmp, good, persistent=True))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
