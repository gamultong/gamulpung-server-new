SELECT payload_json
FROM stat_event
WHERE added_at < ?
  AND event_type IN ('JOIN', 'QUIT')
ORDER BY id DESC
LIMIT ?;
