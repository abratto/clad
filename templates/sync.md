<!-- Template for Stage 03 (03_syncs). Purpose: see methodology/architecture/SYNCHRONIZATIONS.md. -->

# <SyncName> — <one-line purpose>

> Sync template. Declarative only — no branching, no state, no I/O.

<!-- ⚠️ SYNC AUTHORING RULES — READ BEFORE WRITING THE RULE BLOCK

ONE SYNC PER CHAIN-TABLE ROW
  Each row transition in the approved chain table becomes exactly one sync
  file. Do not collapse multiple transitions into one sync. Count the rows
  in 02b_chain-table/output/ for this scenario; you must produce that many
  syncs (minus the Web.handle row, which is the entry point, not a sync
  trigger — unless Web.handle itself is the `when`).

WHERE CLAUSE — DATA ROUTING ONLY
  The `where` clause declares how data flows from the `when` outcome to
  the `then` call. It is a field-path mapping, not a computation engine.

  ALLOWED:
    email    = body.email          (read a field from the flow token)
    userId   = result_of(#2).id    (read a field from an earlier outcome)
    status   = "active"            (sync constant — Pattern C)

  NOT ALLOWED:
    passwordHash = hash(body.password)   (computation — belongs in the concept)
    token        = jwt.sign(payload)     (I/O — belongs in the concept)
    count        = items.length + 1      (arithmetic — belongs in the concept)

  If you find yourself writing a function call in `where`, stop. The
  computation belongs inside the concept action that receives the data.
  Pass the raw field through and let the concept hash/sign/transform it.

LABEL EVERY WHERE PATTERN
  Every `where` line must be prefixed with its pattern label:
    A: — flow-token join (field from Web.handle body)
    B: — flow-sibling join (field from an earlier action's output)
    C: — sync constant (literal value)
    D: — concept-state join (named region of another concept's state)

DECLARE BEFORE USE
  Every variable referenced in the `then` line must either come directly
  from the `when` outcome's flow token, or be declared explicitly in a
  `where` line. You may not reference a name in `then` that does not
  appear in `when` or `where`.

  NOT ALLOWED:
    then: Web.respond(status=422, body={errors: validationErrors})
    — if validationErrors is not declared in `where`, this is invalid.

  ALLOWED:
    where: B: validationErrors = result_of(Account.validate).errors
    then:  Web.respond(status=422, body={errors: validationErrors})
-->

## Rule

```
when:  <Concept>.<action>(<args>) -> <Outcome>
where: A: <local> = body.<field>
       B: <local> = result_of(<Concept>.<action>).<field>
       C: <local> = "<literal value>"
then:  <Concept>.<action>(<args>)
```

## Cites

> Which use-case scenario(s) this sync exists to satisfy.

- `../01_usecase/output/usecase.md` — scenario "<name>"

## Notes

> Optional. Anything a reviewer should know.
