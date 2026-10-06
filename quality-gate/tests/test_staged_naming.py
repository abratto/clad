#!/usr/bin/env python3
"""Regression coverage for verify_responsibility_map_shape.py and
verify_chain_map_names.py (maintenance change `staged-naming-discipline`).

01a declares action NAMES only — a signature or outcome enum in the
responsibility map is Stage 02 detail written too early. 01b chain tables
may only invoke action names the 01a map declared — the chain table is the
canonical name source downstream, so it must not invent names.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QG = REPO_ROOT / "quality-gate"

RESP_MAP_CLEAN = """# Responsibility map — UC-01-a

## Concepts

| Concept | Origin | Owned state (one line) | Owned actions | Notes |
|---|---|---|---|---|
| `Web` | `new` | route table | `request`, `respond` | bootstrap |
| `UserNaming` | `new` | `username: UserId -> String` | `register`, `lookupByUsername` | x |
| `PasswordAuth` | `new` | `hashes: Map<UserId, PasswordHash>` | `check` | x |
"""

RESP_MAP_SIGNATURE = RESP_MAP_CLEAN.replace(
    "`register`, `lookupByUsername`",
    "`register`, `lookupByUsername(username) -> Found(userId) | NotFound`")

RESP_MAP_OUTCOME = RESP_MAP_CLEAN.replace(
    "`check`", "`check [ ok ]`")

CHAIN_OK = """# Chain table — `successful-login`

| # | When | Then | Inputs | Outcome | Why this step |
|---|---|---|---|---|---|
| 1 | `Web/request[POST /login]` | `Web.request` | `POST /login` | `Routed` | entry |
| 2 | `Web.request[Routed]` | `UserNaming.lookupByUsername` | `username` | `Found(userId)` | find the user |
| 3 | `UserNaming.lookupByUsername[Found(userId)]` | `PasswordAuth.check` | `userId`, `password` | `Ok` | verify |
| 4 | `PasswordAuth.check[Ok]` | `Web.respond[200]` | `200` | `Sent` | exit |
"""

CHAIN_UNDECLARED = CHAIN_OK.replace(
    "`PasswordAuth.check` | `userId`, `password` | `Ok` | verify |",
    "`PasswordAuth.verify` | `userId`, `password` | `Ok` | verify |")


def run(script, *args):
    return subprocess.run(
        [sys.executable, str(QG / script), *args],
        cwd=REPO_ROOT, capture_output=True, text=True)


class ResponsibilityMapShapeTests(unittest.TestCase):

    def _write(self, root, text):
        path = Path(root) / "responsibility-map.md"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_clean_map_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            resp = self._write(temporary, RESP_MAP_CLEAN)
            result = run("verify_responsibility_map_shape.py",
                         "--resp-map", resp)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_signature_in_actions_cell_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            resp = self._write(temporary, RESP_MAP_SIGNATURE)
            result = run("verify_responsibility_map_shape.py",
                         "--resp-map", resp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("UserNaming", result.stdout)
            self.assertIn("Stage 02", result.stdout)

    def test_outcome_enum_in_actions_cell_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            resp = self._write(temporary, RESP_MAP_OUTCOME)
            result = run("verify_responsibility_map_shape.py",
                         "--resp-map", resp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PasswordAuth", result.stdout)

    def test_typed_state_column_is_not_flagged(self):
        # `username: UserId -> String` in Owned state is legal — only the
        # Owned actions column is checked.
        with tempfile.TemporaryDirectory() as temporary:
            resp = self._write(temporary, RESP_MAP_CLEAN)
            result = run("verify_responsibility_map_shape.py",
                         "--resp-map", resp)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)

    def test_missing_file_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run("verify_responsibility_map_shape.py",
                         "--resp-map", str(Path(temporary) / "absent.md"))
            self.assertEqual(result.returncode, 0)
            self.assertIn("SKIP", result.stdout)


class ChainMapNamesTests(unittest.TestCase):

    def _fixture(self, root, resp_text, chain_text):
        root = Path(root)
        resp = root / "responsibility-map.md"
        resp.write_text(resp_text, encoding="utf-8")
        chain_dir = root / "chains"
        chain_dir.mkdir()
        (chain_dir / "successful-login-chain.md").write_text(
            chain_text, encoding="utf-8")
        return str(resp), str(chain_dir)

    def test_declared_actions_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            resp, chain_dir = self._fixture(temporary, RESP_MAP_CLEAN, CHAIN_OK)
            result = run("verify_chain_map_names.py",
                         "--resp-map", resp, "--chain-dir", chain_dir)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)
            self.assertIn("PASS", result.stdout)

    def test_undeclared_action_fails_and_names_the_fix(self):
        with tempfile.TemporaryDirectory() as temporary:
            resp, chain_dir = self._fixture(
                temporary, RESP_MAP_CLEAN, CHAIN_UNDECLARED)
            result = run("verify_chain_map_names.py",
                         "--resp-map", resp, "--chain-dir", chain_dir)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PasswordAuth/verify", result.stdout)
            self.assertIn("Owned actions", result.stdout)

    def test_web_actions_are_exempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            resp, chain_dir = self._fixture(temporary, RESP_MAP_CLEAN, CHAIN_OK)
            result = run("verify_chain_map_names.py",
                         "--resp-map", resp, "--chain-dir", chain_dir)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)

    def test_missing_chain_dir_skips(self):
        with tempfile.TemporaryDirectory() as temporary:
            resp = Path(temporary) / "responsibility-map.md"
            resp.write_text(RESP_MAP_CLEAN, encoding="utf-8")
            result = run("verify_chain_map_names.py",
                         "--resp-map", str(resp),
                         "--chain-dir", str(Path(temporary) / "absent"))
            self.assertEqual(result.returncode, 0)
            self.assertIn("SKIP", result.stdout)


if __name__ == "__main__":
    unittest.main()
