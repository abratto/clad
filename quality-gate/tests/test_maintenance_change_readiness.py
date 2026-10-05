#!/usr/bin/env python3
"""Regression coverage for maintenance-change scoping (D1: derived-project config)."""

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import verify_maintenance_change_readiness as maint  # noqa: E402


class MaintenanceScopeTests(unittest.TestCase):

    def test_clad_properties_is_still_maintenance_scoped(self):
        self.assertTrue(maint.is_maintenance_scope("clad.properties"))

    def test_quality_gate_is_not_maintenance_scoped(self):
        self.assertFalse(maint.is_maintenance_scope("quality-gate/advance.py"))
        self.assertFalse(maint.is_maintenance_scope(".githooks/pre-commit"))

    def test_binding_key_only_change_is_project_config(self):
        diff = (
            "-test.command=python3 quality-gate/verify_artefacts.py && mvn test -f reference-impl/pom.xml -pl java-legible -am\n"
            "+test.command=python3 quality-gate/verify_artefacts.py && mvn test -f app/pom.xml\n"
            "-sync.impl.dir=reference-impl/java-legible/src/main/java/dev/legible/example/login\n"
            "+sync.impl.dir=app/src/main/java/dev/library/lending/syncs\n"
        )
        self.assertTrue(maint.is_project_config_only(diff))

    def test_platform_key_change_is_not_project_config(self):
        diff = "+workflow.autonomous=true\n"
        self.assertFalse(maint.is_project_config_only(diff))

    def test_mixed_binding_and_platform_key_is_not_project_config(self):
        diff = (
            "+test.command=mvn -f app/pom.xml test\n"
            "+workflow.session-per-stage=true\n"
        )
        self.assertFalse(maint.is_project_config_only(diff))

    def test_empty_diff_is_not_project_config(self):
        self.assertFalse(maint.is_project_config_only(""))


class FieldValueTests(unittest.TestCase):
    """The shipped template wraps a field's parenthetical onto following lines;
    `field_value` must read the backticked token, not require end-of-line."""

    def test_single_line_field(self):
        self.assertEqual(
            maint.field_value("- **Status:** `active`\n", "Status"), "active")

    def test_template_wrapped_status_is_parsed(self):
        # Verbatim from templates/maintenance-change.md.
        text = (
            "- **Status:** `<draft | active | closed>` (`draft` until design approval,\n"
            "  `active` while implementing, `closed` after evidence approval)\n"
        )
        self.assertEqual(maint.field_value(text, "Status"), "<draft | active | closed>")

    def test_field_with_trailing_prose_is_parsed(self):
        text = "- **Design gate:** `approved` (approved in the source experiment — see below)\n"
        self.assertEqual(maint.field_value(text, "Design gate"), "approved")

    def test_missing_field_is_empty(self):
        self.assertEqual(maint.field_value("- **Change class:** `platform`\n", "Status"), "")

    def test_template_file_status_parses_to_a_known_state(self):
        template = (REPO_ROOT / "templates" / "maintenance-change.md").read_text()
        self.assertIn(
            maint.field_value(template, "Status"),
            {"<draft | active | closed>", "draft", "active", "closed"})


if __name__ == "__main__":
    unittest.main()
