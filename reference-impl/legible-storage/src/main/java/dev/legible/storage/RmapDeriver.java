package dev.legible.storage;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Derives a concept's relational tables from its Stage 02 {@code ## State}
 * relational notation, by Halpin's <strong>Rmap</strong>.
 *
 * <p><strong>Input notation.</strong> One fact type per line:
 * <pre>
 *   field: Subject -&gt; Value        -- annotations
 *   field: (A, B) -&gt; Value         -- composite subject (objectified / nested)
 *   field: Subject -&gt; {Value}      -- multi-valued ("zero or more")
 * </pre>
 * Annotations recognised: {@code mandatory | optional}, {@code unique …},
 * {@code default <expr>}, and an enumerated value constraint
 * {@code in {a, b, c}} or {@code in {a..b}}.
 *
 * <p><strong>Rmap stages.</strong>
 * <ol>
 *   <li>Each subject object type is a table; nested/compound subjects become
 *       their own table (they are "compidots").</li>
 *   <li>A fact type whose key is composite (the subject is a pair, or the value
 *       is multi-valued) maps to its own table, keyed on that composite.</li>
 *   <li>Fact types with a simple key on a common object type group into that
 *       object type's table, keyed on its identifier.</li>
 *   <li>Compidots are unpacked into component attributes (the columns of their
 *       own table).</li>
 * </ol>
 *
 * <p>A concept whose state ranges over several object types yields several
 * tables (an {@link RmapModel}); this is what lets a concept such as an ontology
 * (three reference schemes plus a compound subject) realise faithfully, instead
 * of being forced into one table.
 */
public final class RmapDeriver {

    /** {@code field: Subject -> Value} (single subject, single value). */
    private static final Pattern SIMPLE = Pattern.compile(
            "^\\s*(\\w+)\\s*:\\s*(\\w+)\\s*->\\s*(\\w+)\\s*(?:--\\s*(.*))?\\s*$");

    /** {@code field: (A, B) -> Value} (compound/objectified subject). */
    private static final Pattern COMPOUND = Pattern.compile(
            "^\\s*(\\w+)\\s*:\\s*\\(\\s*([^)]*)\\s*\\)\\s*->\\s*(\\w+)\\s*(?:--\\s*(.*))?\\s*$");

    /** {@code field: Subject -> {Value}} or the word form "zero or more". */
    private static final Pattern MULTI = Pattern.compile(
            "^\\s*(\\w+)\\s*:\\s*(\\w+)\\s*->\\s*\\{\\s*(\\w+)\\s*\\}\\s*(?:--\\s*(.*))?\\s*$");

    /** {@code field: Subject -> Value -- zero or more} (multi-valued in prose). */
    private static final Pattern MULTI_PROSE = Pattern.compile(
            "^\\s*(\\w+)\\s*:\\s*(\\w+)\\s*->\\s*(\\w+)\\s*--\\s*(.*\\b(zero or more|many|optional many)\\b.*)$");

    /** {@code Sub is a Sup -- mapping: absorb|separate|partition} (subtype declaration). */
    private static final Pattern SUBTYPE = Pattern.compile(
            "^\\s*(\\w+)\\s+is a\\s+(\\w+)\\s*(?:--\\s*(.*))?\\s*$");

    /** {@code independent T} — an object type with no functional fact role. */
    private static final Pattern INDEPENDENT = Pattern.compile(
            "^\\s*independent\\s+(\\w+)\\s*(?:--\\s*(.*))?\\s*$");

    /**
     * {@code object-type <Entity> identified-by <IdType>} — a reference-scheme
     * declaration: the entity's identity column is named after {@code <IdType>},
     * not after the entity.
     */
    private static final Pattern OBJECT_TYPE = Pattern.compile(
            "^\\s*object-type\\s+(\\S+)\\s+identified-by\\s+(\\S+)(?:\\s+--.*)?\\s*$");

    private static final Pattern DEFAULT = Pattern.compile("\\bdefault\\s+(\\w+)");
    private static final Pattern ENUM_IN = Pattern.compile("\\bin\\s*\\{([^}]*)\\}");

    /**
     * {@code unique while <field> absent|missing} — filtered uniqueness in the
     * annotation tail (see {@link #uniqueWhileAbsentOf}).
     */
    private static final Pattern UNIQUE_WHILE_ABSENT = Pattern.compile(
            "\\bunique\\s+while\\s+(\\w+)\\s+(?:absent|missing)");

    /** A standalone `unique` — not the `unique while \u2026` spelling. */
    private static final Pattern PLAIN_UNIQUE = Pattern.compile(
            "\\bunique(?!\\s+while\\b)");

    /** How a subtype's fact types realise (the per-model Rmap choice). */
    private enum SubtypeMapping {
        ABSORB, SEPARATE, PARTITION;

        static SubtypeMapping of(String annotation) {
            if (annotation == null) {
                return SEPARATE; // deterministic default: loss-free separation
            }
            String a = annotation.toLowerCase(java.util.Locale.ROOT);
            if (a.contains("absorb")) return ABSORB;
            if (a.contains("partition")) return PARTITION;
            return SEPARATE;
        }
    }

    private RmapDeriver() {
    }

    /**
     * Derive the concept's table set from its {@code ## State} block body.
     *
     * <p>This is the raw-notation form, kept for the equivalence check and for
     * callers that hold a {@code ## State} body. The canonical Rmap input is the
     * Stage 03b data model, read via
     * {@link #deriveModelFromDataModel(String, String)}.
     */
    public static RmapModel deriveModel(String concept, String stateNotation) {
        return realize(concept, parse(concept, stateNotation));
    }

    /**
     * Derive the concept's table set from its Stage 03b
     * {@code <Name>.data-model.md} text, via the CSDP-aligned
     * {@code ## Machine model} block (the canonical Rmap input). The block's
     * {@code fact} / {@code is a} / {@code independent} clauses are the same
     * grammar as {@code ## State}; {@code object-type … identified-by …}
     * declares reference schemes and contributes no fact of its own.
     *
     * <p>Use {@link #deriveModel(String, String)} only for a raw {@code ## State}
     * body; a data-model file contains CSDP prose, so this entry extracts the
     * block rather than parsing the whole file.
     */
    public static RmapModel deriveModelFromDataModel(String concept, String dataModelMarkdown) {
        return realize(concept, parse(concept, machineModelBody(concept, dataModelMarkdown)),
                referenceSchemes(concept, dataModelMarkdown));
    }

    /**
     * The single table derived from a data-model file (see
     * {@link #deriveModelFromDataModel}); throws when the concept is multi-table.
     */
    public static RelationSchema deriveFromDataModel(String concept, String dataModelMarkdown) {
        RmapModel model = deriveModelFromDataModel(concept, dataModelMarkdown);
        if (model.tables().size() != 1) {
            throw new IllegalArgumentException("concept " + concept + " realises as "
                    + model.tables().size() + " tables — use deriveModelFromDataModel()");
        }
        return model.tables().get(0);
    }

    /**
     * Extract the {@code ## Machine model} fenced block from a data-model file,
     * returning only the clauses the realization {@link #parse} understands: the
     * {@code object-type …} declarations are dropped (they name reference
     * schemes, not facts). Throws when the section or its fence is absent — a
     * data-model file without a machine block cannot drive Rmap.
     */
    private static String machineModelBlock(String concept, String dataModelMarkdown) {
        String[] lines = dataModelMarkdown.split("\\R");
        int section = -1;
        for (int i = 0; i < lines.length; i++) {
            if (lines[i].trim().equals("## Machine model")) {
                section = i;
                break;
            }
        }
        if (section < 0) {
            throw new IllegalArgumentException(
                    "no `## Machine model` block in data model for concept " + concept);
        }
        int fence = -1;
        for (int i = section + 1; i < lines.length; i++) {
            if (lines[i].trim().startsWith("```")) {
                fence = i;
                break;
            }
        }
        if (fence < 0) {
            throw new IllegalArgumentException(
                    "`## Machine model` block is not fenced in data model for concept " + concept);
        }
        StringBuilder block = new StringBuilder();
        for (int i = fence + 1; i < lines.length; i++) {
            if (lines[i].trim().startsWith("```")) {
                break;
            }
            block.append(lines[i]).append('\n');
        }
        return block.toString();
    }

    private static String machineModelBody(String concept, String dataModelMarkdown) {
        StringBuilder body = new StringBuilder();
        for (String raw : machineModelBlock(concept, dataModelMarkdown).split("\\R")) {
            String line = raw.trim();
            if (line.startsWith("object-type")) {
                continue; // reference-scheme declaration, not a fact
            }
            // The machine block prefixes each fact with `fact `; the realization
            // parser reads the bare `field : Subject -> Value` form.
            if (line.startsWith("fact ")) {
                line = line.substring("fact ".length()).trim();
            }
            body.append(line).append('\n');
        }
        return body.toString();
    }

    /** The reference scheme per object type: {@code object-type E identified-by I}. */
    private static Map<String, String> referenceSchemes(String concept, String dataModelMarkdown) {
        Map<String, String> schemes = new LinkedHashMap<>();
        for (String raw : machineModelBlock(concept, dataModelMarkdown).split("\\R")) {
            Matcher m = OBJECT_TYPE.matcher(raw.trim());
            if (m.matches()) {
                schemes.put(m.group(1), m.group(2));
            }
        }
        return schemes;
    }

    /**
     * Derive the single table for the common case (one object type, no
     * compound/multi-valued subjects). Throws when the concept is genuinely
     * multi-table — callers that can handle a set should use
     * {@link #deriveModel(String, String)}.
     */
    public static RelationSchema derive(String concept, String stateNotation) {
        RmapModel model = deriveModel(concept, stateNotation);
        if (model.tables().size() != 1) {
            throw new IllegalArgumentException("concept " + concept + " realises as "
                    + model.tables().size() + " tables — use deriveModel()");
        }
        return model.tables().get(0);
    }

    // ---- parsing -------------------------------------------------------------

    private record FactType(String field, List<String> subjectTypes, String valueType,
                            boolean multiValued, boolean mandatory, boolean unique,
                            String defaultValue, String valueConstraint,
                            String uniqueWhileAbsent) {
        boolean compound() {
            return subjectTypes.size() > 1;
        }
    }

    /** Parsed subtype declarations: which could a new model add; none today. */
    record DeclaredSubtype(String subtype, String supertype, SubtypeMapping mapping) {}

    private record ParsedState(List<FactType> facts, List<DeclaredSubtype> subtypes,
                               List<String> independentTypes) {}

    private static ParsedState parse(String concept, String stateNotation) {
        List<FactType> facts = new ArrayList<>();
        List<DeclaredSubtype> subtypes = new ArrayList<>();
        List<String> independentTypes = new ArrayList<>();
        boolean sawRelation = false;
        for (String line : stateNotation.split("\\R")) {
            if (line.isBlank()) {
                continue;
            }
            String trimmed = line.trim();
            // Skip structural/prose lines: headings, blockquotes, fenced-code
            // markers, and anything that is clearly not a relation line. A
            // *candidate* relation line that fails to parse still throws below.
            if (trimmed.startsWith("#") || trimmed.startsWith(">")
                    || trimmed.startsWith("```") || trimmed.startsWith("--")
                    || trimmed.endsWith(":")) {
                continue;
            }
            Matcher sub = SUBTYPE.matcher(trimmed);
            if (sub.matches() && !trimmed.contains("->")) {
                subtypes.add(new DeclaredSubtype(sub.group(1), sub.group(2),
                        SubtypeMapping.of(sub.group(3))));
                sawRelation = true;
                continue;
            }
            Matcher ind = INDEPENDENT.matcher(trimmed);
            if (ind.matches()) {
                independentTypes.add(ind.group(1));
                sawRelation = true;
                continue;
            }
            if (!trimmed.contains("->")) {
                continue;
            }
            sawRelation = true;
            Matcher cm = COMPOUND.matcher(line);
            if (cm.matches()) {
                facts.add(factType(concept, cm.group(1),
                        splitSubjects(cm.group(2)), cm.group(3), false, cm.group(4)));
                continue;
            }
            Matcher mm = MULTI.matcher(line);
            if (mm.matches()) {
                facts.add(factType(concept, mm.group(1),
                        List.of(mm.group(2)), mm.group(3), true, mm.group(4)));
                continue;
            }
            Matcher mp = MULTI_PROSE.matcher(line);
            if (mp.matches()) {
                facts.add(factType(concept, mp.group(1),
                        List.of(mp.group(2)), mp.group(3), true, mp.group(4)));
                continue;
            }
            Matcher sm = SIMPLE.matcher(line);
            if (sm.matches()) {
                facts.add(factType(concept, sm.group(1),
                        List.of(sm.group(2)), sm.group(3), false, sm.group(4)));
                continue;
            }
            // A line that looks like a relation (`->` present) but does not
            // match: surface it loudly rather than silently dropping a fact —
            // a silent drop is the exact failure this rewrite fixes.
            throw new IllegalArgumentException(
                    "cannot parse state relation for " + concept + ": " + line);
        }
        if (!sawRelation) {
            throw new IllegalArgumentException("no state relation parsed for concept " + concept);
        }
        return new ParsedState(facts, subtypes, independentTypes);
    }

    private static List<String> splitSubjects(String inner) {
        List<String> out = new ArrayList<>();
        for (String s : inner.split(",")) {
            if (!s.isBlank()) {
                out.add(s.trim());
            }
        }
        return out;
    }

    private static FactType factType(String concept, String field, List<String> subjects,
                                     String valueType, boolean multi, String annotations) {
        String ann = annotations == null ? "" : annotations;
        String filter = uniqueWhileAbsentOf(ann);
        // When a filtered uniqueness is present it replaces the unconditional
        // one: `unique while X absent` is NOT a global UNIQUE — the column-only
        // `UNIQUE` marker must not also fire for the `unique while …` spelling.
        boolean unique = filter != null
                ? PLAIN_UNIQUE.matcher(ann).find()
                : ann.contains("unique");
        return new FactType(field, subjects, valueType, multi,
                ann.contains("mandatory"),
                unique,
                defaultOf(ann),
                enumConstraint(ann),
                filter);
    }

    private static String defaultOf(String annotations) {
        Matcher m = DEFAULT.matcher(annotations);
        return m.find() ? m.group(1) : null;
    }

    private static String enumConstraint(String annotations) {
        Matcher m = ENUM_IN.matcher(annotations);
        return m.find() ? m.group(1) : null;
    }

    /**
     * A filtered uniqueness — `unique while returnedAt absent` — the
     * external-uniqueness-with-open-individuals rule (at most one OPEN loan per
     * copy), realised by the DDL renderers as a partial unique index over the
     * fact column filtered on the named field's NULL. Only meaningful with a
     * single-valued fact; ignored for multi-valued child tables.
     */
    private static String uniqueWhileAbsentOf(String annotations) {
        Matcher m = UNIQUE_WHILE_ABSENT.matcher(annotations);
        return m.find() ? m.group(1) : null;
    }

    // ---- realization (Rmap stages 1-4) ----------------------------------------

    private static RmapModel realize(String concept, ParsedState parsed) {
        return realize(concept, parsed, Map.of());
    }

    private static RmapModel realize(String concept, ParsedState parsed,
                                     Map<String, String> referenceSchemes) {
        List<FactType> facts = parsed.facts();
        Map<String, SubtypeMapping> subtypeOf = new LinkedHashMap<>();
        Map<String, String> supertypeOf = new LinkedHashMap<>();
        for (DeclaredSubtype d : parsed.subtypes()) {
            subtypeOf.put(d.subtype(), d.mapping());
            supertypeOf.put(d.subtype(), d.supertype());
        }

        // Stage 1: each subject object type is a table; a compound subject is a
        // compidot (its own table). A subtype's simple-key facts group into the
        // table its mapping chooses — the supertype's under absorption, its own
        // under separation/partition. Preserve first-seen order.
        Map<String, List<FactType>> byObjectType = new LinkedHashMap<>();
        Map<String, Boolean> compidots = new LinkedHashMap<>();
        Set<String> occupiedTables = new LinkedHashSet<>();
        for (FactType f : facts) {
            if (f.compound()) {
                String key = compoundKey(f.subjectTypes());
                compidots.put(key, true);
                byObjectType.computeIfAbsent(key, k -> new ArrayList<>()).add(f);
                occupiedTables.add(key);
                continue;
            }
            String subject = f.subjectTypes().get(0);
            if (subtypeOf.containsKey(subject)
                    && subtypeOf.get(subject) == SubtypeMapping.ABSORB) {
                subject = supertypeOf.get(subject);
            }
            byObjectType.computeIfAbsent(subject, k -> new ArrayList<>()).add(f);
            occupiedTables.add(subject);
        }

        // Absorption moves the subtype's fact types onto the supertype's
        // table; the supertype group must therefore see them. Retarget the
        // grouped lists, not the facts themselves.
        for (Map.Entry<String, String> e : supertypeOf.entrySet()) {
            if (subtypeOf.get(e.getKey()) != SubtypeMapping.ABSORB) {
                continue;
            }
            List<FactType> absorbed = byObjectType.remove(e.getKey());
            if (absorbed != null) {
                byObjectType.computeIfAbsent(e.getValue(), k -> new ArrayList<>())
                        .addAll(absorbed);
                occupiedTables.remove(e.getKey());
            }
        }

        // Partition: the supertype's own fact types are flattened into each
        // subtype's table (disjoint, exhaustive members carry the whole shape),
        // so the supertype needs no table of its own.
        Map<String, List<String>> partitionMembers = new LinkedHashMap<>();
        for (Map.Entry<String, String> e : supertypeOf.entrySet()) {
            if (subtypeOf.get(e.getKey()) == SubtypeMapping.PARTITION) {
                partitionMembers.computeIfAbsent(e.getValue(), k -> new ArrayList<>())
                        .add(e.getKey());
            }
        }
        for (Map.Entry<String, List<String>> e : partitionMembers.entrySet()) {
            String supertype = e.getKey();
            List<FactType> supertypeFacts = byObjectType.get(supertype);
            if (supertypeFacts == null) {
                continue;
            }
            List<FactType> direct = new ArrayList<>();
            for (FactType f : supertypeFacts) {
                if (!f.compound() && f.subjectTypes().get(0).equals(supertype)) {
                    direct.add(f);
                }
            }
            for (String member : e.getValue()) {
                List<FactType> memberGroup = byObjectType.computeIfAbsent(member,
                        k -> new ArrayList<>());
                for (FactType f : direct) {
                    if (!memberGroup.contains(f)) {
                        memberGroup.add(f);
                    }
                }
            }
            byObjectType.remove(supertype);
            occupiedTables.remove(supertype);
        }

        // A declared supertype with no facts of its own under
        // separation/partition contributes no rows; drop its empty group.
        byObjectType.entrySet().removeIf(e -> e.getValue().isEmpty());

        // An object type whose facts are all multi-valued plays no functional
        // role of its own: its multi-valued facts realise as child tables, so a
        // table for it would be identity-only (unpopulationable through the SPI).
        // Drop it — the child table already carries the subject column.
        byObjectType.entrySet().removeIf(e ->
                e.getValue().stream().allMatch(FactType::multiValued));

        // Table naming: when the region's realised non-compidot tables are
        // exactly one, it carries the concept's plain name; otherwise each
        // table is concept-qualified.
        List<String> simpleTables = new ArrayList<>();
        for (String t : byObjectType.keySet()) {
            if (!compidots.containsKey(t)) {
                simpleTables.add(t);
            }
        }
        // The "single -> concept name" collapse is suppressed whenever a
        // separate/partition member table is in play: a member table is
        // resolved by its deterministic member name (`memberTableName`), so
        // collapsing the last surviving simple table to the concept name would
        // make `tableForMember` return null (the drop rule can remove a member
        // whose only facts are multi-valued).
        boolean hasMemberTables = supertypeOf.entrySet().stream()
                .filter(e -> subtypeOf.get(e.getKey()) != SubtypeMapping.ABSORB)
                .anyMatch(e -> byObjectType.containsKey(e.getKey()));
        boolean single = simpleTables.size() == 1
                && parsed.independentTypes().isEmpty()
                && !hasMemberTables;
        Map<String, String> tableNames = new LinkedHashMap<>();
        for (String t : byObjectType.keySet()) {
            boolean isCompidot = compidots.containsKey(t);
            if (isCompidot || !single) {
                tableNames.put(t, snake(concept) + "__" + snakeName(t));
            } else {
                tableNames.put(t, snake(concept));
            }
        }

        List<RelationSchema> tables = new ArrayList<>();
        for (Map.Entry<String, List<FactType>> entry : byObjectType.entrySet()) {
            String objectType = entry.getKey();
            tables.add(realizeTable(concept, objectType, entry.getValue(),
                    compidots.containsKey(objectType), tableNames.get(objectType),
                    subtypeOf, supertypeOf, tableNames, referenceSchemes));
        }
        // Stage 2: multi-valued facts get their own child table (composite PK).
        for (RelationSchema child : childTables(concept, facts, tableNames, tables,
                referenceSchemes, subtypeOf, supertypeOf)) {
            tables.add(child);
        }
        // Independent object types play no functional role; Rmap realises each
        // as its own single-column table keyed by the reference scheme.
        for (String independent : parsed.independentTypes()) {
            if (tableNames.containsKey(independent)) {
                continue; // already realised through its facts' grouping
            }
            // A lone independent type carries the concept's plain name; beside
            // other tables it is concept-qualified.
            tables.add(independentTable(concept, independent, byObjectType.isEmpty()
                    ? snake(concept) : snake(concept) + "__" + snakeName(independent),
                    referenceSchemes));
        }
        return new RmapModel(concept, tables);
    }

    private static RmapModel realize(String concept, List<FactType> facts) {
        return realize(concept, new ParsedState(facts, List.of(), List.of()));
    }

    /** The single-column table for an independent object type. */
    private static RelationSchema independentTable(String concept, String objectType,
                                                   String table,
                                                   Map<String, String> referenceSchemes) {
        // The column follows the type's reference scheme, like every other
        // identity column; a type without a declared scheme falls back to its
        // own name.
        String id = snake(referenceSchemes.getOrDefault(objectType, objectType));
        List<RelationSchema.Column> columns = List.of(
                new RelationSchema.Column(id, id, "TEXT", true, false, null, null));
        return new RelationSchema(concept, table, objectType, columns,
                List.of(id), List.of(), List.of(), false);
    }

    /**
     * The reference-scheme type of an object type, following the subtype chain
     * to its root. A subtype has no reference scheme of its own and inherits its
     * supertype's <em>transitively</em> (ORM: {@code isA} is transitive), so the
     * identity column is named after the ROOT supertype's scheme — not the
     * immediate supertype's.
     */
    private static String rootScheme(String objectType,
                                     Map<String, String> supertypeOf,
                                     Map<String, String> referenceSchemes) {
        String current = objectType;
        java.util.Set<String> seen = new java.util.LinkedHashSet<>();
        while (supertypeOf.containsKey(current) && seen.add(current)) {
            current = supertypeOf.get(current);
        }
        return referenceSchemes.getOrDefault(current, current);
    }

    private static RelationSchema realizeTable(String concept, String objectType,
                                               List<FactType> group, boolean isCompidot,
                                               String table,
                                               Map<String, SubtypeMapping> subtypeOf,
                                               Map<String, String> supertypeOf,
                                               Map<String, String> tableNames,
                                               Map<String, String> referenceSchemes) {
        // Stage 3: absorb every simple-key fact grouped under this object type.
        // Stage 4: a compidot absorbs its component value columns. Subtypes
        // realise under the mapping's choice (separate/partition keep a table,
        // with an intra-concept link to the supertype's table).
        List<RelationSchema.Column> columns = new ArrayList<>();
        List<RelationSchema.Check> checks = new ArrayList<>();
        List<String> foreignKeys = new ArrayList<>();
        List<String> pk;

        boolean isSubtype = subtypeOf.containsKey(objectType)
                && subtypeOf.get(objectType) != SubtypeMapping.ABSORB;

        for (FactType f : group) {
            if (f.compound()) {
                // The compound fact's components are columns of the compidot
                // table (subject components + the value).
                for (String s : f.subjectTypes()) {
                    // Each component column follows its own type's reference scheme.
                    String col = snake(rootScheme(s, supertypeOf, referenceSchemes));
                    addColumn(columns, col, col, "TEXT", true, false, null, null);
                }
                addColumn(columns, f.field(), snake(f.field()), sqlTypeOf(f.valueType()),
                        f.mandatory(), f.unique(), f.defaultValue(), null,
                        f.uniqueWhileAbsent());
                if (f.valueConstraint() != null) {
                    checks.add(new RelationSchema.Check(
                            checkName(objectType, f.field()),
                            checkExprOn(snake(f.field()), f.valueConstraint())));
                }
                continue;
            }
            // Multi-valued fact (zero or more): Rmap stage 2 → its own child
            // table, keyed on (subject, value). Handled in childTables.
            if (f.multiValued()) {
                continue;
            }
            addColumn(columns, f.field(), snake(f.field()), sqlTypeOf(f.valueType()),
                    f.mandatory(), f.unique(), f.defaultValue(), null,
                    f.uniqueWhileAbsent());
            if (f.valueConstraint() != null) {
                checks.add(new RelationSchema.Check(
                        checkName(objectType, f.field()),
                        checkExprOn(snake(f.field()), f.valueConstraint())));
            }
        }

        if (isCompidot) {
            // A compidot's primary key is its component columns (the
            // objectified fact's roles); it has no separate surrogate id.
            pk = new ArrayList<>();
            for (String s : objectType.split("\\+")) {
                pk.add(snake(rootScheme(s, supertypeOf, referenceSchemes)));
            }
        } else if (isSubtype) {
            // A subtype has no reference scheme of its own — its identity is
            // the supertype's (a subtype row is a supertype row). The table
            // therefore keys on the supertype's identity column, and reports
            // the supertype's scheme as its identity-owning object type.
            String supertype = supertypeOf.get(objectType);
            String supertable = tableNames.get(supertype);
            // The key column is the ROOT supertype's identity column (the scheme
            // is inherited transitively), not the immediate supertype's entity.
            String idColumn = snake(rootScheme(objectType, supertypeOf, referenceSchemes));
            if (supertable != null) {
                // The subtype's specific columns carry their own rows only
                // where an individual exists as that subtype; the shared key
                // links to the supertype's table (an intra-concept FK — legal
                // under R2; no FK crosses a concept boundary).
                foreignKeys.add(idColumn + " -> " + supertable
                        + "(" + idColumn + ")");
            }
            objectType = supertype;
            pk = List.of(idColumn);
            if (columns.stream().noneMatch(c -> c.column().equals(idColumn))) {
                columns.add(0, new RelationSchema.Column(idColumn, idColumn, "TEXT",
                        true, false, null, null));
            }
        } else {
            // The identity column is named after the object type's reference
            // scheme (`object-type E identified-by I` -> column `snake(I)`), not
            // after the entity; a type without a declared scheme falls back to
            // its own name.
            String idColumn = snake(referenceSchemes.getOrDefault(objectType, objectType));
            if (columns.stream().noneMatch(c -> c.column().equals(idColumn))) {
                columns.add(0, new RelationSchema.Column(idColumn, idColumn, "TEXT",
                        true, false, null, null));
            }
            pk = List.of(idColumn);
        }
        return new RelationSchema(concept, table, objectType, columns,
                pk, foreignKeys, checks, false);
    }

    /** Child tables for multi-valued ("zero or more") facts — Rmap stage 2. */
    /**
     * Child tables for multi-valued ("zero or more") facts — Rmap stage 2.
     * The child's FK names the table actually keyed on the subject object type
     * (the supertype's under absorb, the subtype's own otherwise — that is
     * {@code tableNames}); the target column is the subject's identity column
     * itself, not the concept name.
     */
    private static List<RelationSchema> childTables(String concept, List<FactType> facts,
                                                    Map<String, String> tableNames,
                                                    List<RelationSchema> tables,
                                                    Map<String, String> referenceSchemes,
                                                    Map<String, SubtypeMapping> subtypeOf,
                                                    Map<String, String> supertypeOf) {
        List<RelationSchema> out = new ArrayList<>();
        for (FactType f : facts) {
            if (!f.multiValued()) {
                continue;
            }
            String subject = f.subjectTypes().get(0);
            // The subject column is the subject's identity column. A subtype
            // subject keys on the supertype's identity column (its own scheme is
            // inherited) and its rows live in the member table (separate/
            // partition) or the supertype's table (absorb); a normal subject keys
            // on its own scheme.
            String subjectColumn;
            String parentTable;
            if (subtypeOf.containsKey(subject)) {
                String supertype = supertypeOf.get(subject);
                subjectColumn = snake(rootScheme(subject, supertypeOf, referenceSchemes));
                boolean absorbed = subtypeOf.get(subject) == SubtypeMapping.ABSORB;
                parentTable = tableNames.get(absorbed ? supertype : subject);
            } else {
                subjectColumn = snake(referenceSchemes.getOrDefault(subject, subject));
                parentTable = tableNames.get(subject);
            }
            List<RelationSchema.Column> cols = new ArrayList<>();
            cols.add(new RelationSchema.Column(subjectColumn, subjectColumn, "TEXT",
                    true, false, null, null));
            cols.add(new RelationSchema.Column(f.field(), snake(f.field()),
                    sqlTypeOf(f.valueType()), true, false, null, null));
            List<String> pk = List.of(subjectColumn, snake(f.field()));
            // Render the intra-concept FK only when the subject's own table was
            // realised and carries data facts. An identity-only parent (the
            // subject plays no functional role of its own — only multi-valued
            // facts or objectified-pair components) is not emitted at all, so it
            // has no table to point at, and an FK there would be
            // unpopulationable.
            boolean parentHasData = parentTable != null && tables.stream()
                    .filter(t -> t.table().equals(parentTable))
                    .findFirst()
                    .map(t -> !t.dataColumns().isEmpty())
                    .orElse(false);
            out.add(new RelationSchema(concept,
                    snake(concept) + "__" + snake(f.field()), subject,
                    cols, pk,
                    parentHasData
                            ? List.of(subjectColumn + " -> " + parentTable
                                      + "(" + subjectColumn + ")")
                            : List.<String>of(),
                    List.of(), false));
        }
        return out;
    }

    private static void addColumn(List<RelationSchema.Column> columns, String predicate,
                                  String column, String sqlType, boolean mandatory,
                                  boolean unique, String defaultValue, String constraint) {
        addColumn(columns, predicate, column, sqlType, mandatory, unique,
                defaultValue, constraint, null);
    }

    private static void addColumn(List<RelationSchema.Column> columns, String predicate,
                                  String column, String sqlType, boolean mandatory,
                                  boolean unique, String defaultValue, String constraint,
                                  String uniqueWhileAbsent) {
        if (columns.stream().anyMatch(c -> c.column().equals(column))) {
            return;
        }
        columns.add(new RelationSchema.Column(predicate, column, sqlType,
                mandatory, unique, defaultValue, constraint, uniqueWhileAbsent));
    }

    private static String compoundKey(List<String> subjectTypes) {
        return String.join("+", subjectTypes);
    }

    private static String checkExprOn(String column, String enumBody) {
        List<String> inValues = new ArrayList<>();
        List<String> quoted = new ArrayList<>();
        for (String v : enumBody.split(",")) {
            String t = v.trim();
            if (t.isEmpty()) {
                continue;
            }
            if (t.contains("..")) {
                // Interval form a..b — emit a BETWEEN on a numeric column.
                String[] bounds = t.split("\\.\\.");
                return column + " BETWEEN " + bounds[0].trim() + " AND " + bounds[1].trim();
            }
            quoted.add("'" + t + "'");
        }
        return column + " IN (" + String.join(", ", quoted) + ")";
    }

    private static String checkName(String objectType, String field) {
        // snakeName sanitizes a compound subject key ('+' is illegal in an
        // unquoted SQL identifier): Physician+Patient → physician_and_patient.
        return "ck_" + snakeName(objectType) + "_" + snake(field);
    }

    private static String sqlTypeOf(String valueType) {
        return switch (valueType) {
            case "Int", "Integer" -> "INTEGER";
            case "Timestamp" -> "TIMESTAMP";
            default -> "TEXT";
        };
    }

    private static String snake(String s) {
        return s.replaceAll("([a-z0-9])([A-Z])", "$1_$2").toLowerCase();
    }

    /** Sanitise an object-type key (which may be {@code A+B}) for a table name. */
    private static String snakeName(String s) {
        return snake(s.replace("+", "_and_"));
    }

    /**
     * The table name a subtype/partition member realises under:
     * {@code snake(concept) + "__" + snakeName(member)}. A member table
     * reports the SUPERtype as its {@code objectType} (a subtype has no
     * reference scheme of its own), so {@link RmapModel#tableFor} cannot
     * distinguish members — the deterministic naming rule is the only
     * member-resolvable handle. Absorbed members realise no table of their
     * own (their predicates live on the supertype's table).
     */
    public static String memberTableName(String concept, String member) {
        return snake(concept) + "__" + snakeName(member);
    }

    // Public helper for tests/callers building child tables.
    /** Test hook: the model's child tables (composite PK over (subject, value)). */
    static List<RelationSchema> childTablesFor(String concept, String stateNotation) {
        return deriveModel(concept, stateNotation).tables().stream()
                .filter(t -> t.primaryKey().size() == 2 && t.columns().size() == 2)
                .toList();
    }
}
