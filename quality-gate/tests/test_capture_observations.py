#!/usr/bin/env python3
"""Captured flow JSON becomes trace observations."""

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import capture_observations as capture  # noqa: E402


class CaptureObservationTests(unittest.TestCase):

    def test_flow_actions_become_runtime_chain(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "successful-login.json"
            path.write_text(json.dumps({"actions": [
                {"concept": "Web", "action": "request", "outcome": "Routed"},
                {"concept": "UserNaming", "action": "lookupByUsername",
                 "outcome": "Found"},
                {"concept": "Web", "action": "respond", "outcome": "Sent"},
            ]}), encoding="utf-8")
            result = capture.observations_from_dir(temporary)
            self.assertEqual(
                result["successful-login"]["runtime"],
                ["Web.request[ROUTED]", "UserNaming/lookupByUsername[FOUND]",
                 "Web/respond[SENT]"])
            self.assertEqual(result["successful-login"]["verdict"], "covered")

    def test_flows_dir_ignores_non_flow_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "successful-login.json").write_text(json.dumps({"actions": [
                {"concept": "Web", "action": "request", "outcome": "Routed"},
                {"concept": "Web", "action": "respond", "outcome": "Sent"},
            ]}), encoding="utf-8")
            (directory / "observations.json").write_text(json.dumps({
                "successful-login": {"runtime": [], "test": "x", "verdict": "covered"}
            }), encoding="utf-8")
            (directory / "flow-ids.json").write_text(
                json.dumps(["f-1", "f-2"]), encoding="utf-8")
            result = capture.observations_from_dir(temporary)
        self.assertEqual(list(result), ["successful-login"])
        self.assertEqual(result["successful-login"]["verdict"], "covered")

    def test_base_url_fetches_mapped_flows(self):
        from unittest import mock
        payload = {"actions": [
            {"concept": "Web", "action": "request", "outcome": "Routed"},
            {"concept": "Web", "action": "respond", "outcome": "Sent"},
        ]}
        with mock.patch.object(capture, "_get_json", return_value=payload):
            result = capture.observations_from_base_url(
                "http://localhost:8080",
                {"login": {"flow": "f-1", "test": "LoginFlowTest.ok"}})
        self.assertEqual(result["login"]["runtime"],
                         ["Web.request[ROUTED]", "Web/respond[SENT]"])
        self.assertEqual(result["login"]["test"], "LoginFlowTest.ok")

    def test_scenario_inference_uses_terminal_status(self):
        from unittest import mock
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "UC-01"
            chain = feature / "stages/01b_chain-table/output"
            chain.mkdir(parents=True)
            for name, status in (("ok", "200"), ("bad", "401")):
                (chain / f"{name}-chain.md").write_text(
                    "| # | When | Then | Inputs | Outcome | Why |\n"
                    "|---|---|---|---|---|---|\n"
                    "| 1 | `Web/request[POST /x]` | `Web.request` | `x` | `Routed` | e |\n"
                    f"| 2 | `Web.request[Routed]` | `Web.respond[{status}]` | `{status}` | `Sent` | r |\n",
                    encoding="utf-8")
            flows = [{"flowId": "f200"}, {"flowId": "f401"}]
            payloads = {
                "f200": {"actions": [
                    {"concept": "Web", "action": "request", "outcome": "Routed",
                     "input": {"method": "POST", "route": "/x"}},
                    {"concept": "Web", "action": "respond", "outcome": "Sent",
                     "input": {"status": 200}}]},
                "f401": {"actions": [
                    {"concept": "Web", "action": "request", "outcome": "Routed",
                     "input": {"method": "POST", "route": "/x"}},
                    {"concept": "Web", "action": "respond", "outcome": "Sent",
                     "input": {"status": 401}}]},
            }

            def fake_get(url):
                if url.endswith("/flows"):
                    return flows
                return payloads[url.rsplit("/", 1)[-1]]

            with mock.patch.object(capture, "_get_json", side_effect=fake_get):
                result = capture.infer_scenario_map(
                    str(feature), "http://localhost:8080")
        self.assertEqual(result["ok"]["flow"], "f200")
        self.assertEqual(result["bad"]["flow"], "f401")

    def test_scenario_inference_from_chain_trigger(self):
        from unittest import mock
        flows = [{"flowId": "f-login", "actionCount": 2}]
        # A 200 terminal status uniquely identifies `successful-login` among the
        # four UC-00-login scenarios that share `POST /login`.
        payload = {"actions": [
            {"concept": "Web", "action": "request", "outcome": "Routed",
             "input": {"method": "POST", "route": "/login"}},
            {"concept": "Web", "action": "respond", "outcome": "Sent",
             "input": {"status": 200}},
        ]}

        def fake_get(url):
            return flows if url.endswith("/flows") else payload

        with mock.patch.object(capture, "_get_json", side_effect=fake_get):
            result = capture.infer_scenario_map(
                str(REPO_ROOT / "examples/UC-00-login"),
                "http://localhost:8080")
        self.assertEqual(list(result), ["successful-login"])
        self.assertEqual(result["successful-login"]["flow"], "f-login")

    def _feature(self, temporary, scenarios):
        feature = Path(temporary) / "UC-01"
        chain = feature / "stages/01b_chain-table/output"
        chain.mkdir(parents=True)
        for name, status, message in scenarios:
            (chain / f"{name}-chain.md").write_text(
                "| # | When | Then | Inputs | Outcome | Why |\n"
                "|---|---|---|---|---|---|\n"
                "| 1 | `Web/request[POST /x]` | `Web.request` | `x` | `Routed` | e |\n"
                f"| 2 | `Web.request[Routed]` | `Web.respond[{status}]` | "
                f"`{status}`, `{message}` | `Sent` | r |\n",
                encoding="utf-8")
        return feature

    def test_ambiguous_flows_refuse_to_guess(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as temporary:
            # Two scenarios share trigger, status, AND message — mechanically
            # indistinguishable.
            feature = self._feature(temporary, [
                ("unknown-user", "401", "username or password didn't match"),
                ("wrong-password", "401", "username or password didn't match"),
            ])
            flows = [{"flowId": "f-1"}, {"flowId": "f-2"}]
            payload = {"actions": [
                {"concept": "Web", "action": "request", "outcome": "Routed",
                 "input": {"method": "POST", "route": "/x"}},
                {"concept": "Web", "action": "respond", "outcome": "Sent",
                 "input": {"status": 401,
                           "message": "username or password didn't match"}},
            ]}

            def fake_get(url):
                return flows if url.endswith("/flows") else payload

            with mock.patch.object(capture, "_get_json", side_effect=fake_get):
                with self.assertRaises(capture.FlowInferenceError) as ctx:
                    capture.infer_scenario_map(str(feature), "http://localhost")
        self.assertEqual(len(ctx.exception.ambiguities), 2)
        _, _, candidates = ctx.exception.ambiguities[0]
        self.assertEqual(candidates, ["unknown-user", "wrong-password"])

    def test_ambiguous_flows_fail_the_cli_with_scenario_map_advice(self):
        import contextlib
        import io
        from unittest import mock
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, [
                ("unknown-user", "401", "same"),
                ("wrong-password", "401", "same"),
            ])
            flows = [{"flowId": "f-1"}, {"flowId": "f-2"}]
            payload = {"actions": [
                {"concept": "Web", "action": "request", "outcome": "Routed",
                 "input": {"method": "POST", "route": "/x"}},
                {"concept": "Web", "action": "respond", "outcome": "Sent",
                 "input": {"status": 401, "message": "same"}},
            ]}

            def fake_get(url):
                return flows if url.endswith("/flows") else payload

            out = io.StringIO()
            with mock.patch.object(capture, "_get_json", side_effect=fake_get):
                with contextlib.redirect_stdout(out):
                    code = capture.main([
                        "--base-url", "http://localhost",
                        "--feature", str(feature)])
        self.assertEqual(code, 1)
        self.assertIn("--scenario-map", out.getvalue())

    def test_terminal_payload_disambiguates_same_status(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, [
                ("lockout", "401", "Too many attempts. Try again in 15 minutes."),
                ("wrong-password", "401", "username or password didn't match"),
            ])
            flows = [{"flowId": "f-lock"}]
            payload = {"actions": [
                {"concept": "Web", "action": "request", "outcome": "Routed",
                 "input": {"method": "POST", "route": "/x"}},
                {"concept": "Web", "action": "respond", "outcome": "Sent",
                 "input": {"status": 401,
                           "body": {"message": "Too many attempts. Try again in 15 minutes."}}},
            ]}

            def fake_get(url):
                return flows if url.endswith("/flows") else payload

            with mock.patch.object(capture, "_get_json", side_effect=fake_get):
                result = capture.infer_scenario_map(str(feature), "http://localhost")
        self.assertEqual(list(result), ["lockout"])

    def test_debug_input_shape_variants_still_resolve_the_trigger(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, [("only", "200", "ok")])
            flows = [{"flowId": "f-only"}]
            payloads = [
                # nested under input.request
                {"actions": [
                    {"concept": "Web", "action": "request", "outcome": "Routed",
                     "input": {"request": {"method": "POST", "route": "/x"}}},
                    {"concept": "Web", "action": "respond", "outcome": "Sent",
                     "input": {"status": 200}}]},
                # a bare string input
                {"actions": [
                    {"concept": "Web", "action": "request", "outcome": "Routed",
                     "input": "POST /x"},
                    {"concept": "Web", "action": "respond", "outcome": "Sent",
                     "input": {"status": 200}}]},
            ]
            for payload in payloads:
                def fake_get(url, payload=payload):
                    return flows if url.endswith("/flows") else payload

                with mock.patch.object(capture, "_get_json", side_effect=fake_get):
                    result = capture.infer_scenario_map(
                        str(feature), "http://localhost")
                self.assertEqual(list(result), ["only"], payload)

    def test_archive_endpoint_is_used_when_inflight_is_empty(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, [("only", "200", "ok")])
            payload = {"actions": [
                {"concept": "Web", "action": "request", "outcome": "Routed",
                 "input": {"method": "POST", "route": "/x"}},
                {"concept": "Web", "action": "respond", "outcome": "Sent",
                 "input": {"status": 200}}]}

            def fake_get(url):
                if url.endswith("/flows"):
                    return []
                if url.endswith("/archive"):
                    return [{"flowId": "f-archived"}]
                return payload

            with mock.patch.object(capture, "_get_json", side_effect=fake_get):
                result = capture.infer_scenario_map(str(feature), "http://localhost")
        self.assertEqual(list(result), ["only"])
        self.assertEqual(result["only"]["flow"], "f-archived")

    def test_keyless_flow_matched_by_terminal_status(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as temporary:
            feature = self._feature(temporary, [
                ("ok", "200", "ok"), ("bad", "401", "no")])
            flows = [{"flowId": "f-bad"}]
            # No request input at all — only the terminal status identifies it.
            payload = {"actions": [
                {"concept": "Web", "action": "respond", "outcome": "Sent",
                 "input": {"status": 401}}]}

            def fake_get(url):
                return flows if url.endswith("/flows") else payload

            with mock.patch.object(capture, "_get_json", side_effect=fake_get):
                result = capture.infer_scenario_map(str(feature), "http://localhost")
        self.assertEqual(list(result), ["bad"])


if __name__ == "__main__":
    unittest.main()
