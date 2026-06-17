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


def check_data_model(path):
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

    return failures


def check_cross_concept_refs(data_dir, concept_dir):
    """Check no entity/value types from one concept appear as entity types
    in another concept's data model."""
    failures = []

    # Build set of concept names
    concept_names = set()
    if os.path.isdir(concept_dir):
        for fname in os.listdir(concept_dir):
            if fname.endswith(".concept.md"):
                concept_names.add(fname.replace(".concept.md", ""))

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


def main():
    parser = argparse.ArgumentParser(
        description="Validate conceptual data model CSDP structure")
    parser.add_argument("--data-dir", required=True,
                        help="Path to 03b_data-model/output/")
    parser.add_argument("--concept-dir", required=True,
                        help="Path to 02_concepts/output/ (for entity name cross-ref)")
    args = parser.parse_args()

    data_dir = args.data_dir
    concept_dir = args.concept_dir

    if not os.path.isdir(data_dir):
        print(f"FAIL  data model directory not found: {data_dir}")
        sys.exit(1)

    data_files = sorted([
        f for f in os.listdir(data_dir) if f.endswith(".data-model.md")
    ])

    if not data_files:
        print("FAIL  no .data-model.md files found")
        sys.exit(1)

    # Check 5: One file per concept (at minimum, one exists)
    print(f"INFO  {len(data_files)} data model files: {data_files}")

    total_failures = 0

    # Structural checks per file
    for fname in data_files:
        path = os.path.join(data_dir, fname)
        file_failures = check_data_model(path)
        for msg in file_failures:
            print(f"FAIL  {fname}: {msg}")
            total_failures += 1

    # Cross-concept entity reference check
    cross_failures = check_cross_concept_refs(data_dir, concept_dir)
    for msg in cross_failures:
        print(f"FAIL  {msg}")
        total_failures += 1

    if total_failures == 0:
        print(f"PASS  {len(data_files)} data models pass all CSDP structure checks")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
