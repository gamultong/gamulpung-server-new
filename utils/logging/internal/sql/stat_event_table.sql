-- Purpose: Create the stat event table used for gameplay and lifecycle analytics.
-- Structure: Initialized from server lifespan through utils.logging.internal.repository.set_stat_event_table(); written by stats event recorder.
CREATE TABLE IF NOT EXISTS stat_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    added_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    event_type TEXT NOT NULL,
    actor_id TEXT,
    tile_id TEXT,
    x INTEGER,
    y INTEGER,
    value INTEGER,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_stat_event_type_added ON stat_event(event_type, added_at);
CREATE INDEX IF NOT EXISTS idx_stat_event_actor_added ON stat_event(actor_id, added_at);
CREATE INDEX IF NOT EXISTS idx_stat_event_tile_added ON stat_event(tile_id, added_at);
CREATE INDEX IF NOT EXISTS idx_stat_event_xy ON stat_event(x, y);
