#!/usr/bin/env python3
"""Rmap derivation and SQL rendering — the single authoritative implementation.

Rmap (Halpin's relational mapping) turns a Stage 03b conceptual model into a
set of relational tables. This module is the one implementation used by the
CLAD workflow; Java profiles consume the generated SQL/descriptor rather than
re-deriving the schema.

The input is the `<Name>.data-model.md` document, specifically its
`## Machine model` (or `## Conceptual model`) fenced block. The output is an
in-memory `RmapModel`, a deterministic SQL migration, and an optional runtime
descriptor.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

import artifact_parsers as ap
import clad_stages as cs


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Column:
    predicate: str
    column: str
    sql_type: str = "TEXT"
    mandatory: bool = False
    unique: bool = False
    default: Optional[str] = None
    value_constraint: Optional[str] = None
    unique_while_absent: Optional[str] = None


@dataclass(frozen=True)
class Check:
    name: str
    expression: str


@dataclass
class RelationSchema:
    concept: str
    table: str
    object_type: str
    columns: List[Column]
    primary_key: List[str]
    foreign_keys: List[str] = field(default_factory=list)
    checks: List[Check] = field(default_factory=list)
    derived: bool = False

    @property
    def qualified_name(self) -> str:
        return f"{self.concept}.{self.table}"

    @property
    def id_column(self) -> str:
        return self.primary_key[0]

    def column_for(self, predicate: str) -> Optional[Column]:
        for column in self.columns:
            if column.predicate == predicate:
                return column
        return None

    def identity_columns(self) -> List[Column]:
        key_names = (self.primary_key
                     if "+" in self.object_type or len(self.primary_key) <= 1
                     else self.primary_key[:-1])
        names = set(key_names)
        return [c for c in self.columns if c.column in names]

    def data_columns(self) -> List[Column]:
        identity = set(self.identity_columns())
        return [c for c in self.columns if c not in identity]


@dataclass
class RmapModel:
    concept: str
    tables: List[RelationSchema]

    def object_types(self) -> List[str]:
        return [table.object_type for table in self.tables]

    def table_for(self, object_type: str) -> Optional[RelationSchema]:
        for table in self.tables:
            if table.object_type == object_type:
                return table
        return None

    def table_for_member(self, member: str) -> Optional[RelationSchema]:
        name = member_table_name(self.concept, member)
        for table in self.tables:
            if table.table == name:
                return table
        return None

    def table_for_predicate(self, predicate: str) -> Optional[RelationSchema]:
        for table in self.tables:
            if table.column_for(predicate) is not None:
                return table
        return None


# --------------------------------------------------------------------------
# Internal fact shape
# --------------------------------------------------------------------------

ABSORB = "absorb"
SEPARATE = "separate"
PARTITION = "partition"


@dataclass
class FactType:
    field: str
    subject_types: List[str]
    value_type: str
    multi_valued: bool
    mandatory: bool
    unique: bool
    default: Optional[str]
    value_constraint: Optional[str]
    unique_while_absent: Optional[str]

    @property
    def compound(self) -> bool:
        return len(self.subject_types) > 1


@dataclass
class ParsedState:
    facts: List[FactType]
    subtypes: List[tuple]
    independent: List[str]


def _annotation(relation: ap.StateRelation) -> str:
    return (relation.multiplicity or "").strip()


def _is_multi(relation: ap.StateRelation) -> bool:
    value = relation.value_type.strip()
    annotation = _annotation(relation).lower()
    return (value.startswith("{") and value.endswith("}")
            or "zero or more" in annotation
            or re.search(r"\bmany\b", annotation) is not None)


def _unique_parts(annotation: str) -> tuple[bool, Optional[str]]:
    filtered = re.search(r"\bunique\s+while\s+(\w+)\s+(?:absent|missing)",
                         annotation, re.IGNORECASE)
    if filtered:
        plain = re.search(r"\bunique(?!\s+while\b)", annotation, re.IGNORECASE)
        return bool(plain), filtered.group(1)
    return "unique" in annotation.lower(), None


def _fact_type(relation: ap.StateRelation) -> FactType:
    subject = relation.subject_type.strip()
    if subject.startswith("(") and subject.endswith(")"):
        subjects = [part.strip() for part in subject[1:-1].split(",")
                    if part.strip()]
    else:
        subjects = [subject]
    value = relation.value_type.strip()
    if value.startswith("{") and value.endswith("}"):
        value = value[1:-1].strip()
    annotation = _annotation(relation)
    unique, unique_while = _unique_parts(annotation)
    default = re.search(r"\bdefault\s+([A-Za-z0-9_.'-]+)", annotation)
    enum = re.search(r"\bin\s*\{([^}]*)\}", annotation)
    return FactType(
        field=relation.field,
        subject_types=subjects,
        value_type=value,
        multi_valued=_is_multi(relation),
        mandatory="mandatory" in annotation.lower(),
        unique=unique,
        default=default.group(1) if default else None,
        value_constraint=enum.group(1).strip() if enum else None,
        unique_while_absent=unique_while,
    )


def _parsed_state(machine: ap.MachineModel) -> ParsedState:
    facts = [_fact_type(relation) for relation in machine.facts]
    subtypes = [(sub, sup, (mapping or SEPARATE).lower())
                for sub, sup, mapping in machine.subtypes]
    return ParsedState(facts, subtypes, list(machine.independent))


# --------------------------------------------------------------------------
# Naming helpers (must match the Java implementation byte-for-byte)
# --------------------------------------------------------------------------

def snake(value: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).lower()


def snake_name(value: str) -> str:
    return snake(value.replace("+", "_and_"))


def scheme_column(scheme: str) -> str:
    if scheme.endswith(".id"):
        return snake(scheme[:-len(".id")]) + "_id"
    return snake(scheme)


def member_table_name(concept: str, member: str) -> str:
    return snake(concept) + "__" + snake_name(member)


def _sql_type(value_type: str) -> str:
    if value_type in ("Int", "Integer"):
        return "INTEGER"
    if value_type in ("Timestamp", "Instant"):
        return "TIMESTAMP"
    if value_type == "Boolean":
        return "BOOLEAN"
    return "TEXT"


# --------------------------------------------------------------------------
# Realization
# --------------------------------------------------------------------------

def _root_scheme(object_type: str, supertype_of: Dict[str, str],
                 reference_schemes: Dict[str, str]) -> str:
    current = object_type
    seen = set()
    while current in supertype_of and current not in seen:
        seen.add(current)
        current = supertype_of[current]
    return reference_schemes.get(current, current)


def _check_expression(column: str, enum_body: str) -> str:
    quoted = []
    for raw in enum_body.split(","):
        token = raw.strip()
        if not token:
            continue
        if ".." in token:
            low, high = token.split("..", 1)
            return f"{column} BETWEEN {low.strip()} AND {high.strip()}"
        quoted.append("'" + token + "'")
    return f"{column} IN ({', '.join(quoted)})"


def _check_name(object_type: str, field_name: str) -> str:
    return "ck_" + snake_name(object_type) + "_" + snake(field_name)


def _add_column(columns: List[Column], predicate: str, column: str,
                sql_type: str, mandatory: bool, unique: bool,
                default: Optional[str], value_constraint: Optional[str] = None,
                unique_while_absent: Optional[str] = None) -> None:
    if any(existing.column == column for existing in columns):
        return
    columns.append(Column(predicate, column, sql_type, mandatory, unique,
                          default, value_constraint, unique_while_absent))


def _realize_table(concept: str, object_type: str, group: List[FactType],
                   is_compidot: bool, table: str,
                   subtype_of: Dict[str, str], supertype_of: Dict[str, str],
                   table_names: Dict[str, str],
                   reference_schemes: Dict[str, str]) -> RelationSchema:
    columns: List[Column] = []
    checks: List[Check] = []
    foreign_keys: List[str] = []
    is_subtype = (object_type in subtype_of
                  and subtype_of[object_type] != ABSORB)

    for fact in group:
        if fact.compound:
            for subject in fact.subject_types:
                column = scheme_column(_root_scheme(
                    subject, supertype_of, reference_schemes))
                _add_column(columns, column, column, "TEXT", True, False, None)
            _add_column(columns, fact.field, snake(fact.field),
                        _sql_type(fact.value_type), fact.mandatory,
                        fact.unique, fact.default, None,
                        fact.unique_while_absent)
            if fact.value_constraint is not None:
                checks.append(Check(
                    _check_name(object_type, fact.field),
                    _check_expression(snake(fact.field), fact.value_constraint)))
            continue
        if fact.multi_valued:
            continue
        _add_column(columns, fact.field, snake(fact.field),
                    _sql_type(fact.value_type), fact.mandatory,
                    fact.unique, fact.default, None,
                    fact.unique_while_absent)
        if fact.value_constraint is not None:
            checks.append(Check(
                _check_name(object_type, fact.field),
                _check_expression(snake(fact.field), fact.value_constraint)))

    if is_compidot:
        primary_key = [scheme_column(_root_scheme(
            subject, supertype_of, reference_schemes))
            for subject in object_type.split("+")]
    elif is_subtype:
        supertype = supertype_of[object_type]
        supertable = table_names.get(supertype)
        id_column = scheme_column(_root_scheme(
            object_type, supertype_of, reference_schemes))
        if supertable is not None:
            foreign_keys.append(
                f"{id_column} -> {supertable}({id_column})")
        object_type = supertype
        primary_key = [id_column]
        if not any(column.column == id_column for column in columns):
            columns.insert(0, Column(id_column, id_column, "TEXT", True,
                                     False, None))
    else:
        id_column = scheme_column(
            reference_schemes.get(object_type, object_type))
        if not any(column.column == id_column for column in columns):
            columns.insert(0, Column(id_column, id_column, "TEXT", True,
                                     False, None))
        primary_key = [id_column]

    return RelationSchema(concept, table, object_type, columns, primary_key,
                          foreign_keys, checks, False)


def _child_tables(concept: str, facts: List[FactType],
                  table_names: Dict[str, str], tables: List[RelationSchema],
                  reference_schemes: Dict[str, str],
                  subtype_of: Dict[str, str],
                  supertype_of: Dict[str, str]) -> List[RelationSchema]:
    result: List[RelationSchema] = []
    for fact in facts:
        if not fact.multi_valued:
            continue
        subject = fact.subject_types[0]
        if subject in subtype_of:
            supertype = supertype_of[subject]
            subject_column = scheme_column(_root_scheme(
                subject, supertype_of, reference_schemes))
            absorbed = subtype_of[subject] == ABSORB
            parent_table = table_names.get(supertype if absorbed else subject)
        else:
            subject_column = scheme_column(
                reference_schemes.get(subject, subject))
            parent_table = table_names.get(subject)

        columns = [
            Column(subject_column, subject_column, "TEXT", True, False, None),
            Column(fact.field, snake(fact.field), _sql_type(fact.value_type),
                   True, False, None),
        ]
        primary_key = [subject_column, snake(fact.field)]
        parent = next((t for t in tables if t.table == parent_table), None)
        parent_has_data = parent is not None and bool(parent.data_columns())
        result.append(RelationSchema(
            concept, snake(concept) + "__" + snake(fact.field), subject,
            columns, primary_key,
            [f"{subject_column} -> {parent_table}({subject_column})"]
            if parent_has_data else [],
            [], False))
    return result


def _independent_table(concept: str, object_type: str, table: str,
                       reference_schemes: Dict[str, str]) -> RelationSchema:
    column = scheme_column(reference_schemes.get(object_type, object_type))
    return RelationSchema(
        concept, table, object_type,
        [Column(column, column, "TEXT", True, False, None)],
        [column], [], [], False)


def derive_model(concept: str, data_model_text: str,
                 source: Optional[str] = None) -> RmapModel:
    """Derive a concept's table set from its Stage 03b data-model text."""
    machine = ap.parse_machine_model(data_model_text)
    if not machine.present:
        raise ValueError(
            f"no `## Machine model` / `## Conceptual model` block in "
            f"{source or concept}")
    if machine.errors:
        raise ValueError("; ".join(machine.errors))
    parsed = _parsed_state(machine)
    return _realize(concept, parsed, machine.object_types)


def _realize(concept: str, parsed: ParsedState,
             reference_schemes: Dict[str, str]) -> RmapModel:
    facts = parsed.facts
    subtype_of = {sub: mapping for sub, _sup, mapping in parsed.subtypes}
    supertype_of = {sub: sup for sub, sup, _mapping in parsed.subtypes}

    by_object_type: Dict[str, List[FactType]] = {}
    compidots = set()
    for fact in facts:
        if fact.compound:
            key = "+".join(fact.subject_types)
            compidots.add(key)
            by_object_type.setdefault(key, []).append(fact)
            continue
        subject = fact.subject_types[0]
        if subtype_of.get(subject) == ABSORB:
            subject = supertype_of[subject]
        by_object_type.setdefault(subject, []).append(fact)

    # Absorption moves a subtype's facts onto the supertype's table.
    for subtype, supertype in list(supertype_of.items()):
        if subtype_of.get(subtype) != ABSORB:
            continue
        absorbed = by_object_type.pop(subtype, None)
        if absorbed is not None:
            by_object_type.setdefault(supertype, []).extend(absorbed)

    # Partition flattens the supertype's own facts into each member table.
    partition_members: Dict[str, List[str]] = {}
    for subtype, supertype in supertype_of.items():
        if subtype_of.get(subtype) == PARTITION:
            partition_members.setdefault(supertype, []).append(subtype)
    for supertype, members in partition_members.items():
        supertype_facts = by_object_type.get(supertype)
        if supertype_facts is None:
            continue
        direct = [f for f in supertype_facts
                  if not f.compound and f.subject_types[0] == supertype]
        for member in members:
            group = by_object_type.setdefault(member, [])
            for fact in direct:
                if fact not in group:
                    group.append(fact)
        by_object_type.pop(supertype, None)

    by_object_type = {key: value for key, value in by_object_type.items()
                       if value}
    # A type whose facts are all multi-valued has no functional role of its
    # own; its child tables already carry the subject column.
    by_object_type = {key: value for key, value in by_object_type.items()
                       if not all(fact.multi_valued for fact in value)}

    simple_tables = [key for key in by_object_type if key not in compidots]
    has_member_tables = any(
        mapping != ABSORB and subtype in by_object_type
        for subtype, mapping in subtype_of.items())
    single = (len(simple_tables) == 1
              and not parsed.independent
              and not has_member_tables)
    table_names: Dict[str, str] = {}
    for object_type in by_object_type:
        if object_type in compidots or not single:
            table_names[object_type] = (
                snake(concept) + "__" + snake_name(object_type))
        else:
            table_names[object_type] = snake(concept)

    tables: List[RelationSchema] = []
    for object_type, group in by_object_type.items():
        tables.append(_realize_table(
            concept, object_type, group, object_type in compidots,
            table_names[object_type], subtype_of, supertype_of, table_names,
            reference_schemes))
    tables.extend(_child_tables(
        concept, facts, table_names, tables, reference_schemes,
        subtype_of, supertype_of))
    for independent in parsed.independent:
        if independent in table_names:
            continue
        table = (snake(concept) if not by_object_type
                 else snake(concept) + "__" + snake_name(independent))
        tables.append(_independent_table(
            concept, independent, table, reference_schemes))
    return RmapModel(concept, tables)


# --------------------------------------------------------------------------
# SQL rendering (byte-for-byte compatible with the former Java renderer)
# --------------------------------------------------------------------------

_SQL_TYPE = {"INTEGER": "integer", "TIMESTAMP": "timestamp",
             "BOOLEAN": "boolean"}


def _quote(value: str) -> str:
    return '"' + value + '"'


def _fk_constraint(spec: str) -> str:
    arrow = spec.index("->")
    column = spec[:arrow].strip()
    reference = spec[arrow + 2:].strip()
    table = reference[:reference.index("(")].strip()
    target = reference[reference.index("(") + 1:reference.index(")")].strip()
    return (f"FOREIGN KEY ({_quote(column)}) REFERENCES "
            f"{_quote(table)} ({_quote(target)})")


def _filtered_index(table: str, column: Column) -> str:
    return ("CREATE UNIQUE INDEX IF NOT EXISTS "
            + _quote(f"{table}_{column.column}_open_idx")
            + " ON " + _quote(table)
            + " (" + _quote(column.column) + ")"
            + " WHERE " + _quote(snake(column.unique_while_absent or ""))
            + " IS NULL")


def _create_table(schema: RelationSchema) -> str:
    single_pk = len(schema.primary_key) == 1
    single_key = schema.primary_key[0] if single_pk else None
    parts: List[str] = []
    for column in schema.columns:
        part = _quote(column.column) + " " + _SQL_TYPE.get(
            column.sql_type, "varchar")
        if column.default is not None:
            part += " DEFAULT " + column.default
        if column.mandatory:
            part += " NOT NULL"
        if column.unique:
            part += " UNIQUE"
        if single_pk and column.column == single_key:
            part += " PRIMARY KEY"
        parts.append(part)
    if not single_pk:
        parts.append("PRIMARY KEY ("
                     + ", ".join(_quote(c) for c in schema.primary_key) + ")")
    for check in schema.checks:
        parts.append(f"CONSTRAINT {check.name} CHECK ({check.expression})")
    for foreign_key in schema.foreign_keys:
        parts.append(_fk_constraint(foreign_key))
    text = ("CREATE TABLE IF NOT EXISTS " + _quote(schema.table)
            + " (\n  " + ",\n  ".join(parts) + "\n)")
    for column in schema.columns:
        if column.unique_while_absent is not None:
            text += ";\n" + _filtered_index(schema.table, column)
    return text


def render_migration(app_label: str, models: Sequence[RmapModel]) -> str:
    text = (
        f"-- Base DDL for {app_label} concept state.\n"
        "--\n"
        "-- GENERATED by quality-gate/rmap.py from the Stage 03b\n"
        "-- conceptual data models via Halpin's R-map. Do NOT edit by hand:\n"
        "-- regenerate after a concept `## State` change (see RELATIONAL_LOWERING.md).\n"
        "--\n"
        "-- R-map realises typed, keyed, constrained tables: NOT NULL (mandatory),\n"
        "-- UNIQUE / PRIMARY KEY, CHECK (value constraints), FOREIGN KEY (intra-\n"
        "-- concept references only — no cross-concept FK, R2). A concept whose\n"
        "-- state ranges over several object types is a table set. TEXT is written\n"
        "-- as varchar here so jOOQ's DDLDatabase can introspect the schema.\n"
    )
    for model in models:
        for table in model.tables:
            text += "\n" + _create_table(table) + ";\n"
    return text


def render_review(concept: str, data_model_text: str) -> str:
    """Human review view generated from the same conceptual block as Rmap."""
    machine = ap.parse_machine_model(data_model_text)
    parsed = _parsed_state(machine)
    model = _realize(concept, parsed, machine.object_types)
    lines = [f"# {concept} — conceptual model review", ""]
    lines.append("## Object types")
    lines.append("")
    lines.append("| Type | Reference scheme |")
    lines.append("|---|---|")
    for object_type, scheme in machine.object_types.items():
        lines.append(f"| `{object_type}` | `{scheme}` |")
    lines.append("")
    lines.append("## Fact types")
    lines.append("")
    lines.append("| Predicate | Subject | Value | Multi | Mandatory | Unique | Default | Constraint |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for fact in parsed.facts:
        subject = ", ".join(fact.subject_types)
        annotations = []
        if fact.unique_while_absent:
            annotations.append(f"unique while {fact.unique_while_absent} absent")
        lines.append(
            f"| `{fact.field}` | `{subject}` | `{fact.value_type}` | "
            f"{'yes' if fact.multi_valued else 'no'} | "
            f"{'yes' if fact.mandatory else 'no'} | "
            f"{'yes' if fact.unique else 'no'} | "
            f"{fact.default or ''} | "
            f"{'; '.join(annotations) or (('in {' + fact.value_constraint + '}') if fact.value_constraint else '')} |")
    if parsed.subtypes:
        lines.append("")
        lines.append("## Subtypes")
        lines.append("")
        lines.append("| Subtype | Supertype | Mapping |")
        lines.append("|---|---|---|")
        for subtype, supertype, mapping in parsed.subtypes:
            lines.append(f"| `{subtype}` | `{supertype}` | `{mapping}` |")
    lines.append("")
    lines.append("## Relational realization")
    lines.append("")
    for table in model.tables:
        lines.append(f"### `{table.table}`")
        lines.append("")
        lines.append(f"- Object type: `{table.object_type}`")
        lines.append(f"- Primary key: {', '.join(f'`{c}`' for c in table.primary_key)}")
        lines.append("- Columns: " + ", ".join(
            f"`{c.column}` ({c.sql_type}{', NOT NULL' if c.mandatory else ''}"
            f"{', UNIQUE' if c.unique else ''})" for c in table.columns))
        if table.checks:
            lines.append("- Checks: " + "; ".join(
                f"`{check.name}` = {check.expression}" for check in table.checks))
        if table.foreign_keys:
            lines.append("- Foreign keys: " + ", ".join(
                f"`{fk}`" for fk in table.foreign_keys))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def model_descriptor(models: Sequence[RmapModel]) -> dict:
    """Internal runtime descriptor (not a reviewed interchange artifact)."""
    return {
        "models": [
            {
                "concept": model.concept,
                "tables": [
                    {
                        "concept": table.concept,
                        "table": table.table,
                        "objectType": table.object_type,
                        "primaryKey": list(table.primary_key),
                        "foreignKeys": list(table.foreign_keys),
                        "columns": [
                            {
                                "predicate": c.predicate,
                                "column": c.column,
                                "sqlType": c.sql_type,
                                "mandatory": c.mandatory,
                                "unique": c.unique,
                                "default": c.default,
                                "valueConstraint": c.value_constraint,
                                "uniqueWhileAbsent": c.unique_while_absent,
                            }
                            for c in table.columns
                        ],
                        "checks": [
                            {"name": c.name, "expression": c.expression}
                            for c in table.checks
                        ],
                        "ddl": _create_table(table),
                    }
                    for table in model.tables
                ],
            }
            for model in models
        ]
    }


def _project_sources(features_dir: str) -> tuple[str, List[tuple[str, str, str]]]:
    """All current conceptual models for the app.

    The canonical corpus is authoritative after promotion. A project with no
    corpus falls back to each feature's 03b model, first concept wins.
    """
    features_dir = os.path.abspath(features_dir)
    corpus = os.path.join(features_dir, "_system", "concepts")
    sources: List[tuple[str, str, str]] = []
    if os.path.isdir(corpus):
        for name in sorted(os.listdir(corpus)):
            if not name.endswith(".data-model.md"):
                continue
            path = os.path.join(corpus, name)
            sources.append((name[:-len(".data-model.md")], path,
                            open(path, encoding="utf-8").read()))
    if sources:
        return "app", sources

    seen = set()
    for feature in sorted(os.listdir(features_dir)):
        if not feature.startswith("UC-"):
            continue
        data_dir = os.path.join(features_dir, feature, "stages",
                                "03b_data-model", "output")
        if not os.path.isdir(data_dir):
            continue
        for name in sorted(os.listdir(data_dir)):
            if not name.endswith(".data-model.md"):
                continue
            concept = name[:-len(".data-model.md")]
            if concept in seen:
                continue
            seen.add(concept)
            path = os.path.join(data_dir, name)
            sources.append((concept, path, open(path, encoding="utf-8").read()))
    if not sources:
        raise SystemExit(
            f"FAIL  no conceptual models found under {features_dir} "
            f"(_system/concepts or UC-*/stages/03b_data-model/output)")
    return "app", sources


def _alter_sql(baseline: dict, current: dict, app_label: str) -> tuple[str, List[str]]:
    """Incremental DDL from a baseline descriptor to the current descriptor.

    Creates new tables and adds new columns/checks. Removals are never emitted
    automatically (destructive); they are reported for human review. A new
    mandatory column without a default is refused — it cannot be applied to
    existing rows safely.
    """
    warnings: List[str] = []
    baseline_tables = {
        table["table"]: table
        for model in baseline.get("models", [])
        for table in model.get("tables", [])
    }
    statements: List[str] = []
    for model in current.get("models", []):
        for table in model.get("tables", []):
            name = table["table"]
            old = baseline_tables.get(name)
            if old is None:
                statements.append(table["ddl"] + ";")
                continue
            old_columns = {column["column"]: column
                           for column in old.get("columns", [])}
            for column in table.get("columns", []):
                col = column["column"]
                if col in old_columns:
                    continue
                part = (_quote(col) + " "
                        + _SQL_TYPE.get(column.get("sqlType"), "varchar"))
                if column.get("default") is not None:
                    part += " DEFAULT " + column["default"]
                if column.get("mandatory"):
                    if column.get("default") is None:
                        raise SystemExit(
                            f"FAIL  cannot add mandatory column {name}.{col} "
                            f"without a default to an existing table")
                    part += " NOT NULL"
                if column.get("unique"):
                    part += " UNIQUE"
                if column.get("valueConstraint"):
                    part += f" CHECK ({column['valueConstraint']})"
                statements.append(
                    f"ALTER TABLE {_quote(name)} ADD COLUMN {part};")
            for column in old_columns:
                if column not in {c["column"] for c in table.get("columns", [])}:
                    warnings.append(
                        f"{name}.{column}: column exists in the baseline but "
                        f"not in the current model — not dropped automatically")
            old_checks = {check["name"] for check in old.get("checks", [])}
            for check in table.get("checks", []):
                if check["name"] in old_checks:
                    continue
                statements.append(
                    f"ALTER TABLE {_quote(name)} ADD CONSTRAINT "
                    f"{_quote(check['name'])} CHECK ({check['expression']});")
    for name in baseline_tables:
        if not any(table["table"] == name
                   for model in current.get("models", [])
                   for table in model.get("tables", [])):
            warnings.append(
                f"{name}: table exists in the baseline but not in the current "
                f"model — not dropped automatically")
    header = (
        f"-- Incremental DDL for {app_label} concept state.\n"
        "--\n"
        "-- GENERATED by quality-gate/rmap.py from a baseline descriptor and the\n"
        "-- current Stage 03b conceptual models. Do NOT edit by hand.\n"
        "-- Destructive changes (dropped tables/columns) are reported, never emitted.\n"
    )
    if not statements:
        return header + "-- no schema changes\n", warnings
    return header + "\n" + "\n".join(statements) + "\n", warnings


def _guarded_write(path: str, text: str, force: bool,
                   label: str = "applied migration") -> int:
    """Write a migration only when it is new/current, or --force is given."""
    if os.path.isfile(path) and not force:
        with open(path, encoding="utf-8") as handle:
            existing = handle.read()
        if existing == text:
            print(f"PASS  {path} is already current")
            return 0
        print(f"FAIL  {path} exists and differs — pass --force to overwrite "
              f"this {label} (or use --alter with a baseline)")
        return 1
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"WROTE {path}")
    return 0


def _repo_root_for(args) -> str:
    if args.features_dir:
        return os.path.dirname(os.path.abspath(args.features_dir))
    if args.feature:
        return os.path.dirname(os.path.dirname(os.path.abspath(args.feature)))
    return os.getcwd()


def _property(args, key: str) -> str:
    repo = _repo_root_for(args)
    value = ""
    props = os.path.join(repo, "clad.properties")
    if os.path.isfile(props):
        with open(props, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line.startswith(key + "="):
                    value = line.split("=", 1)[1].strip()
                    break
    if args.feature:
        override = os.path.join(os.path.abspath(args.feature), "_config",
                                key + ".md")
        if os.path.isfile(override):
            with open(override, encoding="utf-8") as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") \
                            and not stripped.startswith("<!--"):
                        value = stripped
                        break
    return value


def _baseline_candidates(args, name: str) -> List[str]:
    repo = _repo_root_for(args)
    candidates = [os.path.join(repo, "_generated", "rmap-baselines",
                               name + ".json")]
    if args.features_dir:
        candidates.append(os.path.join(os.path.abspath(args.features_dir),
                                       "_system", "rmap-baselines",
                                       name + ".json"))
    if args.feature:
        candidates.insert(0, os.path.join(os.path.abspath(args.feature),
                                          "_generated", "rmap-baselines",
                                          name + ".json"))
    return candidates


def _resolve_baseline(args) -> str:
    """Explicit path > `--baseline NAME_OR_PATH` > `rmap.baseline` config > default.

    `--baseline-descriptor` is a deprecated alias: `main` folds it into
    `args.baseline`, so this function sees a single value.
    """
    value = args.baseline
    if value and os.path.isfile(value):
        return value
    if not value:
        configured = _property(args, "rmap.baseline")
        if configured:
            repo = _repo_root_for(args)
            path = (configured if os.path.isabs(configured)
                    else os.path.join(repo, configured))
            if os.path.isfile(path):
                return path
            raise SystemExit(f"FAIL  configured rmap.baseline not found: {path}")
        value = "default"
    for path in _baseline_candidates(args, value):
        if os.path.isfile(path):
            return path
    searched = "\n  ".join(_baseline_candidates(args, value))
    raise SystemExit(
        f"FAIL  no baseline descriptor for `{value}`. Searched:\n  {searched}\n"
        f"Record one with --record-baseline {value} or set rmap.baseline.")


def _record_baseline_path(args, value: str) -> str:
    repo = _repo_root_for(args)
    if not value or value == "default":
        return os.path.join(repo, "_generated", "rmap-baselines", "default.json")
    if os.sep in value or value.endswith(".json"):
        return value if os.path.isabs(value) else os.path.join(repo, value)
    return os.path.join(repo, "_generated", "rmap-baselines", value + ".json")



# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _feature_sources(feature: str) -> tuple[str, List[tuple[str, str, str]]]:
    feature_root = os.path.abspath(feature)
    data_dir = cs.DATA_DIR(feature_root)
    if not os.path.isdir(data_dir):
        raise SystemExit(f"FAIL  no Stage 03b output directory: {data_dir}")
    wanted = set(cs.feature_model_concepts(feature_root))
    # Preserve the authored responsibility-map order (UserNaming, PasswordAuth,
    # Session), not alphabetical order. It is deterministic and keeps the
    # migration diff stable across a feature.
    order: List[str] = []
    resp_map = os.path.join(feature_root, "stages", "01a_responsibility-map",
                            "output", "responsibility-map.md")
    if os.path.isfile(resp_map):
        order = [name for name in ap.parse_responsibility_map(resp_map)
                 if name != "Web"]
    available = {name[:-len(".data-model.md")]
                 for name in os.listdir(data_dir)
                 if name.endswith(".data-model.md")}
    sequence = ([name for name in order if name in available]
                + sorted(available - set(order)))
    sources = []
    for concept in sequence:
        if wanted and concept not in wanted:
            continue
        path = os.path.join(data_dir, concept + ".data-model.md")
        sources.append((concept, path, open(path, encoding="utf-8").read()))
    if not sources:
        raise SystemExit(f"FAIL  no data models found in {data_dir}")
    return os.path.basename(feature_root), sources


def _feature_models(feature: str) -> tuple[str, List[RmapModel]]:
    label, sources = _feature_sources(feature)
    return label, [derive_model(concept, text, source=path)
                   for concept, path, text in sources]


def _data_models(paths: Iterable[str]) -> tuple[str, List[RmapModel]]:
    models = []
    for path in paths:
        text = open(path, encoding="utf-8").read()
        concept = os.path.basename(path)
        if concept.endswith(".data-model.md"):
            concept = concept[:-len(".data-model.md")]
        models.append(derive_model(concept, text, source=path))
    return "CLAD", models


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Derive Rmap SQL from Stage 03b conceptual models")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--feature", help="Feature root")
    group.add_argument("--data-model", action="append", default=[],
                       help="One <Name>.data-model.md (repeatable)")
    group.add_argument("--features-dir",
                       help="Project aggregate: canonical corpus models, or "
                            "feature 03b models when no corpus exists")
    parser.add_argument("--app-label", default=None)
    parser.add_argument("--write", default=None, help="Write full SQL to this path")
    parser.add_argument("--baseline", nargs="?", const="default", default=None,
                        metavar="NAME_OR_PATH",
                        help="Deployed baseline for --alter: an existing descriptor "
                             "path, or a name (default: default) searched under "
                             "_generated/rmap-baselines/ or _system/rmap-baselines/")
    parser.add_argument("--baseline-descriptor", default=None,
                        help="Deprecated alias for --baseline <path>")
    parser.add_argument("--record-baseline", nargs="?", const="default",
                        default=None,
                        help="Record the current descriptor as a baseline "
                             "(path or name; default: default)")
    parser.add_argument("--alter", default=None,
                        help="Write incremental ALTER/CREATE SQL to this path")
    parser.add_argument("--check-alter", default=None,
                        help="Fail when this incremental SQL file is stale")
    parser.add_argument("--force", action="store_true",
                        help="Allow --write/--alter to overwrite an existing "
                             "migration")
    parser.add_argument("--check", default=None,
                        help="Fail when this committed SQL is stale")
    parser.add_argument("--json", default=None,
                        help="Write the internal runtime descriptor")
    parser.add_argument("--stdout", action="store_true",
                        help="Print SQL (default when no output option)")
    parser.add_argument("--review", action="store_true",
                        help="Print the generated human-review tables")
    args = parser.parse_args(argv)

    # `--baseline-descriptor` is a deprecated alias for `--baseline <path>`;
    # fold it into the single value so `_resolve_baseline` has one source.
    if args.baseline_descriptor:
        if args.baseline not in (None, "default"):
            parser.error("--baseline-descriptor is a deprecated alias for "
                         "--baseline <path>; pass only one of them")
        args.baseline = args.baseline_descriptor

    if args.feature:
        app_label, sources = _feature_sources(args.feature)
    elif args.features_dir:
        app_label, sources = _project_sources(args.features_dir)
    else:
        app_label = "CLAD"
        sources = []
        for path in args.data_model:
            concept = os.path.basename(path)
            if concept.endswith(".data-model.md"):
                concept = concept[:-len(".data-model.md")]
            sources.append((concept, path, open(path, encoding="utf-8").read()))
    app_label = args.app_label or app_label
    if args.review:
        for concept, _path, text in sources:
            sys.stdout.write(render_review(concept, text))
            sys.stdout.write("\n")
        return 0
    models = [derive_model(concept, text, source=path)
              for concept, path, text in sources]
    sql = render_migration(app_label, models)
    descriptor = model_descriptor(models)

    if args.record_baseline is not None:
        if args.write or args.alter or args.check_alter:
            print("FAIL  --record-baseline is exclusive with --write/--alter/"
                  "--check-alter")
            return 1
        path = _record_baseline_path(args, args.record_baseline)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        code = _guarded_write(
            path, json.dumps(descriptor, indent=2) + "\n", args.force,
            label="baseline record")
        if code == 0:
            print(f"      baseline: {path}")
        return code

    if args.alter or args.check_alter:
        if args.write:
            print("FAIL  --alter is incremental; use --write for full SQL")
            return 1
        baseline_path = _resolve_baseline(args)
        with open(baseline_path, encoding="utf-8") as handle:
            baseline = json.load(handle)
        alter_sql, warnings = _alter_sql(baseline, descriptor, app_label)
        for warning in warnings:
            print(f"WARN  {warning}")
        print(f"  baseline: {baseline_path}")
        if args.alter:
            code = _guarded_write(args.alter, alter_sql, args.force)
            if code != 0:
                return code
        if args.check_alter:
            if not os.path.isfile(args.check_alter):
                print(f"FAIL  incremental SQL not found: {args.check_alter}")
                return 1
            with open(args.check_alter, encoding="utf-8") as handle:
                committed = handle.read()
            if committed != alter_sql:
                print(f"FAIL  {args.check_alter} is stale — regenerate it")
                return 1
            print(f"PASS  {args.check_alter} matches the baseline diff")
        if args.json:
            with open(args.json, "w", encoding="utf-8") as handle:
                json.dump(descriptor, handle, indent=2)
                handle.write("\n")
            print(f"WROTE {args.json}")
        if args.stdout or not (args.alter or args.check_alter or args.json):
            sys.stdout.write(alter_sql)
        return 0

    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(model_descriptor(models), handle, indent=2)
            handle.write("\n")
        print(f"WROTE {args.json}")
    if args.write:
        code = _guarded_write(args.write, sql, args.force)
        if code != 0:
            return code
    if args.check:
        if not os.path.isfile(args.check):
            print(f"FAIL  committed SQL not found: {args.check}")
            return 1
        committed = open(args.check, encoding="utf-8").read()
        if committed != sql:
            print(f"FAIL  {args.check} is stale — run `./clad rmap --write`")
            return 1
        print(f"PASS  {args.check} matches the conceptual model")
    if args.stdout or not (args.write or args.check or args.json):
        sys.stdout.write(sql)
    return 0


if __name__ == "__main__":
    sys.exit(main())
