# Port Specification - <system name>

## Port entries

<!-- One row per external boundary. `Owner` is the bootstrap concept for an
     inbound port, or the owning concept / engine capability for an outbound
     port. Observable semantics include retry, idempotency, ordering, timeout,
     and delivery guarantees only when they affect the approved contract. -->

| Name | Direction | Adapter type | Owner | Source contract | Observable semantics | Contract tests |
|---|---|---|---|---|---|---|
| `<name>` | `inbound` or `outbound` | HTTP REST / gRPC / GraphQL / queue / provider SDK | `<Web, Concept, or Engine>` | `<URL or file path>` | `<response shape / idempotency / delivery>` | `<test path or n/a>` |

## Fixed conventions

<!-- List rules imposed by an external contract that are not derivable from
     use cases. For inbound ports, examples include error envelopes, resource
     wrappers, and identifier formats. For outbound ports, examples include
     provider acknowledgement/error mapping or required idempotency headers. -->

## Scope
<!-- Which stages consume this document:
           - Inbound ports: Stage 04b exact response shapes; Stage 04c contract
                scenarios; Delivery contract-test tier.
           - Outbound ports: the owning concept/sync contract and adapter-boundary
                tests; delivery semantics that change outcomes re-enter the feature
                pipeline at the owning stage.
           - See methodology/overlays/PORTS_AND_ADAPTERS.md.
-->
