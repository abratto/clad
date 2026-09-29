#!/usr/bin/env python3
"""Property tests: deterministic generators produce artefacts their sibling
verify_* checks accept — generator output must satisfy the gate by construction.

The core assertion types:

  1. `generate_syncs` over a fixture feature reproduces the canonical sync-name
     set (stem equality) and the emitted *.sync.md files pass
     verify_sync_matrix / verify_sync_cycle_graph / verify_sync_overlap.
  2. `generate_contract` excludes the bootstrap Web concept and emits one contract per
     business concept.
  3. `generate_sync_cards` emits one card per participating concept and a
     pattern-d-summary.
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"
GEN_SYNCS = QG / "generate_syncs.py"
GEN_CONTRACT = QG / "generate_contract.py"
GEN_CARDS = QG / "generate_sync_cards.py"
GEN_DATA = QG / "generate_data_model.py"
VERIFY_MATRIX = QG / "verify_sync_matrix.py"
VERIFY_CYCLE = QG / "verify_sync_cycle_graph.py"
VERIFY_OVERLAP = QG / "verify_sync_overlap.py"
VERIFY_DATA_MODEL = QG / "verify_data_model.py"
VERIFY_CONTRACT_PARITY = QG / "verify_contract_parity.py"
VERIFY_OUTCOME_ALIGNMENT = QG / "verify_outcome_alignment.py"
VERIFY_ACTION_CHAIN = QG / "verify_action_chain.py"


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(script), *map(str, args)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )


class GeneratorPropertyTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Copy the worked example so generators write into an isolated tree.
        cls.tmp = tempfile.TemporaryDirectory()
        cls.platform = Path(cls.tmp.name)
        # Feature must sit under a `features/` dir for scope derivation.
        cls.features = cls.platform / "features"
        cls.features.mkdir()
        src = REPO_ROOT / "examples" / "UC-00-login"
        cls.feature = cls.features / "UC-00-login"
        shutil.copytree(src, cls.feature)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def sync_dir(self):
        return self.feature / "stages" / "03_syncs" / "output"

    def test_generate_syncs_reproduces_canonical_names(self):
        # Wipe and regenerate.
        d = self.sync_dir()
        for f in d.glob("*.sync.md"):
            f.unlink()

        r = run(GEN_SYNCS, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        stems = sorted(f.name.replace(".sync.md", "") for f in d.glob("*.sync.md"))
        # UC-00-login has exactly seven syncs.
        self.assertEqual(len(stems), 7, stems)
        # Action-first naming grammar v3 (maintenance/sync-name-grammar-v3.md),
        # plus v3.1's route component for route-scoped bootstraps AND pinned
        # rules (maintenance/route-scoped-sync-names.md): the chain root is
        # `Web/request[POST /login]`, so every rule in the pack carries `ForLogin`.
        self.assertIn("GrantForLoginWhenCheckOk", stems)
        self.assertIn("LookupByUsernameForLoginWhenRequestRouted", stems)
        self.assertIn("RespondForLoginWhenCheckLocked", stems)
        self.assertIn("RespondForLoginWhenLookupByUsernameRefused", stems)

    def test_generated_syncs_pass_sync_checks(self):
        d = self.sync_dir()
        for f in d.glob("*.sync.md"):
            f.unlink()
        run(GEN_SYNCS, "--feature", self.feature, "--write")

        for script in (VERIFY_MATRIX, VERIFY_CYCLE, VERIFY_OVERLAP):
            r = run(script, "--sync-dir", d)
            self.assertEqual(
                r.returncode, 0,
                f"{script.name} failed post-generation:\n{r.stdout}{r.stderr}")

    def test_generate_contract_excludes_bootstrap_and_covers_concepts(self):
        contract_dir = self.feature / "stages" / "04_implement" / "04b_contract" / "output"
        for f in contract_dir.glob("*.contract.md"):
            f.unlink()
        r = run(GEN_CONTRACT, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        specs = sorted(f.name.replace(".contract.md", "") for f in contract_dir.glob("*.contract.md"))
        self.assertEqual(specs, ["PasswordAuth", "Session", "UserNaming"])
        self.assertNotIn("Web", specs)
        # Outcome enums must be SCREAMING_SNAKE_CASE (normalized), not naive .upper().
        pa = (contract_dir / "PasswordAuth.contract.md").read_text(encoding="utf-8")
        self.assertIn("`BAD_PASSWORD`", pa)
        self.assertNotIn("`BADPASSWORD`", pa)

    def test_contract_enums_come_from_the_concept_not_one_features_chain(self):
        """A canonical contract keeps every action's outcomes.

        A feature that only *extends* a concept does not invoke its older
        actions, so an enum derived purely from this feature's chain tables
        would silently drop them (UC-03 lost `enrol`'s and `acquire`'s)."""
        sys.path.insert(0, str(QG))
        import generate_contract as gc

        spec = self.feature / "stages" / "02_concepts" / "output" / "UserNaming.concept.md"
        got = gc.collect_concept_outcomes(str(spec))
        # The concept's own flow tokens are the canonical source.
        self.assertTrue(got, "no flow-token outcomes parsed from the concept spec")
        for (concept, action), values in got.items():
            self.assertEqual(concept, "UserNaming")
            for v in values:
                self.assertRegex(v, r"^[A-Z][A-Z0-9_]*$")

    def test_every_non_bootstrap_rule_pins_its_flow_root(self):
        """The flow pin (maintenance/sync-flow-pinning.md).

        A flow token scopes a match to one flow, but within a flow any rule whose
        `when` matches fires — so two use cases sharing a completion fire each
        other's rules. Every non-bootstrap rule therefore names its flow root
        first, with its route matcher, and the pin is NOT a name component (it is
        in every such rule, so it discriminates nothing)."""
        sync_dir = self.sync_dir()
        for f in sync_dir.glob("*.sync.md"):
            f.unlink()
        r = run(GEN_SYNCS, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

        pinned = 0
        for path in sorted(sync_dir.glob("*.sync.md")):
            text = path.read_text(encoding="utf-8")
            if "WhenRequestRouted" in path.name:
                # The bootstrap IS the flow root: it has no pin to carry.
                self.assertNotIn("requested: Web/request:", text, path.name)
                continue
            self.assertIn("requested: Web/request:", text,
                          f"{path.name} must pin its flow root")
            pinned += 1
        self.assertGreater(pinned, 0, "no non-bootstrap rules to check")

    def test_the_pin_route_scopes_a_pinned_rules_name(self):
        """A pinned rule's route is a name component; the pin conjunct is not.

        Two use cases may pin the same trigger+target on different routes, so
        the route is what lets `causedBySync` say which fired
        (maintenance/route-scoped-sync-names.md). The uniform `requested`
        conjunct itself still never appears."""
        sync_dir = self.sync_dir()
        stems = {f.name.replace(".sync.md", "") for f in sync_dir.glob("*.sync.md")}
        self.assertIn("CheckForLoginWhenLookupByUsernameFound", stems)
        self.assertFalse([s for s in stems if "JoinRequestRouted" in s],
                         "the uniform pin conjunct must not appear in any name")

    def test_generate_cards_cover_participating_concepts(self):
        dep_dir = self.feature / "stages" / "03a_dependency-review" / "output"
        r = run(GEN_CARDS, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cards = sorted(f.name.replace("-card.md", "") for f in dep_dir.glob("*-card.md"))
        # UC-00-login has cards for the 3 business concepts AND the Web bootstrap.
        self.assertEqual(cards, ["PasswordAuth", "Session", "UserNaming", "Web"])
        self.assertTrue((dep_dir / "pattern-d-summary.md").exists())

    def test_generate_data_model_passes_csdp_structure_check(self):
        data_dir = self.feature / "stages" / "03b_data-model" / "output"
        for f in data_dir.glob("*.data-model.md"):
            f.unlink()
        r = run(GEN_DATA, "--feature", self.feature, "--write")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        models = sorted(f.name.replace(".data-model.md", "") for f in data_dir.glob("*.data-model.md"))
        self.assertEqual(models, ["PasswordAuth", "Session", "UserNaming"])
        r = run(VERIFY_DATA_MODEL,
                "--data-dir", data_dir,
                "--concept-dir", self.feature / "stages" / "02_concepts" / "output")
        self.assertEqual(r.returncode, 0,
                         f"generated data models failed CSDP check:\n{r.stdout}{r.stderr}")

    def test_route_scoped_bootstrap_renders_route_matcher(self):
        """A `Web/request` bootstrap sync carries its R15 route matcher.

        The generator previously emitted `[ ... ]` and the author added the
        route/method by hand every UC."""
        sys.path.insert(0, str(QG))
        import generate_syncs as gs
        g = gs.GeneratedSync(
            name="SessionValidateForTagsWhenWebRequestRouted",
            stem="SessionValidateForTagsWhenWebRequestRouted",
            trigger_concept="Web", trigger_action="request",
            trigger_completion="Routed",
            target_concept="Session", target_action="validate",
            source_row="1", target_row="2",
            when_sig='Web/request: [ route: "tags" ; method: "GET" ] => [ Routed ]',
            then_sig="Session/validate: [ <args> ]",
            literals='route = "tags" ; method = "GET"',
            binds=[], pattern_d_notes=[], cited_scenario="List Tags",
            route="tags", method="GET")
        out = gs.render_sync(g)
        self.assertIn('route: "tags" ; method: "GET"', out)
        self.assertIn('route = "tags"', out)

    def test_end_to_end_downstream_chain_passes_all_cross_stage_checks(self):
        """Regenerate the full derivable chain (03→03a→03b→04b→04c) from the
        authored upstream (01/01a/02) and run every cross-stage verify_* over
        the result. This is the integration test that catches coherence bugs
        (e.g. outcome normalization drift) that per-file unit tests miss."""
        f = self.feature
        # Regenerate every derivable downstream stage.
        for gen, kwargs in [
            (GEN_SYNCS, {}),
            (GEN_CARDS, {}),
            (GEN_DATA, {}),
            (GEN_CONTRACT, {}),
        ]:
            r = run(gen, "--feature", f, "--write")
            self.assertEqual(r.returncode, 0, f"{gen.name}:\n{r.stdout}{r.stderr}")

        checks = [
            (VERIFY_MATRIX, "--sync-dir", f / "stages/03_syncs/output"),
            (VERIFY_CYCLE, "--sync-dir", f / "stages/03_syncs/output"),
            (VERIFY_OVERLAP, "--sync-dir", f / "stages/03_syncs/output"),
            (VERIFY_DATA_MODEL, "--data-dir", f / "stages/03b_data-model/output",
             "--concept-dir", f / "stages/02_concepts/output"),
            (VERIFY_CONTRACT_PARITY, "--concept-dir", f / "stages/02_concepts/output",
             "--contract-dir", f / "stages/04_implement/04b_contract/output"),
            (VERIFY_OUTCOME_ALIGNMENT, "--chain-dir", f / "stages/01b_chain-table/output",
             "--contract-dir", f / "stages/04_implement/04b_contract/output"),
            (VERIFY_ACTION_CHAIN,
             "--resp-map", f / "stages/01a_responsibility-map/output/responsibility-map.md",
             "--chain-dir", f / "stages/01b_chain-table/output",
             "--concept-dir", f / "stages/02_concepts/output",
             "--sync-dir", f / "stages/03_syncs/output",
             "--dep-dir", f / "stages/03a_dependency-review/output",
             "--contract-dir", f / "stages/04_implement/04b_contract/output"),
        ]
        for script, *args in checks:
            r = run(script, *args)
            self.assertEqual(r.returncode, 0,
                             f"{script.name} failed on regenerated chain:\n{r.stdout}{r.stderr}")


class BranchedChainGeneratorTests(unittest.TestCase):
    """A chain with an extension branch must derive one sync per real edge,
    matched by completion token — not by adjacent row position (which used to
    fabricate a sync across the terminal row)."""

    def test_branch_rows_derive_four_syncs_no_fabrication(self):
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "features/UC-01-library-loans"
            chain = feature / "stages/01b_chain-table/output"
            chain.mkdir(parents=True)
            rows = [
                ("1", "`Web/request[POST /lend]`", "`Web.request`", "`Routed`"),
                ("2", "`Web.request[Routed]`", "`Inventory.lend`", "`Lent`"),
                ("3", "`Inventory.lend[Lent]`", "`Ledger.record`", "`Recorded`"),
                ("4", "`Ledger.record[Recorded]`", "`Web.respond[200]`", "`Sent`"),
                ("5", "`Web.request[Routed]`", "`Inventory.lend`", "`Unavailable`"),
                ("6", "`Inventory.lend[Unavailable]`", "`Web.respond[409]`", "`Sent`"),
            ]
            body = ["# Chain table — `lend-copy`", "",
                    "| # | When | Then | Inputs | Outcome | Why this step |",
                    "|---|---|---|---|---|---|"]
            for num, when, then, outcome in rows:
                body.append(f"| {num} | {when} | {then} | `x` | {outcome} | e |")
            (chain / "lend-copy-chain.md").write_text(
                "\n".join(body) + "\n", encoding="utf-8")

            r = run(GEN_SYNCS, "--feature", feature)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            stems = sorted(line.split("WRITE ", 1)[1].split("  ")[0]
                           .replace(".sync.md", "")
                           for line in r.stdout.splitlines()
                           if "WOULD WRITE" in line)
            self.assertEqual(len(stems), 4, stems)
            # Action-first naming grammar v3 (maintenance/sync-name-grammar-v3.md),
            # plus the route component for pinned rules.
            self.assertIn("LendForLendWhenRequestRouted", stems)
            self.assertIn("RecordForLendWhenLendLent", stems)
            self.assertIn("RespondForLendWhenRecordRecorded", stems)
            self.assertIn("RespondForLendWhenLendUnavailable", stems)
            # The old positional pairing fabricated this transition across the
            # terminal row 4 -> branch row 5.
            self.assertNotIn("RespondWhenRespondSent", stems)


class GeneratorRegressionTests(unittest.TestCase):
    """Defects D10/D11/D20: payload lowering, respond literals, branch scenarios."""

    def _write_chain(self, chain, name, rows):
        chain.mkdir(parents=True, exist_ok=True)
        body = ["# Chain table", "",
                "| # | When | Then | Inputs | Outcome | Why this step |",
                "|---|---|---|---|---|---|"]
        for num, when, then, outcome in rows:
            body.append(f"| {num} | `{when}` | `{then}` | `x` | `{outcome}` | e |")
        (chain / f"{name}-chain.md").write_text("\n".join(body) + "\n",
                                                encoding="utf-8")

    def test_multi_field_payload_splits_into_one_bind_per_field(self):
        sys.path.insert(0, str(QG))
        import generate_syncs as gs
        with tempfile.TemporaryDirectory() as temporary:
            feature = Path(temporary) / "features/UC-01-lend"
            chain = feature / "stages/01b_chain-table/output"
            self._write_chain(chain, "lend-copy", [
                ("1", "Web/request[POST /lend]", "Web.request", "Routed(ref, name)"),
                ("2", "Web.request[Routed(ref, name)]", "Inventory.lend", "Lent"),
                ("3", "Inventory.lend[Lent]", "Web.respond[200]", "Sent"),
            ])
            syncs, _ = gs.derive_syncs_for_feature(str(feature))
            lends = [s for s in syncs if s.target_action == "lend"]
            self.assertEqual(len(lends), 1, [s.target_action for s in syncs])
            self.assertEqual(sorted(v for v, _p, _s in lends[0].binds),
                             ["?name", "?ref"])
            responses = [s for s in syncs if s.target_action == "respond"]
            self.assertIn("status = 200", responses[0].literals)


if __name__ == "__main__":
    unittest.main()
