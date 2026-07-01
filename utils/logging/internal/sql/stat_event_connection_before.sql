-- Purpose: Find the latest connection-count payload before a dashboard time window starts.
-- Structure: Loaded by utils.logging.internal.repository.get_previous_connection_payloads() for hourly connection charts.
SELECT payload_json
FROM stat_event
WHERE added_at < ?
  AND event_type IN ('JOIN', 'QUIT')
ORDER BY id DESC
LIMIT ?;
