#!/usr/bin/env python3
"""Regression coverage for the sync-gate soundness fixes.

Five false greens the experiment reproduced:
  1. Stage 03 accepts a malformed `when`/`then` rule body (matrix intact).
  2. Transition coverage accepts an unrelated `.sync.md` because counts match.
  3. Strict implementation parity compares only the primary trigger + first
     target.
  4. Sync-matrix row IDs are not cross-referenced against the chain table.
  5. Route-filter behavior vs its index label, and impl route parity.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QG))

MATRIX = QG / "verify_sync_matrix.py"
TRANSITION = QG / "verify_sync_transition_coverage.py"
PARITY = QG / "verify_sync_implementation_parity.py"

import generate_syncs as gs  # noqa: E402


CHAIN = """# Chain table — `do-a-thing`

| # | When | Then | Inputs | Outcome | Why this step |
|---|---|---|---|---|---|
| 1 | `Web/request[POST /things]` | `Web.request` | `POST /things` | `Routed` | entry |
| 2 | `Web.request[Routed]` | `Thing.create` | `name` | `Created` | write |
| 3 | `Thing.create[Created]` | `Web.respond[201]` | `201`, `{ id }` | `Sent` | respond |
"""


def sync_doc(*, source="1", target="2",
             when_sig='Web/request: [ route: "things" ] => [ Routed ]',
             then_sig="Thing/create: [ name: ?n ]",
             when_body='requested: Web/request: [ route: "things" ; method: "POST" ] => [ Routed ; ... ]',
             then_body="Thing/create: [ name: ?n ]"):
    return (
        "sync CreateForThingsWhenRequestRouted\n\n"
        "## Sync Contract Matrix\n\n"
        "| Source row | Target row | `when` signature | `then` signature | Allowed literals |\n"
        "|---|---|---|---|---|\n"
        f"| `{source}` | `{target}` | `{when_sig}` | `{then_sig}` | `<none>` |\n\n"
        "## Rule\n\n"
        "```\n"
        "when {\n"
        f"    {when_body}\n"
        "}\n"
        "then {\n"
        f"    {then_body}\n"
        "}\n"
        "```\n\n"
        "## Cites\n\n"
        "- `../01_usecase/output/usecase.md` — scenario \"Do a thing\"\n")


def run(script, *args, cwd=REPO_ROOT):
    return subprocess.run([sys.executable, str(script), *args],
                          cwd=cwd, capture_output=True, text=True)


def make_sync_dir(tmp, doc):
    d = Path(tmp) / "03_syncs" / "output"
    d.mkdir(parents=True)
    (d / "CreateForThingsWhenRequestRouted.sync.md").write_text(doc,
                                                                encoding="utf-8")
    return d


def make_chain_dir(tmp):
    d = Path(tmp) / "01b_chain-table" / "output"
    d.mkdir(parents=True)
    (d / "do-a-thing-chain.md").write_text(CHAIN, encoding="utf-8")
    return d


class SyncMatrixSoundnessTests(unittest.TestCase):

    def test_valid_matrix_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            sd = make_sync_dir(tmp, sync_doc())
            cd = make_chain_dir(tmp)
            r = run(MATRIX, "--sync-dir", str(sd), "--chain-dir", str(cd))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_malformed_rule_body_fails(self):
        """A valid-looking matrix over an unparseable rule is a false green."""
        doc = sync_doc(when_body="this is not a conjunct at all",
                       then_body="nor is this a target")
        with tempfile.TemporaryDirectory() as tmp:
            sd = make_sync_dir(tmp, doc)
            r = run(MATRIX, "--sync-dir", str(sd))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("malformed sync rule", r.stdout)

    def test_malformed_where_block_fails(self):
        doc = sync_doc().replace(
            "then {", "where {\n    this is not a where clause\n}\nthen {", 1)
        with tempfile.TemporaryDirectory() as tmp:
            sd = make_sync_dir(tmp, doc)
            r = run(MATRIX, "--sync-dir", str(sd))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("malformed `where` block", r.stdout)

    def test_bogus_row_ids_fail_against_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            sd = make_sync_dir(tmp, sync_doc(source="999", target="888"))
            cd = make_chain_dir(tmp)
            r = run(MATRIX, "--sync-dir", str(sd), "--chain-dir", str(cd))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("does not exist in the chain table", r.stdout)

    def test_signature_not_naming_chain_action_fails(self):
        doc = sync_doc(then_sig="Something/else: [ x: ?x ]",
                       then_body="Something/else: [ x: ?x ]")
        with tempfile.TemporaryDirectory() as tmp:
            sd = make_sync_dir(tmp, doc)
            cd = make_chain_dir(tmp)
            r = run(MATRIX, "--sync-dir", str(sd), "--chain-dir", str(cd))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("does not name chain row 2", r.stdout)


class TransitionCoverageSoundnessTests(unittest.TestCase):

    def _feature(self, tmp, *, frozen=False):
        root = Path(tmp) / "features" / "UC-01-x"
        chain = root / "stages" / "01b_chain-table" / "output"
        chain.mkdir(parents=True)
        (chain / "do-a-thing-chain.md").write_text(CHAIN, encoding="utf-8")
        cdir = root / "stages" / "02_concepts" / "output"
        cdir.mkdir(parents=True)
        (cdir / "Thing.concept.md").write_text(
            "concept Thing [ThingId]\nintroduced-by UC-01-x\npurpose\n    p\n\n"
            "## State\n\n```\nname: ThingId -> Text -- mandatory\n```\n\n"
            "## Actions\n\n```\ncreate [ name: Text ] => [ id: ThingId ]\n"
            '    flow token: { action: "Thing.create", name, id, outcome: "CREATED" }\n```\n',
            encoding="utf-8")
        rm = root / "stages" / "01a_responsibility-map" / "output"
        rm.mkdir(parents=True)
        (rm / "responsibility-map.md").write_text(
            "| Concept | Origin | Owned state (one line) | Owned actions | Notes |\n"
            "|---|---|---|---|---|\n"
            "| `Thing` | `new` | name | create | x |\n", encoding="utf-8")
        if frozen:
            (root / "RESUME.md").write_text(
                "# RESUME\n\n- **Gate 3 (Acceptance spec):** `approved`\n",
                encoding="utf-8")
        return root

    def _write_expected(self, root):
        expected, _ = gs.derive_syncs_for_feature(str(root))
        sd = root / "stages" / "03_syncs" / "output"
        sd.mkdir(parents=True, exist_ok=True)
        for g in expected:
            (sd / f"{g.stem}.sync.md").write_text(sync_doc(), encoding="utf-8")
        return expected, sd

    def test_missing_transition_with_count_matching_file_fails_when_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._feature(tmp)
            expected, sd = self._write_expected(root)
            self.assertGreaterEqual(len(expected), 2)
            # Remove one real carrier and add an unrelated file so counts agree.
            (sd / f"{expected[0].stem}.sync.md").unlink()
            (sd / "Unrelated.sync.md").write_text(sync_doc(), encoding="utf-8")
            r = run(TRANSITION, "--feature", str(root))
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn(expected[0].stem, r.stdout)

    def test_frozen_feature_tolerates_legacy_naming(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._feature(tmp, frozen=True)
            expected, sd = self._write_expected(root)
            (sd / f"{expected[0].stem}.sync.md").unlink()
            (sd / "Unrelated.sync.md").write_text(sync_doc(), encoding="utf-8")
            r = run(TRANSITION, "--feature", str(root))
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("frozen", r.stdout)


SPEC = """sync GrantForThingsWhenCreateCreated

## Sync Contract Matrix

| Source row | Target row | `when` signature | `then` signature | Allowed literals |
|---|---|---|---|---|
| `2` | `2` | `Thing/create: [...] => [ Created ] ∧ requested: Web/request: [ route: "things" ] => [ Routed ]` | `Session/grant: [ userId: ?user ]` | `<none>` |

## Rule

```
when {
    Thing/create: [ name: ?n ] => [ Created ; id: ?id ]
    requested: Web/request: [ route: "things" ; method: "POST" ] => [ Routed ; ... ]
}
where {
    bind ( triggerField("id") as ?user )
}
then {
    Session/grant: [ userId: ?user ]
}
```

## Cites

- `../01_usecase/output/usecase.md` — scenario "Do a thing"
"""

GOOD_JAVA = """package x;
import static dev.legible.engine.Dsl.*;
final class ThingSyncs {
    static Object grant() {
        return rule("GrantForThingsWhenCreateCreated")
            .when(conj("trigger", "Thing", "create", "Created"))
            .and(conj("requested", "Web", "request", "Routed")
                    .matching(Map.of("route", "things")))
            .where(bind("?user", triggerField("id")))
            .then(invoke("Session", "grant", args("userId", ref("?user"))))
            .build();
    }
}
"""


def make_parity_world(tmp, java):
    root = Path(tmp)
    sd = root / "syncs"
    sd.mkdir()
    (sd / "GrantForThingsWhenCreateCreated.sync.md").write_text(SPEC,
                                                               encoding="utf-8")
    impl = root / "impl"
    impl.mkdir()
    (impl / "ThingSyncs.java").write_text(java, encoding="utf-8")
    return sd, impl


class ImplementationParitySoundnessTests(unittest.TestCase):

    def _run(self, tmp, java):
        sd, impl = make_parity_world(tmp, java)
        return run(PARITY, "--sync-dir", str(sd), "--sync-impl-dir", str(impl),
                   "--strict-trigger")

    def test_full_parity_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(tmp, GOOD_JAVA)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_second_conjunct_route_mismatch_fails(self):
        bad = GOOD_JAVA.replace('Map.of("route", "things")',
                                'Map.of("route", "WRONG")')
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(tmp, bad)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("route-literal mismatch", r.stdout)

    def test_second_conjunct_action_mismatch_fails(self):
        bad = GOOD_JAVA.replace('conj("requested", "Web", "request", "Routed")',
                                'conj("requested", "Web", "other", "Routed")')
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(tmp, bad)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("conjunct mismatch", r.stdout)

    def test_argument_name_mismatch_fails(self):
        bad = GOOD_JAVA.replace('args("userId", ref("?user"))',
                                'args("WRONGARG", ref("?user"))')
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(tmp, bad)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("argument mismatch", r.stdout)

    def test_where_binding_source_mismatch_fails(self):
        """Changing a binding's source (same var) is a provenance drift."""
        bad = GOOD_JAVA.replace('triggerField("id")', 'triggerInput("id")')
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(tmp, bad)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("where-clause mismatch", r.stdout)

    def test_impl_where_without_spec_block_is_unresolved(self):
        """A spec with no `where { }` block cannot verify an impl that has
        `.where(...)` — that is unresolved, not a silent pass."""
        spec_without_where = SPEC.split("where {")[0] + "then {" + \
            SPEC.split("then {", 1)[1]
        with tempfile.TemporaryDirectory() as tmp:
            sd, impl = make_parity_world(tmp, GOOD_JAVA)
            (sd / "GrantForThingsWhenCreateCreated.sync.md").write_text(
                spec_without_where, encoding="utf-8")
            r = run(PARITY, "--sync-dir", str(sd), "--sync-impl-dir", str(impl),
                    "--strict-trigger")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("unresolved", r.stdout)

    def test_helper_based_then_is_unresolved_not_passed(self):
        """A `then` with no inline invoke(...) cannot be verified — it must be
        reported unresolved, not silently accepted."""
        bad = GOOD_JAVA.replace(
            '.then(invoke("Session", "grant", args("userId", ref("?user"))))',
            '.then(helper())')
        with tempfile.TemporaryDirectory() as tmp:
            r = self._run(tmp, bad)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("unresolved", r.stdout)


if __name__ == "__main__":
    unittest.main()
