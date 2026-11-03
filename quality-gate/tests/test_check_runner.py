#!/usr/bin/env python3
"""Tests for the shared check_runner shell.

The verdict words are a contract with advance.py/verify_artefacts.py: PASS and
SKIP exit 0, FAIL exits 1, and SKIP is never rendered as PASS. These tests pin
that contract so a future "tidy" cannot blur "nothing to check" into "passed".
"""

import contextlib
import io
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QG))

import check_runner as cr  # noqa: E402


def _capture(fn, *args, **kwargs):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = fn(*args, **kwargs)
    return code, buf.getvalue()


class VerdictTests(unittest.TestCase):

    def test_ok_exits_zero_and_prints_pass(self):
        code, out = _capture(cr.emit, cr.Verdict.ok("all good"))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "PASS  all good")

    def test_skip_exits_zero_but_prints_skip_not_pass(self):
        code, out = _capture(cr.emit, cr.Verdict.skip("no input"))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "SKIP  no input")
        self.assertNotIn("PASS", out)


class FailTests(unittest.TestCase):

    def test_fail_exits_one(self):
        code, _out = _capture(cr.emit, cr.Verdict.fail(
            "1 problem", [cr.Problem("broken", where="file.md")]))
        self.assertEqual(code, 1)

    def test_fail_renders_summary_where_and_fix(self):
        verdict = cr.Verdict.fail("1 collapsed branch", [
            cr.Problem("token fans out", where="a-chain.md", fix="split it")])
        code, out = _capture(cr.emit, verdict)
        self.assertEqual(code, 1)
        self.assertIn("FAIL  1 collapsed branch", out)
        self.assertIn("a-chain.md: token fans out", out)
        self.assertIn("split it", out)

    def test_warn_prints_problems_but_exits_zero(self):
        verdict = cr.Verdict(cr.WARN, "2 advisory finding(s):",
                             [cr.Problem("a", bullet=True),
                              cr.Problem("b", bullet=True)])
        code, out = _capture(cr.emit, verdict)
        self.assertEqual(code, 0)
        self.assertIn("WARN  2 advisory finding(s):", out)
        self.assertIn("  - a", out)
        self.assertIn("  - b", out)

    def test_prelude_prints_before_the_summary(self):
        verdict = cr.Verdict.ok("done")
        verdict.prelude = "INFO  line"
        code, out = _capture(cr.emit, verdict)
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), ["INFO  line", "PASS  done"])

    def test_single_problem_without_summary_uses_its_own_line(self):
        verdict = cr.Verdict.fail("", [cr.Problem("missing file", where="x.md")])
        code, out = _capture(cr.emit, verdict)
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("FAIL  x.md: missing file"), out)


class RenderTests(unittest.TestCase):

    def test_render_helpers_match_emit_words(self):
        self.assertEqual(cr.render_pass("x"), "PASS  x")
        self.assertEqual(cr.render_skip("y"), "SKIP  y")

    def test_run_check_parses_args_and_returns_exit_code(self):
        def body(args):
            return cr.Verdict.ok(f"got {args.value}")

        def configure(parser):
            parser.add_argument("--value", required=True)

        code, out = _capture(cr.run_check, "spec", body,
                             ["--value", "abc"], configure)
        self.assertEqual(code, 0)
        self.assertIn("got abc", out)

    def test_run_report_returns_the_body_exit_code_verbatim(self):
        def body(args):
            print(f"table for {args.dir}")
            return 1

        def configure(parser):
            parser.add_argument("--dir", required=True)

        code, out = _capture(cr.run_report, "spec", body,
                             ["--dir", "/tmp/x"], configure)
        self.assertEqual(code, 1)
        self.assertIn("table for /tmp/x", out)


if __name__ == "__main__":
    unittest.main()
