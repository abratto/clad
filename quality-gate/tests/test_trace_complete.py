#!/usr/bin/env python3
"""Trace placeholders must not survive Stage 05."""

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import verify_trace_complete as vtc  # noqa: E402


class TraceCompleteTests(unittest.TestCase):

    def _feature(self, root, body):
        feature = root / "UC-01-trace"
        out = feature / "stages/05_verify/output"
        out.mkdir(parents=True)
        (out / "trace.md").write_text(body, encoding="utf-8")
        return feature

    def test_todo_markers_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(Path(temporary),
                                    "Resume point: next\n\n<TODO: runtime evidence>\n")
            self.assertNotEqual(vtc.main(["--feature-root", str(feature)]), 0)

    def test_resolved_trace_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(Path(temporary),
                                    "Resume point: next\n\n"
                                    "Web.request[ROUTED] -> Web.respond[SENT]\n")
            self.assertEqual(vtc.main(["--feature-root", str(feature)]), 0)

    def test_runtime_chain_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(
                Path(temporary),
                "Resume point: next\n\n## s\n\n"
                "- **Expected chain (from 01b):**\n"
                "  1. `Web.request[ROUTED]`\n"
                "  2. `Web.respond[SENT]`\n"
                "- **Runtime trace:** `Web.request[ROUTED]`\n"
                "- **Flow test:** X.y\n"
                "- **Verdict:** covered\n")
            self.assertNotEqual(vtc.main(["--feature-root", str(feature)]), 0)

    def test_subcase_runtime_chain_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(
                Path(temporary),
                "Resume point: next\n\n## s\n\n"
                "- **Expected chain (from 01b):**\n"
                "  1. `Web.request[ROUTED]`\n"
                "  2. `Web.respond[SENT]`\n"
                "- **Runtime trace:** `Web.request[ROUTED]` -> `Web.respond[SENT]`\n"
                "- **Flow test:** X.y\n"
                "- **Verdict:** covered\n\n"
                "### s — sub-case: refusal\n\n"
                "- **Expected chain (from 01b):**\n"
                "  1. `Web.request[ROUTED]`\n"
                "  2. `Claim.validate[REFUSED]`\n"
                "  3. `Web.respond[SENT]`\n"
                "- **Runtime trace:** `Web.request[ROUTED]` -> `Web.respond[SENT]`\n"
                "- **Flow test:** X.refused\n"
                "- **Verdict:** covered\n")
            self.assertNotEqual(vtc.main(["--feature-root", str(feature)]), 0)

    def test_missing_resume_point_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(Path(temporary), "Web.request[ROUTED]\n")
            self.assertNotEqual(vtc.main(["--feature-root", str(feature)]), 0)


if __name__ == "__main__":
    unittest.main()
