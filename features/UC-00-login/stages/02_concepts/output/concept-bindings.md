<!-- Stage 02 output for UC-00-login. This file is ALWAYS emitted. Under the
system-scope concept model (R22) it records which canonical concepts the
feature uses and how. See templates/concept-bindings.md. -->

# Concept bindings — UC-00-login

> UC-00-login is the worked example that introduced the concept vocabulary, so
> every row is `new`: the proposal is authored here and was promoted into the
> canonical corpus (`features/_system/concepts/`) with provenance
> `introduced-by UC-00-login`. Bootstrap concepts are governed separately and
> are not listed.

| Concept | Origin | Actions used | Proposal |
|---|---|---|---|
| `UserNaming` | `new` | `lookupByUsername`, `register` | `UserNaming.concept.md` |
| `PasswordAuth` | `new` | `check`, `setCredential` | `PasswordAuth.concept.md` |
| `Session` | `new` | `grant`, `lookup` | `Session.concept.md` |

## Notes

- Reusing a concept (a later feature) would emit a `reused:UC-00-login` row
  with `—` in the *Proposal* column and no spec copy.
