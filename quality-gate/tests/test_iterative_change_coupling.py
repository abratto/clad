#!/usr/bin/env python3
"""Regression coverage for iterative-change coupling (R17 presentation change handling)."""

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import verify_iterative_change_coupling as coupling  # noqa: E402


class IterativeChangeCouplingTests(unittest.TestCase):

    def test_import_only_diff_is_presentation_change(self):
        diff = (
            "--- a/UserConcept.java\n"
            "+++ b/UserConcept.java\n"
            "@@ -3,6 +3,6 @@\n"
            "-import com.example.app.engine.ActionLog;\n"
            "-import com.example.app.engine.ConceptAgent;\n"
            "+import dev.legible.engine.ActionLog;\n"
            "+import dev.legible.engine.ConceptAgent;\n"
        )
        self.assertTrue(coupling.is_import_or_package_only_diff(diff))

    def test_package_only_diff_is_presentation_change(self):
        diff = (
            "--- a/FlowManager.java\n"
            "+++ b/FlowManager.java\n"
            "@@ -1 +1 @@\n"
            "-package com.example.app.engine;\n"
            "+package dev.legible.engine;\n"
        )
        self.assertTrue(coupling.is_import_or_package_only_diff(diff))

    def test_behaviour_change_is_not_presentation_change(self):
        diff = (
            "--- a/UserConcept.java\n"
            "+++ b/UserConcept.java\n"
            "@@ -80,6 +80,6 @@\n"
            "-        writeCompletion(inv, Map.of(\"outcome\", ResourceFactory.createStringLiteral(\"FOUND\")));\n"
            "+        writeCompletion(inv, Map.of(\"outcome\", ResourceFactory.createStringLiteral(\"REGISTERED\")));\n"
        )
        self.assertFalse(coupling.is_import_or_package_only_diff(diff))

    def test_mixed_import_and_behaviour_change_is_not_presentation(self):
        diff = (
            "--- a/UserConcept.java\n"
            "+++ b/UserConcept.java\n"
            "@@ -3,7 +3,7 @@\n"
            "-import com.example.app.engine.ConceptAgent;\n"
            "+import dev.legible.engine.ConceptAgent;\n"
            " \n"
            "     private void doRegister(ActionRecord inv) {\n"
            "-        String u = inv.binding(\"username\");\n"
            "+        String u = inv.binding(\"userId\");\n"
        )
        self.assertFalse(coupling.is_import_or_package_only_diff(diff))

    def test_empty_diff_is_presentation_change(self):
        self.assertTrue(coupling.is_import_or_package_only_diff(""))

    # --- D29/D30: bootstrap and non-implementation classes are exempt ------
    def test_bootstrap_concept_impl_is_exempt(self):
        paths = ["app/src/main/java/dev/library/lending/concepts/web/WebConcept.java"]
        self.assertEqual(coupling.changed_concept_impls(paths), set())

    def test_production_concept_impl_is_detected(self):
        paths = ["app/src/main/java/dev/library/lending/concepts/lending/LendingConcept.java"]
        self.assertEqual(coupling.changed_concept_impls(paths), {"Lending"})

    def test_test_class_under_concepts_is_exempt(self):
        paths = ["app/src/test/java/dev/library/lending/concepts/lending/LendingRecordTest.java"]
        self.assertEqual(coupling.changed_concept_impls(paths), set())

    def test_fixture_and_aggregator_are_exempt(self):
        paths = [
            "app/src/main/java/dev/library/lending/syncs/SyncTestFixture.java",
            "app/src/main/java/dev/library/lending/syncs/EnrolSyncRules.java",
        ]
        self.assertEqual(coupling.changed_sync_impls(paths), set())

    def test_sync_impl_is_detected(self):
        paths = ["app/src/main/java/dev/library/lending/syncs/ChargeForLoanWhenOverdue.java"]
        self.assertEqual(coupling.changed_sync_impls(paths), {"ChargeForLoanWhenOverdue"})

    # --- D31: pairing only on modification, not greenfield addition --------
    def test_greenfield_new_file_is_exempt(self):
        paths = ["app/src/main/java/dev/library/lending/concepts/lending/LendingConcept.java"]
        self.assertEqual(
            coupling.changed_concept_impls(paths, is_new=lambda p: True), set())

    def test_modified_existing_impl_is_detected(self):
        paths = ["app/src/main/java/dev/library/lending/concepts/lending/LendingConcept.java"]
        self.assertEqual(
            coupling.changed_concept_impls(paths, is_new=lambda p: False), {"Lending"})

    def test_missing_matches_reports_unpaired_impl(self):
        self.assertEqual(coupling.missing_matches({"Lending"}, {"Stocking"}), ["Lending"])
        self.assertEqual(coupling.missing_matches({"Lending"}, {"Lending"}), [])


if __name__ == "__main__":
    unittest.main()
