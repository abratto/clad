package com.example.app.infrastructure;

import com.example.app.engine.FlowManager;
import com.example.app.engine.FlowToken;
import com.example.app.engine.RdfVocabulary;
import java.util.Map;
import java.util.UUID;

/**
 * The sole HTTP entry concept (hard rule R4). No business concept may
 * carry HTTP annotations.
 *
 * <p>This skeleton does not register any real Micronaut routes yet; it
 * exists to anchor the R4 ArchUnit check and to serve as the parent of
 * every flow-token tree (a {@code Web.handle} token is the root of any
 * inbound request).
 */
public final class WebConcept {

    private final FlowManager flow;

    public WebConcept(FlowManager flow) {
        this.flow = flow;
    }

    /**
     * Mint the root flow token for an inbound HTTP request. Returns the
     * token so concept actions invoked downstream can pass its id as
     * their parent.
     */
    public FlowToken handle(String requestId, String actor) {
        return flow.emit(
                "Web.handle",
                actor,
                null,
                Map.of(RdfVocabulary.FIELD_REQUEST_ID, requestId));
    }
}
