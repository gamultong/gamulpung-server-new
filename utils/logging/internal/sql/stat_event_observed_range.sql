SELECT
    MIN(added_at) AS first_seen_at,
    MAX(added_at) AS last_seen_at
FROM stat_event;
