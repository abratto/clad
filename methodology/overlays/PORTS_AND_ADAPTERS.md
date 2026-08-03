# Architecture overlay — Ports and adapters

> **Status: optional.** Adopt this overlay when a CLAD system has more than
> one transport surface or communicates with infrastructure outside the
> engine. It supplements, but does not replace, the concept and sync rules.

## Purpose

CLAD already makes the business core explicit: concepts own state and policy;
syncs own declarative cross-concept coordination. This overlay makes the
remaining boundary roles explicit:

| Role | Direction | Responsibility |
|---|---|---|
| Primary adapter | External caller -> CLAD flow | Translate a transport signal into an authored bootstrap action, then translate the authored result back to that transport. |
| Secondary adapter | CLAD capability -> external system | Implement a port declared by a concept or engine capability; translate data and protocol details at that boundary. |
| Bootstrap concept | Inside the CLAD flow | Own the transport entry/exit actions and dispatch table. It is not a business concept. |

`Web` is CLAD's HTTP bootstrap example. The general primary-adapter rules live
in [`../architecture/WEB_CONCEPT.md`](../architecture/WEB_CONCEPT.md).

## Boundary rules

### Primary adapters

A primary adapter may:

1. authenticate or normalize a transport request;
2. invoke one authored bootstrap action / flow root;
3. await the authored result; and
4. serialize it to the transport's response, acknowledgement, or display.

It must not call a business concept directly, read business state, choose a
domain branch, or bypass the action/sync chain. A browser or mobile client is
also a primary adapter: it renders state and sends requests, but business
decisions remain in the CLAD flow.

### Secondary adapters

A secondary adapter implements a port required by one concept or by the engine.
Examples include a database driver, mail provider, payment gateway, object
store, identity provider, or outbound message producer.

A secondary adapter may translate protocol, credentials, serialization,
provider errors, and provider-specific acknowledgement details. It must not:

- decide a business outcome or policy;
- invoke another concept or a sync;
- read or mutate a concept's state except through its declared port operation;
- hide retry, idempotency, ordering, or delivery semantics that the concept's
  action outcome needs to expose.

The owning concept defines how a port result becomes an action outcome. Syncs
coordinate work triggered by that outcome; they do not perform the I/O.
Generic dispatch, durable delivery, and adapter registration are engine or
profile concerns, not concept responsibilities.

## Declaring a port

Use [`../../templates/port-spec.md`](../../templates/port-spec.md) when an
external contract constrains the system. Record each port's direction, owner,
source contract, and observable semantics.

- An inbound port names its bootstrap concept and response contract.
- An outbound port names its owning concept or engine capability and the
  declared operation/outcome contract.
- Retry, timeout, idempotency, ordering, and delivery guarantees belong in the
  owner contract when they can change an observable outcome. Provider-specific
  implementation mechanics do not.

Do not create a concept merely to wrap a framework client. Create one only when
the capability owns business state or policy. Otherwise it is a secondary
adapter behind an existing concept or engine port.

## Change routing

| Change | Route |
|---|---|
| Primary or secondary adapter implementation changes while declared contracts and observable semantics stay unchanged | Maintenance route in [`../core/ITERATIVE_CHANGES.md`](../core/ITERATIVE_CHANGES.md) |
| New inbound transport with the same use-case contract | Stage 00 port specification, then 04b/04c boundary tests |
| New outbound capability that creates business responsibility or state | Re-enter at 01a responsibility mapping |
| Port operation, visible response, action outcome, timeout interpretation, retry/idempotency, ordering, or delivery guarantee changes | Re-enter at the earliest owning concept or sync stage; update downstream SPEC and tests |
| Serialization, SDK, credential, provider endpoint, or transport implementation changes that preserve the declared port contract | Maintenance route plus adapter-boundary tests |

When a change is both a provider replacement and an observable semantic change,
use both routes: the maintenance record covers the realization; iterative
re-entry corrects the feature contract.

## Evidence and tests

Keep test ownership aligned with the boundary:

| Boundary | Required evidence |
|---|---|
| Primary adapter | Contract test where an external contract exists; flow test proving the authored action chain; no controller/client business branch. |
| Secondary adapter | Adapter-boundary test covering request mapping, response/error mapping, timeout behavior, and idempotency propagation when applicable. |
| Owning concept | Unit tests proving each declared external result maps to its approved action outcome and completion fields. |
| Full flow | Stage 04c/04e and Stage 05 evidence remain the oracle for user-visible behaviour and flow-token lineage. |

A provider contract-test failure is an adapter realization defect. A concept
outcome or flow-test failure is a contract/behaviour defect. Do not repair the
latter by putting business branching in an adapter.

## Adoption checklist

- [ ] Every external boundary is classified as primary or secondary.
- [ ] Every primary adapter reaches the system only through its bootstrap
      action and returns only an authored result.
- [ ] Every secondary adapter has a named owner and declared observable
      semantics when they matter to a use case.
- [ ] No adapter contains domain policy, cross-concept coordination, or direct
      foreign concept-state access.
- [ ] Boundary tests and the relevant flow tests are included in the test
      matrix.