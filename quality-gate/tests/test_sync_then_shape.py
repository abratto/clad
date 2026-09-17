#!/usr/bin/env python3
"""Fixture tests for verify_sync_then_shape.py.

A sync `then` carries the authored result; response framing belongs to the
primary adapter (PORTS_AND_ADAPTERS rule 4). A nested `{ … }` in a `then`
signature is a defect.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "quality-gate" / "verify_sync_then_shape.py"

FLAT = """sync RespondWhenEnrolEnrolled

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `2` | `5` | `MemberEnrolment/enrol: [...] => [ Enrolled ]` | `Web/respond: [ status: 201 ; memberId: ?memberId ]` | `201` |

## Rule

```
when {
    MemberEnrolment/enrol: [ ... ] => [ Enrolled ; ... ]
}
then {
    Web/respond: [ status: 201 ; memberId: ?memberId ]
}
```
"""

FRAMED = FLAT.replace(
    "Web/respond: [ status: 201 ; memberId: ?memberId ]",
    "Web/respond: [ status: 201 ; body: { memberId: ?memberId } ]")


class SyncThenShapeTests(unittest.TestCase):

    def _feature(self, tmp, sync_body):
        d = Path(tmp) / "features" / "UC-01-x" / "stages" / "03_syncs" / "output"
        d.mkdir(parents=True)
        (d / "RespondWhenEnrolEnrolled.sync.md").write_text(sync_body,
                                                            encoding="utf-8")
        return Path(tmp) / "features"

    def _run(self, features, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--features-dir", str(features), *extra],
            cwd=REPO_ROOT, capture_output=True, text=True)

    def test_flat_then_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(self._feature(tmp, FLAT))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)

    def test_nested_body_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(self._feature(tmp, FRAMED))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("carry a transport frame", r.stdout)

    def test_nested_body_is_advisory_when_asked(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(self._feature(tmp, FRAMED), "--advisory")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("WARN", r.stdout)

    def test_no_sync_specs_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(Path(tmp) / "features")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SKIP", r.stdout)


if __name__ == "__main__":
    unittest.main()
