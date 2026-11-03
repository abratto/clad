#!/usr/bin/env python3
"""check_runner.py — the shared shell for `verify_*.py` checks.

Every check script resolves its own inputs (that is its job) and then reports
one of three verdicts. This module owns the *shape* of that report so sixty
scripts do not each re-implement it: a PASS/SKIP verdict exits 0, a FAIL exits
1, and a defect names what is wrong, where, and what to do about it.

The three verdicts are not decorative — `advance.py` and `verify_artefacts.py`
distinguish them. `SKIP` means "no input, nothing to verify"; it is not a PASS,
and 0.27.0 taught agents to read it distinctly. Keep the words exactly:

    print(render_skip("no chain tables"))        -> SKIP  no chain tables
    print(render_pass("tokens are consistent"))  -> PASS  tokens are consistent
    print(render_fail(Problem("...", where=...)))

`run_check` wraps the whole lifecycle — parse args, call the body, print the
verdict, exit — so a new check is a `spec`, a `body`, and nothing else. The
body returns a `Verdict`; anything it prints first (detail lines, a table) is
passed through unchanged, so existing output layout survives the migration.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Sequence


# Verdict words. `advance.py`/`verify_artefacts.py` key off these, so they are
# a contract, not a label choice.
PASS = "PASS"
SKIP = "SKIP"
FAIL = "FAIL"
WARN = "WARN"
UNVERIFIED = "UNVERIFIED"


@dataclass
class Problem:
    """One reason a check failed: what is wrong, where, and how to fix it."""

    message: str
    where: Optional[str] = None
    fix: Optional[str] = None
    bullet: bool = False

    def lines(self) -> List[str]:
        head = f"{self.where}: {self.message}" if self.where else self.message
        out = [f"  - {head}" if self.bullet else f"  {head}"]
        if self.fix:
            out.append(f"      {self.fix}")
        return out


@dataclass
class Verdict:
    """The result of a check body.

    `status` is one of the module constants. `problems` are rendered as the
    per-item detail of a FAIL; `detail` is free-form output printed after the
    summary line (a warning, a count, a caveat).
    """

    status: str
    message: str = ""
    problems: List[Problem] = field(default_factory=list)
    detail: Optional[str] = None
    prelude: Optional[str] = None

    @classmethod
    def ok(cls, message: str = "", detail: Optional[str] = None) -> "Verdict":
        return cls(PASS, message, detail=detail)

    @classmethod
    def skip(cls, message: str) -> "Verdict":
        return cls(SKIP, message)

    @classmethod
    def fail(cls, message: str, problems: Sequence[Problem] = ()
             ) -> "Verdict":
        return cls(FAIL, message, list(problems))

    @property
    def exit_code(self) -> int:
        return 0 if self.status in (PASS, SKIP, WARN, UNVERIFIED) else 1


def render_pass(message: str = "") -> str:
    return f"{PASS}  {message}".rstrip()


def render_skip(message: str) -> str:
    return f"{SKIP}  {message}"


def render_fail(problem: Problem, prefix: str = "") -> str:
    """One problem as a FAIL block.

    With a `prefix` (a summary such as "3 collapsed branches"), the problem's
    own line(s) follow it; without one, the problem's first line IS the FAIL
    line, so a single-problem check reads `FAIL  where: message`.
    """
    lines = problem.lines()
    if prefix:
        return "\n".join([f"{FAIL}  {prefix}"] + lines)
    head = f"{FAIL}  {lines[0].strip()}"
    return "\n".join([head] + lines[1:])


def emit(verdict: Verdict) -> int:
    """Print a verdict in the canonical layout and return its exit code."""
    if verdict.prelude:
        print(verdict.prelude)
    if verdict.status in (FAIL, WARN) and (verdict.problems or verdict.message):
        word = verdict.status
        count = len(verdict.problems)
        if verdict.message:
            print(f"{word}  {verdict.message}")
            for problem in verdict.problems:
                for line in problem.lines():
                    print(line)
        elif count == 1:
            print(render_fail(verdict.problems[0]))
        else:
            print(f"{word}  {count} problem(s) found")
            for problem in verdict.problems:
                for line in problem.lines():
                    print(line)
    elif verdict.status == SKIP:
        print(render_skip(verdict.message))
    else:
        print(f"{verdict.status}  {verdict.message}".rstrip())
    if verdict.detail:
        print(verdict.detail)
    return verdict.exit_code


def run_check(spec: str, body: Callable[[argparse.Namespace], Verdict],
              argv: Optional[Sequence[str]] = None,
              configure: Optional[Callable[[argparse.ArgumentParser], None]] = None
              ) -> int:
    """Parse `argv` into a namespace, call `body`, print the verdict, exit.

    `configure(parser)` adds the check's own arguments. Deliberately tiny: the
    check owns its inputs; the runner owns only the report.
    """
    parser = argparse.ArgumentParser(description=spec)
    if configure is not None:
        configure(parser)
    args = parser.parse_args(argv)
    return emit(body(args))


def run_report(spec: str, body: Callable[[argparse.Namespace], int],
               argv: Optional[Sequence[str]] = None,
               configure: Optional[Callable[[argparse.ArgumentParser], None]] = None
               ) -> int:
    """Like `run_check`, but for a body that prints its own report lines.

    Some checks emit interleaved per-item PASS/WARN/FAIL tables that a single
    `Verdict` cannot reproduce verbatim (a per-feature loop, a truncation
    footer). Their body keeps its own `print`s and returns the exit code; this
    wrapper owns only the argparse wiring, which was otherwise copied into
    every such script. Use `run_check` when the verdict fits the model; use
    this when byte-exact table output matters more than structure.
    """
    parser = argparse.ArgumentParser(description=spec)
    if configure is not None:
        configure(parser)
    args = parser.parse_args(argv)
    return int(body(args))


__all__ = [
    "PASS", "SKIP", "FAIL", "WARN", "UNVERIFIED",
    "Problem", "Verdict",
    "render_pass", "render_skip", "render_fail", "emit", "run_check",
    "run_report",
]


if __name__ == "__main__":
    sys.exit(0)
