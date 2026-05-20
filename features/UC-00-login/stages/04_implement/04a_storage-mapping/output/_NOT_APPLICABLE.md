# Not applicable — in-memory profile

The Java reference profile (`reference-impl/java-micronaut-jena/`) is
currently in-memory: each `*Concept` class owns its state in plain
Java collections. Hard rule R2 ("one persistence region per concept")
is satisfied by R1 (no cross-concept imports), since no other concept
can read the field.

When the RDF backend lands in `reference-impl/java-micronaut-jena/`,
this sub-stage will produce one `<Name>.storage.md` per concept
describing how the approved data model maps onto the named graph URI
and triple shape that concept owns.
