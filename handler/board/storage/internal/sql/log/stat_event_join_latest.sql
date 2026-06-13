SELECT actor_id, MAX(added_at) AS connected_at
FROM stat_event
WHERE event_type = 'JOIN'
GROUP BY actor_id;
