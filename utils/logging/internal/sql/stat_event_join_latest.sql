-- Purpose: Get each actor's latest JOIN timestamp for active cursor session duration.
-- Structure: Loaded by utils.logging.internal.repository.get_latest_join_times(), then merged into dashboard active cursors.
SELECT actor_id, MAX(added_at) AS connected_at
FROM stat_event
WHERE event_type = 'JOIN'
GROUP BY actor_id;
