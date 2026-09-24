package com.example.app.storage;

/**
 * The selectable concept-state backend. Chosen by the {@code clad.storage}
 * configuration property; the engine's {@code FactStore} SPI is the boundary,
 * so concepts and syncs are identical whichever backend is active.
 */
public enum StorageBackend {
    MEMORY,
    POSTGRES
}
