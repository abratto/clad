#!/usr/bin/env python3
"""Regression coverage for the concept-test-derivation gate.

The parser must accept the format the stage template
(`templates/test-intent-derivation-map.md`) actually specifies: a
`### Concept.action -> test class: Class` heading followed by a table whose
columns are `| # | @Nested | Test method | Outcome | ... |`. It must also keep
accepting the legacy header without the `@Nested` column.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "quality-gate" / "verify_concept_test_derivation.py"


class ConceptTestDerivationTests(unittest.TestCase):

    def _run(self, contract_dir, derivation, test_root):
        return subprocess.run(
            [sys.executable, str(SCRIPT),
             "--contract-dir", str(contract_dir),
             "--derivation", str(derivation),
             "--test-source-root", str(test_root)],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )

    def _spec(self, contract_dir):
        contract_dir.mkdir(parents=True, exist_ok=True)
        (contract_dir / "Widget.contract.md").write_text(
            "# Widget\n\n### `check(userId)`\n"
            "- **Outcomes (enum):** `OK`, `BAD`\n",
            encoding="utf-8",
        )

    def _java(self, test_root):
        pkg = test_root / "example"
        pkg.mkdir(parents=True, exist_ok=True)
        (pkg / "WidgetCheckTest.java").write_text(
            "class WidgetCheckTest {\n"
            "    @Test\n    void shouldReturnOk() { }\n"
            "    @Test\n    void shouldReturnBad() { }\n"
            "}\n",
            encoding="utf-8",
        )

    def test_template_format_with_nested_column(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract_dir = root / "spec"
            derivation = root / "concept-test-derivation.md"
            test_root = root / "tests"
            self._spec(contract_dir)
            self._java(test_root)
            derivation.write_text(
                "# Derivation\n\n"
                "### `Widget.check` → test class: `WidgetCheckTest`\n\n"
                "| # | @Nested | Test method | Outcome | Source | "
                "Preconditions |\n"
                "|---|---|---|---|---|---|\n"
                "| 1 | `WhenOk` | `shouldReturnOk()` | `OK` | Flow: `x` | none |\n"
                "| 2 | `WhenBad` | `shouldReturnBad()` | `BAD` | "
                "Spec: `Widget.contract.md:4` | none |\n",
                encoding="utf-8",
            )
            result = self._run(contract_dir, derivation, test_root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_legacy_format_without_nested_column(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract_dir = root / "spec"
            derivation = root / "concept-test-derivation.md"
            test_root = root / "tests"
            self._spec(contract_dir)
            self._java(test_root)
            derivation.write_text(
                "# Derivation\n\n"
                "### `Widget.check` → test class: `WidgetCheckTest`\n\n"
                "| # | Test method | Outcome | Source | Preconditions |\n"
                "|---|---|---|---|---|\n"
                "| 1 | `shouldReturnOk()` | `OK` | Flow: `x` | none |\n"
                "| 2 | `shouldReturnBad()` | `BAD` | Spec: `Widget.contract.md:4` | none |\n",
                encoding="utf-8",
            )
            result = self._run(contract_dir, derivation, test_root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_outcome_row_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract_dir = root / "spec"
            derivation = root / "concept-test-derivation.md"
            test_root = root / "tests"
            self._spec(contract_dir)
            self._java(test_root)
            derivation.write_text(
                "# Derivation\n\n"
                "### `Widget.check` → test class: `WidgetCheckTest`\n\n"
                "| # | @Nested | Test method | Outcome | Source | "
                "Preconditions |\n"
                "|---|---|---|---|---|---|\n"
                "| 1 | `WhenOk` | `shouldReturnOk()` | `OK` | Flow: `x` | none |\n",
                encoding="utf-8",
            )
            result = self._run(contract_dir, derivation, test_root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("BAD", result.stdout)


if __name__ == "__main__":
    unittest.main()
