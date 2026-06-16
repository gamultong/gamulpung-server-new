SELECT event_type, actor_id, tile_id, x, y, value, payload_json
FROM stat_event
WHERE event_type = ?;
