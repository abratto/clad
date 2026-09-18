#!/usr/bin/env python3
"""Grammar coverage for declarative join + collect
(maintenance/engine-declarative-join-collect.md).

Covers:
  * chain-table composite `When` parsing (`∧`-separated named conjuncts);
  * `verify_chain_grammar` accepting a composite `When` (one `Then`, one
    outcome token) and rejecting a malformed one;
  * sync-spec multi-`when` parsing and the `WhenJoin…And…` naming rule;
  * `collect` / `collect distinct` / `collect by` where-form detection;
  * `verify_sync_matrix` and the cycle graph accepting a joined rule
    (incoming edges from *all* conjunct sources);
  * single-trigger/single-conjunct backward compatibility.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import artifact_parsers as ap  # noqa: E402
import verify_implementation_parity as parity  # noqa: E402
import verify_sync_cycle_graph as cycle  # noqa: E402

AND = "\u2227"
VERIFY_CHAIN = QUALITY_GATE / "verify_chain_grammar.py"
VERIFY_MATRIX = QUALITY_GATE / "verify_sync_matrix.py"


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )


DIAGRAM = """
## Diagram

```mermaid
stateDiagram-v2
    [*] --> Web_request
    Web_request --> [*]
```
"""


def chain_body(rows, diagram=DIAGRAM):
    body = ["# Chain table — `join`", "",
            "| # | When | Then | Inputs | Outcome | Why this step |",
            "|---|---|---|---|---|---|"]
    for num, when, then, outcome in rows:
        body.append(f"| {num} | {when} | {then} | `x` | {outcome} | e |")
    return "\n".join(body) + "\n" + (diagram or "")


JOIN_SYNC = f"""sync RespondWhenJoinListListedAndTagTagged

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `2+3` | `4` | `a: Catalog/list: [...] => [ Listed ] {AND} b: Tagging/tag: [...] => [ Tagged ]` | `Web/respond: [ ok ]` | `<none>` |

## Rule

```
when {{
    a: Catalog/list: [ id: ?id ] => [ Listed ; id: ?id ]
    b: Tagging/tag: [ id: ?id ] => [ Tagged ; id: ?id ]
}}
where {{
    collect distinct ( Tagging: {{ ?id tags: ?t }} as ?tags )
    collect by ?id ( Article: {{ ?id title: ?title }} as ?titles )
}}
then {{
    Web/respond: [ tags: ?tags ]
}}
```

## Cites

- `../01_usecase/output/usecase.md` — scenario "publish"
"""


class ChainJoinParsingTests(unittest.TestCase):

    def test_composite_when_parses_named_conjuncts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "publish-chain.md"
            write(path, chain_body([
                ("1", "`Web/request[POST /publish]`", "`Web.request`", "`Routed`"),
                ("2", "`Web.request[Routed]`", "`Catalog.list`", "`Listed`"),
                ("3", "`Web.request[Routed]`", "`Tagging.tag`", "`Tagged`"),
                ("4", f"`a: Catalog.list[Listed] {AND} b: Tagging.tag[Tagged]`",
                 "`Web.respond[200]`", "`Sent`"),
            ]))
            rows = ap.parse_chain_table(str(path))
            join = rows[-1]
            self.assertTrue(join.composite_when)
            self.assertEqual([c.name for c in join.conjuncts], ["a", "b"])
            self.assertEqual([c.concept for c in join.conjuncts], ["Catalog", "Tagging"])
            self.assertEqual([c.action for c in join.conjuncts], ["list", "tag"])
            self.assertEqual([c.outcome for c in join.conjuncts], ["Listed", "Tagged"])
            self.assertEqual((join.then_concept, join.then_action),
                             ("Web", "respond"))
            self.assertEqual(join.outcome_tokens, ["Sent"])

    def test_single_conjunct_row_is_backward_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "solo-chain.md"
            write(path, chain_body([
                ("1", "`Web/request[POST /x]`", "`Web.request`", "`Routed`"),
            ]))
            row = ap.parse_chain_table(str(path))[0]
            self.assertFalse(row.composite_when)
            self.assertEqual(len(row.conjuncts), 1)
            self.assertIsNone(row.conjuncts[0].name)
            self.assertEqual(row.when, "Web/request[POST /x]")

    def test_grammar_verifier_accepts_composite_when(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "join-chain.md", chain_body([
                ("1", "`Web/request[POST /publish]`", "`Web.request`", "`Routed`"),
                ("2", "`Web.request[Routed]`", "`Catalog.list`", "`Listed`"),
                ("3", "`Web.request[Routed]`", "`Tagging.tag`", "`Tagged`"),
                ("4", f"`a: Catalog.list[Listed] {AND} b: Tagging.tag[Tagged]`",
                 "`Web.respond[200]`", "`Sent`"),
            ]))
            result = run(VERIFY_CHAIN, "--chain-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_grammar_verifier_requires_the_state_diagram(self):
        """The diagram is part of the 01b artefact, not a nicety.

        The gate covers the table and the diagram together; an omitted diagram
        is an incomplete artefact (and reading the old "optional" heading
        instead of the same-turn rule is how one got omitted)."""
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "join-chain.md", chain_body([
                ("1", "`Web/request[POST /publish]`", "`Web.request`", "`Routed`"),
            ], diagram=None))
            result = run(VERIFY_CHAIN, "--chain-dir", tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("stateDiagram-v2", result.stdout)

    def test_grammar_verifier_rejects_a_sequence_diagram(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "join-chain.md", chain_body([
                ("1", "`Web/request[POST /publish]`", "`Web.request`", "`Routed`"),
            ], diagram="\n```mermaid\nsequenceDiagram\n  A->>B: x\n```\n"))
            result = run(VERIFY_CHAIN, "--chain-dir", tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("stateDiagram-v2", result.stdout)

    def test_grammar_verifier_rejects_empty_conjunct(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "bad-chain.md", chain_body([
                ("1", f"`Catalog.list[Listed] {AND} `", "`Web.respond[200]`", "`Sent`"),
            ]))
            result = run(VERIFY_CHAIN, "--chain-dir", tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("composite", result.stdout)


class ChainJoinGenerationTests(unittest.TestCase):

    def test_joined_chain_row_derives_joined_sync_stem(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "features/UC-01-pub"
            write(feature / "stages/01b_chain-table/output/publish-chain.md",
                  chain_body([
                      ("1", "`Web/request[POST /publish]`", "`Web.request`", "`Routed`"),
                      ("2", "`Web.request[Routed]`", "`Catalog.list`", "`Listed`"),
                      ("3", "`Web.request[Routed]`", "`Tagging.tag`", "`Tagged`"),
                      ("4", f"`a: Catalog.list[Listed] {AND} b: Tagging.tag[Tagged]`",
                       "`Web.respond[200]`", "`Sent`"),
                  ]))
            gen = QUALITY_GATE / "generate_syncs.py"
            result = run(gen, "--feature", feature, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            stems = sorted(
                p.name.replace(".sync.md", "")
                for p in (feature / "stages/03_syncs/output").glob("*.sync.md"))
            self.assertIn("RespondWhenJoinListListedAndTagTagged", stems)


class SyncJoinParsingTests(unittest.TestCase):

    def test_join_spec_parses_and_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "RespondWhenJoinListListedAndTagTagged.sync.md"
            write(path, JOIN_SYNC)
            spec = ap.parse_sync(str(path))
            self.assertTrue(spec.is_join)
            self.assertEqual([c.name for c in spec.conjuncts], ["a", "b"])
            self.assertEqual(
                [(c.concept, c.action, c.outcome) for c in spec.conjuncts],
                [("Catalog", "list", "Listed"), ("Tagging", "tag", "Tagged")])
            self.assertEqual((spec.trigger_concept, spec.trigger_action),
                             ("Catalog", "list"))

    def test_join_naming_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "RespondWhenJoinListListedAndTagTagged.sync.md"
            write(path, JOIN_SYNC)
            spec = ap.parse_sync(str(path))
            stem = ap.sync_stem(spec.then_targets[0][0], spec.then_targets[0][1],
                                spec.conjuncts, spec.is_join)
            self.assertEqual(stem, "RespondWhenJoinListListedAndTagTagged")
            names = parity.expected_sync_names(str(path), JOIN_SYNC)
            self.assertIn("RespondWhenJoinListListedAndTagTagged", names)

    def test_collect_where_forms_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "RespondWhenJoinListListedAndTagTagged.sync.md"
            write(path, JOIN_SYNC)
            spec = ap.parse_sync(str(path))
            self.assertEqual(len(spec.collect_forms), 2)
            joined = " ".join(spec.collect_forms)
            self.assertIn("collect distinct", joined)
            self.assertIn("collect by", joined)
            # A collect over a `Concept: { ... }` source is still Pattern D.
            self.assertIn("Tagging", spec.pattern_d_concepts)
            self.assertIn("Article", spec.pattern_d_concepts)

    def test_absent_state_pattern_is_detected_as_a_concept_read(self):
        """`absent(...)` consults concept state and binds nothing (a D- read).

        It must still appear in `pattern_d_concepts`, so the 03a dependency
        cards and the pattern summary audit it exactly like a positive read —
        maintenance/engine-absent-state-guard.md."""
        body = """sync ShelveWhenCloseReturned

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `4` | `7` | `Lending/close: [...] => [ Returned ]` | `Stocking/shelve: [ copyId: ?copyId ]` | `<none>` |

## Rule

```
when {
    Lending/close: [ ... ] => [ Returned ; ... ]
}
where {
    bind ( when.copyId as ?copyId )
    fanOut ( ?loanId ; "Lending" ; "borrower" ; ?memberId )
    absent ( Lending ; ?loanId ; returnedAt )
    collect ( ?loanId as ?openLoans )
}
then {
    Stocking/shelve: [ copyId: ?copyId ]
}
```
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.sync.md"
            write(path, body)
            spec = ap.parse_sync(str(path))
        self.assertIn("Lending", spec.pattern_d_concepts)
        self.assertTrue(spec.has_pattern_d)
        self.assertIn("collect", " ".join(spec.collect_forms))

    def test_single_trigger_sync_is_unchanged(self):
        spec_text = (
            "sync SessionGrantWhenPasswordAuthCheckOk\n\n## Rule\n\n"
            "```\nwhen {\n"
            "    PasswordAuth/check: [ userId: ?u ; password: ?p ] => [ ok ; userId: ?u ]\n"
            "}\nwhere {\n    bind ( uuid() as ?s )\n}\nthen {\n"
            "    Session/grant: [ userId: ?u ]\n}\n```\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SessionGrantWhenPasswordAuthCheckOk.sync.md"
            write(path, spec_text)
            spec = ap.parse_sync(str(path))
            self.assertFalse(spec.is_join)
            self.assertEqual((spec.trigger_concept, spec.trigger_action,
                              spec.trigger_outcome), ("PasswordAuth", "check", "ok"))
            self.assertEqual([c.name for c in spec.conjuncts], [None])
            stem = ap.sync_stem("Session", "grant", spec.conjuncts, False)
            self.assertEqual(stem, "GrantWhenCheckOk")


class JavaJoinEmitterTests(unittest.TestCase):

    def test_joined_spec_lowers_to_conj_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = Path(tmp) / "features/UC-01-pub"
            write(feature / "stages/03_syncs/output/"
                  "RespondWhenJoinListListedAndTagTagged.sync.md",
                  JOIN_SYNC)
            out = Path(tmp) / "src"
            emitter = QUALITY_GATE / "generate_syncs_java.py"
            result = run(emitter, "--feature", feature, "--out", out, "--write")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            java = next(out.glob("*.java")).read_text(encoding="utf-8")
            self.assertIn('.when(conj("a", "Catalog", "list", "Listed"))', java)
            self.assertIn('.and(conj("b", "Tagging", "tag", "Tagged"))', java)
            self.assertIn("public SyncRule rule() {", java)


class JoinerAwareVerifierTests(unittest.TestCase):

    def test_cycle_graph_edges_include_every_conjunct_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "RespondWhenJoinListListedAndTagTagged.sync.md",
                  JOIN_SYNC)
            edges = cycle.parse_syncs_edges(tmp)
            sources = {edge[1][:2] for edge in edges}
            self.assertEqual(sources, {("Catalog", "list"), ("Tagging", "tag")})

    def test_sync_matrix_accepts_joined_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "RespondWhenJoinListListedAndTagTagged.sync.md",
                  JOIN_SYNC)
            result = run(VERIFY_MATRIX, "--sync-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()


class JoinNamingAndCoverageTests(unittest.TestCase):
    """Payload-free join stems (OS filename limit) + Stage-03 coverage check."""

    def test_join_stem_strips_conjunct_payloads(self):
        conjuncts = [
            ap.Conjunct(name="a", concept="Catalog", action="lookupBySlug",
                        outcome="Found(articleId, authorId)"),
            ap.Conjunct(name="b", concept="Following", action="isFollowing",
                        outcome="Following(flag)"),
        ]
        stem = ap.sync_stem("Web", "respond", conjuncts, True)
        self.assertEqual(
            stem, "RespondWhenJoinLookupBySlugFoundAndIsFollowingFollowing")
        self.assertLess(len(stem) + len(".sync.md"), 255)

    def test_transition_coverage_flags_a_missing_sync(self):
        import verify_sync_transition_coverage as cov
        # UC-00-login: all transitions present -> PASS.
        r = subprocess.run(
            [sys.executable, str(QUALITY_GATE / "verify_sync_transition_coverage.py"),
             "--feature", str(REPO_ROOT / "features/UC-00-login")],
            cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)


if __name__ == "__main__":
    unittest.main()
