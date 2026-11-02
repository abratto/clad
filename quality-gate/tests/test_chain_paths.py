#!/usr/bin/env python3
"""A branched chain table yields one path per terminal branch."""

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import artifact_parsers as ap  # noqa: E402
import chain_paths  # noqa: E402

CHAIN = """| # | When | Then | Inputs | Outcome | Why |
|---|---|---|---|---|---|
| 1 | `Web/request[POST /x]` | `Web.request` | `x` | `ROUTED` | entry |
| 2 | `Web.request[ROUTED]` | `Claim.validate` | `x` | `OK` | valid |
| 3 | `Web.request[ROUTED]` | `Claim.validate` | `x` | `REFUSED` | invalid |
| 4 | `Claim.validate[OK]` | `Claim.submit` | `x` | `ACCEPTED` | write |
| 5 | `Claim.submit[ACCEPTED]` | `Web.respond[201]` | `201` | `SENT` | success |
| 6 | `Claim.validate[REFUSED]` | `Web.respond[400]` | `400` | `SENT` | refusal |
"""


class ChainPathTests(unittest.TestCase):

    def test_branches_are_enumerated_per_terminal(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "branch-chain.md"
            path.write_text(CHAIN, encoding="utf-8")
            rows = ap.parse_chain_table(str(path))
        paths = chain_paths.enumerate_paths(rows)
        self.assertEqual(len(paths), 2)
        success = chain_paths.success_path(paths)
        self.assertEqual(success.status, "201")
        self.assertEqual(
            success.tokens,
            ["Web.request[ROUTED]", "Claim/validate[OK]",
             "Claim/submit[ACCEPTED]", "Web.respond[SENT]"])
        refusal = next(p for p in paths if p.status == "400")
        self.assertEqual(
            refusal.tokens,
            ["Web.request[ROUTED]", "Claim/validate[REFUSED]",
             "Web.respond[SENT]"])
        self.assertTrue(success.is_success)
        self.assertFalse(refusal.is_success)


if __name__ == "__main__":
    unittest.main()
