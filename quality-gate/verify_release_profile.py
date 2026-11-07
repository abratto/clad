#!/usr/bin/env python3
"""
verify_release_profile.py — a repo that declares itself release-grade must
enforce the strongest checks where they apply.

Why this exists (testing-discipline proposal 3):
  CLAD has mutation scoring and, for persistent profiles, a durable-run proof —
  but a local configuration can skip them without a visible qualification
  (`mutation.require=false`). A production repo should be able to *declare*
  release-grade and have that declaration enforced: mutation must actually run,
  and a persistent profile must record durable proof.

Contract:
  `clad.properties` `release.enforce=true` activates the release profile:
    * `mutation.command` must be set, and `mutation.require=true` (a SKIP is a
      failure, not a silent pass);
    * when `storage.persistent=true`, a durable proof must exist
      (`stages/05_verify/output/durable-proof.md`, see verify_durable_proof.py)
      — checked against `--feature-root` when given.
  `release.enforce=false` (the template default) is a deliberate non-release
  declaration: the check SKIPs, so a derived project is not forced to enable it.
  `--require` (CI for a release build) makes `release.enforce=false` itself a
  failure.

Usage:
  python3 verify_release_profile.py [--repo-root .] [--feature-root <UC>] [--require]

Exit: 0 pass/skip, 1 fail.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402


def _find_root(start):
    probe = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(probe, "clad.properties")):
            return probe
        parent = os.path.dirname(probe)
        if parent == probe:
            return os.path.abspath(start)
        probe = parent


def _property(repo_root, key):
    path = os.path.join(repo_root, "clad.properties")
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            if k.strip() == key:
                return v.strip()
    return ""


def _true(value):
    return (value or "").strip().lower() in ("true", "1", "yes", "on")


def _any_durable_proof(repo):
    features = os.path.join(repo, "features")
    if not os.path.isdir(features):
        return False
    for name in os.listdir(features):
        if not name.startswith("UC-"):
            continue
        proof = os.path.join(features, name, "stages", "05_verify", "output",
                             "durable-proof.md")
        if os.path.isfile(proof):
            return True
    return False


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--repo-root", default="",
                            help="Repo root holding clad.properties (default: walk up)")
        parser.add_argument("--feature-root", default="",
                            help="Feature to check for durable proof when persistent")
        parser.add_argument("--require", action="store_true",
                            help="This is a release build: release.enforce must be true")

    def body(args: argparse.Namespace) -> cr.Verdict:
        repo = os.path.abspath(args.repo_root) if args.repo_root else _find_root(os.getcwd())
        enforce = _true(_property(repo, "release.enforce"))
        if not enforce:
            if args.require:
                return cr.Verdict.fail(
                    "release build requires `release.enforce=true`",
                    [cr.Problem(
                        "set `release.enforce=true` in clad.properties for a "
                        "release build, or run without --require for a template",
                        bullet=True)])
            return cr.Verdict.skip(
                "release profile not enabled (template; `release.enforce=false`)")

        failures = []
        if not _property(repo, "mutation.command"):
            failures.append("mutation.command must be set for a release profile")
        if not _true(_property(repo, "mutation.require")):
            failures.append(
                "mutation.require must be true for a release profile (a SKIP "
                "must fail, not pass silently)")
        if _true(_property(repo, "storage.persistent")):
            if args.feature_root:
                proof = os.path.join(
                    os.path.abspath(args.feature_root), "stages", "05_verify",
                    "output", "durable-proof.md")
                if not os.path.isfile(proof):
                    failures.append(
                        f"persistent release profile is missing durable proof: "
                        f"{os.path.relpath(proof, repo)}")
            elif not _any_durable_proof(repo):
                failures.append(
                    "persistent release profile has no durable proof in any "
                    "feature (stages/05_verify/output/durable-proof.md)")
        if failures:
            return cr.Verdict.fail(
                "release profile is not satisfied",
                [cr.Problem(f, bullet=True) for f in failures])
        return cr.Verdict.ok("release profile satisfied (mutation + durable enforced)")

    return cr.run_check(
        "A release-grade repo enforces mutation and durable checks", body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
