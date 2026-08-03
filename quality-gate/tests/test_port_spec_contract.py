#!/usr/bin/env python3
"""Regression fixtures for directional port-spec contract validation."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PORT_SPEC_CONTRACT = REPO_ROOT / "quality-gate" / "verify_port_spec_contract.py"


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run(port_spec, spec_dir, feature_dir):
    return subprocess.run(
        [
            sys.executable,
            str(PORT_SPEC_CONTRACT),
            "--port-spec", str(port_spec),
            "--spec-dir", str(spec_dir),
            "--feature-dir", str(feature_dir),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def port_spec(entries):
    return f"""# Port Specification - Test system

## Port entries

| Name | Direction | Adapter type | Owner | Source contract | Observable semantics | Contract tests |
|---|---|---|---|---|---|---|
{entries}

## Fixed conventions

None.

## Scope

Directional port evidence is required by the relevant implementation stage.
"""


class PortSpecContractFixtures(unittest.TestCase):

    def fixture(self, entries, spec_body, feature_body):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        port_spec_path = root / "port-spec.md"
        spec_dir = root / "specs"
        feature_dir = root / "features"
        write(port_spec_path, port_spec(entries))
        write(spec_dir / "Notification.spec.md", spec_body)
        write(feature_dir / "notification.feature", feature_body)
        return port_spec_path, spec_dir, feature_dir

    def test_inbound_port_requires_and_accepts_response_shape_evidence(self):
        port_spec_path, spec_dir, feature_dir = self.fixture(
            "| Login API | inbound | HTTP REST | Web | `openapi/login.yaml` | JSON response envelope | `specs/login.hurl` |",
            """# Notification -- SPEC

## Response shapes

### `POST /login`

- **Success wrapper:** `$.session`
- **Required fields:** `$.session.token` -- `string`
- **Primary error envelope:** `$.errors.credentials`
""",
            """@contract
Feature: Login API

  Scenario: Reject invalid credentials
    Then JSON path `$.errors.credentials` has type `array`
    And the error envelope is `$.errors.credentials`
""",
        )

        result = run(port_spec_path, spec_dir, feature_dir)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_outbound_port_requires_adapter_evidence_not_http_contract_evidence(self):
        port_spec_path, spec_dir, feature_dir = self.fixture(
            "| Welcome email | outbound | provider SDK | Notification | `provider/send-api.md` | idempotency key forwarded | `NotificationMailAdapterTest.java` |",
            "# Notification -- SPEC\n\n## Actions\n\n### sendWelcomeEmail(...) -> OutcomeRef\n",
            "Feature: Welcome email\n\n  Scenario: Send a welcome email\n    Then the message is accepted\n",
        )

        result = run(port_spec_path, spec_dir, feature_dir)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_port_entry_evidence_and_inbound_shapes_fail(self):
        port_spec_path, spec_dir, feature_dir = self.fixture(
            "| Login API | inbound | HTTP REST | Web | `openapi/login.yaml` | JSON response envelope |  |",
            "# Notification -- SPEC\n\n## Actions\n\n### login(...) -> OutcomeRef\n",
            "Feature: Login API\n",
        )

        result = run(port_spec_path, spec_dir, feature_dir)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Contract tests", result.stdout)
        self.assertIn("Response shapes", result.stdout)
        self.assertIn("@contract", result.stdout)


if __name__ == "__main__":
    unittest.main()