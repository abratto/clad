package com.example.app.engine;

/**
 * Stable identifiers used in flow-token field maps. Syncs pattern-match
 * by these names, so they must change only via the spec process.
 *
 * <p>When the RDF backend lands, these become full URIs under a CLAD
 * vocabulary namespace.
 */
public final class RdfVocabulary {

    private RdfVocabulary() {}

    public static final String FIELD_USER_ID = "userId";
    public static final String FIELD_USERNAME = "username";
    public static final String FIELD_SESSION_ID = "sessionId";
    public static final String FIELD_OUTCOME = "outcome";
    public static final String FIELD_REQUEST_ID = "requestId";
}
