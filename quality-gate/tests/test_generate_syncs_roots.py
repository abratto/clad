#!/usr/bin/env python3
"""Regression: route/method is derived per flow root, not from row 0.

A chain may carry more than one `Web/request[...] -> Web.request` root (e.g. a
POST write flow and a GET read flow sharing one path — UC-12's
`/admin/onboarding`). The generator must derive each rule's route/method from
the root of *its own* flow, and must never emit the roots as syncs (two roots
sharing a path once fabricated a `Web/request -> Web/request` self-sync and
pinned the GET flow `POST`).
"""

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"


class RootRouteMethodTests(unittest.TestCase):

    def setUp(self):
        sys.path.insert(0, str(QG))
        import generate_syncs as gs
        self.gs = gs

    def test_explicit_route_and_method(self):
        route, method = self.gs._root_route_method(
            'Web/request[route: "admin/onboarding" ; method: "GET"]')
        self.assertEqual((route, method), ("admin/onboarding", "GET"))

    def test_shorthand_method_and_path(self):
        # The shorthand form `Web/request[POST /loans]` names a single-segment
        # route; the generator reads the resource segment as the route.
        route, method = self.gs._root_route_method("Web/request[POST /loans]")
        self.assertEqual((route, method), ("loans", "POST"))

    def test_two_roots_yield_independent_matchers(self):
        post = self.gs._root_route_method('Web/request[route: "admin/onboarding" ; method: "POST"]')
        get = self.gs._root_route_method('Web/request[route: "admin/onboarding" ; method: "GET"]')
        self.assertEqual(post[1], "POST")
        self.assertEqual(get[1], "GET")
        self.assertEqual(post[0], get[0])

    def test_outcome_payload_extracts_the_parenthesised_payload(self):
        # The sync binds from the ROW's own trigger completion, not from the
        # producer row it was matched to (the carrier may be a payload-less
        # REFUSED of the same action — experiment defect D25).
        self.assertEqual(self.gs._outcome_payload("Found(userId)"), "userId")
        self.assertEqual(self.gs._outcome_payload("OK(sex, ruleSetId)"), "sex, ruleSetId")
        self.assertEqual(self.gs._outcome_payload("Refused"), "")

    def test_flow_root_payload_binds_as_pattern_a_input(self):
        # A bootstrap that carries a field (`Routed(sessionId)`) binds it from
        # the flow-root INPUT (Pattern A, triggerInput) — `Web.request` emits no
        # completion fields — never as a completion field (Pattern B).
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            features = Path(temporary) / "features"
            chain = (features / "UC-09-read" / "stages/01b_chain-table/output"
                     / "read-chain.md")
            chain.parent.mkdir(parents=True, exist_ok=True)
            chain.write_text(
                "# Chain table\n\n"
                "| # | When | Then | Inputs | Outcome | Why this step |\n"
                "|---|---|---|---|---|---|\n"
                "| 1 | `Web/request[GET /read]` | `Web.request` | `x` | `Routed(sessionId)` | entry |\n"
                "| 2 | `Web.request[Routed(sessionId)]` | `Session.validate` | `sessionId` | `Valid(accountId)` | step |\n"
                "| 3 | `Session.validate[Valid(accountId)]` | `Profiling.readProfile` | `accountId` | `Ok` | step |\n",
                encoding="utf-8")
            syncs, _ = self.gs.derive_syncs_for_feature(str(features / "UC-09-read"))
            bootstrap = [s for s in syncs if s.trigger_concept == "Web"][0]
            self.assertIn(("?sessionId", "A"),
                          [(v, p) for v, p, _ in bootstrap.binds])
            self.assertIn("Flow-root input", bootstrap.binds[0][2])
            # A domain trigger's payload is a COMPLETION field -> Pattern B.
            domain = [s for s in syncs if s.trigger_concept == "Session"][0]
            self.assertIn(("?accountId", "B"),
                          [(v, p) for v, p, _ in domain.binds])
            self.assertIn('triggerField("accountId")', domain.binds[0][2])


if __name__ == "__main__":
    unittest.main()
