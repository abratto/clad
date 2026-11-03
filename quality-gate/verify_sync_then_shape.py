#!/usr/bin/env python3
"""
verify_sync_then_shape.py — a sync `then` carries the authored result, not the
transport frame.

Why this exists:
  Response framing belongs to the primary adapter, which
  `methodology/overlays/PORTS_AND_ADAPTERS.md` charges with "serialize[ing] it
  to the transport's response". A sync that nests a `body: { … }` into its
  `then` is writing the wire frame into coordination — and it is unenforceable:
  the fluent DSL has no nested-map argument source, and
  `verify_sync_implementation_parity` compares only the `then` *target*, so a
  spec that promises a frame its implementation cannot produce goes unnoticed
  (maintenance change `transport-framing-adapter-owned`).

Rule:
  A `then` argument list is flat — `[ httpStatus: 200 ; sessionToken: ?sid ]`. A
  `{ … }` inside a `then` signature is a defect.

Findings: every `Concept/action: [ … { … } … ]` signature line (in the Rule
block or the Sync Contract Matrix) whose argument list contains a brace.

Usage:
  python3 verify_sync_then_shape.py [--features-dir features] [--advisory]

Exit: 0 pass/warn/skip, 1 fail (unless --advisory).
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402

# `Concept/action: [ ... ]` — the argument list stops at the first `]`, so a
# nested `body: { … }` remains inside the captured group.
SIGNATURE = re.compile(r"\b([A-Z]\w*/\w+):\s*\[([^\]]*)\]")
# A quoted literal may carry a brace: a path-parameter route is
# `"claims/{claimId}/decision"`. Only an unquoted brace is a transport frame.
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"')
# Argument names in a `Web/respond` signature (values may contain `;` inside a
# quoted message, but names are the `word:` at the start of an item).
ARG_NAME = re.compile(r'(?:^|;)\s*([A-Za-z_]\w*)\s*:')
STATUS_VALUE = re.compile(r'\bhttpStatus\s*:\s*([^;]+)')
LEGACY_STATUS = re.compile(r'(?:^|;)\s*status\s*:')


def scan(path):
    """Return a list of (line number, signature) for framed `then` signatures."""
    hits = []
    with open(path, encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            for match in SIGNATURE.finditer(line):
                args = QUOTED.sub('""', match.group(2))
                if "{" in args:
                    hits.append((lineno, match.group(1)))
    return hits


def response_findings(path):
    """Return response-grammar findings: unique args + numeric transport status."""
    findings = []
    with open(path, encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            for match in SIGNATURE.finditer(line):
                if match.group(1) != "Web/respond":
                    continue
                args = QUOTED.sub('""', match.group(2))
                names = ARG_NAME.findall(args)
                duplicates = sorted({name for name in names
                                     if names.count(name) > 1})
                if duplicates:
                    findings.append(
                        f"line {lineno}: Web/respond repeats "
                        f"{', '.join(duplicates)} — the transport status and a "
                        f"body field must have distinct names (e.g. "
                        f"`claimStatus`)")
                if LEGACY_STATUS.search(args):
                    findings.append(
                        f"line {lineno}: Web/respond uses `status` for the "
                        f"transport; name it `httpStatus` and keep domain "
                        f"fields distinct (e.g. `claimStatus`)")
                status = STATUS_VALUE.search(args)
                if not status:
                    findings.append(
                        f"line {lineno}: Web/respond has no `httpStatus`")
                elif not re.fullmatch(r"\s*\d{3}\s*", status.group(1)):
                    findings.append(
                        f"line {lineno}: Web/respond `httpStatus` must be a "
                        f"numeric transport code, got `{status.group(1).strip()}`")
    return findings


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--features-dir", default="features")
        parser.add_argument("--advisory", action="store_true",
                            help="Report findings as warnings (exit 0)")

    def body(args: argparse.Namespace) -> cr.Verdict:
        if not os.path.isdir(args.features_dir):
            return cr.Verdict.skip(
                f"no features directory at {args.features_dir}")

        scanned = 0
        findings = []
        for feature in sorted(os.listdir(args.features_dir)):
            if not feature.startswith("UC-"):
                continue
            sync_dir = os.path.join(args.features_dir, feature, "stages",
                                    "03_syncs", "output")
            if not os.path.isdir(sync_dir):
                continue
            for name in sorted(os.listdir(sync_dir)):
                if not name.endswith(".sync.md"):
                    continue
                scanned += 1
                path = os.path.join(sync_dir, name)
                for lineno, signature in scan(path):
                    findings.append(
                        f"{feature}/{name}:{lineno}: `{signature}` nests a "
                        f"`{{ … }}` in its `then` — pass the authored result "
                        f"flat; the primary adapter serializes the response frame")
                for finding in response_findings(path):
                    findings.append(f"{feature}/{name}: {finding}")

        if not scanned:
            return cr.Verdict.skip("no sync specs found")

        if findings:
            summary = (f"{len(findings)} sync `then` defect(s) — carry a "
                       f"transport frame or violate the response grammar:")
            deck = [cr.Problem(finding, bullet=True) for finding in findings]
            if args.advisory:
                verdict = cr.Verdict(cr.WARN, summary)
                verdict.problems = deck
                return verdict
            return cr.Verdict.fail(summary, deck)

        return cr.Verdict.ok(
            f"{scanned} sync spec(s) carry the authored result, not a frame")

    return cr.run_check(
        "A sync then carries the authored result, not the transport frame",
        body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
