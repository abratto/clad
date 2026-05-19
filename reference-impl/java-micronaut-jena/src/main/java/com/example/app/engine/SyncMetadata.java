package com.example.app.engine;

import java.lang.annotation.Documented;
import java.lang.annotation.Retention;
import java.lang.annotation.Target;

import static java.lang.annotation.ElementType.TYPE;
import static java.lang.annotation.RetentionPolicy.RUNTIME;

/**
 * Human-readable sync graph metadata for dev-only debug introspection.
 *
 * <p>{@link com.example.app.infrastructure.DebugController} uses this
 * annotation to describe registered {@link SyncAgent} rules as flows and
 * steps instead of raw SPARQL fragments.
 */
@Documented
@Retention(RUNTIME)
@Target(TYPE)
public @interface SyncMetadata {

    String flow();

    int step();

    String triggeredBy();

    String fires();

    String where() default "";
}
