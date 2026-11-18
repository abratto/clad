#!/usr/bin/env python3
"""
verify_data_model.py — Stage gate: CSDP structural validation for data model files.

Why this exists:
  Conceptual data models follow a rigid 7-step CSDP structure with 20 required
  sub-sections. An LLM can omit steps, leave constraint sections empty, or
  accidentally introduce storage primitives (VARCHAR, FOREIGN KEY, etc.) into
  what should be a profile-neutral model. This script checks all structural
  requirements deterministically, leaving only the ORM modelling decisions
  to human judgment.

Checks:
  1. All 7 CSDP step headings present (## Step 1 through ## Step 7)
  2. All sub-section headings present (### Familiar examples, ### Object types, etc.)
  3. Constraint sub-sections have content or "None" marker
  4. No storage-leakage patterns (DDL statements, SQL constructs, engine names)
  5. One file per concept spec
  6. No cross-concept entity type references (entity type names don't
     reference other concept namespaces)

Usage:
  python3 verify_data_model.py \
    --data-dir <data-model-output/> \
    --concept-dir <concept-output/>
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_runner as cr  # noqa: E402
import artifact_parsers as ap  # noqa: E402
import generate_data_model as gdm  # noqa: E402


# All required sub-section headings across the 7 CSDP steps
REQUIRED_SUBSECTIONS = [
    "Familiar examples",
    "Elementary facts",
    "Step 1 quality checks",
    "Object types",
    "Fact types",
    "Population check",
    "Entity-type combination check",
    "Arithmetic derivations",
    "Uniqueness constraints",
    "Arity checks",
    "Mandatory role constraints",
    "Logical derivations",
    "Value constraints",
    "Set comparison constraints",
    "Subtype constraints",
    "Other constraints",
    "Final checks",
]

# Sub-sections that are "constraint sub-sections" — must have content or "None"
CONSTRAINT_SUBSECTIONS = {
    "Entity-type combination check",
    "Arithmetic derivations",
    "Uniqueness constraints",
    "Arity checks",
    "Mandatory role constraints",
    "Logical derivations",
    "Value constraints",
    "Set comparison constraints",
    "Subtype constraints",
    "Other constraints",
}

# A stateless concept's data model says so explicitly (generator wording).
STATELESS_MARKER = re.compile(r"is stateless", re.IGNORECASE)

# Storage-leakage patterns: these indicate profile-specific implementation
# detail leaking into a conceptual model. Each is a (regex, context_note) pair.
STORAGE_LEAK_PATTERNS = [
    # DDL/SQL construct usage (not mentioning them as concepts to avoid)
    (r"\bCREATE\s+TABLE\b", "SQL DDL statement"),
    (r"\bALTER\s+TABLE\b", "SQL DDL statement"),
    (r"\bCREATE\s+INDEX\b", "SQL DDL statement"),
    (r"`[A-Z]+`\s+NOT\s+NULL", "SQL column constraint"),
    (r"REFERENCES\s+\w+\s*\(", "SQL foreign key definition"),
    # Storage engine specifics
    (r"\bPostgreSQL\b", "database engine name"),
    (r"\bMySQL\b", "database engine name"),
    (r"\bMongoDB\b", "database engine name"),
    (r"\bTDB2?\b", "storage engine name"),
    # Profile-specific annotations and frameworks
    (r"@(Entity|Table|Column|Index)", "JPA/persistence annotation"),
    # RDF/SPARQL as storage detail (not as conceptual reference)
    (r"SPARQL\s+(query|update|construct|ask|select)", "SPARQL storage operation"),
]


def _snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _machine_multi(relation):
    value = relation.value_type.strip()
    annotation = (relation.multiplicity or "").lower()
    return ((value.startswith("{") and value.endswith("}"))
            or "zero or more" in annotation
            or re.search(r"\bmany\b", annotation) is not None)


def _resolve_machine_entity(name, machine, subtype_of):
    """Resolve a type name to a same-concept entity, or None for a value type."""
    if name in machine.object_types:
        return name
    entities = {entity for entity, scheme in machine.object_types.items()
                if scheme == name}
    if len(entities) == 1:
        return next(iter(entities))
    roots = [entity for entity in entities if entity not in subtype_of]
    return roots[0] if len(roots) == 1 else None


def check_machine_semantics(machine):
    """Ambiguity/cycle checks the textual grammar cannot express.

    Deterministic derivation is only safe when every name maps to exactly one
    column/table and the subtype graph is acyclic with known mappings.
    """
    failures = []
    field_names = {}
    for fact in machine.facts:
        folded = _snake(fact.field)
        if folded in field_names:
            failures.append(
                f"machine model facts '{field_names[folded]}' and "
                f"'{fact.field}' both map to column '{folded}'")
        else:
            field_names[folded] = fact.field
        if re.search(r"\bderived\b", fact.multiplicity or "", re.IGNORECASE):
            failures.append(
                f"fact '{fact.field}' is marked derived; derived facts are "
                f"outside CLAD's Rmap supported subset — derive them at "
                f"concept-read time, not as a stored fact")

    type_names = {}
    for object_type in machine.object_types:
        folded = _snake(object_type)
        if folded in type_names:
            failures.append(
                f"object types '{type_names[folded]}' and "
                f"'{object_type}' both map to table prefix '{folded}'")
        else:
            type_names[folded] = object_type

    supertype_of = {}
    for subtype, supertype, mapping in machine.subtypes:
        if mapping not in {"absorb", "separate", "partition"}:
            failures.append(
                f"subtype '{subtype}' has unknown mapping '{mapping}' "
                f"(expected absorb|separate|partition)")
        supertype_of[subtype] = supertype

    for start in supertype_of:
        seen = []
        current = start
        while current in supertype_of:
            if current in seen:
                cycle = " -> ".join(seen + [current])
                failures.append(f"subtype cycle: {cycle}")
                break
            seen.append(current)
            current = supertype_of[current]

    subtype_of = {subtype: mapping
                  for subtype, _supertype, mapping in machine.subtypes}
    discriminator_subs = {sub for sub, _pred, _value in machine.discriminators}
    by_supertype = {}
    for subtype, supertype, mapping in machine.subtypes:
        by_supertype.setdefault(supertype, set()).add(mapping)
    for supertype, mappings in by_supertype.items():
        if "absorb" in mappings and "partition" in mappings:
            failures.append(
                f"supertype '{supertype}' mixes absorb and partition "
                f"subtypes; partition drops the table absorption needs")
        if "partition" in mappings and "separate" in mappings:
            failures.append(
                f"supertype '{supertype}' mixes partition and separate "
                f"subtypes; partition drops the supertype table a separate "
                f"subtype needs")
        if "partition" in mappings and subtype_of.get(supertype) == "absorb":
            failures.append(
                f"partitioned supertype '{supertype}' is itself absorbed; "
                f"an absorbed type has no table to partition")

    for subtype, _supertype, mapping in machine.subtypes:
        if mapping != "absorb":
            continue
        owned = [fact for fact in machine.facts
                 if not fact.subject_type.strip().startswith("(")
                 and fact.subject_type.strip() == subtype]
        mandatory = [fact for fact in owned
                     if "mandatory" in (fact.multiplicity or "").lower()
                     and not _machine_multi(fact)]
        if not mandatory and subtype not in discriminator_subs:
            failures.append(
                f"absorbed subtype '{subtype}' has no mandatory simple fact "
                f"and no discriminator; membership is not inferable — use "
                f"mapping: separate, add a mandatory fact, or add a "
                f"discriminator")
        if any("default" in (fact.multiplicity or "").lower()
               for fact in owned):
            failures.append(
                f"absorbed subtype '{subtype}' has a fact with a default; a "
                f"default would make non-members look like members")
        for fact in owned:
            if _machine_multi(fact):
                failures.append(
                    f"absorbed subtype '{subtype}' has a multi-valued fact "
                    f"'{fact.field}'; conditional cardinality cannot be "
                    f"expressed — use mapping: separate or partition")

    scheme_to_entities = {}
    for entity, scheme in machine.object_types.items():
        scheme_to_entities.setdefault(scheme, set()).add(entity)
    for scheme, entities in scheme_to_entities.items():
        if scheme in machine.object_types or len(entities) <= 1:
            continue
        roots = [entity for entity in entities if entity not in subtype_of]
        if len(roots) != 1:
            failures.append(
                f"reference scheme '{scheme}' identifies multiple object "
                f"types ({', '.join(sorted(entities))}); an entity reference "
                f"through it is ambiguous")

    partition_supers = {
        supertype for _subtype, supertype, mapping in machine.subtypes
        if mapping == "partition"}
    for fact in machine.facts:
        if fact.subject_type.strip().startswith("("):
            continue
        value = fact.value_type.strip()
        if value.startswith("{"):
            continue
        if value in machine.object_types:
            target = value
        elif value in scheme_to_entities:
            entities = scheme_to_entities[value]
            roots = [entity for entity in entities
                     if entity not in subtype_of]
            target = (next(iter(entities)) if len(entities) == 1
                      else roots[0] if len(roots) == 1 else None)
        else:
            target = None
        if target in partition_supers:
            failures.append(
                f"fact '{fact.field}' references partitioned supertype "
                f"'{target}', which has no single table; reference a member "
                f"instead")

    facts_by_field = {fact.field: fact for fact in machine.facts}

    for fact in machine.facts:
        subject_mandatory, value_mandatory = ap.role_flags(fact.multiplicity)
        if value_mandatory is None:
            continue
        target = _resolve_machine_entity(
            fact.value_type.strip(), machine, subtype_of)
        if target is None:
            failures.append(
                f"fact '{fact.field}' states value-role participation but "
                f"'{fact.value_type.strip()}' is not an object type")
            continue
        if (fact.unique and value_mandatory is True
                and subject_mandatory is False):
            failures.append(
                f"1:1 fact '{fact.field}' is oriented on the optional role; "
                f"rewrite it with the mandatory role as the subject so the "
                f"column is grouped on the mandatory side")

    for constraint in machine.unique_constraints:
        subjects = set()
        for predicate in constraint.predicates:
            fact = facts_by_field.get(predicate)
            if fact is None:
                failures.append(
                    f"unique constraint names unknown fact '{predicate}'")
                continue
            if fact.subject_type.strip().startswith("(") or _machine_multi(fact):
                failures.append(
                    f"unique constraint predicate '{predicate}' must be a "
                    f"simple single-valued fact")
                continue
            subjects.add(fact.subject_type.strip())
        if len(subjects) > 1:
            failures.append(
                f"unique constraint ({', '.join(constraint.predicates)}) spans "
                f"multiple subject types/tables; only same-table uniqueness is "
                f"supported")
        if constraint.while_absent:
            fact = facts_by_field.get(constraint.while_absent)
            if fact is None:
                failures.append(
                    f"unique constraint filter names unknown fact "
                    f"'{constraint.while_absent}'")
            elif (fact.subject_type.strip().startswith("(")
                  or _machine_multi(fact)):
                failures.append(
                    f"unique constraint filter '{constraint.while_absent}' "
                    f"must be a simple single-valued fact")
            elif fact.subject_type.strip() not in subjects:
                failures.append(
                    f"unique constraint filter '{constraint.while_absent}' "
                    f"is on a different table from the constrained facts")

    for group in machine.disjoint:
        if len(group) < 2:
            failures.append(
                f"disjoint constraint needs at least two subtypes: "
                f"({', '.join(group)})")
        supers = {supertype_of.get(subtype) for subtype in group}
        if None in supers or len(supers) != 1:
            failures.append(
                f"disjoint subtypes ({', '.join(group)}) must share one "
                f"declared supertype")

    for supertype in machine.exhaustive:
        children = [subtype for subtype, parent in supertype_of.items()
                    if parent == supertype]
        if not children:
            failures.append(
                f"exhaustive supertype '{supertype}' has no declared subtypes")

    for subtype, predicate, value in machine.discriminators:
        if subtype_of.get(subtype) != "absorb":
            failures.append(
                f"discriminator on '{subtype}' requires mapping: absorb")
            continue
        fact = facts_by_field.get(predicate)
        if fact is None:
            failures.append(
                f"discriminator on '{subtype}' names unknown fact '{predicate}'")
            continue
        if fact.subject_type.strip().startswith("(") or _machine_multi(fact):
            failures.append(
                f"discriminator fact '{predicate}' must be simple and "
                f"single-valued")
        if fact.subject_type.strip() != supertype_of.get(subtype):
            failures.append(
                f"discriminator fact '{predicate}' must be a fact on the "
                f"direct supertype '{supertype_of.get(subtype)}'")
        if ap.role_flags(fact.multiplicity)[0] is not True:
            failures.append(
                f"discriminator fact '{predicate}' must be mandatory")
        for other_sub, other_predicate, other_value in machine.discriminators:
            if (other_sub != subtype and other_predicate == predicate
                    and other_value == value):
                failures.append(
                    f"subtypes '{subtype}' and '{other_sub}' share "
                    f"discriminator value '{value}' on '{predicate}'")

    declared = set(machine.object_types) | set(machine.independent)
    declared |= {fact.subject_type for fact in machine.facts
                 if not fact.subject_type.startswith("(")}
    declared |= {fact.value_type for fact in machine.facts}
    for subtype, supertype, _mapping in machine.subtypes:
        if supertype not in declared:
            failures.append(
                f"subtype '{subtype}' names undeclared supertype '{supertype}'")
    return failures


def _annotation_tokens(relation):
    raw = (relation.multiplicity or "").lower()
    tokens = {token.strip() for token in raw.split(",") if token.strip()}
    if relation.unique:
        tokens.add("unique")
    return tuple(sorted(tokens))


def _machine_signature(machine):
    facts = sorted(
        (fact.field, fact.subject_type, fact.value_type,
         _annotation_tokens(fact))
        for fact in machine.facts)
    unique = sorted(
        (constraint.predicates, constraint.while_absent or "")
        for constraint in machine.unique_constraints)
    return (facts, sorted(machine.subtypes), sorted(machine.independent),
            unique, sorted(machine.disjoint), sorted(machine.exhaustive),
            sorted(machine.discriminators))


def _concept_path(concept_name, concept_dirs):
    for directory in concept_dirs:
        candidate = os.path.join(directory, f"{concept_name}.concept.md")
        if os.path.isfile(candidate):
            return candidate
    return None


def check_machine_model_fidelity(path, concept_dirs):
    """The machine block must remain a faithful transcription of `## State`.

    `generate_data_model.py` builds the block mechanically. If a human edits
    one side without regenerating, the schema silently diverges from the
    approved concept state. Compare the semantic fact signatures instead of
    raw bytes so annotation order is not significant.
    """
    name = os.path.basename(path).replace(".data-model.md", "")
    concept_path = _concept_path(name, concept_dirs)
    if concept_path is None:
        return []
    with open(path, encoding="utf-8") as handle:
        actual_text = handle.read()
    actual = ap.parse_machine_model(actual_text)
    if not actual.present:
        return []
    concept = ap.parse_concept(concept_path)
    # The generator only lowers `field: Subject -> Value` relations. A
    # legitimate map/collection state form has no machine fact, so fidelity
    # would be a false failure there.
    if not any("->" in line for line in concept.state_lines):
        return []
    expected = ap.parse_machine_model(gdm.render(concept))
    actual_sig = _machine_signature(actual)
    expected_sig = _machine_signature(expected)
    if actual_sig == expected_sig:
        return []
    return [
        "machine model diverges from the concept `## State` — regenerate "
        "with generate_data_model.py and resolve only the judgment TODOs "
        f"(expected facts {expected_sig[0]}, got {actual_sig[0]})"
    ]


def check_data_model(path, concept_dirs=None):
    """Validate a single data model file. Returns list of failure messages."""
    failures = []
    with open(path) as f:
        content = f.read()

    lines = content.split("\n")

    # Check 1: All 7 CSDP step headings
    for i in range(1, 8):
        if f"## Step {i}" not in content:
            failures.append(f"missing ## Step {i} heading")

    # Check 2: All sub-section headings present
    found_subsections = set()
    for line in lines:
        m = re.match(r"^###\s+(.+)$", line.strip())
        if m:
            found_subsections.add(m.group(1).strip())

    for sub in REQUIRED_SUBSECTIONS:
        if sub not in found_subsections:
            failures.append(f"missing ### {sub}")

    # Check 3: Constraint sub-sections have content or "None"
    current_step = None
    current_subsection = None
    subsection_content = []

    for line in lines:
        m_step = re.match(r"^## Step \d", line.strip())
        if m_step:
            current_step = line.strip()
            current_subsection = None
            continue
        m_sub = re.match(r"^###\s+(.+)$", line.strip())
        if m_sub:
            # Check previous subsection
            if current_subsection and current_subsection in CONSTRAINT_SUBSECTIONS:
                text = " ".join(subsection_content).strip()
                if not text or text == "-":
                    failures.append(f"section '{current_subsection}' "
                                    f"in {current_step} is empty")
            current_subsection = m_sub.group(1).strip()
            subsection_content = []
            continue
        if current_subsection:
            subsection_content.append(line.strip())

    # Check last subsection
    if current_subsection and current_subsection in CONSTRAINT_SUBSECTIONS:
        text = " ".join(subsection_content).strip()
        if not text or text == "-":
            failures.append(f"section '{current_subsection}' "
                            f"in {current_step} is empty")

    # Check 4: No storage-primitive leakage patterns
    for i, line in enumerate(lines, 1):
        for pattern, note in STORAGE_LEAK_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                failures.append(f"line {i}: {note} ('{pattern}')")

    # Check 5: The CSDP-aligned machine model block required by Rmap.
    machine = ap.parse_machine_model(content)
    stateless = any(STATELESS_MARKER.search(line) for line in lines)
    if not stateless and not machine.present:
        failures.append(
            "missing `## Conceptual model` block (Rmap input; "
            "`## Machine model` is accepted as the legacy alias)")
    else:
        failures.extend(machine.errors)
        failures.extend(check_machine_semantics(machine))
        # Every fact subject must be a declared object type, an introduced
        # value type, or a compound of declared object types — catch a block
        # that names a type no Step declared.
        declared = set(machine.object_types)
        value_types = {f.value_type for f in machine.facts}
        for f in machine.facts:
            subject = f.subject_type.strip()
            parts = ([p.strip() for p in subject.strip("()").split(",")]
                     if subject.startswith("(") else [subject])
            for p in parts:
                if not p:
                    continue
                if p in declared or p in value_types or p in machine.independent:
                    continue
                failures.append(
                    f"machine model references undeclared type '{p}' "
                    f"in fact '{f.field}'")

    if concept_dirs:
        failures.extend(check_machine_model_fidelity(path, concept_dirs))
    return failures


def check_cross_concept_refs(data_dir, concept_dirs):
    """Check no entity/value types from one concept appear as entity types
    in another concept's data model.

    `concept_dirs` is a list of concept-spec dirs; they are merged with earlier
    dirs shadowing later ones by concept name."""
    failures = []

    # Build set of concept names across every concept source
    concept_names = set(ap.concept_spec_paths(concept_dirs))

    # For each data model file, extract entity type names and check they
    # don't belong to another concept
    if not os.path.isdir(data_dir):
        return failures

    for fname in os.listdir(data_dir):
        if not fname.endswith(".data-model.md"):
            continue
        own_concept = fname.replace(".data-model.md", "")
        path = os.path.join(data_dir, fname)
        with open(path) as f:
            content = f.read()

        # Find Entity and Value type declarations under Object types
        in_object_types = False
        for line in content.split("\n"):
            if "### Object types" in line:
                in_object_types = True
                continue
            if in_object_types:
                if line.startswith("###") or line.startswith("##"):
                    in_object_types = False
                    continue
                # Match: `- Entity: \`SomeType\`` or `- Value: \`SomeType\``
                m = re.match(r"^-\s+(Entity|Value):\s+`(\w+)`", line.strip())
                if m:
                    type_name = m.group(2)
                    # Check if this type name matches another concept name
                    matched_concepts = [
                        c for c in concept_names
                        if c != own_concept and type_name == c
                    ]
                    if matched_concepts:
                        failures.append(
                            f"{fname}: entity type '{type_name}' matches "
                            f"concept name '{matched_concepts[0]}' — "
                            f"possible foreign key/schema coupling")

    return failures


def main(argv=None) -> int:
    def configure(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--data-dir", required=True,
                            help="Path to 03b_data-model/output/")
        parser.add_argument("--concept-dir", required=True, action="append",
                            help="Concept-spec dir for entity-name cross-ref; "
                                 "repeatable. Earlier dirs shadow later ones.")

    def body(args: argparse.Namespace):
        data_dir = args.data_dir
        concept_dirs = args.concept_dir

        if not os.path.isdir(data_dir):
            print(f"FAIL  data model directory not found: {data_dir}")
            return 1

        data_files = sorted([
            f for f in os.listdir(data_dir) if f.endswith(".data-model.md")
        ])

        if not data_files:
            print("FAIL  no .data-model.md files found")
            return 1

        # Check 5: One file per concept (at minimum, one exists)
        print(f"INFO  {len(data_files)} data model files: {data_files}")

        total_failures = 0

        # Structural checks per file
        for fname in data_files:
            path = os.path.join(data_dir, fname)
            file_failures = check_data_model(path, concept_dirs)
            for msg in file_failures:
                print(f"FAIL  {fname}: {msg}")
                total_failures += 1

        # Cross-concept entity reference check
        cross_failures = check_cross_concept_refs(data_dir, concept_dirs)
        for msg in cross_failures:
            print(f"FAIL  {msg}")
            total_failures += 1

        if total_failures == 0:
            print(f"PASS  {len(data_files)} data models pass all CSDP structure checks")
            return 0
        return 1

    return cr.run_report("Validate conceptual data model CSDP structure", body, argv, configure)


if __name__ == "__main__":
    sys.exit(main())
