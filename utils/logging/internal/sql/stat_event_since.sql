-- Purpose: Read stat events inside a dashboard time window.
-- Structure: Loaded by utils.logging.internal.repository.get_stat_events_since() for stats summary, charts, players, and tile heatmap.
SELECT id, added_at, event_type, actor_id, tile_id, x, y, value, payload_json
FROM stat_event
WHERE added_at >= ?
ORDER BY id ASC;
