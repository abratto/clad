#!/usr/bin/env python3
"""Rmap derivation and SQL rendering — the single authoritative implementation.

Rmap (Halpin's relational mapping) turns a Stage 03b conceptual model into a
set of relational tables. This module implements CLAD's documented **supported
subset** of Rmap (`methodology/architecture/RMAP_CONFORMANCE.md`) — it does not
claim every advanced refinement in the published procedure. It is the one
implementation used by the CLAD workflow; Java profiles consume the generated
SQL/descriptor rather than re-deriving the schema.

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


@dataclass(frozen=True)
class UniqueGroup:
    columns: List[str]
    while_absent: Optional[str] = None


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
    unique_groups: List[UniqueGroup] = field(default_factory=list)

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
    warnings: List[str] = field(default_factory=list)

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
    # The object type (or compound-subject key) that authored this fact. It
    # differs from the storage owner when the fact belongs to an absorbed
    # subtype: the fact is a nullable, conditionally mandatory column on the
    # supertype's table, not an unconditional one.
    source_type: str = ""
    # Explicit value-role participation (`value mandatory` / `value optional`).
    # None means the block did not state it. The subject role is `mandatory`.
    value_mandatory: Optional[bool] = None

    @property
    def compound(self) -> bool:
        return len(self.subject_types) > 1


@dataclass
class ParsedState:
    facts: List[FactType]
    subtypes: List[tuple]
    independent: List[str]
    unique_constraints: List[ap.UniqueConstraint]
    disjoint: List[tuple]
    exhaustive: List[str]
    discriminators: List[tuple]


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
    if re.search(r"\bderived\b", annotation, re.IGNORECASE):
        raise ValueError(
            f"fact '{relation.field}' is marked derived; derived facts are "
            f"outside CLAD's Rmap supported subset — derive them at "
            f"concept-read time instead of storing a base column")
    unique, unique_while = _unique_parts(annotation)
    default = re.search(r"\bdefault\s+([A-Za-z0-9_.'-]+)", annotation)
    enum = re.search(r"\bin\s*\{([^}]*)\}", annotation)
    subject_mandatory, value_mandatory = ap.role_flags(annotation)
    return FactType(
        field=relation.field,
        subject_types=subjects,
        value_type=value,
        multi_valued=_is_multi(relation),
        mandatory=subject_mandatory is True,
        unique=unique,
        default=default.group(1) if default else None,
        value_constraint=enum.group(1).strip() if enum else None,
        unique_while_absent=unique_while,
        value_mandatory=value_mandatory,
    )


def _parsed_state(machine: ap.MachineModel) -> ParsedState:
    facts = [_fact_type(relation) for relation in machine.facts]
    subtypes = [(sub, sup, (mapping or SEPARATE).lower())
                for sub, sup, mapping in machine.subtypes]
    return ParsedState(
        facts, subtypes, list(machine.independent),
        list(machine.unique_constraints), list(machine.disjoint),
        list(machine.exhaustive), list(machine.discriminators))


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


DEFAULT_TYPE_MAP = {
    "Int": "INTEGER",
    "Integer": "INTEGER",
    "Timestamp": "TIMESTAMP",
    "Instant": "TIMESTAMP",
    "Boolean": "BOOLEAN",
    "Decimal": "NUMERIC",
    "Numeric": "NUMERIC",
    "UUID": "UUID",
    "Uuid": "UUID",
    "Date": "DATE",
    "Time": "TIME",
    "Json": "JSONB",
    "JSON": "JSONB",
    "JSONB": "JSONB",
    "Bytes": "BYTEA",
    "Bytea": "BYTEA",
}


def _sql_type(value_type: str, type_map: Optional[Dict[str, str]] = None,
              strict: bool = False) -> str:
    """Map a conceptual value type to a SQL type.

    The built-in scalar names are mapped directly. A project/feature type map
    (`storage.type.<Name>=<SQL>` or `_config/type-map.md`) can add domain types;
    an unregistered domain value type keeps the historical `TEXT` fallback. In
    strict mode an unknown type fails loudly instead.
    """
    text = value_type.strip()
    params = re.match(
        r"^(\w+)\s*\(\s*(\d+)\s*(?:,\s*(\d+)\s*)?\)$", text)
    base = params.group(1) if params else text
    mapping = type_map or {}
    custom = mapping.get(text) or mapping.get(base)
    if custom is not None:
        rendered = custom.strip().upper()
        if (params and "(" not in rendered
                and rendered in ("NUMERIC", "DECIMAL")):
            rendered += "(" + params.group(2)
            if params.group(3):
                rendered += "," + params.group(3)
            rendered += ")"
        return rendered
    if params:
        if base in ("Decimal", "Numeric"):
            return ("NUMERIC(" + params.group(2)
                    + ("," + params.group(3) if params.group(3) else "")
                    + ")")
        if strict:
            raise ValueError(
                f"value type '{text}' is not a registered SQL type")
        return "TEXT"
    if text in DEFAULT_TYPE_MAP:
        return DEFAULT_TYPE_MAP[text]
    folded = text.lower()
    for name, sql in DEFAULT_TYPE_MAP.items():
        if name.lower() == folded:
            return sql
    if strict:
        raise ValueError(
            f"value type '{text}' is not a registered SQL type; add it to "
            f"the type map (`storage.type.{text}=<sql-type>`) or register a "
            f"runtime codec")
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


def _storage_owner(object_type: str, supertype_of: Dict[str, str],
                   mapping_of: Dict[str, str]) -> str:
    """The table-owning type for a fact subject.

    An absorbed subtype has no table of its own: its facts live on the nearest
    ancestor that is not itself absorbed. A separate or partition subtype owns
    its own table, so the walk stops there.
    """
    current = object_type
    seen = set()
    while (current in supertype_of
           and mapping_of.get(current) == ABSORB
           and current not in seen):
        seen.add(current)
        current = supertype_of[current]
    return current


def _entity_index(reference_schemes: Dict[str, str]) -> Dict[str, set]:
    """Reference-scheme type -> the object types it identifies."""
    index: Dict[str, set] = {}
    for entity, scheme in reference_schemes.items():
        index.setdefault(scheme, set()).add(entity)
    return index


def _resolve_entity(name: str, reference_schemes: Dict[str, str],
                    scheme_index: Dict[str, set],
                    subtype_of: Dict[str, str]) -> Optional[str]:
    """Resolve a fact value type to a same-concept entity, if it names one.

    An exact object-type name wins over a reference-scheme collision (a
    subtype commonly shares its root's scheme). When only a scheme is used,
    a unique root of the sharing entities is the referent; two unrelated
    entities sharing a scheme are genuinely ambiguous.
    """
    if name in reference_schemes:
        return name
    entities = scheme_index.get(name)
    if not entities:
        return None
    if len(entities) == 1:
        return next(iter(entities))
    roots = sorted(entity for entity in entities
                   if entity not in subtype_of)
    if len(roots) == 1:
        return roots[0]
    raise ValueError(
        f"ambiguous entity reference '{name}' names multiple object "
        f"types: {', '.join(sorted(entities))}")


def _fk_parts(spec: str) -> tuple[str, str, str]:
    arrow = spec.index("->")
    column = spec[:arrow].strip()
    reference = spec[arrow + 2:].strip()
    table = reference[:reference.index("(")].strip()
    target = reference[reference.index("(") + 1:reference.index(")")].strip()
    return column, table, target


def _fk_target(spec: str) -> str:
    return _fk_parts(spec)[1]


def _order_tables(tables: List[RelationSchema]) -> List[RelationSchema]:
    """Order tables so every inline FK references a table created earlier.

    `RmapPostgresFactStore.createSchema()` executes each table's embedded DDL,
    so forward references are not safe. Original order is retained among
    independent tables; a cycle is a modelling defect and fails loudly.
    """
    names = {table.table for table in tables}
    dependencies: Dict[str, set] = {}
    for table in tables:
        for fk in table.foreign_keys:
            target = _fk_target(fk)
            if target not in names:
                raise ValueError(
                    f"foreign key {fk!r} on table '{table.table}' references "
                    f"a table outside this concept's table set; cross-concept "
                    f"foreign keys are forbidden (R2)")
        dependencies[table.table] = {
            _fk_target(fk) for fk in table.foreign_keys
            if _fk_target(fk) != table.table}
    ordered: List[RelationSchema] = []
    remaining = list(tables)
    created: set = set()
    while remaining:
        progress = False
        for table in list(remaining):
            if dependencies[table.table] <= created:
                ordered.append(table)
                created.add(table.table)
                remaining.remove(table)
                progress = True
        if not progress:
            cycle = ", ".join(table.table for table in remaining)
            raise ValueError(f"foreign-key cycle among tables: {cycle}")
    return ordered


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


def _membership_check_name(object_type: str, subtype: str) -> str:
    return ("ck_" + snake_name(object_type) + "_"
            + snake_name(subtype) + "_member")[:63]


def _membership_checks(object_type: str, group: List[FactType],
                       subtype_of: Dict[str, str],
                       supertype_of: Dict[str, str],
                       discriminators: List[tuple]) -> List[Check]:
    """Qualified-optional checks for facts absorbed from subtypes.

    Without a discriminator, a row is a subtype member exactly when its subtype
    facts are present; the check allows either all guarded columns null
    (non-member) or every effective mandatory fact present (member), including
    the mandatory facts of absorbed ancestors. A discriminator makes membership
    explicit: the subtype's facts are required when the discriminator holds the
    declared value, and forbidden otherwise.
    """
    checks: List[Check] = []
    disc_by_sub = {sub: (predicate, value)
                   for sub, predicate, value in discriminators}
    absorbed = sorted({
        fact.source_type for fact in group
        if fact.source_type != object_type
        and subtype_of.get(fact.source_type) == ABSORB})
    for source in absorbed:
        own = [fact for fact in group
               if fact.source_type == source
               and not fact.compound and not fact.multi_valued]
        mandatory = [fact for fact in own if fact.mandatory]
        discriminator = disc_by_sub.get(source)
        if not mandatory and discriminator is None:
            raise ValueError(
                f"absorbed subtype '{source}' has no mandatory simple fact "
                f"and no discriminator; membership is not inferable — use "
                f"mapping: separate, add a mandatory fact, or add a "
                f"discriminator")
        if any(fact.default is not None for fact in own):
            raise ValueError(
                f"absorbed subtype '{source}' has a fact with a default; a "
                f"default would make non-members look like members — remove "
                f"the default or use mapping: separate")

        required = list(mandatory)
        ancestor = supertype_of.get(source)
        while ancestor and subtype_of.get(ancestor) == ABSORB:
            required.extend(
                fact for fact in group
                if fact.source_type == ancestor
                and not fact.compound and not fact.multi_valued
                and fact.mandatory)
            ancestor = supertype_of.get(ancestor)

        guarded = [snake(fact.field) for fact in own]
        needed = [snake(fact.field) for fact in required]
        if discriminator is not None:
            if not guarded:
                continue
            predicate, value = discriminator
            column = snake(predicate)
            literal = _sql_default(value)
            null_part = " AND ".join(
                f"{guarded_column} IS NULL" for guarded_column in guarded)
            if needed:
                member_part = " AND ".join(
                    f"{needed_column} IS NOT NULL"
                    for needed_column in needed)
                expression = (
                    f"({column} <> {literal} AND {null_part}) OR "
                    f"({column} = {literal} AND {member_part})")
            else:
                expression = (
                    f"({column} <> {literal} AND {null_part}) OR "
                    f"({column} = {literal})")
            checks.append(Check(
                _membership_check_name(object_type, source), expression))
            continue
        if len(guarded) == 1 and len(needed) == 1 and guarded == needed:
            continue
        expression = (
            "(" + " AND ".join(f"{column} IS NULL" for column in guarded)
            + ") OR ("
            + " AND ".join(f"{column} IS NOT NULL" for column in needed)
            + ")")
        checks.append(Check(
            _membership_check_name(object_type, source), expression))
    return checks


def _realize_table(concept: str, object_type: str, group: List[FactType],
                   is_compidot: bool, table: str,
                   subtype_of: Dict[str, str], supertype_of: Dict[str, str],
                   table_names: Dict[str, str],
                   reference_schemes: Dict[str, str],
                   discriminators: List[tuple],
                   type_map: Optional[Dict[str, str]] = None,
                   strict_types: bool = False) -> RelationSchema:
    columns: List[Column] = []
    checks: List[Check] = []
    foreign_keys: List[str] = []
    mapping = subtype_of.get(object_type)

    for fact in group:
        # A fact whose source is an absorbed subtype is conditional: nullable
        # for the supertype at large, constrained by the membership check.
        conditional = (fact.source_type != object_type
                       and subtype_of.get(fact.source_type) == ABSORB)
        if fact.compound:
            for subject in fact.subject_types:
                column = scheme_column(_root_scheme(
                    subject, supertype_of, reference_schemes))
                _add_column(columns, column, column, "TEXT", True, False, None)
            _add_column(columns, fact.field, snake(fact.field),
                        _sql_type(fact.value_type, type_map, strict_types),
                        fact.mandatory and not conditional,
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
                    _sql_type(fact.value_type, type_map, strict_types),
                    fact.mandatory and not conditional,
                    fact.unique, fact.default, None,
                    fact.unique_while_absent)
        if fact.value_constraint is not None:
            checks.append(Check(
                _check_name(object_type, fact.field),
                _check_expression(snake(fact.field), fact.value_constraint)))

    checks.extend(_membership_checks(
        object_type, group, subtype_of, supertype_of, discriminators))

    if is_compidot:
        primary_key = [scheme_column(_root_scheme(
            subject, supertype_of, reference_schemes))
            for subject in object_type.split("+")]
    elif mapping in (SEPARATE, PARTITION):
        supertype = supertype_of[object_type]
        id_column = scheme_column(_root_scheme(
            object_type, supertype_of, reference_schemes))
        if mapping == SEPARATE:
            anchor = _storage_owner(supertype, supertype_of, subtype_of)
            supertable = table_names.get(anchor)
            if supertable is None:
                raise ValueError(
                    f"separate subtype '{object_type}' has no supertype table "
                    f"('{supertype}' owns none); use a partition member or "
                    f"give the supertype stored state")
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
                  supertype_of: Dict[str, str],
                  type_map: Optional[Dict[str, str]] = None,
                  strict_types: bool = False) -> List[RelationSchema]:
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
            Column(fact.field, snake(fact.field),
                   _sql_type(fact.value_type, type_map, strict_types),
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
                 source: Optional[str] = None,
                 type_map: Optional[Dict[str, str]] = None,
                 strict_types: bool = False) -> RmapModel:
    """Derive a concept's table set from its Stage 03b data-model text."""
    machine = ap.parse_machine_model(data_model_text)
    if not machine.present:
        raise ValueError(
            f"no `## Machine model` / `## Conceptual model` block in "
            f"{source or concept}")
    if machine.errors:
        raise ValueError("; ".join(machine.errors))
    parsed = _parsed_state(machine)
    return _realize(concept, parsed, machine.object_types,
                    type_map=type_map, strict_types=strict_types)


def _validate_fact_roles(facts: List[FactType],
                         reference_schemes: Dict[str, str],
                         subtype_of: Dict[str, str]) -> List[str]:
    """Check value-role participation and Halpin's 1:1 grouping choice.

    A 1:1 between two object types belongs on the mandatory side. CLAD keeps
    the authored predicate orientation (automatic predicate flipping needs a
    runtime fact mapping), so the wrong orientation fails loudly instead of
    producing a silently weaker schema. A mandatory value role on a non-1:1
    fact is accepted but cannot be enforced by a single column.
    """
    warnings: List[str] = []
    index = _entity_index(reference_schemes)
    for fact in facts:
        if fact.value_mandatory is None:
            continue
        if fact.multi_valued:
            raise ValueError(
                f"fact '{fact.field}' states value-role participation on a "
                f"multi-valued fact; that constraint is not expressible as a "
                f"single column")
        target = _resolve_entity(
            fact.value_type, reference_schemes, index, subtype_of)
        if target is None:
            raise ValueError(
                f"fact '{fact.field}' states value-role participation but "
                f"'{fact.value_type}' is not an object type in this concept")
        if fact.compound:
            warnings.append(
                f"fact '{fact.field}' states value-role participation on an "
                f"objectified fact; the constraint is not enforced by the "
                f"generated schema")
            continue
        if fact.unique and fact.value_mandatory is True and not fact.mandatory:
            raise ValueError(
                f"1:1 fact '{fact.field}' is oriented on the optional role; "
                f"rewrite it with the mandatory role as the subject (for "
                f"example `fact {fact.field} : {fact.value_type} -> "
                f"{fact.subject_types[0]} -- mandatory, unique`) so the "
                f"column is grouped on the mandatory side")
        if fact.value_mandatory is True and not fact.unique:
            warnings.append(
                f"fact '{fact.field}' has a mandatory value role but is not "
                f"1:1; a single column cannot enforce that every '{target}' "
                f"participates (use a sync/assertion)")
    return warnings


def _validate_subtypes(facts: List[FactType],
                       subtypes: List[tuple],
                       discriminators: List[tuple],
                       disjoint: List[tuple],
                       exhaustive: List[str]) -> Dict[str, str]:
    """Reject subtype shapes whose constraints cannot be preserved.

    Mixing strategies on one supertype either drops the table another strategy
    needs (partition drops it; absorb/separate expect it) or makes membership
    undecidable. An absorbed subtype needs a mandatory qualifier or a
    discriminator; its multi-valued facts cannot be conditional. The
    absorption qualifier and default rules are enforced by
    `_membership_checks` when the table is realized.
    """
    subtype_of = {sub: mapping for sub, _sup, mapping in subtypes}
    supertype_of = {sub: sup for sub, sup, _mapping in subtypes}
    discriminator_subs = {sub for sub, _pred, _value in discriminators}
    by_super: Dict[str, set] = {}
    for sub, sup, mapping in subtypes:
        by_super.setdefault(sup, set()).add(mapping)
    for sup, mappings in by_super.items():
        if ABSORB in mappings and PARTITION in mappings:
            raise ValueError(
                f"supertype '{sup}' mixes absorb and partition subtypes; "
                f"partition drops the table absorption needs — use one "
                f"strategy per supertype")
        if PARTITION in mappings and SEPARATE in mappings:
            raise ValueError(
                f"supertype '{sup}' mixes partition and separate subtypes; "
                f"partition drops the supertype table a separate subtype "
                f"needs — use one strategy per supertype")
        if PARTITION in mappings and subtype_of.get(sup) == ABSORB:
            raise ValueError(
                f"partitioned supertype '{sup}' is itself absorbed; an "
                f"absorbed type has no table to partition")
    facts_by_field = {fact.field: fact for fact in facts}
    for sub, _sup, mapping in subtypes:
        if mapping != ABSORB:
            continue
        owned = [fact for fact in facts
                 if not fact.compound and fact.subject_types[0] == sub]
        if any(fact.multi_valued for fact in owned):
            raise ValueError(
                f"absorbed subtype '{sub}' has a multi-valued fact; its "
                f"cardinality cannot be conditional on membership — use "
                f"mapping: separate or partition")
        if (not any(fact.mandatory for fact in owned)
                and sub not in discriminator_subs):
            raise ValueError(
                f"absorbed subtype '{sub}' has no mandatory simple fact and "
                f"no discriminator; membership is not inferable — use "
                f"mapping: separate, add a mandatory fact, or add a "
                f"discriminator")
    seen_discriminators = set()
    for sub, predicate, value in discriminators:
        if subtype_of.get(sub) != ABSORB:
            raise ValueError(
                f"discriminator on '{sub}' requires mapping: absorb")
        fact = facts_by_field.get(predicate)
        if fact is None:
            raise ValueError(
                f"discriminator on '{sub}' names unknown fact '{predicate}'")
        if fact.compound or fact.multi_valued:
            raise ValueError(
                f"discriminator fact '{predicate}' must be simple and "
                f"single-valued")
        if fact.subject_types[0] != supertype_of.get(sub):
            raise ValueError(
                f"discriminator fact '{predicate}' must be a fact on the "
                f"direct supertype '{supertype_of.get(sub)}'")
        if not fact.mandatory:
            raise ValueError(
                f"discriminator fact '{predicate}' must be mandatory")
        key = (predicate, value)
        if key in seen_discriminators:
            raise ValueError(
                f"two subtypes share discriminator value '{value}' on "
                f"'{predicate}'")
        seen_discriminators.add(key)
    for group in disjoint:
        if len(group) < 2:
            raise ValueError(
                f"disjoint constraint needs at least two subtypes: "
                f"({', '.join(group)})")
        supers = {supertype_of.get(subtype) for subtype in group}
        if None in supers or len(supers) != 1:
            raise ValueError(
                f"disjoint subtypes ({', '.join(group)}) must share one "
                f"declared supertype")
    for supertype in exhaustive:
        children = [subtype for subtype, parent in supertype_of.items()
                    if parent == supertype]
        if not children:
            raise ValueError(
                f"exhaustive supertype '{supertype}' has no declared subtypes")
    return subtype_of


def _entity_table_name(entity: str, reference_schemes: Dict[str, str],
                       table_names: Dict[str, str],
                       supertype_of: Dict[str, str],
                       subtype_of: Dict[str, str]) -> Optional[str]:
    """The table that realises an entity, or None when it is identity-only.

    Subjects are authored either as the object-type name or as its
    reference-scheme type, so both spellings resolve to the same table. An
    absorbed subtype resolves to its owner's table; a separate/partition
    subtype with no table of its own is identity-only and must not fall back to
    the supertype table (that would silently weaken subtype membership).
    """
    mapping = subtype_of.get(entity)
    if mapping in (SEPARATE, PARTITION):
        return table_names.get(entity)
    scheme = reference_schemes.get(entity, entity)
    candidates = [entity, scheme,
                  _storage_owner(entity, supertype_of, subtype_of)]
    for candidate in list(candidates):
        owner = _storage_owner(candidate, supertype_of, subtype_of)
        if owner not in candidates:
            candidates.append(owner)
    for candidate in candidates:
        if candidate in table_names:
            return table_names[candidate]
    return None


def _add_entity_foreign_keys(model: RmapModel, facts: List[FactType],
                             reference_schemes: Dict[str, str],
                             subtype_of: Dict[str, str],
                             supertype_of: Dict[str, str],
                             table_names: Dict[str, str],
                             partition_supers: set) -> List[str]:
    """Render same-concept entity references as FKs when the target has state.

    The runtime writes `predicate(subject) = value` and has no operation that
    materialises an identity-only individual, so a FK to a table with no data
    column could never be satisfied. That case stays opaque with a warning.
    """
    warnings: List[str] = []
    index = _entity_index(reference_schemes)
    by_table = {table.table: table for table in model.tables}
    for fact in facts:
        if fact.compound or fact.multi_valued:
            continue
        target = _resolve_entity(
            fact.value_type, reference_schemes, index, subtype_of)
        if target is None:
            continue
        if target in partition_supers:
            raise ValueError(
                f"fact '{fact.field}' references partitioned supertype "
                f"'{target}', which has no single table; reference a member "
                f"instead")
        owner = _storage_owner(target, supertype_of, subtype_of)
        target_table = _entity_table_name(
            target, reference_schemes, table_names, supertype_of, subtype_of)
        schema = by_table.get(target_table) if target_table else None
        if schema is None:
            warnings.append(
                f"fact '{fact.field}' references '{target}', which owns no "
                f"table; the column stays opaque")
            continue
        if not schema.data_columns():
            warnings.append(
                f"fact '{fact.field}' references identity-only object type "
                f"'{target}'; the column stays opaque (the target has no "
                f"stored row)")
            continue
        if subtype_of.get(target) == ABSORB:
            warnings.append(
                f"fact '{fact.field}' references absorbed subtype "
                f"'{target}'; the FK enforces {owner} membership, not "
                f"{target} membership")
        column = snake(fact.field)
        owners = [
            table for table in model.tables
            if any(data.column == column for data in table.data_columns())]
        for table in owners:
            spec = f"{column} -> {schema.table}({schema.id_column})"
            if spec not in table.foreign_keys:
                table.foreign_keys.append(spec)
    return warnings


def _add_unique_groups(model: RmapModel, constraints: List[ap.UniqueConstraint],
                       facts: List[FactType]) -> None:
    """Resolve multi-column uniqueness declarations to table constraints."""
    facts_by_field = {fact.field: fact for fact in facts}
    for constraint in constraints:
        predicate_facts = []
        for predicate in constraint.predicates:
            fact = facts_by_field.get(predicate)
            if fact is None:
                raise ValueError(
                    f"unique constraint names unknown fact '{predicate}'")
            if fact.compound or fact.multi_valued:
                raise ValueError(
                    f"unique constraint predicate '{predicate}' must be a "
                    f"simple single-valued fact")
            predicate_facts.append(fact)
        owners = []
        for fact in predicate_facts:
            tables = [
                table for table in model.tables
                if any(column.column == snake(fact.field)
                       for column in table.data_columns())]
            if len(tables) != 1:
                raise ValueError(
                    f"unique constraint ({', '.join(constraint.predicates)}) "
                    f"spans multiple tables; only same-table uniqueness is "
                    f"supported")
            owners.append(tables[0])
        table = owners[0]
        if any(owner.table != table.table for owner in owners):
            raise ValueError(
                f"unique constraint ({', '.join(constraint.predicates)}) "
                f"spans multiple tables; only same-table uniqueness is "
                f"supported")
        columns = [snake(fact.field) for fact in predicate_facts]
        while_absent = None
        if constraint.while_absent:
            filter_fact = facts_by_field.get(constraint.while_absent)
            if filter_fact is None:
                raise ValueError(
                    f"unique constraint filter names unknown fact "
                    f"'{constraint.while_absent}'")
            if filter_fact.compound or filter_fact.multi_valued:
                raise ValueError(
                    f"unique constraint filter '{constraint.while_absent}' "
                    f"must be a simple single-valued fact")
            if not any(column.column == snake(filter_fact.field)
                       for column in table.data_columns()):
                raise ValueError(
                    f"unique constraint filter '{constraint.while_absent}' "
                    f"is on a different table from the constrained facts")
            while_absent = snake(filter_fact.field)
        group = UniqueGroup(columns, while_absent)
        if group not in table.unique_groups:
            table.unique_groups.append(group)


def _add_subtype_constraint_warnings(
        model: RmapModel, disjoint: List[tuple], exhaustive: List[str],
        facts: List[FactType], subtype_of: Dict[str, str],
        supertype_of: Dict[str, str], discriminators: List[tuple]) -> None:
    """Enforce absorbed disjointness where a table check can; report the rest."""
    facts_by_field = {fact.field: fact for fact in facts}
    disc_by_sub = {sub: (predicate, value)
                   for sub, predicate, value in discriminators}
    for group in disjoint:
        mappings = {subtype_of.get(subtype) for subtype in group}
        if mappings == {PARTITION}:
            continue  # partition members are physically disjoint
        if mappings == {SEPARATE}:
            model.warnings.append(
                f"disjoint subtypes ({', '.join(group)}) are mapped separately; "
                f"the declared disjointness is not enforced by the generated "
                f"schema")
            continue
        if mappings != {ABSORB}:
            model.warnings.append(
                f"disjoint subtypes ({', '.join(group)}) mix maps; the "
                f"declared disjointness is not enforced by the generated "
                f"schema")
            continue
        supertype = supertype_of.get(group[0])
        subjects = {supertype, *group}
        table = next((candidate for candidate in model.tables
                      if any(candidate.column_for(fact.field) is not None
                             for fact in facts
                             if fact.subject_types[0] in subjects
                             and not fact.compound
                             and not fact.multi_valued)), None)
        if table is None:
            model.warnings.append(
                f"disjoint subtypes ({', '.join(group)}) have no common "
                f"table; the declared disjointness is not enforced")
            continue
        discriminators_in_group = [disc_by_sub.get(subtype)
                                   for subtype in group]
        same_discriminator = (
            all(discriminators_in_group)
            and len({predicate for predicate, _ in discriminators_in_group}) == 1
            and len({value for _, value in discriminators_in_group})
            == len(group))
        if same_discriminator:
            continue  # one discriminator column cannot hold two values at once
        present = []
        missing = False
        for subtype in group:
            discriminator = disc_by_sub.get(subtype)
            if discriminator is not None:
                predicate, value = discriminator
                present.append(
                    f"{snake(predicate)} = {_sql_default(value)}")
                continue
            own = [fact for fact in facts
                   if fact.subject_types[0] == subtype
                   and not fact.compound and not fact.multi_valued]
            columns = [snake(fact.field) for fact in own]
            if not columns:
                missing = True
                break
            present.append(
                "(" + " OR ".join(f"{column} IS NOT NULL"
                                  for column in columns) + ")")
        if missing:
            model.warnings.append(
                f"disjoint subtypes ({', '.join(group)}) include a subtype "
                f"with no simple facts; the declared disjointness is not "
                f"enforced")
            continue
        for index, first in enumerate(present):
            for second in present[index + 1:]:
                table.checks.append(Check(
                    ("ck_" + snake_name(table.table) + "_disjoint_"
                     + str(len(table.checks)))[:63],
                    f"NOT ({first} AND {second})"))
    for supertype in exhaustive:
        mappings = {
            mapping for subtype, mapping in subtype_of.items()
            if supertype_of.get(subtype) == supertype}
        if mappings == {PARTITION}:
            continue  # partition is exhaustive by construction
        if mappings == {ABSORB} and all(
                subtype in disc_by_sub for subtype, mapping in subtype_of.items()
                if supertype_of.get(subtype) == supertype):
            model.warnings.append(
                f"exhaustive supertype '{supertype}' has discriminators; the "
                f"generated check enforces membership, but full coverage is "
                f"only enforced when the discriminator's value constraint "
                f"lists every subtype value")
            continue
        model.warnings.append(
            f"exhaustive supertype '{supertype}' is not enforced by the "
            f"generated schema (only partition is exhaustive by construction)")


def _realize(concept: str, parsed: ParsedState,
             reference_schemes: Dict[str, str],
             type_map: Optional[Dict[str, str]] = None,
             strict_types: bool = False) -> RmapModel:
    facts = parsed.facts
    subtype_of = _validate_subtypes(
        facts, parsed.subtypes, parsed.discriminators,
        parsed.disjoint, parsed.exhaustive)
    role_warnings = _validate_fact_roles(
        facts, reference_schemes, subtype_of)
    supertype_of = {sub: sup for sub, sup, _mapping in parsed.subtypes}
    partition_supers = {
        sup for _sub, sup, mapping in parsed.subtypes
        if mapping == PARTITION}

    by_owner: Dict[str, List[FactType]] = {}
    compidots = set()
    for fact in facts:
        if fact.compound:
            key = "+".join(fact.subject_types)
            fact.source_type = key
            compidots.add(key)
            by_owner.setdefault(key, []).append(fact)
            continue
        subject = fact.subject_types[0]
        fact.source_type = subject
        owner = _storage_owner(subject, supertype_of, subtype_of)
        by_owner.setdefault(owner, []).append(fact)

    def _depth(object_type: str) -> int:
        depth = 0
        current = object_type
        seen = set()
        while current in supertype_of and current not in seen:
            seen.add(current)
            current = supertype_of[current]
            depth += 1
        return depth

    # Partition flattens the supertype's own simple facts into each member
    # table; the supertype table is dropped. Process outer supertypes first so
    # a nested partition member also receives the ancestor's flattened facts.
    for supertype in sorted(partition_supers, key=_depth):
        members = [sub for sub, sup, mapping in parsed.subtypes
                   if sup == supertype and mapping == PARTITION]
        super_group = by_owner.pop(supertype, None)
        if not super_group:
            continue
        direct = [fact for fact in super_group
                  if not fact.compound and not fact.multi_valued]
        for member in members:
            group = by_owner.setdefault(member, [])
            for fact in direct:
                group.append(fact)

    by_owner = {key: value for key, value in by_owner.items() if value}
    # A type whose facts are all multi-valued has no functional role of its
    # own; its child tables already carry the subject column.
    by_owner = {key: value for key, value in by_owner.items()
                if not all(fact.multi_valued for fact in value)}

    simple_tables = [key for key in by_owner if key not in compidots]
    has_member_tables = any(
        mapping != ABSORB and subtype in by_owner
        for subtype, mapping in subtype_of.items())
    single = (len(simple_tables) == 1
              and not parsed.independent
              and not has_member_tables)
    table_names: Dict[str, str] = {}
    for object_type in by_owner:
        if object_type in compidots or not single:
            table_names[object_type] = (
                snake(concept) + "__" + snake_name(object_type))
        else:
            table_names[object_type] = snake(concept)

    tables: List[RelationSchema] = []
    for object_type, group in by_owner.items():
        tables.append(_realize_table(
            concept, object_type, group, object_type in compidots,
            table_names[object_type], subtype_of, supertype_of, table_names,
            reference_schemes, parsed.discriminators,
            type_map, strict_types))
    tables.extend(_child_tables(
        concept, facts, table_names, tables, reference_schemes,
        subtype_of, supertype_of, type_map, strict_types))
    for independent in parsed.independent:
        if independent in table_names:
            continue
        table = (snake(concept) if not by_owner
                 else snake(concept) + "__" + snake_name(independent))
        table_names[independent] = table
        tables.append(_independent_table(
            concept, independent, table, reference_schemes))

    model = RmapModel(concept, tables)
    model.warnings.extend(role_warnings)
    _add_unique_groups(model, parsed.unique_constraints, facts)
    _add_subtype_constraint_warnings(
        model, parsed.disjoint, parsed.exhaustive, facts, subtype_of,
        supertype_of, parsed.discriminators)
    model.warnings.extend(_add_entity_foreign_keys(
        model, facts, reference_schemes, subtype_of, supertype_of,
        table_names, partition_supers))
    for sub, sup, mapping in parsed.subtypes:
        if mapping == SEPARATE and subtype_of.get(sup) == ABSORB:
            model.warnings.append(
                f"separate subtype '{sub}' sits under absorbed supertype "
                f"'{sup}'; its FK enforces {_storage_owner(sup, supertype_of, subtype_of)} "
                f"membership, not {sup} membership")
    model.tables = _order_tables(tables)
    return model


# --------------------------------------------------------------------------
# SQL rendering
# --------------------------------------------------------------------------

_SQL_TYPE = {
    "INTEGER": "integer",
    "TIMESTAMP": "timestamp",
    "BOOLEAN": "boolean",
    "NUMERIC": "numeric",
    "UUID": "uuid",
    "DATE": "date",
    "TIME": "time",
    "JSONB": "jsonb",
    "BYTEA": "bytea",
}


def _render_sql_type(sql_type: str) -> str:
    text = (sql_type or "TEXT").strip()
    if text.upper() == "TEXT":
        return "varchar"
    if "(" in text:
        return text.lower()
    return _SQL_TYPE.get(text.upper(), text.lower())


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


def _fk_alter(table: str, spec: str) -> str:
    column, target_table, target = _fk_parts(spec)
    name = ("fk_" + table + "_" + column)[:63]
    return (f"ALTER TABLE {_quote(table)} ADD CONSTRAINT {_quote(name)} "
            f"FOREIGN KEY ({_quote(column)}) REFERENCES "
            f"{_quote(target_table)} ({_quote(target)});")


def _unique_group_alter(table: str, columns: Sequence[str],
                        while_absent: Optional[str]) -> str:
    if while_absent is not None:
        name = (table + "_" + "_".join(columns) + "_open_idx")[:63]
        return ("CREATE UNIQUE INDEX IF NOT EXISTS " + _quote(name)
                + " ON " + _quote(table)
                + " (" + ", ".join(_quote(column) for column in columns) + ")"
                + " WHERE " + _quote(while_absent) + " IS NULL;")
    name = ("uq_" + table + "_" + "_".join(columns))[:63]
    return ("ALTER TABLE " + _quote(table) + " ADD CONSTRAINT " + _quote(name)
            + " UNIQUE (" + ", ".join(_quote(column) for column in columns)
            + ");")


def _filtered_index(table: str, column: Column) -> str:
    return ("CREATE UNIQUE INDEX IF NOT EXISTS "
            + _quote(f"{table}_{column.column}_open_idx")
            + " ON " + _quote(table)
            + " (" + _quote(column.column) + ")"
            + " WHERE " + _quote(snake(column.unique_while_absent or ""))
            + " IS NULL")


_SQL_DEFAULT_KEYWORDS = {"null", "true", "false", "current_timestamp",
                          "current_date", "current_time", "now()"}


def _sql_default(value: str) -> str:
    """Render a CSDP `default` annotation as a SQL literal.

    String defaults must be quoted (`DEFAULT 'active'`); a bare identifier is
    parsed by SQL as a column reference and rejected. Numbers, booleans, NULL,
    and known temporal keywords stay unquoted. A value already quoted is kept.
    """
    text = value.strip()
    if not text:
        return "NULL"
    if text[:1] in ("'", '"'):
        return text
    if text.lower() in _SQL_DEFAULT_KEYWORDS:
        return text
    if re.fullmatch(r"-?\d+(\.\d+)?", text):
        return text
    return "'" + text.replace("'", "''") + "'"


def _create_table(schema: RelationSchema) -> str:
    single_pk = len(schema.primary_key) == 1
    single_key = schema.primary_key[0] if single_pk else None
    parts: List[str] = []
    for column in schema.columns:
        part = _quote(column.column) + " " + _render_sql_type(column.sql_type)
        if column.default is not None:
            part += " DEFAULT " + _sql_default(column.default)
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
    for group in schema.unique_groups:
        if group.while_absent is None:
            parts.append("UNIQUE ("
                         + ", ".join(_quote(c) for c in group.columns) + ")")
    for check in schema.checks:
        parts.append(f"CONSTRAINT {check.name} CHECK ({check.expression})")
    for foreign_key in schema.foreign_keys:
        parts.append(_fk_constraint(foreign_key))
    text = ("CREATE TABLE IF NOT EXISTS " + _quote(schema.table)
            + " (\n  " + ",\n  ".join(parts) + "\n)")
    for column in schema.columns:
        if column.unique_while_absent is not None:
            text += ";\n" + _filtered_index(schema.table, column)
    for group in schema.unique_groups:
        if group.while_absent is not None:
            index_name = (schema.table + "_" + "_".join(group.columns)
                          + "_open_idx")
            text += (
                ";\nCREATE UNIQUE INDEX IF NOT EXISTS " + _quote(index_name)
                + " ON " + _quote(schema.table)
                + " (" + ", ".join(_quote(c) for c in group.columns) + ")"
                + " WHERE " + _quote(group.while_absent) + " IS NULL")
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


def render_review(concept: str, data_model_text: str,
                  type_map: Optional[Dict[str, str]] = None,
                  strict_types: bool = False) -> str:
    """Human review view generated from the same conceptual block as Rmap."""
    machine = ap.parse_machine_model(data_model_text)
    parsed = _parsed_state(machine)
    model = _realize(concept, parsed, machine.object_types,
                     type_map=type_map, strict_types=strict_types)
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
    if model.warnings:
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        for warning in model.warnings:
            lines.append(f"- {warning}")
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
        if table.unique_groups:
            lines.append("- Unique groups: " + "; ".join(
                "(" + ", ".join(f"`{column}`" for column in group.columns)
                + ")" + (f" while `{group.while_absent}` absent"
                         if group.while_absent else "")
                for group in table.unique_groups))
        if table.checks:
            lines.append("- Checks: " + "; ".join(
                f"`{check.name}` = {check.expression}" for check in table.checks))
        if table.foreign_keys:
            lines.append("- Foreign keys: " + ", ".join(
                f"`{fk}`" for fk in table.foreign_keys))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _table_descriptor(table: RelationSchema) -> dict:
    entry = {
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
    if table.unique_groups:
        entry["uniqueGroups"] = [
            {"columns": list(group.columns),
             "whileAbsent": group.while_absent}
            for group in table.unique_groups
        ]
    return entry


def model_descriptor(models: Sequence[RmapModel]) -> dict:
    """Internal runtime descriptor (not a reviewed interchange artifact)."""
    return {
        "models": [
            {
                "concept": model.concept,
                "tables": [_table_descriptor(table) for table in model.tables],
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

    Creates new tables and adds new columns, checks, foreign keys, and unique
    groups. A changed CHECK expression is replaced (drop + add) with a warning;
    removed tables/columns/checks/keys are reported, never dropped
    automatically. A new mandatory column without a default is refused — it
    cannot be applied to existing rows safely.
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
                        + _render_sql_type(column.get("sqlType")))
                if column.get("default") is not None:
                    part += " DEFAULT " + _sql_default(column["default"])
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
            old_checks = {
                check["name"]: check["expression"]
                for check in old.get("checks", [])}
            new_checks = {
                check["name"]: check["expression"]
                for check in table.get("checks", [])}
            for check in table.get("checks", []):
                check_name = check["name"]
                if check_name not in old_checks:
                    statements.append(
                        f"ALTER TABLE {_quote(name)} ADD CONSTRAINT "
                        f"{_quote(check_name)} CHECK ({check['expression']});")
                    continue
                if old_checks[check_name] != check["expression"]:
                    statements.append(
                        f"ALTER TABLE {_quote(name)} DROP CONSTRAINT "
                        f"{_quote(check_name)};")
                    statements.append(
                        f"ALTER TABLE {_quote(name)} ADD CONSTRAINT "
                        f"{_quote(check_name)} CHECK ({check['expression']});")
                    warnings.append(
                        f"{name}.{check_name}: check expression changed — "
                        f"the generated migration drops and re-adds it; "
                        f"existing rows must satisfy the new expression")
            for check_name in old_checks:
                if check_name not in new_checks:
                    warnings.append(
                        f"{name}.{check_name}: check exists in the baseline "
                        f"but not in the current model — not dropped "
                        f"automatically")
            old_fks = set(old.get("foreignKeys", []))
            new_fks = set(table.get("foreignKeys", []))
            for fk in sorted(new_fks - old_fks):
                statements.append(_fk_alter(name, fk))
            for fk in sorted(old_fks - new_fks):
                warnings.append(
                    f"{name}: foreign key {fk} exists in the baseline but "
                    f"not in the current model — not dropped automatically")
            old_groups = {
                (tuple(group["columns"]), group.get("whileAbsent"))
                for group in old.get("uniqueGroups", [])}
            new_groups = {
                (tuple(group["columns"]), group.get("whileAbsent"))
                for group in table.get("uniqueGroups", [])}
            for columns, while_absent in sorted(
                    new_groups - old_groups,
                    key=lambda item: (item[0], item[1] or "")):
                statements.append(
                    _unique_group_alter(name, columns, while_absent))
            for columns, while_absent in sorted(
                    old_groups - new_groups,
                    key=lambda item: (item[0], item[1] or "")):
                warnings.append(
                    f"{name}: unique group ({', '.join(columns)}) exists in "
                    f"the baseline but not in the current model — not dropped "
                    f"automatically")
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


def _type_config_for(repo: str,
                     feature: Optional[str] = None) -> tuple[Dict[str, str], bool]:
    """Read `storage.type.*` properties and a feature `_config/type-map.md`.

    The map values are SQL types (e.g. `Money=NUMERIC(12,2)`). A feature map
    overrides the root properties. `storage.type.strict=true` makes unregistered
    value types fail instead of falling back to TEXT.
    """
    mapping: Dict[str, str] = {}
    strict = False
    props = os.path.join(repo, "clad.properties")
    if os.path.isfile(props):
        with open(props, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line.startswith("storage.type.") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                name = key[len("storage.type."):].strip()
                value = value.strip()
                if name.lower() == "strict":
                    strict = value.lower() in ("1", "true", "yes", "on")
                elif name:
                    mapping[name] = value
    if feature:
        override = os.path.join(os.path.abspath(feature), "_config",
                                "type-map.md")
        if os.path.isfile(override):
            with open(override, encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if (not line or line.startswith("#")
                            or line.startswith("<!--") or line.startswith("|")
                            or "=" not in line):
                        continue
                    name, value = line.split("=", 1)
                    name, value = name.strip(), value.strip()
                    if name and value:
                        mapping[name] = value
    return mapping, strict


def _type_config(args) -> tuple[Dict[str, str], bool]:
    repo = _repo_root_for(args)
    feature = os.path.abspath(args.feature) if args.feature else None
    return _type_config_for(repo, feature)


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
    feature = os.path.abspath(feature)
    repo = os.path.dirname(os.path.dirname(feature))
    type_map, strict = _type_config_for(repo, feature)
    label, sources = _feature_sources(feature)
    return label, [derive_model(concept, text, source=path,
                                type_map=type_map, strict_types=strict)
                   for concept, path, text in sources]


def _data_models(paths: Iterable[str]) -> tuple[str, List[RmapModel]]:
    type_map, strict = _type_config_for(os.getcwd())
    models = []
    for path in paths:
        text = open(path, encoding="utf-8").read()
        concept = os.path.basename(path)
        if concept.endswith(".data-model.md"):
            concept = concept[:-len(".data-model.md")]
        models.append(derive_model(concept, text, source=path,
                                   type_map=type_map, strict_types=strict))
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
    type_map, strict_types = _type_config(args)
    if args.review:
        for concept, _path, text in sources:
            sys.stdout.write(render_review(
                concept, text, type_map, strict_types))
            sys.stdout.write("\n")
        return 0
    models = [derive_model(concept, text, source=path,
                           type_map=type_map, strict_types=strict_types)
              for concept, path, text in sources]
    for model in models:
        for warning in model.warnings:
            sys.stderr.write(f"WARN  {model.concept}: {warning}\n")
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
