<!-- Additivity exceptions — a feature's `extends` proposals are additive-only
     by default. Purpose & rules: methodology/implementation/RULES.md R22 and
     methodology/architecture/CONCEPTS.md §"Additivity". This file is the output
     shape only. -->

# Additivity exceptions — `<feature-name>`

> An `extends` proposal is **additive only**: it may add fact types, actions,
> and outcomes, but must not drop or restate a canonical line. A deliberate
> removal that is *not* the change's purpose is authorised here — one bullet per
> removed canonical line, the exact line in backticks with a reason and the
> consumer impact.
>
> `verify_concept_additivity.py` waives the additive-only failure **only** for
> lines listed here. An unnoted drop still fails.
>
> A change whose *purpose* is the removal is a **`remodel`**, not an exception:
> it carries `## Migration notes` and needs consent receipts (R22). Do not use
> this file for that.
>
> Delete this file if the feature's extends drop nothing.

<!-- One bullet per authorised drop:

- `<exact canonical line>` — <reason; which consumer is affected>
-->
