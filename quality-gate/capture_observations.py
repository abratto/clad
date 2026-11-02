#!/usr/bin/env python3
"""Turn captured `/api/dev/flow/{id}` data into trace observations.

Two capture modes:

  --flows-dir <dir>   one `<scenario>.json` per captured flow response
  --base-url <url>    fetch the debug surface directly; requires a scenario map
                      (`{"scenario": "flowId"}` or
                       `{"scenario": {"flow": "flowId", "test": "Class.method"}}`)
                      or `--feature` to infer one from the chain tables.

Inference (`--feature`) matches a captured flow to a scenario by HTTP trigger,
then terminal status, then terminal message/payload. When those cannot tell two
scenarios apart — several flows share a trigger/status/message, or the debug
input shape is unknown — inference refuses to guess: it raises
`FlowInferenceError` and the CLI exits non-zero, telling the human to pass an
explicit `--scenario-map`. A silent pick would put a wrong flow id in the trace.

Output is the observations JSON consumed by `generate_trace.py --observations`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request

import artifact_parsers as ap


def _actions(payload):
    if isinstance(payload, list):
        for item in payload:
            actions = _actions(item)
            if actions:
                return actions
        return []
    if isinstance(payload, dict):
        if isinstance(payload.get("actions"), list):
            return payload["actions"]
        if isinstance(payload.get("flow"), dict):
            return _actions(payload["flow"])
    return []


def _runtime_chain(actions):
    chain = []
    for action in actions:
        concept = action.get("concept")
        name = action.get("action")
        if not concept or not name:
            continue
        outcome = ap.normalize_outcome(action.get("outcome") or "")
        if concept == "Web" and name == "request":
            chain.append("Web.request[ROUTED]")
        else:
            chain.append(f"{concept}/{name}[{outcome}]")
    return chain


def observation(payload, test="<TODO: flow test>"):
    actions = _actions(payload)
    return {
        "runtime": _runtime_chain(actions),
        "test": test,
        "verdict": "covered" if actions else "missing",
    }


def observations_from_dir(directory):
    result = {}
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        scenario = name[:-len(".json")]
        with open(os.path.join(directory, name), encoding="utf-8") as handle:
            payload = json.load(handle)
        # A flows dir may also hold a helper list or a previously derived
        # observations.json. Only a flow payload (actions, or an explicitly
        # empty actions list) is a scenario capture.
        actions = _actions(payload)
        if not actions and not (isinstance(payload, dict) and "actions" in payload):
            continue
        test = (payload.get("test", "<TODO: flow test>")
                if isinstance(payload, dict) else "<TODO: flow test>")
        result[scenario] = observation(payload, test)
    return result


def _get_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


class FlowInferenceError(Exception):
    """Raised when a captured flow cannot be told apart from a scenario.

    `ambiguities` is a list of `(flow_id, key, candidate_scenarios)` and
    `unmatched` a list of `(flow_id, key)` that matched no scenario at all.
    """

    def __init__(self, ambiguities, unmatched=()):
        self.ambiguities = list(ambiguities)
        self.unmatched = list(unmatched)
        super().__init__(
            f"{len(self.ambiguities)} ambiguous flow(s) cannot be inferred")


def _request_dicts(action):
    """Every dict that might carry the HTTP method/route for a `Web/request`.

    The debug input shape is not fixed: the request metadata may sit under
    `input`, under `input.request`, or under `fields`; a capture from a
    different profile may even carry a bare string (`"POST /login"`).
    """
    for key in ("input", "fields"):
        data = action.get(key)
        if not isinstance(data, dict):
            continue
        nested = data.get("request")
        if isinstance(nested, dict):
            yield nested
        yield data
    yield action


def _route_key(method, route):
    if not isinstance(route, str):
        return ""
    method = (method or "").upper()
    route = route.split("?", 1)[0].rstrip("/")
    if method and route:
        return f"{method} {route}"
    return ""


def _flow_key(payload):
    for action in _actions(payload):
        if action.get("concept") != "Web" or action.get("action") != "request":
            continue
        for data in _request_dicts(action):
            key = _route_key(
                data.get("method") or data.get("httpMethod"),
                data.get("route") or data.get("path") or data.get("uri")
                or data.get("url"))
            if key:
                return key
        raw = action.get("input")
        if isinstance(raw, str):
            match = re.match(r"\s*([A-Za-z]+)\s+(\S+)", raw)
            if match:
                key = _route_key(match.group(1), match.group(2))
                if key:
                    return key
    return ""


def _scenario_triggers(feature_root):
    chain_dir = os.path.join(feature_root, "stages", "01b_chain-table", "output")
    result = {}
    if not os.path.isdir(chain_dir):
        return result
    pattern = re.compile(r"Web/request\[\s*([A-Za-z]+)\s+([^\]\s]+)\s*\]")
    for name in sorted(os.listdir(chain_dir)):
        if not name.endswith("-chain.md") or name.endswith("-all-scenarios-chain.md"):
            continue
        rows = ap.parse_chain_table(os.path.join(chain_dir, name))
        if not rows:
            continue
        # The request row is normally first, but scan every `when` cell so a
        # chain with a leading setup row still resolves its trigger.
        match = None
        for row in rows:
            match = pattern.search(row.when)
            if match:
                break
        if not match:
            continue
        scenario = name[:-len("-chain.md")]
        result[scenario] = {
            "trigger": f"{match.group(1).upper()} {match.group(2).rstrip('/')}",
            "status": _terminal_status(rows),
            "message": _terminal_message(rows),
        }
    return result


def _terminal_row(rows):
    for row in reversed(rows):
        if row.then_concept == "Web" and row.then_action == "respond":
            return row
    return None


def _terminal_status(rows):
    row = _terminal_row(rows)
    if row and row.then_suffix:
        match = re.search(r"\d+", row.then_suffix)
        if match:
            return match.group(0)
    return ""


def _terminal_message(rows):
    """The authored terminal message, not the whole `Inputs` cell.

    A chain terminal row's `Inputs` cell is often
    `` `401`, `{ message: "Too many attempts…" }` ``; only the message text is
    useful for matching a captured response body.
    """
    row = _terminal_row(rows)
    if not row:
        return ""
    cell = row.inputs
    match = re.search(r'message:\s*"?([^"}]+?)"?\s*\}?\s*$', cell)
    if match:
        return match.group(1).strip().strip('"')
    # Drop a leading status token (`401`, `200`) when there is no message field.
    return re.sub(r"^\s*\d{3}\s*,?\s*", "", cell).strip()


def _flow_terminal(payload):
    """`(status, message, body)` for the last `Web/respond` action, or empties."""
    for action in reversed(_actions(payload)):
        if action.get("concept") == "Web" and action.get("action") == "respond":
            data = action.get("input") or {}
            fields = action.get("fields") or {}
            status = ""
            message = ""
            body = ""
            if isinstance(data, dict):
                status = str(data.get("status") or "")
                message = str(data.get("message") or data.get("body") or "")
                if data.get("body") is not None and not isinstance(
                        data.get("body"), (str, int, float, bool)):
                    body = json.dumps(data.get("body"), sort_keys=True)
            if not status and isinstance(fields, dict):
                status = str(fields.get("status") or "")
            if not message and isinstance(fields, dict):
                message = str(fields.get("message") or fields.get("body") or "")
            if isinstance(data, dict) and data.get("payload") is not None:
                body = body or json.dumps(data.get("payload"), sort_keys=True)
            return status, message, body
    return "", "", ""


def _normalise_payload(text):
    text = str(text).lower()
    text = re.sub(r"[`\"']", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _payload_matches(expected, actual):
    """True when the authored terminal message appears in the captured payload.

    The captured body is often JSON (`{"message": "Too many attempts…"}`) while
    the chain authors the message prose, so compare on normalised tokens rather
    than on whole-string equality.
    """
    expected = _normalise_payload(expected)
    actual = _normalise_payload(actual)
    if not expected or not actual:
        return False
    if expected in actual:
        return True
    tokens = [token for token in expected.split() if len(token) > 2]
    return bool(tokens) and all(token in actual for token in tokens)


def _match_flow(triggers, payload, used):
    """`(candidates, key, narrowed)` for one captured flow.

    `narrowed` is False only when there was nothing to match on (no trigger and
    no terminal status/message), which is "unmatched", not "ambiguous".
    """
    key = _flow_key(payload)
    status, message, body = _flow_terminal(payload)

    if key:
        candidates = [scenario for scenario, info in triggers.items()
                      if info["trigger"] == key and scenario not in used]
        narrowed = True
    else:
        candidates = [scenario for scenario in triggers if scenario not in used]
        narrowed = False

    if len(candidates) > 1 and status:
        by_status = [scenario for scenario in candidates
                     if triggers[scenario]["status"] == status]
        if by_status:
            candidates = by_status
            narrowed = True
    if len(candidates) > 1 and (message or body):
        actual = " ".join(part for part in (message, body) if part)
        by_message = [scenario for scenario in candidates
                      if _payload_matches(triggers[scenario]["message"], actual)]
        if by_message:
            candidates = by_message
            narrowed = True
    if not narrowed:
        return [], key, False
    return candidates, key, True


def infer_scenario_map(feature_root, base_url):
    base = base_url.rstrip("/")
    flows = _get_json(f"{base}/api/dev/flows")
    if not flows:
        # Completed flows leave inFlight before the HTTP response, so the
        # in-flight list is empty after a request. The archive endpoint lists
        # the retained completed flows (newest first).
        flows = _get_json(f"{base}/api/dev/archive")
    triggers = _scenario_triggers(feature_root)
    mapping = {}
    used = set()
    unmatched = []
    ambiguities = []
    for flow in flows:
        flow_id = flow.get("flowId")
        if not flow_id:
            continue
        payload = _get_json(f"{base}/api/dev/flow/{flow_id}")
        candidates, key, narrowed = _match_flow(triggers, payload, used)
        if len(candidates) == 1:
            match = candidates[0]
            used.add(match)
            mapping[match] = {"flow": flow_id, "test": "<TODO: flow test>"}
        elif len(candidates) > 1:
            ambiguities.append((flow_id, key, sorted(candidates)))
        else:
            unmatched.append((flow_id, key))
    if not mapping and len(triggers) == 1 and len(flows) == 1 and not ambiguities:
        scenario = next(iter(triggers))
        mapping[scenario] = {"flow": flows[0]["flowId"],
                             "test": "<TODO: flow test>"}
    for flow_id, key in unmatched:
        print(f"WARN  could not infer a scenario for flow {flow_id} "
              f"({key or 'no trigger input'})", file=sys.stderr)
    if ambiguities:
        raise FlowInferenceError(ambiguities, unmatched)
    return mapping


def observations_from_base_url(base_url, scenario_map):
    result = {}
    base = base_url.rstrip("/")
    for scenario, entry in sorted(scenario_map.items()):
        if isinstance(entry, str):
            flow_id, test = entry, "<TODO: flow test>"
        else:
            flow_id = entry["flow"]
            test = entry.get("test", "<TODO: flow test>")
        payload = _get_json(f"{base}/api/dev/flow/{flow_id}")
        result[scenario] = observation(payload, test)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert captured flow data into trace observations")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--flows-dir")
    source.add_argument("--base-url")
    parser.add_argument("--scenario-map", default="",
                        help="JSON map scenario -> flowId (or inferred with --feature)")
    parser.add_argument("--feature", default="",
                        help="Feature root used to infer scenarios from chain triggers")
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)

    if args.flows_dir:
        observations = observations_from_dir(args.flows_dir)
    else:
        if args.scenario_map:
            with open(args.scenario_map, encoding="utf-8") as handle:
                scenario_map = json.load(handle)
        elif args.feature:
            try:
                scenario_map = infer_scenario_map(
                    os.path.abspath(args.feature), args.base_url)
            except FlowInferenceError as exc:
                print(f"FAIL  could not infer {len(exc.ambiguities)} flow(s) "
                      f"unambiguously:")
                for flow_id, key, candidates in exc.ambiguities:
                    print(f"  flow {flow_id} ({key or 'no trigger input'}) "
                          f"matches: {', '.join(candidates)}")
                print("Pass --scenario-map with an explicit "
                      "scenario -> flowId mapping for the ambiguous flow(s).")
                return 1
            if not scenario_map:
                print("FAIL  could not infer any scenario→flow mapping; "
                      "pass --scenario-map")
                return 1
        else:
            print("FAIL  --base-url requires --scenario-map or --feature")
            return 1
        observations = observations_from_base_url(args.base_url, scenario_map)

    text = json.dumps(observations, indent=2) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"WROTE {args.out}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
