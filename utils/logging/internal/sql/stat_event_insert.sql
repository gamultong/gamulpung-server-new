-- Purpose: Persist one gameplay/stat lifecycle event into stat_event.
-- Structure: Loaded by utils.logging.internal.repository.insert_stat_event(), which is called by utils.stats.internal.event_recorder.
INSERT INTO stat_event (
    event_type,
    actor_id,
    tile_id,
    x,
    y,
    value,
    payload_json
) VALUES (?, ?, ?, ?, ?, ?, ?);
