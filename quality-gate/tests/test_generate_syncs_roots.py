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


if __name__ == "__main__":
    unittest.main()
