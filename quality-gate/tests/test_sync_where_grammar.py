#!/usr/bin/env python3
"""Unit tests for the structured `where` grammar (sync_where.py).

The grammar is documented in `templates/sync.md`; this locks the parser and the
spec↔Java normalization so implementation parity can compare binding provenance.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "quality-gate"))

import sync_where as sw  # noqa: E402


class SpecGrammarTests(unittest.TestCase):

    def sigs(self, block):
        return sw.clause_signatures(sw.parse_spec_where(block))

    def test_bind_source_factories(self):
        got = self.sigs(
            'bind ( triggerInput("username") as ?u )\n'
            'bind ( triggerField("userId") as ?user )\n'
            'bind ( siblingInput(Web/request, "password") as ?p )\n'
            'bind ( uuid() as ?id )')
        self.assertIn("bind ?u triggerInput(username)", got)
        self.assertIn("bind ?user triggerField(userId)", got)
        self.assertIn("bind ?p siblingInput(Web, request, password)", got)
        self.assertIn("bind ?id uuid()", got)

    def test_pattern_d_read_binds_each_field(self):
        got = self.sigs("Counter: { ?u count: ?count ; total: ?total }")
        self.assertIn("bind ?count stateRead(Counter, ref(?u), count)", got)
        self.assertIn("bind ?total stateRead(Counter, ref(?u), total)", got)

    def test_optional_wraps_inner_clause(self):
        got = self.sigs("OPTIONAL { Comment: { ?post body: ?body } }")
        self.assertEqual(
            got, ["optional (bind ?body stateRead(Comment, ref(?post), body))"])

    def test_absent_and_fanout(self):
        got = self.sigs(
            'fanOut ( ?loanId ; "Lending" ; "borrower" ; ?memberId )\n'
            'absent ( "Lending" ; ?loanId ; "returnedAt" )')
        self.assertIn("fanOut ?loanId Lending borrower ref(?memberId)", got)
        self.assertIn("absent ?loanId Lending returnedAt", got)

    def test_collect_forms(self):
        got = self.sigs(
            "collect ( ?loanId as ?openLoans )\n"
            'collect distinct ( triggerField("tag") as ?tags )\n'
            'collect by ?id ( triggerField("t") as ?titles )')
        self.assertIn("bind ?openLoans collect(ref(?loanId))", got)
        self.assertIn("bind ?tags distinct(triggerField(tag))", got)
        self.assertIn("collectBy ?titles triggerField(t) ?id", got)

    def test_generator_placeholder_is_accepted(self):
        self.assertEqual(self.sigs("bind ( <source> as ?x )"),
                         ["bind ?x <source>"])

    def test_unrecognized_clause_raises(self):
        with self.assertRaises(sw.WhereParseError):
            sw.parse_spec_where("this is not a where clause")


class SpecJavaParityTests(unittest.TestCase):

    def test_spec_and_java_normalize_equal(self):
        spec = (
            'bind ( triggerInput("username") as ?u )\n'
            'bind ( siblingInput(Web/request, "password") as ?p )\n'
            "Counter: { ?u count: ?count }\n"
            'absent ( "Lending" ; ?loanId ; "returnedAt" )\n'
            "collect by ?id ( triggerField(\"t\") as ?titles )")
        java = (
            'bind("?u", triggerInput("username")),'
            'bind("?p", siblingInput(WEB, REQUEST, "password")),'
            'bind("?count", stateRead("Counter", ref("?u"), "count")),'
            'absent("?loanId", "Lending", "returnedAt"),'
            'collectBy("?titles", triggerField("t"), "?id")')
        a = sw.clause_signatures(sw.parse_spec_where(spec))
        b = sw.clause_signatures(
            sw.parse_java_where(java, {"WEB": "Web", "REQUEST": "request"}))
        self.assertEqual(a, b)

    def test_extract_where_block(self):
        text = "when {\n}\nwhere {\n    bind ( uuid() as ?x )\n}\nthen {\n}"
        self.assertIn("bind ( uuid() as ?x )", sw.extract_where_block(text))
        self.assertEqual(sw.extract_where_block("no where here"), "")


if __name__ == "__main__":
    unittest.main()
