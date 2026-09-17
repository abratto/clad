#!/usr/bin/env python3
"""Coverage for the system-scope concept model (maintenance change
`system-scope-concept-vocabulary`): resolver union/fallback, proposal matrix,
registry consistency, and gated/idempotent promotion."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import clad_stages as cs  # noqa: E402

PROPOSALS = QUALITY_GATE / "verify_concept_proposals.py"
REGISTRY = QUALITY_GATE / "verify_concept_registry.py"
PROMOTE = QUALITY_GATE / "promote_concepts.py"
CATALOG = QUALITY_GATE / "generate_concepts_catalog.py"

CONCEPT = """concept {name} [UserId]
introduced-by {introducer}
purpose
    to {name-lower}

## State

```
{name-lower}At: UserId -> Timestamp   -- mandatory
```

## Actions

```
{name-lower} [ userId: UserId ] => [ ok ]
    flow token: {{ action: "{name}.{name-lower}", userId, outcome: "OK" }}
```

## Operational principle

```
after  {name}/{name-lower}: [ userId: u ] => [ ok ]
```
"""


def concept(name, introducer="UC-01-a"):
    return CONCEPT.format(name=name, **{"name-lower": name.lower(), "introducer": introducer})


def resp_map(rows):
    """rows: list of (concept, origin)."""
    lines = [
        "# Responsibility map — UC-01-a", "",
        "## Concepts", "",
        "| Concept | Origin | Owned state (one line) | Owned actions | Notes |",
        "|---|---|---|---|---|",
    ]
    for c, origin in rows:
        lines.append(f"| `{c}` | {origin} | `f: UserId -> T` | `{c.lower()}` | |")
    lines.append("")
    return "\n".join(lines)


def make_feature(tmp, rows, specs=(), gate2=None, bindings=None):
    feature = Path(tmp) / "features" / "UC-01-a"
    out = feature / "stages" / "01a_responsibility-map" / "output"
    out.mkdir(parents=True, exist_ok=True)
    (out / "responsibility-map.md").write_text(resp_map(rows), encoding="utf-8")

    cdir = feature / "stages" / "02_concepts" / "output"
    cdir.mkdir(parents=True, exist_ok=True)
    for name in specs:
        (cdir / f"{name}.concept.md").write_text(concept(name), encoding="utf-8")
    if bindings is not None:
        (cdir / "concept-bindings.md").write_text(bindings, encoding="utf-8")

    if gate2 is not None:
        (feature / "RESUME.md").write_text(
            f"# RESUME\n\n- **Gate 2 (Architecture):** `{gate2}`\n"
            f"- **Gate 2 content hash:** `{'a' * 64}`\n", encoding="utf-8")
    return feature


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True)


class ResolverTests(unittest.TestCase):

    def test_no_corpus_falls_back_to_feature_output_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = make_feature(tmp, [("Foo", "new")], specs=("Foo",))
            dirs = cs.concept_source_dirs(str(feature))
            self.assertEqual(len(dirs), 1)
            self.assertTrue(dirs[0].endswith("02_concepts/output"))

    def test_corpus_is_appended_and_proposal_shadows(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = make_feature(tmp, [("Foo", "new")], specs=("Foo",))
            corpus = Path(tmp) / "features" / "_system" / "concepts"
            corpus.mkdir(parents=True)
            (corpus / "Foo.concept.md").write_text(concept("Foo"), encoding="utf-8")
            dirs = cs.concept_source_dirs(str(feature))
            self.assertEqual(len(dirs), 2)
            self.assertTrue(dirs[0].endswith("02_concepts/output"))
            self.assertTrue(dirs[1].endswith("_system/concepts"))


class ProposalMatrixTests(unittest.TestCase):

    def test_new_without_proposal_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = make_feature(tmp, [("Foo", "new")], specs=())
            r = run(PROPOSALS, "--feature", str(feature))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("requires a proposal", r.stdout)

    def test_reuse_with_spec_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = make_feature(tmp, [("Foo", "reused:UC-00-login")],
                                   specs=("Foo",))
            r = run(PROPOSALS, "--feature", str(feature))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("must NOT carry a spec file", r.stdout)

    def test_new_with_proposal_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = make_feature(tmp, [("Foo", "new")], specs=("Foo",))
            r = run(PROPOSALS, "--feature", str(feature))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)


class RegistryTests(unittest.TestCase):

    def test_reused_concept_with_local_spec_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = make_feature(tmp, [("Foo", "reused:UC-00-login")],
                                   specs=("Foo",), gate2="approved")
            corpus = Path(tmp) / "features" / "_system" / "concepts"
            corpus.mkdir(parents=True)
            (Path(tmp) / "features" / "_system" / "concepts-catalog.md").write_text(
                "| `Foo` |\n", encoding="utf-8")
            r = run(REGISTRY, "--features-dir", str(Path(tmp) / "features"))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("must not redefine", r.stdout)

    def test_stocked_worked_example_does_not_require_a_corpus(self):
        """A derived project carries UC-00-login for reference but does not
        inherit its vocabulary; the registry must not demand its promotion."""
        with tempfile.TemporaryDirectory() as tmp:
            features = Path(tmp) / "features"
            uc00 = features / "UC-00-login"
            out = uc00 / "stages" / "01a_responsibility-map" / "output"
            out.mkdir(parents=True)
            (out / "responsibility-map.md").write_text(
                resp_map([("Foo", "new")]), encoding="utf-8")
            (uc00 / "RESUME.md").write_text(
                "- **Gate 2 (Architecture):** `approved`\n", encoding="utf-8")
            r = run(REGISTRY, "--features-dir", str(features))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertNotIn("not in the corpus", r.stdout)

    def test_approved_unpromoted_proposal_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = make_feature(tmp, [("Foo", "new")], specs=("Foo",),
                                   gate2="approved")
            r = run(REGISTRY, "--features-dir", str(Path(tmp) / "features"))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("not in the corpus", r.stdout)


class PromotionTests(unittest.TestCase):

    def test_refuses_without_gate2_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = make_feature(tmp, [("Foo", "new")], specs=("Foo",),
                                   gate2="pending")
            r = run(PROMOTE, "--feature", str(feature))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("Gate 2", r.stdout)
            self.assertFalse((Path(tmp) / "features" / "_system" / "concepts"
                              / "Foo.concept.md").exists())

    def test_dependence_claims_ignores_the_table_header(self):
        """The Proposals table header must not be read as a claim row (it made
        promote-concepts report `Concept requires Requires (dependence claim)`)."""
        with tempfile.TemporaryDirectory() as tmp:
            feature = make_feature(tmp, [("Foo", "new")], specs=("Foo",),
                                   gate2="approved")
            rm = (feature / "stages/01a_responsibility-map/output"
                  / "responsibility-map.md")
            rm.write_text(rm.read_text(encoding="utf-8") + (
                "\n## Proposals\n\n"
                "| Concept | Kind | Proposed addition (actions / state) "
                "| Requires (dependence claim) | Rationale |\n"
                "|---|---|---|---|---|\n"
                "| `Foo` | `new` | `run` | — | why |\n"), encoding="utf-8")
            import promote_concepts as pc  # noqa: E402
            self.assertEqual(pc.dependence_claims(str(feature)), [])

    def test_promotes_then_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            feature = make_feature(tmp, [("Foo", "new")], specs=("Foo",),
                                   gate2="approved")
            first = run(PROMOTE, "--feature", str(feature))
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            corpus_spec = Path(tmp) / "features" / "_system" / "concepts" / "Foo.concept.md"
            self.assertTrue(corpus_spec.is_file())
            self.assertIn("introduced-by UC-01-a", corpus_spec.read_text(encoding="utf-8"))
            self.assertTrue((Path(tmp) / "features" / "_system"
                             / "concepts-catalog.md").is_file())

            second = run(PROMOTE, "--feature", str(feature))
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            self.assertIn("no-op", second.stdout)


class CatalogTests(unittest.TestCase):

    def test_catalog_generation_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "concepts"
            corpus.mkdir(parents=True)
            (corpus / "Foo.concept.md").write_text(concept("Foo"), encoding="utf-8")
            args = ["--concepts-dir", str(corpus),
                    "--features-dir", str(Path(tmp) / "features")]
            a = run(CATALOG, *args).stdout
            b = run(CATALOG, *args).stdout
            self.assertEqual(a, b)
            self.assertIn("| `Foo` |", a)


if __name__ == "__main__":
    unittest.main()
