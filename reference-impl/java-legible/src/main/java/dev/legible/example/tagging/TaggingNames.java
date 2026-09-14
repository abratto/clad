package dev.legible.example.tagging;

import dev.legible.example.social.PostingConcept;
import dev.legible.example.social.NotifyingConcept;

/**
 * Readable relay constants for the tagging sync rules that reference concept
 * classes from other feature packages. Concept strings come from the owning
 * concept classes' {@code NAME} constants; the aliases here exist only because
 * a same-token static-import alias is not expressible in Java. Nothing here is
 * logic — see {@code maintenance/sync-dsl-legibility.md}.
 */
public final class TaggingNames {

    public static final String TAGGING = TaggingConcept.NAME;
    public static final String PROFILING = ProfilingConcept.NAME;
    public static final String SUBSCRIBING = SubscribingConcept.NAME;
    public static final String POSTING = PostingConcept.NAME;
    public static final String NOTIFYING = NotifyingConcept.NAME;

    private TaggingNames() {
    }
}
