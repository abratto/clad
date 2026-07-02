# Port Specification - <system name>

## Source
<!-- URL or file path of the external API contract -->

## Adapter type
<!-- HTTP REST / gRPC / GraphQL / etc. -->

## Fixed conventions
<!-- List the serialization rules imposed by the external contract that are NOT
     derivable from use cases. Examples:
     - Error envelope: {"errors": {"<field>": ["<message>"]}}
     - All resource IDs are integers, not UUIDs
     - Resource responses are wrapped: {"article": {...}}, {"user": {...}}
     - Nested author object required in every comment response
-->

## Contract test suite
<!-- Reference to the external test files, e.g. specs/api/hurl/ -->

## Scope
<!-- Which stages consume this document:
     - Stage 04b: exact response shapes in spec.md
     - Stage 04c: contract-compliance scenarios in .feature files
     - Delivery: contract test tier in CI
-->
