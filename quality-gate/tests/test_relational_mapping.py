#!/usr/bin/env python3
"""Regression coverage for the relational storage-mapping gate."""

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUALITY_GATE = REPO_ROOT / "quality-gate"
sys.path.insert(0, str(QUALITY_GATE))

import verify_relational_mapping as relational  # noqa: E402


class RelationalMappingTests(unittest.TestCase):

    def test_rdf_mapping_is_not_relational(self):
        self.assertFalse(relational.is_relational(
            "# Storage mapping\n- Concept region: one named graph per concept\n"
            "- Fact type: RDF triple"))

    def test_postgres_mapping_is_relational(self):
        self.assertTrue(relational.is_relational(
            "# Storage mapping\n- Profile: PostgreSQL schema per application"))

    def test_create_table_mapping_is_relational(self):
        self.assertTrue(relational.is_relational(
            "CREATE TABLE user_accounts (user_id uuid PRIMARY KEY)"))

    def test_foreign_key_is_a_violation(self):
        failures = relational.validate_relational_mapping(
            "CREATE TABLE passwordauth_credentials (\n"
            "  user_id uuid REFERENCES user_accounts(user_id)\n"
            ")")
        self.assertEqual(1, len(failures))
        self.assertIn("R2", failures[0])

    def test_no_foreign_key_is_clean(self):
        failures = relational.validate_relational_mapping(
            "CREATE TABLE user_accounts (\n"
            "  user_id uuid PRIMARY KEY,\n"
            "  username varchar(255) NOT NULL UNIQUE\n"
            ")")
        self.assertEqual(0, len(failures))


if __name__ == "__main__":
    unittest.main()
