-- Purpose: Read the newest stat events for the stats dashboard recent event panel.
-- Structure: Loaded by utils.logging.internal.repository.get_recent_stat_events(), then mapped by utils.stats.internal.dashboard_repository.
SELECT id, added_at, event_type, actor_id, tile_id, x, y, value, payload_json
FROM stat_event
ORDER BY id DESC
LIMIT ?;
