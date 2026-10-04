package dev.legible.storage;

import java.util.ArrayList;
import java.util.List;

/**
 * A concept's relational realisation — a <strong>table set</strong> (one concept
 * region may own several tables), per Halpin's Rmap.
 *
 * <p>Rmap maps a conceptual schema's elementary fact types into normalized
 * tables by grouping: fact types with a <em>composite</em> key map to their own
 * table (stage 2), fact types with a <em>simple</em> key on a common object type
 * group into that object type's table (stage 3), and nested/objectified fact
 * types ("compidots") are unpacked into their component attributes (stages 1
 * and 4). A concept whose state ranges over more than one object type therefore
 * realises as more than one table; the {@code RelationSchema} record models one
 * table, and this record models the concept's whole set.
 *
 * <p>This supersedes the older single-{@code RelationSchema}-per-concept shape:
 * the concept is the region (R2), and a region may be a set of tables.
 */
public record RmapModel(
        String concept,
        List<RelationSchema> tables) {

    public RmapModel {
        tables = List.copyOf(tables);
    }

    /** The single-table convenience case (a concept whose state is one object type). */
    public RmapModel(String concept, RelationSchema table) {
        this(concept, List.of(table));
    }

    /** Every table's primary (object) type this concept's region owns. */
    public List<String> objectTypes() {
        List<String> out = new ArrayList<>();
        for (RelationSchema t : tables) {
            out.add(t.objectType());
        }
        return out;
    }

    /** The table keyed on {@code objectType}, or {@code null}. */
    public RelationSchema tableFor(String objectType) {
        for (RelationSchema t : tables) {
            if (t.objectType().equals(objectType)) {
                return t;
            }
        }
        return null;
    }

    /** The table that realises the given fact-type predicate, or {@code null}. */
    public RelationSchema tableForPredicate(String predicate) {
        for (RelationSchema t : tables) {
            if (t.columnFor(predicate) != null) {
                return t;
            }
        }
        return null;
    }
}
