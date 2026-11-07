#!/usr/bin/env python3
"""
acceptance_evidence.py — compare machine-produced runtime evidence to the frozen
Acceptance Spec.

Why this exists:
  The Acceptance Spec (Gate 3) states, per scenario, the expected token chain
  and response. The native flow tests assert them in code, and `trace.md` records
  a runtime chain the author assembles. Neither proves that the *running app*
  produced the approved chain, status, and body for each scenario — the trace is
  assembled, not produced. This module reads evidence a test run emitted
  (`acceptance-evidence.json`) and compares it to the spec, so "the test predicts
  this path" is separated from "the app produced this path."

Evidence shape (written by a test-run emitter, assembled by
`capture_observations.py --write-evidence`):

    {
      "<scenario>": {
        "runtime": ["Web.request[ROUTED]", "UserNaming/lookupByUsername[FOUND]", ...],
        "status": 200,
        "body": { "sessionToken": "..." },
        "readback": { ... }        # optional; required for a persistent profile
      }
    }

The contract is language-neutral JSON; any profile (Java, TS, Python) can emit
it. `parse_acceptance_spec` / `compare` are the shared comparison.
"""

from __future__ import annotations

import json
import os
import re

SCENARIO_RE = re.compile(r"^##\s+Scenario:\s*(.+?)\s*$", re.MULTILINE)
CHAIN_RE = re.compile(r"\*\*Expected token chain:\*\*\s*(.+)$", re.MULTILINE)
RESPONSE_RE = re.compile(r"\*\*Expected response:\*\*\s*(.+)$", re.MULTILINE)
TOKEN_RE = re.compile(r"`([^`]+)`")
STATUS_RE = re.compile(r"\b([1-5]\d\d)\b")
FIELD_RE = re.compile(r"([A-Za-z_]\w*)\s*:")


def _norm_token(token: str) -> str:
    """Canonical `Concept/action[OUTCOME]` regardless of `Concept.action` spelling
    and outcome casing (the spec writes `Concept.action[FOUND]`; the engine
    emits `Concept/action[FOUND]`)."""
    token = token.strip()
    m = re.match(r"^([A-Za-z]\w*)\s*[./]\s*([A-Za-z]\w*)\s*\[(.*)\]$", token)
    if not m:
        return token
    concept, action, outcome = m.group(1), m.group(2), m.group(3).strip()
    return f"{concept}/{action}[{outcome.upper()}]"


def _spec_sections(text: str):
    """`{scenario: body}` for each `## Scenario:` section."""
    matches = list(SCENARIO_RE.finditer(text))
    out = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1).strip()] = text[start:end]
    return out


def _body_fields(response_line: str):
    """Field names declared in a response's `{ ... }` body (or bare `k: v`)."""
    brace = re.search(r"\{(.*)\}", response_line)
    scope = brace.group(1) if brace else response_line
    return {name for name in FIELD_RE.findall(scope)}


def parse_acceptance_spec(path: str):
    """`{scenario: {chain, status, body_fields}}` from an Acceptance Spec."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    spec = {}
    for scenario, body in _spec_sections(text).items():
        chain_line = CHAIN_RE.search(body)
        chain = [_norm_token(t) for t in TOKEN_RE.findall(chain_line.group(1))] \
            if chain_line else []
        resp_line = RESPONSE_RE.search(body)
        status = None
        fields = set()
        if resp_line:
            sm = STATUS_RE.search(resp_line.group(1))
            status = int(sm.group(1)) if sm else None
            fields = _body_fields(resp_line.group(1))
        spec[scenario] = {"chain": chain, "status": status,
                          "body_fields": fields}
    return spec


def load_evidence(path: str):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _as_status(value):
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def compare(spec, evidence, persistent=False):
    """Return a list of human-readable problems (empty = evidence matches)."""
    problems = []
    for scenario, want in sorted(spec.items()):
        got = evidence.get(scenario)
        if not got:
            problems.append(f"{scenario}: no runtime evidence recorded")
            continue
        runtime = [_norm_token(t) for t in (got.get("runtime") or [])]
        if want["chain"] and runtime != want["chain"]:
            problems.append(
                f"{scenario}: runtime chain does not match the acceptance spec — "
                f"expected {' -> '.join(want['chain'])}; "
                f"observed {' -> '.join(runtime) or '<none>'}")
        if want["status"] is not None:
            actual = _as_status(got.get("status"))
            if actual != want["status"]:
                problems.append(
                    f"{scenario}: status {actual} does not match the acceptance "
                    f"spec's {want['status']}")
        body = got.get("body")
        body_keys = set(body.keys()) if isinstance(body, dict) else set()
        missing = sorted(want["body_fields"] - body_keys)
        if missing:
            problems.append(
                f"{scenario}: response body is missing field(s) the acceptance "
                f"spec declares: {', '.join(missing)}")
        if persistent and not got.get("readback"):
            problems.append(
                f"{scenario}: a persistent profile must record a persisted "
                f"read-back in its evidence")
    return problems
