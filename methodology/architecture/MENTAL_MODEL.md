# Mental model — WYSIWID for object-oriented engineers

CLAD's WYSIWID architecture (Concepts + Syncs over an action log) is
the same shape as object-oriented design, with one critical
difference: **all coupling is explicit and inspectable in the
artefacts**. This file gives you the parallel as a translation table
plus the artefact map, so you can map what you already know onto what
the methodology asks for.

The parallel below is **precise, not metaphorical**. Each row names
two things that play the same structural role.

---

## OO ↔ WYSIWID parallel

| Object-oriented concept | WYSIWID equivalent | Where it lives |
|---|---|---|
| Class | Concept | `*.concept.md`, then `<Name>Concept.java` (or profile equivalent) |
| Method signature | Action signature (name, args, outcome enum) | Concept spec `actions:` section, then `<Name>.spec.md` |
| Field / instance variable | State field in concept's named region | Concept spec `state:` section, then data model (`<Name>.data-model.md`), then storage mapping (`<Name>.storage.md`) |
| Encapsulation (`private`) | One named region per concept (R2); no other concept reads it | Hard rule R2; per-concept named graph (Java/Jena) or schema |
| Method call between objects | Sync: `then: OtherConcept.action(...)` | One `*.sync.md` per coordination link |
| `someOther.getFoo()` (field access on another object) | **Pattern D** — sync `where:` reads another concept's named region | `where:` clause in sync; row in 03a dependency review |
| Return value used by caller | Pattern B — flow-sibling output joined by flow-token id | `where:` clause; row in chain table |
| Method parameter | Pattern A — read from the original `Web.handle` body | `where:` clause; row in chain table |
| Hard-coded literal in a caller | Pattern C — sync constant | `where:` clause |
| Sequence diagram | Chain table (Stage 02b) — table form is canonical, Mermaid is derived | `<scenario>-chain.md` |
| CRC card | Per-concept dependency review card (Stage 03a) | `<concept>-card.md` |
| `interface` / public API | Concept's `actions:` section + outcome enums | Concept spec; `<Name>.spec.md` |
| Dependency injection of a service | A sync that wires `Web.handle → SomeService.action` | `*.sync.md` |
| Observer / event bus | The action log (every action emits a flow-token completion event; syncs subscribe via `when:`) | Built into the runtime; not user code |
| Polymorphism | Multiple syncs matching the same `when:` pattern (each fires independently) | `*.sync.md` files; commutativity required (see SYNCHRONIZATIONS.md) |

---

## The key difference: coupling is in the data, not the code

In OO, coupling lives in the source: `import OtherClass`,
`new OtherService()`, a constructor parameter. To find what depends
on what, you grep imports. Reachability is implicit in the call
graph.

In WYSIWID, coupling lives in the artefacts:

- Every cross-concept invocation is one row in one `*.sync.md`.
- Every cross-concept state read is one row in one `*.sync.md`'s
  `where:` clause **and** one row in the consumer's dependency-
  review card **and** one row in the feature's `pattern-d-summary.md`.
- Every concept's own behaviour is one `*.concept.md` and (in code)
  one named region with no foreign references.

The design is in the data. The code follows mechanically. This is
why R1 ("no concept imports another concept") is enforceable by a
grep, why Stage 03a can produce a complete coupling surface in one
pass, and why Stage 05 can back-trace a runtime flow token to a
named scenario without instrumentation.

The OO version of "find every place that calls `User.getEmail()`" is
an IDE feature. The WYSIWID version is `grep "User\." -- "*.sync.md"`
plus the rows in `pattern-d-summary.md`. It is a **flat artefact**
rather than a runtime traversal, and that is the property the
methodology is paying for.

---

## Complete artefact map

If you are an OO engineer trying to figure out where each familiar
artefact "lives" in CLAD, this is the full map:

| OO artefact | CLAD equivalent | Stage that produces it | Layer |
|---|---|---|---|
| Class diagram | Responsibility map | 02a | output |
| Sequence diagram | Chain table | 02b | output |
| Class definition (with methods) | Concept spec | 02 | output |
| CRC card (responsibilities + collaborators) | Dependency review card | 03a | output |
| Conceptual schema | Data model file | 03b | output |
| Schema / storage realization | Storage mapping file | 04a | output |
| Public interface (`.h`, `.d.ts`, etc.) | SPEC slice | 04b | output |
| Integration test (HTTP-level) | Flow test | 04c | output |
| Unit test | Concept test | 04d | output |
| Wiring test (does the framework call the right method?) | Sync test | 04e | output |
| Production trace / APM span tree | Flow-token tree | 05 | runtime |

---

## What does **not** translate

- **Inheritance.** WYSIWID has no inheritance between concepts. The
  closest equivalent is multiple concepts implementing the same
  *kind* of action (`User.register`, `Account.register`) — but they
  are coordinated via syncs, not via a shared base. If you find
  yourself wanting inheritance, the right move is usually a third
  concept that owns the shared responsibility, called by syncs from
  the others.
- **Mutable shared references.** A concept never holds a pointer
  into another concept. If you need to reach `User`'s email from
  `PasswordReset`, you do it via Pattern D (a typed read of the
  named region by id) at the moment you need it, not via a cached
  reference.
- **Constructors with side effects.** Concept "construction" (boot)
  is the responsibility of the runtime, not user code. Side effects
  belong in actions.

---

## Further reading

- [`LEGIBLE.md`](LEGIBLE.md) — what WYSIWID is and why
- [`CONCEPTS.md`](CONCEPTS.md) — concept anatomy
- [`SYNCHRONIZATIONS.md`](SYNCHRONIZATIONS.md) — how syncs work
- [`SYNC_PATTERNS.md`](SYNC_PATTERNS.md) — the four legal data-flow patterns
- [`../implementation/STAGES.md`](../implementation/STAGES.md) — stage-by-stage walk
