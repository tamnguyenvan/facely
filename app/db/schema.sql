-- Facely Database Schema

CREATE TABLE IF NOT EXISTS identities (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    person_id   TEXT    NOT NULL UNIQUE,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS embeddings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_id  INTEGER NOT NULL REFERENCES identities(id) ON DELETE CASCADE,
    model_name   TEXT    NOT NULL,
    vector       BLOB    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(identity_id, model_name)
);

CREATE INDEX IF NOT EXISTS idx_embeddings_identity ON embeddings(identity_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_name);
