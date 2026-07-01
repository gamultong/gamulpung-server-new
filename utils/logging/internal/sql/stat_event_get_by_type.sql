-- Purpose: Fetch one stat event by type for repository tests and targeted smoke checks.
-- Structure: Loaded by utils.logging.internal.repository.get_stat_event_by_type() against the stat_event table.
SELECT event_type, actor_id, tile_id, x, y, value, payload_json
FROM stat_event
WHERE event_type = ?;
