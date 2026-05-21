# reference-impl/

This folder will hold one or more **implementation profiles**: concrete
language/framework choices that realise the WYSIWID pattern under the
hard rules in
[`../methodology/implementation/RULES.md`](../methodology/implementation/RULES.md).

A profile is a self-contained subfolder. The seed ships one profile
skeleton:

- [`java-micronaut-jena/`](java-micronaut-jena/) — Java 21 + Micronaut
  for HTTP/runtime, Apache Jena for per-concept RDF graphs and
  flow-token logging.

Other profiles (TypeScript/Deno, Kotlin/Ktor, Python/FastAPI, …) can
be added as sibling folders without changing anything in
`methodology/`. The methodology is profile-independent.

For repositories created from the CLAD template, treat this directory as
an **upstream reference shelf**, not as the main product code root. If
you choose one of these profiles, copy the selected profile's starter
code and conventions into your own runtime/app directory and continue
product-specific implementation there. Do not mix downstream business
code back into `reference-impl/`, or the starter profile stops being a
clean exemplar.
