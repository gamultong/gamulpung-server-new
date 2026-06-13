SELECT id, added_at, event_type, actor_id, tile_id, x, y, value, payload_json
FROM stat_event
WHERE added_at >= ?
ORDER BY id ASC;
